#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成完整房间布局脚本
根据实际建筑布局生成238间房间的完整数据
"""

import json
from datetime import datetime
import os

def generate_complete_layout():
    """生成完整的房间布局"""
    
    # 加载现有的入住数据
    json_files = [f for f in os.listdir('.') if f.startswith('rooms_data_') and f.endswith('.json')]
    
    if not json_files:
        print("未找到现有房间数据文件！")
        return None
    
    latest_file = sorted(json_files)[-1]
    print(f"加载现有数据文件: {latest_file}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        existing_data = json.load(f)
    
    # 创建现有房间的映射 (根据房间号)
    existing_rooms_map = {}
    for room in existing_data['rooms']:
        room_key = f"{room['floor']}-{room['room_number']}"
        existing_rooms_map[room_key] = room
    
    # 生成完整房间布局
    all_rooms = []
    
    # 1楼: 只有10间实际房间 (01-06, 07-10)，按照用户要求的布局
    floor = 1
    # 1楼房间编号：01-06, 07-10 (显示时会有通道占位)
    floor1_rooms = [f"1{i:02d}" for i in range(1, 7)] + [f"1{i:02d}" for i in range(7, 11)]
    
    for i, room_number in enumerate(floor1_rooms, 1):
        room_key = f"{floor}-{room_number}"
        
        if room_key in existing_rooms_map:
            # 使用现有数据
            all_rooms.append(existing_rooms_map[room_key])
        else:
            # 创建空房间
            all_rooms.append(create_empty_room(floor, room_number, i))
    
    # 2-20楼: 每层12间房
    for floor in range(2, 21):
        for room_in_floor in range(1, 13):  # 01-12
            room_number = f"{floor}{room_in_floor:02d}"
            room_key = f"{floor}-{room_number}"
            
            if room_key in existing_rooms_map:
                # 使用现有数据
                all_rooms.append(existing_rooms_map[room_key])
            else:
                # 创建空房间
                all_rooms.append(create_empty_room(floor, room_number, room_in_floor))
    
    # 按楼层和房间号排序
    all_rooms.sort(key=lambda x: (x['floor'], x['room_in_floor']))
    
    # 生成完整数据结构
    complete_data = {
        'total_rooms': len(all_rooms),
        'rooms': all_rooms,
        'timestamp': datetime.now().isoformat(),
        'layout_info': {
            'building': 'A4栋',
            'floors': 20,
            'floor_1_rooms': 10,  # 1楼10间（01-06, 07-12，中间2个通道）
            'regular_floor_rooms': 12,  # 2-20楼每层12间
            'total_designed_rooms': 10 + 19 * 12  # 238间
        }
    }
    
    return complete_data

def create_empty_room(floor, room_number, room_in_floor):
    """创建空房间数据"""
    return {
        'house_id': f"empty_{floor}_{room_in_floor}",  # 虚拟房间ID
        'house_name': f"之寓·未来-A4栋-1单元-{room_number}",
        'building': 4,
        'unit': 1,
        'floor': floor,
        'room_in_floor': room_in_floor,
        'room_number': str(room_number),
        'tenants': [],
        'main_tenant': None,
        'co_tenants': [],
        'is_vacant': True  # 标记为空房间
    }

def analyze_layout(data):
    """分析房间布局"""
    rooms = data['rooms']
    
    print("\n" + "="*60)
    print("完整房间布局分析")
    print("="*60)
    print(f"总房间数: {data['total_rooms']}")
    
    # 按楼层统计
    floor_stats = {}
    occupied_count = 0
    vacant_count = 0
    
    for room in rooms:
        floor = room['floor']
        if floor not in floor_stats:
            floor_stats[floor] = {'total': 0, 'occupied': 0, 'vacant': 0}
        
        floor_stats[floor]['total'] += 1
        
        if room['tenants']:
            floor_stats[floor]['occupied'] += 1
            occupied_count += 1
        else:
            floor_stats[floor]['vacant'] += 1
            vacant_count += 1
    
    print(f"\n总体统计:")
    print(f"  已入住: {occupied_count} 间")
    print(f"  空闲: {vacant_count} 间")
    print(f"  入住率: {occupied_count/data['total_rooms']*100:.1f}%")
    
    print(f"\n楼层详细统计:")
    for floor in sorted(floor_stats.keys()):
        stats = floor_stats[floor]
        print(f"  {floor}楼: {stats['total']}间 (入住{stats['occupied']}间, 空闲{stats['vacant']}间)")
    
    print("="*60)

def main():
    """主函数"""
    try:
        # 生成完整布局
        complete_data = generate_complete_layout()
        
        if complete_data:
            # 保存数据
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"complete_rooms_layout_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(complete_data, f, ensure_ascii=False, indent=2)
            
            print(f"完整房间布局已保存到: {filename}")
            
            # 分析布局
            analyze_layout(complete_data)
            
        else:
            print("生成完整布局失败")
            
    except Exception as e:
        print(f"程序执行出错: {str(e)}")

if __name__ == "__main__":
    main() 