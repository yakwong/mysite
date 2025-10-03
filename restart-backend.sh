#!/bin/bash
# 重启后端服务脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "正在重启后端服务..."

# 停止服务
"$SCRIPT_DIR/stop-backend.sh"

# 等待 2 秒
sleep 2

# 启动服务
"$SCRIPT_DIR/start-backend.sh"
