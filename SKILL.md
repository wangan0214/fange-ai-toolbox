---
name: fange-html-deck-editor
version: 1.0.13
description: |
  本地 HTML 幻灯片（deck）可视化编辑器：浏览器改字直接落盘 + 单会话 Playwright
  渲染 + 历史快照回滚 + 三层可编辑 PPT 导出 + 一键上传飞书云空间。适用于任何
  deck-style HTML（每页用 `<section class="slide">` 包起来的多页幻灯片）。
  是「guizang-ppt-skill（生成HTML）→ 本工具（改字精修）→ 导出PPTX / 上传飞书」
  交付链路的一环，与 feishu-html-slides 的飞书交付路径打通。
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
  - 可编辑 16:9 .pptx（**三层结构**：① 干净背景图 → ② 色块独立矩形 → ③ 文字独立文本框），**默认模式**
  - 高清整页图 16:9 .pptx（每页：2× 高分辨率整页截图，不可改字），**可选模式**
  - 历史快照（自动，按时间戳）
  - 飞书云空间上传（「更多 ▾」一键把当前 HTML 或已导出 PPTX 经 lark-cli 传到飞书云空间）
---

# fange-html-deck-editor · 本地 HTML 幻灯片编辑器

## 这是什么

一个**完全本地**（127.0.0.1，零外发）的浏览器内编辑器，专门编辑 deck-style HTML
幻灯片（每页 `<section class="slide">`）。跑起来后：

- 左侧缩略图列表 + 右侧大预览，每页文字/HTML 可在浏览器里直接改、改完保存即落盘
- **单会话 Playwright** 渲染（无头 Chrome 起一次，逐页截图）→ 比每页启一次的方案快 10x+
- **历史快照**：每次保存自动留 `.fde_history/<base>/<base>.YYYYMMDDTHHMMSS.ffffff.html`
  （微秒级时间戳防碰撞），保留最近 60 个；UI 一键回滚，回滚前自动保留当前版本
- **导出 PPT**：顶栏下拉选「可编辑版 / 高清整页图」两种模式，服务端用 python-pptx 打包成 16:9 `.pptx`
- **拖拽排序** / ▲▼ 挪页 / 文件切换 / 拖拽 .html 进编辑器导入
- **上传飞书云空间**：「更多 ▾」里把当前 HTML 或已导出的 PPTX 一键 `lark-cli drive +upload` 到飞书云空间（链接自动复制并打开），把 `feishu-html-slides` 的飞书交付路径真正落地。**上传前先做授权校验**：未授权/未绑定飞书账号（或缺少 `drive:file:upload` 权限）时，前端弹出引导框提示执行 `lark-cli auth login` 授权后再重试，避免误传失败

> 默认数据零外发、零云端依赖、可断网运行；**仅「上传飞书云空间」会与飞书交互**（经本机 lark-cli）。浏览器是唯一编辑界面。

## 适用场景

- 你有若干 deck-style HTML 文件需要改字（演讲稿、产品介绍、培训材料）
- 你想所见即所得地改，但不想开 IDE 改源码再重新渲染
- 你需要导出成 PPT 给不会看 HTML 的人看
- 你想要一个「改错能回滚」的本地工作流（每次保存都有快照）

## 不适用

- 普通 Markdown / DOCX 编辑（请用对应 skill）
- 非 deck 结构（每页不是 `<section class="slide">` 的）HTML
- 需要多人实时协作编辑的场景（本工具是单人本地编辑；但「上传飞书云空间」可把成品发到飞书供他人查看 / 评论）

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
| **可编辑 PPT 按浏览器视觉行拆框** | 用 DOM Range 逐字符读取真实换行；每个视觉行独立文本框、清零内边距并禁止 PowerPoint 二次断行，避免多行标题被压成一行或冲出页面 |
| **可编辑 PPT 三层结构（背景/色块/文字）** | 背景图用 `visibility:hidden` 注入 CSS 去掉文字+实色块（保留图片/SVG/canvas/网格/页脚，用 `:has()` 保护媒体祖先）；色块按 DOM 顺序作为独立 PPTX 矩形（实色填充 / 仅边框 / 圆角）添加；文字最后添加永远在最上层 —— 背景更干净、元素更多独立可编辑 |
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
6. （可选）用户点「上传飞书云空间」→ 当前 HTML 或导出 PPTX 经 lark-cli 上传到飞书云空间

## 与 fange 其他 skill 的边界

- **不替代** `fange-fengmian-generator` / `fange-shipin-fengmian-generator`：那些是单图封面/海报生成，这是**多页 deck 编辑**
- **不替代** `fange-koubo-script`：那是脚本创作工具，跟 PPT 渲染无关
- **串联 guizang-ppt-skill**（归藏PPT）：它生成 deck HTML（FDE 瑞士现代红片子即其瑞士风骨架 `red accent` 定制版），本工具直接打开编辑、改字精修
- **打通 feishu-html-slides**（飞书 HTML 幻灯片）：它的工作流是「生成 HTML → 上传飞书云空间 / 部署妙搭」；本工具的「上传飞书云空间」按钮正是把后半段飞书交付真正落地（用 `lark-cli drive +upload`）
- **可串联**：`fange-koubo-script` 出逐字稿 → 手工/脚本转 deck HTML → 本 skill 编辑 → 导出 PPT / 上传飞书

## 迭代记录

### v1.0.13（2026-07-30）跨文件尺寸探测 + slide-bg 重置

**两个根因 + 一处加固，全是 buildEditor 上下文里跑出来的问题，不是源 HTML 的问题：**

1. **measureSrc 跨文件 CSS 污染**（核心 bug）
   - 旧逻辑：把源 `.slide` cloneNode 后插到主 document 的 `meas` 容器里，读 `probe.offsetWidth`。
   - **问题**：主 document 里已经注入了**上一次** buildEditor 注入的源 CSS（EP25 残留 `min-width:1280px`），第二次测 FDE 时 probe 被残留 CSS 压成 1280。
   - 修复：优先扫 doc 自己的 `<style>` 找 `.slide` 固定 width（FDE `1920px`、EP25 `1280px` 都能一次命中），扫不到才走 probe，且 probe 改放到**独立 iframe** 里测（隔离主 document CSS）。
   - 现象对比：
     - 修复前：FDE 加载后 `--sw=1280, --sc=0.75` → H1（`font-size:132px; width:1560px`）缩放后 1170px > 960px slide-frame → 整段被 `overflow:hidden` 裁掉（P01 "是商业逻辑里的一环" 右半截消失、P02 "它赚的，是「让企业用" 被裁成"它赚的，最"）
     - 修复后：FDE 加载后 `--sw=1920, --sc=0.5` → H1 缩放后 780px 装在 960px slide-frame 内 ✓

2. **slide-bg inline style 残留**
   - 旧逻辑：`if(bgLayers.length) editor.style.setProperty('--slide-bg','transparent')`——只在有背景层时设 transparent，没背景层时**不动** #editor 的 inline style。
   - **问题**：上次 buildEditor 把 `transparent` 写到 #editor 的 inline style，下次无背景层源**不重置**，CSS 变量继承上 inline 优先 → `.slide{background:var(--slide-bg,#ffffff)!important}` 解析为 `transparent` → 整页变黑底黑字。
   - 修复：每次 buildEditor 开头 `editor.style.removeProperty('--slide-bg')` 先清掉，**再**根据 `bgLayers` 决定要不要设 transparent。

3. **（加固）`editor-override-css` 兜底**
   - 保留 `:root{--slide-bg:#ffffff;...}` 和 `.slide{background:var(--slide-bg,#ffffff)!important}` 双保险，**变量 fallback #ffffff** 必须写死（去掉 fallback 写空会让背景变 transparent）。
   - 实际生效链：`#orig-css :root` → `:root` 兜底 → `#editor` inline 覆盖（清空后取 #orig-css 的值）→ `.slide` 计算时按级联解析。

**为什么 v1.0.12 没发现**：v1.0.12 只修浏览器 disk cache（`Cache-Control: no-store`），但首屏加载或切文件时主 document CSS 残留 ≠ 缓存问题，是**逻辑顺序问题**，缓存无关。无痕模式 / 硬刷都没用，必须修 measureSrc 隔离 + slide-bg 重置。

**回归范围**（v1.0.13 修复后实测）：
- FDE 瑞士现代 v2（1920×1080）首次加载：sw=1920, sc=0.5, slideBg=白 ✓
- 切 v1.3 (1280×720) → 切回 FDE 瑞士现代：sw=1920, sc=0.5, slideBg=白 ✓（之前 sw=1280 黑底）
- 直接打开 editor.html（默认就是 FDE 瑞士现代）：sw=1920, sc=0.5, slideBg=白 ✓
- P1 完整："FDE 不是个岗位，是商业逻辑里的一环" 不再被裁
- P2 完整："它赚的，是「让企业用上 AI」这段价值链的钱" 不再被裁

### v1.0.12（2026-07-30）编辑器 Chrome disk cache 导致内容被裁

`editor_server.py` 加 `Cache-Control: no-store, no-cache, must-revalidate, max-age=0` + `Pragma: no-cache` + `Expires: 0`，每次 GET 重读 `EDITOR_HTML` 模板，强制浏览器不缓存旧版 editor.html。避免 v1.0.11 之前版本（缺 transform:scale 缩放规则）被 disk cache 缓存后，内容被 960px slide-frame overflow:hidden 裁切。

### v1.0.10（2026-07-25）导出 PPT 锁定精确 16:9 / 1920×1080

`build_editable_pptx` / `build_image_pptx` / legacy `build_pptx` 的 `prs.slide_width/height` 改用精确 `Emu(12192000)/Emu(6858000)`（替代 `Inches(13.333)` 浮点截断），加显式注释防误改 4:3。