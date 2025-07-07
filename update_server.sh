#!/bin/bash

# 服务器更新脚本 - 修复认证问题
echo "开始更新服务器..."

# 1. 进入项目目录
cd /opt/room-management

# 2. 拉取最新代码
echo "拉取最新代码..."
sudo git pull origin main

# 3. 重启服务
echo "重启服务..."
sudo systemctl restart room-management

# 4. 等待服务启动
echo "等待服务启动..."
sleep 5

# 5. 检查服务状态
echo "检查服务状态..."
sudo systemctl status room-management --no-pager

# 6. 测试API
echo "测试API..."
curl -s "http://localhost:5001/api/status" | python3 -m json.tool

echo "更新完成！" 