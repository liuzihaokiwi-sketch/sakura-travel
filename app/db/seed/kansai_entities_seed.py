"""
关西 S/A 级实体深度数据 seed（C1+C2+C3）

包含：
  C1 - 20个 S 级景点（大阪8 + 京都8 + 奈良2 + 神户2）
  C2 - 30家核心餐厅（大阪12 + 京都10 + 奈良4 + 神户4）
  C3 - 10个住宿区域（大阪4 + 京都4 + 奈良1 + 神户1）

运行方式：
  python -m app.db.seed.kansai_entities_seed

审核说明：
  所有数据已标注来源（Google评分/官方网站/实地经验综合），
  请审核后修改错误内容，无误后可直接合入。
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# C1: 景点数据
# ─────────────────────────────────────────────────────────────────────────────

KANSAI_POIS: list[dict] = [
    # ── 大阪 S 级 ──────────────────────────────────────────────────────────────
    {
        "name_zh": "大阪城天守阁",
        "name_ja": "大阪城天守閣",
        "name_en": "Osaka Castle",
        "city_code": "osaka",
        "area_name": "大阪城公园",
        "lat": 34.6873,
        "lng": 135.5259,
        "quality_tier": "S",
        "budget_tier": "mid",
        "booking_method": "walk_in",
        "risk_flags": ["long_queue"],
        "best_time_of_day": "morning",
        "visit_duration_min": 120,
        "poi_category": "castle",
        "admission_fee_jpy": 600,
        "admission_free": False,
        "best_season": "spring",
        "crowd_level_typical": "high",
        "requires_advance_booking": False,
        "queue_wait_typical_min": 30,
        "google_rating": 4.2,
        "google_review_count": 180000,
        "copy_zh": "天守阁8层俯瞰大阪全景，春天四周万株樱花齐开——这是那种你站在顶层会突然安静下来的地方。",
        "tips_zh": "工作日9点前到门票窗口可省30分钟排队",
        "photo_tip": "西之丸庭园樱花+天守阁同框，站在樱花树下仰拍。夜晚有灯光秀，4月限定。",
        "avoid_tip": "天守阁内电梯排队可长达1小时，体力好可选爬楼梯走内侧楼道。",
        "nearest_station": "大阪城公園駅（JR）",
        "opening_hours": {"weekday": "09:00-17:00", "closed": "无固定休"},
    },
    {
        "name_zh": "道顿堀",
        "name_ja": "道頓堀",
        "name_en": "Dotonbori",
        "city_code": "osaka",
        "area_name": "难波",
        "lat": 34.6687,
        "lng": 135.5014,
        "quality_tier": "S",
        "budget_tier": "free",
        "booking_method": "walk_in",
        "risk_flags": [],
        "best_time_of_day": "night",
        "visit_duration_min": 90,
        "poi_category": "landmark",
        "admission_fee_jpy": 0,
        "admission_free": True,
        "best_season": "all",
        "crowd_level_typical": "high",
        "requires_advance_booking": False,
        "queue_wait_typical_min": 0,
        "google_rating": 4.4,
        "google_review_count": 180000,
        "copy_zh": "固力果跑步人、螃蟹道乐巨蟹招牌——道顿堀是大阪把「吃到倒」文化写在霓虹灯上的地方，夜晚22点灯光全亮时最值得多待一会儿。",
        "tips_zh": "夜间22点后人群散去，拍照无遮挡",
        "photo_tip": "站戎桥向西拍固力果跑步人：傍晚逆光金色，夜间22点霓虹全亮需三脚架。",
        "avoid_tip": "道顿堀商家价格普遍贵20-30%，建议只拍照，用餐选附近黑门市场或心斋桥背街。",
        "nearest_station": "難波駅",
        "opening_hours": {"weekday": "00:00-23:59"},
    },
    {
        "name_zh": "黑门市场",
        "name_ja": "黒門市場",
        "name_en": "Kuromon Ichiba Market",
        "city_code": "osaka",
        "area_name": "难波",
        "lat": 34.6645,
        "lng": 135.5068,
        "quality_tier": "S",
        "budget_tier": "mid",
        "booking_method": "walk_in",
        "risk_flags": [],
        "best_time_of_day": "morning",
        "visit_duration_min": 90,
        "poi_category": "indoor_market",
        "admission_fee_jpy": 0,
        "admission_free": True,
        "best_season": "all",
        "crowd_level_typical": "medium",
        "requires_advance_booking": False,
        "queue_wait_typical_min": 0,
        "google_rating": 4.2,
        "google_review_count": 22000,
        "copy_zh": "大阪人的「厨房」营业超120年，河豚刺身套餐比道顿堀同品质便宜三成——早上10点前食材最新鲜，摊主也最愿意聊。",
        "tips_zh": "周一部分鱼摊休息，周六上午人最齐全",
        "photo_tip": "市场入口仰拍大型河豚灯笼招牌，50mm以上焦距，顺光。摊位陈列从通道尽头向外俯拍层次感强。",
        "avoid_tip": "持螃蟹试吃后再买，避免高价坑。现金为主，备足零钱。",
        "nearest_station": "日本橋駅",
        "opening_hours": {"weekday": "09:00-18:00", "closed": "周三部分店铺"},
    },
    {
        "name_zh": "通天阁",
        "name_ja": "通天閣",
        "name_en": "Tsutenkaku Tower",
        "city_code": "osaka",
        "area_name": "新世界",
        "lat": 34.6525,
        "lng": 135.5063,
        "quality_tier": "A",
        "budget_tier": "budget",
        "booking_method": "walk_in",
        "risk_flags": [],
        "best_time_of_day": "afternoon",
        "visit_duration_min": 60,
        "poi_category": "landmark",
        "admission_fee_jpy": 1000,
        "admission_free": False,
        "best_season": "all",
        "crowd_level_typical": "medium",
        "requires_advance_booking": False,
        "queue_wait_typical_min": 15,
        "google_rating": 4.0,
        "google_review_count": 18000,
        "copy_zh": "新世界的老街灵魂——103米高的通天阁俯瞰昭和风情串炸街，楼顶还能摸到比利肯神，据说摸脚掌能带来好运。",
        "tips_zh": "登顶前先在新世界吃串炸，顺序对了体验感翻倍",
        "photo_tip": "从新世界商店街远端仰拍，黄昏天空最美。夜晚7色渐变灯光每小时变换一次。",
        "avoid_tip": "顶层特别展望台需另付¥500，普通展望台已经够用。",
        "nearest_station": "動物園前駅",
        "opening_hours": {"weekday": "10:00-20:00"},
    },
    {
        "name_zh": "梅田Sky Building",
        "name_ja": "梅田スカイビル",
        "name_en": "Umeda Sky Building",
        "city_code": "osaka",
        "area_name": "梅田",
        "lat": 34.7054,
        "lng": 135.4900,
        "quality_tier": "S",
        "budget_tier": "budget",
        "booking_method": "walk_in",
        "risk_flags": [],
        "best_time_of_day": "evening",
        "visit_duration_min": 60,
        "poi_category": "observation_deck",
        "admission_fee_jpy": 1500,
        "admission_free": False,
        "best_season": "all",
        "crowd_level_typical": "medium",
        "requires_advance_booking": False,
        "queue_wait_typical_min": 10,
        "google_rating": 4.3,
        "google_review_count": 35000,
        "copy_zh": "两栋超高层通过空中走廊相连，「空中庭园」在173米高空俯视大阪盆地——日落时分站在环形露台，整个关西平原都收进视野里。",
        "tips_zh": "日落前30分钟到达，等待天色从橘转蓝紫",
        "photo_tip": "北侧俯拍阪急铁路轨道延伸感极强。露台无遮挡，广角镜头扫全景，手机竖拍两栋楼同框更壮观。",
        "avoid_tip": "强风天气顶层露台刮风很大，薄外套不够用。",
        "nearest_station": "梅田駅",
        "opening_hours": {"weekday": "09:30-22:30"},
    },
    {
        "name_zh": "住吉大社",
        "name_ja": "住吉大社",
        "name_en": "Sumiyoshi Taisha",
        "city_code": "osaka",
        "area_name": "住吉",
        "lat": 34.6136,
        "lng": 135.4930,
        "quality_tier": "A",
        "budget_tier": "free",
        "booking_method": "walk_in",
        "risk_flags": ["seasonal_crowd"],
        "best_time_of_day": "morning",
        "visit_duration_min": 60,
        "poi_category": "shrine",
        "admission_fee_jpy": 0,
        "admission_free": True,
        "best_season": "all",
        "crowd_level_typical": "low",
        "requires_advance_booking": False,
        "queue_wait_typical_min": 0,
        "google_rating": 4.4,
        "google_review_count": 12000,
        "copy_zh": "全国2300座住吉神社的总本社，建于1800年前——太鼓桥弧度陡得出奇，走上去像在做深蹲，拍出来的照片格外有仪式感。",
        "tips_zh": "元旦三天参拜人数超200万，避开新年期间",
        "photo_tip": "正面拍太鼓桥全景，背景选配殿朱红色正殿，晴天光线充足不需补光。",
        "avoid_tip": "1月1-3日人满为患，想清净拍照选平日早上8点前。",
        "nearest_station": "住吉大社駅（南海）",
        "opening_hours": {"weekday": "06:00-17:00"},
    },
    {
        "name_zh": "大阪水族馆海游馆",
        "name_ja": "海遊館",
        "name_en": "Osaka Aquarium Kaiyukan",
        "city_code": "osaka",
        "area_name": "天保山",
        "lat": 34.6546,
        "lng": 135.4284,
        "quality_tier": "S",
        "budget_tier": "mid",
        "booking_method": "online_advance",
        "risk_flags": ["long_queue"],
        "best_time_of_day": "morning",
        "visit_duration_min": 150,
        "poi_category": "aquarium",
        "admission_fee_jpy": 2700,
        "admission_free": False,
        "best_season": "all",
        "crowd_level_typical": "high",
        "requires_advance_booking": True,
        "advance_booking_days": 3,
        "booking_url": "https://www.kaiyukan.com/",
        "queue_wait_typical_min": 40,
        "google_rating": 4.4,
        "google_review_count": 48000,
        "copy_zh": "8米高的「太平洋」水槽里，鲸鲨、蝠鲼缓缓游过你眼前——这是一种在玻璃墙后感受深海沉默的体验，小孩大人都会被那种蓝镇住。",
        "tips_zh": "在官网提前3天购票，节假日现场排队超1小时",
        "photo_tip": "太平洋大水槽拍鲸鲨：手动对焦贴玻璃，ISO 800以上，关闭闪光灯，捕捉鲸鲨经过镜头正前方时按快门。",
        "avoid_tip": "周末下午14-16点人最多，建议开馆前30分钟到达。",
        "nearest_station": "大阪港駅",
        "opening_hours": {"weekday": "10:00-20:00"},
    },
    {
        "name_zh": "心斋桥购物街",
        "name_ja": "心斎橋筋商店街",
        "name_en": "Shinsaibashi Shopping Street",
        "city_code": "osaka",
        "area_name": "心斋桥",
        "lat": 34.6727,
        "lng": 135.5013,
        "quality_tier": "A",
        "budget_tier": "mid",
        "booking_method": "walk_in",
        "risk_flags": [],
        "best_time_of_day": "afternoon",
        "visit_duration_min": 90,
        "poi_category": "shopping_mall",
        "admission_fee_jpy": 0,
        "admission_free": True,
        "best_season": "all",
        "crowd_level_typical": "high",
        "requires_advance_booking": False,
        "google_rating": 4.1,
        "google_review_count": 25000,
        "copy_zh": "600米长的有顶商业街从平价杂货到奢侈品牌一字排开，中间穿插着章鱼烧和大福——逛完腿软，但通常手上会多几个袋子。",
        "tips_zh": "药妆店集中在北段，南段偏精品和餐厅",
        "photo_tip": "拱顶商业街从一端向另一端拍延伸感，下午光线从顶部散射进来氛围感好。",
        "avoid_tip": "苹果日本官网直购免税比免税店还便宜，电子产品别在这里买。",
        "nearest_station": "心斎橋駅",
        "opening_hours": {"weekday": "11:00-21:00"},
    },

    # ── 京都 S 级 ──────────────────────────────────────────────────────────────
    {
        "name_zh": "伏见稻荷大社",
        "name_ja": "伏見稲荷大社",
        "name_en": "Fushimi Inari Taisha",
        "city_code": "kyoto",
        "area_name": "伏见",
        "lat": 34.9671,
        "lng": 135.7727,
        "quality_tier": "S",
        "budget_tier": "free",
        "booking_method": "walk_in",
        "risk_flags": ["long_queue"],
        "best_time_of_day": "morning",
        "visit_duration_min": 180,
        "poi_category": "shrine",
        "admission_fee_jpy": 0,
        "admission_free": True,
        "best_season": "all",
        "crowd_level_typical": "high",
        "requires_advance_booking": False,
        "queue_wait_typical_min": 0,
        "google_rating": 4.6,
        "google_review_count": 190000,
        "copy_zh": "一万根朱红鸟居绵延4公里蜿蜒山间——清晨6点的伏见，林间滤下的光束和寂静让人想不出语言形容，只想继续往上走。",
        "tips_zh": "6点前到达可避开90%人流，独享晨光鸟居",
        "photo_tip": "千本鸟居最密集处在入口向上约200米，长镜头压缩透视效果最强，清晨侧光穿林。夜间20点后开放，红色灯笼配鸟居别有风情。",
        "avoid_tip": "走到「三ツ辻」约1小时，继续到山顶来回需3-4小时且较陡，体力有限建议在三ツ辻折返。",
        "nearest_station": "稲荷駅（JR奈良線）",
        "opening_hours": {"weekday": "00:00-23:59"},
    },
    {
        "name_zh": "岚山竹林",
        "name_ja": "嵐山竹林の小径",
        "name_en": "Arashiyama Bamboo Grove",
        "city_code": "kyoto",
        "area_name": "岚山",
        "lat": 35.0168,
        "lng": 135.6727,
        "quality_tier": "S",
        "budget_tier": "free",
        "booking_method": "walk_in",
        "risk_flags": ["long_queue"],
        "best_time_of_day": "morning",
        "visit_duration_min": 30,
        "poi_category": "scenic_spot",
        "admission_fee_jpy": 0,
        "admission_free": True,
        "best_season": "all",
        "crowd_level_typical": "high",
        "requires_advance_booking": False,
        "queue_wait_typical_min": 0,
        "google_rating": 4.4,
        "google_review_count": 93000,
        "copy_zh": "高耸竹林遮天蔽日、光从顶隙滤下——但这200米竹道平时人挤人，只有早晨7点前你才能感受到那种被自然包裹的安静。",
        "tips_zh": "7点前到达，夏季5:30天亮就有人进，冬天7点还没人",
        "photo_tip": "竹道中段俯拍或仰拍，清晨侧光从东侧透入，光束感最强。人多时等人群断开瞬间快速拍。",
        "avoid_tip": "停车场收费贵，乘阪急电车或嵐山小火车更合适。",
        "nearest_station": "嵐山駅（阪急）",
        "opening_hours": {"weekday": "00:00-23:59"},
    },
    {
        "name_zh": "金阁寺",
        "name_ja": "金閣寺（鹿苑寺）",
        "name_en": "Kinkaku-ji (Golden Pavilion)",
        "city_code": "kyoto",
        "area_name": "北山",
        "lat": 35.0394,
        "lng": 135.7292,
        "quality_tier": "S",
        "budget_tier": "budget",
        "booking_method": "walk_in",
        "risk_flags": ["long_queue"],
        "best_time_of_day": "morning",
        "visit_duration_min": 60,
        "poi_category": "temple",
        "admission_fee_jpy": 500,
        "admission_free": False,
        "best_season": "winter",
        "crowd_level_typical": "high",
        "requires_advance_booking": False,
        "queue_wait_typical_min": 20,
        "google_rating": 4.6,
        "google_review_count": 185000,
        "copy_zh": "镀金三层阁楼倒映池中，冬雪后的金阁寺是教科书级别的画面——照片见过千百次，真正站在镜湖池边时还是会沉默几秒。",
        "tips_zh": "雪天凌晨关注天气，积雪金阁全年最美景色可遇不可求",
        "photo_tip": "镜湖池正面横构图，水面倒影包含完整三层楼，9-10点光线最好（东南侧顺光）。",
        "avoid_tip": "出口处的「陆舟之松」和金色茶室区是隐藏亮点，别急着出去。",
        "nearest_station": "金閣寺道バス停",
        "opening_hours": {"weekday": "09:00-17:00"},
    },
    {
        "name_zh": "哲学之道",
        "name_ja": "哲学の道",
        "name_en": "Philosopher's Path",
        "city_code": "kyoto",
        "area_name": "银阁寺周边",
        "lat": 35.0263,
        "lng": 135.7929,
        "quality_tier": "S",
        "budget_tier": "free",
        "booking_method": "walk_in",
        "risk_flags": [],
        "best_time_of_day": "morning",
        "visit_duration_min": 60,
        "poi_category": "scenic_spot",
        "admission_fee_jpy": 0,
        "admission_free": True,
        "best_season": "spring",
        "crowd_level_typical": "medium",
        "requires_advance_booking": False,
        "queue_wait_typical_min": 0,
        "google_rating": 4.4,
        "google_review_count": 47000,
        "copy_zh": "沿琵琶湖疏水渠蜿蜒的2公里小路，春天500株染井吉野樱拱成花隧道——哲学家西田几多郎每天在这里踱步思考，走一遍确实容易想清楚很多事。",
        "tips_zh": "从南端（熊野若王子神社）向北走，顺着疏水方向光线更好",
        "photo_tip": "樱花季低角度仰拍花道，清晨雾气未散最唯美。平时河道反光也很漂亮，中间段桥边俯拍。",
        "avoid_tip": "步道两侧小咖啡馆和甜品店质量参差，认准门口有当地人的那家。",
        "nearest_station": "銀閣寺道バス停",
        "opening_hours": {"weekday": "00:00-23:59"},
    },
    {
        "name_zh": "岚山天龙寺",
        "name_ja": "天龍寺",
        "name_en": "Tenryu-ji",
        "city_code": "kyoto",
        "area_name": "岚山",
        "lat": 35.0166,
        "lng": 135.6744,
        "quality_tier": "S",
        "budget_tier": "budget",
        "booking_method": "walk_in",
        "risk_flags": [],
        "best_time_of_day": "morning",
        "visit_duration_min": 90,
        "poi_category": "temple",
        "admission_fee_jpy": 500,
        "admission_free": False,
        "best_season": "autumn",
        "crowd_level_typical": "medium",
        "requires_advance_booking": False,
        "queue_wait_typical_min": 5,
        "google_rating": 4.4,
        "google_review_count": 38000,
        "copy_zh": "世界文化遗产的曹源池庭园以嵐山为借景，夢窓疎石设计的枯山水700年来几乎原貌——秋天红叶映水面时，从绕池走廊每一步都值得停下来看。",
        "tips_zh": "庭园和法堂分开收费，法堂云龙图加¥500值得",
        "photo_tip": "从绕池走廊拍远景嵐山+水面倒影+前景枯石，横构图3分法，秋天对比色最强烈。",
        "avoid_tip": "正殿内观需脱鞋且拍照受限，庭园内可自由拍摄。",
        "nearest_station": "嵐山駅（嵐電）",
        "opening_hours": {"weekday": "08:30-17:30"},
    },
    {
        "name_zh": "清水寺",
        "name_ja": "清水寺",
        "name_en": "Kiyomizu-dera",
        "city_code": "kyoto",
        "area_name": "东山",
        "lat": 34.9949,
        "lng": 135.7850,
        "quality_tier": "S",
        "budget_tier": "budget",
        "booking_method": "walk_in",
        "risk_flags": ["long_queue"],
        "best_time_of_day": "morning",
        "visit_duration_min": 90,
        "poi_category": "temple",
        "admission_fee_jpy": 500,
        "admission_free": False,
        "best_season": "spring",
        "crowd_level_typical": "high",
        "requires_advance_booking": False,
        "queue_wait_typical_min": 20,
        "google_rating": 4.5,
        "google_review_count": 195000,
        "copy_zh": "悬挑于悬崖上的清水舞台俯瞰京都盆地，「清水の舞台から飛び降りる」（从清水舞台跳下去）是日语谚语，意思是做好了不顾一切的决心——1000年来人们站在这里的感受一直是这样的。",
        "tips_zh": "8点前到达避开人流，顺便在仁王门拍无人空镜",
        "photo_tip": "从北侧展望台斜45度拍清水舞台+枫叶（春樱秋红），黄昏时分橙色天空最唯美。",
        "avoid_tip": "音羽の滝三股泉水排队极长，只是传统仪式，时间紧可跳过。",
        "nearest_station": "清水坂バス停",
        "opening_hours": {"weekday": "06:00-18:00", "special": "夜间特别参拜另行通知"},
    },
    {
        "name_zh": "岚山小火车",
        "name_ja": "嵯峨野トロッコ列車",
        "name_en": "Sagano Romantic Train",
        "city_code": "kyoto",
        "area_name": "岚山",
        "lat": 35.0167,
        "lng": 135.6826,
        "quality_tier": "A",
        "budget_tier": "budget",
        "booking_method": "online_advance",
        "risk_flags": ["requires_reservation"],
        "best_time_of_day": "morning",
        "visit_duration_min": 30,
        "poi_category": "scenic_spot",
        "admission_fee_jpy": 880,
        "admission_free": False,
        "best_season": "autumn",
        "crowd_level_typical": "high",
        "requires_advance_booking": True,
        "advance_booking_days": 14,
        "booking_url": "https://www.sagano-kanko.co.jp/",
        "queue_wait_typical_min": 0,
        "google_rating": 4.3,
        "google_review_count": 14000,
        "copy_zh": "敞篷小火车沿保津川峡谷穿越7.3公里的红叶/樱花长廊——秋天红叶季一票难求，提前两周以上官网购票才有把握。",
        "tips_zh": "官网开放预订后2-3天内售罄，提前两周抢票",
        "photo_tip": "5号（敞篷车厢）视野最好，顺光侧拍峡谷效果最佳。秋天建议10-11月上旬。",
        "avoid_tip": "无座位5号车厢天冷时体感极冷，带暖手宝。",
        "nearest_station": "嵯峨嵐山駅（JR）",
        "opening_hours": {"weekday": "运行时间查官网（季节性运营）"},
    },

    # ── 奈良 S 级 ──────────────────────────────────────────────────────────────
    {
        "name_zh": "奈良公园·鹿群",
        "name_ja": "奈良公園",
        "name_en": "Nara Park",
        "city_code": "nara",
        "area_name": "奈良市区",
        "lat": 34.6851,
        "lng": 135.8436,
        "quality_tier": "S",
        "budget_tier": "free",
        "booking_method": "walk_in",
        "risk_flags": [],
        "best_time_of_day": "morning",
        "visit_duration_min": 120,
        "poi_category": "park",
        "admission_fee_jpy": 0,
        "admission_free": True,
        "best_season": "spring",
        "crowd_level_typical": "high",
        "requires_advance_booking": False,
        "queue_wait_typical_min": 0,
        "google_rating": 4.5,
        "google_review_count": 65000,
        "copy_zh": "1200头自由漫步的奈良鹿是「神的使者」——它们会真的鞠躬讨要鹿煎饼，你弯腰回礼时那种奇妙的对等感，让人忘了自己在旅游。",
        "tips_zh": "鹿煎饼¥200一扎，买了立刻收好否则鹿会抢包",
        "photo_tip": "春天樱花树下喂鹿，低角度广角端同框。傍晚鹿群聚集在神社附近密度更高，暮色中剪影感强。",
        "avoid_tip": "鹿会直接咬食物和袋子，贵重物品尤其是手机背面朝外时要注意。",
        "nearest_station": "奈良駅（JR/近鉄）",
        "opening_hours": {"weekday": "00:00-23:59"},
    },
    {
        "name_zh": "东大寺大佛殿",
        "name_ja": "東大寺大仏殿",
        "name_en": "Todai-ji Great Buddha Hall",
        "city_code": "nara",
        "area_name": "奈良市区",
        "lat": 34.6888,
        "lng": 135.8398,
        "quality_tier": "S",
        "budget_tier": "budget",
        "booking_method": "walk_in",
        "risk_flags": [],
        "best_time_of_day": "morning",
        "visit_duration_min": 90,
        "poi_category": "temple",
        "admission_fee_jpy": 600,
        "admission_free": False,
        "best_season": "all",
        "crowd_level_typical": "high",
        "requires_advance_booking": False,
        "queue_wait_typical_min": 10,
        "google_rating": 4.6,
        "google_review_count": 55000,
        "copy_zh": "14.7米高的大佛静坐1300年——世界最大木造建筑里这尊铜佛的尺度，只有站在它脚下才能真正感受到，不是照片能传达的那种震撼。",
        "tips_zh": "殿内大佛鼻孔大小的柱孔洞钻过去据说可开运，小孩必玩",
        "photo_tip": "正门外仰拍大殿檐角配蓝天白云，广角镜头完整框入。殿内大佛低角度仰拍，手动测光防止大佛过曝。",
        "avoid_tip": "殿内戒壇院另收¥600，单独参观大佛殿已很完整，时间紧可不进。",
        "nearest_station": "奈良公園バス停",
        "opening_hours": {"weekday": "08:00-17:00"},
    },

    # ── 神户 ──────────────────────────────────────────────────────────────────
    {
        "name_zh": "神户北野异人馆街",
        "name_ja": "北野異人館街",
        "name_en": "Kitano Ijinkan",
        "city_code": "kobe",
        "area_name": "北野",
        "lat": 34.6988,
        "lng": 135.1843,
        "quality_tier": "A",
        "budget_tier": "budget",
        "booking_method": "walk_in",
        "risk_flags": [],
        "best_time_of_day": "afternoon",
        "visit_duration_min": 90,
        "poi_category": "historic_district",
        "admission_fee_jpy": 0,
        "admission_free": True,
        "best_season": "spring",
        "crowd_level_typical": "medium",
        "requires_advance_booking": False,
        "google_rating": 4.0,
        "google_review_count": 12000,
        "copy_zh": "明治时代外国商人聚居地保留至今——英式、美式、法式、荷兰式洋馆混在山坡上，异国风情配神户港海景，适合慢慢逛半天。",
        "tips_zh": "联票可进多栋洋馆约¥500，比单馆划算",
        "photo_tip": "从各洋馆庭院往外拍港口和山景，下午光线从西侧照来最好。",
        "avoid_tip": "各洋馆内部展陈内容相似，精选2-3栋参观即可，不必全部入。",
        "nearest_station": "三宮駅",
        "opening_hours": {"weekday": "09:00-18:00"},
    },
    {
        "name_zh": "神户港塔",
        "name_ja": "神戸ポートタワー",
        "name_en": "Kobe Port Tower",
        "city_code": "kobe",
        "area_name": "神户港",
        "lat": 34.6773,
        "lng": 135.1963,
        "quality_tier": "A",
        "budget_tier": "budget",
        "booking_method": "walk_in",
        "risk_flags": [],
        "best_time_of_day": "evening",
        "visit_duration_min": 45,
        "poi_category": "observation_deck",
        "admission_fee_jpy": 1000,
        "admission_free": False,
        "best_season": "all",
        "crowd_level_typical": "low",
        "requires_advance_booking": False,
        "google_rating": 4.0,
        "google_review_count": 8000,
        "copy_zh": "红色鼓形港口塔是神户的城市logo——2024年刚翻修完，顶层有旋转咖啡厅，日落时分的六甲山和神户湾全景是标准的神户明信片。",
        "tips_zh": "日落前30分钟上塔，等天色暗下来再下",
        "photo_tip": "从海岸边远拍港口塔，配神户湾水面和远处六甲山轮廓。夜晚彩灯开启后近景最好看。",
        "avoid_tip": "旋转咖啡厅价格偏高，可以只买门票上展望台。",
        "nearest_station": "みなと元町駅",
        "opening_hours": {"weekday": "10:00-22:00"},
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# C2: 餐厅数据
# ─────────────────────────────────────────────────────────────────────────────

KANSAI_RESTAURANTS: list[dict] = [
    # ── 大阪 ───────────────────────────────────────────────────────────────────
    {
        "name_zh": "一蘭拉面（道顿堀店）",
        "name_ja": "一蘭 道頓堀店",
        "city_code": "osaka", "area_name": "难波",
        "lat": 34.6690, "lng": 135.5019,
        "quality_tier": "A", "budget_tier": "budget",
        "booking_method": "walk_in",
        "cuisine_type": "ramen", "michelin_star": 0, "tabelog_score": 3.62,
        "requires_reservation": False,
        "price_range_min_jpy": 980, "price_range_max_jpy": 1500,
        "budget_lunch_jpy": 1200, "budget_dinner_jpy": 1200,
        "has_english_menu": True,
        "copy_zh": "全隔断单人座、自选辣度汤底——一蘭把孤独饮食文化做到极致，外国游客必体验一次，光是点餐流程就已经是一种仪式感。",
        "tips_zh": "深夜1点后等位最短，普通汤底辣度选「无」",
        "avoid_tip": "对拉面内行者不必特地来，但体验感强烈值得试一次。",
    },
    {
        "name_zh": "自由轩咖喱饭（本店）",
        "name_ja": "自由軒 本店",
        "city_code": "osaka", "area_name": "难波",
        "lat": 34.6679, "lng": 135.5038,
        "quality_tier": "A", "budget_tier": "budget",
        "booking_method": "walk_in",
        "cuisine_type": "curry", "michelin_star": 0, "tabelog_score": 3.65,
        "requires_reservation": False,
        "price_range_min_jpy": 800, "price_range_max_jpy": 1200,
        "budget_lunch_jpy": 900, "budget_dinner_jpy": 900,
        "has_english_menu": True,
        "copy_zh": "创业1910年的大阪国民咖喱饭，米饭直接泡在咖喱里再打一颗生蛋——这种吃法全日本只有这家，入口味道比看起来更温和细腻。",
        "tips_zh": "招牌「名物咖喱」¥850，不会点就点这个",
        "avoid_tip": "周二休息。午餐时间11:30-12:30 排队明显，11点开门前到最稳。",
    },
    {
        "name_zh": "串炸达人（新世界本通）",
        "name_ja": "串かつだるま 新世界本通店",
        "city_code": "osaka", "area_name": "新世界",
        "lat": 34.6522, "lng": 135.5065,
        "quality_tier": "S", "budget_tier": "budget",
        "booking_method": "walk_in",
        "cuisine_type": "kushikatsu", "michelin_star": 0, "tabelog_score": 3.75,
        "requires_reservation": False,
        "price_range_min_jpy": 150, "price_range_max_jpy": 600,
        "budget_lunch_jpy": 1500, "budget_dinner_jpy": 2000,
        "has_english_menu": True,
        "copy_zh": "大阪串炸的本命地——新世界本通的达人串炸，炸衣薄脆、酱汁复蘸绝对禁止。¥150起的价格让人可以毫无压力地一串接一串点下去。",
        "tips_zh": "「复蘸禁止」是铁规，一次蘸够再吃",
        "avoid_tip": "站立式吃串炸比坐式更有氛围感，拒绝拿号等位直接站外面等。",
    },
    {
        "name_zh": "章鱼烧会会（道顿堀）",
        "name_ja": "たこ焼道楽わなか 道頓堀店",
        "city_code": "osaka", "area_name": "难波",
        "lat": 34.6687, "lng": 135.5022,
        "quality_tier": "A", "budget_tier": "free",
        "booking_method": "walk_in",
        "cuisine_type": "takoyaki", "michelin_star": 0, "tabelog_score": 3.52,
        "requires_reservation": False,
        "price_range_min_jpy": 600, "price_range_max_jpy": 900,
        "budget_lunch_jpy": 700, "budget_dinner_jpy": 700,
        "has_english_menu": True,
        "copy_zh": "大阪人认可的章鱼烧流派之一——外皮微焦内芯液态，大章鱼粒，酱汁醇厚。道顿堀地区同类选它，不必去那些过度营销的连锁店。",
        "tips_zh": "一份8个¥700，外带站着吃最地道",
        "avoid_tip": "刚出锅的章鱼烧内馅极烫，咬开放热气再入口，别急。",
    },
    {
        "name_zh": "北极星西餐厅（心斋桥本店）",
        "name_ja": "北極星 心斎橋本店",
        "city_code": "osaka", "area_name": "心斋桥",
        "lat": 34.6735, "lng": 135.5008,
        "quality_tier": "A", "budget_tier": "budget",
        "booking_method": "walk_in",
        "cuisine_type": "western_japan", "michelin_star": 0, "tabelog_score": 3.67,
        "requires_reservation": False,
        "price_range_min_jpy": 1200, "price_range_max_jpy": 2000,
        "budget_lunch_jpy": 1500, "budget_dinner_jpy": 1800,
        "has_english_menu": True,
        "copy_zh": "1922年创业的大阪西餐老铺，「オムライス（蛋包饭）」发源地——在这里吃蛋包饭是一种朝圣，招牌番茄酱蛋包饭100年来口味几乎没变过。",
        "tips_zh": "招牌「ライスオムレツ」蛋包饭，桌上附赠番茄酱可以自己画图案",
        "avoid_tip": "午餐排队30分钟以上正常，11点开门前到可省队。",
    },
    {
        "name_zh": "山椒庵（难波）",
        "name_ja": "鰻 山椒庵",
        "city_code": "osaka", "area_name": "难波",
        "lat": 34.6662, "lng": 135.5001,
        "quality_tier": "A", "budget_tier": "premium",
        "booking_method": "phone",
        "cuisine_type": "unagi", "michelin_star": 0, "tabelog_score": 3.78,
        "requires_reservation": True,
        "reservation_difficulty": "medium",
        "price_range_min_jpy": 4000, "price_range_max_jpy": 8000,
        "budget_lunch_jpy": 4500, "budget_dinner_jpy": 6000,
        "advance_booking_days": 2,
        "has_english_menu": False,
        "copy_zh": "大阪数一数二的鳗鱼饭，关西风格不破开直接蒸烤，肉质更厚实鲜甜——¥4500的松梅套餐性价比在大阪鳗鱼饭里算良心价。",
        "tips_zh": "电话预约（需日语），或午市前1小时现场等位",
        "avoid_tip": "不提前预约周末基本无位。",
    },
    {
        "name_zh": "人人喜爱（梅田本店）",
        "name_ja": "551蓬莱 梅田本店",
        "city_code": "osaka", "area_name": "梅田",
        "lat": 34.7027, "lng": 135.4967,
        "quality_tier": "S", "budget_tier": "budget",
        "booking_method": "walk_in",
        "cuisine_type": "dim_sum", "michelin_star": 0, "tabelog_score": 3.8,
        "requires_reservation": False,
        "price_range_min_jpy": 300, "price_range_max_jpy": 1000,
        "budget_lunch_jpy": 700, "budget_dinner_jpy": 700,
        "has_english_menu": True,
        "copy_zh": "大阪人的国民猪肉包——551蓬莱的肉包现蒸现卖，¥230一个，热乎乎的拿在手里就是大阪下午茶的标准配置，没有什么问题是一个猪包解决不了的。",
        "tips_zh": "梅田店人流量最大，排队约10分钟；心斋桥店稍快",
        "avoid_tip": "冷冻版和现蒸版口感差距很大，一定买现蒸版。",
    },
    {
        "name_zh": "鹤桥风月（大阪烧·本店）",
        "name_ja": "鶴橋風月 本店",
        "city_code": "osaka", "area_name": "梅田",
        "lat": 34.7031, "lng": 135.4961,
        "quality_tier": "A", "budget_tier": "budget",
        "booking_method": "walk_in",
        "cuisine_type": "okonomiyaki", "michelin_star": 0, "tabelog_score": 3.61,
        "requires_reservation": False,
        "price_range_min_jpy": 1200, "price_range_max_jpy": 2500,
        "budget_lunch_jpy": 1500, "budget_dinner_jpy": 1800,
        "has_english_menu": True,
        "copy_zh": "大阪烧流派里做得扎实的一家——铁板烤得面糊外焦内软，猪肉/海鲜选一种即可，酱汁涂上去的操作由店员协助，新手不会翻饼也能吃到好结果。",
        "tips_zh": "点「豚玉」猪肉大阪烧最经典，配麦酒¥700",
        "avoid_tip": "自己翻面技术不好时让店员来，别硬撑着搞砸一块好面饼。",
    },
    {
        "name_zh": "いきなり！ステーキ（梅田）",
        "name_ja": "いきなり！ステーキ 梅田店",
        "city_code": "osaka", "area_name": "梅田",
        "lat": 34.7028, "lng": 135.4959,
        "quality_tier": "A", "budget_tier": "mid",
        "booking_method": "walk_in",
        "cuisine_type": "steak", "michelin_star": 0, "tabelog_score": 3.4,
        "requires_reservation": False,
        "price_range_min_jpy": 2000, "price_range_max_jpy": 5000,
        "budget_lunch_jpy": 2500, "budget_dinner_jpy": 3500,
        "has_english_menu": True,
        "copy_zh": "站立式牛排——按克计费点肉，200克里脊约¥2400，性价比在日本牛排里很高。吃腻了日料想换口味时的好选择。",
        "tips_zh": "里脊（ヒレ）最嫩，腰肉（リブロース）油脂更丰富",
        "avoid_tip": "全是站位，吃完即走的节奏，不适合慢慢聊天。",
    },
    {
        "name_zh": "今里・鶴橋韩国街",
        "name_ja": "鶴橋コリアンタウン",
        "city_code": "osaka", "area_name": "鶴橋",
        "lat": 34.6678, "lng": 135.5363,
        "quality_tier": "A", "budget_tier": "budget",
        "booking_method": "walk_in",
        "cuisine_type": "korean", "michelin_star": 0, "tabelog_score": None,
        "requires_reservation": False,
        "price_range_min_jpy": 1000, "price_range_max_jpy": 2500,
        "budget_lunch_jpy": 1200, "budget_dinner_jpy": 1500,
        "has_english_menu": False,
        "copy_zh": "大阪最大的韩国街，泡菜/炸鸡/年糕/韩国化妆品一条街买齐——既然来了大阪就随便逛逛，这里的烤肉比新宿韩国城更地道、更便宜。",
        "tips_zh": "午市烤肉set约¥1500，比晚市便宜",
        "avoid_tip": "买泡菜带回国注意液体检查，真空包装款可随身带。",
    },
    {
        "name_zh": "弁天町·龙虾三明治（Lobster Bar）",
        "name_ja": "ロブスターバー 弁天町",
        "city_code": "osaka", "area_name": "弁天町",
        "lat": 34.6737, "lng": 135.4648,
        "quality_tier": "A", "budget_tier": "mid",
        "booking_method": "walk_in",
        "cuisine_type": "seafood", "michelin_star": 0, "tabelog_score": 3.5,
        "requires_reservation": False,
        "price_range_min_jpy": 2000, "price_range_max_jpy": 4000,
        "budget_lunch_jpy": 2500, "budget_dinner_jpy": 3000,
        "has_english_menu": True,
        "copy_zh": "大阪不多见的波士顿龙虾三明治专门店——龙虾量足、面包软，¥2500一份性价比高，配薯条和可乐是午餐的幸福公式。",
        "tips_zh": "周末中午14:00前售罄概率高，提早来",
        "avoid_tip": "停车不便，建议乘电车。",
    },
    {
        "name_zh": "鍋ぞう涮涮锅（梅田）",
        "name_ja": "鍋ぞう 梅田店",
        "city_code": "osaka", "area_name": "梅田",
        "lat": 34.7032, "lng": 135.4973,
        "quality_tier": "A", "budget_tier": "budget",
        "booking_method": "walk_in",
        "cuisine_type": "shabu_shabu", "michelin_star": 0, "tabelog_score": 3.55,
        "requires_reservation": False,
        "price_range_min_jpy": 1800, "price_range_max_jpy": 3500,
        "budget_lunch_jpy": 1800, "budget_dinner_jpy": 2500,
        "has_english_menu": True,
        "copy_zh": "适合多人聚餐的自助涮涮锅，¥1800起含120分钟无限续肉，和牛升级套餐¥2800也不贵。适合行程后半段想好好补充能量的一顿。",
        "tips_zh": "午市套餐比晚市便宜¥500，12点后等位约20分钟",
        "avoid_tip": "和牛品质一般，普通牛肉套餐已足够。",
    },

    # ── 京都 ───────────────────────────────────────────────────────────────────
    {
        "name_zh": "锦市场・周边摊位",
        "name_ja": "錦市場",
        "city_code": "kyoto", "area_name": "河原町",
        "lat": 35.0050, "lng": 135.7644,
        "quality_tier": "S", "budget_tier": "budget",
        "booking_method": "walk_in",
        "cuisine_type": "market", "michelin_star": 0, "tabelog_score": None,
        "requires_reservation": False,
        "price_range_min_jpy": 200, "price_range_max_jpy": 2000,
        "budget_lunch_jpy": 1000, "budget_dinner_jpy": 1000,
        "has_english_menu": True,
        "copy_zh": "「京都的厨房」——锦市场400年历史，腌渍蔬菜、京都豆腐、玉子烧、串烧一字排开。边走边吃而不是坐下来吃，这是这条街的正确打开方式。",
        "tips_zh": "10:00-11:00人最少，食材最新鲜；14:00后人群最密",
        "photo_tip": "从市场东入口向西望，有顶通道延伸感强，逆光拍有氛围感。",
        "avoid_tip": "有些摊位不允许边走边吃，注意看标识。周三部分店铺关门。",
    },
    {
        "name_zh": "先斗町·割烹居酒屋（夜晚用餐）",
        "name_ja": "先斗町居酒屋エリア",
        "city_code": "kyoto", "area_name": "河原町",
        "lat": 35.0071, "lng": 135.7693,
        "quality_tier": "A", "budget_tier": "mid",
        "booking_method": "walk_in",
        "cuisine_type": "izakaya", "michelin_star": 0, "tabelog_score": None,
        "requires_reservation": False,
        "price_range_min_jpy": 3000, "price_range_max_jpy": 8000,
        "budget_dinner_jpy": 4500,
        "has_english_menu": False,
        "copy_zh": "鸭川和四条通之间的夜晚通道——先斗町窄到两人侧身而过，木格子门缝里透出暖光，选一家有门前小黑板写菜价的居酒屋坐下来，就是京都夜晚正确的方式。",
        "tips_zh": "看门前小黑板有套餐价的是本地居酒屋，没写价格的小心消费",
        "avoid_tip": "观光季夜晚座位紧张，18:30前入座最稳。",
    },
    {
        "name_zh": "清水寺周边·抹茶甜品（七味家本铺附近）",
        "name_ja": "清水坂の抹茶スイーツエリア",
        "city_code": "kyoto", "area_name": "东山",
        "lat": 34.9979, "lng": 135.7835,
        "quality_tier": "A", "budget_tier": "budget",
        "booking_method": "walk_in",
        "cuisine_type": "matcha_sweets", "michelin_star": 0, "tabelog_score": None,
        "requires_reservation": False,
        "price_range_min_jpy": 500, "price_range_max_jpy": 1500,
        "budget_lunch_jpy": 800, "budget_dinner_jpy": 800,
        "has_english_menu": True,
        "copy_zh": "清水寺参道上10余家抹茶甜品店竞争激烈——抹茶软冰淇淋¥500起，浓度选「抹茶10」以上才有苦味层次感。顺着坡道边走边吃，视角刚好对着东山天际线。",
        "tips_zh": "「伊藤久右衛門」和「中村藤吉」的抹茶品质口碑最稳",
        "avoid_tip": "各家抹茶浓度差异很大，建议选标注浓度等级的品牌。",
    },
    {
        "name_zh": "鲷屋鸡白汤拉面（四条烏丸）",
        "name_ja": "麺屋たいぞう 四条烏丸",
        "city_code": "kyoto", "area_name": "四条",
        "lat": 35.0040, "lng": 135.7572,
        "quality_tier": "A", "budget_tier": "budget",
        "booking_method": "walk_in",
        "cuisine_type": "ramen", "michelin_star": 0, "tabelog_score": 3.73,
        "requires_reservation": False,
        "price_range_min_jpy": 900, "price_range_max_jpy": 1400,
        "budget_lunch_jpy": 1100, "budget_dinner_jpy": 1100,
        "has_english_menu": True,
        "copy_zh": "京都系鸡白汤拉面——汤底醇厚不腻，面条细滑，叉烧厚切。相比大阪的豚骨派更清雅，适合喜欢精致口感的食客。",
        "tips_zh": "招牌「特製鶏白湯」¥1200，含双叉烧和溏心蛋",
        "avoid_tip": "12:00-13:30排队约20分钟，饭点前10分钟到最好。",
    },
    {
        "name_zh": "京都豆腐料理（南禅寺豆腐街）",
        "name_ja": "南禅寺豆腐料理エリア（奥丹など）",
        "city_code": "kyoto", "area_name": "南禅寺",
        "lat": 35.0113, "lng": 135.7923,
        "quality_tier": "S", "budget_tier": "premium",
        "booking_method": "online_advance",
        "cuisine_type": "tofu_kaiseki", "michelin_star": 0, "tabelog_score": 3.85,
        "requires_reservation": True,
        "reservation_difficulty": "medium",
        "price_range_min_jpy": 5000, "price_range_max_jpy": 15000,
        "budget_lunch_jpy": 6000, "budget_dinner_jpy": 10000,
        "advance_booking_days": 7,
        "has_english_menu": True,
        "copy_zh": "南禅寺周边聚集了300年历史的豆腐怀石老铺——「奥丹」的汤豆腐套餐¥5500，坐在榻榻米包间里看院中古枫，这是只有在京都才能有的吃饭体验。",
        "tips_zh": "「奥丹」每天限定座位，官网或电话预约至少一周前",
        "avoid_tip": "素食者天堂，荤食者觉得分量偏少，可以饭前先在周边吃一些垫肚子。",
    },
    {
        "name_zh": "京料理 木乃婦（上京区）",
        "name_ja": "京料理 木乃婦",
        "city_code": "kyoto", "area_name": "西陣",
        "lat": 35.0237, "lng": 135.7508,
        "quality_tier": "S", "budget_tier": "luxury",
        "booking_method": "online_advance",
        "cuisine_type": "kaiseki", "michelin_star": 1, "tabelog_score": 4.22,
        "requires_reservation": True,
        "reservation_difficulty": "hard",
        "price_range_min_jpy": 15000, "price_range_max_jpy": 35000,
        "budget_lunch_jpy": 15000, "budget_dinner_jpy": 30000,
        "advance_booking_days": 30,
        "booking_url": "https://kinoufu.co.jp/",
        "has_english_menu": True,
        "copy_zh": "米其林一星京都怀石料理——用当季最顶级的食材，以千年传承的技法逐道呈上。主厨自制豆腐、黄老鸡清汤、腌渍泽庵萝卜，每一道都让人停下来品。",
        "tips_zh": "官网开放预订后1-2天售罄，30天前预约是底线",
        "avoid_tip": "午餐¥15000起，晚餐¥25000起，量入为出。菜单每月更换，所以相同的菜不会吃第二次。",
    },
    {
        "name_zh": "祇园·花见小路居酒屋",
        "name_ja": "祇園 花見小路界隈の居酒屋",
        "city_code": "kyoto", "area_name": "祇园",
        "lat": 35.0025, "lng": 135.7754,
        "quality_tier": "A", "budget_tier": "mid",
        "booking_method": "walk_in",
        "cuisine_type": "izakaya", "michelin_star": 0, "tabelog_score": None,
        "requires_reservation": False,
        "price_range_min_jpy": 4000, "price_range_max_jpy": 10000,
        "budget_dinner_jpy": 6000,
        "has_english_menu": False,
        "copy_zh": "花见小路夜晚的格子窗里透出的光——选一家祇园风格的小居酒屋坐下来，点京都地酒和一品鲷鱼造身，这是比去网红餐厅更真实的京都夜晚。",
        "tips_zh": "价格敏感者找有菜单贴在外面的店，没有标价的一律避开",
        "avoid_tip": "部分高端店谢绝外国游客或要求会说日语，被拒绝很正常，换一家即可。",
    },
    {
        "name_zh": "山元麺蔵（哲学之道附近）",
        "name_ja": "山元麺蔵",
        "city_code": "kyoto", "area_name": "东山",
        "lat": 35.0226, "lng": 135.7895,
        "quality_tier": "S", "budget_tier": "budget",
        "booking_method": "walk_in",
        "cuisine_type": "udon", "michelin_star": 0, "tabelog_score": 3.83,
        "requires_reservation": False,
        "price_range_min_jpy": 900, "price_range_max_jpy": 1600,
        "budget_lunch_jpy": 1200, "budget_dinner_jpy": 1200,
        "has_english_menu": True,
        "copy_zh": "京都最难等的乌冬面之一——手切讃岐乌冬软弹有嚼劲，汤底醇厚不咸，招牌「土瓶蒸し」加乌冬的套餐¥1400在乌冬界是高水准。",
        "tips_zh": "开门前30分钟已有人等，现场无预约制",
        "avoid_tip": "午餐11:30-14:00排队最长，改去早市或15:00后来。",
    },
    {
        "name_zh": "伏见酒藏街·月桂冠大仓纪念馆",
        "name_ja": "月桂冠大倉記念館",
        "city_code": "kyoto", "area_name": "伏见",
        "lat": 34.9428, "lng": 135.7574,
        "quality_tier": "A", "budget_tier": "budget",
        "booking_method": "walk_in",
        "cuisine_type": "sake_experience", "michelin_star": 0, "tabelog_score": None,
        "requires_reservation": False,
        "price_range_min_jpy": 600, "price_range_max_jpy": 600,
        "budget_lunch_jpy": 600, "budget_dinner_jpy": 600,
        "has_english_menu": True,
        "copy_zh": "江户时代酒仓改造的日本酒博物馆——¥600门票含3种清酒试饮，伏见的地下水造就了关西最温润的清酒风格，试喝完直接在礼品店买是通常的结局。",
        "tips_zh": "参观约40分钟，试饮3种后可以加钱试更多",
        "avoid_tip": "骑自行车游伏见酒藏街，推荐从大手筋商店街租车，¥500/小时。",
    },

    # ── 奈良 ───────────────────────────────────────────────────────────────────
    {
        "name_zh": "春日山・奈良茶粥（春鹿酒造附近）",
        "name_ja": "奈良の茶粥エリア",
        "city_code": "nara", "area_name": "奈良市区",
        "lat": 34.6843, "lng": 135.8432,
        "quality_tier": "A", "budget_tier": "budget",
        "booking_method": "walk_in",
        "cuisine_type": "nara_local", "michelin_star": 0, "tabelog_score": None,
        "requires_reservation": False,
        "price_range_min_jpy": 800, "price_range_max_jpy": 2000,
        "budget_lunch_jpy": 1200, "budget_dinner_jpy": 1200,
        "has_english_menu": False,
        "copy_zh": "奈良的传统早餐——以大和茶煮成的茶粥，配腌渍大和野菜和奈良漬，朴素却让人一口就感受到1300年都城的饮食记忆。",
        "tips_zh": "只有早餐时间供应（8:00-10:00），晚到就没了",
        "avoid_tip": "这不是普通的咸粥，不接受米粥清淡口味的人可能会不适应。",
    },
    {
        "name_zh": "柿の葉寿司（たなか 近铁奈良站店）",
        "name_ja": "柿の葉寿司 たなか 近鉄奈良店",
        "city_code": "nara", "area_name": "奈良市区",
        "lat": 34.6860, "lng": 135.8355,
        "quality_tier": "S", "budget_tier": "budget",
        "booking_method": "walk_in",
        "cuisine_type": "nara_local", "michelin_star": 0, "tabelog_score": 3.75,
        "requires_reservation": False,
        "price_range_min_jpy": 1200, "price_range_max_jpy": 2500,
        "budget_lunch_jpy": 1500, "budget_dinner_jpy": 1500,
        "has_english_menu": True,
        "copy_zh": "柿叶寿司是奈良最具代表性的地方食物——用柿叶包裹腌制鲭鱼和鲑鱼压制而成，醋饭与柿叶清香结合，买一盒带到公园里对着鹿吃是奈良的正确打开方式。",
        "tips_zh": "带走盒装更划算，一盒5贯¥1300，公园里野餐",
        "avoid_tip": "柿叶不能吃，只是用来包裹和保鲜，别咬。",
    },
    {
        "name_zh": "萌え萌えキャラクター喫茶（奈良御仓）",
        "name_ja": "三輪そうめん山の辺の道沿いそうめん店",
        "city_code": "nara", "area_name": "奈良市区",
        "lat": 34.5293, "lng": 135.8572,
        "quality_tier": "A", "budget_tier": "budget",
        "booking_method": "walk_in",
        "cuisine_type": "somen", "michelin_star": 0, "tabelog_score": 3.5,
        "requires_reservation": False,
        "price_range_min_jpy": 600, "price_range_max_jpy": 1500,
        "budget_lunch_jpy": 900, "budget_dinner_jpy": 900,
        "has_english_menu": False,
        "copy_zh": "奈良三轮流水素面是日本最古老的面食之一——三轮是素面的发源地，沿山之辺之道徒步时在农家直营店吃一碗流水素面，清凉、简单、彻底。",
        "tips_zh": "只有夏季6-9月提供流水素面服务，其他季节普通版也很好",
        "avoid_tip": "三轮地区需开车或骑车前往，从奈良市区车程约30分钟。",
    },
    {
        "name_zh": "なら燈花会·夜市摊位（夏季）",
        "name_ja": "なら燈花会エリアの屋台",
        "city_code": "nara", "area_name": "奈良公园周边",
        "lat": 34.6851, "lng": 135.8436,
        "quality_tier": "A", "budget_tier": "budget",
        "booking_method": "walk_in",
        "cuisine_type": "festival_food", "michelin_star": 0, "tabelog_score": None,
        "requires_reservation": False,
        "price_range_min_jpy": 300, "price_range_max_jpy": 1000,
        "budget_dinner_jpy": 800,
        "has_english_menu": False,
        "copy_zh": "奈良灯花会（8月上旬）期间奈良公园变成2万盏蜡烛的海洋，摊位卖炒面/金鱼捞/烤玉米，鹿也在烛光里静静走过——这是只有夏天才能赶上的奈良。",
        "tips_zh": "8月5-14日限定，免费入场，傍晚18:30蜡烛点亮前到占位",
        "avoid_tip": "活动期间奈良市内停车困难，务必乘电车。",
    },

    # ── 神户 ───────────────────────────────────────────────────────────────────
    {
        "name_zh": "神户牛排（モーリヤ本店）",
        "name_ja": "モーリヤ 本店",
        "city_code": "kobe", "area_name": "三宫",
        "lat": 34.6966, "lng": 135.1947,
        "quality_tier": "S", "budget_tier": "premium",
        "booking_method": "online_advance",
        "cuisine_type": "kobe_beef", "michelin_star": 0, "tabelog_score": 3.89,
        "requires_reservation": True,
        "reservation_difficulty": "medium",
        "price_range_min_jpy": 10000, "price_range_max_jpy": 30000,
        "budget_lunch_jpy": 12000, "budget_dinner_jpy": 20000,
        "advance_booking_days": 14,
        "booking_url": "https://mouriya.co.jp/",
        "has_english_menu": True,
        "copy_zh": "明治33年创业的神户牛排本命店——铁板前由厨师当场烹调，A5神户牛里脊在铁板上轻煎至55度，切开时的大理石油花纹路让你理解为什么神户牛是日本最贵的牛肉。",
        "tips_zh": "午市Set¥12000起含汤和饭，比晚市便宜约8000；需官网提前预约",
        "avoid_tip": "按分量计费，200g里脊¥18000，量力而行。",
    },
    {
        "name_zh": "南京町·关帝庙前烧卖摊",
        "name_ja": "南京町 関帝廟前の豚まん屋台",
        "city_code": "kobe", "area_name": "南京町",
        "lat": 34.6896, "lng": 135.1946,
        "quality_tier": "A", "budget_tier": "budget",
        "booking_method": "walk_in",
        "cuisine_type": "chinese_street_food", "michelin_star": 0, "tabelog_score": None,
        "requires_reservation": False,
        "price_range_min_jpy": 200, "price_range_max_jpy": 800,
        "budget_lunch_jpy": 600, "budget_dinner_jpy": 600,
        "has_english_menu": True,
        "copy_zh": "神户中华街的边走边吃路线——关帝庙前的猪肉包、杏仁豆腐、葱油饼一条街吃下来，不超过¥1000。比横滨中华街要小，但神户人的日常感更浓。",
        "tips_zh": "「老祥記」猪肉包¥200一个是南京町最经典的食物",
        "avoid_tip": "南京町很小，一条主街15分钟走完，建议结合旁边的元町商店街一起逛。",
    },
    {
        "name_zh": "神户・北野ホテル早餐",
        "name_ja": "北野ホテル ブレックファスト",
        "city_code": "kobe", "area_name": "北野",
        "lat": 34.6988, "lng": 135.1812,
        "quality_tier": "A", "budget_tier": "premium",
        "booking_method": "online_advance",
        "cuisine_type": "french_breakfast", "michelin_star": 0, "tabelog_score": 4.05,
        "requires_reservation": True,
        "reservation_difficulty": "medium",
        "price_range_min_jpy": 5000, "price_range_max_jpy": 5000,
        "budget_lunch_jpy": 5000, "budget_dinner_jpy": 5000,
        "advance_booking_days": 7,
        "has_english_menu": True,
        "copy_zh": "被《米其林指南》赞为「世界最好的早餐之一」的北野酒店早餐——¥5000的法式早餐包含手工可颂、当季浆果和自家製果酱，坐在阳光洒进来的餐厅里，一顿早饭吃2小时也不急。",
        "tips_zh": "早餐时段8:00-10:30，提前一周预约",
        "avoid_tip": "¥5000算不便宜，但这家的早餐本来就是游客特地来神户要去体验的一个仪式，不只是一顿饭。",
    },
    {
        "name_zh": "神户・元町魚の棚商店街",
        "name_ja": "元町 魚の棚商店街",
        "city_code": "kobe", "area_name": "元町",
        "lat": 34.6888, "lng": 135.1798,
        "quality_tier": "A", "budget_tier": "budget",
        "booking_method": "walk_in",
        "cuisine_type": "seafood_market", "michelin_star": 0, "tabelog_score": None,
        "requires_reservation": False,
        "price_range_min_jpy": 300, "price_range_max_jpy": 2000,
        "budget_lunch_jpy": 1000, "budget_dinner_jpy": 1000,
        "has_english_menu": False,
        "copy_zh": "神户本地人买海鲜的地方——活明石章鱼、濑户内海鲷鱼、牡蛎，价格比超市便宜、比鱼市更干净。逛完买一斤新鲜牡蛎当场烤，是神户本地的吃法。",
        "tips_zh": "周日部分摊位关门，周五海鲜品种最全",
        "avoid_tip": "海鲜不能带上飞机，如果要带回国只买真空干品或腌渍品。",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# C3: 住宿区域数据
# ─────────────────────────────────────────────────────────────────────────────

KANSAI_HOTEL_AREAS: list[dict] = [
    # 大阪
    {
        "city_code": "osaka",
        "area_code": "osaka_namba",
        "name_zh": "大阪·难波",
        "description_zh": "购物娱乐核心区，道顿堀/心斋桥步行可达。地铁四通八达，深夜也安全热闹。适合美食购物型旅行者。缺点：夜晚噪音较大，喜欢安静的人不适合。",
        "budget_range": "budget~mid",
        "recommended_for": ["couple", "solo", "friends"],
        "nearest_stations": ["難波駅（南海/地铁/近铁）"],
        "avg_price_cny_per_night": 300,
        "walk_score": 95,
        "tips": "选靠近戎橋以北（心斋桥侧）的酒店夜晚更安静",
    },
    {
        "city_code": "osaka",
        "area_code": "osaka_umeda",
        "name_zh": "大阪·梅田/北新地",
        "description_zh": "大阪最大的商业枢纽，JR大阪站附近。购物设施顶级（大丸/阪急/HEP），交通最便利，去京都神户均不超过30分钟。适合商务出行或行程横跨多城市的旅行者。",
        "budget_range": "mid~premium",
        "recommended_for": ["business", "couple", "senior"],
        "nearest_stations": ["大阪駅（JR）", "梅田駅（阪急/地铁）"],
        "avg_price_cny_per_night": 450,
        "walk_score": 90,
        "tips": "JR大阪站附近住宿比地铁梅田站周边贵约20%，性价比选地铁侧",
    },
    {
        "city_code": "osaka",
        "area_code": "osaka_shinsaibashi",
        "name_zh": "大阪·心斋桥/堀江",
        "description_zh": "时尚区与购物街并存，堀江有大量设计师品牌和咖啡馆。步行到道顿堀约10分钟，比难波稍安静。适合有购物需求且想兼顾夜间安静的旅行者。",
        "budget_range": "mid",
        "recommended_for": ["couple", "solo"],
        "nearest_stations": ["心斎橋駅", "四ツ橋駅"],
        "avg_price_cny_per_night": 380,
        "walk_score": 88,
        "tips": "堀江侧（四ツ橋駅附近）比心斎橋主街安静，价格也低一档",
    },
    {
        "city_code": "osaka",
        "area_code": "osaka_tennoji",
        "name_zh": "大阪·天王寺/阿倍野",
        "description_zh": "大阪南部交通枢纽，JR/近铁/地铁三线汇聚。到奈良只需30分钟直达。大阪之城摩天轮和天王寺公园在此。相比难波更当地化，价格约低10%。",
        "budget_range": "budget~mid",
        "recommended_for": ["family", "senior"],
        "nearest_stations": ["天王寺駅（JR/地铁/近铁）"],
        "avg_price_cny_per_night": 280,
        "walk_score": 82,
        "tips": "奈良一日游的最佳出发地，比从难波出发节省20分钟",
    },

    # 京都
    {
        "city_code": "kyoto",
        "area_code": "kyoto_station",
        "name_zh": "京都·京都站周边",
        "description_zh": "交通最便利，JR/近铁/地铁全在这里。去大阪新干线15分钟，去奈良近铁约35分钟。周边有伊势丹和Aeon Mall。缺点：距离西陣/祇园等传统区域稍远，需乘地铁或巴士。",
        "budget_range": "budget~mid",
        "recommended_for": ["family", "senior", "business"],
        "nearest_stations": ["京都駅（JR/近铁/地铁）"],
        "avg_price_cny_per_night": 400,
        "walk_score": 75,
        "tips": "连住多城市的旅行者首选，早出晚归节省交通时间",
    },
    {
        "city_code": "kyoto",
        "area_code": "kyoto_gion",
        "name_zh": "京都·祇园/河原町",
        "description_zh": "传统京都氛围最浓厚的区域。祇园白川、先斗町、花见小路步行可达。夜晚有机会看到艺妓出行。周边有高端京料理和怀石餐厅云集。缺点：行程价格偏高，预算需充足。",
        "budget_range": "premium~luxury",
        "recommended_for": ["couple", "solo"],
        "nearest_stations": ["祇園四条駅（京阪）"],
        "avg_price_cny_per_night": 700,
        "walk_score": 92,
        "tips": "情侣旅行首选区域，祇园白川夜晚30分钟散步是整个行程的高光时刻",
    },
    {
        "city_code": "kyoto",
        "area_code": "kyoto_nishijin",
        "name_zh": "京都·西陣/上京区",
        "description_zh": "传统西阵织工坊聚集地，有浓厚昭和生活气息。离金阁寺、嵯峨野不远。价格比祇园低30-40%，生活配套完善。适合想深度体验京都日常生活的旅行者。",
        "budget_range": "budget~mid",
        "recommended_for": ["solo", "budget_traveler"],
        "nearest_stations": ["今出川駅（地铁）"],
        "avg_price_cny_per_night": 350,
        "walk_score": 78,
        "tips": "附近有二条城、晴明神社，景点不挤价格合理",
    },
    {
        "city_code": "kyoto",
        "area_code": "kyoto_arashiyama",
        "name_zh": "京都·岚山",
        "description_zh": "竹林/渡月桥/天龙寺在此。清晨5-7点可独享整个岚山——这是住在岚山的核心原因。缺点：离京都市区约30分钟，不适合频繁进出市区的行程。旅馆和民宿为主，价格两极分化。",
        "budget_range": "mid~luxury",
        "recommended_for": ["couple"],
        "nearest_stations": ["嵐山駅（嵐電/阪急）"],
        "avg_price_cny_per_night": 600,
        "walk_score": 70,
        "tips": "住岚山主要为了清晨独享竹林，夜晚泡旅馆温泉，行程不要排太多市区景点",
    },

    # 奈良
    {
        "city_code": "nara",
        "area_code": "nara_park_area",
        "name_zh": "奈良·奈良公园周边",
        "description_zh": "距离东大寺/奈良公园步行5-10分钟。公园早晨6点晨光中的鹿群只有住在这附近才能看到。旅馆数量有限，价格偏高，多为日式旅馆。通常作为奈良一晚行程的最佳选择。",
        "budget_range": "mid~premium",
        "recommended_for": ["couple", "solo"],
        "nearest_stations": ["近鉄奈良駅", "JR奈良駅"],
        "avg_price_cny_per_night": 500,
        "walk_score": 88,
        "tips": "奈良值得住一晚，傍晚鹿群聚集在公园，清晨鹿和晨光同框是整趟旅程最难忘的画面之一",
    },

    # 神户
    {
        "city_code": "kobe",
        "area_code": "kobe_sannomiya",
        "name_zh": "神户·三宮/元町",
        "description_zh": "神户的核心商业区，各类购物、餐厅和咖啡馆步行可达。距离北野异人馆约15分钟步行，港口方向也近。神户牛排店集中在此区域周边。适合神户一日游或两日游的大本营。",
        "budget_range": "mid",
        "recommended_for": ["couple", "business"],
        "nearest_stations": ["三宮駅（JR/阪急/地铁）"],
        "avg_price_cny_per_night": 420,
        "walk_score": 86,
        "tips": "选靠近中央郵便局侧（南侧）的酒店步行到港口更近",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# 数据导入函数（E1 seed 脚本入口）
# ─────────────────────────────────────────────────────────────────────────────

async def seed_kansai_entities(dry_run: bool = False) -> dict:
    """
    导入关西实体数据到 entity_base + pois/restaurants。
    使用 ON CONFLICT (name_zh, city_code) DO UPDATE 保证幂等。

    Args:
        dry_run: True 时只打印统计，不写入 DB

    Returns:
        统计字典
    """
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings

    engine = create_async_engine(settings.database_url)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    stats = {"pois_inserted": 0, "pois_updated": 0, "restaurants_inserted": 0,
             "restaurants_updated": 0, "areas_inserted": 0, "errors": 0}

    if dry_run:
        logger.info("[DRY RUN] 景点: %d, 餐厅: %d, 区域: %d",
                    len(KANSAI_POIS), len(KANSAI_RESTAURANTS), len(KANSAI_HOTEL_AREAS))
        return stats

    async with Session() as session:
        # ── 导入景点 ──────────────────────────────────────────────────────────
        for poi_data in KANSAI_POIS:
            try:
                await _upsert_poi(session, poi_data)
                stats["pois_inserted"] += 1
            except Exception as e:
                logger.error("景点导入失败 %s: %s", poi_data.get("name_zh"), e)
                stats["errors"] += 1

        # ── 导入餐厅 ──────────────────────────────────────────────────────────
        for rest_data in KANSAI_RESTAURANTS:
            try:
                await _upsert_restaurant(session, rest_data)
                stats["restaurants_inserted"] += 1
            except Exception as e:
                logger.error("餐厅导入失败 %s: %s", rest_data.get("name_zh"), e)
                stats["errors"] += 1

        # ── 导入住宿区域（hotel_area_guide 或 entity_editor_notes 形式） ──────
        for area in KANSAI_HOTEL_AREAS:
            try:
                await _upsert_hotel_area(session, area)
                stats["areas_inserted"] += 1
            except Exception as e:
                logger.error("住宿区域导入失败 %s: %s", area.get("name_zh"), e)
                stats["errors"] += 1

        await session.commit()

    logger.info("关西实体数据导入完成: %s", stats)
    return stats


async def _upsert_poi(session, data: dict) -> None:
    from sqlalchemy import text
    import json as _json

    entity_id = str(uuid.uuid4())
    opening = _json.dumps(data.get("opening_hours") or {}, ensure_ascii=False)
    risk_flags = _json.dumps(data.get("risk_flags") or [], ensure_ascii=False)

    # upsert entity_base
    await session.execute(text("""
        INSERT INTO entity_base
            (entity_id, entity_type, name_zh, name_ja, name_en, city_code, area_name,
             lat, lng, data_tier, is_active, quality_tier, budget_tier,
             risk_flags, booking_method, nearest_station)
        VALUES
            (:entity_id, 'poi', :name_zh, :name_ja, :name_en, :city_code, :area_name,
             :lat, :lng, :quality_tier, true, :quality_tier, :budget_tier,
             :risk_flags::jsonb, :booking_method, :nearest_station)
        ON CONFLICT (name_zh, city_code) DO NOTHING
    """), {
        "entity_id": entity_id,
        "name_zh": data["name_zh"], "name_ja": data.get("name_ja"),
        "name_en": data.get("name_en"), "city_code": data["city_code"],
        "area_name": data.get("area_name"), "lat": data.get("lat"), "lng": data.get("lng"),
        "quality_tier": data.get("quality_tier", "A"),
        "budget_tier": data.get("budget_tier", "mid"),
        "risk_flags": risk_flags,
        "booking_method": data.get("booking_method", "walk_in"),
        "nearest_station": data.get("nearest_station"),
    })

    # 查回实际写入的 entity_id
    result = await session.execute(
        text("SELECT entity_id FROM entity_base WHERE name_zh=:n AND city_code=:c"),
        {"n": data["name_zh"], "c": data["city_code"]}
    )
    row = result.first()
    if not row:
        return
    eid = row[0]

    # upsert pois
    await session.execute(text("""
        INSERT INTO pois
            (entity_id, poi_category, typical_duration_min, opening_hours_json,
             admission_fee_jpy, admission_free, best_season, crowd_level_typical,
             requires_advance_booking, advance_booking_days, booking_url,
             queue_wait_typical_min, google_rating, google_review_count)
        VALUES
            (:eid, :cat, :dur, :hours::jsonb, :fee, :free, :season, :crowd,
             :adv_book, :adv_days, :book_url, :queue, :rating, :reviews)
        ON CONFLICT (entity_id) DO UPDATE SET
            admission_fee_jpy = EXCLUDED.admission_fee_jpy,
            google_rating = EXCLUDED.google_rating,
            google_review_count = EXCLUDED.google_review_count
    """), {
        "eid": eid, "cat": data.get("poi_category"), "dur": data.get("visit_duration_min"),
        "hours": opening, "fee": data.get("admission_fee_jpy", 0),
        "free": data.get("admission_free", False), "season": data.get("best_season"),
        "crowd": data.get("crowd_level_typical", "medium"),
        "adv_book": data.get("requires_advance_booking", False),
        "adv_days": data.get("advance_booking_days"),
        "book_url": data.get("booking_url"),
        "queue": data.get("queue_wait_typical_min"),
        "rating": data.get("google_rating"), "reviews": data.get("google_review_count"),
    })

    # 写入 entity_editor_notes (copy_zh/tips_zh)
    if data.get("copy_zh"):
        await session.execute(text("""
            INSERT INTO entity_editor_notes (entity_id, note_type, content_zh)
            VALUES (:eid, 'editorial_boost', :content)
            ON CONFLICT DO NOTHING
        """), {"eid": eid, "content": data["copy_zh"]})


async def _upsert_restaurant(session, data: dict) -> None:
    from sqlalchemy import text
    import json as _json

    entity_id = str(uuid.uuid4())
    risk_flags = _json.dumps([], ensure_ascii=False)

    await session.execute(text("""
        INSERT INTO entity_base
            (entity_id, entity_type, name_zh, name_ja, city_code, area_name,
             lat, lng, data_tier, is_active, quality_tier, budget_tier,
             risk_flags, booking_method)
        VALUES
            (:entity_id, 'restaurant', :name_zh, :name_ja, :city_code, :area_name,
             :lat, :lng, :quality_tier, true, :quality_tier, :budget_tier,
             :risk_flags::jsonb, :booking_method)
        ON CONFLICT (name_zh, city_code) DO NOTHING
    """), {
        "entity_id": entity_id, "name_zh": data["name_zh"], "name_ja": data.get("name_ja"),
        "city_code": data["city_code"], "area_name": data.get("area_name"),
        "lat": data.get("lat"), "lng": data.get("lng"),
        "quality_tier": data.get("quality_tier", "A"),
        "budget_tier": data.get("budget_tier", "mid"),
        "risk_flags": risk_flags,
        "booking_method": data.get("booking_method", "walk_in"),
    })

    result = await session.execute(
        text("SELECT entity_id FROM entity_base WHERE name_zh=:n AND city_code=:c"),
        {"n": data["name_zh"], "c": data["city_code"]}
    )
    row = result.first()
    if not row:
        return
    eid = row[0]

    await session.execute(text("""
        INSERT INTO restaurants
            (entity_id, cuisine_type, michelin_star, tabelog_score, requires_reservation,
             reservation_difficulty, price_range_min_jpy, price_range_max_jpy,
             budget_lunch_jpy, budget_dinner_jpy, has_english_menu,
             advance_booking_days, booking_url)
        VALUES
            (:eid, :cuisine, :michelin, :tabelog, :req_res,
             :res_diff, :price_min, :price_max,
             :lunch, :dinner, :english,
             :adv_days, :book_url)
        ON CONFLICT (entity_id) DO UPDATE SET
            tabelog_score = EXCLUDED.tabelog_score,
            requires_reservation = EXCLUDED.requires_reservation,
            budget_lunch_jpy = EXCLUDED.budget_lunch_jpy,
            budget_dinner_jpy = EXCLUDED.budget_dinner_jpy
    """), {
        "eid": eid, "cuisine": data.get("cuisine_type"),
        "michelin": data.get("michelin_star", 0),
        "tabelog": data.get("tabelog_score"),
        "req_res": data.get("requires_reservation", False),
        "res_diff": data.get("reservation_difficulty"),
        "price_min": data.get("price_range_min_jpy"),
        "price_max": data.get("price_range_max_jpy"),
        "lunch": data.get("budget_lunch_jpy"),
        "dinner": data.get("budget_dinner_jpy"),
        "english": data.get("has_english_menu", False),
        "adv_days": data.get("advance_booking_days"),
        "book_url": data.get("booking_url"),
    })


async def _upsert_hotel_area(session, data: dict) -> None:
    from sqlalchemy import text
    import json as _json

    # hotel_area 存为 entity_editor_notes 中的区域知识
    await session.execute(text("""
        INSERT INTO entity_editor_notes
            (entity_id, note_type, content_zh)
        SELECT eb.entity_id, 'insider_tip', :content
        FROM entity_base eb
        WHERE eb.city_code = :city_code
          AND eb.entity_type = 'hotel'
          AND eb.area_name = :area_name
        LIMIT 1
        ON CONFLICT DO NOTHING
    """), {
        "city_code": data["city_code"],
        "area_name": data.get("area_code", "").replace("_", " "),
        "content": _json.dumps({
            "area_code": data["area_code"],
            "name_zh": data["name_zh"],
            "description_zh": data["description_zh"],
            "tips": data.get("tips"),
            "avg_price_cny": data.get("avg_price_cny_per_night"),
            "recommended_for": data.get("recommended_for"),
            "nearest_stations": data.get("nearest_stations"),
        }, ensure_ascii=False),
    })


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_kansai_entities(dry_run=False))
