#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
房间分配可视化网页应用 - 动态数据版本
"""

from flask import Flask, render_template, jsonify, request
import logging
import json
from datetime import datetime
from bson import ObjectId
from config import Config
from api_client import RoomsDataManager
from auth_manager import get_fresh_auth_info, update_auth_info
import threading
import time

app = Flask(__name__)
app.config['DEBUG'] = Config.DEBUG

# 自定义JSON编码器处理MongoDB ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

# MongoDB ObjectId序列化函数
def convert_objectid(obj):
    """递归转换ObjectId为字符串"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    else:
        return obj

# 配置日志
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# 初始化数据管理器
data_manager = RoomsDataManager()

# 全局变量用于跟踪认证状态
auto_auth_lock = threading.Lock()
last_auth_check = 0
auth_check_interval = 3600  # 1小时检查一次认证状态（降低频率）

def check_and_refresh_auth():
    """检查并刷新认证信息"""
    global last_auth_check
    
    current_time = time.time()
    
    # 如果距离上次检查不足1小时，跳过
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

def auth_check_on_page_access():
    """仅在页面访问时进行认证检查"""
    try:
        logger.info("页面访问时进行认证检查...")
        
        # 尝试获取数据来验证认证有效性
        test_data = data_manager.generate_complete_layout()
        
        if test_data and test_data.get('rooms'):
            occupied_rooms = [r for r in test_data.get('rooms', []) if r.get('tenants')]
            
            # 如果入住房间数量正常，认证有效
            if len(occupied_rooms) > 100:
                logger.info(f"认证检查通过，当前 {len(occupied_rooms)} 个房间已入住")
                return True
            else:
                logger.warning(f"认证检查发现异常，只有 {len(occupied_rooms)} 个房间已入住，尝试刷新认证...")
                return check_and_refresh_auth()
        else:
            logger.warning("认证检查失败，无法获取数据，尝试刷新认证...")
            return check_and_refresh_auth()
            
    except Exception as e:
        logger.error(f"认证检查失败: {str(e)}")
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
        floors[floor].sort(key=lambda x: x.get('room_number', ''))
    
    return floors

@app.route('/')
def index():
    """主页 - 仅在此处进行认证检查"""
    # 仅在访问主页时进行认证检查
    auth_check_on_page_access()
    return render_template('index.html')

@app.route('/api/rooms')
def get_rooms_data():
    """获取房间数据API - 动态从外部API获取"""
    try:
        logger.info("开始获取房间数据...")
        
        # 移除自动认证检查，直接获取数据
        # 如果认证过期，API客户端会自动处理401错误
        
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
        
        response_data = {
            'total_rooms': data.get('total_rooms', 0),
            'floors': floors_data,
            'timestamp': data.get('timestamp', ''),
            'floor_numbers': sorted(floors_data.keys()),
            'layout_info': data.get('layout_info', {}),
            'occupied_count': len(occupied_rooms)
        }
        
        # 转换ObjectId
        response_data = convert_objectid(response_data)
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"获取房间数据失败: {str(e)}")
        return jsonify({'error': f'获取房间数据失败: {str(e)}'}), 500

@app.route('/api/room/<house_id>')
def get_room_detail(house_id):
    """获取房间详细信息 - 优先从数据库读取"""
    try:
        logger.info(f"获取房间详情: {house_id}")
        
        # 优先尝试从数据库获取房间详情
        room_detail = data_manager.get_room_detail_from_db(house_id)
        
        if room_detail:
            logger.info(f"从数据库获取房间 {house_id} 详情成功")
            room_detail = convert_objectid(room_detail)
            return jsonify(room_detail)
        
        # 如果数据库中没有，再从API获取
        logger.warning(f"数据库中未找到房间 {house_id}，尝试从API获取...")
        data = data_manager.generate_complete_layout()
        
        if not data:
            return jsonify({'error': '无法获取房间数据'}), 500
        
        rooms = data.get('rooms', [])
        for room in rooms:
            if str(room['house_id']) == str(house_id):
                room = convert_objectid(room)
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
        results = convert_objectid(results)
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
        
        # 强制检查认证信息
        auth_success = check_and_refresh_auth()
        
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
        # 移除自动认证检查，直接获取数据
        
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
                'auth_status': 'valid'
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

# ==================== 标签管理API ====================

@app.route('/api/tags')
def get_available_tags():
    """获取可用的标签列表"""
    try:
        tags = data_manager.get_available_tags()
        tag_stats = data_manager.get_tag_statistics()
        
        # 从配置中获取标签颜色
        tag_colors = Config.STUDENT_TAGS.get('tag_colors', {})
        
        return jsonify({
            'success': True,
            'tags': tags,
            'statistics': tag_stats,
            'colors': tag_colors
        })
        
    except Exception as e:
        logger.error(f"获取标签列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取标签列表失败: {str(e)}'
        }), 500

@app.route('/api/tags/statistics')
def get_tag_statistics():
    """获取标签统计信息"""
    try:
        stats = data_manager.get_tag_statistics()
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"获取标签统计失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取标签统计失败: {str(e)}'
        }), 500

@app.route('/api/students/<student_id>/tag', methods=['PUT'])
def update_student_tag(student_id):
    """更新学生标签"""
    try:
        data = request.get_json()
        if not data or 'tag' not in data:
            return jsonify({
                'success': False,
                'error': '缺少标签参数'
            }), 400
        
        tag = data['tag']
        
        # 验证标签是否有效
        available_tags = data_manager.get_available_tags()
        if tag not in available_tags:
            return jsonify({
                'success': False,
                'error': f'无效的标签: {tag}'
            }), 400
        
        # 更新标签
        success = data_manager.update_student_tag(student_id, tag)
        
        if success:
            logger.info(f"学生 {student_id} 标签更新为: {tag}")
            return jsonify({
                'success': True,
                'message': f'标签更新成功: {tag}',
                'student_id': student_id,
                'tag': tag
            })
        else:
            return jsonify({
                'success': False,
                'error': '标签更新失败'
            }), 500
            
    except Exception as e:
        logger.error(f"更新学生标签失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'更新失败: {str(e)}'
        }), 500

@app.route('/api/students/tag/<tag>')
def get_students_by_tag(tag):
    """根据标签获取学生列表"""
    try:
        students = data_manager.get_students_by_tag(tag)
        
        response_data = {
            'success': True,
            'tag': tag,
            'students': students,
            'count': len(students)
        }
        
        # 转换ObjectId
        response_data = convert_objectid(response_data)
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"根据标签获取学生失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取学生失败: {str(e)}'
        }), 500

@app.route('/api/students/batch-tag', methods=['PUT'])
def batch_update_student_tags():
    """批量更新学生标签"""
    try:
        data = request.get_json()
        if not data or 'updates' not in data:
            return jsonify({
                'success': False,
                'error': '缺少更新数据'
            }), 400
        
        updates = data['updates']  # [{'student_id': 'xxx', 'tag': 'yyy'}, ...]
        
        if not isinstance(updates, list):
            return jsonify({
                'success': False,
                'error': '更新数据格式错误'
            }), 400
        
        # 验证标签
        available_tags = data_manager.get_available_tags()
        
        success_count = 0
        failed_updates = []
        
        for update in updates:
            student_id = update.get('student_id')
            tag = update.get('tag')
            
            if not student_id or not tag:
                failed_updates.append({
                    'student_id': student_id,
                    'error': '缺少学生ID或标签'
                })
                continue
            
            if tag not in available_tags:
                failed_updates.append({
                    'student_id': student_id,
                    'error': f'无效标签: {tag}'
                })
                continue
            
            # 更新标签
            if data_manager.update_student_tag(student_id, tag):
                success_count += 1
            else:
                failed_updates.append({
                    'student_id': student_id,
                    'error': '更新失败'
                })
        
        logger.info(f"批量更新完成: {success_count} 成功, {len(failed_updates)} 失败")
        
        return jsonify({
            'success': True,
            'message': f'批量更新完成: {success_count} 成功, {len(failed_updates)} 失败',
            'success_count': success_count,
            'failed_count': len(failed_updates),
            'failed_updates': failed_updates
        })
        
    except Exception as e:
        logger.error(f"批量更新学生标签失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'批量更新失败: {str(e)}'
        }), 500

@app.route('/api/sync', methods=['POST'])
def sync_data():
    """同步数据从外部API到数据库"""
    try:
        logger.info("开始同步数据...")
        
        # 从外部API获取完整数据并存入数据库
        data = data_manager.generate_complete_layout()
        
        if not data:
            logger.error("数据同步失败，无法获取外部API数据")
            return jsonify({'error': '数据同步失败', 'success': False}), 500
        
        logger.info(f"数据同步成功，共同步 {len(data.get('rooms', []))} 个房间")
        
        response_data = {
            'success': True,
            'message': '数据同步成功',
            'synced_rooms': len(data.get('rooms', [])),
            'timestamp': data.get('timestamp', datetime.now().isoformat())
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"数据同步失败: {str(e)}")
        return jsonify({'error': f'数据同步失败: {str(e)}', 'success': False}), 500

@app.route('/api/rooms/with-tags')
def get_rooms_with_tags():
    """获取带标签信息的房间数据 - 优先从数据库读取"""
    try:
        logger.info("获取带标签的房间数据...")
        
        # 优先从数据库获取数据
        data = data_manager.get_rooms_with_tags()
        
        if not data or not data.get('rooms'):
            logger.warning("数据库中无数据，尝试从API获取并同步...")
            # 如果数据库中没有数据，则从API获取并同步
            data = data_manager.generate_complete_layout()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': '无法获取房间数据'
                }), 500
        
        # 按楼层组织数据
        rooms = data.get('rooms', [])
        floors_data = organize_rooms_by_floor(rooms)
        
        # 统计标签信息
        tag_stats = data.get('tag_statistics', {})
        
        logger.info(f"成功获取带标签的房间数据，共 {len(rooms)} 个房间")
        
        response_data = {
            'success': True,
            'total_rooms': data.get('total_rooms', 0),
            'occupied_count': data.get('occupied_count', 0),
            'vacant_count': data.get('vacant_count', 0),
            'floors': floors_data,
            'timestamp': data.get('timestamp', ''),
            'floor_numbers': sorted(floors_data.keys()),
            'layout_info': data.get('layout_info', {}),
            'tag_statistics': tag_stats
        }
        
        # 转换ObjectId
        response_data = convert_objectid(response_data)
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"获取带标签房间数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取数据失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    # 启动应用
    logger.info("启动房间管理系统...")
    logger.info(f"调试模式: {Config.DEBUG}")
    logger.info(f"监听地址: {Config.HOST}:{Config.PORT}")
    
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG) 