# fange-html-deck-editor · 开发铁律与架构手册（Hands-off）

> **用途**：编辑 `templates/editor.html` / `scripts/editor_server.py` / 导出脚本 **之前**，先读这份。
> 规则来自 v1.0.10–v1.0.23 踩坑沉淀，规则优先、非编年。改完务必跑 §12 Playwright 冒烟测试。
> 这份文档是「hands-off」参考：未来任何会话加载本 skill 后，按此手册即可直接动手，无需重新推导。

---

## 0. 三个 canonical 副本（编辑前先确认你在改哪个）

| 副本 | 路径 | 用途 |
|---|---|---|
| 工作区 | `/Users/fanshuai/Documents/搞钱集中营/17-帆哥PPT编辑器/` | 日常运行 / 浏览器编辑 |
| OB 镜像 | `/Users/fanshuai/【工作盘】/7、王帆的知识库/0.【搞钱行动】/17-帆哥PPT编辑器/` | git 仓库，remote=`wangan0214/fange-ai-toolbox` |
| Skill | `~/.workbuddy/skills/fange-html-deck-editor/` | 被 WorkBuddy 加载的技能包 |

- **三者结构完全一致**（README / SKILL.md / references / scripts / templates）。改完 `templates/editor.html` 必须 `cp` 到另外两个位置的 `templates/`。
- OB 提交纪律：改完 `git add -A && git commit`（本地安全）；`git push` 常被代理 502 挡，本地 commit 即可，网络恢复再 push（见 §14）。

---

## 1. 坐标系铁律（最常踩，错一次就改值偏离）

- 画布 `.slide` 有 `transform:scale(var(--sc))`，`--sc = Math.min(960/w, 700/h)`（fit-both-dimensions，防竖屏撑爆）。
- **鼠标位移 → 源像素**：`delta_src = mouseDelta_display / sc`。写回 `element.style.left/top/width/height`（这是源像素，不受 transform 影响）。
- **绝不**用 `getComputedStyle` 读画布显示像素当源像素——被 transform 污染，混淆即改值偏离。
- 元素非 absolute 时，第一次移动用 `offsetLeft/offsetTop` 转 absolute（保持原位不跳）；写回前 `offOriginX = startOffsetLeft − startSrcBox.left` 转回 offsetParent 空间。

---

## 2. CSS 注入铁律（整页黑底根因）

- 收集源 CSS 必须用 `el.textContent` 拿**裸 CSS 字符串**，再 `$("#orig-css").textContent = parts.join("\n")` 整体注入。
- **绝不用** `s.outerHTML` 塞进 `#orig-css.innerHTML`：HTML5 把内嵌 `<style>` 当 rawText 不解析 → `:root` 变量失效 → 整页黑底。`<link rel=stylesheet>` 仍可用 outerHTML（合法）。

---

## 3. 正则匹配 `<section class="slide">` 铁律

- 禁止写死紧跟 literal `<section class="slide"`。用
  `<section\b[^>]*\bclass=["'][^"']*slide[^"']*["'][^>]*>`
  兼容任意属性顺序、class 含子串（如 `<section class="slide active">`）、额外修饰类。否则漏匹配 → `matches.length` 少页 → 保存越界崩溃。

---

## 4. 跨文件 / 重载必须重置（防 CSS 污染 / inline 残留）

每次 `buildEditor` / 加载文件开头必须：
1. **清源 CSS 变量与 inline style**：`editor.style.removeProperty('--slide-bg')` 等；`measureSrc` 优先扫 doc 自备 `<style>` 找固定 width，扫不到才进**独立 iframe** 测（隔离主 document 上次残留 CSS）。
2. **重建** buildHtml 的 `order` / `editedSlides`（不要复用旧数组）。
3. **清空撤销栈** `slideHistory=[]; histIdx=-1; pushHistory()`（每次加载文件重置，避免跨文件混合）。

---

## 5. 撤销栈（v1.0.19）

- 快照 `{order, 各页 innerHTML}`，覆盖**文字 / 拖拽 / 属性 / 重置 inline / 设为 absolute / 页面顺序重排**全部改动类型。
- 文字输入 500ms 防抖合并成一步；其余改动动作结束立即压栈；与栈顶无实质变化不压栈（避免拖拽未动噪声）。
- 顺序重排经 `applyOrder(newOrder)` 把 `order/sideItems/wrapEls/editedSlides` 四数组按快照 order 重排并 `reflow()`，完整撤销页面顺序调整。

---

## 6. open-in-place 架构（v1.0.22，不污染用户项目）

- 编辑器本体独立放在 `17-帆哥PPT编辑器/`；点「打开 PPT…」(`/api/pick`→`/api/open`) 后后端 `ALLOWED_ROOT` **动态切到该 deck 所在目录**。
- 保存 / 渲染 / 回滚全部作用于 `ACTIVE_FILE`（原文件绝对路径），**写回原路径、不复制不移动**。
- 历史 `EDITOR_HOME/.history/<sha1(abs)[:12]>/`、渲染 `EDITOR_HOME/.render/<deckKey>/`、日志 `EDITOR_HOME/editor.log`——**绝不**在用户项目目录写 `.history` 或副本（用 `sha1(abs_path)[:12]` 做命名空间，不同目录同名 `index.html` 互不串台）。
- 拖拽 /「导入副本」因浏览器拿不到绝对路径，保存只下载编辑版副本（不回写）；**只有「打开 PPT…」才是真原地写回**。

---

## 7. 路由陷阱

- `/api/history-file` 必须排在 `/api/history` 之前（后者 `startswith('/api/history')` 会遮蔽前者）。任何 `/api/X` 与 `/api/X-xxx` 都把**更具体的放前面**。

---

## 8. UI 字色铁律

- 顶栏 / 工具栏等深色 panel 内的文字，颜色必须显式 `color:var(--ui-text)`，**不能**继承 body 的 `var(--ink)`（黑底黑字）。通用教训：深底亮字处禁用 body 继承链。

---

## 9. resize handle 设计（P0，v1.0.23）

- 8 向手柄 `.rh`(n/s/e/w/ne/nw/se/sw) + `.sel-box` 挂在 `.slide-frame`（**显示像素空间，不随 `.slide` transform 二次缩放**）。
- 写回：`startResize` 记录 `srcBox = pickedEl.getBoundingClientRect()`（element.style 是源像素，故读它即源像素）+ `sc`；`onResizeMove` 中 `dx/dy = mouseΔ / sc`，按 `dir` 改 `w/h/left/top`，**MIN=8 源像素**；同步面板数字；`onResizeUp` 后 `styleDirty + pushHistory`。
- 选中 `pickEl` 渲染手柄；取消选中 / `exitStyleMode` 调 `clearResizeLayer()` 清掉。拖拽时 `onDragMove` 末尾 `positionResizeLayer()` 同步手柄位置。

---

## 10. 代码视图兜底（P0，v1.0.23）

- `#code-modal` 编辑**整体 deck 源**：`openCodeView` 用 `buildHtml()` 导出当前态填入 `#code-area`；`#code-apply` 用 `DOMParser.parseFromString(html,'text/html')` + `buildEditor(parsedDoc)` 整体重解析重渲染。逃生舱，避免 GUI 改不动时卡死。
- 点遮罩 / 「取消」关闭；「应用」后 `dirty=true + pushHistory`。

---

## 11. 视口响应式源（vw/vh，无固定 width）

- 必须让用户选视口比例（顶栏 `#viewport-select` 16:10/16:9/9:16/4:3）。自动检测无法稳定判断源设计意图（同一源不同视口排版完全不同）。
- `--sc` 用 fit-both-dimensions（`Math.min(960/w,700/h)`）防竖屏 9:16 撑爆。

---

## 12. 如何用 Playwright 真机冒烟测试（防改崩 · 必做）

改完 `editor.html` **必须**跑一次 headless 冒烟，确认 **0 JS errors** + 关键能力可用。

- **环境分层**：① 预览 / PDF / PNG 包 / 长图渲染走 **Node 版 playwright**（`/Users/fanshuai/.workbuddy/binaries/node/workspace/node_modules/playwright`）+ 系统 Chrome；② **PPTX 导出（可编辑三层 + 图片模式）依赖 `python-pptx` + python-playwright，已装进专用 venv** `/Users/fanshuai/.workbuddy/binaries/python/envs/fange-editor`（基于托管 python 3.13.12，含 PIL + python-pptx 1.0.2 + playwright 1.62.0，用系统 Chrome 无需下载浏览器）。一键启动脚本优先选该 venv，故 PPTX 已本地离线可用。pip 网络实际可用（PyPI 443 可达；之前"无网络"是代理瞬时抽风的误判）。
- **服务端渲染管线已切到 Node**：`scripts/render_slides_pw.mjs`（替代原 `render_slides_pw.py`）。`editor_server.py` 的 `render_all_pw` 现在 `subprocess` 调 `node render_slides_pw.mjs --out DIR SRC 1 N`，并通过环境变量 `PW_NODE_MODULES` 把 playwright 包路径传给 node（node 用 `createRequire(绝对路径)` 解析，因为 NODE_PATH 对 ESM 不生效）。CLI / 输出契约（`P<num> -> name (bytes)B`、`ALL DONE`）与旧 Python 版完全一致，后端渲染相关功能（PPTX / PDF / PNG 包 / 长图导出）共用它。
- `require` 用**绝对路径**（NODE_PATH 对 node 不生效）：`const { chromium } = require('/Users/.../node_modules/playwright')`。
- 语法预检：`node --check`（提取 `<script>` 块）确保无语法错再跑。
- 测试 deck：最小 2 页含 `.box` 绝对定位元素（`/tmp/t2/index.html`）。
- 脚本断言链：打开 deck → 进样式模式 → `pickEl(.box)` → 断言 8 手柄存在 → 模拟 e 手柄右移 80px → 断言宽度 `200 → 200+80/0.75`（÷sc 正确）→ 打开代码视图断言含 `<section class="slide">` → 点保存断言文件 mtime/字节变化 → 收集 `console` / `pageerror` **必须为空**。
- 实测基线（v1.0.23）：`styleModeOn=true, picked=true, handles.count=8, e手柄右移80px→width 200→306.667px, code modal 打开含 slide 源, save 写回原文件, errors=[]`。

---

## 13. 能力基线（已完成 / 待做）

**✅ 已完成**
- 拖拽移动 + 自动对齐吸附（v1.0.18）
- 拖拽缩放 handle 8 向（v1.0.23）
- 代码视图兜底（v1.0.23）
- 撤销 / 重做栈（v1.0.19）
- 视口比例选择（v1.0.15）
- 历史快照回滚 / 三层可编辑 PPT 导出 / 飞书云空间上传
- 单会话 Playwright 渲染（无头 Chrome 起一次逐页截图，已切 Node 版）
- **PDF / PNG 包 / 长截图导出（纯 PIL 本地合并，无需新依赖）（v1.0.24）**
- **AI 生成入口（Step1 上云，v1.0.26）**：顶栏「✨ AI 生成」→ 主题/文档 → 同契约 deck → 复用打开流程进 Step2 精修。`scripts/gen_llm.py` 云端 LLM（OpenAI 兼容，env 配置 key/base/model，urllib 零依赖）+ 离线兜底（无 key 自动走 `gen_deck`）。`POST /api/gen-ai`：`generated/<ts>.html`；**Freemium 门控只在云端 LLM 路径生效**（`GEN_FREE_LIMIT` 默认 3，超额 `need_upgrade` + `upgrade_url`），**离线兜底无限**（本地编辑永久免费）。

**⏳ P1 待做**
- AI 协作闭环（批注 / 生成 prompt）
- SVG / Canvas 编辑
- 多模态生成输入（图片 / URL）

**✅ PPTX 导出已解锁（v1.0.25）**：可编辑三层（干净背景 + 可改色块 + 366 个可改字文本框/25 页）+ 图片模式，均本地离线可用（venv `fange-editor`）。若 venv 缺失，启动器回退托管 python，PPTX 按钮会提示需安装 `python-pptx`（联网一次性 `pip install python-pptx playwright` 即可恢复，无需走云端）。

---

## 14. 提交 / 同步纪律

- 改完 `cp` 到三个副本的 `templates/editor.html`；OB `git add -A && git commit`（本地安全）。
- push：`git push --set-upstream origin main`（首次需设 upstream）。代理 502 时本地 commit 即可，网络恢复再 push。
- macOS 无 `timeout` 命令，用 git 级超时重试：
  `GIT_HTTP_CONNECT_TIMEOUT=20 GIT_HTTP_LOW_SPEED_LIMIT=1 GIT_HTTP_LOW_SPEED_TIME=20 git push`
