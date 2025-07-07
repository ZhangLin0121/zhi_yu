#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
强制认证更新脚本
确保服务器能获取到真实的入住数据
"""

import json
import sys
import os
from datetime import datetime

def update_auth_with_verified_tokens():
    """使用经过验证的认证信息强制更新"""
    
    print("🔐 开始强制更新认证信息...")
    
    # 经过本地验证的有效认证信息（2025-07-07 测试有效，155个房间已入住）
    verified_auth = {
        "_ams_token": "web_cdpi6hgs9ez80cb8jit3emwv2wuh4uo5",
        "_common_token": "web_cdpi6hgs9ez80cb8jit3emwv2wuh4uo5",
        "HWWAFSESID": "13733731437c2a43e3",
        "HWWAFSESTIME": "1751861002097"
    }
    
    try:
        # 导入认证管理器
        from auth_manager import update_auth_info
        
        # 强制更新认证信息
        success = update_auth_info(verified_auth)
        
        if success:
            print("✅ 认证信息更新成功")
            
            # 立即验证认证有效性
            print("🧪 验证认证有效性...")
            
            from api_client import RoomsDataManager
            manager = RoomsDataManager()
            data = manager.generate_complete_layout()
            
            if data:
                rooms = data.get('rooms', [])
                occupied_rooms = [r for r in rooms if r.get('tenants')]
                
                print(f"📊 数据验证结果:")
                print(f"  总房间数: {len(rooms)}")
                print(f"  已入住房间: {len(occupied_rooms)}")
                print(f"  入住率: {len(occupied_rooms)/len(rooms)*100:.1f}%")
                
                if len(occupied_rooms) > 100:
                    print("")
                    print("🎉 认证验证成功！")
                    print(f"✅ 成功获取到 {len(occupied_rooms)} 个已入住房间的真实数据")
                    
                    # 显示一些入住房间示例
                    print("")
                    print("🏠 入住房间示例:")
                    for i, room in enumerate(occupied_rooms[:5]):
                        tenants = room.get('tenants', [])
                        tenant_names = [t.get('tenant_name', '未知') for t in tenants]
                        print(f"  - {room.get('room_number', '未知')}: {len(tenants)}人 ({', '.join(tenant_names[:2])})")
                    
                    return True
                else:
                    print("❌ 认证验证失败：入住房间数量异常")
                    return False
            else:
                print("❌ 认证验证失败：无法获取数据")
                return False
        else:
            print("❌ 认证信息更新失败")
            return False
            
    except Exception as e:
        print(f"❌ 强制认证更新失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 强制认证更新脚本启动")
    print("=" * 50)
    
    # 检查当前目录
    if not os.path.exists('auth_manager.py'):
        print("❌ 错误：请在项目根目录下运行此脚本")
        sys.exit(1)
    
    # 执行强制认证更新
    success = update_auth_with_verified_tokens()
    
    if success:
        print("")
        print("🎯 强制认证更新完成！")
        print("✅ 服务器现在可以获取到真实的入住数据")
        print("")
        print("📋 下一步：")
        print("1. 重启应用程序")
        print("2. 访问 http://服务器IP:5001 验证数据")
        print("3. 确认页面显示155个已入住房间")
    else:
        print("")
        print("❌ 强制认证更新失败")
        print("🔧 请检查：")
        print("1. 网络连接是否正常")
        print("2. 依赖模块是否完整")
        print("3. 认证信息是否已过期")

if __name__ == "__main__":
    main() 