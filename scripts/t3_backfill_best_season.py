"""
T3: best_season 批量回填
规则推断（不用 AI），从实体名称/类型/cluster seasonality 推断

优先级:
  1. 精确规则（名称关键词 + poi_category）
  2. activity_clusters.seasonality 继承
  3. 其余标 all

运行: python scripts/t3_backfill_best_season.py [--dry-run]
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import argparse
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ─── 关键词规则 (按特异性从高到低排列，先匹配先赢) ─────────────────────────────
KEYWORD_RULES = [
    # winter 特征
    (r"雪|snow|スキー|ski|流氷|drift.?ice|アイス|ice|ゲレンデ|冰|冬", "winter"),
    # summer 特征
    (r"ラベンダー|lavender|花畑|flower|ひまわり|sunflower|サンフラワー|ガーデン|garden|夏祭|夏まつり|summer", "summer"),
    # autumn 特征
    (r"紅葉|紅叶|もみじ|autumn|red.?leaf|秋|koyo", "autumn"),
    # spring 特征
    (r"桜|さくら|sakura|cherry|梅|ume|spring|花見|はなみ", "spring"),
]

# poi_category → season (onsen/museum/etc. 全年可去)
CATEGORY_SEASON = {
    "ski":          "winter",
    "ski_resort":   "winter",
    "onsen":        "all",
    "museum":       "all",
    "shrine":       "all",
    "temple":       "all",
    "landmark":     "all",
    "specialty_shop": "all",
    "park":         "all",
    "aquarium":     "all",
    "zoo":          "all",
}

# 合法的 best_season 枚举值
VALID_SEASONS = {"spring", "summer", "autumn", "winter", "all"}


def infer_season_from_name(name: str) -> str | None:
    """从名称关键词推断季节"""
    if not name:
        return None
    combined = name.lower()
    for pattern, season in KEYWORD_RULES:
        if re.search(pattern, combined, re.IGNORECASE):
            return season
    return None


def infer_season_from_category(poi_category: str) -> str | None:
    """从 poi_category 推断季节"""
    return CATEGORY_SEASON.get(poi_category)


def parse_cluster_seasonality(seasonality) -> str | None:
    """解析 activity_clusters.seasonality (可能是 JSON 数组或字符串)"""
    if not seasonality:
        return None
    if isinstance(seasonality, list):
        vals = seasonality
    elif isinstance(seasonality, str):
        s = seasonality.strip()
        if s.startswith("["):
            try:
                vals = json.loads(s)
            except Exception:
                vals = [s]
        else:
            vals = [s]
    else:
        return None

    # 映射常见值
    season_map = {
        "winter_only": "winter", "winter": "winter",
        "summer_only": "summer", "summer": "summer",
        "spring": "spring", "autumn": "autumn", "fall": "autumn",
        "all_year": "all", "year_round": "all", "all": "all",
    }
    for v in vals:
        v_lower = str(v).strip().lower()
        if v_lower in season_map:
            return season_map[v_lower]
        if v_lower in VALID_SEASONS:
            return v_lower
    return None


async def build_cluster_season_map(session) -> dict[str, str]:
    """构建 entity_id → season（从 circle_entity_roles + cluster seasonality 继承）"""
    r = await session.execute(text("""
        SELECT cer.entity_id::text, ac.seasonality
        FROM circle_entity_roles cer
        JOIN activity_clusters ac ON ac.cluster_id = cer.cluster_id
        WHERE ac.is_active = true
          AND ac.seasonality IS NOT NULL
          AND cer.entity_id IS NOT NULL
    """))
    entity_season = {}
    for row in r.fetchall():
        entity_id = row[0]
        season = parse_cluster_seasonality(row[1])
        if season and entity_id not in entity_season:
            entity_season[entity_id] = season
    return entity_season


async def main(dry_run: bool = False) -> None:
    async with AsyncSessionLocal() as session:
        # 验证前状态
        r_before = await session.execute(text(
            "SELECT COUNT(CASE WHEN best_season IS NOT NULL THEN 1 END), COUNT(*) FROM pois"
        ))
        row = r_before.fetchone()
        print(f"Before: {row[0]}/{row[1]} pois have best_season")

        # 拉所有 pois（含名称和 poi_category）
        r_pois = await session.execute(text("""
            SELECT p.entity_id::text, p.best_season, p.poi_category,
                   eb.name_zh, eb.name_ja, eb.name_en
            FROM pois p
            JOIN entity_base eb ON eb.entity_id = p.entity_id
            WHERE eb.is_active = true
        """))
        pois = r_pois.fetchall()
        print(f"Total active pois: {len(pois)}")

        # 构建 cluster 继承 map
        cluster_season_map = await build_cluster_season_map(session)
        print(f"Cluster season map: {len(cluster_season_map)} entities")

        updated = skipped = already_valid = 0
        reason_counts: dict[str, int] = {}

        for entity_id, current_season, poi_category, name_zh, name_ja, name_en in pois:
            # 如果已有合法值，跳过
            if current_season and current_season.strip() in VALID_SEASONS:
                already_valid += 1
                continue

            # 推断逻辑
            season = None
            reason = None

            # 1. 名称关键词 (优先用日文名)
            for name in [name_ja or "", name_zh or "", name_en or ""]:
                season = infer_season_from_name(name)
                if season:
                    reason = "name_keyword"
                    break

            # 2. poi_category
            if not season and poi_category:
                season = infer_season_from_category(poi_category)
                if season:
                    reason = "poi_category"

            # 3. cluster 继承
            if not season and entity_id in cluster_season_map:
                season = cluster_season_map[entity_id]
                reason = "cluster_inherit"

            # 4. 兜底
            if not season:
                season = "all"
                reason = "default"

            reason_counts[reason] = reason_counts.get(reason, 0) + 1

            if dry_run:
                updated += 1
                continue

            await session.execute(text("""
                UPDATE pois SET best_season = :season
                WHERE entity_id = CAST(:eid AS uuid)
            """), {"season": season, "eid": entity_id})
            updated += 1

            if updated % 100 == 0:
                await session.flush()

        if not dry_run:
            await session.commit()

        print(f"\nResult: updated={updated}, already_valid={already_valid}, skipped={skipped}")
        print(f"Reason breakdown: {reason_counts}")

        if not dry_run:
            r_after = await session.execute(text(
                "SELECT best_season, COUNT(*) FROM pois GROUP BY best_season ORDER BY COUNT(*) DESC"
            ))
            print("\n=== After distribution ===")
            for row in r_after.fetchall():
                print(f"  {row[0]}: {row[1]}")

            r_null = await session.execute(text(
                "SELECT COUNT(*) FROM pois WHERE best_season IS NULL"
            ))
            null_count = r_null.scalar()
            if null_count < 100:
                print(f"\n[PASS] Verification: only {null_count} NULL best_season")
            else:
                print(f"\n[WARN] Verification: {null_count} NULL best_season (target < 100)")

        print("\n[OK] T3 DONE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
