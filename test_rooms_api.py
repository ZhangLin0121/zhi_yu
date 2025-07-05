#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
房间入住信息API测试脚本
"""

import requests
import json

def test_rooms_api():
    """测试房间入住信息API请求"""
    
    url = "https://platform.inzhiyu.com/ams/api/contractEnterprise/guestsList"
    
    headers = {
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
    
    cookies = {
        'HWWAFSESID': '26cf673e248a27b3a5',
        'HWWAFSESTIME': '1751609522843',
        '_ams_token': 'web_bgd6s9lz980w7c45z8gvkhrd5spkd2mw',
        '_common_token': 'web_bgd6s9lz980w7c45z8gvkhrd5spkd2mw'
    }
    
    payload = {
        "pageNumber": 1,
        "pageSize": 50,
        "guestsName": "",
        "contractType": 3,
        "contractId": 1489
    }
    
    try:
        print("发送房间API测试请求...")
        response = requests.post(url, json=payload, headers=headers, cookies=cookies, timeout=30)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("请求成功！")
            print(f"响应数据结构: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # 分析响应结构
            if data.get('success') or data.get('code') == 200:
                # 尝试不同的数据路径
                records = None
                total = 0
                
                if 'data' in data:
                    if isinstance(data['data'], dict):
                        records = data['data'].get('records') or data['data'].get('list') or data['data'].get('items')
                        total = data['data'].get('total', 0)
                    elif isinstance(data['data'], list):
                        records = data['data']
                        total = len(records)
                
                if records:
                    print(f"\n总记录数: {total}")
                    print(f"当前页记录数: {len(records)}")
                    
                    if records:
                        print(f"第一条记录示例: {json.dumps(records[0], ensure_ascii=False, indent=2)}")
                        
                        # 分析字段
                        if isinstance(records[0], dict):
                            print(f"记录字段: {list(records[0].keys())}")
                else:
                    print("未找到记录数据，完整响应:")
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                    
        else:
            print(f"请求失败: {response.text}")
            
    except Exception as e:
        print(f"请求出错: {str(e)}")

if __name__ == "__main__":
    test_rooms_api() 