"""
avoid_traps.py — "千万别踩的N个坑" 避雷模板
"""
from __future__ import annotations

from typing import Any


def build_prompt(topic: dict[str, Any], context: dict[str, Any]) -> str:
    city = context.get("city", "大阪")
    n = context.get("n", 5)
    traps = context.get("traps", [])
    traps_str = "\n".join(f"- {t}" for t in traps[:n]) if traps else "（根据真实旅行经验自动生成）"

    return f"""你是一位去过{city}多次的旅行博主，帮我写一篇小红书避雷图文。

【选题】去{city}千万别踩的{n}个坑
【避雷素材参考】
{traps_str}

【输出要求】
1. 标题：强烈警示感，有数字，引发好奇，25字以内
2. 正文：
   - 开头：一句话说踩坑成本（损失多少时间/金钱）
   - 每个坑：坑名+为什么坑+正确做法（具体到操作步骤）
   - 用"❌ 别这样" + "✅ 应该这样"的对比格式
   - 数字具体（"排队2小时"不是"很长时间"）
   - 结尾轻CTA：想要完整避坑版行程，私信/看主页
3. 图片建议：建议配一张"踩坑现场"类对比图或实拍
4. 话题标签：8-10个

输出格式：
【标题】...
【正文】...
【配图建议】...
【话题标签】...
"""


def parse_output(raw: str) -> dict[str, Any]:
    sections: dict[str, str] = {}
    current_key = None
    lines = []
    for line in raw.splitlines():
        if line.startswith("【") and "】" in line:
            if current_key:
                sections[current_key] = "\n".join(lines).strip()
            current_key = line[1:line.index("】")]
            lines = [line[line.index("】") + 1:].strip()]
        else:
            lines.append(line)
    if current_key:
        sections[current_key] = "\n".join(lines).strip()

    hashtags = [t.strip().lstrip("#") for t in sections.get("话题标签", "").split() if t.strip()]
    image_hints = [h.strip() for h in sections.get("配图建议", "").splitlines() if h.strip()]
    return {
        "title": sections.get("标题", ""),
        "body": sections.get("正文", ""),
        "image_hints": image_hints,
        "hashtags": hashtags,
    }
