#!/usr/bin/env node
/*
 * 单会话渲染（Node 版）：用本机已装的 Node-Playwright 启动一次 Chrome（系统安装版），
 * 把 deck 全部幻灯片截成 PNG。与 Python 版 render_slides_pw.py 保持相同 CLI / 输出契约：
 *   用法：node render_slides_pw.mjs --out DIR SRC [start] [end]   （默认 1..N，N=源文件 slide 数）
 *   逐页输出：P<num> -> <name> (<bytes>B
 *   结束输出：ALL DONE in Xs
 *
 * 为什么是 Node 版：本机 Python 环境未安装 playwright（且无 pip 网络），但 Node-Playwright +
 * 系统 Chrome 已就绪。编辑器所有「渲染依赖」功能（PPTX / PDF / PNG 包 / 长图导出）共用本渲染器。
 *
 * 依赖解析：优先用环境变量 PW_NODE_MODULES 指向的 playwright；否则回退到本机固定工作区 node_modules。
 */
import { createRequire } from 'module';
import { readFileSync, writeFileSync, unlinkSync, mkdirSync } from 'fs';
import { tmpdir } from 'os';
import { join, dirname, basename } from 'path';
import { pathToFileURL } from 'url';

const require = createRequire(import.meta.url);
const PW_CANDIDATES = [
  process.env.PW_NODE_MODULES,
  '/Users/fanshuai/.workbuddy/binaries/node/workspace/node_modules/playwright',
].filter(Boolean);
let chromium = null;
for (const c of PW_CANDIDATES) {
  try { ({ chromium } = require(c)); break; } catch (e) { /* try next */ }
}
if (!chromium) {
  console.error('FATAL: 找不到 Node-Playwright，请确认 PW_NODE_MODULES 或固定工作区 node_modules 存在');
  process.exit(2);
}

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const CHROME_PATH = (() => { try { require('fs').accessSync(CHROME); return CHROME; } catch { return undefined; } })();

function countSlides(src) {
  const html = readFileSync(src, 'utf-8');
  return (html.match(/class="slide"/g) || []).length;
}

function parseArgs(argv) {
  let outDir = null;
  const cleaned = [];
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--out' && i + 1 < argv.length) { outDir = argv[i + 1]; i++; continue; }
    cleaned.push(argv[i]);
  }
  const src = cleaned.find(a => a.endsWith('.html') || a.includes('/') || require('fs').existsSync(a));
  const rest = cleaned.filter(a => a !== src).map(Number);
  return { outDir, src, start: rest[0] || 1, end: rest[1] || null };
}

async function main() {
  const { outDir, src, start, end } = parseArgs(process.argv.slice(2));
  if (!src) { console.error('FATAL: 缺少 SRC'); process.exit(2); }
  const WORK = outDir || dirname(src);
  mkdirSync(WORK, { recursive: true });

  let n = end;
  if (!n) n = countSlides(src);
  const s0 = start, e0 = n;

  // 去掉 Google Fonts 的 <link>（联网被禁用时会阻塞内联 deck 脚本初始化）。
  let html = readFileSync(src, 'utf-8');
  html = html.replace(/<link[^>]*fonts\.(googleapis|gstatic)\.com[^>]*>/g, '');
  const tmpsrc = join(WORK, `fde-deck-${Date.now()}.html`);
  writeFileSync(tmpsrc, html, 'utf-8');

  const args = [
    '--no-sandbox', '--no-first-run', '--no-default-browser-check',
    '--disable-dev-shm-usage', '--disable-gpu', '--disable-software-rasterizer',
    '--disable-component-update', '--disable-background-networking',
    '--disable-backgrounding-occluded-windows', '--disable-sync',
    '--disable-default-apps', '--no-pings',
    '--disable-features=Translate,BackForwardCache,OptimizationHints,MediaRouter,InfiniteSessionRestore',
  ];
  const t0 = Date.now();
  const browser = await chromium.launch({ executablePath: CHROME_PATH, headless: true, args });
  try {
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
    await page.goto(pathToFileURL(tmpsrc).href, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction("typeof deck !== 'undefined'", { timeout: 15000 });
    for (let i = s0 - 1; i < e0; i++) {
      const pnum = i + 1;
      const pad = pnum < 10 ? '0' : '';
      await page.evaluate(`deck.showSlide(${i})`);
      await page.waitForTimeout(800); // deck 的 reveal 过渡延迟最高 .6s + 字体回退
      const out = join(WORK, `preview-P${pad}${pnum}.png`);
      const buf = await page.screenshot({ clip: { x: 0, y: 0, width: 1920, height: 1080 } });
      writeFileSync(out, buf);
      console.log(`P${pad}${pnum} -> ${basename(out)} (${buf.length}B)`);
    }
  } finally {
    await browser.close();
    try { unlinkSync(tmpsrc); } catch {}
  }
  console.log(`ALL DONE in ${(Date.now() - t0) / 1000}s`);
}

main().catch(e => { console.error('RENDER ERROR:', e); process.exit(1); });
