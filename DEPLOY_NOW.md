# 🚀 立即部署指南

## 当前状态
- ✅ 本地开发完成
- ✅ 代码已推送到GitHub
- ⚠️ 服务器需要更新（当前显示0个已入住房间）

## 一键部署命令

**请在服务器 47.122.68.192 上执行以下命令：**

```bash
curl -sSL https://raw.githubusercontent.com/ZhangLin0121/zhi_yu/main/simple_deploy.sh | bash
```

## 部署过程说明

该命令将自动执行以下步骤：

1. **停止现有进程**
   ```bash
   pkill -f "python3 app.py"
   ```

2. **更新代码**
   ```bash
   cd /opt/room-management
   git fetch origin
   git reset --hard origin/main
   ```

3. **安装依赖**
   ```bash
   pip3 install -r requirements.txt
   ```

4. **初始化认证信息**
   - 自动设置最新的认证token
   - 创建认证缓存文件

5. **启动新版本**
   ```bash
   nohup python3 app.py > app.log 2>&1 &
   ```

6. **验证部署**
   - 测试API状态
   - 验证数据获取
   - 确认认证有效性

## 预期结果

部署成功后，您应该看到：

```
✅ 应用启动成功
📊 房间数据: 238 个房间
🎉 部署完成！

🌐 访问地址: http://47.122.68.192:5001
```

## 新功能特性

部署后，系统将具备以下新功能：

1. **自动认证管理**
   - 每次页面加载时自动检查认证状态
   - 检测到认证过期时自动获取新认证
   - 5分钟智能检查间隔

2. **认证刷新按钮**
   - 页面上的绿色"更新认证"按钮
   - 一键手动刷新认证信息
   - 实时状态反馈

3. **智能数据同步**
   - 自动维护最新的入住数据
   - 无需手动干预
   - 确保页面始终显示真实数据

## 验证步骤

部署完成后，请验证：

1. **访问主页**
   ```
   http://47.122.68.192:5001
   ```

2. **检查API状态**
   ```bash
   curl http://47.122.68.192:5001/api/status
   ```
   应该显示 `occupied_count` > 0

3. **测试认证刷新**
   - 点击页面上的"更新认证"按钮
   - 应该显示成功通知

## 故障排除

如果部署失败，请检查：

1. **查看部署日志**
   ```bash
   cd /opt/room-management
   tail -20 app.log
   ```

2. **检查进程状态**
   ```bash
   ps aux | grep python3
   ```

3. **手动启动**
   ```bash
   cd /opt/room-management
   python3 app.py
   ```

## 技术支持

如有问题，请检查：
- 网络连接是否正常
- Python依赖是否安装完整
- 认证信息是否有效
- 防火墙设置是否正确

---

**部署命令（复制粘贴）：**
```bash
curl -sSL https://raw.githubusercontent.com/ZhangLin0121/zhi_yu/main/simple_deploy.sh | bash
``` 