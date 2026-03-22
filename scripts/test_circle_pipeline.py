"""
test_circle_pipeline.py — 端到端测试完整 City-Circle 规划管线

流程:
  1. 模拟 TripProfile (关西 6 天, 情侣, mid 预算)
  2. Phase 2a: 城市圈选择
  3. Phase 2b: 资格过滤 (eligibility_gate)
  4. Phase 2c: 主要活动排序 (major_activity_ranker)
  5. Phase 2d: 酒店策略 (hotel_base_builder)
  6. Phase 3:  骨架编排 (route_skeleton_builder)
  7. 结果汇总
"""
import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("test_pipeline")
logger.setLevel(logging.INFO)

from sqlalchemy import text
from app.db.session import AsyncSessionLocal


# ── helpers ───────────────────────────────────────────────────────────────────

def _print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def _print_kv(label: str, value, indent=2):
    pad = " " * indent
    print(f"{pad}{label}: {value}")


# ── main ──────────────────────────────────────────────────────────────────────

async def main():
    print("\n🗾 City-Circle Pipeline — 端到端测试")
    print("   目标: 关西经典圈 · 6天5晚 · 情侣 · 中等预算\n")

    async with AsyncSessionLocal() as session:

        # ── 0. 验证种子数据 ─────────────────────────────────────────────
        _print_section("Phase 0: 数据验证")

        row = await session.execute(text(
            "SELECT count(*) FROM city_circles WHERE is_active = true"
        ))
        circle_count = row.scalar()
        print(f"  活跃城市圈: {circle_count}")

        row = await session.execute(text(
            "SELECT count(*) FROM activity_clusters WHERE circle_id = 'kansai_classic_circle'"
        ))
        cluster_count = row.scalar()
        print(f"  关西活动簇: {cluster_count}")

        row = await session.execute(text(
            "SELECT count(*) FROM hotel_strategy_presets WHERE circle_id = 'kansai_classic_circle'"
        ))
        preset_count = row.scalar()
        print(f"  关西酒店预设: {preset_count}")

        row = await session.execute(text(
            "SELECT count(*) FROM entity_base WHERE city_code IN ('kyoto','osaka','nara') AND is_active = true"
        ))
        entity_count = row.scalar()
        print(f"  关西实体 (kyoto/osaka/nara): {entity_count}")

        row = await session.execute(text(
            "SELECT count(*) FROM route_matrix_cache"
        ))
        matrix_count = row.scalar()
        print(f"  路线矩阵缓存: {matrix_count} 对")

        if circle_count == 0 or cluster_count == 0:
            print("\n❌ 种子数据不足，无法继续。请先执行 seed_kansai_mvp.py")
            return

        print("  ✅ 数据充足，继续测试")

        # ── 1. 构造 mock TripProfile ────────────────────────────────────
        _print_section("Phase 1: 构造用户画像 (mock TripProfile)")

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

        _print_kv("天数", profile.duration_days)
        _print_kv("城市", [c["city_code"] for c in profile.cities])
        _print_kv("同行", profile.party_type)
        _print_kv("预算", profile.budget_level)
        _print_kv("机场", f"{profile.arrival_airport} → {profile.departure_airport}")
        _print_kv("季节", "spring/cherry_blossom (4月)")

        # ── 2. 城市圈选择 ──────────────────────────────────────────────
        _print_section("Phase 2a: 城市圈选择")

        from app.domains.planning.city_circle_selector import select_city_circle
        circle_result = await select_city_circle(session, profile)

        if circle_result.selected:
            sel = circle_result.selected
            _print_kv("✅ 选中", f"{sel.circle_id} ({sel.name_zh})")
            _print_kv("总分", f"{sel.total_score:.4f}")
            for dim, score in sorted(sel.breakdown.items(), key=lambda x: -x[1]):
                _print_kv(f"  {dim}", f"{score:.3f}", indent=4)
            if sel.explain.why_selected:
                _print_kv("原因", sel.explain.why_selected)
        else:
            print("  ❌ 无城市圈被选中")
            for trace in circle_result.trace:
                print(f"    {trace}")
            return

        circle_id = circle_result.selected_circle_id
        print(f"\n  其他候选:")
        for c in circle_result.candidates:
            if c.circle_id != circle_id:
                tag = "❌" if c.rejected else "🔸"
                reason = c.reject_reason or f"score={c.total_score:.3f}"
                print(f"    {tag} {c.circle_id} — {reason}")

        # ── 2b. 资格过滤 ──────────────────────────────────────────────
        _print_section("Phase 2b: 活动簇资格过滤 (Eligibility Gate)")

        from app.domains.planning.eligibility_gate import run_eligibility_gate
        try:
            elig_result = await run_eligibility_gate(session, circle_id, profile)
            passed_ids = elig_result.passed_cluster_ids
            _print_kv("通过", f"{len(passed_ids)} 个簇")
            for cid in sorted(passed_ids):
                _print_kv("  ✅", cid, indent=4)
            if hasattr(elig_result, "failed_cluster_ids"):
                failed = elig_result.failed_cluster_ids or set()
                if failed:
                    _print_kv("淘汰", f"{len(failed)} 个簇")
                    for cid in sorted(failed):
                        _print_kv("  ❌", cid, indent=4)
        except Exception as e:
            logger.warning("eligibility_gate 失败 (%s)，使用全部簇作为 fallback", e)
            # fallback: 使用所有簇
            from sqlalchemy import select as sa_select
            from app.db.models.city_circles import ActivityCluster
            q = await session.execute(
                sa_select(ActivityCluster.cluster_id).where(
                    ActivityCluster.circle_id == circle_id
                )
            )
            passed_ids = {r[0] for r in q.fetchall()}
            _print_kv("Fallback 全部簇", f"{len(passed_ids)} 个")

        # ── 2c. 主要活动排序 ──────────────────────────────────────────
        _print_section("Phase 2c: 主要活动排序")

        from app.domains.planning.major_activity_ranker import rank_major_activities
        ranking_result = await rank_major_activities(
            session,
            circle_id=circle_id,
            profile=profile,
            passed_cluster_ids=passed_ids,
        )

        _print_kv("容量", f"{ranking_result.capacity_used:.1f} / {ranking_result.capacity_total:.1f}")
        print(f"\n  选中主要活动 ({len(ranking_result.selected_majors)}):")
        for m in ranking_result.selected_majors:
            print(f"    🎯 {m.name_zh} [{m.level}] "
                  f"score={m.major_score:.2f} "
                  f"(base={m.base_quality_score:.2f} ctx={m.context_fit_score:.2f}) "
                  f"dur={m.default_duration} corridor={m.primary_corridor}")

        if ranking_result.all_ranked:
            not_selected = [m for m in ranking_result.all_ranked if not m.selected]
            if not_selected:
                print(f"\n  未选中 ({len(not_selected)}):")
                for m in not_selected[:5]:
                    print(f"    🔸 {m.name_zh} [{m.level}] "
                          f"score={m.major_score:.2f} — {m.selection_reason}")

        # ── 2d. 酒店策略 ──────────────────────────────────────────────
        _print_section("Phase 2d: 酒店住法策略")

        from app.domains.planning.hotel_base_builder import build_hotel_strategy
        hotel_result = await build_hotel_strategy(
            session,
            circle_id=circle_id,
            profile=profile,
            selected_cluster_ids=[m.cluster_id for m in ranking_result.selected_majors],
        )

        _print_kv("策略", hotel_result.preset_name or "(默认)")
        _print_kv("总夜数", hotel_result.total_nights)
        _print_kv("换酒店次数", hotel_result.switch_count)
        _print_kv("末晚安全", "✅" if hotel_result.last_night_safe else "⚠️ 不安全")
        if hotel_result.last_night_airport_minutes:
            _print_kv("末晚→机场", f"{hotel_result.last_night_airport_minutes} 分钟")

        for i, base in enumerate(hotel_result.bases, 1):
            print(f"\n    Base {i}: {base.base_city} · {base.area}")
            print(f"      住 {base.nights} 晚")
            print(f"      覆盖: {base.served_cluster_ids}")

        if hotel_result.explain.why_selected:
            print(f"\n  {hotel_result.explain.why_selected}")

        # ── 3. 骨架编排 ──────────────────────────────────────────────
        _print_section("Phase 3: 日骨架编排")

        from app.domains.planning.route_skeleton_builder import build_route_skeleton
        skeleton_result = build_route_skeleton(
            duration_days=profile.duration_days,
            selected_majors=ranking_result.selected_majors,
            hotel_bases=hotel_result.bases,
            pace=profile.pace or "moderate",
        )

        for frame in skeleton_result.frames:
            meals = "/".join(m.meal_type[0].upper() for m in frame.meal_windows)
            driver_str = frame.main_driver_name or "—"
            print(
                f"  Day {frame.day_index} [{frame.day_type:10}] "
                f"🏨{frame.sleep_base:15} "
                f"🚶{frame.primary_corridor or '—':15} "
                f"🎯{driver_str:20} "
                f"cap={frame.day_capacity_units:.1f} "
                f"⏱{frame.transfer_budget_minutes}m "
                f"🍽{meals} "
                f"[{frame.intensity}]"
            )
            if frame.title_hint:
                print(f"         📝 {frame.title_hint}")

        # ── 汇总 ──────────────────────────────────────────────────────
        _print_section("Pipeline 汇总")

        print(f"  城市圈:     {circle_id}")
        print(f"  主要活动:   {len(ranking_result.selected_majors)} 个")
        print(f"  酒店策略:   {hotel_result.preset_name} ({hotel_result.total_nights}晚, "
              f"{hotel_result.switch_count}次换)")
        print(f"  骨架天数:   {len(skeleton_result.frames)} 天")
        print(f"  路线矩阵:   {matrix_count} 对缓存可用")
        print()

        # trace
        all_traces = (
            circle_result.trace
            + ranking_result.trace
            + hotel_result.trace
            + skeleton_result.trace
        )
        if all_traces:
            print("  📋 Trace Log:")
            for t in all_traces[-15:]:
                print(f"    {t}")

        print(f"\n✅ 端到端管线测试完成！\n")


asyncio.run(main())
