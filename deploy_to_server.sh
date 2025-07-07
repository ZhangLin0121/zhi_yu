#!/bin/bash

# 简化的服务器部署脚本
# 在服务器上拉取最新代码并部署

echo "🚀 开始部署房间管理系统..."

# 服务器信息
PROJECT_DIR="/opt/room-management"
REPO_URL="https://github.com/ZhangLin0121/zhi_yu.git"

# 1. 停止现有进程
echo "🛑 停止现有进程..."
sudo pkill -f "python3 app.py" || true
sudo pkill -f "app.py" || true

# 2. 创建项目目录
echo "📁 准备项目目录..."
sudo mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# 3. 拉取最新代码
if [ -d ".git" ]; then
    echo "🔄 更新代码..."
    sudo git fetch origin
    sudo git reset --hard origin/main
    sudo git pull origin main
else
    echo "📥 克隆代码..."
    sudo git clone "$REPO_URL" .
fi

# 4. 安装依赖
echo "📦 安装依赖..."
sudo pip3 install -r requirements.txt

# 5. 初始化有效认证信息
echo "🔐 初始化认证信息..."
sudo python3 -c "
from auth_manager import update_auth_info
# 使用经过验证的有效认证信息
auth = {
    '_ams_token': 'web_cdpi6hgs9ez80cb8jit3emwv2wuh4uo5',
    '_common_token': 'web_cdpi6hgs9ez80cb8jit3emwv2wuh4uo5',
    'HWWAFSESID': '13733731437c2a43e3',
    'HWWAFSESTIME': '1751861002097'
}
update_auth_info(auth)
print('✅ 认证信息已更新')

# 验证动态获取功能
from api_client import RoomsDataManager
manager = RoomsDataManager()
data = manager.generate_complete_layout()
if data:
    occupied_rooms = [r for r in data.get('rooms', []) if r.get('tenants')]
    print(f'✅ 动态获取验证成功: {len(occupied_rooms)} 个房间已入住')
else:
    print('❌ 动态获取验证失败')
"

# 6. 启动应用
echo "🚀 启动应用..."
sudo nohup python3 app.py > app.log 2>&1 &
echo $! | sudo tee app.pid

# 7. 等待启动并测试
echo "⏳ 等待启动..."
sleep 8

echo "🧪 测试应用..."
if curl -s "http://localhost:5001/api/status" > /dev/null; then
    echo "✅ 应用启动成功"
    
    # 获取状态信息
    STATUS_DATA=$(curl -s "http://localhost:5001/api/status")
    echo "📊 服务器状态："
    echo "$STATUS_DATA" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    occupied = data.get('occupied_count', 0)
    total = data.get('total_rooms', 0)
    print(f'  - 总房间数: {total}')
    print(f'  - 已入住房间: {occupied}')
    print(f'  - API状态: {data.get(\"status\", \"未知\")}')
    
    if occupied > 100:
        print('')
        print('🎉 部署成功！')
        print(f'✅ 服务器正确显示 {occupied} 个入住房间的动态数据')
        print('✅ 动态获取功能正常工作')
    else:
        print('')
        print('⚠️  警告：入住房间数量异常')
        print(f'   当前显示: {occupied} 个入住房间')
        print('   预期应该显示: 155+ 个入住房间')
except Exception as e:
    print(f'❌ 状态解析失败: {e}')
"
    
    echo ""
    echo "🎉 部署完成！"
    echo "🌐 访问地址: http://47.122.68.192:5001"
    echo "🔗 房间页面: https://www.cacophonyem.me/rooms/"
else
    echo "❌ 应用启动失败"
    echo "📋 查看日志："
    tail -20 app.log
    exit 1
fi 