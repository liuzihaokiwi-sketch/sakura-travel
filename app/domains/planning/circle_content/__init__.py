"""
circle_content — 每个城市圈独立的静态内容包和 AI 角色配置。

结构：
  每个城市圈一个文件，命名为 {circle_family}.py
  每个文件暴露：
    STATIC_PREP: dict      — 出行准备静态块
    PERSONA_NAME: str      — AI 规划师名字
    DEST_NAME: str         — 目的地中文全称
    DEST_ALIASES: dict     — city_code → 中文名映射
    PERSONA_BIO: str       — AI 角色背景（用于 system prompt）
"""
from __future__ import annotations

from typing import Any


def get_circle_content(circle_family: str) -> "CircleContent":
    """按 circle_family 加载对应内容包，找不到时 fallback 到 japan。"""
    _map = {
        "kansai": "kansai",
        "kanto": "kanto",
        "hokkaido": "hokkaido",
        "south_china": "south_china",
        "guangdong": "guangdong",
        "northern_xinjiang": "northern_xinjiang",
    }
    module_name = _map.get(circle_family, "kansai")
    import importlib
    mod = importlib.import_module(f"app.domains.planning.circle_content.{module_name}")
    return CircleContent(
        static_prep=mod.STATIC_PREP,
        persona_name=mod.PERSONA_NAME,
        dest_name=mod.DEST_NAME,
        dest_aliases=mod.DEST_ALIASES,
        persona_bio=mod.PERSONA_BIO,
        visual_trigger_tags=getattr(mod, "VISUAL_TRIGGER_TAGS", set()),
    )


def get_circle_family_from_circle_id(circle_id: str) -> str:
    """从 circle_id 推断 circle_family。"""
    if not circle_id:
        return "kansai"
    lower = circle_id.lower()
    if "kansai" in lower:
        return "kansai"
    if "kanto" in lower or "tokyo" in lower:
        return "kanto"
    if "hokkaido" in lower:
        return "hokkaido"
    if "south_china" in lower or "guangzhou" in lower or "shenzhen" in lower:
        return "south_china"
    if "guangdong" in lower:
        return "guangdong"
    if "xinjiang" in lower or "northern" in lower:
        return "northern_xinjiang"
    return "kansai"


class CircleContent:
    def __init__(
        self,
        static_prep: dict[str, Any],
        persona_name: str,
        dest_name: str,
        dest_aliases: dict[str, str],
        persona_bio: str,
        visual_trigger_tags: set[str],
    ) -> None:
        self.static_prep = static_prep
        self.persona_name = persona_name
        self.dest_name = dest_name
        self.dest_aliases = dest_aliases
        self.persona_bio = persona_bio
        self.visual_trigger_tags = visual_trigger_tags

    def resolve_dest_name(self, city_code: str) -> str:
        return self.dest_aliases.get(city_code, city_code)
