#!/bin/bash

# 房间管理系统服务器部署脚本
# 使用方法：在服务器上运行此脚本

echo "🚀 开始房间管理系统服务器部署..."

# 检查当前用户和目录
echo "👤 当前用户: $(whoami)"
echo "📁 当前目录: $(pwd)"

# 1. 创建项目目录（如果不存在）
PROJECT_DIR="/opt/room-management"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "📁 创建项目目录: $PROJECT_DIR"
    sudo mkdir -p "$PROJECT_DIR"
    sudo chown $(whoami):$(whoami) "$PROJECT_DIR"
fi

# 2. 进入项目目录
cd "$PROJECT_DIR" || {
    echo "❌ 无法进入项目目录: $PROJECT_DIR"
    exit 1
}

# 3. 克隆或更新代码
if [ -d ".git" ]; then
    echo "🔄 更新现有代码..."
    git fetch origin
    git reset --hard origin/main
    git pull origin main
else
    echo "📥 克隆代码仓库..."
    git clone https://github.com/ZhangLin0121/zhi_yu.git .
fi

# 4. 检查Python环境
echo "🐍 检查Python环境..."
python3 --version
pip3 --version

# 5. 安装依赖
echo "📦 安装Python依赖..."
pip3 install -r requirements.txt

# 6. 初始化认证信息
echo "🔐 初始化认证信息..."
python3 -c "
try:
    from auth_manager import update_auth_info
    current_auth = {
        '_ams_token': 'web_cdpi6hgs9ez80cb8jit3emwv2wuh4uo5',
        '_common_token': 'web_cdpi6hgs9ez80cb8jit3emwv2wuh4uo5',
        'HWWAFSESID': '13733731437c2a43e3',
        'HWWAFSESTIME': '1751861002097'
    }
    if update_auth_info(current_auth):
        print('✅ 认证信息初始化成功')
    else:
        print('❌ 认证信息初始化失败')
except Exception as e:
    print(f'❌ 认证初始化错误: {e}')
"

# 7. 测试应用
echo "🧪 测试应用功能..."
python3 -c "
try:
    from api_client import RoomsDataManager
    manager = RoomsDataManager()
    data = manager.generate_complete_layout()
    
    if data:
        total_rooms = data.get('total_rooms', 0)
        rooms = data.get('rooms', [])
        occupied_rooms = [r for r in rooms if r.get('tenants')]
        print(f'✅ 数据获取成功 - 总房间数: {total_rooms}, 已入住: {len(occupied_rooms)}')
    else:
        print('❌ 数据获取失败')
except Exception as e:
    print(f'❌ 测试失败: {e}')
"

# 8. 创建启动脚本
echo "📝 创建启动脚本..."
cat > start_app.sh << 'EOF'
#!/bin/bash
cd /opt/room-management
export PYTHONPATH=/opt/room-management:$PYTHONPATH
nohup python3 app.py > app.log 2>&1 &
echo $! > app.pid
echo "应用已启动，PID: $(cat app.pid)"
EOF

chmod +x start_app.sh

# 9. 创建停止脚本
echo "📝 创建停止脚本..."
cat > stop_app.sh << 'EOF'
#!/bin/bash
if [ -f app.pid ]; then
    PID=$(cat app.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "应用已停止，PID: $PID"
        rm -f app.pid
    else
        echo "应用进程不存在"
        rm -f app.pid
    fi
else
    echo "未找到PID文件，尝试通过进程名停止..."
    pkill -f "python3 app.py"
fi
EOF

chmod +x stop_app.sh

# 10. 停止旧进程
echo "🛑 停止旧进程..."
./stop_app.sh

# 11. 启动新进程
echo "🚀 启动新进程..."
./start_app.sh

# 12. 等待启动
echo "⏳ 等待应用启动..."
sleep 5

# 13. 检查进程状态
echo "🔍 检查进程状态..."
if [ -f app.pid ]; then
    PID=$(cat app.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "✅ 应用正在运行，PID: $PID"
    else
        echo "❌ 应用启动失败"
        cat app.log
        exit 1
    fi
else
    echo "❌ 未找到PID文件"
    exit 1
fi

# 14. 测试API
echo "🧪 测试API..."
sleep 3
if curl -s "http://localhost:5001/api/status" | python3 -m json.tool; then
    echo "✅ API测试成功"
else
    echo "❌ API测试失败"
    echo "查看日志:"
    tail -20 app.log
    exit 1
fi

# 15. 测试数据
echo "🧪 测试数据获取..."
curl -s "http://localhost:5001/api/rooms" | python3 -c "
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
    
    print(f'✅ 数据测试成功')
    print(f'   总房间数: {total_rooms}')
    print(f'   楼层数: {len(floors)}')
    print(f'   已入住: {total_occupied}')
    print(f'   入住率: {total_occupied/total_rooms*100:.1f}%')
except Exception as e:
    print(f'❌ 数据测试失败: {e}')
"

echo ""
echo "🎉 部署完成！"
echo ""
echo "🌐 访问地址："
echo "  - 主页: http://47.122.68.192:5001"
echo "  - API状态: http://47.122.68.192:5001/api/status"
echo "  - 房间数据: http://47.122.68.192:5001/api/rooms"
echo ""
echo "📋 管理命令："
echo "  - 启动应用: ./start_app.sh"
echo "  - 停止应用: ./stop_app.sh"
echo "  - 查看日志: tail -f app.log"
echo "  - 查看进程: ps aux | grep python3" 