"""
片段攻略库种子数据 — tokyo_classic 8 条
对应 L21，可通过 python -m app.db.seed.fragments_seed 导入

执行方式（本地）：
  python -m app.db.seed.fragments_seed

执行方式（Docker）：
  docker compose exec backend python -m app.db.seed.fragments_seed
"""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.models.fragments import GuideFragment, FragmentUsageStats

logger = logging.getLogger(__name__)

# ── 种子数据 ─────────────────────────────────────────────────────────────────

FRAGMENTS: list[dict] = [
    # ─ 1. 浅草经典半日（上午）─────────────────────────────────────────────
    {
        "fragment_type": "route",
        "title": "浅草经典上午：雷门 → 仲见世通 → 浅草寺",
        "summary": "浅草最标志性的半日路线，从雷门打卡开始，经仲见世通买传统小食，到浅草寺参拜。人少时段在开门后 1 小时内。",
        "city_code": "tokyo",
        "area_code": "asakusa",
        "theme_families": ["classic_first", "culture_deep"],
        "party_types": ["couple", "solo", "family_no_kids", "friends"],
        "budget_levels": ["budget", "mid", "premium"],
        "season_tags": ["all_year", "spring", "autumn"],
        "day_index_hint": None,
        "duration_slot": "morning",
        "body_skeleton": {
            "duration_hours": 3,
            "start_time_suggest": "09:00",
            "stops": [
                {"order": 1, "name": "雷门", "duration_min": 20, "tip": "站在对面马路拍全景，比正门前更好看"},
                {"order": 2, "name": "仲见世通", "duration_min": 40, "tip": "左边第三家揚げまんじゅう必吃，¥150/个"},
                {"order": 3, "name": "浅草寺本堂", "duration_min": 30, "tip": "取签可以多拿几次，凶签不用担心放回去就好"},
                {"order": 4, "name": "二天门·传法院通", "duration_min": 30, "tip": "游客较少的古朴小街，有很多昭和风小店"}
            ],
            "transport": "出发：任一地铁线到浅草站 / 结束：可步行至上野（约 20 分钟）",
            "budget_estimate": "¥0-300（门票免费，小食自选）"
        },
        "quality_score": 8.5,
        "source_type": "manual",
        "status": "active",
        "is_active": True,
    },
    # ─ 2. 上野公园 + 博物馆上午 ──────────────────────────────────────────
    {
        "fragment_type": "route",
        "title": "上野：公园 + 国立博物馆上午游",
        "summary": "早上 9 点进入上野公园，先走不忍池，再进东京国立博物馆精华展厅，午前结束。春天加樱花道，秋天加银杏道。",
        "city_code": "tokyo",
        "area_code": "ueno",
        "theme_families": ["classic_first", "culture_deep"],
        "party_types": ["couple", "solo", "family_no_kids", "senior"],
        "budget_levels": ["budget", "mid"],
        "season_tags": ["spring", "autumn", "all_year"],
        "day_index_hint": None,
        "duration_slot": "morning",
        "body_skeleton": {
            "duration_hours": 3.5,
            "start_time_suggest": "09:00",
            "stops": [
                {"order": 1, "name": "上野恩赐公园 入口", "duration_min": 15, "tip": "从 JR 上野站公园口出，步行 1 分钟"},
                {"order": 2, "name": "不忍池", "duration_min": 30, "tip": "荷花期（7-8月）或樱花期（3-4月）最美，秋冬也有候鸟"},
                {"order": 3, "name": "东京国立博物馆 本馆", "duration_min": 90, "tip": "重点看 2F 日本刀剑 + 3F 江户时代绘画；门票 ¥1000"},
                {"order": 4, "name": "上野动物园入口（可选）", "duration_min": 0, "tip": "带孩子可加，¥600/人，熊猫馆需网上预约"}
            ],
            "transport": "JR 上野站公园口 / 东京地铁上野站",
            "budget_estimate": "¥1000-1500（博物馆 ¥1000 + 小食）"
        },
        "quality_score": 8.2,
        "source_type": "manual",
        "status": "active",
        "is_active": True,
    },
    # ─ 3. 新宿下午购物 ───────────────────────────────────────────────────
    {
        "fragment_type": "route",
        "title": "新宿下午：药妆 + 唐吉诃德 + 黄金街",
        "summary": "新宿标准购物下午路线：从东口药妆店扫货，到唐吉诃德挖免税折扣，黄金街傍晚开始有气氛，适合新宿住宿的行程。",
        "city_code": "tokyo",
        "area_code": "shinjuku",
        "theme_families": ["shopping_first", "classic_first"],
        "party_types": ["couple", "friends", "solo"],
        "budget_levels": ["budget", "mid", "premium"],
        "season_tags": ["all_year"],
        "day_index_hint": None,
        "duration_slot": "afternoon",
        "body_skeleton": {
            "duration_hours": 4,
            "start_time_suggest": "14:00",
            "stops": [
                {"order": 1, "name": "新宿东口药妆一条街", "duration_min": 60, "tip": "松本清/大国药妆/Sundrug，价格比较后再买"},
                {"order": 2, "name": "唐吉诃德新宿歌舞伎町店", "duration_min": 60, "tip": "4F 美妆，B1 零食伴手礼，退税台在 1F"},
                {"order": 3, "name": "新宿御苑（可选）", "duration_min": 60, "tip": "樱花/玫瑰期必去，门票 ¥500，平时可跳过"},
                {"order": 4, "name": "黄金街（ゴールデン街）", "duration_min": 60, "tip": "200 多家只有 5-8 席的迷你酒吧，傍晚 18 点后开"},
            ],
            "transport": "JR 新宿站各出口 / 丸ノ内線・都営新宿線",
            "budget_estimate": "¥0（逛）/ 购物按需"
        },
        "quality_score": 7.8,
        "source_type": "manual",
        "status": "active",
        "is_active": True,
    },
    # ─ 4. 涩谷夜晚 ───────────────────────────────────────────────────────
    {
        "fragment_type": "experience",
        "title": "涩谷夜晚：交叉路口 + Sky 展望台 + 飞鸟山夜景",
        "summary": "涩谷经典夜晚安排：黄昏拍交叉路口，登 Shibuya Sky 看 360° 东京夜景，结束去渋谷横丁吃居酒屋。",
        "city_code": "tokyo",
        "area_code": "shibuya",
        "theme_families": ["couple_aesthetic", "classic_first", "night_crawler"],
        "party_types": ["couple", "friends", "solo"],
        "budget_levels": ["mid", "premium"],
        "season_tags": ["all_year"],
        "day_index_hint": None,
        "duration_slot": "evening",
        "body_skeleton": {
            "duration_hours": 3.5,
            "start_time_suggest": "17:30",
            "stops": [
                {"order": 1, "name": "涩谷十字路口（忠犬ハチ公前）", "duration_min": 30, "tip": "日落前 30 分钟站在星巴克 2F 拍最好看"},
                {"order": 2, "name": "Shibuya Sky（渋谷スカイ）", "duration_min": 75, "tip": "提前官网订票 ¥2000，最后入场 22:30；日落后约 1.5h 最美"},
                {"order": 3, "name": "渋谷横丁", "duration_min": 60, "tip": "8 个地域风格的居酒屋集合，人均 ¥2000-3000，不需要预约"}
            ],
            "transport": "JR/东急/地铁 渋谷站直连",
            "budget_estimate": "¥2000-5000（展望台 ¥2000 + 居酒屋 ¥2000-3000）"
        },
        "quality_score": 8.8,
        "source_type": "manual",
        "status": "active",
        "is_active": True,
    },
    # ─ 5. 镰仓一日 ───────────────────────────────────────────────────────
    {
        "fragment_type": "route",
        "title": "镰仓一日：高德院大佛 → 长谷寺 → 江之电 → 极乐寺 → 七里滨",
        "summary": "东京出发的经典一日郊游，镰仓大佛、江之电海岸线、七里滨咖啡，动漫（灌篮高手）圣地巡礼与自然海景的完美组合。",
        "city_code": "tokyo",
        "area_code": "kamakura",
        "theme_families": ["classic_first", "anime_otaku", "couple_aesthetic"],
        "party_types": ["couple", "friends", "solo"],
        "budget_levels": ["budget", "mid"],
        "season_tags": ["spring", "summer", "autumn"],
        "day_index_hint": None,
        "duration_slot": "full_day",
        "body_skeleton": {
            "duration_hours": 10,
            "start_time_suggest": "08:30",
            "stops": [
                {"order": 1, "name": "出发：新宿/品川→镰仓（JR 横須賀線）", "duration_min": 60, "tip": "避开 9-10 点通勤高峰，8:30 出发最好"},
                {"order": 2, "name": "高德院 镰仓大佛", "duration_min": 60, "tip": "门票 ¥300，可进入大佛内部；早上人少"},
                {"order": 3, "name": "长谷寺（紫阳花/红叶时必去）", "duration_min": 60, "tip": "门票 ¥400，6月绣球花和11月红叶最美"},
                {"order": 4, "name": "乘江之电→极乐寺站", "duration_min": 20, "tip": "江之电一日券 ¥700 合算"},
                {"order": 5, "name": "极乐寺站→七里滨海岸", "duration_min": 30, "tip": "灌篮高手「湘南の海」取景地就在附近的镰倉高校前駅"},
                {"order": 6, "name": "七里滨 bills（早午餐 or 下午茶）", "duration_min": 90, "tip": "需预约，海景 pancake ¥2200，日落时段最美"}
            ],
            "transport": "JR 横须贺线 东京/品川→镰仓（约 55 分钟），回程同路",
            "budget_estimate": "¥3000-5000（交通 ¥2000 + 门票 ¥700 + 餐饮 ¥2000）"
        },
        "quality_score": 9.0,
        "source_type": "manual",
        "status": "active",
        "is_active": True,
    },
    # ─ 6. 东京精品和食晚餐决策 ──────────────────────────────────────────
    {
        "fragment_type": "dining",
        "title": "东京精品和食晚餐选择：人均 ¥5000-15000 区间指南",
        "summary": "针对希望体验正式和食但不想踩雷的用户。分寿司/天妇罗/烧肉三条路线，每类给出稳定高性价比选择和预约建议。",
        "city_code": "tokyo",
        "area_code": None,
        "theme_families": ["gourmet_focus", "classic_first"],
        "party_types": ["couple", "family_no_kids", "solo"],
        "budget_levels": ["premium", "luxury"],
        "season_tags": ["all_year"],
        "day_index_hint": None,
        "duration_slot": "evening",
        "body_skeleton": {
            "duration_hours": 2,
            "options": [
                {
                    "type": "寿司",
                    "name": "根室花まる（丸之内）",
                    "budget": "¥3000-6000/人",
                    "tip": "性价比最高的回转寿司；工作日午餐等候约 30 分钟，晚餐需官网整理券",
                    "reservation": "当日 10:00 开放网上取号"
                },
                {
                    "type": "天妇罗",
                    "name": "天一（银座 or 新宿）",
                    "budget": "¥8000-15000/人",
                    "tip": "老牌天妇罗名店，套餐精准有序，适合想体验 omakase 节奏但不想太贵",
                    "reservation": "提前 2 周 TabeLog/官网"
                },
                {
                    "type": "烧肉",
                    "name": "叙叙苑（各地有分店）",
                    "budget": "¥5000-8000/人",
                    "tip": "日本和牛连锁中口碑最稳定，午餐套餐性价比高于晚餐",
                    "reservation": "官网或电话，建议提前 3 天"
                }
            ]
        },
        "quality_score": 8.0,
        "source_type": "manual",
        "status": "active",
        "is_active": True,
    },
    # ─ 7. 东京地铁实用贴士 ──────────────────────────────────────────────
    {
        "fragment_type": "tips",
        "title": "东京地铁新手必知：换乘/IC卡/通票选择",
        "summary": "东京地铁体系复杂，本片段梳理最常用的 3 个换乘枢纽、IC 卡使用场景、地铁通票是否合算的判断逻辑。",
        "city_code": "tokyo",
        "area_code": None,
        "theme_families": ["classic_first", "budget_focus"],
        "party_types": ["solo", "couple", "friends", "family_no_kids", "family_with_kids", "senior"],
        "budget_levels": ["budget", "mid", "premium"],
        "season_tags": ["all_year"],
        "day_index_hint": 0,
        "duration_slot": None,
        "body_skeleton": {
            "tips": [
                {"topic": "必备 IC 卡", "content": "Suica（JR）或 PASMO（地铁）均可，iPhone 用 Mobile Suica 更方便；充 ¥3000 够 3 天"},
                {"topic": "3 大换乘枢纽", "content": "新宿（JR+小田急+京王+地铁）/ 渋谷（JR+东急+地铁）/ 池袋（JR+西武+东武+地铁）"},
                {"topic": "地铁 24h 券是否合算", "content": "¥600/天，单次 ¥200-250；住新宿/涩谷/浅草密集游才合算，否则 IC 卡更划算"},
                {"topic": "别在高峰坐地铁", "content": "7:30-9:30 / 17:30-19:30 是通勤高峰，建议晚 30 分钟出发，挤不下的感觉很不好"},
                {"topic": "Google Maps 导航", "content": "选「Transit」模式，东京地铁实时数据准确，不用死记路线图"},
            ]
        },
        "quality_score": 8.3,
        "source_type": "manual",
        "status": "active",
        "is_active": True,
    },
    # ─ 8. 成田/羽田机场到市区交通决策 ──────────────────────────────────
    {
        "fragment_type": "logistics",
        "title": "成田/羽田机场到东京市区：4 种方式对比",
        "summary": "机场到市区是新手最容易踩坑的环节。对比 Narita Express/利木津巴士/京成线/出租车，给出最优决策树。",
        "city_code": "tokyo",
        "area_code": None,
        "theme_families": ["classic_first", "budget_focus"],
        "party_types": ["solo", "couple", "friends", "family_no_kids", "family_with_kids", "senior"],
        "budget_levels": ["budget", "mid", "premium"],
        "season_tags": ["all_year"],
        "day_index_hint": 0,
        "duration_slot": None,
        "body_skeleton": {
            "airport": "narita",
            "options": [
                {
                    "name": "成田 Express（N'EX）",
                    "time": "约 60 分钟到新宿/品川",
                    "cost": "¥3070（单程）/ ¥4070（往返优惠票）",
                    "best_for": "住新宿/涩谷/品川的旅客，带大行李也方便",
                    "tip": "可用 JR Pass 免费乘坐；票在官网/绿窗口购买"
                },
                {
                    "name": "京成スカイライナー",
                    "time": "约 41 分钟到上野",
                    "cost": "¥2570（单程）",
                    "best_for": "住上野/浅草/秋叶原方向，比 N'EX 快且便宜",
                    "tip": "不在 JR Pass 范围内，需单独购票"
                },
                {
                    "name": "利木津巴士（Limousine Bus）",
                    "time": "约 80-120 分钟（堵车影响大）",
                    "cost": "¥3200 左右",
                    "best_for": "直接到目标酒店门口，适合行李多的家庭",
                    "tip": "注意确认班次，错过要等 30 分钟"
                },
                {
                    "name": "京成本线（普通/快速）",
                    "time": "约 80 分钟到上野",
                    "cost": "¥1050（最便宜）",
                    "best_for": "预算极省，不赶时间",
                    "tip": "需换乘，行李多时不推荐"
                }
            ],
            "羽田机场": {
                "note": "羽田到市区更近（约 30-40 分钟），选京急线或单轨/东京モノレール即可，¥700-1000"
            }
        },
        "quality_score": 8.6,
        "source_type": "manual",
        "status": "active",
        "is_active": True,
    },
]


async def seed_fragments() -> None:
    async with AsyncSessionLocal() as session:
        existing = (await session.execute(
            select(GuideFragment).where(GuideFragment.city_code == "tokyo")
        )).scalars().all()

        if existing:
            logger.info("tokyo 片段已有 %d 条，跳过种子导入", len(existing))
            return

        logger.info("开始导入 %d 条 tokyo_classic 种子片段...", len(FRAGMENTS))
        for frag_data in FRAGMENTS:
            frag = GuideFragment(**frag_data)
            session.add(frag)
            await session.flush()  # 获取 fragment_id

            # 同时初始化 usage_stats
            stats = FragmentUsageStats(fragment_id=frag.fragment_id)
            session.add(stats)

        await session.commit()
        logger.info("✅ 种子数据导入完成，共 %d 条", len(FRAGMENTS))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_fragments())
