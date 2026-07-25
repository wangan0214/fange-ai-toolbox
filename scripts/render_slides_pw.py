#!/usr/bin/env python3
"""单会话渲染：用 Playwright 启动一次 Chrome（系统安装版），把 deck 全部幻灯片截成 PNG。

相比 render_preview.py（每页启停一次 Chrome，macOS 上反复启动极易被 updater / 进程残留卡死），
本脚本只启动一次浏览器，逐页 deck.showSlide(i) + screenshot，稳定且更快。

用法：python render_slides_pw.py [start] [end]   （默认 1..N，N=源文件 slide 数）
依赖：playwright（指向系统 Chrome，无需下载 chromium）。
"""
import sys, pathlib, subprocess, time, os

DIR = pathlib.Path("/Users/fanshuai/Documents/搞钱集中营/12-FDE研究")
SRC_DEFAULT = DIR / "FDE认知片子-瑞士现代-v2.html"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

def count_slides(src):
    return open(src, "r", encoding="utf-8").read().count('class="slide"')

def main():
    # 用法：render_slides_pw.py [SRC] [start] [end]
    #   SRC 省略则用默认文件；服务端调用时总传入当前编辑文件的绝对路径
    args = sys.argv[1:]
    src = SRC_DEFAULT
    if args and (args[0].endswith(".html") or "/" in args[0] or os.path.exists(args[0])):
        src = pathlib.Path(args[0])
        args = args[1:]
    SRC = src
    n = count_slides(SRC)
    start = int(args[0]) if len(args) >= 1 else 1
    end = int(args[1]) if len(args) >= 2 else n
    from playwright.sync_api import sync_playwright

    # deck 是自包含的（SlidePresentation 内联，无 CDN JS）。唯一外部资源是 Google Fonts 的
    # <link>：联网被禁用时，这个未加载的 stylesheet 会阻塞其后的内联 deck 脚本 → deck 不初始化。
    # 解决办法：渲染用临时副本，去掉 fonts 的 <link>（deck 已有 fallback 字体，CJK 走系统 PingFang），
    # 同时彻底关掉网络 → 无 updater、无网络依赖、完全确定性，杜绝 macOS 上反复启动 Chrome 的随机卡死。
    import tempfile, re
    html = open(SRC, "r", encoding="utf-8").read()
    html = re.sub(r'<link[^>]*fonts\.(googleapis|gstatic)\.com[^>]*>', "", html)
    tmpf = tempfile.NamedTemporaryFile(prefix="fde-deck-", suffix=".html", dir=str(DIR), delete=False)
    TMPSRC = pathlib.Path(tmpf.name)
    tmpf.close()
    TMPSRC.write_text(html, encoding="utf-8")

    args = [
        "--no-sandbox", "--no-first-run", "--no-default-browser-check",
        "--disable-dev-shm-usage", "--disable-gpu", "--disable-software-rasterizer",
        "--disable-component-update", "--disable-background-networking",
        "--disable-backgrounding-occluded-windows", "--disable-sync",
        "--disable-default-apps", "--no-pings",
        "--disable-features=Translate,BackForwardCache,OptimizationHints,MediaRouter,InfiniteSessionRestore",
    ]
    t0 = time.time()
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True, args=args)
        page = browser.new_page(viewport={"width": 1920, "height": 1080},
                                device_scale_factor=1)
        page.goto(f"file://{TMPSRC}", wait_until="domcontentloaded")
        page.wait_for_function("typeof deck !== 'undefined'", timeout=15000)
        for i in range(start - 1, end):
            page.evaluate(f"deck.showSlide({i})")
            page.wait_for_timeout(800)  # deck 的 reveal 过渡延迟最高 .6s，等 800ms 让所有元素稳定 + 字体回退到位
            out = DIR / f"preview-P{i+1:02d}.png"
            page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": 1920, "height": 1080})
            print(f"P{i+1:02d} -> {out.name} ({out.stat().st_size}B)")
        browser.close()
    try:
        TMPSRC.unlink()
    except Exception:
        pass
    print(f"ALL DONE in {time.time()-t0:.1f}s")

if __name__ == "__main__":
    main()
