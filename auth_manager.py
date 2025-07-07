#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证信息管理器 - 提供认证信息更新功能
"""

import json
import logging
import os
import time
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AuthManager:
    """认证信息管理器"""
    
    def __init__(self, auth_file: str = "auth_cache.json"):
        """
        初始化认证管理器
        
        Args:
            auth_file: 认证信息缓存文件路径
        """
        self.auth_file = auth_file
        self.last_update_time = None
        self.cached_auth = None
        self.load_cached_auth()
    
    def load_cached_auth(self) -> Optional[Dict[str, str]]:
        """加载缓存的认证信息"""
        try:
            if os.path.exists(self.auth_file):
                with open(self.auth_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cached_auth = data.get('auth_info', {})
                    self.last_update_time = data.get('update_time')
                    logger.info(f"加载缓存认证信息，更新时间: {self.last_update_time}")
                    return self.cached_auth
        except Exception as e:
            logger.warning(f"加载缓存认证信息失败: {str(e)}")
        
        return None
    
    def save_auth_info(self, auth_info: Dict[str, str]) -> bool:
        """
        保存认证信息到缓存文件
        
        Args:
            auth_info: 认证信息字典
            
        Returns:
            是否保存成功
        """
        try:
            data = {
                'auth_info': auth_info,
                'update_time': datetime.now().isoformat()
            }
            
            with open(self.auth_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.cached_auth = auth_info
            self.last_update_time = data['update_time']
            logger.info("认证信息已保存到缓存文件")
            return True
            
        except Exception as e:
            logger.error(f"保存认证信息失败: {str(e)}")
            return False
    
    def get_auth_info(self) -> Optional[Dict[str, str]]:
        """获取认证信息"""
        return self.cached_auth
    
    def is_auth_expired(self, max_age_hours: int = 24) -> bool:
        """
        检查认证信息是否过期
        
        Args:
            max_age_hours: 最大有效时间（小时）
            
        Returns:
            是否过期
        """
        if not self.last_update_time:
            return True
        
        try:
            update_time = datetime.fromisoformat(self.last_update_time)
            age_hours = (datetime.now() - update_time).total_seconds() / 3600
            return age_hours > max_age_hours
        except Exception:
            return True
    
    def update_auth_from_curl(self, curl_command: str) -> bool:
        """
        从curl命令中提取认证信息
        
        Args:
            curl_command: 包含认证信息的curl命令
            
        Returns:
            是否更新成功
        """
        try:
            # 提取Cookie头信息
            import re
            cookie_match = re.search(r'-H ["\']Cookie: ([^"\']+)["\']', curl_command)
            if not cookie_match:
                logger.error("无法从curl命令中找到Cookie信息")
                return False
            
            cookie_string = cookie_match.group(1)
            
            # 解析cookies
            auth_info = {}
            for cookie in cookie_string.split('; '):
                if '=' in cookie:
                    name, value = cookie.split('=', 1)
                    if name.strip() in ['_ams_token', '_common_token', 'HWWAFSESID', 'HWWAFSESTIME']:
                        auth_info[name.strip()] = value.strip()
            
            if auth_info:
                self.save_auth_info(auth_info)
                logger.info("从curl命令中成功提取并保存认证信息")
                return True
            else:
                logger.error("未能从curl命令中提取到有效的认证信息")
                return False
                
        except Exception as e:
            logger.error(f"从curl命令提取认证信息失败: {str(e)}")
            return False
    
    def print_update_instructions(self):
        """打印更新认证信息的说明"""
        instructions = """
=== 认证信息更新说明 ===

当API返回401错误时，说明认证信息已过期，需要手动更新。

更新步骤：
1. 打开浏览器，访问 https://platform.inzhiyu.com/
2. 使用账号密码登录
3. 登录成功后，打开浏览器开发者工具（F12）
4. 切换到Network标签页
5. 刷新页面或进行任何操作触发API请求
6. 找到任何一个对 platform.inzhiyu.com 的请求
7. 右键点击请求，选择"Copy as cURL"
8. 将复制的curl命令粘贴到程序中

或者，您可以直接提供以下认证信息：
- _ams_token: 
- _common_token: 
- HWWAFSESID: 
- HWWAFSESTIME: 

程序会自动保存这些信息以供后续使用。
        """
        print(instructions)


# 全局认证管理器实例
auth_manager = AuthManager()


def get_fresh_auth_info() -> Optional[Dict[str, str]]:
    """
    获取最新的认证信息
    
    Returns:
        认证信息字典，失败时返回None
    """
    # 检查缓存的认证信息
    cached_auth = auth_manager.get_auth_info()
    
    if cached_auth and not auth_manager.is_auth_expired():
        logger.info("使用缓存的认证信息")
        return cached_auth
    
    # 认证信息过期或不存在，提示用户更新
    logger.warning("认证信息过期或不存在，需要手动更新")
    auth_manager.print_update_instructions()
    
    return None


def update_auth_info(auth_info: Dict[str, str]) -> bool:
    """
    更新认证信息
    
    Args:
        auth_info: 认证信息字典
        
    Returns:
        是否更新成功
    """
    return auth_manager.save_auth_info(auth_info)


if __name__ == "__main__":
    # 测试认证管理器
    logging.basicConfig(level=logging.INFO)
    
    # 示例：更新认证信息
    sample_auth = {
        '_ams_token': 'web_cdpi6hgs9ez80cb8jit3emwv2wuh4uo5',
        '_common_token': 'web_cdpi6hgs9ez80cb8jit3emwv2wuh4uo5',
        'HWWAFSESID': '13733731437c2a43e3',
        'HWWAFSESTIME': '1751861002097'
    }
    
    if update_auth_info(sample_auth):
        print("认证信息更新成功")
    
    # 测试获取认证信息
    auth_info = get_fresh_auth_info()
    if auth_info:
        print("当前认证信息:")
        print(json.dumps(auth_info, indent=2))
    else:
        print("无可用的认证信息") 