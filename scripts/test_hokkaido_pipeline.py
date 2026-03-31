"""
test_hokkaido_pipeline.py — 北海道行程生成全链路质量验证

独立可执行脚本，覆盖 7 个北海道用例，逐步验证 pipeline 每个阶段的输入输出并打分。
任何人/AI 直接 `python scripts/test_hokkaido_pipeline.py` 即可运行。

用例矩阵:
  HK-01  情侣5天基础    札幌+小樽+函馆   couple       5月  moderate
  HK-02  家庭带幼儿     札幌+小樽        family_child  7月  relaxed
  HK-03  冬季滑雪温泉   札幌+登别        couple       2月  moderate
  HK-04  单人美食深度   札幌             solo         9月  packed
  HK-05  函馆洞爷专线   函馆+洞爷        couple       6月  moderate
  HK-06  老年慢旅      札幌+登别         senior       10月 relaxed
  HK-07  7天环岛       札幌+旭川+富良野+函馆  group   8月  packed

每步评分 0-10，共 8 步，满分 80。>= 48 为 PASS，>= 40 为 WARN，否则 FAIL。

用法:
  python scripts/test_hokkaido_pipeline.py              # 全部用例
  python scripts/test_hokkaido_pipeline.py HK-01         # 单个用例
  python scripts/test_hokkaido_pipeline.py HK-01 HK-05   # 多个用例
"""
from __future__ import annotations

import asyncio
import logging
import sys
import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Optional

# 确保项目根目录在 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(levelname)-5s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
# 关闭 SQLAlchemy echo 和其他噪音
for _logger_name in ("sqlalchemy.engine", "sqlalchemy", "sqlalchemy.engine.Engine",
                      "app", "httpx", "httpcore"):
    logging.getLogger(_logger_name).setLevel(logging.ERROR)

import os as _os
_os.environ["APP_DEBUG"] = "false"  # 确保 SQLAlchemy echo=False

# Windows 控制台编码修复 — 避免日文字符打印崩溃
import io as _io
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = _io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ═══════════════════════════════════════════════════════════════════════════════
# 用例定义
# ═══════════════════════════════════════════════════════════════════════════════

HOKKAIDO_CASES: list[dict[str, Any]] = [
    {
        "case_id": "HK-01",
        "label": "情侣 5 天基础",
        "desc": "最常见北海道画像，验证基线质量和多城市覆盖",
        "duration_days": 5,
        "cities": [
            {"city_code": "sapporo", "nights": 2},
            {"city_code": "otaru", "nights": 1},
            {"city_code": "hakodate", "nights": 1},
        ],
        "party_type": "couple",
        "budget_level": "mid",
        "pace": "moderate",
        "travel_dates": {"start": "2026-05-10", "end": "2026-05-14"},
        "must_have_tags": ["food", "nature", "onsen"],
        "avoid_tags": [],
        "arrival_airport": "CTS",
        "departure_airport": "CTS",
        "checks": {
            "min_items_per_normal_day": 4,
            "must_have_cities_in_timeline": ["sapporo", "hakodate"],
            "season_filter_active": True,    # 5月不应有冬季活动
            "expect_lunch_dinner": True,
        },
    },
    {
        "case_id": "HK-02",
        "label": "家庭带幼儿",
        "desc": "有 3 岁小孩，节奏慢，验证亲子约束和时间窗",
        "duration_days": 5,
        "cities": [
            {"city_code": "sapporo", "nights": 3},
            {"city_code": "otaru", "nights": 1},
        ],
        "party_type": "family_child",
        "budget_level": "mid",
        "pace": "relaxed",
        "travel_dates": {"start": "2026-07-20", "end": "2026-07-24"},
        "must_have_tags": ["nature", "food"],
        "avoid_tags": [],
        "arrival_airport": "CTS",
        "departure_airport": "CTS",
        "checks": {
            "max_end_time": "19:30",         # 带小孩不超过 19:30
            "max_items_per_day": 8,
            "expect_lunch_dinner": True,
        },
    },
    {
        "case_id": "HK-03",
        "label": "冬季滑雪温泉",
        "desc": "2月滑雪+温泉，验证冬季活动选入、季节过滤反向",
        "duration_days": 4,
        "cities": [
            {"city_code": "sapporo", "nights": 2},
            {"city_code": "noboribetsu", "nights": 1},
        ],
        "party_type": "couple",
        "budget_level": "premium",
        "pace": "moderate",
        "travel_dates": {"start": "2026-02-05", "end": "2026-02-08"},
        "must_have_tags": ["ski", "onsen", "food"],
        "avoid_tags": [],
        "arrival_airport": "CTS",
        "departure_airport": "CTS",
        "checks": {
            "season_should_include_winter": True,  # 2月应该有冬季活动
            "must_have_cities_in_timeline": ["noboribetsu"],
        },
    },
    {
        "case_id": "HK-04",
        "label": "单人美食深度",
        # NOTE: 理想情况是 3 天，但 hokkaido_nature_circle min_days=4，
        # hokkaido_city_circle 是空壳无数据。待 city_circle 数据补齐后改回 3 天。
        "desc": "纯美食团，景点随便看看，验证餐厅比重",
        "duration_days": 4,
        "cities": [
            {"city_code": "sapporo", "nights": 3},
        ],
        "party_type": "solo",
        "budget_level": "premium",
        "pace": "packed",
        "travel_dates": {"start": "2026-09-15", "end": "2026-09-17"},
        "must_have_tags": ["food"],
        "avoid_tags": [],
        "arrival_airport": "CTS",
        "departure_airport": "CTS",
        "checks": {
            "min_items_per_normal_day": 5,   # packed 节奏要填满
        },
    },
    {
        "case_id": "HK-05",
        "label": "函馆+洞爷专线",
        "desc": "完全不经过札幌，验证非札幌城市的活动填充",
        "duration_days": 4,
        "cities": [
            {"city_code": "hakodate", "nights": 2},
            {"city_code": "toya", "nights": 1},
        ],
        "party_type": "couple",
        "budget_level": "mid",
        "pace": "moderate",
        "travel_dates": {"start": "2026-06-01", "end": "2026-06-04"},
        "must_have_tags": ["nature", "onsen"],
        "avoid_tags": [],
        "arrival_airport": "HKD",
        "departure_airport": "HKD",
        "checks": {
            "must_have_cities_in_timeline": ["hakodate", "toya"],
            "must_not_have_cities": ["sapporo"],   # 不应有札幌活动
            "min_items_per_normal_day": 3,
        },
    },
    {
        "case_id": "HK-06",
        "label": "老年慢旅",
        "desc": "70岁老人，节奏慢，早收工，验证时间窗约束",
        "duration_days": 5,
        "cities": [
            {"city_code": "sapporo", "nights": 3},
            {"city_code": "noboribetsu", "nights": 1},
        ],
        "party_type": "senior",
        "budget_level": "premium",
        "pace": "relaxed",
        "travel_dates": {"start": "2026-10-10", "end": "2026-10-14"},
        "must_have_tags": ["onsen", "nature"],
        "avoid_tags": [],
        "arrival_airport": "CTS",
        "departure_airport": "CTS",
        "checks": {
            "max_end_time": "19:30",
        },
    },
    {
        "case_id": "HK-07",
        "label": "7 天环岛",
        "desc": "长行程多城市，验证城市覆盖和骨架容量",
        "duration_days": 7,
        "cities": [
            {"city_code": "sapporo", "nights": 2},
            {"city_code": "asahikawa", "nights": 1},
            {"city_code": "furano", "nights": 1},
            {"city_code": "hakodate", "nights": 2},
        ],
        "party_type": "group",
        "budget_level": "mid",
        "pace": "packed",
        "travel_dates": {"start": "2026-08-01", "end": "2026-08-07"},
        "must_have_tags": ["nature", "food"],
        "avoid_tags": [],
        "arrival_airport": "CTS",
        "departure_airport": "CTS",
        "checks": {
            "must_have_cities_in_timeline": ["sapporo", "hakodate"],
            "min_items_per_normal_day": 4,
        },
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# 评分结果结构
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class StepResult:
    step: str           # E1 ~ E8
    name: str
    score: float = 0.0
    max_score: float = 10.0
    inputs: str = ""
    outputs: str = ""
    deductions: list[str] = field(default_factory=list)
    details: list[str] = field(default_factory=list)
    error: str = ""


@dataclass
class CaseResult:
    case_id: str
    label: str
    steps: list[StepResult] = field(default_factory=list)

    @property
    def total_score(self) -> float:
        return sum(s.score for s in self.steps)

    @property
    def max_total(self) -> float:
        return sum(s.max_score for s in self.steps)

    @property
    def status(self) -> str:
        t = self.total_score
        if t >= 48:
            return "PASS"
        if t >= 40:
            return "WARN"
        return "FAIL"


# ═══════════════════════════════════════════════════════════════════════════════
# 评分函数
# ═══════════════════════════════════════════════════════════════════════════════

def score_e1_circle(result, case: dict) -> StepResult:
    """E1: 城市圈选择"""
    s = StepResult(step="E1", name="城市圈选择")
    if result is None:
        s.error = "城市圈选择失败（无结果）"
        return s

    s.score = 10.0
    selected = result.selected
    candidates = result.candidates

    city_codes = [c["city_code"] for c in case.get("cities", [])]
    s.inputs = f"party={case['party_type']}, days={case['duration_days']}, cities={city_codes}"

    if not selected:
        s.score = 0
        s.deductions.append("-10 未选中任何城市圈")
        s.outputs = "selected=None"
        return s

    s.outputs = f"selected={selected.circle_id} (score={selected.total_score:.2f})"
    s.details.append(f"候选数: {len(candidates)}")
    for c in candidates[:5]:
        s.details.append(f"  {c.circle_id}: {c.total_score:.2f}" +
                         (f" [{c.reject_reason}]" if c.reject_reason else ""))

    # 评分
    if selected.total_score < 0.3:
        s.score -= 3
        s.deductions.append(f"-3 选中圈分数过低({selected.total_score:.2f})")
    elif selected.total_score < 0.5:
        s.score -= 1
        s.deductions.append(f"-1 选中圈分数偏低({selected.total_score:.2f})")

    if len(candidates) < 2:
        s.score -= 1
        s.deductions.append(f"-1 候选圈太少({len(candidates)})")

    return s


def score_e2_eligibility(result, case: dict, travel_month: int) -> StepResult:
    """E2: 资格过滤"""
    s = StepResult(step="E2", name="资格过滤")
    if result is None:
        s.error = "资格过滤失败（无结果）"
        return s

    s.score = 10.0
    total_entities = len(result.entity_verdicts)
    passed_entities = len(result.passed_entity_ids)
    total_clusters = len(result.cluster_verdicts)
    passed_clusters = len(result.passed_cluster_ids)

    s.inputs = f"month={travel_month}, avoid={case.get('avoid_tags', [])}"
    s.outputs = (f"实体={passed_entities}/{total_entities}, "
                 f"簇={passed_clusters}/{total_clusters}")

    # 统计过滤原因
    fail_reasons: dict[str, int] = {}
    for v in result.entity_verdicts.values():
        if not v.passed:
            for code in v.fail_codes:
                key = code.split(":")[0]
                fail_reasons[key] = fail_reasons.get(key, 0) + 1
    for reason, count in sorted(fail_reasons.items(), key=lambda x: -x[1]):
        s.details.append(f"  {reason}: {count} 个")

    # 评分
    if total_entities == 0:
        s.score = 0
        s.deductions.append("-10 无实体")
        return s

    pass_rate = passed_entities / total_entities
    if pass_rate < 0.5:
        s.score -= 3
        s.deductions.append(f"-3 通过率过低({pass_rate:.0%})")
    elif pass_rate < 0.7:
        s.score -= 1
        s.deductions.append(f"-1 通过率偏低({pass_rate:.0%})")

    if passed_clusters < 3:
        s.score -= 2
        s.deductions.append(f"-2 通过簇太少({passed_clusters})")

    # 季节过滤验证
    checks = case.get("checks", {})
    if checks.get("season_filter_active"):
        eg005_count = fail_reasons.get("EG-005_SEASON_MISMATCH", 0)
        if eg005_count > 0:
            s.details.append(f"  [OK] 季节过滤生效: {eg005_count} 个实体被过滤")
        else:
            s.score -= 1
            s.deductions.append("-1 季节过滤未生效（应有冬季实体被过滤）")

    return s


def score_e3_ranking(result, case: dict) -> StepResult:
    """E3: 主活动排序"""
    s = StepResult(step="E3", name="主活动排序")
    if result is None:
        s.error = "主活动排序失败（无结果）"
        return s

    s.score = 10.0
    selected = result.selected_majors
    cap_used = result.capacity_used
    cap_total = result.capacity_total

    s.inputs = f"days={case['duration_days']}, pace={case['pace']}"
    s.outputs = (f"选中={len(selected)}, "
                 f"容量={cap_used:.1f}/{cap_total:.1f}")

    for m in selected:
        s.details.append(f"  {m.cluster_id}: score={m.major_score:.1f}, cap={m.capacity_units}")

    # 评分
    if len(selected) == 0:
        s.score = 0
        s.deductions.append("-10 无选中主活动")
        return s

    if cap_used > cap_total * 1.2:
        s.score -= 2
        s.deductions.append(f"-2 容量超载({cap_used:.1f}>{cap_total:.1f})")
    elif cap_used < cap_total * 0.3:
        s.score -= 2
        s.deductions.append(f"-2 容量利用不足({cap_used:.1f}/{cap_total:.1f})")

    # must-go 检查
    unresolved = getattr(result, "must_go_unresolved", []) or []
    if unresolved:
        s.score -= 1
        s.deductions.append(f"-1 must-go 未解决: {unresolved}")

    return s


def score_e4_hotel(result, case: dict) -> StepResult:
    """E4: 酒店策略"""
    s = StepResult(step="E4", name="酒店策略")
    if result is None:
        s.error = "酒店策略失败（无结果）"
        return s

    s.score = 10.0
    s.inputs = f"days={case['duration_days']}, switch_tolerance=medium"
    s.outputs = (f"preset={result.preset_name}, bases={len(result.bases)}, "
                 f"switches={result.switch_count}, "
                 f"last_night_safe={result.last_night_safe}")

    for b in result.bases:
        s.details.append(f"  {b.base_city} x{b.nights}晚 (day {b.check_in_day})")

    expected_nights = case["duration_days"] - 1
    actual_nights = result.total_nights
    if actual_nights != expected_nights:
        s.score -= 2
        s.deductions.append(f"-2 总晚数不对({actual_nights} vs 期望{expected_nights})")

    if not result.last_night_safe:
        s.score -= 2
        s.deductions.append("-2 最后一晚不安全（距机场太远）")

    if result.switch_count > case["duration_days"] - 2:
        s.score -= 1
        s.deductions.append(f"-1 换酒店次数过多({result.switch_count})")

    return s


def score_e5_skeleton(skeleton, case: dict) -> StepResult:
    """E5: 骨架构建"""
    s = StepResult(step="E5", name="骨架构建")
    if skeleton is None:
        s.error = "骨架构建失败（无结果）"
        return s

    s.score = 10.0
    frames = skeleton.frames
    s.inputs = f"days={case['duration_days']}, pace={case['pace']}"
    s.outputs = f"frames={len(frames)}"

    if len(frames) != case["duration_days"]:
        s.score -= 3
        s.deductions.append(f"-3 天数不匹配({len(frames)} vs {case['duration_days']})")

    for f in frames:
        driver_name = f.main_driver_name or f.main_driver or "-"
        s.details.append(
            f"  Day {f.day_index} [{f.day_type:10s}] "
            f"corridor={f.primary_corridor or '-':25s} "
            f"driver={driver_name[:20]:20s} "
            f"remaining={f.remaining_minutes}min"
        )
        if f.remaining_minutes < 0:
            s.score -= 1
            s.deductions.append(f"-1 Day {f.day_index} 剩余时间为负({f.remaining_minutes})")

    # 检查 day_type
    if frames and frames[0].day_type != "arrival":
        s.score -= 1
        s.deductions.append("-1 第一天不是 arrival")
    if frames and frames[-1].day_type != "departure":
        s.score -= 1
        s.deductions.append("-1 最后一天不是 departure")

    return s


def score_e6_timeline(timelines: list[dict], case: dict) -> StepResult:
    """E6: 时间线填充"""
    s = StepResult(step="E6", name="时间线填充")
    if not timelines:
        s.score = 0
        s.error = "时间线为空"
        return s

    s.score = 10.0
    total_items = sum(t["item_count"] for t in timelines)
    s.inputs = f"days={len(timelines)}"
    s.outputs = f"总活动={total_items}"

    checks = case.get("checks", {})
    min_items = checks.get("min_items_per_normal_day", 3)
    max_end = checks.get("max_end_time", "21:30")
    max_end_min = int(max_end.split(":")[0]) * 60 + int(max_end.split(":")[1])

    for t in timelines:
        day_type = t["day_type"]
        items = t["items"]
        city = t["city"]
        item_count = t["item_count"]

        # 展示每天时间线
        s.details.append(f"  Day {t['day_index']} [{day_type}] {city}: {item_count} items")
        for it in items:
            type_icon = {"poi": "P", "restaurant": "R"}.get(it["type"], "?")
            s.details.append(f"    {it['start']}-{it['end']} [{type_icon}] {it['name'][:30]}")

        # 评分
        if day_type in ("normal",) and item_count == 0:
            s.score -= 3
            s.deductions.append(f"-3 Day {t['day_index']} [{city}] 0 个活动")
        elif day_type in ("normal",) and item_count < min_items:
            s.score -= 1
            s.deductions.append(f"-1 Day {t['day_index']} [{city}] 活动偏少({item_count}<{min_items})")

        # 午餐/晚餐检查
        if checks.get("expect_lunch_dinner") and day_type == "normal":
            has_lunch = any(it["slot"] == "lunch" for it in items)
            has_dinner = any(it["slot"] == "dinner" for it in items)
            if not has_lunch:
                s.score -= 0.5
                s.deductions.append(f"-0.5 Day {t['day_index']} 无午餐")
            if not has_dinner:
                s.score -= 0.5
                s.deductions.append(f"-0.5 Day {t['day_index']} 无晚餐")

        # 结束时间检查
        if items:
            last_end = items[-1]["end"]
            last_min = int(last_end.split(":")[0]) * 60 + int(last_end.split(":")[1])
            if last_min > max_end_min:
                s.score -= 0.5
                s.deductions.append(f"-0.5 Day {t['day_index']} 结束太晚({last_end}>{max_end})")

    # 城市覆盖检查
    actual_cities = set(t["city"] for t in timelines if t["item_count"] > 0)
    required_cities = checks.get("must_have_cities_in_timeline", [])
    for rc in required_cities:
        if rc not in actual_cities:
            s.score -= 2
            s.deductions.append(f"-2 {rc} 无活动填充")

    # 不应出现的城市
    forbidden_cities = checks.get("must_not_have_cities", [])
    for fc in forbidden_cities:
        if fc in actual_cities:
            s.score -= 2
            s.deductions.append(f"-2 不应有 {fc} 的活动")

    s.score = max(0, s.score)
    return s


def score_e7_quality_gate(gate_result, case: dict) -> StepResult:
    """E7: 质量门控"""
    s = StepResult(step="E7", name="质量门控")
    if gate_result is None:
        s.error = "质量门控未运行"
        return s

    s.score = 10.0
    s.inputs = f"rules=QTY-01..11"
    s.outputs = f"passed={gate_result.passed}, score={gate_result.score:.2f}"

    for err in gate_result.errors:
        s.details.append(f"  [ERROR] {err}")
    for warn in gate_result.warnings:
        s.details.append(f"  [WARN]  {warn}")

    error_count = len(gate_result.errors)
    warn_count = len(gate_result.warnings)

    if error_count > 0:
        penalty = min(5, error_count * 1.5)
        s.score -= penalty
        s.deductions.append(f"-{penalty:.1f} {error_count} 个 error")

    if warn_count > 3:
        s.score -= 1
        s.deductions.append(f"-1 warning 过多({warn_count})")

    s.score = max(0, s.score)
    return s


def score_e8_eval(eval_result, case: dict) -> StepResult:
    """E8: 离线评测"""
    s = StepResult(step="E8", name="离线评测")
    if eval_result is None:
        s.error = "离线评测未运行"
        return s

    s.score = 10.0
    overall = eval_result.overall
    s.inputs = "weighted 8-dimension eval"
    s.outputs = f"overall={overall:.2f}"
    s.details.append(f"  completeness={eval_result.completeness:.1f}")
    s.details.append(f"  feasibility={eval_result.feasibility:.1f}")
    s.details.append(f"  diversity={eval_result.diversity:.1f}")
    s.details.append(f"  preference_match={eval_result.preference_match:.1f}")
    s.details.append(f"  quality={eval_result.quality:.1f}")
    s.details.append(f"  safety={eval_result.safety:.1f}")
    s.details.append(f"  pacing_quality={eval_result.pacing_quality:.1f}")

    if overall < 0.5:
        s.score -= 4
        s.deductions.append(f"-4 overall 过低({overall:.2f})")
    elif overall < 0.65:
        s.score -= 2
        s.deductions.append(f"-2 overall 偏低({overall:.2f})")
    elif overall < 0.7:
        s.score -= 1
        s.deductions.append(f"-1 overall 边缘({overall:.2f})")

    if eval_result.safety < 7:
        s.score -= 2
        s.deductions.append(f"-2 safety 不达标({eval_result.safety:.1f})")

    s.score = max(0, s.score)
    return s


# ═══════════════════════════════════════════════════════════════════════════════
# Pipeline 执行器
# ═══════════════════════════════════════════════════════════════════════════════

async def run_one_case(case: dict) -> CaseResult:
    """执行单个用例的完整 pipeline，逐步收集结果并评分。"""
    from app.db.session import AsyncSessionLocal
    from app.db.models.business import TripRequest, TripProfile
    from sqlalchemy import select

    cr = CaseResult(case_id=case["case_id"], label=case["label"])
    travel_dates = case.get("travel_dates", {})
    start_str = travel_dates.get("start", "2026-05-10")
    end_str = travel_dates.get("end", "2026-05-14")
    travel_month = int(start_str[5:7]) if start_str else 5

    async with AsyncSessionLocal() as session:
        # ── 创建临时 TripRequest + TripProfile ──
        trip = TripRequest(raw_input=case, status="assembling")
        session.add(trip)
        await session.flush()
        trip_id = trip.trip_request_id

        profile = TripProfile(
            trip_request_id=trip_id,
            duration_days=case["duration_days"],
            cities=case["cities"],
            party_type=case["party_type"],
            budget_level=case["budget_level"],
            pace=case["pace"],
            travel_dates=travel_dates,
            must_have_tags=case.get("must_have_tags", []),
            avoid_tags=case.get("avoid_tags", []),
            arrival_airport=case.get("arrival_airport", "CTS"),
            departure_airport=case.get("departure_airport", "CTS"),
            arrival_shape="same_city",
            daytrip_tolerance="medium",
            hotel_switch_tolerance="medium",
            requested_city_circle=case.get("requested_city_circle", "hokkaido_nature_circle"),
        )
        session.add(profile)
        await session.flush()

        try:
            # ── E1: 城市圈选择 ──
            from app.domains.planning.city_circle_selector import select_city_circle
            try:
                circle_result = await select_city_circle(session, profile)
                cr.steps.append(score_e1_circle(circle_result, case))
            except Exception as exc:
                sr = StepResult(step="E1", name="城市圈选择", error=str(exc))
                cr.steps.append(sr)
                circle_result = None

            if not circle_result or not circle_result.selected:
                # 后续步骤无法继续
                for step_id, step_name in [("E2", "资格过滤"), ("E3", "主活动排序"),
                                           ("E4", "酒店策略"), ("E5", "骨架构建"),
                                           ("E6", "时间线填充"), ("E7", "质量门控"),
                                           ("E8", "离线评测")]:
                    cr.steps.append(StepResult(step=step_id, name=step_name,
                                              error="上游失败，跳过"))
                return cr

            circle_id = circle_result.selected_circle_id
            circle = await session.get(
                (await __import_city_circle()), circle_id
            )

            # ── E2: 资格过滤 ──
            from app.domains.planning.eligibility_gate import (
                run_eligibility_gate, EligibilityContext,
            )
            all_cities = list(set(
                (circle.base_city_codes or []) + (circle.extension_city_codes or [])
            )) if circle else []

            eg_ctx = EligibilityContext(
                circle_id=circle_id,
                city_codes=all_cities,
                avoid_tags=case.get("avoid_tags", []),
                party_type=case["party_type"],
                has_elderly=case["party_type"] == "senior",
                has_children=case["party_type"] == "family_child",
                travel_month=travel_month,
            )
            try:
                eg_result = await run_eligibility_gate(session, eg_ctx)
                cr.steps.append(score_e2_eligibility(eg_result, case, travel_month))
            except Exception as exc:
                cr.steps.append(StepResult(step="E2", name="资格过滤", error=str(exc)))
                eg_result = None

            if eg_result is None:
                for step_id, step_name in [("E3", "主活动排序"), ("E4", "酒店策略"),
                                           ("E5", "骨架构建"), ("E6", "时间线填充"),
                                           ("E7", "质量门控"), ("E8", "离线评测")]:
                    cr.steps.append(StepResult(step=step_id, name=step_name,
                                              error="上游失败，跳过"))
                return cr

            # ── E3: 主活动排序 ──
            from app.domains.planning.major_activity_ranker import rank_major_activities
            from app.domains.planning.precheck_gate import run_precheck_gate
            from app.domains.planning.constraint_compiler import compile_constraints
            from app.domains.planning.policy_resolver import resolve_policy_set

            resolved_policy = resolve_policy_set(circle_id, circle=circle)
            constraints = compile_constraints(profile, resolved_policy=resolved_policy)

            # precheck
            passed_eids = list(eg_result.passed_entity_ids)
            travel_start = date.fromisoformat(start_str)
            travel_dates_list = [travel_start + timedelta(days=i)
                                 for i in range(case["duration_days"])]
            pc_result = await run_precheck_gate(session, passed_eids, travel_dates_list)

            try:
                ranking_result = await rank_major_activities(
                    session=session,
                    circle_id=circle_id,
                    profile=profile,
                    passed_cluster_ids=eg_result.passed_cluster_ids,
                    precheck_failed_entity_ids=pc_result.failed_ids,
                    constraints=constraints,
                )
                cr.steps.append(score_e3_ranking(ranking_result, case))
            except Exception as exc:
                cr.steps.append(StepResult(step="E3", name="主活动排序", error=str(exc)))
                ranking_result = None

            if ranking_result is None or len(ranking_result.selected_majors) == 0:
                for step_id, step_name in [("E4", "酒店策略"), ("E5", "骨架构建"),
                                           ("E6", "时间线填充"), ("E7", "质量门控"),
                                           ("E8", "离线评测")]:
                    cr.steps.append(StepResult(step=step_id, name=step_name,
                                              error="无主活动，跳过"))
                return cr

            # ── E4: 酒店策略 ──
            from app.domains.planning.hotel_base_builder import build_hotel_strategy
            selected_cluster_ids = [m.cluster_id for m in ranking_result.selected_majors]
            try:
                hotel_result = await build_hotel_strategy(
                    session=session,
                    circle_id=circle_id,
                    profile=profile,
                    selected_cluster_ids=selected_cluster_ids,
                    resolved_policy=resolved_policy,
                    constraints=constraints,
                )
                cr.steps.append(score_e4_hotel(hotel_result, case))
            except Exception as exc:
                cr.steps.append(StepResult(step="E4", name="酒店策略", error=str(exc)))
                hotel_result = None

            # ── E5: 骨架构建 ──
            from app.domains.planning.route_skeleton_builder import build_route_skeleton
            try:
                skeleton = build_route_skeleton(
                    duration_days=case["duration_days"],
                    selected_majors=ranking_result.selected_majors,
                    hotel_bases=hotel_result.bases if hotel_result else [],
                    pace=case["pace"],
                    wake_up_time="normal",
                    constraints=constraints,
                    resolved_policy=resolved_policy,
                )
                cr.steps.append(score_e5_skeleton(skeleton, case))
            except Exception as exc:
                cr.steps.append(StepResult(step="E5", name="骨架构建", error=str(exc)))
                skeleton = None

            if skeleton is None:
                for step_id, step_name in [("E6", "时间线填充"),
                                           ("E7", "质量门控"), ("E8", "离线评测")]:
                    cr.steps.append(StepResult(step=step_id, name=step_name,
                                              error="骨架失败，跳过"))
                return cr

            # ── E6: 时间线填充 ──
            # 构建候选池（与 generate_trip.py 逻辑一致）
            from app.db.models.city_circles import CircleEntityRole
            from app.db.models.catalog import EntityBase, Poi, Restaurant

            role_q = await session.execute(
                select(CircleEntityRole, EntityBase).join(
                    EntityBase, CircleEntityRole.entity_id == EntityBase.entity_id
                ).where(
                    CircleEntityRole.circle_id == circle_id,
                    CircleEntityRole.entity_id.in_(eg_result.passed_entity_ids),
                    EntityBase.entity_type.in_(["poi", "activity"]),
                )
            )
            candidate_pool = []
            _seen_ids = set()
            for role, ent in role_q.all():
                _seen_ids.add(ent.entity_id)
                candidate_pool.append({
                    "entity_id": str(ent.entity_id),
                    "name_zh": ent.name_zh,
                    "entity_type": ent.entity_type,
                    "city_code": ent.city_code,
                    "lat": float(ent.lat) if ent.lat else None,
                    "lng": float(ent.lng) if ent.lng else None,
                    "area_name": ent.area_name,
                    "corridor_tags": ent.corridor_tags or [],
                    "final_score": float(ent.google_rating) * 20 if getattr(ent, "google_rating", None) else 50.0,
                    "sub_category": getattr(ent, "sub_category", None),
                    "typical_duration_min": getattr(ent, "typical_duration_min", 60),
                })

            # 补充 POI
            _circle_cities = set(all_cities)
            if len(candidate_pool) < 20 and _circle_cities:
                _extra_q = await session.execute(
                    select(EntityBase, Poi).join(
                        Poi, Poi.entity_id == EntityBase.entity_id
                    ).where(
                        EntityBase.entity_type == "poi",
                        EntityBase.is_active == True,
                        EntityBase.city_code.in_(list(_circle_cities)),
                        EntityBase.entity_id.notin_(list(_seen_ids)) if _seen_ids else True,
                    ).order_by(Poi.google_rating.desc().nullslast())
                    .limit(100)
                )
                for ent, poi in _extra_q.all():
                    candidate_pool.append({
                        "entity_id": str(ent.entity_id),
                        "name_zh": ent.name_zh,
                        "entity_type": ent.entity_type,
                        "city_code": ent.city_code,
                        "lat": float(ent.lat) if ent.lat else None,
                        "lng": float(ent.lng) if ent.lng else None,
                        "final_score": float(poi.google_rating) * 20 if poi.google_rating else 50.0,
                        "sub_category": poi.poi_category,
                        "typical_duration_min": poi.typical_duration_min or 60,
                    })

            # 餐厅候选池
            rest_q = await session.execute(
                select(EntityBase, Restaurant).join(
                    Restaurant, Restaurant.entity_id == EntityBase.entity_id
                ).where(
                    EntityBase.entity_type == "restaurant",
                    EntityBase.is_active == True,
                    EntityBase.city_code.in_(list(_circle_cities)),
                ).order_by(Restaurant.tabelog_score.desc().nullslast())
                .limit(100)
            )
            restaurant_pool = []
            for ent, rest in rest_q.all():
                restaurant_pool.append({
                    "entity_id": str(ent.entity_id),
                    "name_zh": ent.name_zh,
                    "entity_type": "restaurant",
                    "city_code": ent.city_code,
                    "lat": float(ent.lat) if ent.lat else None,
                    "lng": float(ent.lng) if ent.lng else None,
                    "tabelog_score": float(rest.tabelog_score) if rest.tabelog_score else None,
                    "final_score": (float(rest.tabelog_score) if rest.tabelog_score else 3.5) * 20,
                })

            # 调用 timeline_filler
            from app.domains.planning.timeline_filler import fill_and_write_timeline
            from app.db.models.derived import ItineraryPlan, ItineraryDay, ItineraryItem

            plan = ItineraryPlan(trip_request_id=trip_id, status="draft")
            session.add(plan)
            await session.flush()
            plan_id = plan.plan_id

            profile_dict = {
                "party_type": case["party_type"],
                "pace": case["pace"],
                "budget_level": case["budget_level"],
                "travel_month": travel_month,
            }

            try:
                tl_result = await fill_and_write_timeline(
                    session=session,
                    plan_id=plan_id,
                    frames=skeleton.frames,
                    poi_pool=candidate_pool,
                    restaurant_pool=restaurant_pool,
                    profile=profile_dict,
                    ranking_result=ranking_result,
                    hotel_result=hotel_result,
                )
                await session.flush()

                # 读回时间线结果
                days_q = await session.execute(
                    select(ItineraryDay).where(ItineraryDay.plan_id == plan_id)
                    .order_by(ItineraryDay.day_number)
                )
                days = days_q.scalars().all()

                timelines = []
                for day in days:
                    items_q = await session.execute(
                        select(ItineraryItem).where(ItineraryItem.day_id == day.day_id)
                        .order_by(ItineraryItem.sort_order)
                    )
                    items = items_q.scalars().all()

                    # 查实体名称
                    item_dicts = []
                    for it in items:
                        name = "unknown"
                        if it.entity_id:
                            ent = await session.get(EntityBase, it.entity_id)
                            if ent:
                                name = ent.name_zh or ent.name_en or "unknown"
                        item_dicts.append({
                            "name": name,
                            "type": it.item_type or "poi",
                            "start": it.start_time or "??:??",
                            "end": it.end_time or "??:??",
                            "slot": _guess_slot(it.start_time),
                            "duration": it.duration_min or 0,
                        })

                    # 推断 day_type
                    frame = skeleton.frames[day.day_number - 1] if day.day_number <= len(skeleton.frames) else None
                    day_type = frame.day_type if frame else "normal"

                    timelines.append({
                        "day_index": day.day_number,
                        "day_type": day_type,
                        "city": day.city_code or "unknown",
                        "item_count": len(items),
                        "items": item_dicts,
                    })

                cr.steps.append(score_e6_timeline(timelines, case))
            except Exception as exc:
                cr.steps.append(StepResult(step="E6", name="时间线填充", error=str(exc)))
                timelines = []

            # ── E7: 质量门控 ──
            try:
                from app.core.quality_gate import run_quality_gate
                plan_json = await _build_plan_json_for_gate(session, plan_id)
                gate_result = await run_quality_gate(plan_json, db=session)
                cr.steps.append(score_e7_quality_gate(gate_result, case))
            except Exception as exc:
                cr.steps.append(StepResult(step="E7", name="质量门控", error=str(exc)))

            # ── E8: 离线评测 ──
            try:
                from app.domains.evaluation.offline_eval import score_plan, EvalCase
                plan_json_eval = await _build_plan_json_for_gate(session, plan_id)
                eval_case = EvalCase(
                    case_id=f"test_{case['case_id']}",
                    description=case["label"],
                    user_profile={"party_type": case["party_type"]},
                    expected_constraints={"min_days": 1, "max_days": 30},
                    plan_json=plan_json_eval,
                )
                eval_result = score_plan(plan_json_eval, eval_case)
                cr.steps.append(score_e8_eval(eval_result, case))
            except Exception as exc:
                cr.steps.append(StepResult(step="E8", name="离线评测", error=str(exc)))

        finally:
            # 回滚所有临时数据
            await session.rollback()

    return cr


async def __import_city_circle():
    from app.db.models.city_circles import CityCircle
    return CityCircle


def _guess_slot(start_time: Optional[str]) -> str:
    """从 start_time 推断 slot 类型"""
    if not start_time:
        return "unknown"
    try:
        h, m = start_time.split(":")
        minutes = int(h) * 60 + int(m)
    except Exception:
        return "unknown"
    if minutes < 11 * 60 + 30:
        return "morning_core"
    if minutes < 12 * 60 + 30:
        return "lunch"
    if minutes < 15 * 60:
        return "afternoon_easy"
    if minutes < 17 * 60 + 30:
        return "afternoon_light"
    if minutes < 19 * 60:
        return "dinner"
    return "evening"


async def _build_plan_json_for_gate(session, plan_id) -> dict:
    """构建 quality_gate / offline_eval 需要的 plan_json 格式"""
    from sqlalchemy import select
    from app.db.models.derived import ItineraryDay, ItineraryItem
    from app.db.models.catalog import EntityBase

    days_q = await session.execute(
        select(ItineraryDay).where(ItineraryDay.plan_id == plan_id)
        .order_by(ItineraryDay.day_number)
    )
    days = days_q.scalars().all()

    plan_days = []
    for day in days:
        items_q = await session.execute(
            select(ItineraryItem).where(ItineraryItem.day_id == day.day_id)
            .order_by(ItineraryItem.sort_order)
        )
        items = items_q.scalars().all()

        day_items = []
        for item in items:
            entity_name = "unknown"
            entity_type = item.item_type or "poi"
            if item.entity_id:
                entity = await session.get(EntityBase, item.entity_id)
                if entity:
                    entity_name = entity.name_zh or entity.name_en or "unknown"
                    entity_type = entity.entity_type or "poi"

            day_items.append({
                "time": item.start_time or "",
                "name": entity_name,
                "entity_type": entity_type,
                "item_type": entity_type,
                "entity_id": str(item.entity_id) if item.entity_id else None,
                "entity_name": entity_name,
                "start_time": item.start_time or "",
                "end_time": item.end_time or "",
                "duration_min": item.duration_min or 60,
                "copy_zh": "",
            })

        plan_days.append({
            "day_number": day.day_number,
            "city": day.city_code or "",
            "theme": day.day_theme or "",
            "day_theme": day.day_theme or "",
            "items": day_items,
        })

    return {"plan_id": str(plan_id), "days": plan_days}


# ═══════════════════════════════════════════════════════════════════════════════
# 输出格式化
# ═══════════════════════════════════════════════════════════════════════════════

def print_case_result(cr: CaseResult) -> None:
    """格式化输出单个用例的全链路结果"""
    bar = "=" * 60
    print(f"\n{bar}")
    print(f"  {cr.case_id}: {cr.label}")
    print(f"  总分: {cr.total_score:.1f}/{cr.max_total:.1f}  [{cr.status}]")
    print(bar)

    for s in cr.steps:
        if s.error:
            print(f"\n-- {s.step} {s.name} {'─' * (40 - len(s.name))} ERROR")
            print(f"  {s.error}")
            continue

        score_str = f"{s.score:.1f}/{s.max_score:.0f}"
        print(f"\n-- {s.step} {s.name} {'─' * (40 - len(s.name))} {score_str}")

        if s.inputs:
            print(f"  IN:  {s.inputs}")
        if s.outputs:
            print(f"  OUT: {s.outputs}")

        for d in s.details:
            print(f"  {d}")

        for ded in s.deductions:
            print(f"  [!] {ded}")


def print_summary(results: list[CaseResult]) -> None:
    """输出汇总表"""
    print("\n" + "=" * 80)
    print("  汇总")
    print("=" * 80)

    # 表头
    steps = ["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"]
    header = f"{'用例':<8s}"
    for st in steps:
        header += f" {st:>4s}"
    header += f" {'总分':>6s}  状态"
    print(header)
    print("-" * 65)

    for cr in results:
        row = f"{cr.case_id:<8s}"
        step_map = {s.step: s for s in cr.steps}
        for st in steps:
            s = step_map.get(st)
            if s and not s.error:
                row += f" {s.score:4.1f}"
            else:
                row += f"   --"
        row += f" {cr.total_score:5.1f}/{cr.max_total:.0f}  {cr.status}"
        print(row)

    print("-" * 65)
    passed = sum(1 for cr in results if cr.status == "PASS")
    warned = sum(1 for cr in results if cr.status == "WARN")
    failed = sum(1 for cr in results if cr.status == "FAIL")
    print(f"PASS={passed}  WARN={warned}  FAIL={failed}  TOTAL={len(results)}")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    # 解析命令行参数
    requested_ids = set()
    for arg in sys.argv[1:]:
        if not arg.startswith("-"):
            requested_ids.add(arg.upper())

    cases = HOKKAIDO_CASES
    if requested_ids:
        cases = [c for c in cases if c["case_id"] in requested_ids]
        if not cases:
            print(f"未找到用例: {requested_ids}")
            print(f"可用: {[c['case_id'] for c in HOKKAIDO_CASES]}")
            sys.exit(1)

    print(f"Running {len(cases)} test case(s)...")
    results: list[CaseResult] = []

    for case in cases:
        print(f"\n>>> {case['case_id']}: {case['label']}...")
        try:
            cr = await run_one_case(case)
        except Exception as exc:
            cr = CaseResult(case_id=case["case_id"], label=case["label"])
            cr.steps.append(StepResult(step="E0", name="FATAL", error=str(exc)))
        results.append(cr)
        print_case_result(cr)

    if len(results) > 1:
        print_summary(results)

    # 退出码
    any_fail = any(cr.status == "FAIL" for cr in results)
    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    asyncio.run(main())
