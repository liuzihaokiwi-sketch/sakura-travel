"""
comparison.py — "A vs B 到底选哪个" 对比模板
"""
from __future__ import annotations

from typing import Any


def build_prompt(topic: dict[str, Any], context: dict[str, Any]) -> str:
    area_a = context.get("area_a", "河原町")
    area_b = context.get("area_b", "京都站前")
    compare_type = context.get("compare_type", "住宿位置")  # 住宿位置 / 路线 / 餐厅

    return f"""你是一位深度了解日本旅行的博主，帮我写一篇小红书对比图文。

【选题】{area_a} vs {area_b}，{compare_type}到底选哪个
【输出要求】
1. 标题：明确对比两个选项，制造选择困难的共鸣，25字以内
2. 正文结构：
   - 开头：这个问题问了多少次，今天彻底讲清楚
   - 分维度对比（4-5个维度）：
     * 每个维度：区域A的情况 | 区域B的情况
     * 用简洁表格或平行结构
   - 我的推荐：哪类人适合选A，哪类人适合选B（给具体标准）
   - 结尾轻CTA：告诉我你的行程，帮你选最合适的，私信/看主页
3. 图片建议：两个区域各一张代表图 + 一张地图对比
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
