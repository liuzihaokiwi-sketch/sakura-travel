"""osaka_kyoto_benchmark

Revision ID: 20260321_140000
Revises: 20260321_130000
Create Date: 2026-03-21 14:00:00

大阪/京都 Day1 标杆模板（品质炸弹 Phase 1 T7）
- 大阪 5 日模板（Day1：道顿堀→黑门市场→心斋桥→通天阁/新世界）
- 京都 5 日模板（Day1：伏见稻荷→祇园→锦市场→哲学之道）
- 每个景点含 photo_tip / avoid_tip / tabelog_score / evidence_text
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime

# revision identifiers, used by Alembic.
revision = "20260321_140000"
down_revision = "20260321_130000"
branch_labels = None
depends_on = None

# ---------------------------------------------------------------------------
# 大阪 5 日标杆模板
# ---------------------------------------------------------------------------
OSAKA_TEMPLATE = {
    "id": str(uuid.uuid4()),
    "city": "osaka",
    "title": "大阪精华5日",
    "duration_days": 5,
    "theme": "classic",
    "quality_tier": "benchmark",
    "scene_variants": {
        "couple": {"tag_boost": ["romantic_spot", "night_view", "photo_friendly"], "weight": 1.3},
        "family": {"tag_boost": ["kid_friendly", "indoor", "food_diverse"], "weight": 1.2},
        "solo": {"tag_boost": ["street_food", "nightlife", "authentic_local"], "weight": 1.1},
    },
    "days": [
        {
            "day_number": 1,
            "theme": "道顿堀 × 新世界：大阪灵魂首日",
            "spots": [
                {
                    "slot": "morning",
                    "entity_name": "黑门市场",
                    "entity_name_ja": "黒門市場",
                    "category": "market",
                    "duration_min": 90,
                    "open_time": "09:00",
                    "close_time": "18:00",
                    "address": "大阪府大阪市中央区日本橋2丁目",
                    "geo": {"lat": 34.6645, "lng": 135.5068},
                    "tabelog_score": 3.8,
                    "google_rating": 4.2,
                    "review_count": 8420,
                    "evidence_text": "被称为「大阪的厨房」，营业超120年。河豚刺身套餐均价¥5000，比道顿堀同档次餐厅便宜约30%。早上10点前食材最新鲜。",
                    "copy_zh": "大阪人的「厨房」——120年历史的黑门市场，用河豚刺身和松叶蟹开启你的大阪美食之旅。比道顿堀同品质便宜三成，食材新鲜度是关键。",
                    "photo_tip": "站在市场入口仰拍大型河豚灯笼招牌，焦距50mm以上，顺光（上午东侧最佳）。店铺摊位陈列从通道尽头向外俯拍层次感更强。",
                    "avoid_tip": "周一部分鱼摊休息；持螃蟹试吃后再选购正品，避免高价坑。现金为主，备足零钱。",
                    "tags": ["food_market", "authentic_local", "photo_friendly", "morning_only"],
                },
                {
                    "slot": "late_morning",
                    "entity_name": "道顿堀",
                    "entity_name_ja": "道頓堀",
                    "category": "landmark",
                    "duration_min": 60,
                    "open_time": "00:00",
                    "close_time": "23:59",
                    "address": "大阪府大阪市中央区道頓堀",
                    "geo": {"lat": 34.6687, "lng": 135.5014},
                    "tabelog_score": None,
                    "google_rating": 4.4,
                    "review_count": 98000,
                    "evidence_text": "大阪地标步行街，固力果跑步人招牌自1935年沿用至今。戎桥处是大阪最知名拍照打卡地，每晚22-23点灯光效果最佳。",
                    "copy_zh": "固力果跑步人、螃蟹道乐巨蟹招牌……道顿堀是大阪人说「喫倒れ（吃到倒）」文化的具象。白天逛街，夜晚看灯，两种风情截然不同。",
                    "photo_tip": "站在戎桥（戒橋）向西拍摄固力果跑步人：傍晚6-7点逆光金色效果绝佳；夜间22点霓虹全亮，需三脚架长曝光。早晨8点前人少，适合拍干净街景。",
                    "avoid_tip": "道顿堀商家价格普遍比周边贵20-30%，只建议拍照打卡，用餐选黑门或心斋桥背街。持螃蟹/招财猫道具收费的街头表演者请注意拒绝。",
                    "tags": ["landmark", "night_view", "photo_friendly", "street_food"],
                },
                {
                    "slot": "lunch",
                    "entity_name": "美津の（章鱼烧）",
                    "entity_name_ja": "美津の",
                    "category": "restaurant",
                    "duration_min": 45,
                    "open_time": "11:00",
                    "close_time": "22:00",
                    "address": "大阪府大阪市中央区道頓堀1-4-15",
                    "geo": {"lat": 34.6682, "lng": 135.5011},
                    "tabelog_score": 3.87,
                    "google_rating": 4.5,
                    "review_count": 12500,
                    "price_range": "¥500-800/人",
                    "evidence_text": "大阪章鱼烧老字号（1945年创业），Tabelog 3.87分，超12000条评价。外脆内软的「たこ焼き」，原味+葱花版最受欢迎。午饭时段11:30-13:30排队约20分钟。",
                    "copy_zh": "大阪人认证的章鱼烧 —— 美津の自1945年未改过食谱。8个一份¥600，外壳脆响、内里柔嫩流心，配日式酱汁和柴鱼片。这才是大阪的原版风味。",
                    "photo_tip": "章鱼烧出锅时拍：点餐后请店员告知，抓住刚出锅10秒冒烟瞬间，手持18-35mm广角，特写纸盘+柴鱼花飞舞画面。",
                    "avoid_tip": "避免道顿堀主街的网红章鱼烧摊（白底红字的大型连锁），价格贵且份量少。美津の在道顿堀1-4-15，注意地址勿走错。",
                    "tags": ["must_eat", "street_food", "authentic_local", "budget_friendly"],
                },
                {
                    "slot": "afternoon",
                    "entity_name": "心斋桥筋商店街",
                    "entity_name_ja": "心斎橋筋商店街",
                    "category": "shopping",
                    "duration_min": 90,
                    "open_time": "10:00",
                    "close_time": "20:30",
                    "address": "大阪府大阪市中央区心斎橋筋",
                    "geo": {"lat": 34.6724, "lng": 135.5011},
                    "tabelog_score": None,
                    "google_rating": 4.3,
                    "review_count": 45000,
                    "evidence_text": "全长580米的有顶购物街，品牌覆盖ZARA/H&M到Bape/Kith等潮牌。二楼「美国村（アメリカ村）」聚集古着店和小众设计师品牌，Tabelog 4.0+餐厅密度极高。",
                    "copy_zh": "大阪人流量最大的购物街——580米有顶拱廊，从ZARA到Bape一字排开。二楼的美国村才是潮人心头好：Vintage古着、独立设计师、地下Live House，大阪次文化的发源地。",
                    "photo_tip": "美国村三角公园（三角公園）是街头文化聚集地：周末下午有涂鸦、Cosplay、街舞，拍人文纪实效果极佳。商店街整体透视感强，超广角16mm可拍压缩感顶棚。",
                    "avoid_tip": "心斋桥药妆店价格已不比日本其他城市有优势，高价品建议机场免税购买。黄金周和长假人流极大，建议早10点前或晚7点后前往。",
                    "tags": ["shopping", "street_culture", "photo_friendly", "youth_culture"],
                },
                {
                    "slot": "evening",
                    "entity_name": "新世界・通天阁",
                    "entity_name_ja": "新世界・通天閣",
                    "category": "landmark",
                    "duration_min": 120,
                    "open_time": "10:00",
                    "close_time": "21:00",
                    "address": "大阪府大阪市浪速区恵美須東1-18-6",
                    "geo": {"lat": 34.6523, "lng": 135.5062},
                    "tabelog_score": None,
                    "google_rating": 4.2,
                    "review_count": 32000,
                    "ticket_price": "通天阁¥1000/人",
                    "evidence_text": "通天阁高103米，建于1956年，大阪「昭和复古」氛围最浓厚的地区。周边串炸（串カツ）店密集，大阪串炸规则「ソース二度漬け禁止（禁止蘸两次酱）」的起源地。夜晚灯光秀18:00-22:00整点定时。",
                    "copy_zh": "新世界是大阪版的「下町」——昭和复古霓虹灯、串炸小店、老派大阪腔，和道顿堀的网红商业截然不同。通天阁顶层360度俯瞰大阪全景，傍晚时分金色城市轮廓。记住串炸铁则：「禁止蘸两次酱」。",
                    "photo_tip": "通天阁最佳外拍机位：距离南侧100米的「じゃんじゃん横丁（横丁入口）」向北仰拍，落日余晖时分塔体与霓虹同框。顶层望远镜¥100/次，可拍180km能见度良好时的六甲山。",
                    "avoid_tip": "通天阁周边地段历史上治安较差，夜间建议结伴，贵重物品不外露。串炸店避免入「团体游客指定店」，认准本地人多的小店。登塔前确认天气，雾天和雨天几乎无视野。",
                    "tags": ["landmark", "night_view", "retro_atmosphere", "food_nearby"],
                },
            ],
            "transport_notes": [
                "黑门市场→道顿堀：步行12分钟",
                "道顿堀→心斋桥：步行5分钟",
                "心斋桥→新世界：地铁御堂筋线/长堀鶴見緑地線换乗，约15分钟",
                "建议购买大阪1日/2日交通卡（¥800/¥1600），地铁巴士无限乘",
            ],
            "estimated_budget": "¥800-1500（餐饮）+ ¥1000（通天阁门票）",
        }
    ],
}

# ---------------------------------------------------------------------------
# 京都 5 日标杆模板
# ---------------------------------------------------------------------------
KYOTO_TEMPLATE = {
    "id": str(uuid.uuid4()),
    "city": "kyoto",
    "title": "京都精华5日",
    "duration_days": 5,
    "theme": "classic",
    "quality_tier": "benchmark",
    "scene_variants": {
        "couple": {"tag_boost": ["romantic_spot", "zen_garden", "traditional_arts"], "weight": 1.4},
        "family": {"tag_boost": ["kid_friendly", "hands_on_experience", "outdoor"], "weight": 1.2},
        "solo": {"tag_boost": ["zen_culture", "photography", "authentic_local"], "weight": 1.3},
    },
    "days": [
        {
            "day_number": 1,
            "theme": "伏见稻荷 × 祇园：京都灵魂首日",
            "spots": [
                {
                    "slot": "early_morning",
                    "entity_name": "伏见稻荷大社",
                    "entity_name_ja": "伏見稲荷大社",
                    "category": "shrine",
                    "duration_min": 120,
                    "open_time": "00:00",
                    "close_time": "23:59",
                    "address": "京都府京都市伏見区深草藪之内町68",
                    "geo": {"lat": 34.9671, "lng": 135.7727},
                    "tabelog_score": None,
                    "google_rating": 4.7,
                    "review_count": 245000,
                    "ticket_price": "免费",
                    "evidence_text": "全日本约3万座稻荷神社的总本社，拥有超1万座朱红鸟居，蜿蜒山路全程约4km、徒步2-3小时。每年外国旅行者最受欢迎日本景点TOP1（TripAdvisor 2023-2024连续排名）。清晨6点前人流量仅为中午的5%。",
                    "copy_zh": "1万座朱红鸟居在晨雾中连成隧道——伏见稻荷是TripAdvisor连续两年外国旅行者最爱日本景点。清晨6点前独占这条神道，是不需要花钱的奢侈体验。",
                    "photo_tip": "「千本鸟居」最佳机位：右侧通道（上行）清晨6-7点逆光拍摄，鸟居内透出金色散射光。人少时使用F8小光圈保证前后景清晰；有薄雾日效果翻倍。山顶「一ノ峰」鸟居更稀疏，拍局部特写更有禅意。",
                    "avoid_tip": "10点后人流量极大，千本鸟居几乎无法拍到「无人」画面。全程山路4km、爬升约230米，不适合拖行李箱前来，建议运动鞋。狐狸纪念品在山门内部的稻荷茶屋更便宜。",
                    "tags": ["cultural_heritage", "photo_friendly", "early_morning_best", "free_admission", "spiritual"],
                },
                {
                    "slot": "late_morning",
                    "entity_name": "锦市场",
                    "entity_name_ja": "錦市場",
                    "category": "market",
                    "duration_min": 60,
                    "open_time": "09:00",
                    "close_time": "18:00",
                    "address": "京都府京都市中京区錦小路通",
                    "geo": {"lat": 35.0049, "lng": 135.7659},
                    "tabelog_score": 3.7,
                    "google_rating": 4.3,
                    "review_count": 32000,
                    "evidence_text": "被称为「京都的厨房」，全长390米，约100家商铺。京都独有食材：万願寺とうがらし（甜辣椒）、賀茂茄子（圆茄）、湯葉（豆腐皮）等。创业于江户时代，有400年历史。",
                    "copy_zh": "「京都的厨房」——锦市场390米拱廊内，100家店铺出售京都独有食材。试吃文化浓厚：腌渍物、湯葉、京野菜串……一条街走下来就是一顿京都风味早餐。",
                    "photo_tip": "市场中央「錦天満宮」鸟居被两侧建筑夹住、末端嵌入墙内，是网红拍照点（「壁に刺さる鳥居」）。市场通道用28-35mm拍摄两侧商品延伸感最佳，色彩对比鲜艳。",
                    "avoid_tip": "锦市场商品以试吃和散买为主，大包装商品在周边超市更划算。部分摊位对拍照敏感，食品类拍摄前请确认。周三部分商铺休息。",
                    "tags": ["food_market", "authentic_local", "photo_friendly", "cultural_heritage"],
                },
                {
                    "slot": "lunch",
                    "entity_name": "お豆腐料理 松ヶ枝",
                    "entity_name_ja": "お豆腐料理 松ヶ枝",
                    "category": "restaurant",
                    "duration_min": 60,
                    "open_time": "11:30",
                    "close_time": "21:00",
                    "address": "京都府京都市東山区祗園町北側347-70",
                    "geo": {"lat": 35.0036, "lng": 135.7785},
                    "tabelog_score": 3.84,
                    "google_rating": 4.4,
                    "review_count": 2800,
                    "price_range": "¥1500-3000/人",
                    "evidence_text": "Tabelog 3.84分，祇园地区豆腐料理专门店，提供京都精进料理风格的豆腐御膳。使用京都北大路 大豆制作的「寄せ豆腐」，每日新鲜制作。附近竞品均为¥3500+，性价比突出。",
                    "copy_zh": "京都饮食文化的精髓是「引き算（做减法）」——松ヶ枝的豆腐御膳用6-8道小品呈现这种克制之美。寄せ豆腐的柔嫩和精进料理的清淡，在祇园的午后最对味。",
                    "photo_tip": "豆腐御膳上菜时全景俯拍（F5.6，自然光），再拍竹笼蒸豆腐的热气升腾特写。店内有格子推拉门（格子戸）背景，是京町家氛围代表。",
                    "avoid_tip": "祇园地区餐厅普遍价高，建议提前预约（特别是周末）。不接受网络订餐平台，请直接致电。外带包装不提供，不适合边走边吃。",
                    "tags": ["must_eat", "traditional_cuisine", "healthy", "vegetarian_friendly"],
                },
                {
                    "slot": "afternoon",
                    "entity_name": "祇园・花见小路",
                    "entity_name_ja": "祇園・花見小路",
                    "category": "cultural_district",
                    "duration_min": 90,
                    "open_time": "00:00",
                    "close_time": "23:59",
                    "address": "京都府京都市東山区祇園町南側",
                    "geo": {"lat": 35.0036, "lng": 135.7782},
                    "tabelog_score": None,
                    "google_rating": 4.4,
                    "review_count": 78000,
                    "evidence_text": "全长500米的石板街道，两侧为传统町家（machiya）茶屋。现存约60家御茶屋，仍有约50位艺妓（Geiko）和见习艺妓（Maiko）活跃。傍晚5-7点「出店（おいでやす）」时间，有机会目睹艺妓赴约身影。",
                    "copy_zh": "花见小路是京都「一期一会」精神的缩影——傍晚5点，艺妓盛装走过石板路，是比任何舞台表演都真实的京都风情。即使没有艺妓，石板路+町家+灯笼的组合已经是最完美的京都符号。",
                    "photo_tip": "傍晚5-6点是最佳拍摄窗口：①町家窗格透出暖黄灯光；②路灯刚亮未亮、自然光+人工光黄金平衡；③若遇艺妓出行，提前站在路两侧，切勿追拍或招呼，从侧面45°拍最自然。",
                    "avoid_tip": "花见小路附近居民区有明确「禁止摄影」标识的区域，请严格遵守。强烈禁止跟踪或正面拦截艺妓拍照，已有外国游客因此引发外交事件。进入茶屋需要介绍人制度，随意进入被拒绝为正常。",
                    "tags": ["cultural_heritage", "photo_friendly", "evening_best", "traditional_arts", "must_see"],
                },
                {
                    "slot": "evening",
                    "entity_name": "哲学之道",
                    "entity_name_ja": "哲学の道",
                    "category": "scenic_path",
                    "duration_min": 60,
                    "open_time": "00:00",
                    "close_time": "23:59",
                    "address": "京都府京都市左京区（若王子神社-銀閣寺）",
                    "geo": {"lat": 35.0222, "lng": 135.7953},
                    "tabelog_score": None,
                    "google_rating": 4.5,
                    "review_count": 42000,
                    "ticket_price": "免费",
                    "evidence_text": "沿琵琶湖疏水渠延伸约2km的步行道，两侧约450棵吉野樱。得名于哲学家西田幾多郎每日散步于此。樱花季（3月下旬-4月上旬）是京都最热门赏樱点，枫叶季（11月中旬）同样壮观。",
                    "copy_zh": "哲学家西田幾多郎每日在此漫步冥想，留下了日本哲学的黄金年代。河渠倒映垂樱或红枫，傍晚光线最柔和，是一条适合放空思考的道路——在快节奏旅行中，这段散步时间尤为珍贵。",
                    "photo_tip": "疏水渠倒影拍摄：蹲低至水面视角，用疏水渠护栏作为前景框架。傍晚西侧逆光，渠面金色反射。樱花季：樱花隧道仰拍（大光圈F2.8，天空留白）；枫叶季：红叶+石桥+寺庙三要素构图。",
                    "avoid_tip": "哲学之道南北端分别连接熊野若王子神社和银阁寺，注意行进方向避免走回头路。沿途无大型餐厅，建议在祇园用餐后再前往。冬季17点天黑，路灯稀少，提前返回。",
                    "tags": ["scenic_path", "nature", "free_admission", "photo_friendly", "contemplative"],
                },
            ],
            "transport_notes": [
                "伏见稻荷→锦市场：地铁乌丸线 → 烏丸御池换乘东西线 → 京都市役所前，约25分钟",
                "锦市场→祇园：步行12分钟",
                "祇园→哲学之道：步行20分钟或公交5分钟",
                "建议购买京都巴士1日券（¥700），覆盖主要景点间公交线路",
            ],
            "estimated_budget": "¥1500-3000（餐饮）+ ¥0（全日景点免费）",
        }
    ],
}


def upgrade() -> None:
    """插入大阪/京都标杆模板"""
    conn = op.get_bind()

    now = datetime.utcnow()

    for template in [OSAKA_TEMPLATE, KYOTO_TEMPLATE]:
        # 检查是否已有同城市的 benchmark 模板
        existing = conn.execute(
            sa.text(
                "SELECT id FROM route_templates WHERE city = :city AND quality_tier = 'benchmark' LIMIT 1"
            ),
            {"city": template["city"]},
        ).fetchone()

        if existing:
            # 更新已有模板
            conn.execute(
                sa.text(
                    """
                    UPDATE route_templates SET
                        title = :title,
                        template_data = :template_data,
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "id": str(existing[0]),
                    "title": template["title"],
                    "template_data": sa.cast(str(template), postgresql.JSONB),
                    "updated_at": now,
                },
            )
        else:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO route_templates (id, city, title, duration_days, theme, quality_tier, template_data, created_at, updated_at)
                    VALUES (:id, :city, :title, :duration_days, :theme, :quality_tier, :template_data::jsonb, :created_at, :updated_at)
                    """
                ),
                {
                    "id": template["id"],
                    "city": template["city"],
                    "title": template["title"],
                    "duration_days": template["duration_days"],
                    "theme": template["theme"],
                    "quality_tier": template["quality_tier"],
                    "template_data": str(template).replace("'", '"').replace("None", "null").replace("True", "true").replace("False", "false"),
                    "created_at": now,
                    "updated_at": now,
                },
            )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "DELETE FROM route_templates WHERE city IN ('osaka', 'kyoto') AND quality_tier = 'benchmark'"
        )
    )
