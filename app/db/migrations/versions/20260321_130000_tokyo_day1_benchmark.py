"""东京 Day1 标杆方案 — 推荐理由证据化 + 避坑提醒 + 拍照提示

Revision ID: 20260321_130000
Revises: 20260321_120000
Create Date: 2026-03-21
"""
from __future__ import annotations
import json
from alembic import op
from sqlalchemy import text

revision = "20260321_130000"
down_revision = "20260321_120000"
branch_labels = None
depends_on = None

# ── 东京经典 Day1 标杆模板数据 ────────────────────────────────────────────────
# 线路：上野→浅草→晴空塔→隅田川夕阳
# 设计逻辑：文化密度高 + 交通紧凑 + 早到避开人流 + 有照片机位说明 + 有避坑

TOKYO_DAY1_BENCHMARK = {
    "day_number": 1,
    "city_code": "tokyo",
    "day_theme": "上野·浅草·晴空塔 — 东京最经典的文化开场",
    "transport_note": "全程步行+东京地铁（银座线），无需换乘超过2次",
    "avoid_tips": [
        "浅草寺正门（雷门）10:00后人超多，强烈建议08:30前到，光线也更好",
        "仲见世通り商店街11:00才开门，不要一早冲过去等",
        "晴空塔观景台建议提前在官网买票，现场当日票经常售罄（尤其周末）",
        "隅田川边17:30-18:30是黄金摄影时段，带三脚架或手机稳定器"
    ],
    "items": [
        {
            "sort_order": 1,
            "item_type": "poi",
            "entity_name": "上野恩赐公园",
            "start_time": "09:00",
            "end_time": "10:00",
            "duration_min": 60,
            "copy_zh": "东京最大的公共公园，3月下旬的樱花季期间约1200棵染井吉野樱同时盛开，是全日本最密集的赏樱地之一。非樱花季也值得来——这里有东京国立博物馆、不忍池和西乡隆盛铜像，1小时能把"明治维新后东京的公共生活"走个完整。",
            "tips_zh": "建议09:00入园，工作日人少，光线从东边照进来，不忍池倒影最漂亮。不需要进任何博物馆，公园内步行即可。",
            "photo_tip": "不忍池喷泉+远处东京塔同框：站在池南岸往北拍，35mm焦段效果最好。",
            "avoid_tip": None,
            "tags": ["自然", "历史", "免费", "樱花季必去"],
            "area": "ueno",
            "google_maps_url": "https://maps.app.goo.gl/UenoKoenExample"
        },
        {
            "sort_order": 2,
            "item_type": "transport",
            "entity_name": "上野→浅草（地铁）",
            "start_time": "10:00",
            "end_time": "10:15",
            "duration_min": 15,
            "copy_zh": "乘坐东京地铁银座线，上野站→浅草站，仅2站，约5分钟。IC卡（Suica/PASMO）刷卡即走，车费约170日元。",
            "tips_zh": "在上野站坐银座线浅草方向（向东），注意不要坐反向浅草桥方向的车。",
            "tags": ["交通"],
            "area": "ueno"
        },
        {
            "sort_order": 3,
            "item_type": "poi",
            "entity_name": "浅草寺·雷门",
            "start_time": "10:15",
            "end_time": "11:30",
            "duration_min": 75,
            "copy_zh": "创建于628年的东京最古老寺庙，雷门大灯笼是日本被拍摄次数最多的地标之一。仲见世通り250米长的参道两侧有90多家老铺，卖的是传承百年的人形烧、雷おこし（米花糖）和传统工艺品——不是普通的旅游纪念品一条街。建议进去买一个'雷5'人形烧（1个150日元），现烤现卖，内馅选红豆，这才是当地人吃法。",
            "tips_zh": "雷门正面最佳机位在上午阳光从东南方向照来时，灯笼色彩最饱满。进入本堂内殿需脱鞋，建议穿方便脱穿的鞋。",
            "photo_tip": "雷门灯笼仰拍：蹲下来用手机仰拍，把灯笼和本堂宝楼门纳入同框，效果远胜平拍。夜晚灯笼亮灯后（日落后约30分钟），有另一番质感。",
            "avoid_tip": "10:30后仲见世通り人流急增，逛商店建议10:15入场直接走到底再慢慢往回逛（大多数人从正门进、顺着走，你反向走就不堵了）。",
            "tags": ["文化", "历史", "寺庙", "拍照圣地", "免费参观"],
            "area": "asakusa",
            "admission": "免费（本堂外观），寺内博物馆等需另购票",
            "google_maps_url": "https://maps.app.goo.gl/SensoujiExample"
        },
        {
            "sort_order": 4,
            "item_type": "restaurant",
            "entity_name": "天丼 金子半之助（浅草店）",
            "start_time": "11:30",
            "end_time": "12:30",
            "duration_min": 60,
            "copy_zh": "东京最知名的江户前天丼专门店之一，Tabelog 评分 3.8+（天丼类别全东京排名前5）。招牌「元祖天丼」：特大车海老2尾+穴子（星鳗）+玉子+江户蔬菜，酱汁是秘制减盐版，比一般天丼淡而不腻。人均约¥1,100（合人民币55元），在东京这个级别的天丼是顶级性价比。",
            "tips_zh": "11:30开门时到通常等5-10分钟，12:00后等待时间超过30分钟。单人用餐效率高，可以在吧台坐，边看厨师炸天妇罗边吃，体验感很好。现金优先（可刷卡，但高峰期收银慢）。",
            "photo_tip": "天丼端上来立刻拍：酱汁会渗进米饭，1分钟后颜色和光泽最佳。侧光角度（靠窗坐）效果最好。",
            "avoid_tip": "不接受预约，只能现场等位。周末12:00-13:30等待时间可能超过45分钟，尽量工作日或提前到。",
            "tags": ["餐厅", "天丼", "性价比", "当地推荐"],
            "area": "asakusa",
            "price_range": "¥900-1500/人",
            "reservation": "不接受预约",
            "tabelog_score": "3.82",
            "google_maps_url": "https://maps.app.goo.gl/KanekohannousukeExample"
        },
        {
            "sort_order": 5,
            "item_type": "poi",
            "entity_name": "东京晴空塔",
            "start_time": "13:00",
            "end_time": "15:30",
            "duration_min": 150,
            "copy_zh": "634米，世界第二高塔（仅次于迪拜哈利法塔无线电发射）。天望台350米有全玻璃落地窗360度俯瞰东京，天气好时能看到富士山（推荐10月至2月，能见度最高）。天望回廊445米是全球最高的户外环形观光走廊，在上面走一圈约15分钟，会有一种'漂浮在东京上空'的体验。底层商业（东京晴空街道）有200多家餐厅和店铺，逛完一层要1小时。",
            "tips_zh": "强烈建议提前在官网购票（https://www.tokyo-skytree.jp/cn/）。网购比现场便宜约400-600日元，且可选时段入场，避免等待。若有富士山远眺需求，推荐午后2-4点天空较清澈时入场。",
            "photo_tip": "天望台内：找到角落的玻璃地板（Glass Floor），俯拍城市照最有冲击力。天望回廊：黄昏时分（16:00-18:00）站在西侧，可以拍到夕阳+东京城市剪影，手机长按曝光补偿-1档，防止过曝。",
            "avoid_tip": "天望台350米的门票不包含445米天望回廊，需另加购（约1000日元）。建议两层都买，差距明显。云/阴天时能见度很差，可以在官网查当日能见度预报再决定。",
            "tags": ["地标", "观景台", "拍照圣地", "城市全景"],
            "area": "oshiage",
            "admission": "350m天望台成人¥2100/儿童¥950；445m天望回廊另加¥1000",
            "reservation": "强烈建议官网预购",
            "google_maps_url": "https://maps.app.goo.gl/TokyoSkyTreeExample"
        },
        {
            "sort_order": 6,
            "item_type": "transport",
            "entity_name": "晴空塔→隅田川（步行）",
            "start_time": "15:30",
            "end_time": "15:45",
            "duration_min": 15,
            "copy_zh": "晴空塔出来后直接往西步行约700米即到隅田川东岸。建议沿途经过押上商店街，有几家小众咖啡店值得随机进一家歇脚。",
            "tags": ["交通", "步行"],
            "area": "oshiage"
        },
        {
            "sort_order": 7,
            "item_type": "poi",
            "entity_name": "隅田川·言问桥夕阳机位",
            "start_time": "15:45",
            "end_time": "17:30",
            "duration_min": 105,
            "copy_zh": "隅田川是东京最重要的城市河流，江户时代是货运要道，两岸至今保留着12座各具特色的桥梁。言问桥是其中最有文学感的一座——夏目漱石、芥川龙之介都曾以此为创作背景。黄昏时站在桥上，晴空塔在左、吾妻桥在右、河面反光如镜，是东京城市风光的教科书级别构图。",
            "tips_zh": "日落前30-45分钟抵达，在言问桥栏杆处等待光线变化。日落时间可在手机天气APP查询（东京日落因季节差异大）。周边没有大型商店，建议在晴空塔附近购买饮料补给。",
            "photo_tip": "言问桥标准构图：站在桥中部，以桥面护栏为前景，晴空塔为远景垂直线，用超广角（16mm等效）拍全景。水面波光用HDR模式。若有三脚架，日落后20分钟蓝调时刻拍长曝光，水面会变成绸缎质感。",
            "avoid_tip": "夏季（7-8月）傍晚蚊子多，建议备驱蚊液。台风季（9月）河边风大，注意固定随身物品。",
            "tags": ["自然", "摄影", "文化", "夕阳", "免费"],
            "area": "asakusa",
            "google_maps_url": "https://maps.app.goo.gl/KotoibasiExample"
        },
        {
            "sort_order": 8,
            "item_type": "restaurant",
            "entity_name": "浅草 今半（仲见世店）— 寿喜烧晚餐",
            "start_time": "18:00",
            "end_time": "19:30",
            "duration_min": 90,
            "copy_zh": "创业1895年，日本最负盛名的寿喜烧老店之一，Tabelog 4.0+（寿喜烧类别东京前3）。使用关东风寿喜烧做法（先煎牛肉再加酱汁），与关西风完全不同——酱油、砂糖、清酒三者比例是百年传承配方，甜度和鲜度的平衡极为精准。肉质使用日本和牛A4级别，蘸生蛋液后入口，这是东京最正宗的吃法。人均约¥8,000-15,000（合人民币400-750元），属于日本中高端餐厅，适合作为第一天的仪式感晚餐。",
            "tips_zh": "必须提前预约，旺季（3月樱花季/11月红叶季）至少提前2周。可以在官网或通过电话预约，官网有中文选项。入座后服务员会示范寿喜烧做法，按他们说的步骤来。",
            "photo_tip": "肉片在锅里翻折时拍：铁锅反光+酱汁沸腾+肉色红润，是标准的美食视频素材。用手机ProRes格式或慢动作拍更有质感。",
            "avoid_tip": "寿喜烧的锅汁后期会越来越咸，到后半段建议少蘸汁或加豆腐平衡味道。结束时服务员会问要不要用剩余锅汁做乌冬面（udon締め），建议答应，这是隐藏吃法。",
            "tags": ["餐厅", "寿喜烧", "老店", "仪式感", "需预约"],
            "area": "asakusa",
            "price_range": "¥8,000-15,000/人",
            "reservation": "强烈建议提前预约",
            "tabelog_score": "4.06",
            "google_maps_url": "https://maps.app.goo.gl/ImahannExample"
        }
    ]
}

# ── 完整 Day1 模板插入到 route_templates ────────────────────────────────────

TOKYO_CLASSIC_5D_TEMPLATE = {
    "meta": {
        "template_code": "tokyo_classic_5d",
        "name_zh": "东京经典5日",
        "city_code": "tokyo",
        "duration_days": 5,
        "theme": "classic",
        "tagline_zh": "东京最值得去的地方，用5天走完"
    },
    "scene_variants": {
        "couple": {
            "tagline_suffix_zh": "情侣专属",
            "tag_weight_overrides": {"romantic": 1.5, "hidden_gem": 1.2},
            "filter_exclude_tags": {"family_friendly": 0}
        },
        "family": {
            "tagline_suffix_zh": "亲子推荐",
            "tag_weight_overrides": {"family_friendly": 1.8, "kid_friendly": 2.0},
            "filter_exclude_tags": {"bar": 0}
        },
        "solo": {
            "tagline_suffix_zh": "独行侠玩法",
            "tag_weight_overrides": {"hidden_gem": 1.5, "local_favorite": 1.3}
        }
    },
    "days": [
        TOKYO_DAY1_BENCHMARK,
        {
            "day_number": 2,
            "city_code": "tokyo",
            "day_theme": "新宿·涩谷·原宿 — 时尚与繁华",
            "transport_note": "山手线串联全天，IC卡通行",
            "avoid_tips": [
                "涩谷十字路口拍照请站在Starbucks二楼或Q's Mall Sky Garden平台，不要站在路中间",
                "原宿竹下通り周末13:00-17:00人流量峰值，建议平日或早上11:00前到"
            ],
            "items": [
                {
                    "sort_order": 1,
                    "item_type": "poi",
                    "entity_name": "新宿御苑",
                    "start_time": "09:00",
                    "end_time": "10:30",
                    "duration_min": 90,
                    "copy_zh": "东京最大的国家公园式花园，同时拥有法式、英式、日式三种庭园风格，面积58公顷。非樱花季的绿意同样迷人，是新宿商业区里的'城市绿肺'。",
                    "tips_zh": "门票¥500，园内不准喝酒（特殊开放日除外），适合早上散步。",
                    "area": "shinjuku",
                    "tags": ["自然", "花园", "樱花季"]
                },
                {
                    "sort_order": 2,
                    "item_type": "poi",
                    "entity_name": "涩谷十字路口",
                    "start_time": "14:00",
                    "end_time": "15:00",
                    "duration_min": 60,
                    "copy_zh": "全球最繁忙的行人过街之一，每次绿灯约3000人同时穿越。'涩谷Scramble'已成为现代东京的象征符号，无数电影和广告在此取景。",
                    "tips_zh": "真正的体验在于融入其中过一次，拍照最佳位置是二楼咖啡厅或对面商场的观景台。",
                    "area": "shibuya",
                    "tags": ["地标", "拍照", "城市"]
                },
                {
                    "sort_order": 3,
                    "item_type": "restaurant",
                    "entity_name": "一兰拉面（涩谷店）",
                    "start_time": "12:00",
                    "end_time": "13:00",
                    "duration_min": 60,
                    "copy_zh": "福冈发源的豚骨拉面连锁，以独特的单人隔间'味集中Counter'闻名。汤底浓郁但不腥，面条细而有弹性，辣度/浓度/葱量可以自由调整。对拉面爱好者来说是必打卡之一。",
                    "tips_zh": "人均约¥1,200。可以用机器买票后自助点餐，中文选项可用。高峰时段等位20-30分钟。",
                    "area": "shibuya",
                    "tags": ["餐厅", "拉面", "连锁", "人均¥1200"]
                }
            ]
        },
        {
            "day_number": 3,
            "city_code": "tokyo",
            "day_theme": "银座·皇居·築地 — 东京的精致与历史",
            "transport_note": "步行为主，丸之内线辅助",
            "avoid_tips": [
                "筑地场外市场建议07:30-09:00到，新鲜海产最全，10:00后部分摊位开始收",
                "银座购物日推荐周末14:00-17:00，部分顶级百货会有样品出售"
            ],
            "items": [
                {
                    "sort_order": 1,
                    "item_type": "poi",
                    "entity_name": "筑地场外市场",
                    "start_time": "08:00",
                    "end_time": "09:30",
                    "duration_min": 90,
                    "copy_zh": "东京最知名的海鲜集市，场外市场对公众开放，可以直接购买新鲜海胆、牡蛎、金枪鱼刺身等。场内批发市场2018年迁至丰洲，但场外仍保留大量专业级食材店和小吃。",
                    "tips_zh": "建议早餐时段来，三角饭团+新鲜玉子烧是标配。周日部分摊位关闭。",
                    "area": "tsukiji",
                    "tags": ["美食", "市场", "海鲜", "早餐"]
                }
            ]
        },
        {
            "day_number": 4,
            "city_code": "tokyo",
            "day_theme": "秋叶原·上野·御徒町 — 二次元与美食街",
            "transport_note": "山手线+步行，无需坐出租",
            "avoid_tips": [
                "秋叶原游戏中心避免在机器前站太久不玩，这是礼仪问题"
            ],
            "items": [
                {
                    "sort_order": 1,
                    "item_type": "poi",
                    "entity_name": "秋叶原电器街",
                    "start_time": "10:00",
                    "end_time": "13:00",
                    "duration_min": 180,
                    "copy_zh": "世界最密集的电子游戏和动漫周边集散地，从最新显卡到昭和时代的老旧游戏机应有尽有。Yodobashi Camera是最大的电器连锁，免税购物需带护照。",
                    "tips_zh": "购物前确认是否免税（Tax Free），通常需满¥5,000可申请。不要被中间商拉进小店，大型连锁更可靠。",
                    "area": "akihabara",
                    "tags": ["购物", "动漫", "电子", "免税"]
                }
            ]
        },
        {
            "day_number": 5,
            "city_code": "tokyo",
            "day_theme": "自由时间 + 购物 + 机场",
            "transport_note": "Skyliner特急或Narita Express（N'EX）至成田机场约60-90分钟",
            "avoid_tips": [
                "建议航班起飞前3.5小时出发，成田机场安检排队时间不稳定",
                "最后一天买伴手礼推荐药妆店（松本清、Sundrug），比机场便宜20-30%"
            ],
            "items": [
                {
                    "sort_order": 1,
                    "item_type": "poi",
                    "entity_name": "表参道·青山购物",
                    "start_time": "09:00",
                    "end_time": "12:00",
                    "duration_min": 180,
                    "copy_zh": "东京最有设计感的购物大街，两侧是Prada、Dior等顶奢和Comme des Garçons等日本设计师品牌。青山是日本时尚圈的发源地，随便一栋建筑都出自安藤忠雄、妹岛和世等明星建筑师之手。",
                    "tips_zh": "表参道Hills的螺旋中庭是建筑师安藤忠雄的代表作，进去免费参观值得一看。",
                    "area": "omotesando",
                    "tags": ["购物", "设计", "时尚", "建筑"]
                }
            ]
        }
    ]
}


def upgrade() -> None:
    conn = op.get_bind()
    template_json = json.dumps(TOKYO_CLASSIC_5D_TEMPLATE, ensure_ascii=False)

    # 插入或更新东京经典5日模板
    conn.execute(text("""
        INSERT INTO route_templates (name_zh, city_code, duration_days, theme, sku_tier, template_data, is_active)
        VALUES (:name_zh, :city_code, :duration_days, :theme, :sku_tier, CAST(:template_data AS JSONB), :is_active)
        ON CONFLICT DO NOTHING
    """), {
        "name_zh": "东京经典5日",
        "city_code": "tokyo",
        "duration_days": 5,
        "theme": "classic",
        "sku_tier": "standard",
        "template_data": template_json,
        "is_active": True,
    })

    # 同时插入 3日精华版
    tokyo_3d = {
        **TOKYO_CLASSIC_5D_TEMPLATE,
        "meta": {
            **TOKYO_CLASSIC_5D_TEMPLATE["meta"],
            "template_code": "tokyo_classic_3d",
            "name_zh": "东京精华3日",
            "duration_days": 3,
        },
        "days": TOKYO_CLASSIC_5D_TEMPLATE["days"][:3]
    }
    conn.execute(text("""
        INSERT INTO route_templates (name_zh, city_code, duration_days, theme, sku_tier, template_data, is_active)
        VALUES (:name_zh, :city_code, :duration_days, :theme, :sku_tier, CAST(:template_data AS JSONB), :is_active)
        ON CONFLICT DO NOTHING
    """), {
        "name_zh": "东京精华3日",
        "city_code": "tokyo",
        "duration_days": 3,
        "theme": "classic",
        "sku_tier": "standard",
        "template_data": json.dumps(tokyo_3d, ensure_ascii=False),
        "is_active": True,
    })


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DELETE FROM route_templates WHERE city_code = 'tokyo' AND theme = 'classic'"))
