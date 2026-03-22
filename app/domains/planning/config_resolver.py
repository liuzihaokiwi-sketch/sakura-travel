"""
config_resolver.py — 运营配置解析器

优先级：plan_override > segment > circle > global
每层查找状态为 active 的配置包，合并 weights/thresholds/switches 字段。
高优先级的 key 覆盖低优先级的同名 key（浅合并）。

用法：
    resolver = ConfigResolver(session)
    cfg = await resolver.resolve(
        circle_id="kansai_v1",
        segment="couple",
        plan_id="uuid-xxx",
    )
    photo_bias = cfg.weight("photo_bias", default=1.0)
    max_secondary = cfg.threshold("max_secondary_per_day", default=3)
    shadow_on = cfg.switch("enable_shadow_write", default=False)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.config_center import ConfigPack, ConfigPackVersion, ConfigScope

logger = logging.getLogger(__name__)

# ── 默认配置值（全站兜底）────────────────────────────────────────────────────

DEFAULT_WEIGHTS: dict[str, float] = {
    # 活动
    "major_activity_base_weight":    1.0,
    "secondary_activity_base_weight":0.7,
    "theme_family_bias":             0.0,
    "season_bias":                   0.0,
    "photo_bias":                    0.0,
    "food_bias":                     0.0,
    "shopping_bias":                 0.0,
    "recovery_bias":                 0.0,
    # 酒店
    "hotel_quality_weight":          0.55,
    "hotel_location_weight":         0.25,
    "hotel_commute_weight":          0.10,
    "hotel_experience_weight":       0.05,
    "hotel_last_night_safe_weight":  0.05,
    "hotel_switch_penalty_weight":   -0.10,
    # 餐厅
    "dining_quality_weight":         0.60,
    "dining_queue_penalty_weight":   -0.15,
    "dining_detour_penalty_weight":  -0.10,
    "destination_dining_bonus":      0.10,
    "backup_meal_bonus":             0.05,
    # 节奏
    "dense_day_penalty":             -0.15,
    "backtrack_penalty":             -0.20,
    "long_transfer_penalty":         -0.15,
    "same_corridor_bonus":           0.15,
    "day_trip_penalty":              -0.10,
    "late_arrival_penalty":          -0.10,
    "early_departure_penalty":       -0.10,
}

DEFAULT_THRESHOLDS: dict[str, Any] = {
    "max_secondary_per_day":         3,
    "max_cross_city_days":           3,
    "max_hotel_switches":            2,
    "max_transfer_minutes_per_day":  90,
    "max_walk_minutes_per_day":      40,
    "strong_risk_redline":           0.8,
    "low_match_review_threshold":    0.5,
    # max_major_per_trip_by_day_count: dict keyed by total_days
    "max_major_per_trip_by_day_count": {
        "3": 2, "4": 3, "5": 3, "6": 4, "7": 4,
        "8": 5, "9": 5, "10": 6, "14": 7,
    },
}

DEFAULT_SWITCHES: dict[str, bool] = {
    "enable_city_circle_pipeline":       True,
    "enable_fragment_first":             True,
    "enable_hotel_base_strategy":        True,
    "enable_conditional_pages":          True,
    "enable_shadow_write":               False,
    "enable_live_risk_monitor":          True,
    "enable_operator_override":          True,
    "enable_review_required_for_low_hit": True,
}

# 作用域优先级（越大越优先）
_SCOPE_PRIORITY = {
    "global":        0,
    "circle":        1,
    "segment":       2,
    "plan_override": 3,
}


# ── 已解析配置对象 ────────────────────────────────────────────────────────────

@dataclass
class ResolvedConfig:
    """合并后的配置快照，供生成流水线消费。"""
    weights:    dict[str, Any] = field(default_factory=dict)
    thresholds: dict[str, Any] = field(default_factory=dict)
    switches:   dict[str, bool] = field(default_factory=dict)
    # 来源 trace（用于 audit / explain）
    sources: list[dict] = field(default_factory=list)

    def weight(self, key: str, default: float = 0.0) -> float:
        return float(self.weights.get(key, DEFAULT_WEIGHTS.get(key, default)))

    def threshold(self, key: str, default: Any = None) -> Any:
        val = self.thresholds.get(key, DEFAULT_THRESHOLDS.get(key, default))
        return val

    def switch(self, key: str, default: bool = False) -> bool:
        return bool(self.switches.get(key, DEFAULT_SWITCHES.get(key, default)))

    def max_major_for_days(self, total_days: int) -> int:
        mapping = self.threshold("max_major_per_trip_by_day_count", {})
        # 找最接近且不超过 total_days 的档位
        candidates = [(int(k), v) for k, v in mapping.items() if int(k) <= total_days]
        if candidates:
            return max(candidates, key=lambda x: x[0])[1]
        return 4  # 全局兜底


# ── ConfigResolver ────────────────────────────────────────────────────────────

class ConfigResolver:
    """
    按作用域优先级加载并合并配置。

    resolve() 返回 ResolvedConfig（全量合并后的快照），
    调用方不需要关心优先级逻辑。
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def resolve(
        self,
        circle_id: Optional[str] = None,
        segment: Optional[str] = None,
        plan_id: Optional[str] = None,
    ) -> ResolvedConfig:
        """
        按 global → circle → segment → plan_override 顺序加载配置，
        高优先级覆盖低优先级（浅合并）。
        """
        layers = await self._load_layers(circle_id=circle_id, segment=segment, plan_id=plan_id)

        # 从低优先级到高优先级合并
        merged_weights:    dict[str, Any] = dict(DEFAULT_WEIGHTS)
        merged_thresholds: dict[str, Any] = dict(DEFAULT_THRESHOLDS)
        merged_switches:   dict[str, bool] = dict(DEFAULT_SWITCHES)
        sources: list[dict] = [{"scope": "default", "pack_id": None, "version_no": None}]

        for layer in sorted(layers, key=lambda x: _SCOPE_PRIORITY.get(x["scope_type"], 0)):
            ver = layer["version"]
            if ver.weights:
                merged_weights.update(ver.weights)
            if ver.thresholds:
                merged_thresholds.update(ver.thresholds)
            if ver.switches:
                merged_switches.update(ver.switches)
            sources.append({
                "scope": layer["scope_type"],
                "scope_value": layer["scope_value"],
                "pack_id": str(layer["pack_id"]),
                "version_no": ver.version_no,
            })

        return ResolvedConfig(
            weights=merged_weights,
            thresholds=merged_thresholds,
            switches=merged_switches,
            sources=sources,
        )

    async def _load_layers(
        self,
        circle_id: Optional[str],
        segment: Optional[str],
        plan_id: Optional[str],
    ) -> list[dict]:
        """
        加载所有匹配作用域的 active 配置包及其当前版本。
        返回 [{scope_type, scope_value, pack_id, version: ConfigPackVersion}]
        """
        # 构建候选作用域条件
        scope_conditions = [
            ConfigScope.scope_type == "global",
        ]
        if circle_id:
            scope_conditions.append(
                and_(ConfigScope.scope_type == "circle", ConfigScope.scope_value == circle_id)
            )
        if segment:
            scope_conditions.append(
                and_(ConfigScope.scope_type == "segment", ConfigScope.scope_value == segment)
            )
        if plan_id:
            scope_conditions.append(
                and_(ConfigScope.scope_type == "plan_override", ConfigScope.scope_value == plan_id)
            )

        from sqlalchemy import or_
        scopes_q = await self._session.execute(
            select(ConfigScope).where(
                and_(
                    ConfigScope.is_active == True,
                    or_(*scope_conditions),
                )
            )
        )
        scopes = scopes_q.scalars().all()

        if not scopes:
            return []

        # 按 pack_id 分组，找到对应的 active pack + active version
        pack_ids = list({s.pack_id for s in scopes})
        packs_q = await self._session.execute(
            select(ConfigPack).where(
                and_(
                    ConfigPack.pack_id.in_(pack_ids),
                    ConfigPack.status == "active",
                )
            )
        )
        active_packs: dict = {p.pack_id: p for p in packs_q.scalars().all()}

        if not active_packs:
            return []

        # 加载各 pack 的 active version
        results = []
        for scope in scopes:
            pack = active_packs.get(scope.pack_id)
            if not pack or pack.active_version_no is None:
                continue

            ver_q = await self._session.execute(
                select(ConfigPackVersion).where(
                    and_(
                        ConfigPackVersion.pack_id == scope.pack_id,
                        ConfigPackVersion.version_no == pack.active_version_no,
                    )
                )
            )
            ver = ver_q.scalar_one_or_none()
            if not ver:
                continue

            # 灰度：rollout_pct < 1.0 时，随机抽样
            if float(scope.rollout_pct or 1.0) < 1.0:
                import random
                if random.random() > float(scope.rollout_pct):
                    continue

            results.append({
                "scope_type":  scope.scope_type,
                "scope_value": scope.scope_value,
                "pack_id":     scope.pack_id,
                "version":     ver,
            })

        return results

    async def get_switch(self, key: str, **resolve_kwargs) -> bool:
        """快捷方法：只获取单个开关值。"""
        cfg = await self.resolve(**resolve_kwargs)
        return cfg.switch(key)

    async def get_weight(self, key: str, **resolve_kwargs) -> float:
        """快捷方法：只获取单个权重值。"""
        cfg = await self.resolve(**resolve_kwargs)
        return cfg.weight(key)
