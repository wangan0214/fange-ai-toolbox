#!/bin/bash
# 把 skill 提供的启动器 + 桌面快捷方式安装到当前项目目录
# 用法：在项目目录里跑 ./install.sh

set -e

# 找 skill 根目录（向上两级：scripts/install.sh → skill root）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(dirname "$SCRIPT_DIR")"

PROJECT_DIR="$(pwd)"
PROJECT_NAME="$(basename "$PROJECT_DIR")"
PORT="${PORT:-8731}"

# 1. 复制 start.command 到项目根，重命名为「<项目名>HTML编辑器一键启动.command」
LAUNCHER="$PROJECT_DIR/${PROJECT_NAME}HTML编辑器一键启动.command"
cp "$SCRIPT_DIR/start.command" "$LAUNCHER"
chmod +x "$LAUNCHER"

# 2. 创建 .webloc（macOS 网页快捷方式，自动打开浏览器到编辑器）
WEBLOC="$PROJECT_DIR/${PROJECT_NAME}HTML编辑器.webloc"
cat > "$WEBLOC" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>URL</key>
    <string>http://localhost:${PORT}/</string>
</dict>
</plist>
EOF

echo "✅ 已安装到 $PROJECT_DIR"
echo ""
echo "  🚀 启动编辑器：双击 ${LAUNCHER##*/}"
echo "  🌐 浏览器打开：双击 ${WEBLOC##*/}"
echo "  📁 编辑器已锁定 ROOT=$PROJECT_DIR"
echo ""
echo "提示："
echo "  - 启动后浏览器会自动打开 http://localhost:${PORT}/"
echo "  - ⌘S 保存，⌘Q 退出"
echo "  - 每次保存自动留历史快照到 .fde_history/，UI 历史按钮可回滚"