"""
run_regression.py — 回归测试：跑 3 个用例，输出 1 份合并 PDF

用例：标准型 / 约束型 / 边界型
每个用例独立跑 Phase 2-3（决策+DB），最后合并渲染一份 PDF。
"""
import asyncio
import json
import sys
import uuid
import time
import logging
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logger = logging.getLogger("regression")

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.core.config import settings
from scripts.test_cases import ALL_CASES


async def run_one_case(case: dict, session) -> dict:
    """运行单个用例的 Phase 2（决策链），返回骨架+餐厅数据。
    不写 DB，只返回内存数据供 PDF 渲染。"""

    case_id = case["case_id"]
    logger.info("━━━ 用例: %s ━━━", case["case_label"])

    # 2a. 构造 TripProfile
    from app.db.models.business import TripProfile
    profile = TripProfile(
        trip_request_id=uuid.uuid4(),
        duration_days=case["duration_days"],
        cities=case["cities"],
        party_type=case["party_type"],
        budget_level=case["budget_level"],
        arrival_airport=case.get("arrival_airport", "KIX"),
        departure_airport=case.get("departure_airport", "KIX"),
        arrival_shape=case.get("arrival_shape", "same_city"),
        pace=case.get("pace", "moderate"),
        must_have_tags=case.get("must_have_tags", []),
        avoid_tags=case.get("avoid_tags", []),
        daytrip_tolerance=case.get("daytrip_tolerance", "medium"),
        hotel_switch_tolerance=case.get("hotel_switch_tolerance", "medium"),
        travel_dates=case.get("travel_dates"),
    )
    # 扩展字段：constraint_compiler 会通过 getattr 读取
    if case.get("arrival_time"):
        profile.arrival_time = case["arrival_time"]
    if case.get("blocked_clusters"):
        profile.blocked_clusters = case["blocked_clusters"]
    if case.get("blocked_pois"):
        profile.blocked_pois = case["blocked_pois"]
    if case.get("must_stay_area"):
        profile.must_stay_area = case["must_stay_area"]
    if case.get("departure_day_shape"):
        profile.departure_day_shape = case["departure_day_shape"]

    # 2b. 编译约束
    constraints = compile_constraints(profile)
    logger.info("  约束编译 v%s [%s]: %d trace items",
                constraints.compiler_version, constraints.run_id,
                len(constraints.constraint_trace))
    for line in constraints.trace_summary():
        logger.info("    ├ %s", line)

    # 2c. 城市圈
    from app.domains.planning.city_circle_selector import select_city_circle
    circle_result = await select_city_circle(session, profile)
    circle_id = circle_result.selected_circle_id
    logger.info("  城市圈: %s", circle_id)

    # 2c. 活动簇
    try:
        from app.domains.planning.eligibility_gate import run_eligibility_gate
        elig = await run_eligibility_gate(session, circle_id, profile)
        passed_ids = elig.passed_cluster_ids
    except Exception:
        from app.db.models.city_circles import ActivityCluster
        q = await session.execute(
            select(ActivityCluster.cluster_id)
            .where(ActivityCluster.circle_id == circle_id)
        )
        passed_ids = {r[0] for r in q.fetchall()}
    logger.info("  活动簇: %d 个通过", len(passed_ids))

    # 2d. 排序（constraints-aware）
    from app.domains.planning.major_activity_ranker import rank_major_activities
    ranking = await rank_major_activities(
        session, circle_id, profile, passed_ids,
        constraints=constraints,
    )
    logger.info("  主要活动: %d 个", len(ranking.selected_majors))

    # 2e. 酒店
    from app.domains.planning.hotel_base_builder import build_hotel_strategy
    hotel = await build_hotel_strategy(
        session, circle_id, profile,
        selected_cluster_ids=[m.cluster_id for m in ranking.selected_majors],
    )
    logger.info("  酒店: %s (%d晚)", hotel.preset_name, hotel.total_nights)

    # 2f. 骨架（constraints-aware）
    from app.domains.planning.route_skeleton_builder import build_route_skeleton
    skeleton = build_route_skeleton(
        duration_days=profile.duration_days,
        selected_majors=ranking.selected_majors,
        hotel_bases=hotel.bases,
        pace=profile.pace or "moderate",
        constraints=constraints,
    )
    logger.info("  骨架: %d 天", len(skeleton.frames))

    # 2f2. day_mode 推导（vibe lock）
    from app.domains.planning.day_mode import infer_all_day_modes
    profile_tags = set(t.lower() for t in (profile.must_have_tags or []))
    profile_tags |= set(t.lower() for t in (getattr(profile, "nice_to_have_tags", None) or []))
    day_modes = infer_all_day_modes(
        frames=skeleton.frames,
        constraints=constraints,
        profile_tags=profile_tags,
        party_type=profile.party_type or "couple",
    )
    # 注入 day_mode 到 DayFrame
    for frame, mode in zip(skeleton.frames, day_modes):
        frame.day_mode = mode.mode
        frame.day_mode_boosted = sorted(mode.boosted_tags)
        frame.day_mode_suppressed = sorted(mode.suppressed_tags)
    for mode in day_modes:
        logger.info("  Day%d mode=%s (boosted=%s, suppressed=%s)",
                     mode.day_index, mode.mode,
                     sorted(mode.boosted_tags)[:4],
                     sorted(mode.suppressed_tags)[:4])

    # 2f3. micro-route 候选生成
    from app.domains.planning.micro_route_builder import (
        build_micro_route_candidates, select_best_micro_route,
    )
    micro_route_pools = {}
    # 只追踪 micro-route 选择的去重，不排除已选 majors（majors 作为当天 driver 是合理的）
    used_micro_clusters: set[str] = set()
    for frame, mode in zip(skeleton.frames, day_modes):
        pool = build_micro_route_candidates(
            all_ranked=ranking.all_ranked,
            constraints=constraints,
            day_type=frame.day_type,
            corridor=frame.primary_corridor,
            party_type=profile.party_type or "couple",
            intensity_cap=frame.intensity,
            day_index=frame.day_index,
        )
        # 选最佳 micro-route
        best = select_best_micro_route(
            pool,
            day_mode=mode.mode,
            mode_boosted_tags=mode.boosted_tags,
            mode_suppressed_tags=mode.suppressed_tags,
            already_used_clusters=used_micro_clusters,
        )
        if best:
            used_micro_clusters.add(best.primary_cluster_id)
        micro_route_pools[frame.day_index] = pool
    logger.info("  micro-routes: %d 天有候选",
                sum(1 for p in micro_route_pools.values() if p.routes))

    # 2g. 餐厅填充
    from app.domains.planning.meal_flex_filler import fill_meals
    from app.db.models.catalog import EntityBase
    rest_q = await session.execute(
        select(EntityBase)
        .where(EntityBase.entity_type == "restaurant", EntityBase.is_active == True)
    )
    rest_pool = []
    for e in rest_q.scalars().all():
        rest_pool.append({
            "entity_id": str(e.entity_id),
            "entity_type": e.entity_type,
            "name_zh": e.name_zh, "name_en": e.name_en,
            "city_code": e.city_code, "area_name": e.area_name,
            "corridor_tags": e.corridor_tags or [],
            "cuisine_type": "other",
            "data_tier": e.data_tier, "is_active": True,
            "price_range_min_jpy": 800,
            "price_range_max_jpy": 5000,
        })

    meal_fills = fill_meals(
        frames=skeleton.frames,
        restaurant_pool=rest_pool,
        trip_profile={
            "budget_level": profile.budget_level,
            "party_type": profile.party_type,
            "avoid_list": profile.avoid_tags or [],
        },
        constraints=constraints,
    )
    for mf in meal_fills:
        names = [
            m.restaurant.get("name", "?")
            if isinstance(m.restaurant, dict) else "?"
            for m in mf.meals
        ]
        logger.info("  Day %d 餐: %s", mf.day_index, ", ".join(names))

    # finalize trace
    constraints.finalize_trace()

    # 2h. fusion patch（deterministic 版）
    from app.domains.planning.fusion_patch import (
        run_deterministic_fusion, verify_fusion_constraints,
        build_fusion_trace_events,
    )

    # 组装返回数据（含 evidence_bundle）
    cd = _build_case_data(case, profile, skeleton, hotel, meal_fills, ranking)

    fusion_result = run_deterministic_fusion(cd, day_modes, constraints)
    if fusion_result.patches:
        # 验证 patch 后仍满足硬约束
        ok, violations = verify_fusion_constraints(cd, constraints)
        if not ok:
            fusion_result.applied = False
            fusion_result.rejected_reason = f"constraint violations: {violations}"
            logger.warning("  fusion patch rejected: %s", violations)

    cd["run_id"] = constraints.run_id
    cd["evidence_bundle"] = constraints.to_evidence_dict(
        plan_id=cd.get("run_id", ""),
        request_id=case["case_id"],
        key_decisions=cd.get("profile_summary", {}).get("key_decisions", []),
    )

    # 追加 day_mode + micro_route + fusion trace 到 evidence_bundle
    fusion_events = build_fusion_trace_events(fusion_result, day_modes)
    cd["evidence_bundle"]["quality_trace"] = fusion_events
    cd["evidence_bundle"]["day_modes"] = [
        {"day": m.day_index, "mode": m.mode, "reason": m.reason}
        for m in day_modes
    ]
    cd["evidence_bundle"]["micro_routes_selected"] = [
        {
            "day": di,
            "route_id": p.selected_route.route_id if p.selected_route else None,
            "primary": p.selected_route.primary_name if p.selected_route else None,
            "corridor": p.selected_route.corridor if p.selected_route else None,
            "vibe_tags": sorted(p.selected_route.vibe_tags)[:5] if p.selected_route else [],
        }
        for di, p in micro_route_pools.items()
    ]
    cd["evidence_bundle"]["fusion_result"] = {
        "applied": fusion_result.applied,
        "patch_count": len(fusion_result.patches),
        "rejected_reason": fusion_result.rejected_reason,
    }

    # 存储 day_modes 供断言使用
    cd["day_modes"] = [
        {"day": m.day_index, "mode": m.mode,
         "boosted": sorted(m.boosted_tags), "suppressed": sorted(m.suppressed_tags)}
        for m in day_modes
    ]

    return cd


# -- display_registry import (single source of truth) --

from app.domains.planning.display_registry import (
    CORRIDOR_ZH as _CZH,
    CITY_ZH as _CITY_ZH,
    AREA_ZH as _AREA_ZH,
    CUISINE_ZH as _CUISINE_ZH,
    DAY_TYPE_ZH as _DAY_TYPE_ZH,
    INTENSITY_ZH as _INTENSITY_ZH,
    MEAL_ZH as _MEAL_ZH,
    RAW_KEY_BLACKLIST,
    sanitize as _san,
    display_corridor as _corr_zh,
    display_city as _city_zh,
    display_area as _area_zh,
)
from app.domains.planning.constraint_compiler import compile_constraints



# ── 数据组装 ────────────────────────────────────────────────────────────────────

def _build_case_data(case, profile, skeleton, hotel, meal_fills, ranking):
    """把骨架+餐厅数据组装成 PDF 可消费的 dict（与 export_plan_pdf 格式对齐）"""

    meal_by_day = {mf.day_index: mf for mf in meal_fills}
    hotel_bases_meta = [
        {"city": b.base_city, "area": b.area, "nights": b.nights}
        for b in hotel.bases
    ]
    actual_cities = []
    for b in hotel.bases:
        if b.base_city not in actual_cities:
            actual_cities.append(b.base_city)

    day_data = []
    for frame in skeleton.frames:
        items = []

        # 主活动
        for m in ranking.selected_majors:
            if m.cluster_id == frame.main_driver:
                items.append({
                    "name": m.name_zh,
                    "type": "poi",
                    "is_main": True,
                    "corridor": frame.primary_corridor or "",
                    "corridor_display": _corr_zh(frame.primary_corridor),
                    "area_display": _san(m.name_zh),
                    "copy": "",
                    "tips": "",
                    "why_here": "",
                    "serving_area": "",
                    "cuisine": "",
                    "meal_type": "",
                    "placeholder": False,
                })
                break

        # 餐厅
        mf = meal_by_day.get(frame.day_index)
        if mf:
            for meal in mf.meals:
                r = meal.restaurant if isinstance(meal.restaurant, dict) else {}
                items.append({
                    "name": r.get("name", ""),
                    "type": "restaurant",
                    "is_main": False,
                    "meal_type": meal.meal_type,
                    "corridor": r.get("serving_corridor", ""),
                    "corridor_display": _corr_zh(r.get("serving_corridor", "")),
                    "area_display": _san(r.get("area_name", "")),
                    "serving_area": _san(_corr_zh(r.get("serving_corridor", ""))),
                    "cuisine": r.get("cuisine_type", ""),
                    "why_here": _san(r.get("why_here", "")),
                    "copy": "",
                    "tips": "",
                    "placeholder": False,
                })

        corr_raw = frame.primary_corridor or ""
        day_data.append({
            "day_number": frame.day_index,
            "city_raw": frame.sleep_base,
            "city": _city_zh(frame.sleep_base),
            "theme": frame.title_hint or f"Day {frame.day_index}",
            "day_type_raw": frame.day_type,
            "day_type": _DAY_TYPE_ZH.get(frame.day_type, frame.day_type),
            "corridor_raw": corr_raw,
            "corridor": _corr_zh(corr_raw),
            "intensity_raw": frame.intensity,
            "intensity": _INTENSITY_ZH.get(frame.intensity, frame.intensity),
            "day_mode": frame.day_mode or "",
            "items": items,
        })

    dates = case.get("travel_dates", {})

    actual_hotel_areas = {b.area for b in hotel.bases if b.area}
    actual_hotel_cities = {b.base_city for b in hotel.bases if b.base_city}

    # ── key_decisions：100% 从执行结果生成，不使用 case 输入 ────────────────
    gen_decisions = _generate_decisions_from_execution(
        day_data, ranking, hotel, actual_hotel_cities, actual_hotel_areas,
        skeleton, meal_fills,
    )

    # profile_summary: 保留 case 中的 travel_portrait / hard_constraints / care_about
    # 但 key_decisions 完全替换为执行结果生成版
    raw_ps = dict(case.get("profile_summary", {}))
    raw_ps["key_decisions"] = gen_decisions

    return {
        "case": case,
        "plan_meta": {
            "hotel_bases": hotel_bases_meta,
            "actual_cities": actual_cities,
            "hotel_cities": list(actual_hotel_cities),
            "hotel_areas": list(actual_hotel_areas),
            "hotel_strategy": hotel.preset_name,
        },
        "profile_summary": raw_ps,
        "days": day_data,
        "dates": dates,
    }


def _generate_decisions_from_execution(
    day_data, ranking, hotel, actual_hotel_cities, actual_hotel_areas,
    skeleton, meal_fills,
) -> list[str]:
    """从执行结果反推 key_decisions — 不使用任何人工编写的文案。"""
    decisions = []

    # 1. 住宿决策
    hotel_parts = []
    for b in hotel.bases:
        city_zh = _city_zh(b.base_city)
        area_zh = _area_zh(b.area) if b.area else city_zh
        hotel_parts.append(f"{area_zh}{b.nights}晚")
    decisions.append(f"住宿策略: {' + '.join(hotel_parts)}")

    # 2. 主要活动排列
    for m in ranking.selected_majors:
        # 找到该 major 分配到的 day
        assigned_day = None
        for d in day_data:
            for item in d.get("items", []):
                if item.get("is_main") and item.get("name") == m.name_zh:
                    assigned_day = d["day_number"]
                    break
        if assigned_day:
            decisions.append(f"Day{assigned_day}: {_san(m.name_zh)}")

    # 3. 特殊 day_type 记录
    for d in day_data:
        dt = d.get("day_type_raw", "")
        dn = d["day_number"]
        if dt == "arrival":
            meal_count = sum(1 for i in d.get("items", []) if i.get("type") == "restaurant")
            decisions.append(f"Day{dn}(到达日): {meal_count}餐, 走廊={d.get('corridor','')}")
        elif dt == "departure":
            meal_count = sum(1 for i in d.get("items", []) if i.get("type") == "restaurant")
            poi_count = sum(1 for i in d.get("items", []) if i.get("type") == "poi")
            decisions.append(f"Day{dn}(返程日): {poi_count}景点, {meal_count}餐")
        elif dt == "theme_park":
            decisions.append(f"Day{dn}: 主题公园整天 ({d.get('corridor', '')})")

    # 4. 约束兑现记录
    decisions.append(f"节奏上限: {skeleton.frames[0].intensity if skeleton.frames else '?'}")

    return decisions


# ── 走廊→城市映射（用于 meal corridor consistency 检查）────────────────────────

_CORR_TO_CITY = {
    # 京都（全部 25 bare keys 中属于京都的）
    "arashiyama": "kyoto", "daigo": "kyoto", "fushimi": "kyoto",
    "gion": "kyoto", "gosho": "kyoto", "higashiyama": "kyoto",
    "kawaramachi": "kyoto", "kinugasa": "kyoto", "kita_ku": "kyoto",
    "nijo": "kyoto", "nishikyo": "kyoto", "okazaki": "kyoto",
    "philosopher_path": "kyoto", "zen_garden": "kyoto", "uji": "kyoto",
    # 大阪
    "namba": "osaka", "osakajo": "osaka", "sakurajima": "osaka",
    "shinsekai": "osaka", "osa_nakanoshima": "osaka", "tsuruhashi": "osaka",
    "umeda": "osaka",
    # 奈良 / 神户 / 滋贺
    "nara_park": "nara",
    "kobe_kitano": "kobe", "arima": "kobe",
    "shiga": "shiga",
    # 旧前缀别名兜底
    "kyo_fushimi": "kyoto", "kyo_arashiyama": "kyoto", "kyo_higashiyama": "kyoto",
    "kyo_gion": "kyoto", "kyo_kawaramachi": "kyoto", "kyo_okazaki": "kyoto",
    "kyo_nijo": "kyoto", "kyo_zen_garden": "kyoto",
    "kyo_nishikyo": "kyoto", "kyo_kinugasa": "kyoto",
    "osa_namba": "osaka", "osa_osakajo": "osaka",
    "osa_sakurajima": "osaka", "osa_shinsekai": "osaka",
}
_SLEEP_TO_CITY = {
    "kawaramachi": "kyoto", "gion": "kyoto", "kyoto_station": "kyoto",
    "namba": "osaka", "shinsaibashi": "osaka", "umeda": "osaka",
    "kyoto": "kyoto", "osaka": "osaka",
}
_INTENSITY_ORDER = {"light": 0, "relaxed": 0, "balanced": 1, "moderate": 1, "dense": 2}

# ── 断言检查 ────────────────────────────────────────────────────────────────────

def run_assertions(case_data: dict) -> list[dict]:
    """运行用例断言，返回 [{name, passed, detail}]。
    
    覆盖 3 个核心维度：
      1. 关键约束是否落到底（day type / 禁忌 / 节奏）
      2. 报告结构是否和总纲一致（走廊 / theme_park day / arrival-departure）
      3. raw key / 错城市 / 错走廊是否清干净
    """
    asserts = case_data["case"].get("assertions", {})
    days = case_data["days"]
    results = []

    n = len(days)

    # ══════════════════════════════════════════════════════════════════
    # 1. 天数
    # ══════════════════════════════════════════════════════════════════
    if "min_days" in asserts:
        ok = n >= asserts["min_days"]
        results.append({"name": f"天数>={asserts['min_days']}", "passed": ok, "detail": f"实际{n}天"})
    if "max_days" in asserts:
        ok = n <= asserts["max_days"]
        results.append({"name": f"天数<={asserts['max_days']}", "passed": ok, "detail": f"实际{n}天"})

    # ══════════════════════════════════════════════════════════════════
    # 2. 走廊覆盖
    # ══════════════════════════════════════════════════════════════════
    actual_corrs = {d["corridor_raw"] for d in days if d.get("corridor_raw")}
    for c in asserts.get("must_have_corridors", []):
        ok = c in actual_corrs
        results.append({"name": f"包含走廊 {c}", "passed": ok, "detail": f"实际: {actual_corrs}"})

    # ══════════════════════════════════════════════════════════════════
    # 3. arrival / departure day type 白名单
    # ══════════════════════════════════════════════════════════════════
    if "arrival_day_type" in asserts and n > 0:
        d1 = days[0]
        ok = d1["day_type_raw"] == asserts["arrival_day_type"]
        results.append({"name": "Day1 是 arrival 类型", "passed": ok,
                        "detail": f"实际: {d1['day_type_raw']}"})

    if "arrival_day_max_items" in asserts and n > 0:
        d1 = days[0]
        cnt = len(d1["items"])
        ok = cnt <= asserts["arrival_day_max_items"]
        results.append({"name": f"到达日 item<={asserts['arrival_day_max_items']}",
                        "passed": ok, "detail": f"实际{cnt}个"})

    if "departure_day_type" in asserts and n > 0:
        dl = days[-1]
        ok = dl["day_type_raw"] == asserts["departure_day_type"]
        results.append({"name": "最后一天是 departure 类型", "passed": ok,
                        "detail": f"实际: {dl['day_type_raw']}"})

    if "departure_day_intensity_whitelist" in asserts and n > 0:
        dl = days[-1]
        wl = asserts["departure_day_intensity_whitelist"]
        ok = dl["intensity_raw"] in wl
        results.append({"name": f"返程日节奏在 {wl} 内", "passed": ok,
                        "detail": f"实际: {dl['intensity_raw']}"})

    if "departure_day_max_items" in asserts and n > 0:
        dl = days[-1]
        cnt = len(dl["items"])
        ok = cnt <= asserts["departure_day_max_items"]
        results.append({"name": f"返程日 item<={asserts['departure_day_max_items']}",
                        "passed": ok, "detail": f"实际{cnt}个"})

    # ══════════════════════════════════════════════════════════════════
    # 4. theme_park day 必须落成独立天
    # ══════════════════════════════════════════════════════════════════
    if asserts.get("theme_park_day_exists"):
        ok = any(d["day_type_raw"] == "theme_park" for d in days)
        results.append({"name": "含主题公园日(day_type=theme_park)", "passed": ok,
                        "detail": f"day_types: {[d['day_type_raw'] for d in days]}"})

    # ══════════════════════════════════════════════════════════════════
    # 5. 禁忌餐饮（avoid_cuisine_enforced）
    # ══════════════════════════════════════════════════════════════════
    avoid_list = asserts.get("avoid_cuisine_enforced", [])
    if avoid_list:
        found_bad = []
        for d in days:
            for item in d["items"]:
                if item.get("type") != "restaurant":
                    continue
                name = (item.get("name", "") or "").lower()
                cuisine = (item.get("cuisine", "") or "").lower()
                why = (item.get("why_here", "") or "").lower()
                for av in avoid_list:
                    av_l = av.lower()
                    # 检查多种可能的泄露方式
                    zh_map = {"sushi": "寿司", "sashimi": "刺身", "raw": "生鱼"}
                    av_zh = zh_map.get(av_l, "")
                    if (av_l in name or av_l in cuisine or
                        (av_zh and (av_zh in name or av_zh in (item.get("why_here", "") or "")))):
                        found_bad.append(f"Day{d['day_number']}: {item.get('name','')}({av})")
        ok = len(found_bad) == 0
        results.append({
            "name": f"禁忌餐饮 {avoid_list} 未出现",
            "passed": ok,
            "detail": f"违规: {found_bad[:5]}" if found_bad else "通过",
        })

    # ══════════════════════════════════════════════════════════════════
    # 6. 全天最大节奏约束（relaxed 用户不应出现 dense 天）
    # ══════════════════════════════════════════════════════════════════
    if "all_days_max_intensity" in asserts:
        max_allowed = _INTENSITY_ORDER.get(asserts["all_days_max_intensity"], 1)
        bad_days = []
        for d in days:
            actual_level = _INTENSITY_ORDER.get(d["intensity_raw"], 1)
            if actual_level > max_allowed:
                bad_days.append(f"Day{d['day_number']}={d['intensity_raw']}")
        ok = len(bad_days) == 0
        results.append({
            "name": f"节奏不超过 {asserts['all_days_max_intensity']}",
            "passed": ok,
            "detail": f"违规: {bad_days}" if bad_days else "通过",
        })

    # ══════════════════════════════════════════════════════════════════
    # 7. 餐厅城市/走廊一致性（核心！）
    # ══════════════════════════════════════════════════════════════════
    # 无东京餐厅混入
    banned_cities = set(asserts.get("must_not_have_cities_in_meals", []))
    if banned_cities:
        found_bad = []
        tokyo_markers = ["新桥", "银座", "六本木", "涩谷", "新宿", "浅草",
                         "东京站", "日本桥", "赤坂", "原宿", "品川", "新橋",
                         "銀座", "六本木", "渋谷", "新宿", "浅草"]
        for d in days:
            for item in d["items"]:
                if item.get("type") != "restaurant":
                    continue
                name = (item.get("name", "") or "")
                area = (item.get("area_display", "") or "")
                for tm in tokyo_markers:
                    if tm in name or tm in area:
                        found_bad.append(f"Day{d['day_number']}: {name}")
        ok = len(found_bad) == 0
        results.append({
            "name": f"无{banned_cities}餐厅混入",
            "passed": ok,
            "detail": f"违规: {found_bad[:3]}" if found_bad else "通过",
        })

    # 走廊一致性：lunch/dinner 所在城市 == 当天走廊所在城市
    # 注意：breakfast 豁免（早餐在住宿地，可以和当日主走廊不同城市）
    if asserts.get("meal_corridor_consistency"):
        violations = []
        for d in days:
            day_corr = d.get("corridor_raw", "")
            day_city = _CORR_TO_CITY.get(day_corr, _SLEEP_TO_CITY.get(d.get("city_raw", ""), ""))
            for item in d["items"]:
                if item.get("type") != "restaurant":
                    continue
                # breakfast 豁免：天然在住宿周边，不要求与主走廊同城
                if item.get("meal_type") == "breakfast":
                    continue
                meal_corr = item.get("corridor", "")
                meal_city = _CORR_TO_CITY.get(meal_corr, _SLEEP_TO_CITY.get(meal_corr, ""))
                # 如果 meal_city 和 day_city 都有值但不同 → 违规
                if day_city and meal_city and day_city != meal_city:
                    mt = item.get("meal_type", "?")
                    violations.append(
                        f"Day{d['day_number']}({day_corr}/{day_city}) "
                        f"{mt}: {item.get('name','')}({meal_corr}/{meal_city})"
                    )
        ok = len(violations) == 0
        results.append({
            "name": "餐厅走廊一致性(lunch+dinner)",
            "passed": ok,
            "detail": f"违规: {violations[:5]}" if violations else "通过",
        })

    # ══════════════════════════════════════════════════════════════════
    # 8. 拒绝项断言: 某些主题/关键词不应出现在 day frame
    # ══════════════════════════════════════════════════════════════════
    banned_themes = asserts.get("must_not_have_day_themes", [])
    if banned_themes:
        found_banned = []
        for d in days:
            theme = (d.get("theme", "") or "")
            for bt in banned_themes:
                if bt in theme:
                    found_banned.append(f"Day{d['day_number']}: '{theme}' 含 '{bt}'")
            # 也检查 items 的主活动名
            for item in d["items"]:
                if item.get("is_main"):
                    iname = item.get("name", "") or ""
                    for bt in banned_themes:
                        if bt in iname:
                            found_banned.append(f"Day{d['day_number']}: 主活动 '{iname}' 含 '{bt}'")
        ok = len(found_banned) == 0
        results.append({
            "name": f"拒绝项 {banned_themes} 未出现",
            "passed": ok,
            "detail": f"违规: {found_banned[:5]}" if found_banned else "通过",
        })

    # ══════════════════════════════════════════════════════════════════
    # 9. 无 raw key 泄露
    # ══════════════════════════════════════════════════════════════════
    if asserts.get("no_raw_keys_in_pdf"):
        # 完整黑名单：旧前缀 + 纯英文 bare key + 内部字段名
        raw_keys = [
            # 旧前缀（DB 迁移后不应再出现）
            "kyo_gion", "kyo_fushimi", "kyo_higashiyama", "kyo_kawaramachi",
            "kyo_okazaki", "kyo_arashiyama", "kyo_zen_garden", "kyo_nijo",
            "kyo_nishikyo", "kyo_kinugasa", "kyo_uji",
            "osa_namba", "osa_shinsekai", "osa_osakajo", "osa_sakurajima",
            "osa_nakanoshima",
            # 纯英文 bare key（出现在用户可见文本里就是泄露）
            "philosopher_path", "gosho", "daigo", "kita_ku",
            "nishikyo", "kinugasa", "zen_garden", "tsuruhashi", "shiga",
            # 内部字段名
            "cluster_id", "circle_id", "entity_id", "base_id",
            "corridor_raw", "corridor_key",
        ]
        # 扫描所有用户可见展示字段（已经过 _san 净化的那些）
        user_facing_texts = []
        for d in case_data["days"]:
            user_facing_texts.append(d.get("theme", "") or "")
            user_facing_texts.append(d.get("corridor", "") or "")      # 已翻译版
            user_facing_texts.append(d.get("city", "") or "")          # 已翻译版
            for item in d.get("items", []):
                user_facing_texts.append(item.get("name", "") or "")
                user_facing_texts.append(item.get("why_here", "") or "")
                user_facing_texts.append(item.get("corridor_display", "") or "")
                user_facing_texts.append(item.get("serving_area", "") or "")
        leaked = []
        for rk in raw_keys:
            for txt in user_facing_texts:
                if rk in (txt or ""):
                    leaked.append(rk)
                    break
        ok = len(leaked) == 0
        results.append({
            "name": "无 raw key 泄露",
            "passed": ok,
            "detail": f"泄露: {leaked}" if leaked else "通过",
        })

    # ══════════════════════════════════════════════════════════════════
    # 9. departure 日标题白名单
    #    返程日标题不应包含 "夜游" "美食夜" 等不合适的主题
    # ══════════════════════════════════════════════════════════════════
    if asserts.get("departure_day_type") and n > 0:
        dl = days[-1]
        title = dl.get("theme", "") or ""
        blocked_words = ["夜游", "夜市", "美食夜", "night", "nightlife"]
        found = [w for w in blocked_words if w in title.lower()]
        ok = len(found) == 0
        results.append({
            "name": "返程日标题不含不当主题",
            "passed": ok,
            "detail": f"标题: '{title}', 命中: {found}" if found else f"标题: '{title}'",
        })

    # ══════════════════════════════════════════════════════════════════
    # 10. 摘要同源验证
    #     key_decisions 是从执行结果���成的，验证它确实反映了 day_data
    #     （住宿城市、day_type 标记、major 分配必须和 decisions 描述一致）
    # ══════════════════════════════════════════════════════════════════
    ps = case_data.get("profile_summary", {})
    decisions = ps.get("key_decisions", [])
    if decisions and n > 0:
        # 验证：decisions 中提到的 Day{N} 必须存在于 day_data
        issues = []
        for dec in decisions:
            import re
            day_match = re.search(r"Day(\d+)", dec)
            if day_match:
                day_num = int(day_match.group(1))
                if day_num > n:
                    issues.append(f"Day{day_num} 超出实际天数 {n}")
        ok = len(issues) == 0
        results.append({
            "name": "关键决策同源验证",
            "passed": ok,
            "detail": f"问题: {issues}" if issues else "通过",
        })

    # ══════════════════════════════════════════════════════════════════
    # 11. hotel 城市真实性：plan_meta.hotel_cities 必须覆盖指定城市
    # ══════════════════════════════════════════════════════════════════
    must_hotel_cities = asserts.get("must_have_hotel_cities", [])
    if must_hotel_cities:
        actual_hc = set(case_data.get("plan_meta", {}).get("hotel_cities", []))
        missing_hc = [c for c in must_hotel_cities if c not in actual_hc]
        ok = len(missing_hc) == 0
        results.append({
            "name": f"住宿覆盖城市 {must_hotel_cities}",
            "passed": ok,
            "detail": f"实际住宿城市: {sorted(actual_hc)}" + (f", 缺失: {missing_hc}" if missing_hc else ""),
        })

    # ══════════════════════════════════════════════════════════════════
    # 12. 返程日无 POI 类 item（return_direct_to_airport 场景）
    # ══════════════════════════════════════════════════════════════════
    if asserts.get("departure_day_no_poi") and n > 0:
        dl = days[-1]
        poi_items = [item for item in dl.get("items", []) if item.get("type") == "poi" and item.get("is_main")]
        ok = len(poi_items) == 0
        results.append({
            "name": "返程日无主景点(POI)",
            "passed": ok,
            "detail": f"违规: {[i.get('name','') for i in poi_items]}" if poi_items else "通过",
        })

    # ══════════════════════════════════════════════════════════════════
    # 13b. 到达日如果 arrival_evening_only，不应有午餐
    # ══════════════════════════════════════════════════════════════════
    if n > 0 and days[0].get("day_type_raw") == "arrival":
        arrival_items = days[0].get("items", [])
        arrival_lunches = [i for i in arrival_items
                          if i.get("type") == "restaurant" and i.get("meal_type") == "lunch"]
        # 只有当 case 设置了 arrival_time 且 >= 17:00 时才检查
        arrival_time_str = case_data.get("case", {}).get("arrival_time", "")
        if arrival_time_str:
            try:
                hour = int(arrival_time_str.split(":")[0])
                if hour >= 17:
                    ok = len(arrival_lunches) == 0
                    results.append({
                        "name": "晚到到达日无午餐",
                        "passed": ok,
                        "detail": f"午餐数: {len(arrival_lunches)}" + (f" ({[l.get('name','') for l in arrival_lunches]})" if arrival_lunches else ""),
                    })
            except (ValueError, IndexError):
                pass

    # ══════════════════════════════════════════════════════════════════
    # 13c. 返程日只有约束允许的餐次
    # ══════════════════════════════════════════════════════════════════
    if asserts.get("departure_day_no_poi") and n > 0:
        dep_day = days[-1]
        dep_lunches = [i for i in dep_day.get("items", [])
                      if i.get("type") == "restaurant" and i.get("meal_type") == "lunch"]
        dep_dinners = [i for i in dep_day.get("items", [])
                      if i.get("type") == "restaurant" and i.get("meal_type") == "dinner"]
        # 默认 departure_meal_window = "breakfast_only" → 不应有 lunch 或 dinner
        ok = len(dep_lunches) == 0 and len(dep_dinners) == 0
        results.append({
            "name": "返程日无午/晚餐",
            "passed": ok,
            "detail": f"午餐{len(dep_lunches)}个, 晚餐{len(dep_dinners)}个" if not ok else "通过",
        })

    # ══════════════════════════════════════════════════════════════════
    # 13. theme_park 必须有专属标题/页面（不只是 day_type 标记）
    #     如果用例要求 theme_park，正文里必须有对应的走廊/标题
    # ══════════════════════════════════════════════════════════════════
    if asserts.get("theme_park_day_exists"):
        tp_days = [d for d in days if d["day_type_raw"] == "theme_park"]
        if tp_days:
            # 检查这些天的标题/走廊是否真的体现主题公园
            tp_markers = ["USJ", "环球", "universal", "disney", "迪士尼",
                          "theme_park", "sakurajima", "此花"]
            has_proper_title = False
            for td in tp_days:
                title = (td.get("theme", "") or "").lower()
                corridor = (td.get("corridor_raw", "") or "").lower()
                if any(m.lower() in title or m.lower() in corridor for m in tp_markers):
                    has_proper_title = True
                    break
            results.append({
                "name": "主题公园日有专属标题",
                "passed": has_proper_title,
                "detail": f"标题: {[d['theme'] for d in tp_days]}",
            })

    # ══════════════════════════════════════════════════════════════════
    # S1–S4. 同源锁死断言（same-source integrity）
    # ══════════════════════════════════════════════════════════════════
    bundle = case_data.get("evidence_bundle")
    rid = case_data.get("run_id", "")

    # S1: evidence_bundle 存在
    results.append({
        "name": "同源:evidence_bundle存在",
        "passed": bundle is not None,
        "detail": f"run_id={rid[:8]}…" if bundle else "MISSING",
    })

    if bundle:
        trace_items = bundle.get("constraint_trace", [])

        # S2: 无 pending 状态
        pending_items = [t for t in trace_items if t.get("final_status") == "pending"]
        results.append({
            "name": "同源:无pending约束",
            "passed": len(pending_items) == 0,
            "detail": f"pending: {[t['constraint_name'] for t in pending_items]}" if pending_items else "通过",
        })

        # S3: hard constraints 无 unconsumed
        hard_unc = [t for t in trace_items
                    if t.get("strength") == "hard" and t.get("final_status") == "unconsumed"]
        results.append({
            "name": "同源:hard约束无unconsumed",
            "passed": len(hard_unc) == 0,
            "detail": f"unconsumed: {[t['constraint_name'] for t in hard_unc]}" if hard_unc else "通过",
        })

        # S4: run_id 一致性（bundle.run_id == case_data.run_id）
        bundle_rid = bundle.get("run_id", "")
        results.append({
            "name": "同源:run_id一致",
            "passed": bundle_rid == rid,
            "detail": f"bundle={bundle_rid[:8]}… case={rid[:8]}…" if bundle_rid != rid else "通过",
        })

    # ══════════════════════════════════════════════════════════════════
    # Q1. day_mode 存在性: 每天必须有 day_mode
    # ══════════════════════════════════════════════════════════════════
    day_mode_data = case_data.get("day_modes", [])
    if day_mode_data:
        missing_mode = [d for d in day_mode_data if not d.get("mode")]
        results.append({
            "name": "质量:day_mode全覆盖",
            "passed": len(missing_mode) == 0,
            "detail": f"modes={[d['mode'] for d in day_mode_data]}" if not missing_mode
                     else f"缺失: {missing_mode}",
        })

    # ══════════════════════════════════════════════════════════════════
    # Q2. day_vibe_consistency: day_mode 与 title/driver 一致
    # ══════════════════════════════════════════════════════════════════
    if asserts.get("day_vibe_consistency") and day_mode_data:
        # 检查: arrival mode 的天 title 应含"到达"
        # departure mode 的天 title 应含"返程"
        # theme_park mode 的天 title 应含 USJ/环球
        vibe_issues = []
        mode_map_q = {d["day"]: d["mode"] for d in day_mode_data}
        for d in days:
            dn = d["day_number"]
            mode = mode_map_q.get(dn, "")
            title = (d.get("theme", "") or "").lower()
            if mode == "arrival_light" and "到达" not in title:
                vibe_issues.append(f"Day{dn}: mode=arrival_light but title='{d.get('theme','')}'")
            if mode == "departure_light" and "返程" not in title and "收尾" not in title:
                vibe_issues.append(f"Day{dn}: mode=departure_light but title='{d.get('theme','')}'")
            if mode == "theme_park_full":
                tp_kw = ["usj", "环球", "theme_park", "sakurajima", "此花"]
                if not any(k in title for k in tp_kw):
                    vibe_issues.append(f"Day{dn}: mode=theme_park_full but title='{d.get('theme','')}'")
        ok = len(vibe_issues) == 0
        results.append({
            "name": "质量:day_mode与标题一致",
            "passed": ok,
            "detail": f"问题: {vibe_issues[:3]}" if vibe_issues else "通过",
        })

    # ══════════════════════════════════════════════════════════════════
    # Q3. micro_route 覆盖: evidence_bundle 中有 micro_routes_selected
    # ══════════════════════════════════════════════════════════════════
    if bundle and bundle.get("micro_routes_selected"):
        mr_data = bundle["micro_routes_selected"]
        with_route = [r for r in mr_data if r.get("route_id")]
        results.append({
            "name": "质量:micro-route覆盖",
            "passed": len(with_route) > 0,
            "detail": f"{len(with_route)}/{len(mr_data)} 天有 micro-route",
        })

    # ══════════════════════════════════════════════════════════════════
    # Q4. fusion 硬约束仍 0 违规
    # ══════════════════════════════════════════════════════════════════
    if bundle and bundle.get("fusion_result"):
        fr = bundle["fusion_result"]
        results.append({
            "name": "质量:fusion后硬约束0违规",
            "passed": fr.get("rejected_reason", "") == "",
            "detail": f"applied={fr.get('applied')}, patches={fr.get('patch_count', 0)}"
                     + (f", rejected={fr['rejected_reason']}" if fr.get("rejected_reason") else ""),
        })

    return results


# ── PDF 渲染 ────────────────────────────────────────────────────────────────────

def generate_regression_pdf(all_data: list[dict], output_path: str):
    """生成合并 PDF：每个用例一个章节"""
    import os
    from fpdf import FPDF

    # 字体
    font_dir = Path(__file__).parent / "_fonts"
    font_path = None
    noto = font_dir / "NotoSansSC-Regular.ttf"
    if noto.exists():
        font_path = str(noto)
    else:
        for f in [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"]:
            if os.path.exists(f):
                font_path = f
                break

    class RegPDF(FPDF):
        def __init__(self):
            super().__init__()
            if font_path:
                self.add_font("zh", "", font_path, uni=True)
                self.add_font("zh", "B", font_path, uni=True)
                self._zh = "zh"
            else:
                self._zh = "Helvetica"

        def header(self):
            if self.page_no() == 1:
                return
            self.set_font(self._zh, "", 7)
            self.set_text_color(170, 170, 170)
            self.cell(0, 5, "Travel AI · 回归测试报告", align="R", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(220, 220, 220)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(2)

        def footer(self):
            self.set_y(-12)
            self.set_font(self._zh, "", 7)
            self.set_text_color(170, 170, 170)
            self.cell(0, 8, f"— {self.page_no()} —", align="C")

    pdf = RegPDF()
    zh = pdf._zh

    # ═══ 总封面 ═══
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font(zh, "B", 26)
    pdf.set_text_color(35, 35, 35)
    pdf.cell(0, 14, "Travel AI · 回归测试报告", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font(zh, "", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"{len(all_data)} 个用例 · {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font(zh, "", 10)
    for cd in all_data:
        c = cd["case"]
        pdf.cell(0, 7, f"  {c['case_label']} — {c['case_desc']}", align="C", new_x="LMARGIN", new_y="NEXT")

    # 同源标识区
    pdf.ln(8)
    pdf.set_draw_color(180, 180, 180)
    pdf.line(30, pdf.get_y(), 180, pdf.get_y())
    pdf.ln(4)
    pdf.set_font(zh, "B", 10)
    pdf.set_text_color(60, 80, 130)
    pdf.cell(0, 7, "同源标识 (Same-Source IDs)", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font(zh, "", 8)
    pdf.set_text_color(80, 80, 80)
    for cd in all_data:
        rid = cd.get("run_id", "N/A")
        cid = cd["case"]["case_id"]
        pdf.cell(0, 6, f"  {cid:20s}  run_id={rid}", align="L", new_x="LMARGIN", new_y="NEXT")

    # ═══ 总汇总 ═══
    pdf.add_page()
    pdf.set_font(zh, "B", 18)
    pdf.set_text_color(35, 35, 35)
    pdf.cell(0, 12, "断言汇总", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    total_pass = 0
    total_fail = 0
    for cd in all_data:
        asserts = cd.get("_assert_results", [])
        pdf.set_font(zh, "B", 11)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 8, cd["case"]["case_label"], new_x="LMARGIN", new_y="NEXT")
        for a in asserts:
            ok = a["passed"]
            if ok:
                total_pass += 1
                pdf.set_text_color(60, 150, 60)
                mark = "[PASS]"
            else:
                total_fail += 1
                pdf.set_text_color(200, 50, 50)
                mark = "[FAIL]"
            pdf.set_font(zh, "B", 9)
            pdf.cell(18, 6, mark)
            pdf.set_font(zh, "", 9)
            pdf.set_text_color(80, 80, 80)
            detail = f"  {a['detail']}" if a.get("detail") else ""
            pdf.cell(0, 6, f"{a['name']}{detail}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    pdf.ln(4)
    pdf.set_font(zh, "B", 12)
    color = (60, 150, 60) if total_fail == 0 else (200, 50, 50)
    pdf.set_text_color(*color)
    pdf.cell(0, 8, f"总计: {total_pass} PASS / {total_fail} FAIL", new_x="LMARGIN", new_y="NEXT")

    # ═══ 每个用例的详细报告 ═══
    for cd in all_data:
        case = cd["case"]
        ps = cd.get("profile_summary", {})
        days = cd["days"]
        meta = cd.get("plan_meta", {})
        hotel_bases = meta.get("hotel_bases", [])
        actual_cities = meta.get("actual_cities", [])
        dates = cd.get("dates", {})

        total_days = len(days)
        total_nights = total_days - 1
        cities_str = " · ".join(_city_zh(c) for c in actual_cities)

        # ── 用例封面 ──
        pdf.add_page()
        pdf.ln(25)
        pdf.set_font(zh, "B", 22)
        pdf.set_text_color(35, 35, 35)
        pdf.cell(0, 13, case["case_label"], align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        pdf.set_font(zh, "", 11)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 7, case["case_desc"], align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.cell(0, 7, f"{cities_str} · {total_days}天{total_nights}晚", align="C", new_x="LMARGIN", new_y="NEXT")
        if dates:
            pdf.cell(0, 7, f"{dates.get('start','')} — {dates.get('end','')}", align="C", new_x="LMARGIN", new_y="NEXT")

        # ── 用户画像摘要页（核心新增）──
        if ps:
            pdf.add_page()
            pdf.set_font(zh, "B", 18)
            pdf.set_text_color(35, 35, 35)
            pdf.cell(0, 12, "输入摘要 · 用户画像", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)

            # A. 旅行画像
            _section_title(pdf, zh, "A. 这次旅行画像")
            pdf.set_font(zh, "", 10)
            pdf.set_text_color(60, 60, 60)
            pdf.cell(0, 7, ps.get("travel_portrait", ""), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

            # B. 硬约束
            _section_title(pdf, zh, "B. 本次硬约束")
            pdf.set_font(zh, "", 9)
            pdf.set_text_color(60, 60, 60)
            for item in ps.get("hard_constraints", []):
                pdf.cell(6, 6, "·")
                pdf.cell(0, 6, item, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

            # C. 特别在意
            _section_title(pdf, zh, "C. 你特别在意的事")
            pdf.set_font(zh, "", 9)
            pdf.set_text_color(60, 60, 60)
            for item in ps.get("care_about", []):
                pdf.cell(6, 6, "·")
                pdf.cell(0, 6, item, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

            # D. 关键决策
            _section_title(pdf, zh, "D. 系统因此做出的关键决策")
            pdf.set_font(zh, "", 9)
            pdf.set_text_color(60, 60, 60)
            for i, item in enumerate(ps.get("key_decisions", []), 1):
                pdf.cell(8, 6, f"{i}.")
                pdf.cell(0, 6, item, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

            pdf.set_draw_color(200, 200, 200)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(2)
            pdf.set_font(zh, "", 7)
            pdf.set_text_color(160, 160, 160)
            pdf.cell(0, 5, "以上摘要来自用户输入和系统推断，帮助您核对本攻略的生成依据。", new_x="LMARGIN", new_y="NEXT")

        # ── 行程总览表 ──
        pdf.add_page()
        pdf.set_font(zh, "B", 16)
        pdf.set_text_color(35, 35, 35)
        pdf.cell(0, 10, "行程总览", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        pdf.set_font(zh, "B", 8)
        pdf.set_fill_color(245, 245, 245)
        col_w = [14, 20, 58, 48, 22]
        headers = ["天", "城市", "主题", "走廊", "节奏"]
        for i, h in enumerate(headers):
            pdf.cell(col_w[i], 7, h, border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font(zh, "", 7)
        for d in days:
            pdf.set_text_color(50, 50, 50)
            pdf.cell(col_w[0], 6, str(d["day_number"]), border=1, align="C")
            pdf.cell(col_w[1], 6, d["city"], border=1, align="C")
            pdf.cell(col_w[2], 6, d["theme"][:20], border=1)
            pdf.cell(col_w[3], 6, d["corridor"], border=1, align="C")
            pdf.cell(col_w[4], 6, d["intensity"] or "均衡", border=1, align="C")
            pdf.ln()

        # ── 每日详情 ──
        for d in days:
            pdf.add_page()
            pdf.set_font(zh, "B", 18)
            pdf.set_text_color(35, 35, 35)
            pdf.cell(0, 11, f"Day {d['day_number']}", new_x="LMARGIN", new_y="NEXT")

            pdf.set_font(zh, "", 11)
            pdf.set_text_color(70, 70, 70)
            pdf.cell(0, 7, d["theme"], new_x="LMARGIN", new_y="NEXT")

            pdf.ln(2)
            pdf.set_font(zh, "", 7)
            pdf.set_text_color(130, 130, 130)
            info = []
            if d["city"]: info.append(f"城市: {d['city']}")
            if d["corridor"]: info.append(f"走廊: {d['corridor']}")
            if d["day_type"]: info.append(d["day_type"])
            if d["intensity"]: info.append(f"节奏: {d['intensity']}")
            pdf.cell(0, 5, "  ·  ".join(info), new_x="LMARGIN", new_y="NEXT")

            pdf.ln(2)
            pdf.set_draw_color(220, 220, 220)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)

            for item in d["items"]:
                if item.get("placeholder"):
                    continue

                icon_map = {"poi": "景", "restaurant": "食", "hotel": "宿", "activity": "玩"}
                icon = icon_map.get(item.get("type", ""), "·")
                is_main = item.get("is_main", False)

                pdf.set_font(zh, "B", 10)
                if is_main:
                    pdf.set_text_color(200, 80, 30)
                elif item.get("type") == "restaurant":
                    pdf.set_text_color(60, 120, 60)
                else:
                    pdf.set_text_color(50, 50, 50)

                name = item.get("name", "")
                mt = item.get("meal_type", "")
                if mt:
                    ml = _MEAL_ZH.get(mt, mt)
                    name = f"[{ml}] {name}"
                if is_main:
                    name = f"★ {name}"

                pdf.cell(7, 6, f"[{icon}]")
                pdf.cell(0, 6, name, new_x="LMARGIN", new_y="NEXT")

                # 餐厅详情
                if item.get("type") == "restaurant":
                    pdf.set_font(zh, "", 6)
                    pdf.set_text_color(140, 140, 140)
                    pdf.set_x(16)
                    parts = []
                    sa = item.get("serving_area", "")
                    if sa:
                        parts.append(_san(sa))
                    cu = item.get("cuisine", "")
                    if cu and cu != "other":
                        parts.append(_CUISINE_ZH.get(cu, cu))
                    wh = item.get("why_here", "")
                    if wh:
                        parts.append(_san(wh))
                    if parts:
                        pdf.cell(0, 4, " · ".join(parts), new_x="LMARGIN", new_y="NEXT")

                # 景点位置
                elif item.get("corridor_display"):
                    pdf.set_font(zh, "", 6)
                    pdf.set_text_color(140, 140, 140)
                    pdf.set_x(16)
                    pdf.cell(0, 4, _san(item["corridor_display"]), new_x="LMARGIN", new_y="NEXT")

                pdf.ln(1)

    pdf.output(output_path)
    print(f"\n[OK] PDF: {output_path} ({pdf.pages_count} 页)")


def _section_title(pdf, zh, title):
    pdf.set_font(zh, "B", 11)
    pdf.set_text_color(50, 80, 130)
    pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")


# ── 主入口 ──────────────────────────────────────────────────────────────────────

async def main():
    t0 = time.time()
    print("\n" + "=" * 70)
    print("  Travel AI — 回归测试（3 用例）")
    print("=" * 70 + "\n")

    all_data = []

    async with AsyncSessionLocal() as session:
        for case in ALL_CASES:
            try:
                cd = await run_one_case(case, session)
                # 运行断言
                cd["_assert_results"] = run_assertions(cd)
                all_data.append(cd)
                passed = sum(1 for a in cd["_assert_results"] if a["passed"])
                total = len(cd["_assert_results"])
                logger.info("  断言: %d/%d PASS", passed, total)
                for a in cd["_assert_results"]:
                    mark = "PASS" if a["passed"] else "FAIL"
                    logger.info("    [%s] %s  %s", mark, a["name"], a.get("detail", ""))
            except Exception as e:
                logger.error("用例 %s 失败: %s", case["case_id"], e, exc_info=True)
                all_data.append({
                    "case": case,
                    "profile_summary": case.get("profile_summary", {}),
                    "days": [],
                    "plan_meta": {},
                    "dates": case.get("travel_dates", {}),
                    "_assert_results": [{"name": "执行", "passed": False, "detail": str(e)}],
                })

    # 生成时间戳文件名避免被占用锁住
    ts = time.strftime("%H%M%S")
    output = str(Path(__file__).parent / f"regression_report_{ts}.pdf")
    generate_regression_pdf(all_data, output)

    elapsed = time.time() - t0
    total_pass = sum(1 for cd in all_data for a in cd.get("_assert_results", []) if a["passed"])
    total_fail = sum(1 for cd in all_data for a in cd.get("_assert_results", []) if not a["passed"])

    print(f"\n{'=' * 70}")
    print(f"  总计: {total_pass} PASS / {total_fail} FAIL  ({elapsed:.1f}s)")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    asyncio.run(main())
