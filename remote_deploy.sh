#!/bin/bash

# 远程部署脚本
# 将本地的部署脚本上传到服务器并执行

SERVER_IP="47.122.68.192"
SERVER_USER="root"  # 根据实际情况修改
PROJECT_DIR="/opt/room-management"

echo "🚀 开始远程部署..."

# 1. 上传部署脚本到服务器
echo "📤 上传部署脚本到服务器..."
scp server_deploy_manual.sh ${SERVER_USER}@${SERVER_IP}:/tmp/

# 2. 通过SSH执行部署脚本
echo "🔄 在服务器上执行部署..."
ssh ${SERVER_USER}@${SERVER_IP} "
    chmod +x /tmp/server_deploy_manual.sh
    /tmp/server_deploy_manual.sh
    rm -f /tmp/server_deploy_manual.sh
"

echo "🎉 远程部署完成！"

# 3. 测试部署结果
echo "🧪 测试部署结果..."
sleep 5

echo "📊 检查服务器状态..."
curl -s "http://${SERVER_IP}:5001/api/status" | python3 -m json.tool

echo ""
echo "📊 检查房间数据..."
curl -s "http://${SERVER_IP}:5001/api/rooms" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    total_rooms = data.get('total_rooms', 0)
    floors = data.get('floors', {})
    
    # 统计入住情况
    total_occupied = 0
    for floor_num, rooms in floors.items():
        occupied = len([r for r in rooms if r.get('tenants')])
        total_occupied += occupied
    
    print(f'✅ 远程部署验证成功')
    print(f'   总房间数: {total_rooms}')
    print(f'   楼层数: {len(floors)}')
    print(f'   已入住: {total_occupied}')
    print(f'   入住率: {total_occupied/total_rooms*100:.1f}%')
    
    if total_occupied > 0:
        print('🎉 认证信息更新成功，数据获取正常！')
    else:
        print('⚠️  认证信息可能需要手动更新')
        
except Exception as e:
    print(f'❌ 远程部署验证失败: {e}')
" 