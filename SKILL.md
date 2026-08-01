---
name: fange-html-deck-editor
version: 1.0.19
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

### v1.0.19（2026-08-01）撤销/重做栈 + 修样式模式自动放大
- **撤销栈（用户强需求："所有改动都应该有撤回的能力"）**：顶栏新增「↶ 撤销 / ↷ 重做」按钮 + ⌘Z / ⌘⇧Z（及 Ctrl+Y）快捷键，全局接管，覆盖**文字编辑、画布拖拽、属性面板、重置 inline style、设为 absolute、页面顺序重排**全部改动类型。
  - 快照 = `{order: 原始索引排列, html: 各显示页 innerHTML}`。因 `editedSlides[dp]` 就是用户直接改的 `.slide-wrap .slide` clone，回写 innerHTML 即同时恢复「显示」与「保存真相」（save 直接读它）。
  - 顺序重排通过 `applyOrder(newOrder)` 把 `order/sideItems/wrapEls/editedSlides` 四个数组按快照 order 重新排列并 `reflow()`，从而完整撤销页面顺序调整。
  - 防抖：文字输入连续触发 `input` 事件，500ms 防抖合并成一步；其余改动（拖拽/属性/顺序）在动作结束立即压栈。与栈顶比较，无实质变化不压栈（避免拖拽未动等噪声）。
  - 每次加载/重读文件 `slideHistory=[]; histIdx=-1; pushHistory()` 重置历史，避免跨文件混合。
- **修样式模式自动放大（用户反馈"会突然放大页面，很奇怪"）**：删掉 `enterStyleMode` 里自动 `toggleZoom/applyZoom` 的逻辑。拖拽坐标全程在源像素空间算（mouse delta ÷ 画布 transform:scale），缩略图下也能精确拖拽，无需放大。用户想精确点选可手动点「放大编辑当前页」。

### v1.0.18（2026-07-31）画布直接拖拽 + 自动对齐辅助线（WYSIWYG）

**动机**：v1.0.17 的 Properties 面板（数字输入框）被用户明确否决——"不能拖拽式的交互吗？所见即所得嘛，然后做好自动的对齐不行吗？你这个交互方式我不太能接受"。本版把样式模式从"填数字"改成真正的鼠标拖拽。

**实现要点**：
- `#editor` 上挂 mousedown（capture）→ 选中元素 + 准备拖拽；window 挂 mousemove/mouseup。元素非 absolute 时，第一次移动自动用 `offsetLeft/offsetTop` 转 absolute（保持原位不跳）。
- 坐标全部在**源设计稿像素空间**做（mouse delta / sc），再通过 `offOriginX = startOffsetLeft − startSrcBox.left` 转回 offsetParent 空间写 `element.style.left/top`。**铁律**：不要用 getComputedStyle 读画布显示像素（会被 transform:scale 污染）。
- **自动吸附（阈值 8 源像素）**：遍历被拖元素的 left/center/right × 所有目标的 left/center/right（包括 slide 自身 0/中心/100% + 其他可见元素的边/中），取距离最小者吸附。画一条贯穿画布的 1.5px 红线作为视觉反馈。
- **buildHtml 序列化前剥离** `__drag-guide` 元素和 `__picked/__dragging` class，确保临时标记不写回源文件。

**附带修一个 EP25 保存崩溃 bug**：`buildHtml` 的 `unitRe` 正则写死 `<section class="slide"[^>]*>`，要求 class 紧跟 `<section` 且值为 `"slide"`。但 EP25 P1 是 `<section class="slide active">`，class 含额外修饰类，正则匹配不到，导致 `matches.length` 比 `order.length` 少一页 → `matches[orig]` undefined → 保存崩溃。修：用 `<section\b[^>]*\bclass=["'][^"']*slide[^"']*["'][^>]*>` 兼容任意属性顺序和 class 值。

**回归**：EP25 h1.rise.d2 拖到画面中部，X 自动吸附到画面水平中线 640（sw/2），Y 吸附到附近元素 top 197；buildHtml 输出 18975 字节，零临时 class。

### v1.0.17（2026-07-31）样式模式（Properties 面板）——点选元素改位置/尺寸/transform

**动机**：用户问"如果我要拖动色块位置，目前怎么操作"——之前编辑器只能改文字，位置/尺寸只能改源 HTML。v1 加"样式模式"：点画布元素 → 右侧浮窗显示/编辑 top/left/width/height/transform/font-size/color/background，inline style 写回元素；保存时序列化（RAW.replace 每页 innerHTML）自动带回源文件。

**关键设计**：
- 顶栏「更多」加 `📐 样式模式` toggle；开启时自动 zoom 到当前页（精确点击必须 1:1）
- 画布元素 hover 显示橙色虚线轮廓，点选红实线；面板输入是**源设计稿像素**（FDE 1920×1080 坐标），画布自动按 `--sc` 缩放显示
- 关键铁律：**读/写 `element.style.*` 字符串，不用 getComputedStyle**——因为画布 `transform:scale(var(--sc))` 让 getComputedStyle 拿到的是「画布显示像素」，而 element.style.left 是「源设计稿像素」（写什么就是什么，不受 transform 影响）。混淆两者会导致改值偏离预期。
- 选中 static 元素：top/left 暂时空（不生效），但有一键"⊕ 设为 absolute"按钮（自动用当前 offsetTop/offsetLeft 填 top/left，再让用户调）
- Esc 两段式：1 次取消选中、2 次退出样式模式
- `save()` 加 try-catch 包 buildHtml（序列化失败有友好提示，不卡死）

**回归**：EP25 P1 h1.rise 改 left=300, top=200 → element inline style 正确写入 `position:absolute; top:200px; left:300px;` → 保存 → 源文件含 position:absolute ✓

### v1.0.16（2026-07-30）顶栏品牌字"帆哥的…编辑器"在深色底上看不见

**根因**：`#topbar h1` 没显式 color → 继承 body 的 `var(--ink,#0a0a0a)` 黑色，与 topbar `background:var(--ui-panel)=#1c1c22` 形成黑底黑字；只有 `.accent{color:var(--red)}` 的"PPT"可见。**修法**：h1 显式 `color:var(--ui-text)=#eef0f3`，1 行 CSS。

**通用教训**：顶栏/工具栏等所有直接放在深色 panel 里的文字元素，颜色必须显式声明 `color:var(--ui-text)`，不能依赖 body 继承——继承链上 body 用了 `var(--ink)`（深色文档用的），而 topbar 是深底亮字，继承反过来了。

### v1.0.15（2026-07-30）顶栏视口比例下拉（响应式稿关键）

**根因**：响应式源（`.slide{min-width:100vw;height:100vh}` + `h1{font-size:6.2vw}` + `.bg-deco::before{width:62vw;height:62vw}`，无任何固定 width）渲染时**完全依赖视口尺寸**——源 CSS 里所有元素的位置/字号/光晕大小都按视口的 vw/vh 计算。

- 用户在浏览器里以 **9:16 portrait**（约 624×1130）查看 EP25 源 → 62vw=387px 圆，标题 clamp(34, 38.7, 72)=38.7px
- 旧编辑器用硬编码 **1280×800 iframe** 探测 → sw/sh=1280×800，注入的 vw/vh 变量按 1280 算 → 62vw=794px 圆，标题 clamp(34, 79.4, 72)=72px
- 同一个源，**视口比例不同 → 渲染出的封面排版完全不同**（标题位置、光晕大小、内容垂直居中点都跟着变）

**修法**：顶栏 `#file-select` 旁加 `#viewport-select` 下拉（4 选 1）：

| 比例 | iframe W×H | 适用场景 |
|---|---|---|
| 16:10（默认） | 1280×800 | 桌面宽屏/默认 |
| 16:9 | 1280×720 | 标准 PPT 演示 |
| 9:16 | 720×1280 | **移动竖屏**（EP25 类自媒体封面） |
| 4:3 | 1280×960 | 传统投影/老 PPT |

- `measureSrc` 路径2 的 iframe 视口改用 `VIEWPORTS[viewportKey]`
- `buildEditor` 的 `--sc` 改为 `Math.min(960/w, 700/h)`（fit-both-dimensions）—— 避免 9:16（720×1280）按 960/w=1.33 把 frame 撑到 960×1707 撑爆编辑器
- change 事件触发 `buildEditor(loadedDoc)` 重新探测 sw/sh + 重渲
- 路径1（固定 width 源，如 FDE 1920×1080）走 CSS 字面量，与视口无关——实测 FDE 切 9:16 仍 1920×1080 ✓

**回归范围**（v1.0.15 修复后实测）：
- EP25 默认 16:10: sw=1280, sh=800, sc=0.7500, frame=960×600 ✓（与 v1.0.14 完全一致）
- EP25 切 9:16: sw=720, sh=1280, sc=0.5469, frame=394×700；视觉 1:1 还原用户源 PPT 截图 ✓
- EP25 切 16:9: sw=1280, sh=720, sc=0.7500, frame=960×540 ✓
- EP25 切 4:3: sw=1280, sh=960, sc=0.7292, frame=933×700 ✓
- EP25 反复切回 9:16: 稳定 720×1280，无 CSS 污染 / inline 残留 ✓
- FDE 瑞士现代 v2（固定 1920×1080）切 9:16: 仍 sw=1920, sh=1080, sc=0.5000 ✓
- 无页面报错；bg1=#FFF7F1 在所有视口下都生效（v1.0.14 修复未破）

### v1.0.14（2026-07-30）EP25 视口稿探测 + injectOrigCss 嵌套 style 不解析

**两个根因，全是「视口响应式设计稿」（`.slide{min-width:100vw;height:100vh}`，无固定 width，源比例 16:10=1280×800）加载后整页黑底 / 巨大光晕盖住文字的问题，不是源 HTML 的问题：**

1. **measureSrc 路径1 误测 1140×641（应为 1280×800）**
   - 旧正则 `\.slide[^}]*?width` 会误中 EP25 的 `.slide-inner{max-width:1140px}`，把 1140 当 slide 宽。
   - 修复：用「完整 `.slide{...}` 块」匹配 + 块内 `(?<!-)\bwidth` / `\bheight` 排除 `max-/min-` 前缀，只接受独立 `width:Npx`。扫不到再走路径2。
   - 路径2 加固：iframe 视口由 `1px` 改成 `1280×800`，让 `.slide{min-width:100vw}` 自然撑到 1280；同时**实测 `offsetWidth` 和 `offsetHeight`**，不再硬编码 `h=Math.round(w*9/16)`（EP25 是 16:10，强制 9/16 会推成 720 失真）。实测 EP25=1280×800。

2. **injectOrigCss 嵌套 `<style>` 不解析 → 整页黑底（最致命视觉 bug）**
   - 旧逻辑：`const s=document.createElement("style"); s.textContent=...; parts.push(s.outerHTML)`，再 `$("#orig-css").innerHTML=parts.join("\n")`。
   - **问题**：`s.outerHTML` 含 `<style>...</style>` 标签，塞进 `#orig-css.innerHTML` 时浏览器按 HTML 解析，内嵌 `<style>` 在 HTML5 规范里被当作 **rawText（不解析为样式）** → 源 `:root` 变量（`--bg1/--bg2`）全失效 → `.bg-deco` 的 `background:radial-gradient(...)` 解析为透明 → 整页黑底、`.bg-deco` 光晕圆消失/错位。
   - 修复：直接 `parts.push(fixViewportUnits(el.textContent || ""))` 收集裸 CSS 字符串，再 `$("#orig-css").textContent = parts.join("\n")` 整体注入。`<link rel=stylesheet>` 仍用 `outerHTML`（合法）。

**回归范围**（v1.0.14 修复后实测，4 场景全过）：
- EP25 视口稿（1280×800）：sw=1280, sh=800, sc=0.7500, rootBg1=#FFF7F1（浅米色渐变底生效）, 光晕圆比例正确、文字完整 ✓
- 切 v1.3 (1280×720) → 切瑞士现代 (1920×1080, sc=0.5, slideBg=白) → 回 EP25 (1280×800, rootBg1=#FFF7F1)：跨文件切换无 CSS 污染 / inline 残留 ✓
- v1.0.13 的 FDE 修复未被破坏（瑞士现代 sw=1920, sc=0.5 不变） ✓
- 截图核对：EP25 P1/P2/P3 与源设计稿视觉一致（浅米色 + 橙色光晕 + 黑字 + 卡片完整）

**为什么之前没暴露**：v1.0.13 只覆盖了「FDE 等固定 width 稿」的跨文件 CSS 污染与 slide-bg 残留；EP25 这类**无固定 width 的视口稿**会走路径1 误中 max-width，且整页黑底的根因是 injectOrigCss 的 outerHTML 嵌套陷阱——这是所有"源 CSS 走 innerHTML 注入 preview 容器"场景的通用坑。

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