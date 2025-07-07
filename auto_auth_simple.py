#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版自动认证模块 - 使用requests模拟登录
"""

import requests
import json
import logging
import time
import re
from typing import Dict, Optional
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class SimpleAutoAuthenticator:
    """简化版自动认证器"""
    
    def __init__(self, username: str = "18871627553", password: str = "zywl1212"):
        """
        初始化认证器
        
        Args:
            username: 登录用户名
            password: 登录密码
        """
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.setup_session()
    
    def setup_session(self):
        """设置会话"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def get_login_page(self) -> bool:
        """获取登录页面"""
        try:
            response = self.session.get('https://platform.inzhiyu.com/')
            if response.status_code == 200:
                logger.info("成功获取登录页面")
                return True
            else:
                logger.error(f"获取登录页面失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"获取登录页面时发生错误: {str(e)}")
            return False
    
    def login(self) -> bool:
        """执行登录"""
        try:
            # 首先获取登录页面
            if not self.get_login_page():
                return False
            
            # 准备登录数据
            # 这里我们需要模拟之前观察到的登录请求
            login_url = "https://platform.inzhiyu.com/apiv3/auth/Login"
            
            # 计算密码MD5（根据之前观察到的请求）
            import hashlib
            password_md5 = hashlib.md5(self.password.encode()).hexdigest().upper()
            
            # 构建登录参数
            login_params = {
                'id': self.username,
                'pwd': password_md5,
                'checkcode': '013751',  # 这可能需要动态获取
                'opt': '3'
            }
            
            # 发送登录请求
            response = self.session.get(login_url, params=login_params)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success', False):
                    logger.info("登录成功")
                    return True
                else:
                    logger.error(f"登录失败: {result.get('message', '未知错误')}")
                    return False
            else:
                logger.error(f"登录请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"登录过程中发生错误: {str(e)}")
            return False
    
    def get_auth_info(self) -> Optional[Dict[str, str]]:
        """获取认证信息"""
        try:
            # 执行登录
            if not self.login():
                return None
            
            # 提取cookies中的认证信息
            auth_info = {}
            
            for cookie in self.session.cookies:
                if cookie.name in ['_ams_token', '_common_token', 'HWWAFSESID', 'HWWAFSESTIME']:
                    auth_info[cookie.name] = cookie.value
            
            # 检查是否获取到必要的认证信息
            if '_ams_token' in auth_info and '_common_token' in auth_info:
                logger.info("成功获取认证信息")
                return auth_info
            else:
                logger.error("未能获取到完整的认证信息")
                return None
                
        except Exception as e:
            logger.error(f"获取认证信息时发生错误: {str(e)}")
            return None
    
    def test_auth_info(self, auth_info: Dict[str, str]) -> bool:
        """测试认证信息是否有效"""
        try:
            # 创建测试会话
            test_session = requests.Session()
            
            # 设置cookies
            for name, value in auth_info.items():
                test_session.cookies.set(name, value)
            
            # 设置请求头
            test_session.headers.update({
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
            })
            
            # 测试API请求
            payload = {
                "guestsName": "",
                "contractType": 3,
                "contractId": 1489,
                "pageNumber": 1,
                "pageSize": 5
            }
            
            response = test_session.post(
                "https://platform.inzhiyu.com/ams/api/contractEnterprise/guestsList",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    logger.info("认证信息测试成功")
                    return True
            
            logger.error(f"认证信息测试失败: {response.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"测试认证信息时发生错误: {str(e)}")
            return False


def get_fresh_auth_info() -> Optional[Dict[str, str]]:
    """
    获取最新的认证信息（简化版）
    
    Returns:
        认证信息字典，失败时返回None
    """
    try:
        # 由于简化版实现复杂度较高，我们暂时返回None
        # 让系统使用配置文件中的认证信息
        logger.info("简化版自动认证暂不可用，请手动更新认证信息")
        return None
        
    except Exception as e:
        logger.error(f"获取认证信息失败: {str(e)}")
        return None


if __name__ == "__main__":
    # 测试简化版自动认证
    logging.basicConfig(level=logging.INFO)
    
    auth_info = get_fresh_auth_info()
    if auth_info:
        print("成功获取认证信息:")
        print(json.dumps(auth_info, indent=2))
    else:
        print("获取认证信息失败，请手动更新配置文件") 