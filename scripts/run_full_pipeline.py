"""
run_full_pipeline.py — 本地端到端行程生成（Phase 2→3→4）

不依赖 arq worker，直接在本地完整执行：
  Phase 2: 城市圈决策链（纯算法）
  Phase 3: 装配行程骨架 → 写入 DB
  Phase 4: AI 文案生成（调你配置的 API）+ 质量评估
"""
import asyncio
import json
import sys
import uuid
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
# 降低 SQLAlchemy 噪音
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logger = logging.getLogger("pipeline")

from sqlalchemy import select, text
from app.db.session import AsyncSessionLocal
from app.core.config import settings


async def main():
    t0 = time.time()
    print("\n" + "="*70)
    print("  🗾 关西 6 天行程 — 完整管线执行")
    print("  模型: " + settings.ai_model_standard)
    print("="*70 + "\n")

    async with AsyncSessionLocal() as session:

        # ══════════════════════════════════════════════════════════════════
        # Phase 2: 决策链（纯算法，零 API）
        # ══════════════════════════════════════════════════════════════════
        logger.info("═══ Phase 2: 决策链 ═══")

        # 2a. 构造 TripProfile
        from app.db.models.business import TripProfile
        profile = TripProfile(
            trip_request_id=uuid.uuid4(),
            duration_days=6,
            cities=[
                {"city_code": "kyoto", "nights": 3},
                {"city_code": "osaka", "nights": 2},
            ],
            party_type="couple",
            budget_level="mid",
            arrival_airport="KIX",
            departure_airport="KIX",
            arrival_shape="same_city",
            pace="moderate",
            must_have_tags=["culture", "food"],
            avoid_tags=[],
            daytrip_tolerance="medium",
            hotel_switch_tolerance="medium",
            travel_dates={"start": "2026-04-10", "end": "2026-04-15"},
        )

        # 2b. 城市圈选择
        from app.domains.planning.city_circle_selector import select_city_circle
        circle_result = await select_city_circle(session, profile)
        circle_id = circle_result.selected_circle_id
        logger.info("城市圈: %s (score=%.3f)", circle_id, circle_result.selected.total_score)

        # 2c. 活动簇过滤
        try:
            from app.domains.planning.eligibility_gate import run_eligibility_gate
            elig = await run_eligibility_gate(session, circle_id, profile)
            passed_ids = elig.passed_cluster_ids
        except Exception:
            from app.db.models.city_circles import ActivityCluster
            q = await session.execute(
                select(ActivityCluster.cluster_id).where(ActivityCluster.circle_id == circle_id)
            )
            passed_ids = {r[0] for r in q.fetchall()}
        logger.info("活动簇: %d 个通过", len(passed_ids))

        # 2d. 活动排序
        from app.domains.planning.major_activity_ranker import rank_major_activities
        ranking = await rank_major_activities(session, circle_id, profile, passed_ids)
        logger.info("主要活动: %d 个选中", len(ranking.selected_majors))
        for m in ranking.selected_majors:
            logger.info("  🎯 %s [%s] score=%.1f corridor=%s", m.name_zh, m.level, m.major_score, m.primary_corridor)

        # 2e. 酒店策略
        from app.domains.planning.hotel_base_builder import build_hotel_strategy
        hotel = await build_hotel_strategy(
            session, circle_id, profile,
            selected_cluster_ids=[m.cluster_id for m in ranking.selected_majors],
        )
        logger.info("酒店策略: %s (%d晚, %d次换)", hotel.preset_name, hotel.total_nights, hotel.switch_count)

        # 2f. 骨架编排
        from app.domains.planning.route_skeleton_builder import build_route_skeleton
        skeleton = build_route_skeleton(
            duration_days=profile.duration_days,
            selected_majors=ranking.selected_majors,
            hotel_bases=hotel.bases,
            pace=profile.pace or "moderate",
        )
        logger.info("骨架: %d 天编排完成", len(skeleton.frames))

        # 2g. 餐厅填充
        from app.domains.planning.meal_flex_filler import fill_meals
        from app.db.models.catalog import EntityBase
        rest_q = await session.execute(
            select(EntityBase).where(EntityBase.entity_type == "restaurant", EntityBase.is_active == True)
        )
        rest_pool = [
            {
                "entity_id": str(e.entity_id), "entity_type": e.entity_type,
                "name_zh": e.name_zh, "name_en": e.name_en,
                "city_code": e.city_code, "area_name": e.area_name,
                "corridor_tags": e.corridor_tags or [],
                "cuisine_type": "other",
                "data_tier": e.data_tier, "is_active": True,
                "price_range_min_jpy": 800, "price_range_max_jpy": 5000,
            }
            for e in rest_q.scalars().all()
        ]
        logger.info("餐厅池: %d 家", len(rest_pool))

        meal_fills = fill_meals(
            frames=skeleton.frames,
            restaurant_pool=rest_pool,
            trip_profile={
                "budget_level": profile.budget_level,
                "party_type": profile.party_type,
                "avoid_list": profile.avoid_tags or [],
            },
        )
        for mf in meal_fills:
            filled_names = [m.restaurant.get("name", "?") if isinstance(m.restaurant, dict) else "?" for m in mf.meals]
            logger.info("  Day %d 餐厅: %s", mf.day_index, ", ".join(filled_names))

        t_phase2 = time.time() - t0
        logger.info("Phase 2 完成 (%.1fs, 0 API calls)", t_phase2)

        # ══════════════════════════════════════════════════════════════════
        # Phase 3: 写入 DB（创建 plan + days + items）
        # ══════════════════════════════════════════════════════════════════
        logger.info("═══ Phase 3: 写入 DB ═══")

        from app.db.models.derived import ItineraryPlan, ItineraryDay, ItineraryItem

        # 创建 TripRequest 记录（pipeline 需要）
        from app.db.models.business import TripRequest
        trip_request = TripRequest(
            trip_request_id=profile.trip_request_id,
            user_id=None,
            status="generating",
            raw_input={
                "scene": "couple",
                "duration_days": 6,
                "cities": profile.cities,
            },
        )
        session.add(trip_request)

        # 创建 Plan
        plan_id = uuid.uuid4()
        # 构建 hotel_bases metadata
        hotel_bases_meta = []
        for b in hotel.bases:
            hotel_bases_meta.append({
                "city": b.base_city,
                "area": b.area,
                "nights": b.nights,
            })
        # 推导实际城市列表
        actual_cities = []
        for b in hotel.bases:
            if b.base_city not in actual_cities:
                actual_cities.append(b.base_city)

        plan = ItineraryPlan(
            plan_id=plan_id,
            trip_request_id=profile.trip_request_id,
            status="draft",
            plan_metadata={
                "circle_id": circle_id,
                "circle_score": circle_result.selected.total_score,
                "hotel_strategy": hotel.preset_name,
                "pipeline": "city_circle_v1",
                "model": settings.ai_model_standard,
                "hotel_bases": hotel_bases_meta,
                "actual_cities": actual_cities,
            },
        )
        session.add(plan)

        # 索引 meal_fills by day
        meal_by_day = {}
        for mf in meal_fills:
            meal_by_day[mf.day_index] = mf

        # 城市→走廊中文映射（PDF 渲染用）
        _CZH = {
            "fushimi": "伏见·稻荷", "arashiyama": "岚山·嵯峨野",
            "higashiyama": "东山·清水寺", "gion": "祇园·花见小路",
            "kawaramachi": "河原町·四条", "namba": "难波·道顿堀",
            "osakajo": "大阪城·天满桥", "sakurajima": "环球影城(USJ)",
            "shinsekai": "新世界·天王寺", "nara_park": "奈良公园·东大寺",
        }
        _AZZH = {
            "kawaramachi": "京都·河原町", "namba": "大阪·难波",
            "gion": "京都·祇园", "kyoto": "京都", "osaka": "大阪",
        }

        # 写入每天的结构（使用真实 meal_fills 替代 placeholder）
        for frame in skeleton.frames:
            day = ItineraryDay(
                plan_id=plan_id,
                day_number=frame.day_index,
                city_code=frame.sleep_base,
                day_theme=frame.title_hint or f"Day {frame.day_index}",
                day_summary_zh=f"{frame.day_type} | {frame.primary_corridor or ''} | {frame.intensity}",
            )
            session.add(day)
            await session.flush()

            sort_idx = 0

            # 写入主活动 item
            if frame.main_driver:
                from app.db.models.city_circles import CircleEntityRole
                anchor_q = await session.execute(
                    select(CircleEntityRole).where(
                        CircleEntityRole.circle_id == circle_id,
                        CircleEntityRole.cluster_id == frame.main_driver,
                        CircleEntityRole.is_cluster_anchor == True,
                    ).limit(1)
                )
                anchor = anchor_q.scalars().first()
                if anchor:
                    entity = await session.get(EntityBase, anchor.entity_id)
                    corr_zh = _CZH.get(frame.primary_corridor, frame.primary_corridor or "")
                    item = ItineraryItem(
                        day_id=day.day_id,
                        entity_id=anchor.entity_id,
                        item_type=entity.entity_type if entity else "poi",
                        sort_order=sort_idx,
                        notes_zh=json.dumps({
                            "name": entity.name_zh if entity else "",
                            "corridor": frame.primary_corridor,
                            "corridor_display": corr_zh,
                            "area_display": entity.area_name if entity else "",
                            "is_main_driver": True,
                        }, ensure_ascii=False),
                    )
                    session.add(item)
                    sort_idx += 1

            # 写入真实餐厅 items（从 meal_fills）
            mf = meal_by_day.get(frame.day_index)
            if mf:
                for meal in mf.meals:
                    r = meal.restaurant if isinstance(meal.restaurant, dict) else {}
                    eid = r.get("entity_id")
                    serving_corr = r.get("serving_corridor", "")
                    serving_zh = _CZH.get(serving_corr, _AZZH.get(serving_corr, serving_corr))
                    cuisine_zh_map = {
                        "sushi": "寿司", "ramen": "拉面", "yakiniku": "烧肉",
                        "tempura": "天妇罗", "kushikatsu": "串炸", "kaiseki": "怀石",
                        "cafe": "咖啡轻食", "takoyaki": "章鱼烧", "okonomiyaki": "大阪烧",
                        "yakitori": "烧鸟", "udon": "乌冬", "tonkatsu": "炸猪排",
                    }
                    cu_raw = r.get("cuisine_type", "")
                    cu_zh = cuisine_zh_map.get(cu_raw, cu_raw)
                    # 净化 cuisine_display：如果还是 raw key（如 kyo_gion），再做一层映射
                    if cu_zh and cu_zh.startswith(("kyo_", "osa_")):
                        cu_zh = _CZH.get(cu_zh, cu_zh)

                    # 净化 why_here：确保无 raw key 残留
                    why_here_raw = r.get("why_here", "")
                    for rk, zv in _CZH.items():
                        why_here_raw = why_here_raw.replace(rk, zv)
                    for rk, zv in _AZZH.items():
                        why_here_raw = why_here_raw.replace(rk, zv)

                    # 净化 area_display
                    area_raw = r.get("area_name", "")
                    area_display = _CZH.get(area_raw, _AZZH.get(area_raw, area_raw))

                    meal_item = ItineraryItem(
                        day_id=day.day_id,
                        item_type="restaurant",
                        entity_id=uuid.UUID(eid) if eid else None,
                        sort_order=sort_idx,
                        start_time={"breakfast": "08:00", "lunch": "12:00", "dinner": "18:30"}.get(meal.meal_type, "12:00"),
                        duration_min=60 if meal.meal_type == "dinner" else 45,
                        notes_zh=json.dumps({
                            "name": r.get("name", ""),
                            "meal_type": meal.meal_type,
                            "placeholder": False,
                            "cuisine": cu_raw,
                            "cuisine_display": cu_zh,
                            "why_here": why_here_raw,
                            "serving_area": serving_zh,
                            "corridor": serving_corr,
                            "corridor_display": serving_zh,
                            "area_display": area_display,
                        }, ensure_ascii=False),
                    )
                    session.add(meal_item)
                    sort_idx += 1
            else:
                # fallback: 写 placeholder
                for i, mw in enumerate(frame.meal_windows):
                    meal_item = ItineraryItem(
                        day_id=day.day_id,
                        item_type="restaurant",
                        sort_order=sort_idx,
                        notes_zh=json.dumps({
                            "meal_type": mw.meal_type,
                            "placeholder": True,
                        }, ensure_ascii=False),
                    )
                    session.add(meal_item)
                    sort_idx += 1

        await session.commit()
        logger.info("DB 写入完成: plan_id=%s (%d days)", plan_id, len(skeleton.frames))

        t_phase3 = time.time() - t0 - t_phase2
        logger.info("Phase 3 完成 (%.1fs)", t_phase3)

        # ══════════════════════════════════════════════════════════════════
        # Phase 4: AI 文案生成（调真实 API）
        # ══════════════════════════════════════════════════════════════════
        logger.info("═══ Phase 4: AI 文案生成 ═══")
        t_ai_start = time.time()
        ai_call_count = 0

        # 4a. 实体文案 (copywriter)
        logger.info("--- 4a: 实体文案 (copywriter) ---")
        from app.domains.planning.copywriter import generate_copy

        # 通过 days → items 的关系查询本 plan 的所有 items
        days_q = await session.execute(
            select(ItineraryDay).where(ItineraryDay.plan_id == plan_id)
        )
        day_ids = [d.day_id for d in days_q.scalars().all()]
        items = []
        if day_ids:
            items_q = await session.execute(
                select(ItineraryItem).where(ItineraryItem.day_id.in_(day_ids))
            )
            items = items_q.scalars().all()
        entity_ids = list({item.entity_id for item in items if item.entity_id})

        copy_results = {}
        for eid in entity_ids:
            from app.db.models.catalog import EntityBase
            entity = await session.get(EntityBase, eid)
            if entity:
                try:
                    copy = await generate_copy(entity, scene="couple", redis_client=None)
                    copy_results[str(eid)] = copy
                    ai_call_count += 1
                    logger.info("  ✍️ %s → %s", entity.name_zh, copy.get("copy_zh", "")[:40])
                except Exception as e:
                    logger.warning("  ⚠️ %s 文案失败: %s", entity.name_zh, e)

        logger.info("实体文案完成: %d/%d 成功", len(copy_results), len(entity_ids))

        # 4a'. 回写文案到 items
        for item in items:
            if item.entity_id and str(item.entity_id) in copy_results:
                notes = json.loads(item.notes_zh) if item.notes_zh else {}
                notes.update(copy_results[str(item.entity_id)])
                item.notes_zh = json.dumps(notes, ensure_ascii=False)
        await session.commit()

        # 4b. PlanningOutput 构建（直通，无 report 中间层）
        logger.info("--- 4b: PlanningOutput + page pipeline ---")
        from app.domains.rendering.planning_output import build_planning_output
        from app.domains.rendering.chapter_planner import plan_chapters
        from app.domains.rendering.page_planner import plan_pages_and_persist
        from app.domains.rendering.page_view_model import build_view_models

        report = None
        try:
            import dataclasses as _dc
            frame_dicts = [_dc.asdict(f) for f in skeleton.frames]
            design_brief = {
                "route_strategy": [f"城市圈: {circle_id}"],
                "tradeoffs": [],
                "stay_strategy": [f"hotel: {hotel.preset_name or 'default'}"],
                "budget_strategy": ["mid"],
                "execution_principles": ["moderate"],
            }
            planning_output = await build_planning_output(
                session,
                plan_id=plan_id,
                trip_request_id=trip_request_id,
                day_frames=frame_dicts,
                design_brief=design_brief,
                circle_id=circle_id,
                profile=profile,
            )
            chapters = plan_chapters(planning_output)
            pages = await plan_pages_and_persist(chapters, planning_output, session, plan_id)
            view_models = build_view_models(pages, planning_output)
            report = {"schema_version": "v2", "pages": len(pages), "vms": len(view_models)}
            logger.info("page pipeline 完成: chapters=%d pages=%d vms=%d", len(chapters), len(pages), len(view_models))
        except Exception as e:
            logger.error("page pipeline 失败: %s", e, exc_info=True)
            report = None

        t_phase4 = time.time() - t_ai_start
        logger.info("Phase 4 完成 (%.1fs, %d AI calls)", t_phase4, ai_call_count)

        # ══════════════════════════════════════════════════════════════════
        # Phase 5: 质量评估（可选，规则引擎）
        # ══════════════════════════════════════════════════════════════════
        logger.info("═══ Phase 5: 质量评估 ═══")

        try:
            from app.core.quality_gate import run_quality_gate
            from app.workers.jobs.generate_trip import _build_plan_json
            plan_json = await _build_plan_json(session, plan_id)
            gate_result = await run_quality_gate(plan_json, db=session)
            logger.info("质量门控: %s (score=%.1f)", "✅ PASS" if gate_result.passed else "❌ FAIL", gate_result.score)
            if gate_result.errors:
                for e in gate_result.errors[:5]:
                    logger.warning("  ❌ %s", e)
            if gate_result.warnings:
                for w in gate_result.warnings[:5]:
                    logger.info("  ⚠️ %s", w)
        except Exception as e:
            logger.warning("质量门控跳过: %s", e)

        # 离线评测
        try:
            from app.domains.evaluation.offline_eval import score_plan, EvalCase
            plan_json_eval = await _build_plan_json(session, plan_id)
            eval_case = EvalCase(
                case_id=f"local_{plan_id}",
                description="local pipeline test",
                user_profile={"scene": "couple"},
                expected_constraints={"min_days": 1, "max_days": 30},
                plan_json=plan_json_eval,
            )
            eval_result = score_plan(plan_json_eval, eval_case)
            logger.info(
                "离线评测: overall=%.2f (完整=%.1f 可行=%.1f 多样=%.1f)",
                eval_result.overall, eval_result.completeness,
                eval_result.feasibility, eval_result.diversity,
            )
        except Exception as e:
            logger.warning("离线评测跳过: %s", e)

        # ══════════════════════════════════════════════════════════════════
        # 最终汇总
        # ══════════════════════════════════════════════════════════════════
        total_time = time.time() - t0
        print("\n" + "="*70)
        print("  📊 管线执行汇总")
        print("="*70)
        print(f"  Plan ID:       {plan_id}")
        print(f"  城市圈:        {circle_id} (score={circle_result.selected.total_score:.3f})")
        print(f"  主要活动:      {len(ranking.selected_majors)} 个")
        print(f"  酒店策略:      {hotel.preset_name}")
        print(f"  骨架:          {len(skeleton.frames)} 天")
        print(f"  实体文案:      {len(copy_results)}/{len(entity_ids)} 成功")
        print(f"  攻略报告:      {'✅ 已生成' if report else '❌ 失败'}")
        print(f"  AI 调用次数:   {ai_call_count}")
        print(f"  总耗时:        {total_time:.1f}s (决策={t_phase2:.1f}s DB={t_phase3:.1f}s AI={t_phase4:.1f}s)")
        print(f"  模型:          {settings.ai_model_standard}")
        print("="*70)

        # 输出报告预览
        if report:
            print("\n📝 报告预览:\n")
            overview = report.get("layer1_overview", {})
            design = overview.get("design_philosophy", {})
            if design:
                print(f"  设计理念: {design.get('one_liner', '')}")
                print(f"  核心原则: {design.get('core_principles', '')}")

            ov = overview.get("overview", {})
            if ov:
                print(f"\n  总纲: {ov.get('route_logic', '')[:100]}...")

            daily = report.get("layer2_daily", [])
            for d in daily[:2]:  # 只预览前 2 天
                r = d.get("report", {})
                print(f"\n  Day {d['day_number']}: {d.get('day_theme', '')}")
                print(f"    标题: {r.get('title', '')}")
                print(f"    亮点: {r.get('highlights', '')[:80]}...")

            if len(daily) > 2:
                print(f"\n  ... 还有 {len(daily) - 2} 天 (完整报告已写入 DB)")

        print(f"\n✅ 完整管线执行成功! plan_id={plan_id}\n")


asyncio.run(main())
