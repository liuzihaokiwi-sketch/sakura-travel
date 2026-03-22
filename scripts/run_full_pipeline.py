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
            },
        )
        session.add(plan)

        # 写入每天的结构
        for frame in skeleton.frames:
            day = ItineraryDay(
                plan_id=plan_id,
                day_number=frame.day_index,
                city_code=frame.sleep_base,
                day_theme=frame.title_hint or f"Day {frame.day_index}",
                day_summary_zh=f"{frame.day_type} | {frame.primary_corridor or ''} | {frame.intensity}",
            )
            session.add(day)
            await session.flush()  # 获取 autoincrement day_id

            # 写入主活动 item — 通过 cluster_id 查找 anchor entity
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
                    from app.db.models.catalog import EntityBase
                    entity = await session.get(EntityBase, anchor.entity_id)
                    item = ItineraryItem(
                        day_id=day.day_id,
                        entity_id=anchor.entity_id,
                        item_type=entity.entity_type if entity else "poi",
                        sort_order=1,
                        notes_zh=json.dumps({
                            "corridor": frame.primary_corridor,
                            "is_main_driver": True,
                            "cluster_id": frame.main_driver,
                        }, ensure_ascii=False),
                    )
                    session.add(item)

            # 写入餐窗 placeholder
            for i, meal in enumerate(frame.meal_windows):
                meal_item = ItineraryItem(
                    day_id=day.day_id,
                    item_type="restaurant",
                    sort_order=10 + i,
                    notes_zh=json.dumps({
                        "meal_type": meal.meal_type,
                        "placeholder": True,
                    }, ensure_ascii=False),
                )
                session.add(meal_item)

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

        # 4b. 总纲 + 每日攻略报告 (report_generator)
        logger.info("--- 4b: 总纲 + 每日攻略报告 ---")
        from app.domains.planning.report_generator import generate_report

        user_context = {
            "party_type": "couple",
            "styles": ["文化", "美食"],
            "budget_level": "mid",
            "pace": "moderate",
        }

        try:
            report = await generate_report(session, plan_id, user_context)
            ai_call_count += 1 + len(skeleton.frames)  # 总纲 + 每天
            logger.info("攻略报告生成完成! schema=%s", report.get("schema_version", "?"))

            # 统计字数
            overview = report.get("layer1_overview", {})
            daily = report.get("layer2_daily", [])
            total_chars = len(json.dumps(report, ensure_ascii=False))
            logger.info("报告总字符: %d (总纲 + %d 天)", total_chars, len(daily))
        except Exception as e:
            logger.error("攻略报告生成失败: %s", e, exc_info=True)
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
