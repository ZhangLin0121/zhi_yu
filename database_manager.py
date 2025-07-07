"""
数据库管理模块
负责MongoDB数据存储和标签管理
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from config import Config

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        """初始化数据库连接"""
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.rooms_collection: Optional[Collection] = None
        self.students_collection: Optional[Collection] = None
        self.tags_collection: Optional[Collection] = None
        self.connect()
    
    def connect(self):
        """连接到MongoDB"""
        try:
            # 从配置文件获取MongoDB连接信息
            mongo_config = getattr(Config, 'MONGODB', {
                'host': 'localhost',
                'port': 27017,
                'database': 'room_management'
            })
            
            # 创建MongoDB客户端
            self.client = MongoClient(
                host=mongo_config.get('host', 'localhost'),
                port=mongo_config.get('port', 27017),
                serverSelectionTimeoutMS=5000,  # 5秒超时
                connectTimeoutMS=10000,  # 10秒连接超时
                maxPoolSize=50
            )
            
            # 测试连接
            self.client.admin.command('ping')
            logger.info("MongoDB连接成功")
            
            # 获取数据库
            self.db = self.client[mongo_config.get('database', 'room_management')]
            
            # 获取集合
            self.rooms_collection = self.db['rooms']
            self.students_collection = self.db['students']
            self.tags_collection = self.db['tags']
            
            # 创建索引
            self._create_indexes()
            
        except ConnectionFailure as e:
            logger.error(f"MongoDB连接失败: {e}")
            raise
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def _create_indexes(self):
        """创建必要的索引"""
        try:
            # 房间集合索引
            self.rooms_collection.create_index([("room_number", ASCENDING)], unique=True)
            self.rooms_collection.create_index([("building", ASCENDING), ("floor", ASCENDING)])
            self.rooms_collection.create_index([("updated_at", DESCENDING)])
            
            # 学生集合索引
            self.students_collection.create_index([("student_id", ASCENDING)], unique=True)
            self.students_collection.create_index([("room_number", ASCENDING)])
            self.students_collection.create_index([("name", ASCENDING)])
            self.students_collection.create_index([("tag", ASCENDING)])
            
            # 标签集合索引
            self.tags_collection.create_index([("tag_name", ASCENDING)], unique=True)
            
            logger.info("数据库索引创建完成")
            
        except Exception as e:
            logger.error(f"创建索引失败: {e}")
    
    def save_rooms_data(self, rooms_data: List[Dict]) -> bool:
        """保存房间数据到数据库"""
        try:
            if not rooms_data:
                return False
            
            # 导入MongoDB操作类型
            from pymongo import UpdateOne
            
            # 批量更新房间数据
            operations = []
            current_time = datetime.now()
            
            for room in rooms_data:
                room_doc = {
                    'room_number': room.get('room_number'),
                    'building': room.get('building'),
                    'floor': room.get('floor'),
                    'room_type': room.get('room_type'),
                    'capacity': room.get('capacity', 0),
                    'occupied': room.get('occupied', False),
                    'tenants': room.get('tenants', []),
                    'updated_at': current_time
                }
                
                operations.append(UpdateOne(
                    {'room_number': room.get('room_number')},
                    {'$set': room_doc},
                    upsert=True
                ))
            
            # 执行批量操作
            if operations:
                result = self.rooms_collection.bulk_write(operations)
                logger.info(f"房间数据保存成功: 更新 {result.modified_count} 条，插入 {result.upserted_count} 条")
            
            # 同时保存学生数据
            self._save_students_data(rooms_data)
            
            return True
            
        except Exception as e:
            logger.error(f"保存房间数据失败: {e}")
            return False
    
    def _save_students_data(self, rooms_data: List[Dict]):
        """保存学生数据，智能保留现有标签信息"""
        try:
            # 导入MongoDB操作类型
            from pymongo import UpdateOne
            
            operations = []
            current_time = datetime.now()
            
            for room in rooms_data:
                room_number = room.get('room_number')
                tenants = room.get('tenants', [])
                
                for tenant in tenants:
                    if isinstance(tenant, dict):
                        student_id = tenant.get('student_id')
                        if not student_id:
                            continue
                            
                        # 查询是否已存在该学生，获取现有标签
                        existing_student = self.students_collection.find_one({'student_id': student_id})
                        
                        # 如果学生已存在且有标签，保留原标签；否则使用默认标签
                        existing_tag = '未分类'
                        if existing_student and existing_student.get('tag'):
                            existing_tag = existing_student.get('tag')
                        
                        student_doc = {
                            'student_id': student_id,
                            'name': tenant.get('name'),
                            'room_number': room_number,
                            'building': room.get('building'),
                            'floor': room.get('floor'),
                            'check_in_date': tenant.get('check_in_date'),
                            'mobile': tenant.get('mobile', ''),
                            'is_main': tenant.get('is_main', 0),
                            'certificate_num': tenant.get('certificate_num', ''),
                            'emergency_contact': tenant.get('emergency_contact', ''),
                            'emergency_mobile': tenant.get('emergency_mobile', ''),
                            'sign_status': tenant.get('sign_status', 0),
                            'occupancy_flag': tenant.get('occupancy_flag', 0),
                            'updated_at': current_time
                        }
                        
                        # 根据是否为新学生决定更新方式
                        if existing_student:
                            # 现有学生：保留标签，只更新其他信息
                            operations.append(UpdateOne(
                                {'student_id': student_id},
                                {'$set': student_doc},  # 不更新tag字段
                                upsert=False
                            ))
                        else:
                            # 新学生：设置默认标签
                            student_doc['tag'] = existing_tag
                            operations.append(UpdateOne(
                                {'student_id': student_id},
                                {'$set': student_doc},
                                upsert=True
                            ))
            
            # 执行批量操作
            if operations:
                result = self.students_collection.bulk_write(operations)
                logger.info(f"学生数据智能保存成功: 更新 {result.modified_count} 条，插入 {result.upserted_count} 条")
                
        except Exception as e:
            logger.error(f"保存学生数据失败: {e}")
    
    def get_rooms_data(self, filter_dict: Dict = None) -> List[Dict]:
        """获取房间数据"""
        try:
            filter_dict = filter_dict or {}
            cursor = self.rooms_collection.find(filter_dict).sort("room_number", ASCENDING)
            return list(cursor)
        except Exception as e:
            logger.error(f"获取房间数据失败: {e}")
            return []
    
    def get_students_data(self, filter_dict: Dict = None) -> List[Dict]:
        """获取学生数据"""
        try:
            filter_dict = filter_dict or {}
            cursor = self.students_collection.find(filter_dict).sort("name", ASCENDING)
            return list(cursor)
        except Exception as e:
            logger.error(f"获取学生数据失败: {e}")
            return []
    
    def update_student_tag(self, student_id: str, tag: str) -> bool:
        """更新学生标签"""
        try:
            result = self.students_collection.update_one(
                {'student_id': student_id},
                {
                    '$set': {
                        'tag': tag,
                        'updated_at': datetime.now()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"学生 {student_id} 标签更新为: {tag}")
                return True
            else:
                logger.warning(f"学生 {student_id} 未找到或标签未变更")
                return False
                
        except Exception as e:
            logger.error(f"更新学生标签失败: {e}")
            return False
    
    def get_available_tags(self) -> List[str]:
        """获取可用的标签列表"""
        try:
            # 从标签集合获取预定义标签
            tags_cursor = self.tags_collection.find({}, {'tag_name': 1})
            predefined_tags = [tag['tag_name'] for tag in tags_cursor]
            
            # 如果没有预定义标签，创建默认标签
            if not predefined_tags:
                default_tags = ['22级硕博士', '23级硕博士', '24级硕博士', '实习实践', '未分类']
                self._create_default_tags(default_tags)
                predefined_tags = default_tags
            
            return predefined_tags
            
        except Exception as e:
            logger.error(f"获取标签列表失败: {e}")
            return ['22级硕博士', '23级硕博士', '24级硕博士', '实习实践', '未分类']
    
    def _create_default_tags(self, tags: List[str]):
        """创建默认标签"""
        try:
            # 导入MongoDB操作类型
            from pymongo import UpdateOne
            
            operations = []
            for tag in tags:
                operations.append(UpdateOne(
                    {'tag_name': tag},
                    {
                        '$set': {
                            'tag_name': tag,
                            'description': f'{tag}类别',
                            'created_at': datetime.now()
                        }
                    },
                    upsert=True
                ))
            
            if operations:
                self.tags_collection.bulk_write(operations)
                logger.info("默认标签创建完成")
                
        except Exception as e:
            logger.error(f"创建默认标签失败: {e}")
    
    def add_tag(self, tag_name: str, description: str = '') -> bool:
        """添加新标签"""
        try:
            result = self.tags_collection.insert_one({
                'tag_name': tag_name,
                'description': description,
                'created_at': datetime.now()
            })
            
            if result.inserted_id:
                logger.info(f"新标签添加成功: {tag_name}")
                return True
            return False
            
        except DuplicateKeyError:
            logger.warning(f"标签 {tag_name} 已存在")
            return False
        except Exception as e:
            logger.error(f"添加标签失败: {e}")
            return False
    
    def get_students_by_tag(self, tag: str) -> List[Dict]:
        """根据标签获取学生列表"""
        try:
            cursor = self.students_collection.find({'tag': tag}).sort("name", ASCENDING)
            return list(cursor)
        except Exception as e:
            logger.error(f"根据标签获取学生失败: {e}")
            return []
    
    def get_tag_statistics(self) -> Dict[str, int]:
        """获取标签统计信息"""
        try:
            pipeline = [
                {'$group': {'_id': '$tag', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}}
            ]
            
            result = self.students_collection.aggregate(pipeline)
            stats = {item['_id']: item['count'] for item in result}
            
            return stats
            
        except Exception as e:
            logger.error(f"获取标签统计失败: {e}")
            return {}
    
    def get_room_detail_from_db(self, house_id: str) -> Optional[Dict]:
        """从数据库获取单个房间详情"""
        try:
            # 查找房间信息
            room = self.rooms_collection.find_one({'room_number': house_id})
            if not room:
                # 尝试其他可能的标识符
                room = self.rooms_collection.find_one({'$or': [
                    {'house_id': house_id},
                    {'house_id': int(house_id) if house_id.isdigit() else house_id}
                ]})
            
            if not room:
                return None
            
            # 获取该房间的学生信息
            students = list(self.students_collection.find({'room_number': room['room_number']}))
            
            # 组装房间详情
            room_detail = {
                'house_id': room.get('house_id', house_id),
                'room_number': room['room_number'],
                'building': room.get('building', ''),
                'floor': room.get('floor', 0),
                'room_type': room.get('room_type', ''),
                'capacity': room.get('capacity', 0),
                'occupied': room.get('occupied', False),
                'tenants': []
            }
            
            # 添加租户信息（包含标签）
            for student in students:
                tenant = {
                    'student_id': student['student_id'],
                    'tenant_name': student['name'],
                    'mobile': student.get('mobile', ''),
                    'check_in_date': student.get('check_in_date', ''),
                    'is_main': student.get('is_main', 0),
                    'tag': student.get('tag', '未分类'),
                    'certificate_num': student.get('certificate_num', ''),
                    'emergency_contact': student.get('emergency_contact', ''),
                    'emergency_mobile': student.get('emergency_mobile', ''),
                    'sign_status': student.get('sign_status', 0),
                    'occupancy_flag': student.get('occupancy_flag', 0)
                }
                room_detail['tenants'].append(tenant)
            
            logger.info(f"从数据库成功获取房间 {house_id} 详情")
            return room_detail
            
        except Exception as e:
            logger.error(f"从数据库获取房间详情失败: {e}")
            return None
    
    def get_rooms_with_tags_from_db(self) -> Optional[Dict]:
        """从数据库获取带标签的房间数据"""
        try:
            # 获取所有房间
            rooms = list(self.rooms_collection.find().sort("room_number", ASCENDING))
            
            if not rooms:
                logger.info("数据库中暂无房间数据")
                return None
            
            # 为每个房间添加租户信息（包含标签）
            rooms_with_tags = []
            for room in rooms:
                room_data = {
                    'house_id': room.get('house_id', room['room_number']),
                    'room_number': room['room_number'],
                    'building': room.get('building', ''),
                    'floor': room.get('floor', 0),
                    'room_type': room.get('room_type', ''),
                    'capacity': room.get('capacity', 0),
                    'occupied': room.get('occupied', False),
                    'tenants': []
                }
                
                # 获取该房间的学生信息
                students = list(self.students_collection.find({'room_number': room['room_number']}))
                
                for student in students:
                    tenant = {
                        'student_id': student['student_id'],
                        'tenant_name': student['name'],
                        'mobile': student.get('mobile', ''),
                        'check_in_date': student.get('check_in_date', ''),
                        'is_main': student.get('is_main', 0),
                        'tag': student.get('tag', '未分类'),
                        'certificate_num': student.get('certificate_num', ''),
                        'emergency_contact': student.get('emergency_contact', ''),
                        'emergency_mobile': student.get('emergency_mobile', ''),
                        'sign_status': student.get('sign_status', 0),
                        'occupancy_flag': student.get('occupancy_flag', 0)
                    }
                    room_data['tenants'].append(tenant)
                
                rooms_with_tags.append(room_data)
            
            # 计算标签统计
            tag_stats = self.get_tag_statistics()
            
            # 统计占用情况
            occupied_count = sum(1 for room in rooms_with_tags if room['tenants'])
            
            result = {
                'rooms': rooms_with_tags,
                'tag_statistics': tag_stats,
                'total_rooms': len(rooms_with_tags),
                'occupied_count': occupied_count,
                'vacant_count': len(rooms_with_tags) - occupied_count,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"从数据库成功获取 {len(rooms_with_tags)} 个房间的标签数据")
            return result
            
        except Exception as e:
            logger.error(f"从数据库获取房间标签数据失败: {e}")
            return None

    def close(self):
        """关闭数据库连接"""
        if self.client:
            self.client.close()
            logger.info("数据库连接已关闭")

# 全局数据库管理器实例
db_manager = DatabaseManager() 