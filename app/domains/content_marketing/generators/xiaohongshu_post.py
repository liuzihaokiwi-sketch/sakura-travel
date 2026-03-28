"""
xiaohongshu_post.py — 小红书图文生成器

调用 gpt-4o 生成小红书风格内容，支持 6 种选题模板：
city_guide / food_ranking / budget_breakdown / seasonal_special / avoid_traps / comparison
"""
from __future__ import annotations

import os
from typing import Any

from app.domains.content_marketing.generator_base import ContentGenerator, ContentOutput
from app.domains.content_marketing.templates import (
    avoid_traps,
    budget_breakdown,
    city_guide,
    comparison,
    food_ranking,
    seasonal_special,
)

# 模板映射
_TEMPLATE_MAP = {
    "city_guide": city_guide,
    "food_ranking": food_ranking,
    "budget_breakdown": budget_breakdown,
    "seasonal_special": seasonal_special,
    "avoid_traps": avoid_traps,
    "comparison": comparison,
}

# 小红书通用 CTA
_DEFAULT_CTA = "想要完整定制行程？主页查看 / 私信获取 → 7天手账 ¥298"


class XiaohongshuPostGenerator(ContentGenerator):
    """
    小红书图文生成器

    Usage::

        gen = XiaohongshuPostGenerator()
        out = gen.generate(
            topic={"template": "food_ranking"},
            context={"city": "京都", "n": 5, "restaurants": [...]}
        )
        print(out.title)
        print(out.body)
    """

    def __init__(self, model: str = "gpt-4o", api_key: str | None = None, base_url: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url or os.environ.get("AI_BASE_URL", "https://api.openai.com/v1")

    def _call_llm(self, prompt: str) -> str:
        """调用 LLM，返回原始文本"""
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            raise ImportError("需要安装 openai 包：pip install openai")

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        resp = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一位专注日本旅行的小红书博主，文字风格口语化，像朋友分享不像广告。"
                        "善用emoji，分段短（每段2-3行），有"划重点"感，数字细节丰富。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.85,
            max_tokens=2000,
        )
        return resp.choices[0].message.content or ""

    def generate(self, topic: dict[str, Any], context: dict[str, Any]) -> ContentOutput:
        """
        Args:
            topic: 选题配置，至少包含 {"template": "food_ranking", ...}
            context: 实体数据、城市信息等

        Returns:
            ContentOutput
        """
        template_key = topic.get("template", "city_guide")
        tpl = _TEMPLATE_MAP.get(template_key, city_guide)

        prompt = tpl.build_prompt(topic, context)
        raw = self._call_llm(prompt)
        parsed = tpl.parse_output(raw)

        return ContentOutput(
            title=parsed.get("title", ""),
            body=parsed.get("body", ""),
            image_hints=parsed.get("image_hints", []),
            hashtags=parsed.get("hashtags", []),
            cta_text=_DEFAULT_CTA,
        )
