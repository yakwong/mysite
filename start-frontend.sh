#!/usr/bin/env bash
# 启动前端开发服务
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
RUN_DIR="$FRONTEND_DIR/.run"
LOG_DIR="/tmp/mysite"
PID_FILE="$RUN_DIR/frontend.pid"
LOG_FILE="$LOG_DIR/frontend-dev.log"

mkdir -p "$RUN_DIR" "$LOG_DIR"

if [ ! -d "$FRONTEND_DIR" ]; then
  echo "[前端] 未找到目录: $FRONTEND_DIR" >&2
  exit 1
fi

if [ -f "$PID_FILE" ]; then
  EXISTING_PID="$(cat "$PID_FILE")"
  if kill -0 "$EXISTING_PID" 2>/dev/null; then
    echo "[前端] 开发服务已在运行 (PID: $EXISTING_PID)"
    exit 0
  else
    rm -f "$PID_FILE"
  fi
fi

if ! command -v pnpm >/dev/null 2>&1; then
  echo "[前端] 未检测到 pnpm, 请先安装 pnpm" >&2
  exit 1
fi

cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
  echo "[前端] 首次运行, 正在安装依赖..."
  pnpm install
fi

echo "[前端] 启动 Vite 开发服务 (日志: $LOG_FILE)"

setsid pnpm dev >>"$LOG_FILE" 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"

sleep 2

if kill -0 "$PID" 2>/dev/null; then
  echo "[前端] 启动成功 (PID: $PID)"
  echo "[前端] 查看日志: tail -f $LOG_FILE"
else
  echo "[前端] 启动失败, 请检查日志: $LOG_FILE" >&2
  rm -f "$PID_FILE"
  exit 1
fi
