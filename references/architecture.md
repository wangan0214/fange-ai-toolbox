# fange-html-deck-editor · 架构与实现

## 整体流程

```
┌─────────────────┐    启动    ┌────────────────────────────┐
│ start.command   │ ─────────▶ │ editor_server.py --root X  │
└─────────────────┘            └─────────────┬──────────────┘
                                              │ 127.0.0.1:8731
                                              ▼
┌────────────────────────────────────────────────────────────────┐
│                          浏览器 (Chromium)                       │
│  ┌─────────┐  ┌──────────────────────────────────────────────┐ │
│  │  顶栏   │  │ 文件切换│打开│保存⌘S│[导出模式+导出PPT]│更多▾│状态 │
│  └─────────┘  │  「更多▾」下拉：保存并渲染·仅渲染·放大编辑·导出HTML·历史·放弃重读 │
│               └──────────────────────────────────────────────┘ │
│  ┌─────────┐  ┌──────────────────────────────────────────────┐ │
│  │  侧栏   │  │           编辑区（缩略图 / 1:1 放大）           │ │
│  │ 缩略图  │  │  每页 <section class="slide"> 渲染 + contenteditable│
│  │ 拖拽排序│  └──────────────────────────────────────────────┘ │
│  └─────────┘                                                    │
└────────────────────────────────────────────────────────────────┘
        │                                    │
        │ POST /api/save                     │ POST /api/render
        ▼                                    ▼
┌────────────────────────┐         ┌────────────────────────────┐
│  原子写回源 .html       │         │  单会话 Playwright (Chrome) │
│  + 留历史快照            │         │  逐页 deck.showSlide(i) 截图 │
│  .fde_history/<base>/   │         └─────────────┬──────────────┘
│  <base>.YYYYMMDDTHHMMSS.│                       │
│  ffffff.html            │                       ▼
└────────────────────────┘         ┌────────────────────────────┐
                                   │  PNG × N（每页一张）         │
                                   └─────────────┬──────────────┘
                                                 │
                                                 ▼
                                   ┌────────────────────────────┐
                                   │  python-pptx 打包 16:9 .pptx│
                                   │  → /api/download-pptx 下载  │
                                   └────────────────────────────┘
```

## 关键模块

### 1. 编辑器 UI（templates/editor.html）

**单文件 HTML**（无构建步骤），CSS+JS 全部内联，浏览器打开即用。

**4 个核心数据结构**：

```js
let RAW = "";          // 源文件原文，保存时只替换每 slide 内部内容
let order = [];        // order[显示位置 dp] = 原始索引（用于重排映射）
let editedSlides = [];  // 已编辑的 slide DOM 节点（按显示位置索引）
let sideItems = [], wrapEls = [];  // 侧栏 / 编辑区 DOM（按显示位置索引）
```

**保存的「无损写回」机制**（最关键）：

```js
function buildHtml(){
  // 正则匹配每个 (可选注释) + <section class="slide">...</section> 块
  const unitRe = /(<!--[\s\S]*?-->)?\s*(<section class="slide"[^>]*>)([\s\S]*?)(<\/section>)/g;
  // 仅替换 inner，保留 head / 外链脚本 / 注释 / 外层标签
  // 按 order 重组：head/deck 脚本零修改，slide 块按当前显示顺序拼回
  return pre + body + post;
}
```

**保证**：用户在编辑器里改字，保存前后文件 `diff` 只改动了用户实际改的 `<section>` 内部的字符。源文件里所有外链 CSS/JS、head 注释、Google Fonts 链接、deck 控制脚本**全部一字不动**。

### 2. 后端服务（scripts/editor_server.py）

**纯 http.server + ThreadingTCPServer**（无 Flask/Django 依赖），零外部依赖：

```python
import http.server, socketserver  # 标准库
```

**核心 API**：

| 端点 | 方法 | 作用 |
|---|---|---|
| `/` | GET | 返回编辑器 HTML |
| `/api/files` | GET | 列 ALLOWED_ROOT 下所有 .html（过滤隐藏目录 / 渲染残片） |
| `/api/load?file=` | GET | 读取源文件全文 |
| `/api/save` | POST | 原子写回（tmp + os.replace） + 自动留历史快照 |
| `/api/render` | POST | 后台启动单会话 Playwright 渲染 |
| `/api/render-status` | GET | 渲染进度（运行中 / 完成 / 取消 / 错误） |
| `/api/export-pptx` | POST | 渲染 + python-pptx 打包 16:9 .pptx |
| `/api/download-pptx` | GET | 下载 .pptx |
| `/api/history?file=` | GET | 列出该文件历史快照 |
| `/api/history-file?file=&snap=` | GET | 读取某个快照（预览/下载） |
| `/api/rollback` | POST | 回滚到快照（回滚前自动留当前版快照） |

**关键安全/健壮性细节**：

- `safe_abs(rel)`：防 `..` 穿越 + 强制 `.html` 扩展名
- `safe_snap(snap)`：禁 `/ \ ..` 即可，**允许 UTF-8**（中文快照名能正常回滚）
- `_qs()`：先 `self.path.encode("latin-1").decode("utf-8")` 还原字节，**同时兼容裸 UTF-8 与百分号编码两种请求**（http.server 默认按 Latin-1 解码路径会污染中文）
- 路径白名单只允许 `ALLOWED_ROOT` 内

### 3. 渲染器（scripts/render_slides_pw.py）

**单会话 Playwright**（关键性能优化）：

```python
# 一次启动 Chrome → 复用 page → 逐页 deck.showSlide(i) → screenshot
# 比每页启一次 Playwright 快 10x+
def main():
    browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
    page = browser.new_page(viewport={"width":1920,"height":1080})
    page.goto(src_url)
    page.wait_for_load_state("domcontentloaded")  # 用 DOMContentLoaded 不用 load
    for i in range(count_slides(src)):
        page.evaluate(f"deck.showSlide({i})")
        page.wait_for_timeout(800)  # 让动画/字体落定
        page.screenshot(path=f"{base}-{i+1:02d}.png")
    browser.close()
```

**注意**：`wait_for_load_state("domcontentloaded")` 而非 `"load"`，否则在 `virtual-time-budget` 内 Google Fonts / 大图可能未触发导致空白白图。

### 4. 历史快照

```
.fde_history/
  <base>/
    <base>.20260725T191950696387.html    # 微秒时间戳，同秒多次也唯一
    <base>.20260725T192012123456.html
    ...
```

- 时间戳格式：`YYYYMMDDTHHMMSS` + 6 位微秒（`"%06d" % (time.time()%1*1e6)`）
- 每文件保留最近 60 个，超出删最旧
- **回滚前**自动 `save_snapshot(rel, current_html)` 留当前版（永可再退）

### 5. 三层可编辑 PPT 导出 (scripts/export_editable_pptx.py)

`build_editable_pptx(src)` 对每页生成三层独立 shape，导出后在 PowerPoint 里每一层都可单独编辑/删除/改色：

```
┌─────────────────────────────────────────────────────────────┐
│ 第 1 层 干净背景图（_bg_P*.png）                              │
│   注入 CSS: section.slide[data-clean] :not(...) {visibility:hidden} │
│   仅保留: IMG / SVG / CANVAS / .grid-lines / .chrome(及其子树) │
│   全局隐藏: .progress / .progress-fill / .edit-toggle(浏览器 UI) │
│   → 背景= 幻灯片底色 + 网格 + 配图 + 页脚 chrome               │
├─────────────────────────────────────────────────────────────┤
│ 第 2 层 色块独立矩形                                          │
│   DOM 遍历提取: 实色填充块 + 仅边框块（如 .duo .panel）          │
│   排除: 根底/.grid-lines/含媒体元素/渐变背景块（留在背景图）       │
│   pptx: MSO_SHAPE.RECTANGLE / ROUNDED_RECTANGLE              │
│         fill 实色 / background() 无填充                         │
│         line 边框色+宽(px→pt×0.5) / fill.background() 无边框    │
│   顺序: DOM 文档顺序 → 保证嵌套（白卡内红卡）层级正确              │
├─────────────────────────────────────────────────────────────┤
│ 第 3 层 文字独立文本框（永远在最上层）                            │
│   DOM Range 提取视觉行 → 每行独立文本框                          │
│   word_wrap=False / margin=0 / 字号 pt×0.5                      │
└─────────────────────────────────────────────────────────────┘
```

**关键技术细节**：

- `visibility:hidden` 而非 `display:none` 隐藏块 → flex 子项不重排，坐标不偏移
- `:not(:has(IMG, SVG, CANVAS))` 保护含媒体的祖先不被链式隐藏（否则 `.fig` 被隐藏后配图一起消失）
- 色块用 DOM 顺序绘制 → 内层 hot 块在外层 card 之上
- 文字最后添加 → 永远在所有色块之上（包括跨嵌套）
- preview-P*.png 保留完整渲染（供编辑器预览/缩略图），_bg_P*.png 是干净背景（仅 PPTX 用）

## 启动方式

### 一键（macOS）

```bash
# 默认：编辑所在目录的所有 deck
./scripts/start.command

# 或指定项目目录
./scripts/start.command ~/decks
```

### 手动

```bash
python scripts/editor_server.py \
  --root /path/to/decks \
  --port 8731 \
  --default index.html   # 不传则用 root 下第一个 .html
```

### 安装到项目

```bash
# 把 skill 提供的安装脚本丢到目标项目目录里
cp scripts/install.sh /path/to/your-project/
cd /path/to/your-project
./install.sh
# 会生成 ./启动编辑器.command 和 ./打开编辑器.webloc
```

## 已知约束

| 约束 | 原因 | 缓解 |
|---|---|---|
| 仅 deck 结构有效 | 设计假设每页 `<section class="slide">` | 切到非 deck 文件给明确 err 提示 |
| 单文件同时编辑 | 全局 `RAW / order / editedSlides` | 想同时编辑多文件 → 开多个浏览器标签（每个标签独立状态） |
| 可编辑 PPT 是「干净背景 + 独立色块 + 独立文字」三层 | 浏览器渲染天然是位图 → 背景必须是图 | 文字/色块全部独立为可编辑形状（背景图保留图片/网格/页脚等无法矢量化的视觉）；样式仍不能像真 PPT 那样自由变换 |
| 自动草稿走 localStorage | 浏览器唯一 | 关浏览器不会丢，但清缓存就丢——所以点了「保存」才会留服务器快照 |

## 适用扩展方向

- **支持 Markdown 源**：用户写 .md，编辑器渲染成 deck（需改 buildHtml 与 RAW）
- **多 deck 项目分组**：左侧侧栏加 deck 列表而非页面列表（改动 buildEditor 与 sidebar）
- **A/B 预览**：左右分屏对比改前改后（成本：双 editor 节点 + 同步滚动）
- **Git 集成**：每次保存自动 `git commit`（加 git 钩子）