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

# 尝试导入认证管理器
try:
    from auth_manager import get_fresh_auth_info
    AUTO_AUTH_AVAILABLE = True
except ImportError:
    AUTO_AUTH_AVAILABLE = False
    logging.warning("认证管理器不可用，将使用配置文件中的认证信息")

logger = logging.getLogger(__name__)


class RoomsAPIClient:
    """房间数据API客户端"""
    
    def __init__(self):
        """初始化API客户端"""
        self.session = requests.Session()
        self.auth_refreshed = False
        self.setup_session()
    
    def setup_session(self):
        """配置会话"""
        self.session.headers.update(Config.API_HEADERS)
        self.session.cookies.update(Config.API_COOKIES)
    
    def refresh_auth_if_needed(self):
        """如果需要，刷新认证信息"""
        if not AUTO_AUTH_AVAILABLE:
            logger.warning("自动认证不可用，使用配置文件中的认证信息")
            return False
        
        if self.auth_refreshed:
            logger.info("认证信息已在本次会话中刷新过")
            return True
        
        try:
            logger.info("尝试获取最新认证信息...")
            fresh_auth = get_fresh_auth_info()
            
            if fresh_auth:
                # 更新会话cookies
                self.session.cookies.update(fresh_auth)
                
                # 更新配置（可选，用于调试）
                Config.update_cookies(fresh_auth)
                
                self.auth_refreshed = True
                logger.info("认证信息刷新成功")
                return True
            else:
                logger.error("无法获取最新认证信息")
                return False
                
        except Exception as e:
            logger.error(f"刷新认证信息时发生错误: {str(e)}")
            return False
    
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
                
                # 检查是否是认证失败
                if response.status_code == 401:
                    logger.warning("认证失败，尝试刷新认证信息...")
                    if self.refresh_auth_if_needed():
                        logger.info("认证信息已刷新，重新尝试请求...")
                        continue
                    else:
                        logger.error("无法刷新认证信息，请求失败")
                        return None
                
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"第 {page_number} 页请求成功，状态码: {response.status_code}")
                
                return data
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"第 {page_number} 页请求失败 (尝试 {attempt + 1}/{Config.API_MAX_RETRIES}): {str(e)}")
                
                # 如果是401错误且还没有刷新过认证信息，尝试刷新
                if "401" in str(e) and not self.auth_refreshed:
                    logger.warning("检测到401错误，尝试刷新认证信息...")
                    if self.refresh_auth_if_needed():
                        logger.info("认证信息已刷新，重新尝试请求...")
                        continue
                
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
        # 导入数据库管理器
        try:
            from database_manager import db_manager
            self.db_manager = db_manager
            self.use_database = True
            logger.info("数据库管理器已加载")
        except ImportError as e:
            logger.warning(f"数据库管理器不可用: {e}")
            self.db_manager = None
            self.use_database = False
    
    def generate_complete_layout(self) -> Dict[str, Any]:
        """
        生成完整的房间布局数据
        优先从API获取最新数据，同步到数据库后返回带标签的数据
        
        Returns:
            完整的房间布局数据
        """
        try:
            logger.info("开始生成完整布局数据...")
            
            # 步骤1：从API获取最新的人员数据
            logger.info("从API获取最新人员数据...")
            raw_data = self.api_client.fetch_all_rooms_data()
            occupied_rooms_api = self.api_client.process_room_data(raw_data)
            logger.info(f"API返回 {len(occupied_rooms_api)} 个有人房间")
            
            occupied_rooms = occupied_rooms_api  # 默认使用API数据
            
            # 步骤2：如果使用数据库，同步数据并获取带标签的完整数据
            if self.use_database and self.db_manager:
                logger.info("同步数据到数据库并获取标签信息...")
                
                # 转换数据格式以适配数据库
                rooms_for_db = self._convert_rooms_for_database(occupied_rooms_api)
                
                # 保存到数据库（智能保留标签）
                if self.db_manager.save_rooms_data(rooms_for_db):
                    logger.info("房间数据已智能同步到数据库，标签信息已保留")
                    
                    # 从数据库获取带标签的完整数据
                    occupied_rooms = self._get_rooms_with_tags()
                    logger.info(f"从数据库获取 {len(occupied_rooms)} 个带标签的房间数据")
                else:
                    logger.warning("数据库同步失败，使用API原始数据（无标签信息）")
            else:
                logger.warning("数据库不可用，使用API原始数据（无标签信息）")
            
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
            
            # 计算统计信息
            occupied_count = sum(1 for room in all_rooms if room.get('tenants'))
            
            # 生成完整数据结构
            complete_data = {
                'total_rooms': len(all_rooms),
                'occupied_count': occupied_count,
                'vacant_count': len(all_rooms) - occupied_count,
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
            
            # 如果使用数据库，添加标签统计
            if self.use_database and self.db_manager:
                tag_stats = self.db_manager.get_tag_statistics()
                complete_data['tag_statistics'] = tag_stats
            
            logger.info(f"完整布局生成成功，共 {len(all_rooms)} 个房间，{occupied_count} 个已入住")
            return complete_data
            
        except Exception as e:
            logger.error(f"生成完整布局失败: {str(e)}")
            raise
    
    def _convert_rooms_for_database(self, occupied_rooms: List[Dict]) -> List[Dict]:
        """转换房间数据格式以适配数据库"""
        rooms_for_db = []
        
        for room in occupied_rooms:
            # 转换租户数据
            tenants_for_db = []
            for tenant in room.get('tenants', []):
                tenant_data = {
                    'student_id': tenant.get('guests_id') or tenant.get('id'),
                    'name': tenant.get('tenant_name', ''),
                    'mobile': tenant.get('mobile', ''),
                    'is_main': tenant.get('is_main', 0),
                    'certificate_num': tenant.get('certificate_num', ''),
                    'emergency_contact': tenant.get('emergency_contact', ''),
                    'emergency_mobile': tenant.get('emergency_mobile', ''),
                    'sign_status': tenant.get('sign_status', 0),
                    'occupancy_flag': tenant.get('occupancy_flag', 0),
                    'check_in_date': datetime.now().isoformat()  # 可以从其他字段获取
                }
                tenants_for_db.append(tenant_data)
            
            # 房间数据
            room_data = {
                'room_number': room.get('room_number'),
                'building': room.get('building'),
                'floor': room.get('floor'),
                'room_type': '标准间',  # 可以根据需要调整
                'capacity': len(tenants_for_db) if tenants_for_db else 2,  # 默认容量
                'occupied': len(tenants_for_db) > 0,
                'tenants': tenants_for_db
            }
            
            rooms_for_db.append(room_data)
        
        return rooms_for_db
    
    def get_rooms_with_tags(self) -> Optional[Dict]:
        """获取带标签的房间数据 - 优先从数据库读取"""
        if self.use_database and self.db_manager:
            return self.db_manager.get_rooms_with_tags_from_db()
        return None
    
    def get_room_detail_from_db(self, house_id: str) -> Optional[Dict]:
        """从数据库获取房间详情"""
        if self.use_database and self.db_manager:
            return self.db_manager.get_room_detail_from_db(house_id)
        return None
    
    def _get_rooms_with_tags(self) -> List[Dict]:
        """从数据库获取带标签的房间数据"""
        try:
            # 获取房间数据
            rooms_data = self.db_manager.get_rooms_data({'occupied': True})
            
            # 转换回原格式并添加标签信息
            rooms_with_tags = []
            for room in rooms_data:
                # 获取房间的学生数据（带标签）
                students = self.db_manager.get_students_data({'room_number': room['room_number']})
                
                # 转换租户数据格式
                tenants = []
                main_tenant = None
                co_tenants = []
                
                for student in students:
                    tenant = {
                        'id': student.get('student_id'),
                        'guests_id': student.get('student_id'),
                        'tenant_name': student.get('name', ''),
                        'mobile': student.get('mobile', ''),
                        'is_main': student.get('is_main', 0),
                        'certificate_num': student.get('certificate_num', ''),
                        'emergency_contact': student.get('emergency_contact', ''),
                        'emergency_mobile': student.get('emergency_mobile', ''),
                        'sign_status': student.get('sign_status', 0),
                        'occupancy_flag': student.get('occupancy_flag', 0),
                        'tag': student.get('tag', '未分类')  # 添加标签信息
                    }
                    
                    tenants.append(tenant)
                    
                    if tenant['is_main'] == 1:
                        main_tenant = tenant
                    else:
                        co_tenants.append(tenant)
                
                # 构建房间数据
                room_data = {
                    'house_id': room.get('_id') or f"db_{room['room_number']}",
                    'house_name': f"之寓·未来-A{room['building']}栋-1单元-{room['room_number']}",
                    'building': room['building'],
                    'unit': 1,
                    'floor': room['floor'],
                    'room_in_floor': int(room['room_number'][-2:]) if len(room['room_number']) >= 2 else 1,
                    'room_number': room['room_number'],
                    'tenants': tenants,
                    'main_tenant': main_tenant,
                    'co_tenants': co_tenants,
                    'is_vacant': False
                }
                
                rooms_with_tags.append(room_data)
            
            return rooms_with_tags
            
        except Exception as e:
            logger.error(f"从数据库获取房间数据失败: {e}")
            return []
    
    def get_students_by_tag(self, tag: str) -> List[Dict]:
        """根据标签获取学生列表"""
        if self.use_database and self.db_manager:
            return self.db_manager.get_students_by_tag(tag)
        return []
    
    def update_student_tag(self, student_id: str, tag: str) -> bool:
        """更新学生标签"""
        if self.use_database and self.db_manager:
            return self.db_manager.update_student_tag(student_id, tag)
        return False
    
    def get_available_tags(self) -> List[str]:
        """获取可用标签列表"""
        if self.use_database and self.db_manager:
            return self.db_manager.get_available_tags()
        return Config.STUDENT_TAGS['default_tags']
    
    def get_tag_statistics(self) -> Dict[str, int]:
        """获取标签统计"""
        if self.use_database and self.db_manager:
            return self.db_manager.get_tag_statistics()
        return {}
    
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