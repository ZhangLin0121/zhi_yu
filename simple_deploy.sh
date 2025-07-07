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

# 8. 测试
echo "🧪 测试应用..."
if curl -s "http://localhost:5001/api/status" > /dev/null; then
    echo "✅ 应用启动成功"
    
    # 测试数据
    ROOM_DATA=$(curl -s "http://localhost:5001/api/rooms")
    TOTAL_ROOMS=$(echo "$ROOM_DATA" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('total_rooms', 0))")
    
    echo "📊 房间数据: $TOTAL_ROOMS 个房间"
    echo "🎉 部署完成！"
    echo ""
    echo "🌐 访问地址: http://47.122.68.192:5001"
    echo "📋 管理: kill \$(cat app.pid) # 停止应用"
else
    echo "❌ 应用启动失败"
    echo "📋 查看日志: tail app.log"
    exit 1
fi 