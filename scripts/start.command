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

# 找 python：优先系统 python3（需自行 pip install playwright），
# 若在 WorkBuddy 托管环境则回退到其 venv（已含 playwright）
PY="$(command -v python3 || command -v python)"
if [ -z "$PY" ]; then
  MANAGED="/Users/fanshuai/.workbuddy/binaries/python/envs/default/bin/python3"
  [ -x "$MANAGED" ] && PY="$MANAGED"
fi
if [ -z "$PY" ]; then
  echo "❌ 没找到 python3，请先安装 Python 3（并 pip install playwright）"
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