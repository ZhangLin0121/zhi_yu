# 服务器部署指令

## 快速部署（推荐）

连接到服务器后，执行以下命令：

```bash
# 1. 进入项目目录
cd /opt/room-management

# 2. 拉取最新代码
sudo git pull origin main

# 3. 重启服务
sudo systemctl restart room-management

# 4. 检查服务状态
sudo systemctl status room-management

# 5. 查看日志（可选）
sudo journalctl -u room-management -f --since "5 minutes ago"
```

## 访问地址

- **电脑端**: http://47.122.68.192:5001
- **手机端**: http://47.122.68.192:5001 (自动适配)

## 更新内容

✅ 移除50平米房间的虚线边框和右上角标注  
✅ 在3号和4号房间之间、10号和11号房间之间添加竖直虚线分隔  
✅ 更新图例说明：简化为基本状态颜色+虚线说明  
✅ 优化统计信息：按总计、35平米、50平米、17-20层分类显示  
✅ 每个统计项包含总数、入住数、入住率三个数据  

## 故障排除

如果服务无法启动，请检查：

```bash
# 查看详细日志
sudo journalctl -u room-management -n 50

# 检查端口占用
sudo netstat -tlnp | grep 5001

# 手动启动测试
cd /opt/room-management && python3 app.py
```

## 联系方式

如有问题请联系系统管理员。 