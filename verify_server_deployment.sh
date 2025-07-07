#!/bin/bash

# 服务器部署验证脚本
# 确保服务器能获取到真实的入住数据

echo "🚀 开始验证服务器部署..."
echo ""

SERVER_URL="http://47.122.68.192:5001"

# 1. 执行部署
echo "📦 执行一键部署..."
echo "部署命令: curl -sSL https://raw.githubusercontent.com/ZhangLin0121/zhi_yu/main/simple_deploy.sh | bash"
echo ""
echo "⚠️  请在服务器上执行上述命令，然后按回车继续验证..."
read -p "部署完成后按回车继续: "

# 2. 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 3. 验证API状态
echo "🔍 验证API状态..."
STATUS_RESPONSE=$(curl -s "$SERVER_URL/api/status")

if [ $? -eq 0 ]; then
    echo "✅ 服务器连接成功"
    echo "$STATUS_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print('📊 API状态:')
    print(f'  状态: {data.get(\"status\", \"未知\")}')
    print(f'  总房间数: {data.get(\"total_rooms\", 0)}')
    print(f'  已入住: {data.get(\"occupied_count\", \"未知\")}')
    print(f'  认证状态: {data.get(\"auth_status\", \"未知\")}')
    
    occupied = data.get('occupied_count', 0)
    if isinstance(occupied, int) and occupied > 100:
        print('')
        print('✅ 服务器成功获取到真实入住数据！')
        print(f'🎉 {occupied} 个房间已入住，数据真实有效')
    else:
        print('')
        print('❌ 服务器仍未获取到真实数据')
        print('🔧 可能需要手动刷新认证信息')
except Exception as e:
    print(f'❌ 状态解析失败: {e}')
"
else
    echo "❌ 无法连接到服务器"
    exit 1
fi

echo ""

# 4. 验证房间数据
echo "🏠 验证房间数据..."
ROOMS_RESPONSE=$(curl -s "$SERVER_URL/api/rooms")

if [ $? -eq 0 ]; then
    echo "$ROOMS_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    total_rooms = data.get('total_rooms', 0)
    floors = data.get('floors', {})
    occupied_count = data.get('occupied_count', 0)
    
    print('📊 房间数据验证:')
    print(f'  总房间数: {total_rooms}')
    print(f'  楼层数: {len(floors)}')
    print(f'  已入住: {occupied_count}')
    
    if occupied_count > 100:
        print('')
        print('✅ 房间数据验证成功！')
        print(f'🎯 服务器成功获取到 {occupied_count} 个已入住房间')
        
        # 检查具体的入住房间
        occupied_rooms = []
        for floor_num, rooms in floors.items():
            for room in rooms:
                if room.get('tenants'):
                    occupied_rooms.append(room)
        
        print('')
        print('🏠 入住房间示例:')
        for i, room in enumerate(occupied_rooms[:5]):
            tenants = room.get('tenants', [])
            tenant_names = [t.get('tenant_name', '未知') for t in tenants]
            print(f'  - {room.get(\"room_number\", \"未知\")}: {len(tenants)}人')
            
        print('')
        print('🎉 服务器部署验证成功！')
        print('✅ 真实入住数据已正确显示')
    else:
        print('')
        print('❌ 房间数据验证失败')
        print('🔧 需要检查认证信息或重新部署')
        
except Exception as e:
    print(f'❌ 房间数据解析失败: {e}')
"
else
    echo "❌ 无法获取房间数据"
    exit 1
fi

echo ""

# 5. 测试认证刷新功能
echo "🔑 测试认证刷新功能..."
REFRESH_RESPONSE=$(curl -s -X POST "$SERVER_URL/api/auth/refresh" -H "Content-Type: application/json")

if [ $? -eq 0 ]; then
    echo "$REFRESH_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        print('✅ 认证刷新功能正常')
        print(f'📝 {data.get(\"message\", \"认证刷新成功\")}')
    else:
        print('⚠️  认证刷新功能可能有问题')
        print(f'📝 {data.get(\"message\", \"未知错误\")}')
except Exception as e:
    print(f'❌ 认证刷新测试失败: {e}')
"
else
    echo "❌ 无法测试认证刷新功能"
fi

echo ""
echo "🎯 验证完成！"
echo ""
echo "📋 验证结果总结:"
echo "1. 服务器连接状态"
echo "2. API状态检查"
echo "3. 房间数据验证"
echo "4. 认证刷新测试"
echo ""
echo "🌐 访问地址: $SERVER_URL"
echo "🔗 房间页面: https://www.cacophonyem.me/rooms/" 