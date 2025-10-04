#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

printf "[后端] 重启服务\n"
"$ROOT_DIR/stop-backend.sh"
sleep 1
"$ROOT_DIR/start-backend.sh"
