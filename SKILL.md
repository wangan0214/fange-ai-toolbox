---
name: fange-html-deck-editor
version: 1.0.0
description: |
  本地 HTML 幻灯片（deck）可视化编辑器：浏览器改字直接落盘 + 单会话 Playwright
  渲染 + 历史快照回滚 + PPT 导出。适用于任何 deck-style HTML（每页用
  `<section class="slide">` 包起来的多页幻灯片）。
triggers:
  - HTML 幻灯片编辑器
  - 改字直接落盘
  - deck 编辑器
  - ppt html 编辑
  - 拖拽排序幻灯片
  - 历史快照回滚
  - html 转 ppt
  - fange html deck editor
inputs:
  - 一个 deck-style HTML 项目目录（含若干 .html，每页用 `<section class="slide">`）
outputs:
  - 修改后的 .html 文件
  - 渲染出的 PNG 预览（每个 slide 一张）
  - 打包好的 16:9 .pptx
  - 历史快照（自动，按时间戳）
---

# fange-html-deck-editor · 本地 HTML 幻灯片编辑器

## 这是什么

一个**完全本地**（127.0.0.1，零外发）的浏览器内编辑器，专门编辑 deck-style HTML
幻灯片（每页 `<section class="slide">`）。跑起来后：

- 左侧缩略图列表 + 右侧大预览，每页文字/HTML 可在浏览器里直接改、改完保存即落盘
- **单会话 Playwright** 渲染（无头 Chrome 起一次，逐页截图）→ 比每页启一次的方案快 10x+
- **历史快照**：每次保存自动留 `.fde_history/<base>/<base>.YYYYMMDDTHHMMSS.ffffff.html`
  （微秒级时间戳防碰撞），保留最近 60 个；UI 一键回滚，回滚前自动保留当前版本
- **导出 PPT**：服务端用 python-pptx 把渲染好的 PNG 打包成 16:9 `.pptx`
- **拖拽排序** / ▲▼ 挪页 / 文件切换 / 拖拽 .html 进编辑器导入

> 数据零外发、零云端依赖、可断网运行。浏览器是唯一交互界面。

## 适用场景

- 你有若干 deck-style HTML 文件需要改字（演讲稿、产品介绍、培训材料）
- 你想所见即所得地改，但不想开 IDE 改源码再重新渲染
- 你需要导出成 PPT 给不会看 HTML 的人看
- 你想要一个「改错能回滚」的本地工作流（每次保存都有快照）

## 不适用

- 普通 Markdown / DOCX 编辑（请用对应 skill）
- 非 deck 结构（每页不是 `<section class="slide">` 的）HTML
- 需要多人协作 / 远端访问的场景（这是纯本地工具）

## 快速使用（5 分钟跑起来）

```bash
# 1. 复制 skill 到任意位置（已装就跳过）
# 假设 skill 在 ~/.workbuddy/skills/fange-html-deck-editor/

# 2. cd 到你的 deck 项目目录（假设是 ~/decks）
cd ~/decks

# 3. 用 skill 自带的一键启动脚本（在 scripts/）
~/.workbuddy/skills/fange-html-deck-editor/scripts/start.command
# 或手动：
python ~/.workbuddy/skills/fange-html-deck-editor/scripts/editor_server.py \
  --root ~/decks --port 8731
```

浏览器自动打开 http://localhost:8731/ ，开始改字。

## 关键设计

| 设计 | 为什么 |
|---|---|
| **保存走 replace-inner**：只把每张 `<section>` 内的 innerHTML 替换为用户改后内容，head / 外链脚本 / 注释一字不动 | 用户改字永远不破坏源码结构，能精确写回 |
| **历史快照微秒级时间戳** | 同秒内「连续保存+回滚」文件名不撞、不丢快照 |
| **路径/文件名只禁 `/ \ ..` 不禁中文** | 中文文件名能正常回滚（不要用 ASCII 白名单） |
| **单会话 Playwright** | 一次起 Chrome 渲染所有页，比每页启进程快 10x+ |
| **UTF-8 URL 双重解码兜底**（`_qs()` 用 latin-1→utf-8 重编码） | 服务端同时兼容裸 UTF-8 与百分号编码两种请求 |
| **拖拽 + 文件选择器双导入** | 顶栏「打开文件」按钮 + 整个编辑区可拖入 .html |
| **UI 变量 `--ui-*` 前缀** | 与幻灯片预览注入的 `--panel/--line/--muted` 完全隔离，杜绝样式串台 |

## 触发词

- "用 HTML 幻灯片编辑器" / "跑个 deck 编辑器" / "改这个 PPT 的字"
- "给 deck 加历史快照" / "支持回滚"
- "把 HTML 转成 PPT"

## 触发后做什么

1. 检查工作目录是否有 deck-style HTML（用 `<section class="slide">` 检索）
2. 启动参数化 `editor_server.py --root <dir>`
3. 自动打开浏览器（或告诉用户打开 http://localhost:8731/）
4. 用户编辑 → 自动每 10s 写本地草稿（防浏览器关闭丢）→ 用户点保存即落盘 + 留快照
5. 用户点导出 PPT → 后台渲染 → 打包 → 自动下载

## 与 fange 其他 skill 的边界

- **不替代** `fange-fengmian-generator` / `fange-shipin-fengmian-generator`：那些是单图封面/海报生成，这是**多页 deck 编辑**
- **不替代** `fange-koubo-script`：那是脚本创作工具，跟 PPT 渲染无关
- **可串联**：`fange-koubo-script` 出逐字稿 → 手工/脚本转 deck HTML → 本 skill 编辑 → 导出 PPT