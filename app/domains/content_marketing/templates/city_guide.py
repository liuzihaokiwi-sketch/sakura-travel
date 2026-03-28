"""
city_guide.py — "X天Y城市攻略要点" 内容模板

定义 prompt 结构，供生成器调用。
"""
from __future__ import annotations

from typing import Any


def build_prompt(topic: dict[str, Any], context: dict[str, Any]) -> str:
    circle = context.get("circle_name", "关西")
    days = context.get("days", 7)
    highlights = context.get("highlights", [])
    highlights_str = "\n".join(f"- {h}" for h in highlights) if highlights else "（根据实体数据自动填充）"

    return f"""你是一位在日本旅居多年的旅行博主，帮我写一篇小红书/公众号图文攻略。

【选题】{circle}{days}天旅行攻略要点
【目标读者】计划赴日旅行的中国游客
【数据参考】
{highlights_str}

【输出要求】
1. 标题：吸睛，有数字，25字以内
2. 正文：
   - 开头一句话说核心价值（为什么值得看这篇）
   - 分{min(days, 5)}个要点，每个要点100字左右
   - 每个要点用 emoji 开头，有具体数字细节（"排队约15分钟"而非"可能要排队"）
   - 结尾一句轻CTA：想要完整{days}天行程可以私信/看主页
3. 图片建议：3-5张，说明拍什么场景
4. 话题标签：8-10个，含通用标签+目的地专属标签

输出格式：
【标题】...
【正文】...
【配图建议】...
【话题标签】...
"""


def parse_output(raw: str) -> dict[str, Any]:
    """从 LLM 原始输出解析结构化字段"""
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
