#!/bin/bash
# 房间管理系统部署脚本

echo "开始部署房间管理系统..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
if [ ! -f "requirements.txt" ]; then
    echo "错误: 未找到requirements.txt文件"
    exit 1
fi

# 安装依赖
echo "安装Python依赖..."
python3 -m pip install -r requirements.txt

# 检查必要文件
echo "检查必要文件..."
required_files=("app.py" "templates/index.html" "static/css/style.css" "static/js/app.js")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "错误: 未找到必要文件 $file"
        exit 1
    fi
done

# 检查数据文件
echo "检查数据文件..."
if ! ls complete_rooms_layout_*.json 1> /dev/null 2>&1; then
    echo "错误: 未找到房间数据文件"
    exit 1
fi

# 启动应用
echo "启动房间管理系统..."
echo "访问地址: http://47.122.68.192:5001"
echo "按 Ctrl+C 停止服务"

# 设置环境变量
export FLASK_APP=app.py
export FLASK_ENV=production

# 启动Flask应用
python3 app.py 