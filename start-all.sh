#!/bin/bash
# 启动前后端服务脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "================================"
echo "启动前后端服务"
echo "================================"
echo ""

# 启动后端服务
echo "1. 启动后端服务"
echo "--------------------------------"
"$SCRIPT_DIR/start-backend.sh"
echo ""

# 启动前端服务
echo "2. 启动前端服务"
echo "--------------------------------"
"$SCRIPT_DIR/start-frontend.sh"
echo ""

echo "================================"
echo "所有服务启动完成"
echo "================================"
echo ""
echo "前端日志: tail -f /tmp/frontend.log"
echo "后端日志: tail -f /tmp/backend.log"
