#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API客户端模块 - 处理外部API调用
"""

import requests
import json
import time
import logging
from typing import List, Dict, Any, Optional
import re
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)


class RoomsAPIClient:
    """房间数据API客户端"""
    
    def __init__(self):
        """初始化API客户端"""
        self.session = requests.Session()
        self.setup_session()
    
    def setup_session(self):
        """配置会话"""
        self.session.headers.update(Config.API_HEADERS)
        self.session.cookies.update(Config.API_COOKIES)
    
    def make_request(self, page_number: int = 1, page_size: int = None) -> Optional[Dict[str, Any]]:
        """
        发送API请求
        
        Args:
            page_number: 页码
            page_size: 每页大小
            
        Returns:
            API响应数据或None
        """
        payload = Config.get_api_payload(page_number, page_size)
        
        for attempt in range(Config.API_MAX_RETRIES):
            try:
                logger.info(f"正在请求第 {page_number} 页数据（尝试 {attempt + 1}/{Config.API_MAX_RETRIES}）")
                
                response = self.session.post(
                    Config.API_BASE_URL,
                    json=payload,
                    timeout=Config.API_TIMEOUT
                )
                
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"第 {page_number} 页请求成功，状态码: {response.status_code}")
                
                return data
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"第 {page_number} 页请求失败 (尝试 {attempt + 1}/{Config.API_MAX_RETRIES}): {str(e)}")
                if attempt < Config.API_MAX_RETRIES - 1:
                    logger.info(f"等待 {Config.API_RETRY_DELAY} 秒后重试...")
                    time.sleep(Config.API_RETRY_DELAY)
                else:
                    logger.error(f"第 {page_number} 页请求最终失败")
                    
            except json.JSONDecodeError as e:
                logger.error(f"第 {page_number} 页响应JSON解析失败: {str(e)}")
                break
                
        return None
    
    def fetch_all_rooms_data(self) -> List[Dict[str, Any]]:
        """
        获取所有房间数据
        
        Returns:
            所有房间数据的列表
        """
        all_data = []
        current_page = 1
        total_pages = None
        
        logger.info("开始获取房间入住数据...")
        
        while True:
            # 发送请求
            response_data = self.make_request(current_page, Config.API_PAGE_SIZE)
            
            if not response_data:
                logger.error(f"第 {current_page} 页请求失败，停止获取")
                break
            
            # 检查响应状态
            if not response_data.get('success', False):
                logger.error(f"API返回错误: {response_data.get('message', '未知错误')}")
                break
            
            # 获取数据
            data = response_data.get('data', {})
            records = data.get('records', [])
            
            if not records:
                logger.info(f"第 {current_page} 页没有数据，获取结束")
                break
            
            # 第一次请求时获取总页数
            if total_pages is None:
                total_records = data.get('total', 0)
                total_pages = data.get('pages', 1)
                logger.info(f"总记录数: {total_records}, 总页数: {total_pages}")
            
            # 添加当前页数据
            all_data.extend(records)
            logger.info(f"第 {current_page} 页获取到 {len(records)} 条记录，累计 {len(all_data)} 条")
            
            # 检查是否已到最后一页
            if current_page >= total_pages:
                logger.info("已获取所有数据")
                break
            
            # 准备下一页
            current_page += 1
            
            # 添加请求间隔，避免过于频繁
            time.sleep(0.5)
        
        logger.info(f"获取完成！总共获取 {len(all_data)} 条记录")
        return all_data
    
    def parse_room_info(self, house_name: str) -> Dict[str, Any]:
        """
        解析房间信息
        
        Args:
            house_name: 房间名称，如 "之寓·未来-A4栋-1单元-107"
            
        Returns:
            解析后的房间信息
        """
        # 使用正则表达式解析房间信息
        pattern = r'之寓·未来-A(\d+)栋-(\d+)单元-(\d+)'
        match = re.match(pattern, house_name)
        
        if match:
            building = int(match.group(1))  # 栋号
            unit = int(match.group(2))      # 单元号  
            room_num = match.group(3)       # 房间号
            
            # 从房间号解析楼层和房间
            if len(room_num) >= 3:
                floor = int(room_num[:-2]) if room_num[:-2] else 1
                room_in_floor = int(room_num[-2:])
            else:
                floor = 1
                room_in_floor = int(room_num)
            
            return {
                'building': building,
                'unit': unit,
                'floor': floor,
                'room_number': room_num,
                'room_in_floor': room_in_floor
            }
        
        return None
    
    def process_room_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理原始房间数据
        
        Args:
            raw_data: 从API获取的原始数据
            
        Returns:
            处理后的房间数据列表
        """
        processed_rooms = []
        
        # 按房间分组
        rooms_map = {}
        
        for record in raw_data:
            house_id = record.get('houseId')
            house_name = record.get('houseName', '')
            
            if not house_id or not house_name:
                continue
            
            # 解析房间信息
            room_info = self.parse_room_info(house_name)
            if not room_info:
                logger.warning(f"无法解析房间信息: {house_name}")
                continue
            
            # 如果房间不存在，创建新房间
            if house_id not in rooms_map:
                rooms_map[house_id] = {
                    'house_id': house_id,
                    'house_name': house_name,
                    'building': room_info['building'],
                    'unit': room_info['unit'],
                    'floor': room_info['floor'],
                    'room_in_floor': room_info['room_in_floor'],
                    'room_number': room_info['room_number'],
                    'tenants': [],
                    'main_tenant': None,
                    'co_tenants': []
                }
            
            # 添加租户信息
            tenant = {
                'id': record.get('id'),
                'guests_id': record.get('guestsId'),
                'tenant_name': record.get('tenantName', ''),
                'mobile': record.get('mobile', ''),
                'is_main': record.get('isMain', 0),
                'certificate_num': record.get('certificateNum', ''),
                'emergency_contact': record.get('emergencyContact', ''),
                'emergency_mobile': record.get('emergencyMobile', ''),
                'sign_status': record.get('signStatus', 0),
                'occupancy_flag': record.get('occupancyFlag', 0)
            }
            
            rooms_map[house_id]['tenants'].append(tenant)
            
            # 设置主租户和合租户
            if tenant['is_main'] == 1:
                rooms_map[house_id]['main_tenant'] = tenant
            else:
                rooms_map[house_id]['co_tenants'].append(tenant)
        
        # 转换为列表
        for room in rooms_map.values():
            # 按租户类型排序（主租户在前）
            room['tenants'].sort(key=lambda x: (x['is_main'] == 0, x['tenant_name']))
            processed_rooms.append(room)
        
        # 按楼层和房间号排序
        processed_rooms.sort(key=lambda x: (x['floor'], x['room_in_floor']))
        
        logger.info(f"处理完成，共 {len(processed_rooms)} 个房间")
        return processed_rooms


class RoomsDataManager:
    """房间数据管理器"""
    
    def __init__(self):
        """初始化数据管理器"""
        self.api_client = RoomsAPIClient()
    
    def generate_complete_layout(self) -> Dict[str, Any]:
        """
        生成完整的房间布局数据
        
        Returns:
            完整的房间布局数据
        """
        try:
            # 获取实际入住数据
            raw_data = self.api_client.fetch_all_rooms_data()
            occupied_rooms = self.api_client.process_room_data(raw_data)
            
            # 创建已入住房间的映射
            occupied_rooms_map = {}
            for room in occupied_rooms:
                room_key = f"{room['floor']}-{room['room_number']}"
                occupied_rooms_map[room_key] = room
            
            # 生成完整房间布局
            all_rooms = []
            building_config = Config.BUILDING_CONFIG
            
            # 1楼: 10间房 (01-06, 07-10)
            floor = 1
            floor1_rooms = [f"1{i:02d}" for i in range(1, 7)] + [f"1{i:02d}" for i in range(7, 11)]
            
            for i, room_number in enumerate(floor1_rooms, 1):
                room_key = f"{floor}-{room_number}"
                
                if room_key in occupied_rooms_map:
                    # 使用实际数据
                    all_rooms.append(occupied_rooms_map[room_key])
                else:
                    # 创建空房间
                    all_rooms.append(self.create_empty_room(floor, room_number, i))
            
            # 2-20楼: 每层12间房
            for floor in range(2, 21):
                for room_in_floor in range(1, 13):
                    room_number = f"{floor}{room_in_floor:02d}"
                    room_key = f"{floor}-{room_number}"
                    
                    if room_key in occupied_rooms_map:
                        # 使用实际数据
                        all_rooms.append(occupied_rooms_map[room_key])
                    else:
                        # 创建空房间
                        all_rooms.append(self.create_empty_room(floor, room_number, room_in_floor))
            
            # 按楼层和房间号排序
            all_rooms.sort(key=lambda x: (x['floor'], x['room_in_floor']))
            
            # 生成完整数据结构
            complete_data = {
                'total_rooms': len(all_rooms),
                'rooms': all_rooms,
                'timestamp': datetime.now().isoformat(),
                'layout_info': {
                    'building': building_config['building'],
                    'floors': building_config['total_floors'],
                    'floor_1_rooms': building_config['floor_1_rooms'],
                    'regular_floor_rooms': building_config['regular_floor_rooms'],
                    'total_designed_rooms': building_config['total_rooms']
                }
            }
            
            logger.info(f"完整布局生成成功，共 {len(all_rooms)} 个房间")
            return complete_data
            
        except Exception as e:
            logger.error(f"生成完整布局失败: {str(e)}")
            raise
    
    def create_empty_room(self, floor: int, room_number: str, room_in_floor: int) -> Dict[str, Any]:
        """创建空房间数据"""
        building_config = Config.BUILDING_CONFIG
        
        return {
            'house_id': f"empty_{floor}_{room_in_floor}",
            'house_name': f"之寓·未来-A{building_config['building'][1]}栋-{building_config['unit']}单元-{room_number}",
            'building': int(building_config['building'][1]),
            'unit': building_config['unit'],
            'floor': floor,
            'room_in_floor': room_in_floor,
            'room_number': str(room_number),
            'tenants': [],
            'main_tenant': None,
            'co_tenants': [],
            'is_vacant': True
        } 