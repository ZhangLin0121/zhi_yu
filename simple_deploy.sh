#!/bin/bash

# 简化部署脚本 - 可以直接在服务器上运行
# 使用方法: curl -sSL https://raw.githubusercontent.com/ZhangLin0121/zhi_yu/main/simple_deploy.sh | bash

echo "🚀 开始房间管理系统简化部署..."

# 设置变量
PROJECT_DIR="/opt/room-management"
REPO_URL="https://github.com/ZhangLin0121/zhi_yu.git"

# 1. 创建项目目录
echo "📁 准备项目目录..."
sudo mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# 2. 停止现有进程
echo "🛑 停止现有进程..."
pkill -f "python3 app.py" || true

# 3. 克隆或更新代码
if [ -d ".git" ]; then
    echo "🔄 更新代码..."
    git fetch origin
    git reset --hard origin/main
else
    echo "📥 克隆代码..."
    git clone "$REPO_URL" .
fi

# 4. 安装依赖
echo "📦 安装依赖..."
pip3 install -r requirements.txt

# 5. 初始化认证
echo "🔐 初始化认证..."
python3 -c "
from auth_manager import update_auth_info
# 使用最新有效的认证信息（2025-07-07 测试有效）
auth = {
    '_ams_token': 'web_cdpi6hgs9ez80cb8jit3emwv2wuh4uo5',
    '_common_token': 'web_cdpi6hgs9ez80cb8jit3emwv2wuh4uo5',
    'HWWAFSESID': '13733731437c2a43e3',
    'HWWAFSESTIME': '1751861002097'
}
update_auth_info(auth)
print('✅ 认证信息已更新')

# 测试认证信息有效性
from api_client import RoomsDataManager
manager = RoomsDataManager()
data = manager.generate_complete_layout()
if data:
    occupied_rooms = [r for r in data.get('rooms', []) if r.get('tenants')]
    print(f'✅ 认证验证成功: {len(occupied_rooms)} 个房间已入住')
else:
    print('❌ 认证验证失败')
"

# 6. 启动应用
echo "🚀 启动应用..."
nohup python3 app.py > app.log 2>&1 &
APP_PID=$!
echo $APP_PID > app.pid

# 7. 等待启动
echo "⏳ 等待启动..."
sleep 5

# 8. 强制认证更新（确保获取真实数据）
echo "🔐 强制更新认证信息..."
python3 force_auth_update.py

# 9. 重启应用以应用新认证
echo "🔄 重启应用..."
if [ -f app.pid ]; then
    kill $(cat app.pid) 2>/dev/null || true
    sleep 3
fi

nohup python3 app.py > app.log 2>&1 &
echo $! > app.pid

# 10. 等待启动并测试
echo "⏳ 等待应用重启..."
sleep 8

echo "🧪 测试应用..."
if curl -s "http://localhost:5001/api/status" > /dev/null; then
    echo "✅ 应用启动成功"
    
    # 详细测试数据
    STATUS_DATA=$(curl -s "http://localhost:5001/api/status")
    ROOM_DATA=$(curl -s "http://localhost:5001/api/rooms")
    
    echo "$STATUS_DATA" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    occupied = data.get('occupied_count', 0)
    total = data.get('total_rooms', 0)
    
    print(f'📊 API状态: {data.get(\"status\", \"未知\")}')
    print(f'📊 总房间数: {total}')
    print(f'📊 已入住: {occupied}')
    
    if occupied > 100:
        print('')
        print('🎉 部署验证成功！')
        print(f'✅ 服务器成功获取到 {occupied} 个已入住房间的真实数据')
    else:
        print('')
        print('⚠️  警告：入住房间数量异常，可能需要手动刷新认证')
except:
    print('❌ 状态数据解析失败')
"
    
    echo ""
    echo "🎉 部署完成！"
    echo ""
    echo "🌐 访问地址: http://47.122.68.192:5001"
    echo "🔗 房间页面: https://www.cacophonyem.me/rooms/"
    echo "📋 管理命令:"
    echo "  - 停止应用: kill \$(cat app.pid)"
    echo "  - 查看日志: tail -f app.log"
    echo "  - 重启应用: nohup python3 app.py > app.log 2>&1 & echo \$! > app.pid"
else
    echo "❌ 应用启动失败"
    echo "📋 查看日志: tail -20 app.log"
    echo "🔧 手动启动: python3 app.py"
    exit 1
fi 