# 生成引擎桥接契约（MVP · v1）

> 目的：把 PRD 里的「桥接点」固化成可验证的契约——**生成产物 === 编辑器输入**，无需任何格式转换。
> 本文件对应 P1「生成引擎产品化（Step1 落地）」的最小可用原型（离线、模板化）。

## 1. 契约（生成产物必须满足）

生成的 HTML deck 必须同时满足：

1. **单文件自包含**：一个 `.html`，所有 CSS 内联在 `<style>`，所有脚本内联在 `<script>`；**禁止任何外部字体/CDN**（系统字体栈，符合字体铁律）。
2. **每张幻灯片是 `<section class="slide">`**：`class` 属性字面量必须恰为 `class="slide"`（渲染器/编辑器/计数逻辑都用字面量 `class="slide"` 匹配）。变体样式用 `data-kind="title|section|content"` 等属性，不要往 `class` 里加修饰类（否则计数漏页）。
3. **全局 `deck` 运行时**（编辑器渲染器靠它逐页截图）：
   - `deck.showSlide(i)`：显示第 i 页、隐藏其余（用 `.active` 类切换即可）。
   - 可选 `deck.next()` / `deck.prev()`。
   - 页面初始 `deck.showSlide(0)`。
   - 渲染器会等 `typeof deck !== 'undefined'` 再逐页 `showSlide` + 截图（每张等 800ms 过渡）。
4. **每页固定 1920×1080**：`section.slide{position:absolute;inset:0;width:1920px;height:1080px;display:none}` + `.slide.active{display:block}`。渲染器按视口 1920×1080 截图。
5. **无 Google Fonts `<link>`**：即便有也会被渲染器正则剥离（联网禁用会阻塞内联 deck 脚本初始化）。

满足以上 5 条，生成产物即可被编辑器「打开 PPT…」直接打开、可视化精修、再导出 PDF/PNG包/长图（PPTX 导出暂被 `python-pptx` 缺失阻断，见 playbook §13）。

## 2. 离线原型（已落地）

`scripts/gen_deck.py`：主题/大纲 → 编辑器规范 deck。

```bash
# 命令行
python scripts/gen_deck.py --title "标题" --subtitle "副标题" --out deck.html \
  --section "章节分隔" \
  --slide "内容页标题|要点1;要点2;要点3"

# 或从 markdown 大纲（# 标题 / ## 章节 / - 要点；首段作封面副标题）
python scripts/gen_deck.py --out deck.html --md outline.md
```

- 零依赖、零网络、系统字体；自带极简 `deck` 运行时，契约与 §1 一致。
- 已验证：生成 → Node 渲染器逐页截图 → 6 页 PNG 全部成功（见 `render_slides_pw.mjs` 冒烟）。

## 3. 产品化路线（后续，非本 MVP）

- **云端 LLM 生成（Freemium 收费基座）**：把 §2 的模板生成替换为「主题/文档/图片 → LLM → 同契约 deck」；输出仍是 §1 规范的 HTML，无缝进 Step2 编辑器。这是 PRD 里「AI 生成」收费点。
- **生成页 UI**：编辑器内「AI 生成」入口 → 调云端 → 返回 deck → 一键载入编辑。
- **质量护栏**：LLM 输出必须经 §1 契约校验（slide 数、deck 全局、1920×1080、无 CDN）后再回传，避免脏 deck 进编辑器。
- **成本/合规**：LLM token 成本核算（见 PRD §7.3）、生成内容合规审核（中国 ICP / 欧美 GDPR）。
