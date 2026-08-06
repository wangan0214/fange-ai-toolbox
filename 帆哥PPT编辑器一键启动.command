#!/bin/bash
# 帆哥 PPT 编辑器 · 一键启动
# 启动本地编辑器（localhost:8731），自动在浏览器打开。编辑任意位置的 HTML 幻灯片，原地写回原文件；
# 历史快照 / 渲染产物 / 日志全部存本文件夹（.history / .render / editor.log），绝不污染你的项目目录。
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
PORT=8731

# 选 python：优先本目录 venv，其次托管的 python（自带 PIL + 已验证运行环境），否则系统 python3
MPY="/Users/fanshuai/.workbuddy/binaries/python/versions/3.13.12/bin/python3"
if [ -x "$DIR/.venv/bin/python3" ]; then
  PY="$DIR/.venv/bin/python3"
elif [ -x "$MPY" ]; then
  PY="$MPY"
elif command -v python3 >/dev/null 2>&1; then
  PY="python3"
else
  osascript -e 'display dialog "未找到 python3，无法启动编辑器。" buttons {"好"} default button "好"' 2>/dev/null
  exit 1
fi
# 校验该 python 能 import PIL（PDF/PNG/长图导出依赖）；不能则回退到托管 python
if ! "$PY" -c "import PIL" >/dev/null 2>&1; then
  if [ -x "$MPY" ] && [ "$PY" != "$MPY" ]; then
    PY="$MPY"
  fi
fi

# 已在运行？（root 自动随「打开的 deck」切换，无需重启）
if curl -s --max-time 2 "http://localhost:$PORT/api/root" >/dev/null 2>&1; then
  echo "帆哥 PPT 编辑器已在运行"
else
  LOG="$DIR/editor.log"
  nohup "$PY" "$DIR/scripts/editor_server.py" --port $PORT >"$LOG" 2>&1 &
  for i in $(seq 1 30); do
    if curl -s --max-time 2 "http://localhost:$PORT/api/root" >/dev/null 2>&1; then break; fi
    sleep 0.5
  done
fi
sleep 0.5
open "http://localhost:$PORT"
