#!/usr/bin/env bash
# 查看前后端开发服务状态
set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/tmp/mysite"
LSOF_AVAILABLE=0
if command -v lsof >/dev/null 2>&1; then
  LSOF_AVAILABLE=1
fi

format_time() {
  local file_path="$1"
  if [ ! -f "$file_path" ]; then
    echo ""
    return
  fi
  if date -r "$file_path" "+%Y-%m-%d %H:%M:%S" >/dev/null 2>&1; then
    date -r "$file_path" "+%Y-%m-%d %H:%M:%S"
    return
  fi
  if stat -c '%y' "$file_path" >/dev/null 2>&1; then
    stat -c '%y' "$file_path" | cut -d'.' -f1
    return
  fi
  if stat -f '%Sm' -t '%Y-%m-%d %H:%M:%S' "$file_path" >/dev/null 2>&1; then
    stat -f '%Sm' -t '%Y-%m-%d %H:%M:%S' "$file_path"
    return
  fi
  echo "未知"
}

print_service() {
  local name="$1"
  local pid_file="$2"
  local port="$3"
  local log_file="$4"

  echo "[$name]"

  if [ ! -f "$pid_file" ]; then
    echo "  状态 : 未运行 (缺少 PID 文件)"
  else
    local pid
    pid="$(cat "$pid_file" 2>/dev/null || true)"
    if [ -z "$pid" ]; then
      echo "  状态 : 未运行 (PID 文件为空)"
    elif kill -0 "$pid" 2>/dev/null; then
      local cmd args start_time
      cmd="$(ps -p "$pid" -o comm= 2>/dev/null || echo "未知")"
      args="$(ps -p "$pid" -o args= 2>/dev/null || echo "未知")"
      start_time="$(ps -p "$pid" -o lstart= 2>/dev/null || echo "未知")"
      echo "  状态 : 运行中"
      echo "  PID   : $pid"
      echo "  启动 : $start_time"
      echo "  命令 : $args"
    else
      echo "  状态 : 未运行 (PID $pid 已失效)"
    fi
  fi

  if [ "$LSOF_AVAILABLE" -eq 1 ]; then
    local listeners
    listeners="$(lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null | sort -u | tr '\n' ' ')"
    if [ -n "$listeners" ]; then
      listeners="${listeners% }"
      echo "  端口 : $port (监听 PID: $listeners)"
    else
      echo "  端口 : $port (未检测到监听进程)"
    fi
  else
    echo "  端口 : $port (未检测到监听进程; 未安装 lsof)"
  fi

  if [ -n "$log_file" ]; then
    if [ -f "$log_file" ]; then
      local mtime size
      mtime="$(format_time "$log_file")"
      size="$(wc -c "$log_file" 2>/dev/null | awk '{print $1}' | sed 's/$/ bytes/' )"
      echo "  日志 : $log_file (存在, 最近更新: ${mtime:-未知}, 大小: ${size:-未知})"
    else
      echo "  日志 : $log_file (未找到)"
    fi
  fi

  echo
}

BACKEND_PID_FILE="$SCRIPT_DIR/backend/.run/backend.pid"
FRONTEND_PID_FILE="$SCRIPT_DIR/frontend/.run/frontend.pid"
BACKEND_LOG="$LOG_DIR/backend-dev.log"
FRONTEND_LOG="$LOG_DIR/frontend-dev.log"

print_service "后端" "$BACKEND_PID_FILE" 8000 "$BACKEND_LOG"
print_service "前端" "$FRONTEND_PID_FILE" 8848 "$FRONTEND_LOG"

if [ "$LSOF_AVAILABLE" -ne 1 ]; then
  echo "提示: 未安装 lsof, 无法检测端口监听状态。请使用包管理器安装 lsof 后重试。"
fi
