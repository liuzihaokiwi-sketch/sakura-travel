"""demo_page_pipeline.py — 用真实 DB 数据跑一遍完整页面生成管线"""
import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
logging.basicConfig(level=logging.WARNING)

from app.db.session import AsyncSessionLocal
from sqlalchemy import select, text
from app.db.models.catalog import EntityBase


async def main():
    async with AsyncSessionLocal() as session:
        # 1. 查看可用实体
        r = await session.execute(text(
            "SELECT entity_type, count(*) FROM entity_base "
            "WHERE city_code IN ('kyoto','osaka','nara','kobe') "
            "GROUP BY entity_type"
        ))
        print("=== 关西圈可用实体 ===")
        for row in r.fetchall():
            print(f"  {row[0]:15s} {row[1]:4d}")

        # 2. 拿真实实体
        kyoto_pois = (await session.execute(
            select(EntityBase).where(
                EntityBase.city_code == "kyoto",
                EntityBase.entity_type == "poi",
            ).limit(15)
        )).scalars().all()

        osaka_pois = (await session.execute(
            select(EntityBase).where(
                EntityBase.city_code == "osaka",
                EntityBase.entity_type == "poi",
            ).limit(10)
        )).scalars().all()

        restaurants = (await session.execute(
            select(EntityBase).where(
                EntityBase.city_code.in_(["kyoto", "osaka"]),
                EntityBase.entity_type == "restaurant",
            ).limit(10)
        )).scalars().all()

        print(f"\n拿到: 京都POI={len(kyoto_pois)} 大阪POI={len(osaka_pois)} 餐厅={len(restaurants)}")

        # 3. 构建 PlanningOutput
        from app.domains.rendering.planning_output import PlanningOutput
        from app.domains.planning.report_schema import (
            DaySection, DaySlot, DesignBrief, EmotionalGoal,
            ExecutionNotes, OverviewSection, ProfileSummary, ReportMeta,
            RouteSummaryCard, SelectedCircleInfo, ConditionalSection,
        )

        day_configs = [
            ("arrival", "京都·东山初见", "higashiyama", "light", kyoto_pois[:3]),
            ("normal", "京都·岚山竹林", "arashiyama", "balanced", kyoto_pois[3:6]),
            ("normal", "大阪·道顿堀美食", "namba", "balanced", osaka_pois[:4]),
            ("normal", "京都·金阁寺深度", "kinugasa", "balanced", kyoto_pois[6:9]),
            ("departure", "京都·收尾漫步", "kyoto_station", "light", kyoto_pois[9:11]),
        ]

        mood_map = {
            "arrival": ("期待", "第一天不赶路，慢慢感受京都的节奏"),
            "normal": ("探索", "今天的主角值得你花一整天"),
            "departure": ("收获", "带着回忆轻松离开"),
        }

        days = []
        emotional_goals = []
        conditionals = []
        evidence = []

        for d_idx, (day_type, title, area, intensity, pois) in enumerate(day_configs, 1):
            slots = []
            for s_idx, ent in enumerate(pois):
                name = ent.name_zh or ent.name_en or "unknown"
                slots.append(DaySlot(
                    slot_index=s_idx,
                    kind="poi",
                    entity_id=str(ent.entity_id),
                    title=name,
                    area=ent.area_name or area,
                    start_time_hint=f"{9 + s_idx * 2:02d}:00",
                    duration_mins=ent.visit_duration_min or 90,
                ))
                conditionals.append(ConditionalSection(
                    section_type="extra",
                    trigger_reason=f"Day {d_idx} poi",
                    related_day_indexes=[d_idx],
                    payload={
                        "entity_id": str(ent.entity_id),
                        "name": name,
                        "entity_type": ent.entity_type,
                        "day_index": d_idx,
                        "data_tier": ent.data_tier or "B",
                        "area": ent.area_name or "",
                    },
                ))
                evidence.append({
                    "entity_id": str(ent.entity_id),
                    "name": name,
                    "hero_image_url": None,
                    "why_selected": f"{name}是{area}区域的代表性景点，值得专程前往",
                })

            # 加餐厅
            if d_idx <= len(restaurants):
                rest = restaurants[d_idx - 1]
                rname = rest.name_zh or rest.name_en or "restaurant"
                slots.append(DaySlot(
                    slot_index=len(slots),
                    kind="restaurant",
                    entity_id=str(rest.entity_id),
                    title=rname,
                    area=rest.area_name or area,
                    start_time_hint="12:30",
                    duration_mins=60,
                ))

            keyword, sentence = mood_map.get(day_type, ("探索", ""))
            tags = ["arrival"] if day_type == "arrival" else (["departure"] if day_type == "departure" else [])

            days.append(DaySection(
                day_index=d_idx, title=title, primary_area=area,
                day_goal=sentence, intensity=intensity,
                start_anchor=slots[0].title if slots else "",
                end_anchor=slots[-1].title if slots else "",
                must_keep=slots[0].title if slots else "",
                first_cut="",
                route_integrity_score=0.92,
                risks=[], slots=slots, reasoning=[],
                execution_notes=ExecutionNotes(),
                trigger_tags=tags,
            ))
            emotional_goals.append(EmotionalGoal(
                day_index=d_idx, mood_keyword=keyword, mood_sentence=sentence,
            ))

        po = PlanningOutput(
            meta=ReportMeta(
                trip_id="demo-001", destination="关西经典", total_days=5,
                circle=SelectedCircleInfo(circle_id="kansai_classic_circle", name_zh="关西经典"),
            ),
            profile_summary=ProfileSummary(
                party_type="couple", pace_preference="balanced", budget_bias="mid",
                trip_goals=["寺社文化", "美食", "摄影"],
            ),
            design_brief=DesignBrief(
                route_strategy=["城市圈: 关西经典", "京都3天+大阪1天+收尾1天"],
            ),
            overview=OverviewSection(route_summary=[
                RouteSummaryCard(day_index=d.day_index, title=d.title, primary_area=d.primary_area, intensity=d.intensity)
                for d in days
            ]),
            days=days,
            prep_notes={"title": "出发准备", "items": ["确认护照签证", "下载离线地图", "预约必订餐厅"]},
            conditional_sections=conditionals,
            emotional_goals=emotional_goals,
            selection_evidence=evidence,
            circles=[SelectedCircleInfo(circle_id="kansai_classic_circle", name_zh="关西经典")],
            day_circle_map={d: "kansai_classic_circle" for d in range(1, 6)},
        )

        # 4. 跑 page pipeline
        from app.domains.rendering.chapter_planner import plan_chapters
        from app.domains.rendering.page_planner import plan_pages
        from app.domains.rendering.page_view_model import build_view_models

        chapters = plan_chapters(po)
        pages = plan_pages(chapters, po)
        vms = build_view_models(pages, po)

        # 5. 输出
        print(f"\n{'='*60}")
        print(f"关西经典 5天 · couple · balanced · mid")
        print(f"Pages: {len(pages)}  ViewModels: {len(vms)}")
        print(f"{'='*60}")

        for page in sorted(pages, key=lambda p: p.page_order):
            vm = vms.get(page.page_id)
            if not vm:
                continue

            day_tag = f" [Day {page.day_index}]" if page.day_index else ""
            diy = ""
            if page.sticker_zone:
                diy += f" [贴纸:{page.sticker_zone}]"
            if page.freewrite_zone:
                diy += f" [手写:{page.freewrite_zone}]"

            print(f"\n  P{page.page_order:02d} {page.page_type:25s}{day_tag}{diy}")
            print(f"      {vm.heading.title}")

            if page.page_type == "day_execution":
                for sec in vm.sections:
                    if sec.section_type == "text_block" and hasattr(sec.content, "text"):
                        if sec.content.text:
                            print(f"      mood: {sec.content.text}")
                    elif sec.section_type == "timeline" and hasattr(sec.content, "items"):
                        for item in sec.content.items:
                            icon = {"poi": "[POI]", "restaurant": "[EAT]", "hotel": "[HTL]"}.get(item.type_icon, "[ - ]")
                            dur = f"{item.duration}min" if item.duration else ""
                            print(f"        {item.time} {icon} {item.name}  {dur}")

            if page.page_type == "major_activity_detail":
                for sec in vm.sections:
                    if sec.section_type == "key_reasons" and hasattr(sec.content, "reasons"):
                        for r in sec.content.reasons[:2]:
                            print(f"      reason: {r}")


if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    asyncio.run(main())
