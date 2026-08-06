#!/usr/bin/env python3
"""
帆哥 AI PPT Studio · Step1 本地原型（离线桥接生成器）

把「主题 / 大纲」变成一份**编辑器规范**的 HTML deck（<section class="slide">），
可直接用编辑器「打开 PPT…」打开、可视化精修、再导出。

这就是 PRD 里的「桥接点」：生成产物 === 编辑器输入，无需任何格式转换。
- 纯本地、零依赖、零外部字体/CDN（系统字体栈，符合字体铁律）。
- 自带极简 SlidePresentation 运行时：全局 `deck` 暴露 `showSlide(i)`/`next`/`prev`，
  编辑器渲染器（render_slides_pw.mjs）靠 `deck.showSlide` 逐页截图，契约一致。
- 云端 LLM 生成（Freemium 收费基座）是后续产品化步骤；本脚本是「主题/大纲 → deck」
  的可离线 MVP，用来固化桥接契约 + 验证 Step1→Step2 闭环。

用法：
  python gen_deck.py --title "标题" --subtitle "副标题" --out deck.html \
      --slide "封面要点|要点A;要点B" \
      --slide "章节一|内容1;内容2" \
      --section "章节分隔标题"
  或从 markdown 大纲读入：
  python gen_deck.py --out deck.html --md outline.md
  （md 约定：# 标题 / ## 章节分隔 / - 要点；首段作封面）
"""
import argparse, sys, html, re, os


def esc(s):
    return html.escape(str(s), quote=True)


def slide_title(title, subtitle=""):
    sub = f'<p class="sub">{esc(subtitle)}</p>' if subtitle else ""
    return f'<section class="slide" data-kind="title"><div class="wrap"><h1>{esc(title)}</h1>{sub}</div></section>'


def slide_section(heading):
    return f'<section class="slide" data-kind="section"><div class="wrap"><h2>{esc(heading)}</h2></div></section>'


def slide_content(heading, bullets):
    lis = "".join(f"<li>{esc(b)}</li>" for b in bullets)
    return (f'<section class="slide" data-kind="content"><div class="wrap">'
            f'<h2>{esc(heading)}</h2><ul class="bullets">{lis}</ul></div></section>')


def parse_md(text):
    """极简大纲：# 标题 / ## 章节 / - 要点。返回 (title, subtitle, slides)。"""
    lines = text.splitlines()
    title, subtitle = "未命名演示", ""
    slides = []
    cur_h, cur_b = None, []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("# "):
            title = s[2:].strip()
            continue
        if s.startswith("## "):
            if cur_h is not None:
                slides.append(("content", cur_h, cur_b))
            cur_h, cur_b = s[3:].strip(), []
            continue
        if s.startswith("- "):
            if cur_h is None:
                cur_h = title
            cur_b.append(s[2:].strip())
            continue
        # 普通行：当作副标题（仅当还没设过）或归入当前要点
        if not subtitle and cur_h is None:
            subtitle = s
        elif cur_h is not None:
            cur_b.append(s)
    if cur_h is not None:
        slides.append(("content", cur_h, cur_b))
    return title, subtitle, slides


def build_deck(title, subtitle, slides):
    """slides: list of (kind, ...)。kind: 'title'|'section'|'content'。"""
    body = []
    # 第一页固定封面
    body.append(slide_title(title, subtitle))
    for it in slides:
        if it[0] == "section":
            body.append(slide_section(it[1]))
        elif it[0] == "content":
            body.append(slide_content(it[1], it[2]))
        elif it[0] == "title":
            body.append(slide_title(it[1], it[2] if len(it) > 2 else ""))
    sections = "\n".join(body)
    return TEMPLATE.replace("{{TITLE}}", esc(title)).replace("{{SECTIONS}}", sections)


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=1920,height=1080">
<title>{{TITLE}}</title>
<style>
  :root{
    --ink:#1a1a1a; --muted:#6b7280; --bg:#ffffff; --accent:#ff5a1f;
    --panel:#f5f6f8; --line:#e5e7eb;
  }
  *{box-sizing:border-box;margin:0;padding:0;}
  html,body{width:1920px;height:1080px;background:#222;overflow:hidden;
    font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Helvetica Neue",Arial,sans-serif;}
  section.slide{position:absolute;inset:0;width:1920px;height:1080px;display:none;
    background:var(--bg);color:var(--ink);padding:120px 140px;}
  section.slide.active{display:block;}
  .wrap{max-width:1640px;height:100%;display:flex;flex-direction:column;justify-content:center;}
  h1{font-size:96px;line-height:1.15;letter-spacing:-1px;font-weight:800;}
  h2{font-size:64px;line-height:1.2;font-weight:800;margin-bottom:48px;}
  .sub{margin-top:28px;font-size:36px;color:var(--muted);font-weight:400;}
  .bullets{list-style:none;}
  .bullets li{font-size:44px;line-height:1.7;padding:18px 0 18px 56px;position:relative;
    border-bottom:1px solid var(--line);}
  .bullets li::before{content:"";position:absolute;left:0;top:34px;width:22px;height:22px;
    border-radius:6px;background:var(--accent);}
  .title-slide{background:linear-gradient(135deg,#fff 60%,#fff3ec 100%);}
  section.slide[data-kind="title"] h1{color:var(--ink);}
  section.slide[data-kind="title"] h1::after{content:"";display:block;width:160px;height:14px;background:var(--accent);margin-top:36px;border-radius:8px;}
  section.slide[data-kind="section"]{background:var(--ink);color:#fff;}
  section.slide[data-kind="section"] h2{color:#fff;}
  section.slide[data-kind="section"] h2::before{content:"";display:block;width:120px;height:12px;background:var(--accent);margin-bottom:32px;border-radius:6px;}
  .reveal{animation:fade .55s ease both;}
  @keyframes fade{from{opacity:0;transform:translateY(24px);}to{opacity:1;transform:none;}}
</style>
</head>
<body>
{{SECTIONS}}
<script>
  var SLIDES = Array.prototype.slice.call(document.querySelectorAll('section.slide'));
  var deck = {
    current: 0,
    showSlide: function(i){
      if(i<0||i>=SLIDES.length) return;
      SLIDES.forEach(function(s,idx){ s.classList.toggle('active', idx===i); });
      this.current = i;
      var el = SLIDES[i];
      if(el){ el.classList.remove('reveal'); void el.offsetWidth; el.classList.add('reveal'); }
    },
    next: function(){ this.showSlide(Math.min(this.current+1, SLIDES.length-1)); },
    prev: function(){ this.showSlide(Math.max(this.current-1, 0)); }
  };
  if(document.readyState!=='loading'){ deck.showSlide(0); }
  else { window.addEventListener('DOMContentLoaded', function(){ deck.showSlide(0); }); }
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description="主题/大纲 → 编辑器规范 HTML deck（离线桥接生成器）")
    ap.add_argument("--title", default="未命名演示")
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--out", default="deck.html")
    ap.add_argument("--slide", action="append", default=[],
                    help="内容页：'标题|要点1;要点2'（可重复）")
    ap.add_argument("--section", action="append", default=[],
                    help="章节分隔页标题（可重复）")
    ap.add_argument("--md", default="", help="从 markdown 大纲读入（覆盖 --title/--slide/--section）")
    args = ap.parse_args()

    slides = []
    if args.md and os.path.isfile(args.md):
        with open(args.md, "r", encoding="utf-8") as f:
            t, sub, parsed = parse_md(f.read())
        title, subtitle = t, sub
        for kind, *rest in parsed:
            slides.append((kind, *rest))
    else:
        title, subtitle = args.title, args.subtitle
        for sec in args.section:
            slides.append(("section", sec))
        for sl in args.slide:
            if "|" in sl:
                h, b = sl.split("|", 1)
                bullets = [x for x in b.split(";") if x.strip()]
            else:
                h, bullets = sl, []
            slides.append(("content", h, bullets))

    out = build_deck(title, subtitle, slides)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"OK -> {args.out}  ({len(slides)+1} 页)")


if __name__ == "__main__":
    main()
