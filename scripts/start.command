#!/bin/bash
# 帆哥PPT编辑器 · 一键启动 (v1.0.21: root 跟「脚本所在 deck 目录」走，自动检测重启)
#
# 核心规则：启动器所在目录 = 编辑器的 root
#   - 若启动器旁边有 index.html（说明你把它放在某个 deck 目录里）→ root = 该 deck 目录
#   - 否则（启动器在 fde_editor/ 或 scripts/ 里，没有 index.html）→ root = 12-FDE研究（向后兼容）
#
# 用法（三选一，越靠前越优先）：
#   1) 把本文件复制到「要编辑的 deck 目录」（和 index.html 同级），双击 → root 自动 = 那个 deck ✅ 最推荐
#   2) 命令行：FDE_ROOT=/path/to/deck 一键启动.command   或   一键启动.command /path/to/deck
#   3) 直接双击 fde_editor/ 里的本文件 → root = 12-FDE研究（编辑 FDE 系列 deck 用）
#
# 智能重启：若 8731 上已在跑、但 root 不是你要的 deck，会自动杀掉旧实例、用正确 root 重启。
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 自动定位 editor_server.py（兼容 fde_editor/scripts/ 与 scripts/ 两种布局）
if [ -f "$SCRIPT_DIR/scripts/editor_server.py" ]; then
  SRV="$SCRIPT_DIR/scripts/editor_server.py"
elif [ -f "$SCRIPT_DIR/editor_server.py" ]; then
  SRV="$SCRIPT_DIR/editor_server.py"
else
  echo "❌ 找不到 editor_server.py（请在 fde_editor/ 或 scripts/ 目录下运行本启动器）"; exit 1
fi

PYTHON="/Users/fanshuai/.workbuddy/binaries/python/versions/3.13.12/bin/python3"
[ ! -x "$PYTHON" ] && PYTHON="$(which python3)"

# root 优先级：参数 $1 > 环境变量 FDE_ROOT > 脚本所在目录(若是 deck) > 兜底 12-FDE研究
ROOT_DIR="${1:-$FDE_ROOT}"
if [ -z "$ROOT_DIR" ]; then
  if [ -f "$SCRIPT_DIR/index.html" ]; then
    ROOT_DIR="$SCRIPT_DIR"            # 放在 deck 目录里 → root 就是它
  else
    ROOT_DIR="/Users/fanshuai/Documents/搞钱集中营/12-FDE研究"
  fi
fi

start_editor() {
  LOG="$ROOT_DIR/.fde_editor.log"
  nohup "$PYTHON" "$SRV" --root "$ROOT_DIR" --port 8731 >"$LOG" 2>&1 &
  sleep 1.5
}

# 检测 8731 是否已在跑，且 root 是否匹配
RUNNING_ROOT=""
if curl -s "http://localhost:8731/api/root" 2>/dev/null | grep -q '"root"'; then
  RUNNING_ROOT="$(curl -s "http://localhost:8731/api/root" 2>/dev/null | sed -n 's/.*"root"[ ]*:[ ]*"\([^"]*\)".*/\1/p')"
fi

if [ -n "$RUNNING_ROOT" ]; then
  if [ "$RUNNING_ROOT" = "$ROOT_DIR" ]; then
    echo "编辑器已在运行（root=$ROOT_DIR），直接打开浏览器。"
  else
    echo "8731 上跑的是 root=$RUNNING_ROOT，与本次目标 root=$ROOT_DIR 不同 → 自动重启到正确 deck。"
    pkill -f "editor_server.py --root" 2>/dev/null
    sleep 1
    start_editor
  fi
else
  # 没有有效实例（端口空闲 / 旧版无 /api/root 端点）→ 先清掉可能残留的旧进程再启动
  pkill -f "editor_server.py" 2>/dev/null
  sleep 1
  start_editor
fi

open "http://localhost:8731"
