# 快速部署指南

## 🚀 一键部署到服务器 47.122.68.192

### 步骤1: 上传文件
将 `room-management-deploy.tar.gz` 上传到服务器

### 步骤2: 在服务器上执行
```bash
# 解压文件
tar -xzf room-management-deploy.tar.gz
cd room-management-deploy

# 运行部署脚本
chmod +x server_deploy.sh
./server_deploy.sh

# 复制文件到部署目录
sudo cp -r * /opt/room-management/
cd /opt/room-management

# 启动服务
sudo systemctl enable room-management
sudo systemctl start room-management

# 检查服务状态
sudo systemctl status room-management
```

### 步骤3: 访问应用
🌐 **访问地址**: http://47.122.68.192:5001

## 📱 功能特点
- ✅ 全景视图：238间房间一目了然
- ✅ 1楼特殊布局：01-06、通道、通道、07-10
- ✅ 搜索功能：房间号、姓名、手机号
- ✅ 手机端优化：响应式设计
- ✅ 实时数据：入住率63.4%

## 🔧 故障排除
```bash
# 查看日志
sudo journalctl -u room-management -f

# 重启服务
sudo systemctl restart room-management

# 检查端口
netstat -tlnp | grep 5001

# 检查防火墙
sudo firewall-cmd --list-ports  # CentOS
sudo ufw status                 # Ubuntu
```

## 📞 技术支持
如有问题，请检查：
1. 防火墙是否开放5001端口
2. Python3是否正确安装
3. 服务是否正常运行
4. 网络连接是否正常

---
*部署完成后，您就可以通过手机访问房间管理系统了！* 📱 