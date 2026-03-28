"""
wechat_article.py — 公众号长文生成器（占位，结构同小红书生成器）
"""
from __future__ import annotations

import os
from typing import Any

from app.domains.content_marketing.generator_base import ContentGenerator, ContentOutput
from app.domains.content_marketing.templates import (
    avoid_traps, budget_breakdown, city_guide, comparison, food_ranking, seasonal_special,
)

_TEMPLATE_MAP = {
    "city_guide": city_guide,
    "food_ranking": food_ranking,
    "budget_breakdown": budget_breakdown,
    "seasonal_special": seasonal_special,
    "avoid_traps": avoid_traps,
    "comparison": comparison,
}

_WECHAT_SYSTEM = (
    "你是一位专注日本旅行的公众号作者，文章结构清晰，深度够但不啰嗦。"
    "有明确的开头（为什么值得读）+ 结构化正文 + 明确结尾引导。"
    "适合在手机上阅读，段落不超过5行，多用小标题分层。"
)


class WechatArticleGenerator(ContentGenerator):
    def __init__(self, model: str = "gpt-4o", api_key: str | None = None, base_url: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url or os.environ.get("AI_BASE_URL", "https://api.openai.com/v1")

    def _call_llm(self, prompt: str) -> str:
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            raise ImportError("需要安装 openai 包：pip install openai")

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        resp = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _WECHAT_SYSTEM},
                {"role": "user", "content": prompt + "\n\n注意：这是公众号长文，正文需要1500-2500字，结构更完整，多用小标题。"},
            ],
            temperature=0.8,
            max_tokens=3000,
        )
        return resp.choices[0].message.content or ""

    def generate(self, topic: dict[str, Any], context: dict[str, Any]) -> ContentOutput:
        tpl = _TEMPLATE_MAP.get(topic.get("template", "city_guide"), city_guide)
        prompt = tpl.build_prompt(topic, context)
        raw = self._call_llm(prompt)
        parsed = tpl.parse_output(raw)

        return ContentOutput(
            title=parsed.get("title", ""),
            body=parsed.get("body", ""),
            image_hints=parsed.get("image_hints", []),
            hashtags=parsed.get("hashtags", []),
            cta_text="想要完整定制行程？点击文末链接查看",
        )
