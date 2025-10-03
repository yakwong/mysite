#!/bin/bash
# 关闭后端服务脚本

PID_FILE="/tmp/backend.pid"

# 检查 PID 文件是否存在
if [ ! -f "$PID_FILE" ]; then
    echo "后端服务未运行"
    exit 0
fi

PID=$(cat "$PID_FILE")

# 检查进程是否存在
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "后端服务未运行"
    rm -f "$PID_FILE"
    exit 0
fi

# 停止服务
echo "正在停止后端服务 (PID: $PID)..."
kill "$PID"

# 等待进程结束
for i in {1..10}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo "后端服务已停止"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# 如果进程仍在运行,强制杀死
if ps -p "$PID" > /dev/null 2>&1; then
    echo "强制停止后端服务..."
    kill -9 "$PID"
    sleep 1
fi

rm -f "$PID_FILE"
echo "后端服务已停止"
