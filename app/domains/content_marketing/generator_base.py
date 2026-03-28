"""
generator_base.py — 所有营销内容生成器的基类
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContentOutput:
    """生成器统一输出格式"""
    title: str
    body: str                          # 正文（可含 Markdown 分段）
    image_hints: list[str] = field(default_factory=list)   # 建议配图描述
    hashtags: list[str] = field(default_factory=list)      # 话题标签
    cta_text: str = ""                 # 行动引导文案


class ContentGenerator(ABC):
    """营销内容生成器基类"""

    @abstractmethod
    def generate(self, topic: dict[str, Any], context: dict[str, Any]) -> ContentOutput:
        """
        Args:
            topic: 选题配置，来自 topic_pool
            context: 实体数据、城市圈信息、季节数据等
        Returns:
            ContentOutput
        """
        ...
