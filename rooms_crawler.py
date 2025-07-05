#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
房间入住信息爬取脚本
获取所有房间的入住数据并处理为可视化格式
"""

import requests
import json
import time
import logging
from typing import List, Dict, Any, Optional
import sys
from datetime import datetime
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rooms_crawler.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class RoomsCrawler:
    """房间入住信息爬取器"""
    
    def __init__(self):
        """初始化爬取器"""
        self.base_url = "https://platform.inzhiyu.com/ams/api/contractEnterprise/guestsList"
        self.session = requests.Session()
        self.setup_headers()
        self.page_size = 50
        self.max_retries = 3
        self.retry_delay = 2
        
    def setup_headers(self):
        """设置请求头"""
        self.session.headers.update({
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://platform.inzhiyu.com',
            'Pragma': 'no-cache',
            'Referer': 'https://platform.inzhiyu.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        })
        
        # 设置Cookie
        self.session.cookies.update({
            'HWWAFSESID': '26cf673e248a27b3a5',
            'HWWAFSESTIME': '1751609522843',
            '_ams_token': 'web_bgd6s9lz980w7c45z8gvkhrd5spkd2mw',
            '_common_token': 'web_bgd6s9lz980w7c45z8gvkhrd5spkd2mw'
        })
    
    def make_request(self, page_number: int = 1, page_size: int = 50) -> Optional[Dict[str, Any]]:
        """
        发送API请求
        
        Args:
            page_number: 页码
            page_size: 每页大小
            
        Returns:
            API响应数据或None
        """
        payload = {
            "pageNumber": page_number,
            "pageSize": page_size,
            "guestsName": "",
            "contractType": 3,
            "contractId": 1489
        }
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"正在请求第 {page_number} 页数据（尝试 {attempt + 1}/{self.max_retries}）")
                
                response = self.session.post(
                    self.base_url,
                    json=payload,
                    timeout=30
                )
                
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"第 {page_number} 页请求成功，状态码: {response.status_code}")
                
                return data
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"第 {page_number} 页请求失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    logger.info(f"等待 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"第 {page_number} 页请求最终失败")
                    
            except json.JSONDecodeError as e:
                logger.error(f"第 {page_number} 页响应JSON解析失败: {str(e)}")
                break
                
        return None
    
    def crawl_all_pages(self) -> List[Dict[str, Any]]:
        """
        爬取所有页面的房间数据
        
        Returns:
            所有房间数据的列表
        """
        all_data = []
        current_page = 1
        total_pages = None
        total_records = None
        
        logger.info("开始爬取房间入住数据...")
        
        while True:
            # 发送请求
            response_data = self.make_request(current_page, self.page_size)
            
            if not response_data:
                logger.error(f"第 {current_page} 页请求失败，停止爬取")
                break
            
            # 检查响应状态
            if not response_data.get('success', False):
                logger.error(f"API返回错误: {response_data.get('message', '未知错误')}")
                break
            
            # 获取数据
            data = response_data.get('data', {})
            records = data.get('records', [])
            
            if not records:
                logger.info(f"第 {current_page} 页没有数据，爬取结束")
                break
            
            # 第一次请求时获取总页数和总记录数
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
            time.sleep(1)
        
        logger.info(f"爬取完成！总共获取 {len(all_data)} 条记录")
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
                'room_in_floor': room_in_floor,
                'room_number': room_num,
                'original_name': house_name
            }
        else:
            logger.warning(f"无法解析房间信息: {house_name}")
            return {
                'building': 0,
                'unit': 0,
                'floor': 0,
                'room_in_floor': 0,
                'room_number': house_name,
                'original_name': house_name
            }
    
    def process_room_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        处理房间数据，按房间分组并整理
        
        Args:
            raw_data: 原始数据列表
            
        Returns:
            处理后的房间数据
        """
        rooms_data = {}
        
        for record in raw_data:
            house_name = record.get('houseName', '')
            house_id = record.get('houseId')
            
            # 解析房间信息
            room_info = self.parse_room_info(house_name)
            
            # 如果房间不存在，创建房间记录
            if house_id not in rooms_data:
                rooms_data[house_id] = {
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
            tenant_info = {
                'id': record.get('id'),
                'guests_id': record.get('guestsId'),
                'tenant_name': record.get('tenantName'),
                'mobile': record.get('mobile'),
                'is_main': record.get('isMain', 0),
                'certificate_num': record.get('certificateNum'),
                'emergency_contact': record.get('emergencyContact'),
                'emergency_mobile': record.get('emergencyMobile'),
                'sign_status': record.get('signStatus'),
                'occupancy_flag': record.get('occupancyFlag')
            }
            
            rooms_data[house_id]['tenants'].append(tenant_info)
            
            # 区分主租户和合租户
            if tenant_info['is_main'] == 1:
                rooms_data[house_id]['main_tenant'] = tenant_info
            else:
                rooms_data[house_id]['co_tenants'].append(tenant_info)
        
        # 转换为列表并排序
        rooms_list = list(rooms_data.values())
        rooms_list.sort(key=lambda x: (x['building'], x['unit'], x['floor'], x['room_in_floor']))
        
        return {
            'total_rooms': len(rooms_list),
            'rooms': rooms_list,
            'timestamp': datetime.now().isoformat()
        }
    
    def save_data(self, data: Dict[str, Any], filename: str = None):
        """
        保存数据到文件
        
        Args:
            data: 要保存的数据
            filename: 文件名，默认使用时间戳
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rooms_data_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"数据已保存到: {filename}")
            
        except Exception as e:
            logger.error(f"保存数据失败: {str(e)}")
    
    def analyze_data(self, data: Dict[str, Any]):
        """
        分析房间数据并输出统计信息
        
        Args:
            data: 房间数据
        """
        rooms = data.get('rooms', [])
        
        logger.info("\n" + "="*50)
        logger.info("房间数据统计分析")
        logger.info("="*50)
        logger.info(f"总房间数: {data.get('total_rooms', 0)}")
        
        # 按楼层统计
        floor_stats = {}
        building_stats = {}
        occupancy_stats = {'occupied': 0, 'vacant': 0}
        
        for room in rooms:
            # 楼层统计
            floor = room['floor']
            if floor not in floor_stats:
                floor_stats[floor] = 0
            floor_stats[floor] += 1
            
            # 栋号统计
            building = room['building']
            if building not in building_stats:
                building_stats[building] = 0
            building_stats[building] += 1
            
            # 入住统计
            if room['tenants']:
                occupancy_stats['occupied'] += 1
            else:
                occupancy_stats['vacant'] += 1
        
        logger.info(f"入住房间: {occupancy_stats['occupied']}")
        logger.info(f"空闲房间: {occupancy_stats['vacant']}")
        
        logger.info("\n楼层分布:")
        for floor in sorted(floor_stats.keys()):
            logger.info(f"  {floor}楼: {floor_stats[floor]}间")
        
        logger.info("\n栋号分布:")
        for building in sorted(building_stats.keys()):
            logger.info(f"  A{building}栋: {building_stats[building]}间")
        
        logger.info("="*50)


def main():
    """主函数"""
    try:
        # 创建爬取器实例
        crawler = RoomsCrawler()
        
        # 爬取所有数据
        raw_data = crawler.crawl_all_pages()
        
        if raw_data:
            # 处理数据
            processed_data = crawler.process_room_data(raw_data)
            
            # 保存数据
            crawler.save_data(processed_data)
            
            # 分析数据
            crawler.analyze_data(processed_data)
        else:
            logger.warning("没有获取到任何数据")
            
    except KeyboardInterrupt:
        logger.info("用户中断了程序执行")
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main() 