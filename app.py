#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
房间分配可视化网页应用 - 动态数据版本
"""

from flask import Flask, render_template, jsonify, request
import logging
from datetime import datetime
from config import Config
from api_client import RoomsDataManager
from auth_manager import get_fresh_auth_info, update_auth_info
import threading
import time

app = Flask(__name__)
app.config['DEBUG'] = Config.DEBUG

# 配置日志
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# 初始化数据管理器
data_manager = RoomsDataManager()

# 全局变量用于跟踪自动认证状态
auto_auth_lock = threading.Lock()
last_auth_check = 0
auth_check_interval = 300  # 5分钟检查一次认证状态

# 新增：更主动的认证检查间隔（2分钟）
proactive_auth_check_interval = 120  # 2分钟主动检查一次

def check_and_refresh_auth():
    """检查并刷新认证信息"""
    global last_auth_check
    
    current_time = time.time()
    
    # 如果距离上次检查不足5分钟，跳过
    if current_time - last_auth_check < auth_check_interval:
        return True
    
    with auto_auth_lock:
        try:
            logger.info("检查认证状态...")
            
            # 尝试获取新的认证信息
            fresh_auth = get_fresh_auth_info()
            
            if fresh_auth:
                logger.info("获取到新的认证信息，正在更新...")
                if update_auth_info(fresh_auth):
                    logger.info("认证信息更新成功")
                    # 重新初始化数据管理器
                    global data_manager
                    data_manager = RoomsDataManager()
                    last_auth_check = current_time
                    return True
                else:
                    logger.error("认证信息更新失败")
                    return False
            else:
                logger.warning("未能获取到新的认证信息，使用现有认证信息")
                last_auth_check = current_time
                return True
                
        except Exception as e:
            logger.error(f"认证检查失败: {str(e)}")
            return False

def proactive_auth_check():
    """主动认证检查 - 更频繁的检查"""
    global last_auth_check
    
    current_time = time.time()
    
    # 每2分钟主动检查一次
    if current_time - last_auth_check < proactive_auth_check_interval:
        return True
    
    try:
        logger.info("执行主动认证检查...")
        
        # 尝试获取数据来验证认证有效性
        test_data = data_manager.generate_complete_layout()
        
        if test_data and test_data.get('rooms'):
            occupied_rooms = [r for r in test_data.get('rooms', []) if r.get('tenants')]
            
            # 如果入住房间数量正常，认证有效
            if len(occupied_rooms) > 100:
                logger.info(f"主动认证检查通过，当前 {len(occupied_rooms)} 个房间已入住")
                last_auth_check = current_time
                return True
            else:
                logger.warning(f"主动认证检查发现异常，只有 {len(occupied_rooms)} 个房间已入住，尝试刷新认证...")
                return check_and_refresh_auth()
        else:
            logger.warning("主动认证检查失败，无法获取数据，尝试刷新认证...")
            return check_and_refresh_auth()
            
    except Exception as e:
        logger.error(f"主动认证检查失败: {str(e)}")
        return check_and_refresh_auth()

def auto_authenticate_if_needed():
    """如果需要则自动认证"""
    try:
        # 先执行主动认证检查
        if not proactive_auth_check():
            logger.warning("主动认证检查失败，尝试强制刷新...")
            return check_and_refresh_auth()
        
        # 再次验证数据获取
        test_data = data_manager.generate_complete_layout()
        
        if test_data and test_data.get('rooms'):
            # 检查是否有入住数据
            occupied_rooms = [r for r in test_data.get('rooms', []) if r.get('tenants')]
            if len(occupied_rooms) > 100:
                logger.info(f"认证信息有效，已获取 {len(occupied_rooms)} 个有入住数据的房间")
                return True
            else:
                logger.warning(f"认证可能过期，只获取到 {len(occupied_rooms)} 个入住房间，尝试刷新认证...")
                return check_and_refresh_auth()
        
        # 如果没有入住数据或获取失败，尝试自动认证
        logger.info("当前认证可能无效，尝试自动获取新认证...")
        return check_and_refresh_auth()
        
    except Exception as e:
        logger.error(f"自动认证检查失败: {str(e)}")
        return check_and_refresh_auth()

def organize_rooms_by_floor(rooms):
    """按楼层组织房间数据"""
    floors = {}
    
    for room in rooms:
        floor = room['floor']
        if floor not in floors:
            floors[floor] = []
        floors[floor].append(room)
    
    # 每层房间按房间号排序
    for floor in floors:
        floors[floor].sort(key=lambda x: x['room_in_floor'])
    
    return floors

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/rooms')
def get_rooms_data():
    """获取房间数据API - 动态从外部API获取"""
    try:
        logger.info("开始获取房间数据...")
        
        # 自动检查和更新认证信息
        auto_authenticate_if_needed()
        
        # 从外部API获取实时数据
        data = data_manager.generate_complete_layout()
        
        if not data:
            logger.error("无法获取房间数据")
            return jsonify({'error': '无法获取房间数据'}), 500
        
        # 按楼层组织数据
        rooms = data.get('rooms', [])
        floors_data = organize_rooms_by_floor(rooms)
        
        # 统计入住情况
        occupied_rooms = [r for r in rooms if r.get('tenants')]
        
        logger.info(f"成功获取房间数据，共 {len(rooms)} 个房间，{len(occupied_rooms)} 个已入住")
        
        return jsonify({
            'total_rooms': data.get('total_rooms', 0),
            'floors': floors_data,
            'timestamp': data.get('timestamp', ''),
            'floor_numbers': sorted(floors_data.keys()),
            'layout_info': data.get('layout_info', {}),
            'occupied_count': len(occupied_rooms)
        })
        
    except Exception as e:
        logger.error(f"获取房间数据失败: {str(e)}")
        return jsonify({'error': f'获取房间数据失败: {str(e)}'}), 500

@app.route('/api/room/<house_id>')
def get_room_detail(house_id):
    """获取房间详细信息"""
    try:
        logger.info(f"获取房间详情: {house_id}")
        
        # 自动检查认证
        auto_authenticate_if_needed()
        
        # 获取完整数据
        data = data_manager.generate_complete_layout()
        
        if not data:
            return jsonify({'error': '无法获取房间数据'}), 500
        
        rooms = data.get('rooms', [])
        for room in rooms:
            if str(room['house_id']) == str(house_id):
                return jsonify(room)
        
        return jsonify({'error': '房间不存在'}), 404
        
    except Exception as e:
        logger.error(f"获取房间详情失败: {str(e)}")
        return jsonify({'error': f'获取房间详情失败: {str(e)}'}), 500

@app.route('/api/room/<house_id>', methods=['PUT'])
def update_room(house_id):
    """更新房间信息 - 注意：当前版本不支持更新外部API数据"""
    try:
        room_data = request.get_json()
        if not room_data:
            return jsonify({'error': '无效的请求数据'}), 400
        
        logger.warning(f"尝试更新房间 {house_id}，但当前版本不支持更新外部API数据")
        
        # 当前版本不支持更新外部API数据
        # 可以在这里添加更新逻辑，如果外部API支持的话
        
        return jsonify({
            'error': '当前版本不支持更新房间信息',
            'message': '数据来源于外部API，无法直接修改'
        }), 501
        
    except Exception as e:
        logger.error(f"更新房间信息失败: {str(e)}")
        return jsonify({'error': '更新失败'}), 500

@app.route('/api/search')
def search_rooms():
    """搜索房间"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'rooms': []})
        
        logger.info(f"搜索房间: {query}")
        
        # 获取完整数据
        data = data_manager.generate_complete_layout()
        
        if not data:
            return jsonify({'error': '无法获取房间数据'}), 500
        
        rooms = data.get('rooms', [])
        results = []
        
        query_lower = query.lower()
        
        for room in rooms:
            # 搜索房间号、租户姓名、手机号
            if (query_lower in room['room_number'].lower() or
                query_lower in room['house_name'].lower() or
                any(query_lower in tenant['tenant_name'].lower() or 
                    query_lower in tenant['mobile'] for tenant in room['tenants'])):
                results.append(room)
        
        logger.info(f"搜索完成，找到 {len(results)} 个结果")
        return jsonify({'rooms': results})
        
    except Exception as e:
        logger.error(f"搜索房间失败: {str(e)}")
        return jsonify({'error': f'搜索失败: {str(e)}'}), 500

@app.route('/api/refresh')
def refresh_data():
    """手动刷新数据"""
    try:
        logger.info("手动刷新数据...")
        
        # 强制检查认证信息
        global last_auth_check
        last_auth_check = 0  # 重置检查时间，强制重新认证
        
        # 自动检查和更新认证信息
        auth_success = auto_authenticate_if_needed()
        
        if not auth_success:
            logger.warning("认证更新失败，但继续尝试获取数据...")
        
        # 重新初始化数据管理器以清除可能的缓存
        global data_manager
        data_manager = RoomsDataManager()
        
        # 获取新数据
        data = data_manager.generate_complete_layout()
        
        if not data:
            return jsonify({'error': '刷新数据失败'}), 500
        
        # 统计入住情况
        occupied_rooms = [r for r in data.get('rooms', []) if r.get('tenants')]
        
        logger.info(f"数据刷新成功，{len(occupied_rooms)} 个房间已入住")
        return jsonify({
            'success': True,
            'message': f'数据刷新成功，{len(occupied_rooms)} 个房间已入住',
            'timestamp': data.get('timestamp', ''),
            'total_rooms': data.get('total_rooms', 0),
            'occupied_count': len(occupied_rooms),
            'auth_updated': auth_success
        })
        
    except Exception as e:
        logger.error(f"刷新数据失败: {str(e)}")
        return jsonify({'error': f'刷新数据失败: {str(e)}'}), 500

@app.route('/api/status')
def get_api_status():
    """获取API状态"""
    try:
        # 自动检查认证
        auth_status = auto_authenticate_if_needed()
        
        # 简单的健康检查
        data = data_manager.generate_complete_layout()
        
        if data:
            occupied_rooms = [r for r in data.get('rooms', []) if r.get('tenants')]
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'total_rooms': data.get('total_rooms', 0),
                'occupied_count': len(occupied_rooms),
                'last_update': data.get('timestamp', ''),
                'auth_status': 'valid' if auth_status else 'invalid'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '无法获取数据',
                'auth_status': 'invalid'
            }), 500
            
    except Exception as e:
        logger.error(f"API状态检查失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'auth_status': 'unknown'
        }), 500

@app.route('/api/rooms/details')
def get_all_rooms_details():
    """获取所有房间的详细信息（包括租户详细信息）"""
    try:
        logger.info("Fetching all rooms details...")
        
        # 获取完整的房间布局数据（包含详细信息）
        complete_data = data_manager.generate_complete_layout()
        if not complete_data:
            return jsonify({
                'success': False,
                'error': 'Failed to fetch rooms data'
            }), 500
        
        # 直接返回房间数据，因为generate_complete_layout已经包含了所有详细信息
        rooms_list = complete_data.get('rooms', [])
        
        logger.info(f"Successfully fetched details for {len(rooms_list)} rooms")
        return jsonify({
            'success': True,
            'rooms': rooms_list,
            'total_count': len(rooms_list),
            'timestamp': complete_data.get('timestamp')
        })
        
    except Exception as e:
        logger.error(f"Error in get_all_rooms_details: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/auth/update', methods=['POST'])
def update_auth():
    """更新认证信息"""
    try:
        auth_data = request.get_json()
        if not auth_data:
            return jsonify({'error': '无效的请求数据'}), 400
        
        # 尝试导入认证管理器
        try:
            from auth_manager import update_auth_info
            
            # 验证必要的认证信息
            required_fields = ['_ams_token', '_common_token']
            for field in required_fields:
                if field not in auth_data:
                    return jsonify({'error': f'缺少必要字段: {field}'}), 400
            
            # 更新认证信息
            if update_auth_info(auth_data):
                # 重新初始化数据管理器
                global data_manager
                data_manager = RoomsDataManager()
                
                logger.info("认证信息更新成功")
                return jsonify({
                    'success': True,
                    'message': '认证信息更新成功',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({'error': '认证信息保存失败'}), 500
                
        except ImportError:
            return jsonify({'error': '认证管理器不可用'}), 500
            
    except Exception as e:
        logger.error(f"更新认证信息失败: {str(e)}")
        return jsonify({'error': f'更新失败: {str(e)}'}), 500

@app.route('/api/auth/refresh', methods=['POST'])
def refresh_auth():
    """强制刷新认证信息"""
    try:
        logger.info("强制刷新认证信息...")
        
        # 重置认证检查时间，强制重新认证
        global last_auth_check
        last_auth_check = 0
        
        # 强制检查认证
        auth_success = check_and_refresh_auth()
        
        if auth_success:
            # 测试新认证信息
            test_data = data_manager.generate_complete_layout()
            occupied_rooms = [r for r in test_data.get('rooms', []) if r.get('tenants')] if test_data else []
            
            return jsonify({
                'success': True,
                'message': f'认证信息刷新成功，获取到 {len(occupied_rooms)} 个已入住房间',
                'timestamp': datetime.now().isoformat(),
                'occupied_count': len(occupied_rooms)
            })
        else:
            return jsonify({
                'success': False,
                'message': '认证信息刷新失败'
            }), 500
            
    except Exception as e:
        logger.error(f"刷新认证信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'刷新失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    # 启动应用
    logger.info("启动房间管理系统...")
    logger.info(f"调试模式: {Config.DEBUG}")
    logger.info(f"监听地址: {Config.HOST}:{Config.PORT}")
    
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG) 