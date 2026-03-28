"""
seasonal_special.py — "XX赏樱/赏枫最佳时间" 季节专题模板
"""
from __future__ import annotations

from typing import Any


def build_prompt(topic: dict[str, Any], context: dict[str, Any]) -> str:
    circle = context.get("circle_name", "关西")
    year = context.get("year", 2026)
    season_type = context.get("season_type", "sakura")  # sakura / koyo
    season_name = "赏樱" if season_type == "sakura" else "赏枫"
    spots = context.get("spots", [])
    spots_str = "\n".join(f"- {s.get('name', '')}：预计{s.get('peak_date', '')}，{s.get('note', '')}" for s in spots[:5]) if spots else "（根据实体数据自动填充）"

    return f"""你是一位专注日本旅行的资深博主，帮我写一篇{year}年{circle}{season_name}专题图文。

【选题】{year}{circle}{season_name}最佳时间+路线
【景点数据参考】
{spots_str}

【输出要求】
1. 标题：含年份+地点+季节关键词，SEO友好，25字以内
2. 正文：
   - 开头：{year}年预测时间（几月几日前后），权威数据来源
   - 推荐赏花/赏枫地点 TOP 5，每个含：预计最佳时间、特色、人流情况、附近美食
   - 实用贴士 3-5 条（早去避拥挤、穿什么、买什么票等具体建议）
   - 结尾轻CTA：想要完整{season_name}行程（含每日路线+餐厅），私信/看主页
3. 图片建议：每个景点一张图，建议用往年实拍
4. 话题标签：8-10个（含年份标签）

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
