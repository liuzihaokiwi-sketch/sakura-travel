"""
multi_model_review.py
T22-T25: 多模型评审系统 v1

架构：
  T22 - 规划师模型（Planner）  ：评估路线逻辑/时间分配/体力曲线
  T23 - 用户代理模型（Persona）：从目标客群视角挑体验问题
  T24 - 地接运营模型（Ops）    ：检查排队/预约/交通/天气风险
  T25 - 微调守门模型（Guard）  ：为每个 slot 计算可微调边界

入口：run_multi_model_review(plan: dict, profile: dict) -> ReviewReport
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ── 数据结构 ────────────────────────────────────────────────────────────────

@dataclass
class ModelComment:
    model: str              # planner / persona / ops / guard
    severity: str           # info / warning / critical
    slot_ref: Optional[str] # "day1/slot2" 或 None（整体性）
    category: str           # timing / energy / crowd / transport / experience / boundary
    message: str
    suggestion: Optional[str] = None

@dataclass
class SlotBoundary:
    day_number: int
    slot_index: int
    entity_name: str
    can_swap: bool
    can_time_shift: bool    # 时间可前移/后移
    time_shift_range_min: int  # 最大前移分钟数
    swap_requires_admin: bool  # True = 只有管理员可替换
    reason: str

@dataclass
class ReviewReport:
    plan_id: str
    overall_score: float      # 0-10
    passed: bool              # 是否通过，不通过则转人工
    blocker_count: int
    warning_count: int
    comments: list[ModelComment] = field(default_factory=list)
    slot_boundaries: list[SlotBoundary] = field(default_factory=list)
    summary: str = ""


# ── T22: 规划师模型 ──────────────────────────────────────────────────────────

PLANNER_SYSTEM = """你是一位经验丰富的日本旅游行程规划师，专注于行程逻辑审查。
你的任务：检查给定行程方案的时间分配、地理路线合理性、体力曲线。
输出格式：JSON 数组，每项包含 {severity, slot_ref, category, message, suggestion}。
severity 取值：info / warning / critical
category 取值：timing / route / energy / sequence
slot_ref 格式："dayN/slotM"（1-based），整体性问题用 null。
只输出 JSON，不要解释。"""

PLANNER_USER_TEMPLATE = """行程方案：
{plan_json}

旅行者画像：
{profile_json}

请检查：
1. 每天总时长是否合理（景点游览+交通+用餐，建议8-10小时）
2. 相邻景点间通勤是否合理（超过45分钟需标记 warning）
3. 体力曲线（早上安排高体力景点，下午安排休闲/购物）
4. 用餐时段是否覆盖（午餐12-14点，晚餐17-19点）
5. 行程序列是否地理连贯（避免折返）
"""


async def run_planner_model(plan: dict, profile: dict) -> list[ModelComment]:
    """规划师模型：逻辑检查"""
    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic()
        response = await client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1500,
            system=PLANNER_SYSTEM,
            messages=[{
                "role": "user",
                "content": PLANNER_USER_TEMPLATE.format(
                    plan_json=json.dumps(plan, ensure_ascii=False, indent=2),
                    profile_json=json.dumps(profile, ensure_ascii=False),
                )
            }],
        )
        raw = response.content[0].text.strip()
        items = json.loads(raw) if raw.startswith("[") else []
        return [
            ModelComment(
                model="planner",
                severity=i.get("severity", "info"),
                slot_ref=i.get("slot_ref"),
                category=i.get("category", "timing"),
                message=i.get("message", ""),
                suggestion=i.get("suggestion"),
            )
            for i in items
        ]
    except Exception as e:
        logger.warning(f"[T22 Planner] 模型调用失败: {e}")
        return []


# ── T23: 用户代理模型 ────────────────────────────────────────────────────────

PERSONA_SYSTEM = """你是一位即将前往日本旅行的{party_type}，预算{budget_level}，行程{duration_days}天。
你对行程方案有以下期望和担忧，请以用户视角审查行程：
- 景点对你这类旅行者的体验价值是否高
- 是否有你会觉得无聊/累/不适合的安排
- 餐厅是否符合你的口味和预算
输出格式：JSON 数组，每项 {severity, slot_ref, category, message, suggestion}。
category 取值：experience / food / crowd / budget / preference
只输出 JSON。"""

PERSONA_USER_TEMPLATE = """行程方案：
{plan_json}

请从你（{party_type}）的角度，找出 3-5 个最重要的体验问题或亮点不足之处。"""


async def run_persona_model(plan: dict, profile: dict) -> list[ModelComment]:
    """用户代理模型：体验视角检查"""
    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic()

        party_type_map = {
            "couple": "情侣（两人同行）",
            "family_child": "带孩子的家庭（有6-12岁儿童）",
            "family_no_child": "亲子家庭（无小孩）",
            "solo": "独自旅行者",
            "group": "多人朋友团",
            "senior": "中老年旅行者（50+）",
        }
        party_type = party_type_map.get(profile.get("party_type", "solo"), "旅行者")
        budget_level = profile.get("budget_level", "mid")
        duration = profile.get("duration_days", 5)

        system = PERSONA_SYSTEM.format(
            party_type=party_type,
            budget_level=budget_level,
            duration_days=duration,
        )
        response = await client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1200,
            system=system,
            messages=[{
                "role": "user",
                "content": PERSONA_USER_TEMPLATE.format(
                    plan_json=json.dumps(plan, ensure_ascii=False, indent=2),
                    party_type=party_type,
                )
            }],
        )
        raw = response.content[0].text.strip()
        items = json.loads(raw) if raw.startswith("[") else []
        return [
            ModelComment(
                model="persona",
                severity=i.get("severity", "info"),
                slot_ref=i.get("slot_ref"),
                category=i.get("category", "experience"),
                message=i.get("message", ""),
                suggestion=i.get("suggestion"),
            )
            for i in items
        ]
    except Exception as e:
        logger.warning(f"[T23 Persona] 模型调用失败: {e}")
        return []


# ── T24: 地接运营模型 ────────────────────────────────────────────────────────

OPS_SYSTEM = """你是一位常驻日本的地接运营专家，深度了解各景点的实际运营情况。
你的任务：检查行程中的实际运营风险。
检查项：
1. 需要提前预约的景点是否标注了预约方式
2. 容易排队超过60分钟的景点是否安排了错峰策略
3. 景点/餐厅的实际营业时间是否合规
4. 特定季节/天气下的风险（台风/花粉/梅雨）
5. 交通换乘难度是否在旅行者能力范围内
输出格式：JSON 数组，每项 {severity, slot_ref, category, message, suggestion}。
category 取值：reservation / queue / hours / weather / transport_difficulty
只输出 JSON。"""

OPS_USER_TEMPLATE = """行程方案：
{plan_json}

旅行月份：{travel_month}月
旅行者类型：{party_type}

请识别 3-7 个最重要的实际运营风险。"""


async def run_ops_model(plan: dict, profile: dict) -> list[ModelComment]:
    """地接运营模型：实际风险检查"""
    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic()

        travel_dates = profile.get("travel_dates", {})
        start_date = travel_dates.get("start", "")
        travel_month = int(start_date[5:7]) if start_date and len(start_date) >= 7 else 4

        response = await client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1500,
            system=OPS_SYSTEM,
            messages=[{
                "role": "user",
                "content": OPS_USER_TEMPLATE.format(
                    plan_json=json.dumps(plan, ensure_ascii=False, indent=2),
                    travel_month=travel_month,
                    party_type=profile.get("party_type", "solo"),
                )
            }],
        )
        raw = response.content[0].text.strip()
        items = json.loads(raw) if raw.startswith("[") else []
        return [
            ModelComment(
                model="ops",
                severity=i.get("severity", "info"),
                slot_ref=i.get("slot_ref"),
                category=i.get("category", "queue"),
                message=i.get("message", ""),
                suggestion=i.get("suggestion"),
            )
            for i in items
        ]
    except Exception as e:
        logger.warning(f"[T24 Ops] 模型调用失败: {e}")
        return []


# ── T25: 微调守门模型 ────────────────────────────────────────────────────────

GUARD_SYSTEM = """你是一位行程微调边界分析师。
给定行程方案，为每个 slot 判断：
1. can_swap: 是否可以自助替换（true = 用户可自主换，false = 需管理员确认）
2. can_time_shift: 时间是否可以前移/后移
3. time_shift_range_min: 最大可前移/后移分钟数（0表示固定）
4. swap_requires_admin: 替换是否必须经管理员审批
5. reason: 判断理由

核心规则：
- 必须预约的热门景点（如teamLab/豐洲市場）→ swap_requires_admin=true
- 餐厅：同类可自助换，跨类需管理员
- 最后一天的交通相关 slot → can_swap=false
- 体力较高的景点（爬山/神社山路）→ 如果客人是老人/家庭，swap_requires_admin=true

输出格式：JSON 数组，每项：
{day_number, slot_index, entity_name, can_swap, can_time_shift, time_shift_range_min, swap_requires_admin, reason}
只输出 JSON。"""

GUARD_USER_TEMPLATE = """行程方案：
{plan_json}

旅行者画像：
{profile_json}

请为每个 slot 生成微调边界判断。"""


async def run_guard_model(plan: dict, profile: dict) -> list[SlotBoundary]:
    """微调守门模型：为每个 slot 计算可微调边界"""
    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic()

        response = await client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=2000,
            system=GUARD_SYSTEM,
            messages=[{
                "role": "user",
                "content": GUARD_USER_TEMPLATE.format(
                    plan_json=json.dumps(plan, ensure_ascii=False, indent=2),
                    profile_json=json.dumps(profile, ensure_ascii=False),
                )
            }],
        )
        raw = response.content[0].text.strip()
        items = json.loads(raw) if raw.startswith("[") else []
        return [
            SlotBoundary(
                day_number=i.get("day_number", 1),
                slot_index=i.get("slot_index", 0),
                entity_name=i.get("entity_name", ""),
                can_swap=i.get("can_swap", True),
                can_time_shift=i.get("can_time_shift", True),
                time_shift_range_min=i.get("time_shift_range_min", 30),
                swap_requires_admin=i.get("swap_requires_admin", False),
                reason=i.get("reason", ""),
            )
            for i in items
        ]
    except Exception as e:
        logger.warning(f"[T25 Guard] 模型调用失败: {e}")
        return []


# ── T22 总审：综合打分 ────────────────────────────────────────────────────────

def _compute_score(comments: list[ModelComment]) -> tuple[float, bool, int, int]:
    """计算综合分和是否通过"""
    critical_count = sum(1 for c in comments if c.severity == "critical")
    warning_count = sum(1 for c in comments if c.severity == "warning")

    # 基础分 10，每个 critical -2，每个 warning -0.5
    score = max(0.0, 10.0 - critical_count * 2.0 - warning_count * 0.5)

    # 有 critical 则不通过
    passed = critical_count == 0

    return round(score, 1), passed, critical_count, warning_count


def _generate_summary(report: ReviewReport) -> str:
    """生成人类可读的总结"""
    lines = [f"综合评分：{report.overall_score}/10"]
    if not report.passed:
        lines.append(f"❌ 发现 {report.blocker_count} 个严重问题，建议人工审核后发送")
    elif report.warning_count > 0:
        lines.append(f"⚠️  发现 {report.warning_count} 个提示，建议编辑确认")
    else:
        lines.append("✅ 四维审查通过，可直接发送")

    critical = [c for c in report.comments if c.severity == "critical"]
    for c in critical[:3]:
        lines.append(f"  🔴 [{c.model}/{c.category}] {c.message}")

    return "\n".join(lines)


# ── 主入口 ───────────────────────────────────────────────────────────────────

async def run_multi_model_review(
    plan: dict,
    profile: dict,
    plan_id: str = "unknown",
) -> ReviewReport:
    """
    T22-T25 四维并行审查主入口。
    返回 ReviewReport，包含评分、是否通过、所有评论和 slot 边界。
    """
    logger.info(f"[MultiModelReview] 开始四维审查 plan={plan_id}")

    # 并行调用四个模型
    planner_task = run_planner_model(plan, profile)
    persona_task = run_persona_model(plan, profile)
    ops_task = run_ops_model(plan, profile)
    guard_task = run_guard_model(plan, profile)

    planner_comments, persona_comments, ops_comments, slot_boundaries = await asyncio.gather(
        planner_task, persona_task, ops_task, guard_task,
        return_exceptions=True,
    )

    # 处理异常返回
    all_comments: list[ModelComment] = []
    for result in [planner_comments, persona_comments, ops_comments]:
        if isinstance(result, list):
            all_comments.extend(result)
        elif isinstance(result, Exception):
            logger.error(f"[MultiModelReview] 子模型异常: {result}")

    boundaries: list[SlotBoundary] = []
    if isinstance(slot_boundaries, list):
        boundaries = slot_boundaries

    score, passed, blocker_count, warning_count = _compute_score(all_comments)

    report = ReviewReport(
        plan_id=plan_id,
        overall_score=score,
        passed=passed,
        blocker_count=blocker_count,
        warning_count=warning_count,
        comments=all_comments,
        slot_boundaries=boundaries,
    )
    report.summary = _generate_summary(report)

    logger.info(
        f"[MultiModelReview] 完成 plan={plan_id}: score={score}, passed={passed}, "
        f"criticals={blocker_count}, warnings={warning_count}"
    )
    return report


def review_report_to_dict(report: ReviewReport) -> dict:
    """将 ReviewReport 序列化为 dict（用于存库/返回 API）"""
    return {
        "plan_id": report.plan_id,
        "overall_score": report.overall_score,
        "passed": report.passed,
        "blocker_count": report.blocker_count,
        "warning_count": report.warning_count,
        "summary": report.summary,
        "comments": [
            {
                "model": c.model,
                "severity": c.severity,
                "slot_ref": c.slot_ref,
                "category": c.category,
                "message": c.message,
                "suggestion": c.suggestion,
            }
            for c in report.comments
        ],
        "slot_boundaries": [
            {
                "day_number": b.day_number,
                "slot_index": b.slot_index,
                "entity_name": b.entity_name,
                "can_swap": b.can_swap,
                "can_time_shift": b.can_time_shift,
                "time_shift_range_min": b.time_shift_range_min,
                "swap_requires_admin": b.swap_requires_admin,
                "reason": b.reason,
            }
            for b in report.slot_boundaries
        ],
    }
