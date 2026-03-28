"""
food_ranking.py — "必吃N家XX" 内容模板
"""
from __future__ import annotations

from typing import Any


def build_prompt(topic: dict[str, Any], context: dict[str, Any]) -> str:
    city = context.get("city", "京都")
    food_type = context.get("food_type", "餐厅")
    n = context.get("n", 5)
    restaurants = context.get("restaurants", [])
    rest_str = "\n".join(
        f"- {r.get('name', '')}：人均{r.get('avg_price', '?')}元，{r.get('highlight', '')}"
        for r in restaurants[:n]
    ) if restaurants else "（根据实体数据自动填充）"

    return f"""你是一位旅居{city}的美食博主，帮我写一篇小红书美食排行图文。

【选题】{city}必吃{n}家{food_type}
【餐厅数据参考】
{rest_str}

【输出要求】
1. 标题：带数字+地点+食物类型，制造好奇心，25字以内
2. 正文：
   - 开头：一句话说本地人标准（区别于游客路线）
   - 每家餐厅一段：名字+地址要点+人均+必点+排队情况+适合什么人
   - 数字要具体（"人均150-200元""周末排队约30分钟"）
   - 结尾轻CTA：想要含这些餐厅的完整行程，私信/看主页
3. 图片建议：每家餐厅建议配一张招牌菜图
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
