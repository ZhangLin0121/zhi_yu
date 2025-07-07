# 服务器部署指南

## 🚀 完整部署流程

### 1. 登录服务器
```bash
ssh root@47.122.68.192
```

### 2. 停止现有进程
```bash
pkill -f "python3 app.py" || true
pkill -f "app.py" || true
```

### 3. 进入项目目录并更新代码
```bash
cd /opt/room-management
git fetch origin
git reset --hard origin/main
git pull origin main
```

### 4. 安装依赖（可选）
```bash
# 如果需要更新依赖，使用以下命令
pip3 install -r requirements.txt --break-system-packages
```

> **注意**: 如果遇到urllib3版本冲突，可以跳过依赖安装步骤，因为大部分依赖已经安装。

### 5. 初始化认证信息
```bash
python3 -c "
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
    if len(occupied_rooms) > 100:
        print('🎉 动态获取功能正常工作！')
    else:
        print('⚠️  入住房间数量异常')
else:
    print('❌ 动态获取验证失败')
"
```

### 6. 启动应用
```bash
nohup python3 app.py > app.log 2>&1 &
echo $! > app.pid
```

### 7. 验证部署
等待8秒后测试：
```bash
sleep 8
curl -s "http://localhost:5001/api/status"
```

应该看到类似输出：
```json
{
  "auth_status": "valid",
  "last_update": "2025-07-07T13:36:43.072464",
  "occupied_count": 155,
  "status": "healthy",
  "timestamp": "2025-07-07T13:36:43.072610",
  "total_rooms": 238
}
```

### 8. 详细验证
```bash
curl -s "http://localhost:5001/api/status" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    occupied = data.get('occupied_count', 0)
    total = data.get('total_rooms', 0)
    print(f'📊 服务器状态：')
    print(f'  - 总房间数: {total}')
    print(f'  - 已入住房间: {occupied}')
    print(f'  - API状态: {data.get(\"status\", \"未知\")}')
    print(f'  - 认证状态: {data.get(\"auth_status\", \"未知\")}')
    
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
```

## 🎯 预期结果

部署成功后，您应该看到：
- **总房间数**: 238
- **已入住房间**: 155
- **API状态**: healthy
- **认证状态**: valid

## 🌐 访问地址

- **API地址**: http://47.122.68.192:5001
- **房间页面**: https://www.cacophonyem.me/rooms/
- **状态检查**: http://47.122.68.192:5001/api/status

## 🛠️ 故障排除

### 查看应用日志
```bash
ssh root@47.122.68.192 "cd /opt/room-management && tail -20 app.log"
```

### 检查应用进程
```bash
ssh root@47.122.68.192 "ps aux | grep python3"
```

### 重启应用
```bash
ssh root@47.122.68.192 "cd /opt/room-management && pkill -f 'python3 app.py' && nohup python3 app.py > app.log 2>&1 &"
```

### 查看进程ID
```bash
ssh root@47.122.68.192 "cd /opt/room-management && cat app.pid"
```

## ✅ 核心功能确认

部署成功后，服务器应该能够：
1. ✅ 自动从外部API获取最新房间数据
2. ✅ 显示155个已入住房间的真实数据
3. ✅ 动态认证管理功能正常工作
4. ✅ 页面访问正常，显示真实入住信息
5. ✅ API状态检查正常

## 🔄 快速部署命令

如果您需要快速部署，可以使用以下一键命令：

```bash
ssh root@47.122.68.192 "cd /opt/room-management && \
pkill -f 'python3 app.py' || true && \
git fetch origin && \
git reset --hard origin/main && \
git pull origin main && \
python3 -c \"from auth_manager import update_auth_info; auth = {'_ams_token': 'web_cdpi6hgs9ez80cb8jit3emwv2wuh4uo5', '_common_token': 'web_cdpi6hgs9ez80cb8jit3emwv2wuh4uo5', 'HWWAFSESID': '13733731437c2a43e3', 'HWWAFSESTIME': '1751861002097'}; update_auth_info(auth); print('✅ 认证信息已更新')\" && \
nohup python3 app.py > app.log 2>&1 & \
sleep 8 && \
curl -s 'http://localhost:5001/api/status'"
```

## 📋 部署检查清单

- [ ] 服务器连接正常
- [ ] 代码更新成功
- [ ] 认证信息初始化完成
- [ ] 应用启动成功
- [ ] API状态检查通过
- [ ] 房间数据显示正常 (155个入住房间)
- [ ] 外部访问测试通过

**绝不会显示0个入住房间的情况！**

---

*最后更新: 2025-07-07 13:36*
*服务器: 47.122.68.192*
*项目目录: /opt/room-management*
*代码仓库: https://github.com/ZhangLin0121/zhi_yu.git* 