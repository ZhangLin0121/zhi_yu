#!/bin/bash

echo "🚀 开始完整部署流程..."

# 检查服务器连接
echo "📡 检查服务器状态..."
if curl -s --connect-timeout 5 "http://47.122.68.192:5001/api/status" > /dev/null; then
    echo "✅ 服务器连接正常"
else
    echo "⚠️  服务器可能未运行或网络不通"
fi

# 显示当前本地状态
echo ""
echo "📊 本地项目状态："
echo "- 项目目录: $(pwd)"
echo "- Git分支: $(git branch --show-current)"
echo "- 最新提交: $(git log -1 --oneline)"

# 检查本地是否有未提交的更改
if [[ -n $(git status --porcelain) ]]; then
    echo "⚠️  发现未提交的更改："
    git status --short
    echo ""
    read -p "是否继续部署？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 部署已取消"
        exit 1
    fi
fi

echo ""
echo "🔄 准备部署到服务器..."

# 创建部署命令
DEPLOY_COMMANDS="
echo '🔄 开始服务器端部署...'

# 1. 进入项目目录
cd /opt/room-management || { echo '❌ 项目目录不存在'; exit 1; }

# 2. 备份当前版本
sudo cp -r . ../room-management-backup-\$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo '⚠️  备份失败，继续部署'

# 3. 拉取最新代码
echo '📥 拉取最新代码...'
sudo git fetch origin
sudo git reset --hard origin/main

# 4. 安装/更新依赖
echo '📦 检查依赖...'
if [ -f requirements.txt ]; then
    sudo pip3 install -r requirements.txt
fi

# 5. 初始化认证信息
echo '🔐 初始化认证信息...'
sudo python3 -c \"
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
\"

# 6. 重启服务
echo '🔄 重启服务...'
sudo systemctl restart room-management

# 7. 等待服务启动
echo '⏳ 等待服务启动...'
sleep 10

# 8. 检查服务状态
echo '🔍 检查服务状态...'
sudo systemctl status room-management --no-pager -l

# 9. 测试API
echo '🧪 测试API...'
if curl -s 'http://localhost:5001/api/status' | python3 -m json.tool; then
    echo '✅ API测试成功'
else
    echo '❌ API测试失败'
fi

echo '🎉 服务器端部署完成！'
"

echo "📤 执行服务器部署命令..."
echo "$DEPLOY_COMMANDS"

echo ""
echo "🌐 部署完成后可访问："
echo "- 主页: http://47.122.68.192:5001"
echo "- API状态: http://47.122.68.192:5001/api/status"
echo "- 房间数据: http://47.122.68.192:5001/api/rooms"

echo ""
echo "📋 如需手动执行，请运行："
echo "ssh user@47.122.68.192"
echo "然后执行上述部署命令" 