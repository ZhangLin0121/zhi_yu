#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件 - 管理API认证信息和系统配置
"""

import os
from typing import Dict, Any

class Config:
    """应用配置类"""
    
    # API配置
    API_BASE_URL = "https://platform.inzhiyu.com/ams/api/contractEnterprise/guestsList"
    API_TIMEOUT = 30
    API_MAX_RETRIES = 3
    API_RETRY_DELAY = 2
    API_PAGE_SIZE = 50
    
    # 请求头配置
    API_HEADERS = {
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
    }
    
    # Cookie配置
    API_COOKIES = {
        'HWWAFSESID': '13733731437c2a43e3',
        'HWWAFSESTIME': '1751861002097',
        '_ams_token': 'web_cdpi6hgs9ez80cb8jit3emwv2wuh4uo5',
        '_common_token': 'web_cdpi6hgs9ez80cb8jit3emwv2wuh4uo5'
    }
    
    # API请求参数
    API_PAYLOAD_TEMPLATE = {
        "guestsName": "",
        "contractType": 3,
        "contractId": 1489
    }
    
    # 房间布局配置
    BUILDING_CONFIG = {
        'building': 'A4栋',
        'unit': 1,
        'total_floors': 20,
        'floor_1_rooms': 10,  # 1楼10间房
        'regular_floor_rooms': 12,  # 2-20楼每层12间
        'total_rooms': 10 + 19 * 12  # 238间
    }
    
    # Flask应用配置
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5001))
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # MongoDB配置
    MONGODB = {
        'host': os.getenv('MONGODB_HOST', 'localhost'),
        'port': int(os.getenv('MONGODB_PORT', 27017)),
        'database': os.getenv('MONGODB_DATABASE', 'room_management'),
        'username': os.getenv('MONGODB_USERNAME', ''),
        'password': os.getenv('MONGODB_PASSWORD', ''),
        'auth_source': os.getenv('MONGODB_AUTH_SOURCE', 'admin'),
        'connect_timeout': int(os.getenv('MONGODB_CONNECT_TIMEOUT', 10000)),
        'server_selection_timeout': int(os.getenv('MONGODB_SERVER_SELECTION_TIMEOUT', 5000)),
        'max_pool_size': int(os.getenv('MONGODB_MAX_POOL_SIZE', 50))
    }
    
    # 学生标签配置
    STUDENT_TAGS = {
        'default_tags': ['22级硕博士', '23级硕博士', '24级硕博士', '实习实践', '未分类'],
        'tag_colors': {
            '22级硕博士': '#FF6B6B',
            '23级硕博士': '#4ECDC4', 
            '24级硕博士': '#45B7D1',
            '实习实践': '#96CEB4',
            '未分类': '#FFEAA7'
        }
    }
    
    @classmethod
    def get_api_payload(cls, page_number: int = 1, page_size: int = None) -> Dict[str, Any]:
        """获取API请求载荷"""
        payload = cls.API_PAYLOAD_TEMPLATE.copy()
        payload.update({
            "pageNumber": page_number,
            "pageSize": page_size or cls.API_PAGE_SIZE
        })
        return payload
    
    @classmethod
    def update_cookies(cls, new_cookies: Dict[str, str]):
        """更新Cookie配置"""
        cls.API_COOKIES.update(new_cookies)
    
    @classmethod
    def update_tokens(cls, ams_token: str, common_token: str):
        """更新认证令牌"""
        cls.API_COOKIES.update({
            '_ams_token': ams_token,
            '_common_token': common_token
        }) 