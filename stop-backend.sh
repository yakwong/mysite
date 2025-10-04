#!/usr/bin/env bash
# 停止后端开发服务
set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/backend"
PID_FILE="$BACKEND_DIR/.run/backend.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "[后端] 未检测到运行中的服务"
  exit 0
fi

PID="$(cat "$PID_FILE")"
if ! kill -0 "$PID" 2>/dev/null; then
  echo "[后端] 记录的进程不存在, 清理 PID 文件"
  rm -f "$PID_FILE"
  exit 0
fi

echo "[后端] 正在停止服务 (PID: $PID)"

kill -- -"$PID" 2>/dev/null || kill "$PID" 2>/dev/null || true

for _ in {1..10}; do
  if ! kill -0 "$PID" 2>/dev/null; then
    echo "[后端] 服务已停止"
    rm -f "$PID_FILE"
    exit 0
  fi
  sleep 1
done

echo "[后端] 服务仍在运行, 强制结束"
kill -9 -- -"$PID" 2>/dev/null || kill -9 "$PID" 2>/dev/null
sleep 1
rm -f "$PID_FILE"
echo "[后端] 服务已强制停止"
