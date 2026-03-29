"""
backfill_activity_cluster_fields.py

回填 activity_clusters 的核心字段：
  - city_code
  - experience_family
  - rhythm_role
  - energy_level

优先从现有 seed 脚本收集定义；少量历史遗留簇使用手工补丁。
只补缺失字段，不覆盖数据库里已有值，可重复执行。

用法：
    python scripts/backfill_activity_cluster_fields.py
    python scripts/backfill_activity_cluster_fields.py --circle kansai_classic_circle
    python scripts/backfill_activity_cluster_fields.py --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import importlib
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.db.models.city_circles import ActivityCluster
from app.db.session import AsyncSessionLocal

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

TARGET_FIELDS = (
    "city_code",
    "experience_family",
    "rhythm_role",
    "energy_level",
)

SOURCE_MODULES = [
    "scripts.seed_all_circles",
    "scripts.seed_family_shopping_clusters",
    "scripts.seed_tokyo_clusters",
    "scripts.seed_hokkaido_clusters",
    "scripts.seed_guangfu_clusters",
    "scripts.seed_xinjiang_clusters",
    "scripts.seed_chubu_clusters",
    "scripts.seed_kyushu_clusters",
    "scripts.seed_okinawa_clusters",
    "scripts.seed_huadong_clusters",
    "scripts.seed_chaoshan_clusters",
]


MANUAL_PATCHES: dict[str, dict[str, str]] = {
    # chubu_mountain_circle
    "chu_kamikochi_alpine": {
        "experience_family": "mountain", "rhythm_role": "peak", "energy_level": "high",
    },
    "chu_kanazawa_kenroku": {
        "experience_family": "art", "rhythm_role": "contrast", "energy_level": "medium",
    },
    "chu_matsumoto_castle": {
        "experience_family": "locallife", "rhythm_role": "contrast", "energy_level": "medium",
    },
    "chu_nagoya_city": {
        "experience_family": "food", "rhythm_role": "utility", "energy_level": "medium",
    },
    "chu_shirakawago_heritage": {
        "experience_family": "locallife", "rhythm_role": "peak", "energy_level": "medium",
    },
    "chu_takayama_old_town": {
        "experience_family": "locallife", "rhythm_role": "contrast", "energy_level": "medium",
    },
    # hokkaido_city_circle
    "hok_niseko_skiing": {
        "city_code": "niseko", "experience_family": "mountain", "rhythm_role": "peak", "energy_level": "high",
    },
    "hok_otaru_canal_day": {
        "city_code": "otaru", "experience_family": "locallife", "rhythm_role": "contrast", "energy_level": "low",
    },
    "hok_sapporo_odori_susukino": {
        "city_code": "sapporo", "experience_family": "citynight", "rhythm_role": "contrast", "energy_level": "low",
    },
    # hokkaido_nature_circle
    "hok_asahiyama_zoo": {
        "experience_family": "locallife", "rhythm_role": "contrast", "energy_level": "medium",
    },
    "hok_biei_patchwork_road": {
        "experience_family": "mountain", "rhythm_role": "contrast", "energy_level": "medium",
    },
    "hok_drift_ice_abashiri": {
        "experience_family": "sea", "rhythm_role": "peak", "energy_level": "high",
    },
    "hok_furano_lavender": {
        "experience_family": "flower", "rhythm_role": "peak", "energy_level": "medium",
    },
    "hok_hakodate_morning_market": {
        "experience_family": "food", "rhythm_role": "peak", "energy_level": "medium",
    },
    "hok_otaru_canal_glass": {
        "experience_family": "locallife", "rhythm_role": "contrast", "energy_level": "low",
    },
    "hok_shiretoko_nature": {
        "experience_family": "mountain", "rhythm_role": "peak", "energy_level": "high",
    },
    "hok_toya_noboribetsu_onsen": {
        "experience_family": "onsen", "rhythm_role": "recovery", "energy_level": "low",
    },
    # kansai_classic_circle
    "kyo_ando_architecture": {
        "city_code": "kyoto", "experience_family": "art", "rhythm_role": "contrast", "energy_level": "medium",
    },
    "kyo_autumn_foliage_circuit": {
        "city_code": "kyoto", "experience_family": "flower", "rhythm_role": "peak", "energy_level": "high",
    },
    "kyo_daigo_sakura": {
        "city_code": "kyoto", "experience_family": "flower", "rhythm_role": "peak", "energy_level": "high",
    },
    "kyo_daitokuji_zen_complex": {
        "city_code": "kyoto", "experience_family": "shrine", "rhythm_role": "recovery", "energy_level": "low",
    },
    "kyo_fushimi_momoyama_history": {
        "city_code": "kyoto", "experience_family": "shrine", "rhythm_role": "contrast", "energy_level": "medium",
    },
    "kyo_garden_imperial_circuit": {
        "city_code": "kyoto", "experience_family": "art", "rhythm_role": "recovery", "energy_level": "low",
    },
    "kyo_kaiseki_gion_evening": {
        "city_code": "kyoto", "experience_family": "food", "rhythm_role": "recovery", "energy_level": "low",
    },
    "kyo_night_sakura_gion": {
        "city_code": "kyoto", "experience_family": "flower", "rhythm_role": "contrast", "energy_level": "low",
    },
    "kyo_nishiki_gourmet": {
        "city_code": "kyoto", "experience_family": "food", "rhythm_role": "utility", "energy_level": "low",
    },
    "kyo_sakura_photo_circuit": {
        "city_code": "kyoto", "experience_family": "flower", "rhythm_role": "peak", "energy_level": "high",
    },
    "kyo_upper_arashiyama_niche": {
        "city_code": "kyoto", "experience_family": "mountain", "rhythm_role": "contrast", "energy_level": "medium",
    },
    "kyo_wisteria_byodoin": {
        "city_code": "uji", "experience_family": "flower", "rhythm_role": "contrast", "energy_level": "medium",
    },
    "miho_museum_day_trip": {
        "city_code": "shiga", "experience_family": "art", "rhythm_role": "peak", "energy_level": "medium",
    },
    "nara_family_deer_park": {
        "city_code": "nara", "experience_family": "locallife", "rhythm_role": "peak", "energy_level": "medium",
    },
    "osa_kids_science_circuit": {
        "city_code": "osaka", "experience_family": "art", "rhythm_role": "contrast", "energy_level": "low",
    },
    "osa_ramen_street_food": {
        "city_code": "osaka", "experience_family": "food", "rhythm_role": "utility", "energy_level": "low",
    },
    "osa_tsuruhashi_korea_town": {
        "city_code": "osaka", "experience_family": "food", "rhythm_role": "contrast", "energy_level": "medium",
    },
    # kanto_city_circle
    "tok_asakusa_senso_ji": {
        "city_code": "tokyo", "experience_family": "shrine", "rhythm_role": "peak", "energy_level": "medium",
    },
    "tok_shinjuku_shibuya_night": {
        "city_code": "tokyo", "experience_family": "citynight", "rhythm_role": "peak", "energy_level": "medium",
    },
    "tok_yokohama_bayside": {
        "city_code": "yokohama", "experience_family": "sea", "rhythm_role": "contrast", "energy_level": "low",
    },
    # kyushu_onsen_circle
    "kyu_aso_volcano": {
        "experience_family": "mountain", "rhythm_role": "peak", "energy_level": "high",
    },
    "kyu_beppu_onsen": {
        "experience_family": "onsen", "rhythm_role": "recovery", "energy_level": "low",
    },
    "kyu_fukuoka_hakata_food": {
        "experience_family": "food", "rhythm_role": "peak", "energy_level": "medium",
    },
    "kyu_kagoshima_sakurajima": {
        "experience_family": "mountain", "rhythm_role": "peak", "energy_level": "high",
    },
    "kyu_kumamoto_castle": {
        "experience_family": "locallife", "rhythm_role": "contrast", "energy_level": "medium",
    },
    "kyu_nagasaki_history": {
        "experience_family": "locallife", "rhythm_role": "contrast", "energy_level": "medium",
    },
    "kyu_yufuin_village": {
        "experience_family": "onsen", "rhythm_role": "recovery", "energy_level": "low",
    },
    # okinawa_island_circle
    "oki_american_village": {
        "experience_family": "locallife", "rhythm_role": "contrast", "energy_level": "low",
    },
    "oki_cape_manza_sunset": {
        "experience_family": "sea", "rhythm_role": "contrast", "energy_level": "low",
    },
    "oki_churaumi_aquarium": {
        "experience_family": "sea", "rhythm_role": "peak", "energy_level": "medium",
    },
    "oki_kerama_snorkel": {
        "experience_family": "sea", "rhythm_role": "peak", "energy_level": "high",
    },
    "oki_nago_pineapple_park": {
        "experience_family": "locallife", "rhythm_role": "utility", "energy_level": "low",
    },
    "oki_naha_kokusaidori": {
        "experience_family": "locallife", "rhythm_role": "utility", "energy_level": "low",
    },
    "oki_shuri_castle_culture": {
        "experience_family": "locallife", "rhythm_role": "contrast", "energy_level": "medium",
    },
    # osaka_day_base_circle
    "odc_dotonbori_food": {
        "city_code": "osaka",
    },
    "odc_fushimi_daytrip": {
        "city_code": "kyoto",
    },
    "odc_osakajo": {
        "city_code": "osaka",
    },
    "odc_shinsekai": {
        "city_code": "osaka",
    },
    "odc_usj_themepark": {
        "city_code": "osaka",
    },
    # south_china_five_city_circle
    "gz_canton_tower_river_night": {
        "city_code": "guangzhou", "experience_family": "citynight", "rhythm_role": "peak", "energy_level": "low",
    },
    "sz_nanshan_bay_walk": {
        "city_code": "shenzhen", "experience_family": "sea", "rhythm_role": "contrast", "energy_level": "low",
    },
    "sz_window_of_the_world": {
        "city_code": "shenzhen", "experience_family": "themepark", "rhythm_role": "peak", "energy_level": "high",
    },
    # tokyo_metropolitan_circle
    "tok_akihabara_pop_culture": {
        "experience_family": "locallife", "rhythm_role": "contrast", "energy_level": "medium",
    },
    "tok_disney_resort": {
        "experience_family": "themepark", "rhythm_role": "peak", "energy_level": "high",
    },
    "tok_ginza_imperial_palace": {
        "experience_family": "locallife", "rhythm_role": "contrast", "energy_level": "medium",
    },
    "tok_hakone_fuji_day": {
        "experience_family": "mountain", "rhythm_role": "peak", "energy_level": "high",
    },
    "tok_kamakura_enoshima_day": {
        "experience_family": "shrine", "rhythm_role": "peak", "energy_level": "medium",
    },
    "tok_kawaguchiko_fuji_view": {
        "experience_family": "mountain", "rhythm_role": "peak", "energy_level": "high",
    },
    "tok_nikko_world_heritage": {
        "experience_family": "shrine", "rhythm_role": "peak", "energy_level": "high",
    },
    "tok_odaiba_teamlab": {
        "experience_family": "art", "rhythm_role": "contrast", "energy_level": "medium",
    },
    "tok_shibuya_harajuku_fashion": {
        "experience_family": "locallife", "rhythm_role": "contrast", "energy_level": "medium",
    },
    "tok_tsukiji_toyosu_food": {
        "experience_family": "food", "rhythm_role": "utility", "energy_level": "low",
    },
    "tok_ueno_museum_park": {
        "experience_family": "art", "rhythm_role": "recovery", "energy_level": "low",
    },
}


def _score_patch(row: dict) -> int:
    score = 0
    for field in TARGET_FIELDS:
        if row.get(field):
            score += 1
    return score


def load_seed_patches() -> dict[str, dict]:
    patches: dict[str, dict] = {}
    for module_name in SOURCE_MODULES:
        module = importlib.import_module(module_name)
        for attr in ("CLUSTERS", "NEW_CLUSTERS"):
            rows = getattr(module, attr, None)
            if not rows:
                continue
            for row in rows:
                cluster_id = row.get("cluster_id")
                if not cluster_id:
                    continue
                current = patches.get(cluster_id)
                if current is None or _score_patch(row) > _score_patch(current):
                    patches[cluster_id] = {field: row.get(field) for field in TARGET_FIELDS if row.get(field)}

    # kansai 的节奏补丁是现成的，直接吃进来
    kansai_mod = importlib.import_module("scripts.seed_kansai_unified_clusters")
    rhythm_patch = getattr(kansai_mod, "RHYTHM_PATCH", {})
    for cluster_id, row in rhythm_patch.items():
        existing = patches.setdefault(cluster_id, {})
        for field in ("experience_family", "rhythm_role", "energy_level"):
            if row.get(field):
                existing[field] = row[field]

    for cluster_id, row in MANUAL_PATCHES.items():
        existing = patches.setdefault(cluster_id, {})
        for field, value in row.items():
            if value:
                existing[field] = value
    return patches


async def run(circle_id: str | None = None, dry_run: bool = False) -> None:
    patches = load_seed_patches()
    logger.info("加载了 %d 条 cluster patch", len(patches))

    async with AsyncSessionLocal() as session:
        query = select(ActivityCluster).where(ActivityCluster.is_active == True)
        if circle_id:
            query = query.where(ActivityCluster.circle_id == circle_id)
        clusters = list((await session.execute(query)).scalars().all())

        touched = 0
        missing_patch = []
        for cluster in clusters:
            cluster_patch = patches.get(cluster.cluster_id)
            if not cluster_patch:
                needs_work = any(not getattr(cluster, field, None) for field in TARGET_FIELDS)
                if needs_work:
                    missing_patch.append(cluster.cluster_id)
                continue

            updates = {}
            for field in TARGET_FIELDS:
                current = getattr(cluster, field, None)
                new_value = cluster_patch.get(field)
                if (current is None or current == "") and new_value:
                    updates[field] = new_value

            if not updates:
                continue

            touched += 1
            if dry_run:
                logger.info("[DRY] %s -> %s", cluster.cluster_id, updates)
                continue

            for field, value in updates.items():
                setattr(cluster, field, value)
            logger.info("PATCH %s -> %s", cluster.cluster_id, updates)

        if dry_run:
            logger.info("[DRY RUN] 未写库")
        else:
            await session.commit()

        if missing_patch:
            logger.warning("仍有 %d 个缺字段簇没有 patch：%s", len(missing_patch), missing_patch)
        logger.info("完成：%d 个活动簇已补字段", touched)


def main() -> None:
    parser = argparse.ArgumentParser(description="回填 activity_clusters 核心字段")
    parser.add_argument("--circle", help="只处理指定城市圈")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不写库")
    args = parser.parse_args()
    asyncio.run(run(circle_id=args.circle, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
