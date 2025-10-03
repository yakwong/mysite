#!/bin/bash
# 启动前端服务脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
PID_FILE="/tmp/frontend.pid"
LOG_FILE="/tmp/frontend.log"

# 检查前端服务是否已经运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "前端服务已经在运行 (PID: $PID)"
        exit 0
    else
        echo "清理旧的 PID 文件"
        rm -f "$PID_FILE"
    fi
fi

# 检查前端目录是否存在
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "错误: 前端目录不存在: $FRONTEND_DIR"
    exit 1
fi

# 进入前端目录
cd "$FRONTEND_DIR"

# 检查 node_modules 是否存在
if [ ! -d "node_modules" ]; then
    echo "正在安装前端依赖..."
    pnpm install
fi

# 启动前端服务
echo "正在启动前端服务..."
echo "日志文件: $LOG_FILE"

# 使用 nohup 在后台启动,并将 PID 保存
nohup pnpm dev > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

sleep 2

# 验证服务是否成功启动
if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
    echo "前端服务启动成功 (PID: $(cat "$PID_FILE"))"
    echo "可以通过以下命令查看日志: tail -f $LOG_FILE"
else
    echo "前端服务启动失败,请查看日志: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
