"""
seed_kansai_extended_circles.py — 扩充关西活动簇
新增 12 个活动簇，覆盖：
  - 宇治日归（平等院·宇治上神社）
  - 京都枯山水庭园线（龙安寺·大德寺·东福寺）
  - 桂离宫·现代建筑线
  - 京都深度哲学之道延伸（永观堂·真如堂）
  - 奈良深度线（春日大社·兴福寺·新药师寺）
  - 神户半日归（北野异人馆·南京町·旧居留地）
  - 京都伏见酒藏散步
  - 大阪中之岛·天满桥文化线
  - 京都西阵·二条城线
  - 有马温泉日归
  - 姬路城日归
  - 大阪海游馆·天保山线（家庭向）

执行：
    cd D:/projects/projects/travel-ai
    python scripts/seed_kansai_extended_circles.py

幂等：cluster_id 已存在则 SKIP。
"""
from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.session import AsyncSessionLocal
from app.db.models.city_circles import ActivityCluster

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# ── 新增活动簇 ───────────────────────────────────────────────────────────────

NEW_CLUSTERS = [
    # ── 宇治日归 ──────────────────────────────────────────────────────────────
    {
        "cluster_id": "kyo_uji_day_trip",
        "circle_id": "kansai_classic_circle",
        "city_code": "uji",
        "name_zh": "宇治日归（平等院·宇治上神社·中村藤吉）",
        "name_en": "Uji Day Trip – Byodoin & Uji Kami Shrine",
        "level": "A",
        "default_duration": "full_day",
        "duration_range_days": "0.8-1.0",
        "primary_corridor": "uji",
        "core_visit_minutes": 300,
        "queue_buffer_minutes": 30,
        "photo_buffer_minutes": 30,
        "meal_buffer_minutes": 60,
        "fatigue_weight": 0.9,
        "queue_risk_level": "low",
        "photo_intensity": "high",
        "best_time_window": "09:00-16:00",
        "seasonality": ["all_year", "sakura", "autumn_leaves"],
        "profile_fit": ["architecture", "culture", "photo", "couple", "solo"],
        "trip_role": "anchor",
        "can_drive_hotel": False,
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 0,
        "default_selected": False,
        "notes": "平等院凤凰堂（世界遗产）+宇治上神社（最古老神社）+中村藤吉抹茶。从京都20分，从大阪45分。建筑爱好者必去。",
        "upgrade_triggers": {"tags": ["architecture", "culture", "nature"], "party_types": ["couple", "solo"]},
        "is_active": True,
    },
    # ── 枯山水庭园线 ──────────────────────────────────────────────────────────
    {
        "cluster_id": "kyo_zen_garden_circuit",
        "circle_id": "kansai_classic_circle",
        "city_code": "kyoto",
        "name_zh": "京都·枯山水庭园线（龙安寺·大德寺·东福寺）",
        "name_en": "Kyoto Zen Garden Circuit – Ryoanji, Daitokuji, Tofukuji",
        "level": "A",
        "default_duration": "full_day",
        "duration_range_days": "0.8-1.0",
        "primary_corridor": "kyo_zen_garden",
        "core_visit_minutes": 300,
        "queue_buffer_minutes": 15,
        "photo_buffer_minutes": 60,
        "meal_buffer_minutes": 0,
        "fatigue_weight": 0.8,
        "queue_risk_level": "low",
        "photo_intensity": "extreme",
        "best_time_window": "08:00-15:00",
        "seasonality": ["all_year", "autumn_leaves"],
        "profile_fit": ["architecture", "culture", "solo", "photo", "zen"],
        "trip_role": "anchor",
        "can_drive_hotel": False,
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "龙安寺枯山水石庭（世界遗产）+ 大德寺塔头庭园 + 东福寺通天桥（红叶极品）。小众精华，建筑/禅意爱好者强推。",
        "upgrade_triggers": {"tags": ["architecture", "culture", "zen", "nature"], "party_types": ["solo"]},
        "is_active": True,
    },
    # ── 桂离宫·现代建筑线 ────────────────────────────────────────────────────
    {
        "cluster_id": "kyo_katsura_modern_arch",
        "circle_id": "kansai_classic_circle",
        "city_code": "kyoto",
        "name_zh": "京都·桂离宫+现代建筑线（京都站大楼·陶板名画之庭）",
        "name_en": "Kyoto Katsura Rikyu & Modern Architecture",
        "level": "B",
        "default_duration": "full_day",
        "duration_range_days": "0.8-1.0",
        "primary_corridor": "kyo_nishikyo",
        "core_visit_minutes": 240,
        "queue_buffer_minutes": 0,
        "photo_buffer_minutes": 60,
        "meal_buffer_minutes": 0,
        "fatigue_weight": 0.8,
        "queue_risk_level": "none",
        "photo_intensity": "extreme",
        "best_time_window": "10:00-15:00",
        "seasonality": ["all_year"],
        "profile_fit": ["architecture", "culture", "solo"],
        "trip_role": "anchor",
        "can_drive_hotel": False,
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "桂离宫（需宫内厅提前预约）+京都站大楼（原广司，城市中轴建筑）+陶板名画之庭（安藤忠雄，免费）。纯建筑线路。",
        "upgrade_triggers": {"tags": ["architecture"], "party_types": ["solo"]},
        "is_active": True,
    },
    # ── 永观堂·真如堂红叶线 ──────────────────────────────────────────────────
    {
        "cluster_id": "kyo_eikando_shinnyodo",
        "circle_id": "kansai_classic_circle",
        "city_code": "kyoto",
        "name_zh": "京都·永观堂·真如堂红叶深度线",
        "name_en": "Kyoto Eikando & Shinnyodo Autumn Leaves",
        "level": "A",
        "default_duration": "half_day",
        "duration_range_days": "0.5-0.7",
        "primary_corridor": "kyo_okazaki",
        "core_visit_minutes": 180,
        "queue_buffer_minutes": 30,
        "photo_buffer_minutes": 60,
        "meal_buffer_minutes": 0,
        "fatigue_weight": 0.9,
        "queue_risk_level": "medium",
        "photo_intensity": "extreme",
        "best_time_window": "08:00-11:00",
        "seasonality": ["autumn_leaves", "all_year"],
        "profile_fit": ["photo", "culture", "couple", "solo", "nature"],
        "trip_role": "enrichment",
        "can_drive_hotel": False,
        "time_window_strength": "medium",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "永观堂（京都红叶第一名所）+ 真如堂（本堂前三重塔红叶极美）。搭配哲学之道为全天秋叶线路。",
        "upgrade_triggers": {"tags": ["photo", "nature", "autumn_leaves"], "party_types": ["couple", "solo"]},
        "is_active": True,
    },
    # ── 西芳寺（苔寺）预约线 ─────────────────────────────────────────────────
    {
        "cluster_id": "kyo_saihoji_moss_temple",
        "circle_id": "kansai_classic_circle",
        "city_code": "kyoto",
        "name_zh": "京都·西芳寺（苔寺）",
        "name_en": "Kyoto Saihoji (Moss Temple)",
        "level": "B",
        "default_duration": "half_day",
        "duration_range_days": "0.4-0.5",
        "primary_corridor": "kyo_arashiyama",
        "core_visit_minutes": 120,
        "queue_buffer_minutes": 0,
        "photo_buffer_minutes": 30,
        "meal_buffer_minutes": 0,
        "fatigue_weight": 0.7,
        "queue_risk_level": "none",
        "photo_intensity": "extreme",
        "best_time_window": "10:00-12:00",
        "seasonality": ["all_year", "sakura", "autumn_leaves"],
        "profile_fit": ["architecture", "culture", "solo", "photo", "nature"],
        "trip_role": "enrichment",
        "can_drive_hotel": False,
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 0,
        "default_selected": False,
        "notes": "世界遗产，必须提前网络预约（每日限额120人）。120种苔藓覆盖的梦幻庭园，建筑/园林爱好者毕生愿望。",
        "upgrade_triggers": {"tags": ["architecture", "nature", "garden"], "party_types": ["solo", "couple"]},
        "is_active": True,
    },
    # ── 奈良深度线 ───────────────────────────────────────────────────────────
    {
        "cluster_id": "nara_deep_kasuga_kofuku",
        "circle_id": "kansai_classic_circle",
        "city_code": "nara",
        "name_zh": "奈良深度（春日大社·兴福寺·新药师寺）",
        "name_en": "Nara Deep – Kasuga Taisha, Kofukuji, Shinyakushiji",
        "level": "B",
        "default_duration": "full_day",
        "duration_range_days": "0.8-1.0",
        "primary_corridor": "nara_park",
        "core_visit_minutes": 300,
        "queue_buffer_minutes": 10,
        "photo_buffer_minutes": 30,
        "meal_buffer_minutes": 60,
        "fatigue_weight": 1.0,
        "queue_risk_level": "low",
        "photo_intensity": "high",
        "best_time_window": "08:00-16:00",
        "seasonality": ["all_year", "sakura", "autumn_leaves"],
        "profile_fit": ["culture", "history", "solo", "couple", "nature"],
        "trip_role": "anchor",
        "can_drive_hotel": False,
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "春日大社（世界遗产，2000盏石灯笼）+兴福寺五重塔+新药师寺（奈良时代本物）。比普通奈良游深3倍。",
        "upgrade_triggers": {"tags": ["culture", "history", "nature"], "party_types": ["solo", "couple"]},
        "is_active": True,
    },
    # ── 神户半日/一日线 ──────────────────────────────────────────────────────
    {
        "cluster_id": "kobe_kitano_nankinmachi",
        "circle_id": "kansai_classic_circle",
        "city_code": "kobe",
        "name_zh": "神户·北野异人馆+南京町+旧居留地",
        "name_en": "Kobe Kitano Ijinkan & Nankinmachi",
        "level": "B",
        "default_duration": "full_day",
        "duration_range_days": "0.8-1.0",
        "primary_corridor": "kobe_kitano",
        "core_visit_minutes": 240,
        "queue_buffer_minutes": 20,
        "photo_buffer_minutes": 30,
        "meal_buffer_minutes": 60,
        "fatigue_weight": 1.0,
        "queue_risk_level": "low",
        "photo_intensity": "medium",
        "best_time_window": "10:00-17:00",
        "seasonality": ["all_year"],
        "profile_fit": ["couple", "friends", "culture", "food", "photo"],
        "trip_role": "anchor",
        "can_drive_hotel": False,
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "北野異人館街（西洋建筑群）+南京町（神户中华街）+旧居留地（明治西洋建筑）。从大阪30分/京都55分。港口城市异国风情。",
        "upgrade_triggers": {"tags": ["culture", "food", "architecture"], "party_types": ["couple", "friends"]},
        "is_active": True,
    },
    # ── 伏见酒藏散步 ─────────────────────────────────────────────────────────
    {
        "cluster_id": "kyo_fushimi_sake_town",
        "circle_id": "kansai_classic_circle",
        "city_code": "kyoto",
        "name_zh": "京都·伏见酒藏街·月桂冠大仓纪念馆",
        "name_en": "Kyoto Fushimi Sake District",
        "level": "B",
        "default_duration": "half_day",
        "duration_range_days": "0.4-0.5",
        "primary_corridor": "kyo_fushimi",
        "core_visit_minutes": 120,
        "queue_buffer_minutes": 10,
        "photo_buffer_minutes": 20,
        "meal_buffer_minutes": 30,
        "fatigue_weight": 0.8,
        "queue_risk_level": "low",
        "photo_intensity": "medium",
        "best_time_window": "10:00-15:00",
        "seasonality": ["all_year", "sakura", "autumn_leaves"],
        "profile_fit": ["solo", "couple", "food", "culture"],
        "trip_role": "buffer",
        "can_drive_hotel": False,
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "月桂冠大仓纪念馆（日本酒博物馆） + 十石舟游船 + 寺田屋。可与伏见稻荷合并为全天线路。",
        "is_active": True,
    },
    # ── 大阪中之岛·天满文化线 ────────────────────────────────────────────────
    {
        "cluster_id": "osa_nakanoshima_temma",
        "circle_id": "kansai_classic_circle",
        "city_code": "osaka",
        "name_zh": "大阪·中之岛+天满桥文化线",
        "name_en": "Osaka Nakanoshima & Temmabashi Culture",
        "level": "B",
        "default_duration": "half_day",
        "duration_range_days": "0.3-0.5",
        "primary_corridor": "osa_nakanoshima",
        "core_visit_minutes": 120,
        "queue_buffer_minutes": 0,
        "photo_buffer_minutes": 20,
        "meal_buffer_minutes": 60,
        "fatigue_weight": 0.8,
        "queue_risk_level": "none",
        "photo_intensity": "medium",
        "best_time_window": "11:00-18:00",
        "seasonality": ["all_year", "sakura"],
        "profile_fit": ["solo", "couple", "food", "culture", "architecture"],
        "trip_role": "buffer",
        "can_drive_hotel": True,
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "中之岛公园（春季郁金香）+ 大阪市中央公会堂（辰野金吾设计） + 天满桥商店街午饭。文化密度高的半天线。",
        "is_active": True,
    },
    # ── 京都西阵·二条城线 ────────────────────────────────────────────────────
    {
        "cluster_id": "kyo_nijo_nishijin",
        "circle_id": "kansai_classic_circle",
        "city_code": "kyoto",
        "name_zh": "京都·二条城+西阵织会馆",
        "name_en": "Kyoto Nijo Castle & Nishijin",
        "level": "A",
        "default_duration": "half_day",
        "duration_range_days": "0.4-0.6",
        "primary_corridor": "kyo_nijo",
        "core_visit_minutes": 150,
        "queue_buffer_minutes": 20,
        "photo_buffer_minutes": 20,
        "meal_buffer_minutes": 0,
        "fatigue_weight": 1.0,
        "queue_risk_level": "medium",
        "photo_intensity": "high",
        "best_time_window": "09:00-15:00",
        "seasonality": ["all_year", "sakura", "autumn_leaves"],
        "profile_fit": ["first_timer", "culture", "history", "couple"],
        "trip_role": "enrichment",
        "can_drive_hotel": False,
        "time_window_strength": "medium",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "二条城（世界遗产，德川幕府大政奉还之地）+ 西阵织会馆（传统纺织工艺展示/体验）。适合文化爱好者。",
        "experience_family": "locallife",
        "rhythm_role": "contrast",
        "energy_level": "medium",
        "upgrade_triggers": {"tags": ["culture", "history", "architecture"], "party_types": ["couple"]},
        "is_active": True,
    },
    # ── 有马温泉日归 ─────────────────────────────────────────────────────────
    {
        "cluster_id": "arima_onsen_day_trip",
        "circle_id": "kansai_classic_circle",
        "city_code": "arima_onsen",
        "name_zh": "有马温泉日归（金汤·银汤·炭酸源泉）",
        "name_en": "Arima Onsen Day Trip",
        "level": "B",
        "default_duration": "full_day",
        "duration_range_days": "0.8-1.0",
        "primary_corridor": "arima",
        "core_visit_minutes": 240,
        "queue_buffer_minutes": 30,
        "photo_buffer_minutes": 15,
        "meal_buffer_minutes": 60,
        "fatigue_weight": 0.6,
        "queue_risk_level": "medium",
        "photo_intensity": "low",
        "best_time_window": "10:00-17:00",
        "seasonality": ["all_year", "autumn_leaves"],
        "profile_fit": ["couple", "solo", "family_multi_gen", "relaxed"],
        "trip_role": "anchor",
        "can_drive_hotel": False,
        "time_window_strength": "weak",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 0,
        "default_selected": False,
        "notes": "日本最古老温泉地之一，金汤（含铁碳酸盐）极为稀有。从神户35分/大阪60分。三代同行/情侣强推。",
        "upgrade_triggers": {"tags": ["onsen", "relaxed"], "party_types": ["couple", "family_multi_gen"]},
        "is_active": True,
    },
    # ── 大阪海游馆·天保山（家庭向） ─────────────────────────────────────────
    {
        "cluster_id": "osa_kaiyukan_tempozan",
        "circle_id": "kansai_classic_circle",
        "city_code": "osaka",
        "name_zh": "大阪·海游馆+天保山摩天轮",
        "name_en": "Osaka Kaiyukan Aquarium & Tempozan",
        "level": "A",
        "default_duration": "full_day",
        "duration_range_days": "0.8-1.0",
        "primary_corridor": "osa_sakurajima",
        "core_visit_minutes": 300,
        "queue_buffer_minutes": 45,
        "photo_buffer_minutes": 20,
        "meal_buffer_minutes": 60,
        "fatigue_weight": 1.0,
        "queue_risk_level": "high",
        "photo_intensity": "medium",
        "best_time_window": "10:00-17:00",
        "seasonality": ["all_year"],
        "profile_fit": ["family_child", "couple", "friends"],
        "trip_role": "anchor",
        "can_drive_hotel": False,
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 0,
        "default_selected": False,
        "notes": "世界最大级水族馆（鲸鲨展缸）+ 天保山大观览车。家庭游强推，小孩必爱。从难波地铁20分。",
        "upgrade_triggers": {"tags": ["kids", "family"], "party_types": ["family_child"]},
        "is_active": True,
    },
]


async def seed():
    async with AsyncSessionLocal() as session:
        new_count = skip_count = 0
        for data in NEW_CLUSTERS:
            existing = await session.get(ActivityCluster, data["cluster_id"])
            if existing:
                skip_count += 1
                logger.info("  SKIP cluster: %s", data["cluster_id"])
                continue
            cluster = ActivityCluster(**data)
            session.add(cluster)
            new_count += 1
            logger.info("  NEW  cluster: %s", data["cluster_id"])
        await session.commit()
        logger.info("✅ 活动簇扩充完成: 新建=%d 跳过=%d", new_count, skip_count)


if __name__ == "__main__":
    asyncio.run(seed())
