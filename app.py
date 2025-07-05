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

app = Flask(__name__)
app.config['DEBUG'] = Config.DEBUG

# 配置日志
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# 初始化数据管理器
data_manager = RoomsDataManager()

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
        
        # 从外部API获取实时数据
        data = data_manager.generate_complete_layout()
        
        if not data:
            logger.error("无法获取房间数据")
            return jsonify({'error': '无法获取房间数据'}), 500
        
        # 按楼层组织数据
        rooms = data.get('rooms', [])
        floors_data = organize_rooms_by_floor(rooms)
        
        logger.info(f"成功获取房间数据，共 {len(rooms)} 个房间")
        
        return jsonify({
            'total_rooms': data.get('total_rooms', 0),
            'floors': floors_data,
            'timestamp': data.get('timestamp', ''),
            'floor_numbers': sorted(floors_data.keys()),
            'layout_info': data.get('layout_info', {})
        })
        
    except Exception as e:
        logger.error(f"获取房间数据失败: {str(e)}")
        return jsonify({'error': f'获取房间数据失败: {str(e)}'}), 500

@app.route('/api/room/<house_id>')
def get_room_detail(house_id):
    """获取房间详细信息"""
    try:
        logger.info(f"获取房间详情: {house_id}")
        
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
        
        # 重新初始化数据管理器以清除可能的缓存
        global data_manager
        data_manager = RoomsDataManager()
        
        # 获取新数据
        data = data_manager.generate_complete_layout()
        
        if not data:
            return jsonify({'error': '刷新数据失败'}), 500
        
        logger.info("数据刷新成功")
        return jsonify({
            'success': True,
            'message': '数据刷新成功',
            'timestamp': data.get('timestamp', ''),
            'total_rooms': data.get('total_rooms', 0)
        })
        
    except Exception as e:
        logger.error(f"刷新数据失败: {str(e)}")
        return jsonify({'error': f'刷新数据失败: {str(e)}'}), 500

@app.route('/api/status')
def get_api_status():
    """获取API状态"""
    try:
        # 简单的健康检查
        data = data_manager.generate_complete_layout()
        
        if data:
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'total_rooms': data.get('total_rooms', 0),
                'last_update': data.get('timestamp', '')
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '无法获取数据'
            }), 500
            
    except Exception as e:
        logger.error(f"API状态检查失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
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

if __name__ == '__main__':
    # 启动应用
    logger.info("启动房间管理系统...")
    logger.info(f"调试模式: {Config.DEBUG}")
    logger.info(f"监听地址: {Config.HOST}:{Config.PORT}")
    
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG) 