#!/bin/bash
# 服务器快速部署脚本
# 在服务器 47.122.68.192 上执行此脚本

echo "=== 房间管理系统 - 服务器部署 ==="
echo "GitHub: https://github.com/ZhangLin0121/zhi_yu.git"
echo "服务器: 47.122.68.192:5001"
echo "========================================"

# 检查是否为root用户
if [[ $EUID -eq 0 ]]; then
   echo "警告: 建议不要以root用户运行此脚本"
fi

# 更新系统包
echo "更新系统包..."
if command -v yum &> /dev/null; then
    # CentOS/RHEL
    sudo yum update -y
    sudo yum install -y git python3 python3-pip
elif command -v apt &> /dev/null; then
    # Ubuntu/Debian
    sudo apt update
    sudo apt install -y git python3 python3-pip
else
    echo "警告: 无法自动安装依赖，请手动安装 git python3 python3-pip"
fi

# 创建项目目录
PROJECT_DIR="/opt/room-management"
echo "创建项目目录: $PROJECT_DIR"
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR

# 克隆项目
echo "从GitHub克隆项目..."
cd /opt
if [ -d "$PROJECT_DIR" ]; then
    sudo rm -rf $PROJECT_DIR
fi
sudo git clone https://github.com/ZhangLin0121/zhi_yu.git room-management
sudo chown -R $USER:$USER $PROJECT_DIR
cd $PROJECT_DIR

# 安装Python依赖
echo "安装Python依赖..."
pip3 install --user -r requirements.txt

# 配置防火墙
echo "配置防火墙..."
if command -v firewall-cmd &> /dev/null; then
    # CentOS/RHEL with firewalld
    sudo firewall-cmd --permanent --add-port=5001/tcp
    sudo firewall-cmd --reload
    echo "✅ 已开放5001端口 (firewalld)"
elif command -v ufw &> /dev/null; then
    # Ubuntu with ufw
    sudo ufw allow 5001/tcp
    echo "✅ 已开放5001端口 (ufw)"
elif command -v iptables &> /dev/null; then
    # 使用iptables
    sudo iptables -A INPUT -p tcp --dport 5001 -j ACCEPT
    # 尝试保存规则
    if command -v iptables-save &> /dev/null; then
        sudo iptables-save | sudo tee /etc/iptables/rules.v4 > /dev/null 2>&1
    fi
    echo "✅ 已开放5001端口 (iptables)"
else
    echo "⚠️  请手动开放5001端口"
fi

# 创建systemd服务
echo "创建系统服务..."
sudo tee /etc/systemd/system/room-management.service > /dev/null <<EOF
[Unit]
Description=Room Management System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=10
Environment=FLASK_ENV=production
Environment=PYTHONPATH=$PROJECT_DIR

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd并启动服务
echo "启动服务..."
sudo systemctl daemon-reload
sudo systemctl enable room-management
sudo systemctl start room-management

# 等待服务启动
sleep 3

# 检查服务状态
echo "检查服务状态..."
if sudo systemctl is-active --quiet room-management; then
    echo "✅ 服务启动成功！"
else
    echo "❌ 服务启动失败，查看日志:"
    sudo journalctl -u room-management --no-pager -n 10
    exit 1
fi

# 检查端口
echo "检查端口监听..."
if netstat -tlnp 2>/dev/null | grep -q ":5001 "; then
    echo "✅ 端口5001正在监听"
else
    echo "⚠️  端口5001未监听，请检查服务状态"
fi

# 测试API
echo "测试API接口..."
if curl -s http://localhost:5001/api/rooms | head -1 | grep -q "{"; then
    echo "✅ API接口正常"
else
    echo "⚠️  API接口可能有问题"
fi

echo "========================================"
echo "🎉 部署完成！"
echo ""
echo "📊 系统信息:"
echo "   - 总房间数: 238间"
echo "   - 1楼布局: 01-06, 通道, 通道, 07-10"
echo "   - 入住率: 63.4%"
echo ""
echo "🌐 访问地址:"
echo "   - 电脑端: http://47.122.68.192:5001"
echo "   - 手机端: http://47.122.68.192:5001 (自动适配)"
echo ""
echo "🔧 管理命令:"
echo "   - 查看状态: sudo systemctl status room-management"
echo "   - 查看日志: sudo journalctl -u room-management -f"
echo "   - 重启服务: sudo systemctl restart room-management"
echo "   - 停止服务: sudo systemctl stop room-management"
echo ""
echo "📱 现在您可以通过手机访问房间管理系统了！"
echo "========================================" 