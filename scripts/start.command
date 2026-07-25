#!/bin/bash
# FDE HTML 幻灯片编辑器 · 一键启动（macOS）
# 用法：
#   ./start.command                  # 编辑当前目录的所有 deck
#   ./start.command ~/my-decks       # 编辑指定目录的 deck
#   ./start.command ~/my-decks 9000  # 指定端口

set -e

# 解析参数：可选的 ROOT 和 PORT
ROOT="${1:-$(pwd)}"
PORT="${2:-8731}"

# 绝对路径
ROOT="$(cd "$ROOT" && pwd)"

# 找 python（优先用 WorkBuddy 托管 venv，否则用系统 python3）
PY="/Users/fanshuai/.workbuddy/binaries/python/envs/default/bin/python3"
if [ ! -x "$PY" ]; then
  PY="$(command -v python3)"
fi
if [ -z "$PY" ]; then
  echo "❌ 没找到 python3，请先安装 Python 3"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER="$SCRIPT_DIR/editor_server.py"

if [ ! -f "$SERVER" ]; then
  echo "❌ 找不到 $SERVER"
  exit 1
fi

echo "🚀 FDE HTML 幻灯片编辑器启动中..."
echo "   ROOT  = $ROOT"
echo "   PORT  = $PORT"
echo "   PY    = $PY"
echo ""

# 启动浏览器（macOS）
URL="http://localhost:${PORT}/"
(sleep 1 && open "$URL") &

# 启动服务器（前台阻塞，⌘C 退出）
exec "$PY" "$SERVER" --root "$ROOT" --port "$PORT"