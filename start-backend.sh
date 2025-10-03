#!/bin/bash
# 启动后端服务脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
PID_FILE="/tmp/backend.pid"
LOG_FILE="/tmp/backend.log"

# 检查后端服务是否已经运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "后端服务已经在运行 (PID: $PID)"
        exit 0
    else
        echo "清理旧的 PID 文件"
        rm -f "$PID_FILE"
    fi
fi

# 检查后端目录是否存在
if [ ! -d "$BACKEND_DIR" ]; then
    echo "错误: 后端目录不存在: $BACKEND_DIR"
    exit 1
fi

# 进入后端目录
cd "$BACKEND_DIR"

# 检查虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "警告: .env 文件不存在,请先创建 .env 文件"
    echo "可以参考 .env.example 文件"
fi

# 启动后端服务
echo "正在启动后端服务..."
echo "日志文件: $LOG_FILE"

# 使用 nohup 在后台启动,并将 PID 保存
nohup python manage.py runserver 0.0.0.0:8000 > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

sleep 2

# 验证服务是否成功启动
if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
    echo "后端服务启动成功 (PID: $(cat "$PID_FILE"))"
    echo "可以通过以下命令查看日志: tail -f $LOG_FILE"
else
    echo "后端服务启动失败,请查看日志: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
