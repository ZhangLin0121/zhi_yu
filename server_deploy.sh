#!/bin/bash
# 服务器部署脚本 - 在服务器47.122.68.192上运行

echo "=== 房间管理系统服务器部署 ==="
echo "服务器: 47.122.68.192"
echo "端口: 5001"
echo "=================================="

# 检查是否为root用户
if [[ $EUID -eq 0 ]]; then
   echo "警告: 建议不要以root用户运行此脚本"
fi

# 检查Python环境
echo "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "安装Python3..."
    if command -v yum &> /dev/null; then
        # CentOS/RHEL
        sudo yum update -y
        sudo yum install -y python3 python3-pip
    elif command -v apt &> /dev/null; then
        # Ubuntu/Debian
        sudo apt update
        sudo apt install -y python3 python3-pip
    else
        echo "错误: 无法自动安装Python3，请手动安装"
        exit 1
    fi
fi

# 创建项目目录
PROJECT_DIR="/opt/room-management"
echo "创建项目目录: $PROJECT_DIR"
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR

# 进入项目目录
cd $PROJECT_DIR

# 检查防火墙设置
echo "检查防火墙设置..."
if command -v firewall-cmd &> /dev/null; then
    # CentOS/RHEL with firewalld
    sudo firewall-cmd --permanent --add-port=5001/tcp
    sudo firewall-cmd --reload
    echo "已开放5001端口"
elif command -v ufw &> /dev/null; then
    # Ubuntu with ufw
    sudo ufw allow 5001/tcp
    echo "已开放5001端口"
elif command -v iptables &> /dev/null; then
    # 使用iptables
    sudo iptables -A INPUT -p tcp --dport 5001 -j ACCEPT
    sudo iptables-save | sudo tee /etc/iptables/rules.v4
    echo "已开放5001端口"
fi

# 安装依赖
echo "安装Python依赖..."
pip3 install --user flask requests pandas

# 创建systemd服务文件
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

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd配置
sudo systemctl daemon-reload

echo "=================================="
echo "部署脚本准备完成！"
echo ""
echo "下一步操作："
echo "1. 将所有项目文件上传到服务器的 $PROJECT_DIR 目录"
echo "2. 运行以下命令启动服务："
echo "   sudo systemctl enable room-management"
echo "   sudo systemctl start room-management"
echo "3. 检查服务状态："
echo "   sudo systemctl status room-management"
echo "4. 查看日志："
echo "   sudo journalctl -u room-management -f"
echo ""
echo "访问地址: http://47.122.68.192:5001"
echo "==================================" 