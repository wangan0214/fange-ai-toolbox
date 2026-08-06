#!/usr/bin/env python3
"""
帆哥 AI PPT Studio · Step1 云端生成引擎桥接（LLM → 编辑器规范 deck）

把「主题 / 文档」交给 LLM（OpenAI 兼容接口）生成结构化大纲 JSON，
再委托 gen_deck.build_deck 渲染为 <section class="slide"> deck。
- 云端：设置 LLM_API_KEY 即走 LLM（默认 OpenAI 兼容，可配 LLM_BASE_URL / LLM_MODEL）。
- 本地兜底：无 key 或调用失败 → 用离线模板生成器产出一份可用 deck（保证闭环不断）。
- 零额外依赖：HTTP 用标准库 urllib；JSON 解析容错。
- 输出契约与 gen_deck 完全一致：生成产物 === 编辑器输入，无需任何格式转换。

环境变量：
  LLM_API_KEY   云端 LLM key（不设置则走本地兜底）
  LLM_BASE_URL  OpenAI 兼容 base（默认 https://api.openai.com/v1）
  LLM_MODEL     模型名（默认 gpt-4o-mini）
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_deck import build_deck  # noqa: E402

LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
HAS_LLM = bool(LLM_API_KEY)

SYSTEM_PROMPT = (
    "你是一名专业的演示文稿大纲设计师，服务于「帆哥 AI PPT Studio」。"
    "用户给出主题或参考文档，你需要产出一份结构清晰、适合做幻灯片的大纲。"
    "只输出一个严格 JSON 对象，不要任何解释或 markdown 围栏，格式如下：\n"
    "{\n"
    '  "title": "演示标题",\n'
    '  "subtitle": "副标题（1 句话，可空）",\n'
    '  "slides": [\n'
    '    {"type":"section","heading":"章节名"},\n'
    '    {"type":"content","heading":"页标题","bullets":["要点1","要点2"]}\n'
    "  ]\n"
    "}\n"
    "要求：3-6 个章节；每章节 1-3 页内容；每页 3-5 个要点；要点简洁有力、口语化、适合 PPT 阅读；"
    "中文输出；标题和要点不要带序号前缀；不要把整段话塞进单个要点。"
)


def _call_llm(topic, doc):
    """返回 outline dict 或 None（无 key / 失败）。"""
    if not HAS_LLM:
        return None
    import urllib.request
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    user = f"主题：{topic}\n"
    if doc:
        user += f"参考文档：\n{doc[:6000]}\n"
    user += "请生成大纲 JSON。"
    messages.append({"role": "user", "content": user})
    body = json.dumps({
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")
    req = urllib.request.Request(
        LLM_BASE_URL + "/chat/completions",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"[gen_llm] LLM 调用失败：{type(e).__name__}: {e}\n")
        return None


def _offline_outline(topic, subtitle=""):
    """无 LLM 时的兜底大纲：围绕主题给一套稳健结构。"""
    t = (topic or "").strip() or "未命名演示"
    return {
        "title": t,
        "subtitle": subtitle or "帆哥 AI PPT Studio · 本地草稿",
        "slides": [
            {"type": "section", "heading": "为什么是这件事"},
            {"type": "content", "heading": "核心问题",
             "bullets": [f"关于「{t}」的关键背景", "当前普遍存在的痛点", "为什么必须现在做"]},
            {"type": "content", "heading": "关键要点",
             "bullets": ["要点一：用数据说话", "要点二：找对标", "要点三：小步快跑验证"]},
            {"type": "section", "heading": "怎么做"},
            {"type": "content", "heading": "行动路径",
             "bullets": ["第一步：明确目标与指标", "第二步：最小成本试错", "第三步：放大可行项"]},
            {"type": "content", "heading": "风险提示",
             "bullets": ["常见坑：伪需求", "常见坑：过早投入", "应对：先验证再加码"]},
        ],
    }


def _to_slides(outline):
    slides = []
    for it in outline.get("slides", []):
        typ = it.get("type", "content")
        if typ == "section":
            slides.append(("section", it.get("heading", "")))
        else:
            slides.append(("content", it.get("heading", ""), it.get("bullets", []) or []))
    return slides


def generate(topic, subtitle="", doc="", out=None):
    """生成 deck HTML。返回 (html, used_llm)。"""
    outline = _call_llm(topic, doc)
    used_llm = outline is not None
    if not used_llm:
        outline = _offline_outline(topic, subtitle)
    title = outline.get("title") or topic or "未命名演示"
    sub = outline.get("subtitle", "") or subtitle
    slides = _to_slides(outline)
    html = build_deck(title, sub, slides)
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
    return html, used_llm


def main():
    import argparse
    ap = argparse.ArgumentParser(description="主题/文档 → 编辑器规范 deck（LLM 或本地兜底）")
    ap.add_argument("--topic", required=True, help="演示主题")
    ap.add_argument("--subtitle", default="", help="副标题")
    ap.add_argument("--doc", default="", help="参考文档文本")
    ap.add_argument("--out", default="deck.html", help="输出 html 路径")
    a = ap.parse_args()
    html, used = generate(a.topic, a.subtitle, a.doc, a.out)
    print(f"OK -> {a.out}  (used_llm={used})")


if __name__ == "__main__":
    main()
