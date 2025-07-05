#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
房间分配可视化网页应用
"""

from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime
import logging

app = Flask(__name__)
app.config['DEBUG'] = True

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_rooms_data():
    """加载房间数据"""
    # 优先查找完整布局文件
    complete_files = [f for f in os.listdir('.') if f.startswith('complete_rooms_layout_') and f.endswith('.json')]
    
    if complete_files:
        # 选择最新的完整布局文件
        latest_file = sorted(complete_files)[-1]
        logger.info(f"加载完整房间布局文件: {latest_file}")
    else:
        # 查找普通房间数据文件
        json_files = [f for f in os.listdir('.') if f.startswith('rooms_data_') and f.endswith('.json')]
        
        if not json_files:
            logger.error("未找到房间数据文件！")
            return None
        
        # 选择最新的文件
        latest_file = sorted(json_files)[-1]
        logger.info(f"加载房间数据文件: {latest_file}")
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载房间数据失败: {str(e)}")
        return None

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
    """获取房间数据API"""
    data = load_rooms_data()
    if not data:
        return jsonify({'error': '无法加载房间数据'}), 500
    
    # 按楼层组织数据
    rooms = data.get('rooms', [])
    floors_data = organize_rooms_by_floor(rooms)
    
    return jsonify({
        'total_rooms': data.get('total_rooms', 0),
        'floors': floors_data,
        'timestamp': data.get('timestamp', ''),
        'floor_numbers': sorted(floors_data.keys())
    })

@app.route('/api/room/<int:house_id>')
def get_room_detail(house_id):
    """获取房间详细信息"""
    data = load_rooms_data()
    if not data:
        return jsonify({'error': '无法加载房间数据'}), 500
    
    rooms = data.get('rooms', [])
    for room in rooms:
        if room['house_id'] == house_id:
            return jsonify(room)
    
    return jsonify({'error': '房间不存在'}), 404

@app.route('/api/search')
def search_rooms():
    """搜索房间"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'rooms': []})
    
    data = load_rooms_data()
    if not data:
        return jsonify({'error': '无法加载房间数据'}), 500
    
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
    
    return jsonify({'rooms': results})

if __name__ == '__main__':
    # 生产环境配置
    app.run(host='0.0.0.0', port=5001, debug=False) 