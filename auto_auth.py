#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动认证模块 - 自动登录并获取最新认证信息
"""

import requests
import json
import logging
import time
import re
from typing import Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)


class AutoAuthenticator:
    """自动认证器 - 自动登录并获取认证信息"""
    
    def __init__(self, username: str = "18871627553", password: str = "zywl1212"):
        """
        初始化自动认证器
        
        Args:
            username: 登录用户名
            password: 登录密码
        """
        self.username = username
        self.password = password
        self.login_url = "https://platform.inzhiyu.com/"
        self.driver = None
        
    def setup_driver(self) -> bool:
        """设置Chrome驱动"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无头模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36')
            
            # 尝试使用系统Chrome驱动
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                return True
            except WebDriverException:
                logger.warning("系统Chrome驱动不可用，尝试使用ChromeDriverManager")
                # 如果系统驱动不可用，尝试使用webdriver-manager
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    return True
                except Exception as e:
                    logger.error(f"无法设置Chrome驱动: {str(e)}")
                    return False
                    
        except Exception as e:
            logger.error(f"设置驱动失败: {str(e)}")
            return False
    
    def login_and_get_auth(self) -> Optional[Dict[str, str]]:
        """
        自动登录并获取认证信息
        
        Returns:
            包含认证信息的字典，失败时返回None
        """
        if not self.setup_driver():
            logger.error("无法设置浏览器驱动")
            return None
            
        try:
            logger.info("开始自动登录...")
            
            # 访问登录页面
            self.driver.get(self.login_url)
            
            # 等待页面加载
            wait = WebDriverWait(self.driver, 10)
            
            # 等待用户名输入框
            username_input = wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='请输入注册邮箱或手机号']"))
            )
            
            # 输入用户名
            username_input.clear()
            username_input.send_keys(self.username)
            
            # 等待密码输入框
            password_input = wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='请输入密码或首次邀请码']"))
            )
            
            # 输入密码
            password_input.clear()
            password_input.send_keys(self.password)
            
            # 点击登录按钮
            login_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '登录')]"))
            )
            login_button.click()
            
            # 等待登录完成（URL变化）
            wait.until(lambda driver: "login" not in driver.current_url)
            
            # 等待一段时间确保认证信息加载完成
            time.sleep(3)
            
            # 获取cookies
            cookies = self.driver.get_cookies()
            
            # 提取认证信息
            auth_info = {}
            for cookie in cookies:
                name = cookie['name']
                value = cookie['value']
                
                if name in ['_ams_token', '_common_token', 'HWWAFSESID', 'HWWAFSESTIME']:
                    auth_info[name] = value
            
            # 检查是否获取到必要的认证信息
            if '_ams_token' in auth_info and '_common_token' in auth_info:
                logger.info("成功获取认证信息")
                return auth_info
            else:
                logger.error("未能获取到完整的认证信息")
                return None
                
        except TimeoutException:
            logger.error("登录超时")
            return None
        except Exception as e:
            logger.error(f"登录过程中发生错误: {str(e)}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
    
    def test_auth_info(self, auth_info: Dict[str, str]) -> bool:
        """
        测试认证信息是否有效
        
        Args:
            auth_info: 认证信息字典
            
        Returns:
            认证信息是否有效
        """
        try:
            # 构建cookies字符串
            cookies = "; ".join([f"{k}={v}" for k, v in auth_info.items()])
            
            # 测试API请求
            headers = {
                'Cookie': cookies,
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
            }
            
            payload = {
                "guestsName": "",
                "contractType": 3,
                "contractId": 1489,
                "pageNumber": 1,
                "pageSize": 5
            }
            
            response = requests.post(
                "https://platform.inzhiyu.com/ams/api/contractEnterprise/guestsList",
                headers=headers,
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
    获取最新的认证信息
    
    Returns:
        认证信息字典，失败时返回None
    """
    authenticator = AutoAuthenticator()
    
    # 尝试自动登录获取认证信息
    auth_info = authenticator.login_and_get_auth()
    
    if auth_info:
        # 测试认证信息是否有效
        if authenticator.test_auth_info(auth_info):
            return auth_info
        else:
            logger.error("获取的认证信息无效")
            return None
    else:
        logger.error("无法获取认证信息")
        return None


if __name__ == "__main__":
    # 测试自动认证
    logging.basicConfig(level=logging.INFO)
    
    auth_info = get_fresh_auth_info()
    if auth_info:
        print("成功获取认证信息:")
        print(json.dumps(auth_info, indent=2))
    else:
        print("获取认证信息失败") 