#!/bin/bash
# 打包脚本 - 将项目文件打包用于服务器部署

echo "=== 房间管理系统打包 ==="

# 创建部署包目录
PACKAGE_DIR="room-management-deploy"
if [ -d "$PACKAGE_DIR" ]; then
    rm -rf "$PACKAGE_DIR"
fi
mkdir -p "$PACKAGE_DIR"

# 复制必要文件
echo "复制项目文件..."
cp app.py "$PACKAGE_DIR/"
cp requirements.txt "$PACKAGE_DIR/"
cp server_deploy.sh "$PACKAGE_DIR/"
cp README.md "$PACKAGE_DIR/"

# 复制模板文件
mkdir -p "$PACKAGE_DIR/templates"
cp templates/index.html "$PACKAGE_DIR/templates/"

# 复制静态文件
mkdir -p "$PACKAGE_DIR/static/css"
mkdir -p "$PACKAGE_DIR/static/js"
cp static/css/style.css "$PACKAGE_DIR/static/css/"
cp static/js/app.js "$PACKAGE_DIR/static/js/"

# 复制数据文件
echo "复制数据文件..."
cp complete_rooms_layout_*.json "$PACKAGE_DIR/" 2>/dev/null || echo "警告: 未找到房间布局数据文件"

# 创建部署说明
cat > "$PACKAGE_DIR/DEPLOY_INSTRUCTIONS.md" << 'EOF'
# 服务器部署说明

## 部署步骤

### 1. 上传文件到服务器
将整个 room-management-deploy 目录上传到服务器 47.122.68.192

### 2. 连接到服务器
```bash
ssh your_username@47.122.68.192
```

### 3. 运行部署脚本
```bash
cd room-management-deploy
chmod +x server_deploy.sh
./server_deploy.sh
```

### 4. 复制项目文件
```bash
sudo cp -r * /opt/room-management/
cd /opt/room-management
```

### 5. 启动服务
```bash
sudo systemctl enable room-management
sudo systemctl start room-management
```

### 6. 检查服务状态
```bash
sudo systemctl status room-management
```

### 7. 访问应用
打开浏览器访问: http://47.122.68.192:5001

## 故障排除

### 查看日志
```bash
sudo journalctl -u room-management -f
```

### 重启服务
```bash
sudo systemctl restart room-management
```

### 检查端口
```bash
netstat -tlnp | grep 5001
```

### 防火墙检查
```bash
# CentOS/RHEL
sudo firewall-cmd --list-ports

# Ubuntu
sudo ufw status
```
EOF

# 设置执行权限
chmod +x "$PACKAGE_DIR/server_deploy.sh"

# 创建压缩包
echo "创建压缩包..."
tar -czf room-management-deploy.tar.gz "$PACKAGE_DIR"

echo "=================================="
echo "打包完成！"
echo ""
echo "部署包位置: $(pwd)/room-management-deploy.tar.gz"
echo "部署目录: $(pwd)/$PACKAGE_DIR"
echo ""
echo "下一步操作："
echo "1. 将 room-management-deploy.tar.gz 上传到服务器"
echo "2. 在服务器上解压: tar -xzf room-management-deploy.tar.gz"
echo "3. 进入目录: cd room-management-deploy"
echo "4. 运行部署脚本: ./server_deploy.sh"
echo "5. 按照 DEPLOY_INSTRUCTIONS.md 中的说明完成部署"
echo "==================================" 