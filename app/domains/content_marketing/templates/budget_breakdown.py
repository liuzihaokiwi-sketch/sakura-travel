"""
budget_breakdown.py — "去XX花多少钱" 内容模板
"""
from __future__ import annotations

from typing import Any


def build_prompt(topic: dict[str, Any], context: dict[str, Any]) -> str:
    circle = context.get("circle_name", "关西")
    days = context.get("days", 7)
    budget_level = context.get("budget_level", "mid")
    level_desc = {"budget": "穷游/背包", "mid": "普通游客", "premium": "享受型", "luxury": "奢华"}.get(budget_level, "普通游客")

    return f"""你是一位做过多次{circle}旅行的理财博主，帮我写一篇小红书预算拆解图文。

【选题】{days}天{circle}旅行花多少钱，适合{level_desc}
【输出要求】
1. 标题：有具体数字范围+天数+地区，制造真实感，25字以内
2. 正文：
   - 开头：总费用范围（最低-最高），一句话定调
   - 分类拆解：机票/住宿/餐饮/交通/门票/购物，每项给出范围和省钱建议
   - 每天平均开销是多少
   - 2-3个省钱小技巧（具体可操作）
   - 结尾轻CTA：想要精确到每餐每景点的完整行程，私信/看主页
3. 图片建议：建议一张费用汇总表截图，一张实拍消费收据
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
