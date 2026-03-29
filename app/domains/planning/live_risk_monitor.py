"""
app/domains/planning/live_risk_monitor.py — 实时风险监控引擎（L4-03）

框架级实现，无外部数据源接入。
当前只读 DB 中已有的 entity_temporal_profiles 数据。
将来接入天气/交通 API 时只需实现 RiskDataProvider 接口并注册。

输入：plan_id + trip_date（或完整 plan dict）
输出：list[RiskAlert]，同时写入 plan_metadata.live_risk_alerts

依赖：
  app.db.models.live_risk_rules.LiveRiskRule
  app.db.models.temporal.EntityTemporalProfile
  app.db.models.derived.ItineraryPlan, ItineraryItem
  sqlalchemy.ext.asyncio.AsyncSession
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Optional, Protocol

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.live_risk_rules import LiveRiskRule

logger = logging.getLogger(__name__)


# ── 数据结构 ───────────────────────────────────────────────────────────────────

@dataclass
class RiskAlert:
    """单条风险警报"""
    entity_id: Optional[str]
    rule_code: str
    risk_level: str          # "low" / "medium" / "high" / "critical"
    message: str
    suggested_action: Optional[str] = None
    action_type: str = "info_only"
    affected_day_index: Optional[int] = None
    source: str = "temporal_profile"   # "temporal_profile" / "live_api" / "rule_engine"


# ── RiskDataProvider 接口（将来扩展用）────────────────────────────────────────

class RiskDataProvider(Protocol):
    """
    风险数据提供者接口。

    将来接入天气/交通 API 时，实现此接口并注入 LiveRiskMonitor。
    当前无实现，引擎降级为只读 temporal_profiles。
    """
    async def get_weather_risk(
        self, corridor: str, trip_date: date
    ) -> Optional[dict]:
        """返回 {'rain_probability': 0.8, 'typhoon': False} 等"""
        ...

    async def get_venue_status(self, entity_id: str, trip_date: date) -> Optional[dict]:
        """返回 {'is_closed': True, 'reason': '定期休馆'} 等"""
        ...


# ── 内置规则（当 DB 中没有规则时的默认种子）──────────────────────────────────

_BUILTIN_RULES = [
    {
        "rule_code": "LR_CLOSURE_001",
        "risk_source": "venue",
        "trigger_window": "T-24h",
        "trigger_condition": {"type": "closed_weekday_match"},
        "action_type": "badge",
        "action_params": {"badge_text": "⚠️ 该景点可能今日休息，请出发前确认"},
        "applies_to_entity_types": ["poi", "activity"],
        "applies_to_corridors": None,
        "priority": 80,
    },
    {
        "rule_code": "LR_CROWD_001",
        "risk_source": "venue",
        "trigger_window": "T-24h",
        "trigger_condition": {"type": "crowd_level_gte", "threshold": "extreme"},
        "action_type": "suggest_alternative",
        "action_params": {"badge_text": "🚶 极度拥挤，建议提前 1 小时到达或使用替代景点"},
        "applies_to_entity_types": ["poi", "activity"],
        "applies_to_corridors": None,
        "priority": 60,
    },
    {
        "rule_code": "LR_SEASON_001",
        "risk_source": "event",
        "trigger_window": "T-72h",
        "trigger_condition": {"type": "season_mismatch"},
        "action_type": "info_only",
        "action_params": {"badge_text": "🌸 当前季节与该景点最佳季节不符"},
        "applies_to_entity_types": ["poi", "activity"],
        "applies_to_corridors": None,
        "priority": 40,
    },
    {
        "rule_code": "LR_BOOKING_001",
        "risk_source": "venue",
        "trigger_window": "T-72h",
        "trigger_condition": {"type": "requires_reservation"},
        "action_type": "notify_user",
        "action_params": {"badge_text": "📅 此处需要提前预约，请确认已订位"},
        "applies_to_entity_types": ["restaurant", "activity"],
        "applies_to_corridors": None,
        "priority": 90,
    },
]


# ── 主引擎 ────────────────────────────────────────────────────────────────────

class LiveRiskMonitor:
    """
    风险监控引擎（框架级，无外部数据源）。

    真实数据源将来接入时只需实现 RiskDataProvider 接口。
    当前只读 entity_temporal_profiles 中的 closed_day / seasonal / crowd 信息。
    """

    def __init__(
        self,
        session: AsyncSession,
        data_provider: Optional[RiskDataProvider] = None,
    ) -> None:
        self._session = session
        self._data_provider = data_provider  # 预留，当前为 None
        self._rules: list[LiveRiskRule] = []
        self._rules_loaded = False

    async def load_rules(self) -> None:
        """加载 DB 中生效的规则；若 DB 为空则使用内置规则骨架"""
        stmt = select(LiveRiskRule).where(LiveRiskRule.is_active == True)  # noqa: E712
        result = await self._session.execute(stmt)
        db_rules = result.scalars().all()

        if db_rules:
            self._rules = list(db_rules)
            logger.info("[LiveRiskMonitor] 加载 %d 条规则（来自 DB）", len(self._rules))
        else:
            # DB 无规则，使用内置骨架（对象化）
            self._rules = [
                _make_rule_obj(r) for r in _BUILTIN_RULES
            ]
            logger.info("[LiveRiskMonitor] 使用 %d 条内置规则（DB 为空）", len(self._rules))

        self._rules_loaded = True

    async def evaluate_plan(
        self,
        plan_id: str,
        trip_date: Optional[date] = None,
    ) -> list[RiskAlert]:
        """
        对一个 plan 跑所有适用规则。

        当前：读取 entity_temporal_profiles 中的 closed_day / seasonal / crowd 信息。
        将来：接入天气 API、交通 API 后扩展。

        Returns:
            RiskAlert 列表
        """
        if not self._rules_loaded:
            await self.load_rules()

        alerts: list[RiskAlert] = []

        # ── 1. 获取 plan 中的所有 items ──────────────────────────────────
        items = await self._get_plan_items(plan_id)
        if not items:
            logger.debug("[LiveRiskMonitor] plan %s 无 items", plan_id)
            return alerts

        # ── 2. 获取所有相关 entity 的 temporal profiles ──────────────────
        entity_ids = list({item.get("entity_id") for item in items if item.get("entity_id")})
        temporal_map = await self._get_temporal_profiles(entity_ids)

        # ── 3. 对每个 item 跑规则 ────────────────────────────────────────
        for item in items:
            entity_id = item.get("entity_id")
            entity_type = item.get("entity_type", "poi")
            day_index = item.get("day_index")
            profiles = temporal_map.get(entity_id, []) if entity_id else []

            for rule in sorted(self._rules, key=lambda r: -(r.priority or 50)):
                # 过滤：entity_type 是否适用
                etypes = rule.applies_to_entity_types or []
                if etypes and entity_type not in etypes:
                    continue

                rule_alerts = self._apply_rule(
                    rule, entity_id, entity_type, day_index, profiles, trip_date
                )
                alerts.extend(rule_alerts)

        # ── 4. 去重（同一 entity + rule_code 只保留一条）──────────────────
        seen: set[tuple] = set()
        deduped: list[RiskAlert] = []
        for a in alerts:
            key = (a.entity_id, a.rule_code)
            if key not in seen:
                seen.add(key)
                deduped.append(a)

        logger.info(
            "[LiveRiskMonitor] plan=%s 生成 %d 条风险警报",
            plan_id, len(deduped),
        )
        return deduped

    def _apply_rule(
        self,
        rule: LiveRiskRule,
        entity_id: Optional[str],
        entity_type: str,
        day_index: Optional[int],
        profiles: list[dict],
        trip_date: Optional[date],
    ) -> list[RiskAlert]:
        """对单个 entity 应用单条规则，返回触发的 RiskAlert"""
        condition = rule.trigger_condition or {}
        ctype = condition.get("type", "")
        action_params = rule.action_params or {}
        badge_text = action_params.get("badge_text", rule.rule_code)

        alerts = []

        if ctype == "closed_weekday_match":
            # 检查 closed_days 字段（temporal_profile 中）
            for p in profiles:
                closed_days = p.get("closed_days") or []
                if trip_date and trip_date.weekday() in closed_days:
                    alerts.append(RiskAlert(
                        entity_id=entity_id,
                        rule_code=rule.rule_code,
                        risk_level="high",
                        message=badge_text,
                        suggested_action="请提前确认营业时间",
                        action_type=rule.action_type,
                        affected_day_index=day_index,
                        source="temporal_profile",
                    ))

        elif ctype == "crowd_level_gte":
            threshold = condition.get("threshold", "extreme")
            for p in profiles:
                crowd = p.get("crowd_level", "")
                if crowd == threshold or (
                    threshold == "high" and crowd in ("high", "extreme")
                ):
                    alerts.append(RiskAlert(
                        entity_id=entity_id,
                        rule_code=rule.rule_code,
                        risk_level="medium",
                        message=badge_text,
                        suggested_action=action_params.get("suggestion", "建议提前到达"),
                        action_type=rule.action_type,
                        affected_day_index=day_index,
                        source="temporal_profile",
                    ))

        elif ctype == "season_mismatch":
            if trip_date:
                month = trip_date.month
                for p in profiles:
                    best_months = p.get("best_visit_months") or []
                    if best_months and month not in best_months:
                        alerts.append(RiskAlert(
                            entity_id=entity_id,
                            rule_code=rule.rule_code,
                            risk_level="low",
                            message=badge_text,
                            action_type=rule.action_type,
                            affected_day_index=day_index,
                            source="temporal_profile",
                        ))

        elif ctype == "requires_reservation":
            for p in profiles:
                if p.get("requires_advance_booking"):
                    alerts.append(RiskAlert(
                        entity_id=entity_id,
                        rule_code=rule.rule_code,
                        risk_level="high",
                        message=badge_text,
                        suggested_action="请确认已完成预约",
                        action_type=rule.action_type,
                        affected_day_index=day_index,
                        source="temporal_profile",
                    ))

        return alerts

    async def _get_plan_items(self, plan_id: str) -> list[dict]:
        """从 itinerary_items 查出 plan 的所有 items"""
        try:
            result = await self._session.execute(
                text("""
                    SELECT ii.entity_id, ii.item_type AS entity_type, id.day_number AS day_index
                    FROM itinerary_items ii
                    JOIN itinerary_days id ON ii.day_id = id.day_id
                    WHERE id.plan_id = :plan_id
                """),
                {"plan_id": plan_id},
            )
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as exc:
            logger.warning("[LiveRiskMonitor] 查询 items 失败: %s", exc)
            return []

    async def _get_temporal_profiles(
        self, entity_ids: list[str]
    ) -> dict[str, list[dict]]:
        """批量查询 entity_temporal_profiles"""
        if not entity_ids:
            return {}
        try:
            from app.db.models.temporal import EntityTemporalProfile
            stmt = select(EntityTemporalProfile).where(
                EntityTemporalProfile.entity_id.in_(entity_ids)
            )
            result = await self._session.execute(stmt)
            profiles = result.scalars().all()

            out: dict[str, list[dict]] = {}
            for p in profiles:
                eid = str(p.entity_id)
                if eid not in out:
                    out[eid] = []
                out[eid].append({
                    "season": p.season,
                    "day_part": p.day_part,
                    "crowd_level": p.crowd_level,
                    "best_visit_months": p.best_visit_months,
                    "closed_days": p.closed_days,
                    "requires_advance_booking": p.requires_advance_booking,
                    "queue_minutes_typical": p.queue_minutes_typical,
                })
            return out
        except Exception as exc:
            logger.warning("[LiveRiskMonitor] 查询 temporal_profiles 失败: %s", exc)
            return {}

    async def write_alerts_to_plan(
        self,
        plan_id: str,
        alerts: list[RiskAlert],
    ) -> None:
        """将 alerts 写入 plan_metadata.live_risk_alerts"""
        try:
            await self._session.execute(
                text("""
                    UPDATE itinerary_plans
                    SET plan_metadata = jsonb_set(
                        COALESCE(plan_metadata, '{}'),
                        '{live_risk_alerts}',
                        :alerts::jsonb
                    ),
                    updated_at = NOW()
                    WHERE plan_id = :plan_id
                """),
                {
                    "alerts": json.dumps(
                        [asdict(a) for a in alerts], ensure_ascii=False, default=str
                    ),
                    "plan_id": plan_id,
                },
            )
            await self._session.flush()
            logger.info(
                "[LiveRiskMonitor] 写入 %d 条 alerts 到 plan %s",
                len(alerts), plan_id,
            )
        except Exception as exc:
            logger.warning("[LiveRiskMonitor] 写入 alerts 失败: %s", exc)


# ── 辅助函数 ──────────────────────────────────────────────────────────────────

def _make_rule_obj(raw: dict) -> Any:
    """将内置规则 dict 转为模拟 LiveRiskRule 对象（无 DB 时用）"""
    class _MockRule:
        rule_code = raw["rule_code"]
        risk_source = raw["risk_source"]
        trigger_window = raw["trigger_window"]
        trigger_condition = raw["trigger_condition"]
        action_type = raw["action_type"]
        action_params = raw.get("action_params")
        applies_to_entity_types = raw.get("applies_to_entity_types", [])
        applies_to_corridors = raw.get("applies_to_corridors")
        priority = raw.get("priority", 50)
    return _MockRule()
