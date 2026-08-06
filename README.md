# 本地修改HTML格式的PPT，html一键导出PPT

> 一个本地优先的 HTML 幻灯片编辑器：在浏览器里直接改文字、拖拽排序、历史快照回滚，一键渲染并导出 PPTX。
> 配套 WorkBuddy skill：`fange-html-deck-editor`。

## 功能

- 🖊️ 浏览器内可视化编辑每个 `<section class="slide">` 的文字（所见即所得，1:1 原尺寸）
- 🔀 拖拽排序 / 上移下移 调整幻灯片顺序
- 📂 切换工作目录内多个 HTML 片子；支持「打开文件」按钮与**拖拽 `.html` 导入**
- 🕒 每次保存自动留历史快照，可一键回滚
- 🖼️ 单会话稳定渲染全部幻灯片为 PNG（Playwright，不卡死）
- 📦 一键导出 `.pptx`（16:9），**两种模式可选**：
  - **可编辑版（默认）· 三层结构**：① 干净背景图（去除文字与色块，仅留图片/网格/页脚）；② 色块独立 PPTX 矩形（可单独改色/改边/删除）；③ 文字独立文本框（无填充，改字即生效）
  - **高清整页图**：整页 2× 高分辨率截图铺满一页，纯演示 / 打印用，不可改字
- ☁️ 一键上传到飞书云空间：「更多 ▾」里可把当前 HTML 或已导出的 PPTX 直接经 `lark-cli drive +upload` 传到飞书云空间（链接自动复制并打开）。**上传前先做授权校验**：若本机 `lark-cli` 已授权且绑定飞书账号（user 身份 `tokenStatus=valid` 且具备 `drive:file:upload` 权限）则直接上传；否则前端弹出引导框，提示执行 `lark-cli auth login` 完成授权后再重试，不会误传或报错
- 🔒 默认纯本地 `127.0.0.1` 服务，数据零外发；仅「上传飞书云空间」会与飞书交互

## 快速开始

```bash
# macOS：双击启动器（自动打开浏览器到 http://localhost:8731/）
双击 帆哥PPT编辑器一键启动.command

# 之后在编辑器里点「打开 PPT…」选任意位置的 deck HTML，原地改字、保存写回原文件
```

浏览器打开 http://localhost:8731 即可。

## 依赖

- Python 3.10+
- `pip install playwright` 且 `playwright install chromium`
  - macOS 也可直接用系统 Chrome：默认走 `/Applications/Google Chrome.app`

## 目录结构

- `帆哥PPT编辑器一键启动.command` — macOS 一键启动器（双击即启动，基于 `__file__` 自动定位，无需 `--root`）
- `帆哥PPT编辑器-打开Web界面.webloc` — 浏览器快捷方式（双击直接打开 http://localhost:8731/）
- `scripts/editor_server.py` — 本地 HTTP 服务（open / save / render / export / 历史快照）
- `scripts/render_slides_pw.py` — Playwright 单会话渲染器
- `scripts/export_editable_pptx.py` — 三层可编辑 PPTX 导出
- `templates/editor.html` — 编辑器前端（单文件）
- `references/architecture.md` — 架构与设计说明
- `SKILL.md` — WorkBuddy skill 元数据

> ⚠️ 历史快照 / 渲染产物 / 日志**全部**存编辑器自家目录（`.history/`、`.render/`、`editor.log`），绝不写入你打开的 deck 所在项目文件夹。

## 配套 skill 生态

本编辑器是「HTML 做片 → 可编辑交付」链路的一环，与另外两个 skill 配合使用：

| skill | 角色 | 说明 |
|---|---|---|
| `guizang-ppt-skill`（归藏PPT） | 生成 HTML deck | 单文件 HTML 横向翻页 PPT 生成器；FDE 瑞士现代红片子即其瑞士风骨架 `red accent` 定制版。本编辑器直接打开它产出的 `.html` |
| `feishu-html-slides`（飞书 HTML 幻灯片） | 生成 + 飞书交付编排 | 工作流：用 `guizang-ppt-skill` / `frontend-slides` 生成 HTML → 上传飞书云空间 / 部署飞书妙搭。本编辑器的「上传飞书云空间」按钮正是把这条飞书交付路径真正落地 |
| `fange-html-deck-editor`（本工具） | 改字精修 + PPTX 导出 | 打开生成的 `.html`，浏览器改字、拖拽排序、历史回滚，导出三层可编辑 PPTX |

完整流水：`大纲/素材 → guizang-ppt-skill（生成）→ fange-html-deck-editor（改字精修）→ 导出三层可编辑 PPTX（交付）`；若走飞书交付，则最后一步改为「上传飞书云空间 / 部署妙搭」。

## 相关文档

- 📄 完整使用说明（飞书文档）：https://hpdwyj4rh0.feishu.cn/docx/D2Z4d5lFeoiEMrxOk8yc3EzFnPe
