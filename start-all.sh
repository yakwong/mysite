#!/usr/bin/env bash
# 一次性启动前后端服务
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

printf "==============================\n"
printf "启动前后端服务\n"
printf "==============================\n\n"

printf "[1/2] 启动后端服务\n------------------------------\n"
"$ROOT_DIR/start-backend.sh"
printf "\n"

printf "[2/2] 启动前端服务\n------------------------------\n"
"$ROOT_DIR/start-frontend.sh"
printf "\n"

printf "==============================\n"
printf "所有服务启动完成\n"
printf "==============================\n\n"
printf "后端日志: tail -f /tmp/mysite/backend-dev.log\n"
printf "前端日志: tail -f /tmp/mysite/frontend-dev.log\n"
