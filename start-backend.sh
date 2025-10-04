#!/usr/bin/env bash
# 启动后端开发服务
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
RUN_DIR="$BACKEND_DIR/.run"
LOG_DIR="/tmp/mysite"
PID_FILE="$RUN_DIR/backend.pid"
LOG_FILE="$LOG_DIR/backend-dev.log"
HOST="0.0.0.0"
PORT="8000"

mkdir -p "$RUN_DIR" "$LOG_DIR"

if [ ! -d "$BACKEND_DIR" ]; then
  echo "[后端] 未找到目录: $BACKEND_DIR" >&2
  exit 1
fi

if [ -f "$PID_FILE" ]; then
  EXISTING_PID="$(cat "$PID_FILE")"
  if kill -0 "$EXISTING_PID" 2>/dev/null; then
    echo "[后端] 开发服务已在运行 (PID: $EXISTING_PID)"
    exit 0
  else
    rm -f "$PID_FILE"
  fi
fi

PYTHON_BIN="$BACKEND_DIR/venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "[后端] 未找到可执行的 Python, 请先安装或创建虚拟环境" >&2
    exit 1
  fi
fi

if lsof -i TCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "[后端] 端口 $PORT 已被占用, 启动被取消" >&2
  exit 1
fi

cd "$BACKEND_DIR"

echo "[后端] 启动 Django 开发服务 (日志: $LOG_FILE)"

setsid "$PYTHON_BIN" manage.py runserver "$HOST:$PORT" >>"$LOG_FILE" 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"

sleep 2

if kill -0 "$PID" 2>/dev/null; then
  echo "[后端] 启动成功 (PID: $PID)"
  echo "[后端] 查看日志: tail -f $LOG_FILE"
else
  echo "[后端] 启动失败, 请检查日志: $LOG_FILE" >&2
  rm -f "$PID_FILE"
  exit 1
fi
