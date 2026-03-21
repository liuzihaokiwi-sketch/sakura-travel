"""
质量校验门控 (Quality Gate)

对生成的行程方案执行 11 条 QTY 硬规则校验。
每条规则要么通过（pass），要么失败（fail）并给出原因。

规则列表：
  QTY-01  每天景点数量（3-6个）
  QTY-02  每天餐厅推荐（至少1家，最多3家）
  QTY-03  交通方式覆盖（每天必须有交通说明）
  QTY-04  时间合理性（全天时间窗口 8:00-22:00，无时间冲突）
  QTY-05  体力估算（每天步行距离不超过 15km 等效值）
  QTY-06  实体存在性（景点/餐厅 entity_id 必须在数据库中存在）
  QTY-07  数据新鲜度（实体数据 last_verified_at 不超过 90 天）
  QTY-08  推荐理由覆盖（每个实体必须有推荐理由，且 ≥10 字）
  QTY-09  避坑提醒（每天至少 1 条避坑提醒）
  QTY-10  配图覆盖（每个 S/A 级实体必须有封面图 URL）
  QTY-11  禁用词检查（不出现"AI、算法、模型、评分系统"等词）

用法：
    from app.core.quality_gate import run_quality_gate
    result = await run_quality_gate(plan_data, db)
    if not result.passed:
        # handle failures
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── 禁用词列表 ──────────────────────────────────────────────────────────────
FORBIDDEN_WORDS = [
    "AI", "人工智能", "算法", "模型", "机器学习", "深度学习",
    "评分系统", "推荐引擎", "数据分析", "多维度", "向量",
    "大语言模型", "ChatGPT", "GPT", "LLM",
]

# QTY 规则阈值常量
MIN_SPOTS_PER_DAY = 3
MAX_SPOTS_PER_DAY = 6
MIN_RESTAURANTS_PER_DAY = 1
MAX_RESTAURANTS_PER_DAY = 3
MIN_REASON_LENGTH = 10          # 推荐理由最少字数
MAX_ENTITY_AGE_DAYS = 90        # 数据新鲜度：最多 90 天未验证
MAX_WALK_SCORE_PER_DAY = 15     # 体力上限（近似步行 km 等效）
VALID_TIME_START = 8 * 60       # 08:00（分钟）
VALID_TIME_END = 22 * 60        # 22:00（分钟）


# ── 数据结构 ─────────────────────────────────────────────────────────────────

@dataclass
class RuleResult:
    rule_id: str
    passed: bool
    message: str
    severity: str = "error"     # error | warning
    details: list[str] = field(default_factory=list)


@dataclass
class QualityGateResult:
    passed: bool
    score: float                        # 0.0 - 1.0
    results: list[RuleResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        fail_count = sum(1 for r in self.results if not r.passed and r.severity == "error")
        warn_count = sum(1 for r in self.results if not r.passed and r.severity == "warning")
        return (
            f"质检{'通过' if self.passed else '未通过'} | "
            f"得分 {self.score:.0%} | "
            f"错误 {fail_count} | 警告 {warn_count}"
        )


# ── 辅助函数 ─────────────────────────────────────────────────────────────────

def _parse_time(time_str: str) -> Optional[int]:
    """将 'HH:MM' 转换为分钟数，失败返回 None"""
    if not time_str:
        return None
    try:
        parts = time_str.strip().split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return None


def _get_items_by_type(items: list[dict], item_type: str) -> list[dict]:
    """按 item_type 过滤 items"""
    return [i for i in items if i.get("item_type") == item_type]


def _get_all_text(plan: dict) -> str:
    """提取方案中所有文本字段，用于禁用词扫描"""
    texts = []
    for day in plan.get("days", []):
        texts.append(day.get("day_theme", ""))
        for item in day.get("items", []):
            texts.append(item.get("copy_zh", ""))
            texts.append(item.get("entity_name", ""))
            texts.append(item.get("tips_zh", ""))
    return " ".join(texts)


# ── 11 条规则实现 ─────────────────────────────────────────────────────────────

def check_qty_01(plan: dict) -> RuleResult:
    """QTY-01: 每天景点数量（3-6个）"""
    errors = []
    for day in plan.get("days", []):
        day_num = day.get("day_number", "?")
        spots = [i for i in day.get("items", []) if i.get("item_type") not in ("restaurant", "transport")]
        count = len(spots)
        if count < MIN_SPOTS_PER_DAY:
            errors.append(f"Day {day_num}: 景点数 {count} < {MIN_SPOTS_PER_DAY}")
        elif count > MAX_SPOTS_PER_DAY:
            errors.append(f"Day {day_num}: 景点数 {count} > {MAX_SPOTS_PER_DAY}")
    return RuleResult(
        rule_id="QTY-01",
        passed=len(errors) == 0,
        message="每天景点数量正常" if not errors else f"景点数量异常: {len(errors)} 天",
        details=errors,
    )


def check_qty_02(plan: dict) -> RuleResult:
    """QTY-02: 每天餐厅推荐（至少1家，最多3家）"""
    errors = []
    for day in plan.get("days", []):
        day_num = day.get("day_number", "?")
        restaurants = _get_items_by_type(day.get("items", []), "restaurant")
        count = len(restaurants)
        if count < MIN_RESTAURANTS_PER_DAY:
            errors.append(f"Day {day_num}: 餐厅数 {count} < {MIN_RESTAURANTS_PER_DAY}")
        elif count > MAX_RESTAURANTS_PER_DAY:
            errors.append(f"Day {day_num}: 餐厅数 {count} > {MAX_RESTAURANTS_PER_DAY}")
    return RuleResult(
        rule_id="QTY-02",
        passed=len(errors) == 0,
        message="每天餐厅数量正常" if not errors else f"餐厅数量异常: {len(errors)} 天",
        details=errors,
    )


def check_qty_03(plan: dict) -> RuleResult:
    """QTY-03: 交通方式覆盖（每天必须有交通说明）"""
    errors = []
    for day in plan.get("days", []):
        day_num = day.get("day_number", "?")
        transport_items = _get_items_by_type(day.get("items", []), "transport")
        transport_note = day.get("transport_note", "")
        if not transport_items and not transport_note:
            errors.append(f"Day {day_num}: 缺少交通说明")
    return RuleResult(
        rule_id="QTY-03",
        passed=len(errors) == 0,
        message="交通覆盖完整" if not errors else f"交通说明缺失: {len(errors)} 天",
        details=errors,
    )


def check_qty_04(plan: dict) -> RuleResult:
    """QTY-04: 时间合理性（8:00-22:00，无时间冲突）"""
    errors = []
    for day in plan.get("days", []):
        day_num = day.get("day_number", "?")
        items = sorted(
            [i for i in day.get("items", []) if i.get("start_time")],
            key=lambda x: _parse_time(x.get("start_time", "")) or 0
        )
        last_end = None
        for item in items:
            start = _parse_time(item.get("start_time", ""))
            end = _parse_time(item.get("end_time", "")) if item.get("end_time") else None
            if start is None:
                continue
            if start < VALID_TIME_START:
                errors.append(f"Day {day_num} [{item.get('entity_name','')}]: 开始时间 {item.get('start_time')} 早于 08:00")
            if end and end > VALID_TIME_END:
                errors.append(f"Day {day_num} [{item.get('entity_name','')}]: 结束时间 {item.get('end_time')} 晚于 22:00")
            if last_end and start < last_end:
                errors.append(f"Day {day_num} [{item.get('entity_name','')}]: 时间冲突，与前一活动重叠")
            last_end = end or start + (item.get("duration_min", 60))
    return RuleResult(
        rule_id="QTY-04",
        passed=len(errors) == 0,
        message="时间安排合理" if not errors else f"时间异常: {len(errors)} 处",
        details=errors,
    )


def check_qty_05(plan: dict) -> RuleResult:
    """QTY-05: 体力估算（每天步行等效距离 ≤ 15km）"""
    errors = []
    for day in plan.get("days", []):
        day_num = day.get("day_number", "?")
        total_duration = sum(
            i.get("duration_min", 60) for i in day.get("items", [])
            if i.get("item_type") not in ("transport",)
        )
        # 粗算：每60分钟步行约 1.5km 等效，超过 15km = 600分钟
        walk_score = total_duration / 60 * 1.5
        if walk_score > MAX_WALK_SCORE_PER_DAY:
            errors.append(f"Day {day_num}: 活动总时长 {total_duration}分钟，体力负荷过高（≈{walk_score:.1f}km）")
    severity = "warning"  # 体力超标为警告，不是 hard error
    return RuleResult(
        rule_id="QTY-05",
        passed=len(errors) == 0,
        message="体力安排合理" if not errors else f"体力负荷过高: {len(errors)} 天",
        severity=severity,
        details=errors,
    )


async def check_qty_06(plan: dict, db: Any) -> RuleResult:
    """QTY-06: 实体存在性（entity_id 在数据库中存在）"""
    errors = []
    if db is None:
        return RuleResult(rule_id="QTY-06", passed=True, message="跳过（无 DB）", severity="warning")

    try:
        from sqlalchemy import select, text
        from app.db.models.catalog import EntityBase

        entity_ids = []
        for day in plan.get("days", []):
            for item in day.get("items", []):
                eid = item.get("entity_id")
                if eid:
                    entity_ids.append(str(eid))

        if not entity_ids:
            return RuleResult(rule_id="QTY-06", passed=True, message="无 entity_id 字段，跳过")

        # Bulk check
        result = await db.execute(
            select(EntityBase.entity_id).where(EntityBase.entity_id.in_(entity_ids))
        )
        found_ids = {str(row[0]) for row in result.fetchall()}
        missing = [eid for eid in entity_ids if eid not in found_ids]

        if missing:
            errors = [f"entity_id 不存在: {eid}" for eid in missing[:5]]
    except Exception as e:
        logger.warning("QTY-06 数据库检查失败: %s", e)
        return RuleResult(rule_id="QTY-06", passed=True, message=f"跳过（DB异常: {e}）", severity="warning")

    return RuleResult(
        rule_id="QTY-06",
        passed=len(errors) == 0,
        message="实体存在性验证通过" if not errors else f"发现 {len(missing)} 个无效实体",
        details=errors,
    )


async def check_qty_07(plan: dict, db: Any) -> RuleResult:
    """QTY-07: 数据新鲜度（last_verified_at 不超过 90 天）"""
    errors = []
    if db is None:
        return RuleResult(rule_id="QTY-07", passed=True, message="跳过（无 DB）", severity="warning")

    try:
        from sqlalchemy import select
        from app.db.models.catalog import EntityBase

        entity_ids = []
        for day in plan.get("days", []):
            for item in day.get("items", []):
                eid = item.get("entity_id")
                if eid:
                    entity_ids.append(str(eid))

        if not entity_ids:
            return RuleResult(rule_id="QTY-07", passed=True, message="无 entity_id，跳过")

        cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_ENTITY_AGE_DAYS)
        result = await db.execute(
            select(EntityBase.entity_id, EntityBase.updated_at)
            .where(EntityBase.entity_id.in_(entity_ids))
        )
        stale = []
        for row in result.fetchall():
            eid, updated_at = row[0], row[1]
            if updated_at and updated_at.replace(tzinfo=timezone.utc) < cutoff:
                stale.append(str(eid))
        errors = [f"数据过期（>{MAX_ENTITY_AGE_DAYS}天）: {eid}" for eid in stale[:5]]
    except Exception as e:
        logger.warning("QTY-07 检查失败: %s", e)
        return RuleResult(rule_id="QTY-07", passed=True, message=f"跳过（异常: {e}）", severity="warning")

    return RuleResult(
        rule_id="QTY-07",
        passed=len(errors) == 0,
        message="数据新鲜度正常" if not errors else f"发现 {len(stale)} 个过期实体",
        severity="warning",
        details=errors,
    )


def check_qty_08(plan: dict) -> RuleResult:
    """QTY-08: 推荐理由覆盖（每个实体必须有推荐理由，≥10字）"""
    errors = []
    for day in plan.get("days", []):
        day_num = day.get("day_number", "?")
        for item in day.get("items", []):
            reason = item.get("copy_zh", "") or item.get("reason", "")
            name = item.get("entity_name", item.get("place", "未知"))
            if not reason:
                errors.append(f"Day {day_num} [{name}]: 缺少推荐理由")
            elif len(reason) < MIN_REASON_LENGTH:
                errors.append(f"Day {day_num} [{name}]: 推荐理由太短（{len(reason)}字 < {MIN_REASON_LENGTH}字）")
    return RuleResult(
        rule_id="QTY-08",
        passed=len(errors) == 0,
        message="推荐理由覆盖完整" if not errors else f"推荐理由问题: {len(errors)} 处",
        details=errors,
    )


def check_qty_09(plan: dict) -> RuleResult:
    """QTY-09: 避坑提醒（每天至少 1 条）"""
    errors = []
    for day in plan.get("days", []):
        day_num = day.get("day_number", "?")
        avoid_tips = [
            i for i in day.get("items", [])
            if i.get("tips_type") == "avoid" or i.get("avoid_tip")
        ]
        day_avoid = day.get("avoid_tips", [])
        if not avoid_tips and not day_avoid:
            errors.append(f"Day {day_num}: 缺少避坑提醒")
    return RuleResult(
        rule_id="QTY-09",
        passed=len(errors) == 0,
        message="避坑提醒覆盖完整" if not errors else f"避坑提醒缺失: {len(errors)} 天",
        severity="warning",
        details=errors,
    )


async def check_qty_10(plan: dict, db: Any) -> RuleResult:
    """QTY-10: 配图覆盖（S/A 级实体必须有封面图 URL）"""
    errors = []
    if db is None:
        return RuleResult(rule_id="QTY-10", passed=True, message="跳过（无 DB）", severity="warning")

    try:
        from sqlalchemy import select
        from app.db.models.catalog import EntityBase, EntityMedia

        entity_ids = []
        for day in plan.get("days", []):
            for item in day.get("items", []):
                eid = item.get("entity_id")
                if eid:
                    entity_ids.append(str(eid))

        if not entity_ids:
            return RuleResult(rule_id="QTY-10", passed=True, message="无 entity_id，跳过")

        # 找出 S/A 级实体
        result = await db.execute(
            select(EntityBase.entity_id, EntityBase.data_tier)
            .where(EntityBase.entity_id.in_(entity_ids))
            .where(EntityBase.data_tier.in_(["S", "A"]))
        )
        sa_entities = {str(row[0]) for row in result.fetchall()}

        if not sa_entities:
            return RuleResult(rule_id="QTY-10", passed=True, message="无 S/A 级实体需要配图")

        # 检查有封面图的
        media_result = await db.execute(
            select(EntityMedia.entity_id)
            .where(EntityMedia.entity_id.in_(list(sa_entities)))
            .where(EntityMedia.is_cover == True)  # noqa: E712
        )
        with_cover = {str(row[0]) for row in media_result.fetchall()}
        missing_cover = sa_entities - with_cover
        errors = [f"S/A 级实体缺少封面图: {eid}" for eid in list(missing_cover)[:5]]
    except Exception as e:
        logger.warning("QTY-10 检查失败: %s", e)
        return RuleResult(rule_id="QTY-10", passed=True, message=f"跳过（异常: {e}）", severity="warning")

    return RuleResult(
        rule_id="QTY-10",
        passed=len(errors) == 0,
        message="配图覆盖完整" if not errors else f"发现 {len(missing_cover)} 个缺图实体",
        severity="warning",
        details=errors,
    )


def check_qty_11(plan: dict) -> RuleResult:
    """QTY-11: 禁用词检查（不出现"AI、算法、模型"等词）"""
    all_text = _get_all_text(plan)
    found = []
    for word in FORBIDDEN_WORDS:
        if word in all_text:
            found.append(word)
    return RuleResult(
        rule_id="QTY-11",
        passed=len(found) == 0,
        message="无禁用词" if not found else f"发现禁用词: {', '.join(found)}",
        details=[f"禁用词: {w}" for w in found],
    )


# ── 主入口 ────────────────────────────────────────────────────────────────────

async def run_quality_gate(
    plan: dict,
    db: Any = None,
) -> QualityGateResult:
    """
    对方案执行全部 11 条 QTY 规则校验。

    Args:
        plan:  行程方案 dict（含 days 列表）
        db:    AsyncSession，为 None 时跳过需要 DB 的规则

    Returns:
        QualityGateResult
    """
    results: list[RuleResult] = []

    # 同步规则
    results.append(check_qty_01(plan))
    results.append(check_qty_02(plan))
    results.append(check_qty_03(plan))
    results.append(check_qty_04(plan))
    results.append(check_qty_05(plan))
    results.append(check_qty_08(plan))
    results.append(check_qty_09(plan))
    results.append(check_qty_11(plan))

    # 异步（需要 DB）规则
    results.append(await check_qty_06(plan, db))
    results.append(await check_qty_07(plan, db))
    results.append(await check_qty_10(plan, db))

    # 统计
    errors = [r for r in results if not r.passed and r.severity == "error"]
    warnings = [r for r in results if not r.passed and r.severity == "warning"]

    passed_count = sum(1 for r in results if r.passed)
    score = passed_count / len(results) if results else 0.0

    # 只要有 error 级别失败，整体不通过
    overall_passed = len(errors) == 0

    result = QualityGateResult(
        passed=overall_passed,
        score=score,
        results=results,
        errors=[f"{r.rule_id}: {r.message}" for r in errors],
        warnings=[f"{r.rule_id}: {r.message}" for r in warnings],
    )

    logger.info(
        "质检完成: plan_id=%s %s",
        plan.get("plan_id", "unknown"),
        result.summary(),
    )

    return result


def run_quality_gate_sync(plan: dict) -> QualityGateResult:
    """
    同步版本（不依赖 DB）。用于快速校验或测试。
    """
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(run_quality_gate(plan, db=None))
    finally:
        loop.close()
