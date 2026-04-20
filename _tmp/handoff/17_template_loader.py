"""
Template Loader — 读取 content/kansai/ 的 JSON/MD 文件。

只读、带缓存。规则来源只有 JSON（policy.json / days.json / seasonal_events.json），
不读 brief.md 和 form_design.md（那些是给人看的文档）。
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_BASE = Path(__file__).resolve().parents[3] / "content" / "kansai"


class TemplateLoader:
    """读取 templates_v2/ 目录的模板数据，带内存缓存。"""

    def __init__(self, base_path: str | Path | None = None):
        self.base = Path(base_path) if base_path else _DEFAULT_BASE
        if not self.base.exists():
            raise FileNotFoundError(f"templates_v2 directory not found: {self.base}")

    # ── 顶层文件 ───────────────────────────────────────────────

    @lru_cache(maxsize=1)
    def load_policy(self) -> dict[str, Any]:
        """硬约束、退化路径、校验红线。"""
        return self._read_json(self.base / "policy.json")

    @lru_cache(maxsize=1)
    def load_tag_vocab(self) -> dict[str, Any]:
        """受控标签词表。"""
        return self._read_json(self.base / "tag_vocab.json")

    # ── 城市级文件 ─────────────────────────────────────────────

    def load_city_days(self, city: str) -> dict[str, Any]:
        """Day 模板库（含装配元数据）。"""
        return self._read_json(self.base / city / "days.json")

    def load_city_restaurants(self, city: str) -> dict[str, Any]:
        """餐厅池（含标签、点评、A/B 定位）。"""
        return self._read_json(self.base / city / "restaurants.json")

    def load_city_hotels(self, city: str) -> dict[str, Any]:
        """酒店池（含标签、点评）。"""
        return self._read_json(self.base / city / "hotels.json")

    def load_city_shops(self, city: str) -> dict[str, Any]:
        """店铺池（标签驱动，无替换矩阵）。"""
        return self._read_json(self.base / city / "shops.json")

    def load_city_narrative(self, city: str) -> str:
        """城市性格 + 每日叙事种子（Markdown）。"""
        path = self.base / city / "narrative.md"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def load_seasonal_events(self, city: str) -> dict[str, Any]:
        """季节活动（硬日期 + 机制）。"""
        return self._read_json(self.base / city / "seasonal_events.json")

    def load_city_tips(self, city: str) -> str:
        """实用小技巧（Markdown，直接进手账本）。"""
        path = self.base / city / "tips.md"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    # ── 运营层 ─────────────────────────────────────────────────

    def load_live_prices(self) -> dict[str, Any]:
        """票价信息。"""
        return self._read_json(self.base / "live_facts" / "prices.json")

    def load_live_hours(self) -> dict[str, Any]:
        """营业时间。"""
        return self._read_json(self.base / "live_facts" / "hours.json")

    def load_live_booking(self) -> dict[str, Any]:
        """预约信息。"""
        return self._read_json(self.base / "live_facts" / "booking.json")

    def load_live_facts(self) -> dict[str, Any]:
        """合并所有运营信息。"""
        return {
            "prices": self.load_live_prices(),
            "hours": self.load_live_hours(),
            "booking": self.load_live_booking(),
        }

    # ── 便捷方法 ───────────────────────────────────────────────

    def list_cities(self) -> list[str]:
        """列出所有有 days.json 的城市。"""
        cities = []
        for p in self.base.iterdir():
            if p.is_dir() and (p / "days.json").exists():
                cities.append(p.name)
        return sorted(cities)

    def load_city_all(self, city: str) -> dict[str, Any]:
        """一次性加载某城市的所有模板数据。"""
        return {
            "days": self.load_city_days(city),
            "restaurants": self.load_city_restaurants(city),
            "hotels": self.load_city_hotels(city),
            "shops": self.load_city_shops(city),
            "narrative": self.load_city_narrative(city),
            "seasonal_events": self.load_seasonal_events(city),
            "tips": self.load_city_tips(city),
        }

    # ── 内部 ───────────────────────────────────────────────────

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        if not path.exists():
            logger.warning("Template file not found: %s", path)
            return {}
        with open(path, encoding="utf-8") as f:
            return json.load(f)


# 模块级单例，方便导入使用
@lru_cache(maxsize=1)
def get_template_loader(base_path: str | None = None) -> TemplateLoader:
    """获取 TemplateLoader 单例。"""
    return TemplateLoader(base_path)
