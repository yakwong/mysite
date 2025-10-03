#!/bin/bash
# 重启前端服务脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "正在重启前端服务..."

# 停止服务
"$SCRIPT_DIR/stop-frontend.sh"

# 等待 2 秒
sleep 2

# 启动服务
"$SCRIPT_DIR/start-frontend.sh"
