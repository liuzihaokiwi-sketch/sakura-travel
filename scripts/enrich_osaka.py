import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "data", "kansai_spots", "osaka_city.json")

with open(SRC, "r", encoding="utf-8") as f:
    data = json.load(f)

spot_enrichments = {
    "osa_usj": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市此花区桜島2丁目1-33",
        "nearest_station": "ユニバーサルシティ駅 徒歩5分",
        "when": {
            "open_days": "每日（有年检闭园日）",
            "open_hours": "9:00-20:00（按季节变动）",
            "last_entry": "19:00",
            "closed_notes": "年间有数日定期维修闭园，请官网确认"
        },
        "cost": {"admission_jpy": 8600, "typical_spend_jpy": 15000, "budget_tier": "premium"},
        "review_signals": {
            "google_rating": 4.4, "google_review_count": 85000,
            "dimension_scores": {"scenery": 8, "cultural_depth": 3, "accessibility": 8, "crowd_comfort": 2, "uniqueness": 10, "value_for_money": 5},
            "positive_tags": ["哈利波特园区震撼", "超级任天堂世界全球唯一", "夜间活动精彩", "演出质量高"],
            "negative_tags": ["旺季排队2-3小时", "Express Pass另收高价", "餐饮偏贵", "人流密度极高"]
        },
        "queue_wait_minutes": 90,
        "corridor_tags": ["osaka_bay"],
        "risk_flags": ["requires_reservation", "limited_capacity"],
        "descriptions": {
            "why_selected": "关西唯一S级主题公园，哈利波特魔法世界与超级任天堂世界均为全球顶级沉浸体验，无论是亲子家庭还是动漫粉丝均为必去。",
            "what_to_expect": "园区占地面积大，主力项目包括哈利波特禁忌之旅、飞天翼龙、小黄人疯狂游乐车、马力欧赛车等。任天堂世界需要领整理券或购Express Pass，建议9点前入园直奔热门项目。",
            "skip_if": "对娱乐设施兴趣不大、不能接受高票价与长排队、行程只有3天以内的文化向旅行者可降低优先级。"
        }
    },
    "osa_dotonbori": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市中央区道頓堀1丁目",
        "nearest_station": "なんば駅 徒歩3分",
        "when": {
            "open_days": "每日",
            "open_hours": "终日开放（各店铺营业时间不同）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 2500, "budget_tier": "mid"},
        "review_signals": {
            "google_rating": 4.4, "google_review_count": 120000,
            "dimension_scores": {"scenery": 8, "cultural_depth": 5, "accessibility": 10, "crowd_comfort": 2, "uniqueness": 8, "value_for_money": 7},
            "positive_tags": ["格力高霓虹招牌标志性", "章鱼烧地道", "夜景极佳", "美食选择丰富", "免费散步"],
            "negative_tags": ["旺季人潮拥挤", "游客陷阱店铺多", "部分餐厅性价比低"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["namba_shinsaibashi"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "大阪最具代表性的地标街区，格力高霓虹灯招牌是大阪形象的标志，集中了章鱼烧、大阪烧、蟹料理等所有大阪名物，傍晚到夜间氛围最佳。",
            "what_to_expect": "道顿堀川沿岸步行约500米，格力高跑步人招牌前是必拍打卡位。周边有甲贺流章鱼烧、蟹道乐、金龙拉面等各类餐厅。白天游客密集，傍晚后霓虹灯全亮最有氛围。",
            "skip_if": "极度厌恶人群的旅行者可选择工作日清晨游览，但无法完全避开人潮。"
        }
    },
    "osa_osaka_castle": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市中央区大阪城1-1",
        "nearest_station": "大阪城公園駅 徒歩5分",
        "when": {
            "open_days": "每日（天守阁全年开放）",
            "open_hours": "9:00-17:00（天守阁最终入场16:30）",
            "last_entry": "16:30",
            "closed_notes": "年末年始（12月28日-1月1日）天守阁闭馆"
        },
        "cost": {"admission_jpy": 600, "typical_spend_jpy": 1200, "budget_tier": "budget"},
        "review_signals": {
            "google_rating": 4.3, "google_review_count": 95000,
            "dimension_scores": {"scenery": 9, "cultural_depth": 7, "accessibility": 8, "crowd_comfort": 5, "uniqueness": 7, "value_for_money": 7},
            "positive_tags": ["城公园赏樱绝佳", "外观拍照极美", "历史展示丰富", "公园散步免费"],
            "negative_tags": ["天守阁内部为混凝土重建", "内部博物馆陈设一般", "春季人流较大"]
        },
        "queue_wait_minutes": 20,
        "corridor_tags": ["osaka_castle"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "大阪最具历史象征意义的地标，丰臣秀吉统一天下的权力中心。城公园春季樱花与金色天守阁的组合是关西最经典的风景之一。",
            "what_to_expect": "天守阁共8层，内部为丰臣秀吉与大阪夏之阵相关历史博物馆。顶层360度眺望大阪市区。外城公园面积广大，西之丸庭园春季观樱需另购票。",
            "skip_if": "行程极短且已去过其他日本名城（姬路城、熊本城）的旅行者，可仅逛公园不入天守。"
        }
    },
    "osa_shinsaibashi": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市中央区心斎橋筋1丁目-2丁目",
        "nearest_station": "心斎橋駅 直結",
        "when": {
            "open_days": "每日",
            "open_hours": "11:00-21:00（各店铺营业时间不同）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 5000, "budget_tier": "mid"},
        "review_signals": {
            "google_rating": 4.2, "google_review_count": 60000,
            "dimension_scores": {"scenery": 6, "cultural_depth": 3, "accessibility": 10, "crowd_comfort": 4, "uniqueness": 5, "value_for_money": 6},
            "positive_tags": ["雨天可全程室内购物", "药妆品牌齐全", "连接道顿堀便利", "有顶拱廊遮风挡雨"],
            "negative_tags": ["游客化严重", "价格部分偏高", "与其他城市购物街差异不大"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["namba_shinsaibashi"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "大阪最主要的购物拱廊街，全长约600米，从高端品牌到大众药妆一应俱全，雨天购物首选，与道顿堀无缝衔接。",
            "what_to_expect": "沿街有松本清、唐吉诃德、H&M等主流店铺，南端接道顿堀，北端延伸至美国村方向。药妆比价建议走几家对比后再购买。",
            "skip_if": "对购物无需求的文化深度旅行者可快速穿越前往道顿堀，无需专门停留。"
        }
    },
    "osa_kuromon": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市中央区日本橋2丁目4-1",
        "nearest_station": "日本橋駅 徒歩2分",
        "when": {
            "open_days": "每日（部分摊位周日休息）",
            "open_hours": "9:00-18:00（摊位各异）",
            "last_entry": None,
            "closed_notes": "下午后部分摊位开始收摊，推荐上午前往"
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 2000, "budget_tier": "mid"},
        "review_signals": {
            "google_rating": 4.1, "google_review_count": 45000,
            "dimension_scores": {"scenery": 5, "cultural_depth": 6, "accessibility": 8, "crowd_comfort": 4, "uniqueness": 7, "value_for_money": 6},
            "positive_tags": ["海鲜新鲜现切现吃", "金枪鱼刺身物美价廉", "烤扇贝现场烹制", "体验大阪厨房文化"],
            "negative_tags": ["近年游客化严重", "部分摊位专门宰客", "下午后新鲜度下降"]
        },
        "queue_wait_minutes": 10,
        "corridor_tags": ["namba_shinsaibashi"],
        "risk_flags": ["cash_only"],
        "descriptions": {
            "why_selected": "被称为大阪厨房的百年市场，海鲜、蔬果、腌渍品应有尽有，可以边走边吃体验正宗大阪食文化，是美食控的必访之地。",
            "what_to_expect": "市场长约580米，约170家店铺。推荐现场品尝金枪鱼大腹刺身、炭烤扇贝、现开海胆。大多摊位为现金支付，需提前备好零钱。",
            "skip_if": "不喜欢海鲜或对市场类景点兴趣不大可跳过，午后到访体验会大打折扣。"
        }
    },
    "osa_kaiyukan": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市港区海岸通1丁目1-10",
        "nearest_station": "大阪港駅 徒歩5分",
        "when": {
            "open_days": "每日（有不定休，请官网确认）",
            "open_hours": "10:00-20:00（最终入场19:00）",
            "last_entry": "19:00",
            "closed_notes": "部分季节夜间特别开放延长至21:00"
        },
        "cost": {"admission_jpy": 2700, "typical_spend_jpy": 3500, "budget_tier": "mid"},
        "review_signals": {
            "google_rating": 4.4, "google_review_count": 55000,
            "dimension_scores": {"scenery": 9, "cultural_depth": 5, "accessibility": 7, "crowd_comfort": 6, "uniqueness": 8, "value_for_money": 7},
            "positive_tags": ["鲸鲨主缸震撼壮观", "螺旋形游览路线设计独特", "夜间版灯光浪漫", "亲子体验极佳"],
            "negative_tags": ["票价相对较高", "旺季人多", "停留时间有限"]
        },
        "queue_wait_minutes": 15,
        "corridor_tags": ["osaka_bay"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "世界最大级别水族馆之一，以太平洋巨型主缸和鲸鲨展示闻名，螺旋形游览设计使访客从多个深度欣赏同一水缸，体验无可替代。",
            "what_to_expect": "14个展区重现从日本森林溪流到南极冰海的生态系统，鲸鲨全球仅少数水族馆饲养。傍晚夜间版灯光变换，适合情侣。天保山摩天轮在旁边可以顺路游览。",
            "skip_if": "已在其他城市参观过高质量水族馆（如冲绳美丽海）且行程较紧的旅行者可考虑跳过。"
        }
    },
    "osa_shinsekai": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市浪速区恵美須東1丁目-2丁目",
        "nearest_station": "恵美須町駅 徒歩3分",
        "when": {
            "open_days": "每日",
            "open_hours": "通天阁：10:00-20:00（最终入场19:30）；街区全天开放",
            "last_entry": "19:30",
            "closed_notes": None
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 2000, "budget_tier": "mid"},
        "review_signals": {
            "google_rating": 4.2, "google_review_count": 48000,
            "dimension_scores": {"scenery": 7, "cultural_depth": 7, "accessibility": 8, "crowd_comfort": 6, "uniqueness": 8, "value_for_money": 8},
            "positive_tags": ["昭和下町风情原汁原味", "串炸文化体验一流", "通天阁夜景拍照绝佳", "价格亲民"],
            "negative_tags": ["通天阁展望台性价比一般", "夜间部分街道环境复杂"]
        },
        "queue_wait_minutes": 15,
        "corridor_tags": ["tennoji"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "大阪最有昭和下町气息的历史街区，通天阁铁塔矗立其中，串炸是这里的灵魂美食，与繁华的道顿堀形成强烈反差，是感受大阪庶民文化的最佳去处。",
            "what_to_expect": "通天阁周边的商店街保留了大量20世纪中期的招牌与店铺风格。串炸规矩是蘸酱只能蘸一次不可回蘸。jan jan横丁有老式弹球游戏厅。傍晚霓虹灯亮起后氛围更浓。",
            "skip_if": "行程极短且更偏重自然风景的旅行者可跳过，但错过这里会少掉大阪最独特的一面。"
        }
    },
    "osa_umeda_sky": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市北区大淀中1丁目1-88",
        "nearest_station": "大阪駅 徒歩10分",
        "when": {
            "open_days": "每日",
            "open_hours": "10:00-22:30（最终入场22:00）",
            "last_entry": "22:00",
            "closed_notes": None
        },
        "cost": {"admission_jpy": 1500, "typical_spend_jpy": 1800, "budget_tier": "mid"},
        "review_signals": {
            "google_rating": 4.3, "google_review_count": 40000,
            "dimension_scores": {"scenery": 9, "cultural_depth": 4, "accessibility": 7, "crowd_comfort": 7, "uniqueness": 8, "value_for_money": 7},
            "positive_tags": ["日落夜景一流", "建筑外观独特", "360度无遮挡视野", "情侣浪漫首选"],
            "negative_tags": ["从大阪站需步行约10分钟", "票价偏高"]
        },
        "queue_wait_minutes": 10,
        "corridor_tags": ["umeda"],
        "risk_flags": ["weather_dependent"],
        "descriptions": {
            "why_selected": "大阪夜景观赏首选，双塔建筑通过空中飞廊相连，顶部观景台完全开放，360度欣赏大阪全景，是建筑与视觉体验的双重享受。",
            "what_to_expect": "建议日落前30分钟上去，可同时欣赏夕阳与夜景切换。建筑地下有昭和复古风格的泷见小路美食街，可以在此用餐。雨雾天能见度差，晴天为佳。",
            "skip_if": "阴雨天气时能见度极低，可换至室内景点。已有其他展望台计划的旅行者建议二选一。"
        }
    },
    "osa_abeno_harukas": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市阿倍野区阿倍野筋1丁目1-43",
        "nearest_station": "天王寺駅 直結",
        "when": {
            "open_days": "每日",
            "open_hours": "9:00-22:00（最终入场21:30）",
            "last_entry": "21:30",
            "closed_notes": None
        },
        "cost": {"admission_jpy": 2000, "typical_spend_jpy": 2500, "budget_tier": "mid"},
        "review_signals": {
            "google_rating": 4.2, "google_review_count": 28000,
            "dimension_scores": {"scenery": 9, "cultural_depth": 3, "accessibility": 10, "crowd_comfort": 7, "uniqueness": 7, "value_for_money": 6},
            "positive_tags": ["日本最高级别展望台", "360度全景无遮挡", "天王寺直连方便", "晴天可见六甲山"],
            "negative_tags": ["票价稍高", "与梅田空中庭园差异化不足"]
        },
        "queue_wait_minutes": 5,
        "corridor_tags": ["tennoji"],
        "risk_flags": ["weather_dependent"],
        "descriptions": {
            "why_selected": "日本最高建筑（300米）的展望台，与天王寺站直连，全天候室内观景，晴天可望及明石海峡大桥，是关西视野最开阔的高空体验。",
            "what_to_expect": "60层展望台分室内与户外区域，可俯瞰天王寺动物园与通天阁。与梅田空中庭园相比更高但开放感略低，适合雨天备选。",
            "skip_if": "已去过梅田空中庭园的旅行者二选一即可，行程紧凑时优先选梅田空中庭园。"
        }
    },
    "osa_namba_area": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市中央区難波",
        "nearest_station": "なんば駅 直結",
        "when": {
            "open_days": "每日",
            "open_hours": "终日开放",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 3000, "budget_tier": "mid"},
        "review_signals": {
            "google_rating": 4.3, "google_review_count": 75000,
            "dimension_scores": {"scenery": 7, "cultural_depth": 5, "accessibility": 10, "crowd_comfort": 3, "uniqueness": 7, "value_for_money": 7},
            "positive_tags": ["大阪精华集中地", "交通枢纽极方便", "美食住宿一站式", "关西出发基地"],
            "negative_tags": ["人流密集嘈杂", "游客陷阱店较多"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["namba_shinsaibashi"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "大阪旅行的核心地带，道顿堀、心斋桥、黑门市场、千日前通均聚集于此，是食、购、娱三位一体的终极街区，也是关西旅行的最佳住宿基地。",
            "what_to_expect": "难波站周边半径500米内涵盖了大阪最密集的餐厅、药妆店、百货和娱乐设施。去京都奈良关西空港的特急/急行列车均在此发车，地理位置无可替代。",
            "skip_if": "此区域几乎是大阪旅行的必经之地，唯一可以跳过的理由是已专门住在天王寺或梅田。"
        }
    },
    "osa_sumiyoshi_taisha": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市住吉区住吉2丁目9-89",
        "nearest_station": "住吉大社駅 徒歩3分",
        "when": {
            "open_days": "每日",
            "open_hours": "6:00-17:00（冬季6:30起）",
            "last_entry": "16:30",
            "closed_notes": None
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 500, "budget_tier": "free"},
        "review_signals": {
            "google_rating": 4.4, "google_review_count": 32000,
            "dimension_scores": {"scenery": 7, "cultural_depth": 9, "accessibility": 7, "crowd_comfort": 8, "uniqueness": 8, "value_for_money": 10},
            "positive_tags": ["住吉造建筑样式日本最古", "太鼓桥拍照经典", "游客少安静", "免费参观"],
            "negative_tags": ["距市中心稍远需换乘", "非元旦期间人流稀少"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["sumiyoshi"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "日本最古老神社建筑样式「住吉造」的代表，全国2300余座住吉神社的本宫，太鼓桥横跨神苑，是远离游客喧嚣、感受正宗神道信仰的绝佳场所。",
            "what_to_expect": "境内有4座本殿（均为国宝）、太鼓桥、石燈籠群和绿意盎然的庭园。元旦初诣期间人流达全大阪第一，平日则非常幽静，体验截然不同。",
            "skip_if": "行程极紧张且已安排京都多座神社参观的旅行者可跳过，位置略偏。"
        }
    },
    "osa_osaka_food_exp": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市中央区道頓堀（各体验店铺）",
        "nearest_station": "なんば駅 徒歩5分",
        "when": {
            "open_days": "每日",
            "open_hours": "11:00-20:00（各店铺不同）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 2000, "budget_tier": "mid"},
        "review_signals": {
            "google_rating": 4.3, "google_review_count": 15000,
            "dimension_scores": {"scenery": 5, "cultural_depth": 7, "accessibility": 9, "crowd_comfort": 6, "uniqueness": 8, "value_for_money": 8},
            "positive_tags": ["亲手制作章鱼烧超有趣", "适合亲子互动", "大阪烧DIY体验独特", "价格亲民"],
            "negative_tags": ["热门体验店需排队", "DIY课程语言沟通有时困难"]
        },
        "queue_wait_minutes": 20,
        "corridor_tags": ["namba_shinsaibashi"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "大阪是日本的美食之都，章鱼烧与大阪烧是其代名词，亲手制作体验让旅行从观光升华为参与，是亲子家庭和美食爱好者的高性价比活动。",
            "what_to_expect": "道顿堀附近有多家提供DIY章鱼烧/大阪烧体验的店铺，通常含食材与工具，工作人员会指导制作过程。大阪烧推荐风月总本店或千房，章鱼烧推荐甲贺流。",
            "skip_if": "对烹饪类体验无兴趣、行程时间非常紧张的旅行者，可改为直接品尝名店出品。"
        }
    },
    "osa_shitenoji": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市天王寺区四天王寺1丁目11-18",
        "nearest_station": "四天王寺前夕陽ケ丘駅 徒歩5分",
        "when": {
            "open_days": "每日",
            "open_hours": "8:30-16:30（4-9月至17:00）",
            "last_entry": "16:00",
            "closed_notes": None
        },
        "cost": {"admission_jpy": 300, "typical_spend_jpy": 500, "budget_tier": "budget"},
        "review_signals": {
            "google_rating": 4.0, "google_review_count": 22000,
            "dimension_scores": {"scenery": 5, "cultural_depth": 8, "accessibility": 8, "crowd_comfort": 8, "uniqueness": 6, "value_for_money": 7},
            "positive_tags": ["日本最古官寺历史地位极高", "每月跳蚤市场热闹", "游客稀少安静"],
            "negative_tags": ["建筑为战后混凝土重建", "外观观赏性有限"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["tennoji"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "日本最古老的官立寺院（593年圣德太子建立），是日本佛教建筑原型的所在地，对研究飞鸟时代佛教历史有高度参考价值，每月跳蚤市场极具人气。",
            "what_to_expect": "现存建筑为战后复原，金堂、五重塔、回廊构成完整伽蓝。每月21-22日有四天王寺庚申大祭跳蚤市场，古道具、古着、植物摊位热闹非凡。",
            "skip_if": "对日本佛教建筑史兴趣不大的旅行者可跳过，新世界/天王寺动物园优先级更高。"
        }
    },
    "osa_nakanoshima": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市北区中之島",
        "nearest_station": "渡辺橋駅 徒歩3分",
        "when": {
            "open_days": "每日（公园区域）",
            "open_hours": "公园终日开放；中之岛美术馆10:00-17:00",
            "last_entry": "16:30",
            "closed_notes": "中之岛美术馆周一闭馆"
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 1500, "budget_tier": "free"},
        "review_signals": {
            "google_rating": 4.2, "google_review_count": 18000,
            "dimension_scores": {"scenery": 7, "cultural_depth": 7, "accessibility": 8, "crowd_comfort": 8, "uniqueness": 6, "value_for_money": 8},
            "positive_tags": ["中央公会堂近代建筑极美", "5月玫瑰园盛开壮观", "中之岛美术馆展陈优质", "冬季灯光节顶级"],
            "negative_tags": ["平时景观较平淡", "离主要景区稍远"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["osaka_castle"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "大阪的文化艺术心脏，被两条河流环抱的半岛上聚集着大阪市中央公会堂、大阪府立中之岛图书馆、中之岛美术馆等精华，是建筑爱好者和艺术爱好者的天堂。",
            "what_to_expect": "1910年建成的大阪市中央公会堂是国家重要文化财，外观极为壮观。5月玫瑰园约3700棵玫瑰盛开。12月的光之文艺复兴灯光节是大阪冬季最大规模活动。",
            "skip_if": "对建筑和艺术无特别兴趣的旅行者可跳过，秋冬非灯光节期间亮点较少。"
        }
    },
    "osa_tennoji_zoo": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市天王寺区茶臼山町1-108",
        "nearest_station": "天王寺駅 徒歩5分",
        "when": {
            "open_days": "每日（周一闭园，公众假日顺延）",
            "open_hours": "9:30-17:00（最终入场16:00）",
            "last_entry": "16:00",
            "closed_notes": "每周一及年末年始闭园"
        },
        "cost": {"admission_jpy": 500, "typical_spend_jpy": 1000, "budget_tier": "budget"},
        "review_signals": {
            "google_rating": 3.9, "google_review_count": 20000,
            "dimension_scores": {"scenery": 5, "cultural_depth": 3, "accessibility": 9, "crowd_comfort": 7, "uniqueness": 4, "value_for_money": 7},
            "positive_tags": ["票价便宜亲子友好", "天王寺直连方便", "可与新世界串联"],
            "negative_tags": ["设施较老旧", "动物种类和展示方式一般", "与先进动物园差距明显"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["tennoji"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "大阪市内历史最悠久的动物园，票价低廉，与新世界通天阁地理上紧邻，带小朋友的家庭可顺路游览，无需专程前往。",
            "what_to_expect": "园内有约180种动物，非洲草原区有狮子和长颈鹿。设施略显老旧，但价格亲民，适合与天王寺/新世界行程串联，不建议作为核心景点。",
            "skip_if": "对动物园无特别需求的旅行者可跳过，时间有限时优先游览新世界和通天阁。"
        }
    },
    "osa_teamlab_botanical": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市東住吉区長居公園1-23",
        "nearest_station": "長居駅 徒歩5分",
        "when": {
            "open_days": "每日（夜间限定开放）",
            "open_hours": "19:00-22:00（闭园时间按季节调整）",
            "last_entry": "21:00",
            "closed_notes": "部分季节有不定休，请提前查官网"
        },
        "cost": {"admission_jpy": 1200, "typical_spend_jpy": 1500, "budget_tier": "mid"},
        "review_signals": {
            "google_rating": 4.3, "google_review_count": 18000,
            "dimension_scores": {"scenery": 9, "cultural_depth": 4, "accessibility": 7, "crowd_comfort": 7, "uniqueness": 9, "value_for_money": 7},
            "positive_tags": ["户外植物园与光艺术完美融合", "拍照极佳", "情侣浪漫首选", "与东京teamLab不重复"],
            "negative_tags": ["夜间限定需要提前买票", "雨天体验下降", "距市中心略远"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["tennoji"],
        "risk_flags": ["requires_reservation", "weather_dependent"],
        "descriptions": {
            "why_selected": "长居植物园内的户外teamLab沉浸式光艺术，与东京室内版本截然不同，植物与互动光影的结合在全球独一无二，是摄影爱好者和情侣的夜间必选。",
            "what_to_expect": "在真实的植物园环境中，互动艺术灯光随季节变化，游客行走时触发光影反应。建议提前在官网购票，雨天穿雨鞋或携带雨具。",
            "skip_if": "雨天行程或不愿提前购票的旅行者建议备选室内景点。对数字艺术无特别兴趣也可跳过。"
        }
    },
    "osa_hozenji_yokocho": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市中央区難波1丁目2-16",
        "nearest_station": "なんば駅 徒歩5分",
        "when": {
            "open_days": "每日",
            "open_hours": "终日开放（各店铺18:00-23:00为主）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 3000, "budget_tier": "mid"},
        "review_signals": {
            "google_rating": 4.3, "google_review_count": 22000,
            "dimension_scores": {"scenery": 8, "cultural_depth": 8, "accessibility": 9, "crowd_comfort": 7, "uniqueness": 9, "value_for_money": 7},
            "positive_tags": ["苔藓不动明王像独特", "老派居酒屋氛围绝佳", "远离道顿堀喧嚣", "夫妇善哉甜品必吃"],
            "negative_tags": ["石板路雨天湿滑", "居酒屋消费不低"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["namba_shinsaibashi"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "藏于道顿堀喧嚣之侧的幽静石板小巷，苔藓覆满的水掛不動明王像是大阪最独特的参拜景象，两侧的老牌割烹居酒屋是体验大阪夜间饮食文化的极佳选择。",
            "what_to_expect": "巷子仅约100米长，两排传统居酒屋面对面。给不动明王泼水许愿是传统，据说灵验。夫妇善哉的红豆汤圆是文学名作中的大阪名物，必尝。夜间气氛最佳。",
            "skip_if": "白天到访缺乏夜间氛围，不喜欢居酒屋文化的旅行者可快速路过前往道顿堀。"
        }
    },
    "osa_tenjinbashi_shopping": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市北区天神橋1丁目-6丁目",
        "nearest_station": "南森町駅 徒歩1分",
        "when": {
            "open_days": "每日",
            "open_hours": "10:00-20:00（各店铺不同）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 2000, "budget_tier": "free"},
        "review_signals": {
            "google_rating": 4.1, "google_review_count": 16000,
            "dimension_scores": {"scenery": 5, "cultural_depth": 6, "accessibility": 8, "crowd_comfort": 8, "uniqueness": 7, "value_for_money": 9},
            "positive_tags": ["日本最长商店街2.6公里", "本地居民购物街真实生活感", "价格亲民无游客陷阱", "雨天全程有顶遮蔽"],
            "negative_tags": ["与游客热门区域距离较远", "缺乏特别亮点景观"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["umeda"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "日本最长商店街（全长2.6公里），是大阪本地居民的日常购物场所，物价亲民、游客少，相较心斋桥更能感受大阪人的真实生活，附近中崎町复古咖啡店值得探索。",
            "what_to_expect": "商店街横跨天神桥1丁目至6丁目，以食品、日用品、服装为主。旁边的中崎町有独立咖啡店和古着店群落。",
            "skip_if": "行程较短且专注热门景点的旅行者可跳过，此处适合有充裕时间的二次访客。"
        }
    },
    "osa_minoo_falls": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府箕面市箕面公園",
        "nearest_station": "箕面駅 徒歩40分（箕面大滝）",
        "when": {
            "open_days": "每日",
            "open_hours": "终日开放（自然公园）",
            "last_entry": None,
            "closed_notes": "红叶期间周末人流极多"
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 1000, "budget_tier": "free"},
        "review_signals": {
            "google_rating": 4.4, "google_review_count": 28000,
            "dimension_scores": {"scenery": 9, "cultural_depth": 4, "accessibility": 5, "crowd_comfort": 7, "uniqueness": 7, "value_for_money": 9},
            "positive_tags": ["秋季红叶+瀑布组合震撼", "清幽自然步道", "炸枫叶天妇罗全球独一无二", "从梅田30分钟可达"],
            "negative_tags": ["单程需步行约40分钟", "非红叶期景色一般", "红叶期人流较大"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["minoo"],
        "risk_flags": ["weather_dependent", "steep_climb"],
        "descriptions": {
            "why_selected": "大阪近郊最美瀑布，秋季红叶与瀑布的组合是大阪周边赏枫首选，炸枫叶天妇罗是全球绝无仅有的名物小吃，整段步道自然清幽，是城市旅行中难得的自然体验。",
            "what_to_expect": "从阪急箕面站出发，沿箕面川步行约2.7公里到达落差33米的箕面大滝。途中商店售卖红叶天妇罗名物。猴子出没区域较多，请勿喂食。",
            "skip_if": "非秋季访客或行程极紧、不喜欢步行的旅行者可跳过，非红叶期性价比明显下降。"
        }
    },
    "osa_expo_park_taiyo_tower": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府吹田市千里万博公園1-1",
        "nearest_station": "万博記念公園駅 徒歩5分",
        "when": {
            "open_days": "每日（周三闭园，公众假日顺延）",
            "open_hours": "9:30-17:00（最终入场16:30）",
            "last_entry": "16:30",
            "closed_notes": "太阳之塔内部参观需提前网上预约"
        },
        "cost": {"admission_jpy": 260, "typical_spend_jpy": 1000, "budget_tier": "budget"},
        "review_signals": {
            "google_rating": 4.2, "google_review_count": 25000,
            "dimension_scores": {"scenery": 8, "cultural_depth": 7, "accessibility": 6, "crowd_comfort": 8, "uniqueness": 9, "value_for_money": 8},
            "positive_tags": ["冈本太郎太阳之塔震撼独特", "内部生命之树超现实", "公园广大适合野餐", "旁边EXPOCITY购物方便"],
            "negative_tags": ["内部参观需提前预约", "距市中心较远", "非花季公园景色一般"]
        },
        "queue_wait_minutes": 20,
        "corridor_tags": ["expo"],
        "risk_flags": ["requires_reservation"],
        "descriptions": {
            "why_selected": "1970年大阪万博遗址，冈本太郎设计的太阳之塔是20世纪最具标志性的日本艺术建筑，2018年重新开放的塔内生命之树是震撼性的超现实体验，是艺术爱好者的朝圣地。",
            "what_to_expect": "万博纪念公园占地约264公顷，内有日本庭园和自然文化园两大区域。太阳之塔高70米，内部生命之树展示生命进化过程，极为震撼。旁邻EXPOCITY有NIFREL水族馆和购物中心。",
            "skip_if": "对艺术与20世纪日本历史无特别兴趣的旅行者，距市中心约30分钟，可根据行程灵活取舍。"
        }
    },
    "osa_namba_yasaka_shrine": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市浪速区元町2丁目9-19",
        "nearest_station": "大国町駅 徒歩5分",
        "when": {
            "open_days": "每日",
            "open_hours": "境内终日开放",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 300, "budget_tier": "free"},
        "review_signals": {
            "google_rating": 4.2, "google_review_count": 14000,
            "dimension_scores": {"scenery": 6, "cultural_depth": 5, "accessibility": 7, "crowd_comfort": 8, "uniqueness": 9, "value_for_money": 10},
            "positive_tags": ["12米狮子头造型舞台独一无二", "拍照打卡效果极强", "游客适中不拥挤", "免费参观"],
            "negative_tags": ["游览时间短无需专程", "神社本体规模较小"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["namba_shinsaibashi"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "境内巨大狮子头造型的能舞台是全球最具冲击力的神社建筑之一，高12米、宽11米的狮子大口据说能吞噬厄运，是大阪最值得打卡的Instagram圣地之一。",
            "what_to_expect": "神社本体规模不大，10-15分钟可参观完毕。狮子头舞台在境内正中央，正面拍照极具视觉冲击力。难波周边散步时顺路造访最为合适。",
            "skip_if": "对拍照打卡无特别兴趣且已有充实行程的旅行者可跳过，不值得专程前往。"
        }
    },
    "osa_housing_living_museum": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市北区天神橋6丁目4-20",
        "nearest_station": "天神橋筋六丁目駅 直結",
        "when": {
            "open_days": "每日（周二闭馆，公众假日顺延）",
            "open_hours": "10:00-17:00（最终入场16:30）",
            "last_entry": "16:30",
            "closed_notes": "每周二及年末年始闭馆"
        },
        "cost": {"admission_jpy": 600, "typical_spend_jpy": 1200, "budget_tier": "budget"},
        "review_signals": {
            "google_rating": 4.1, "google_review_count": 8000,
            "dimension_scores": {"scenery": 6, "cultural_depth": 8, "accessibility": 9, "crowd_comfort": 9, "uniqueness": 7, "value_for_money": 8},
            "positive_tags": ["江户时代街道原尺复原", "和服租借价格超低", "雨天绝佳选择", "游客少安静"],
            "negative_tags": ["规模较小参观时间短", "展览以日文为主英文信息有限"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["umeda"],
        "risk_flags": ["no_english"],
        "descriptions": {
            "why_selected": "日本少有的以原尺复原江户时代城市街道为核心展览的博物馆，身着600日元租借的和服漫步其中，感受近世大阪的市民生活，是雨天行程的绝佳选择。",
            "what_to_expect": "9楼为复原的江户时代大阪街道（幕末期），8楼有1920-1970年代大阪城市模型。和服租借仅600日元起，含换装服务，可在街道中拍照留念。",
            "skip_if": "行程充裕且天气晴好时优先选户外景点，此处更适合雨天备选或对江户生活史有特别兴趣的访客。"
        }
    },
    "osa_amerikamura": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府大阪市中央区西心斎橋2丁目",
        "nearest_station": "心斎橋駅 徒歩5分",
        "when": {
            "open_days": "每日",
            "open_hours": "12:00-21:00（各店铺不同）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 3000, "budget_tier": "mid"},
        "review_signals": {
            "google_rating": 4.0, "google_review_count": 12000,
            "dimension_scores": {"scenery": 5, "cultural_depth": 5, "accessibility": 9, "crowd_comfort": 7, "uniqueness": 6, "value_for_money": 6},
            "positive_tags": ["二手潮流服饰淘货天堂", "本地年轻人文化聚集地", "与心斋桥串联方便"],
            "negative_tags": ["对购物无需求者无特别吸引力", "三角公园略显普通"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["namba_shinsaibashi"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "大阪年轻人街头文化与潮流二手服饰的集散地，70-90年代风格的唱片店、美式古着店、纹身店密布，是感受大阪次文化与街头时尚的独特窗口。",
            "what_to_expect": "以三角公园为中心，周边集中了大量古着店（二手服饰）、唱片店和独立小店。与心斋桥仅一街之隔，可与心斋桥、道顿堀串联游览。",
            "skip_if": "对二手服饰和街头文化无兴趣的旅行者可跳过，快速路过前往心斋桥即可。"
        }
    },
    "osa_cupnoodle_museum": {
        "city_code": "osaka", "prefecture": "大阪府",
        "address_ja": "大阪府池田市満寿美町8-25",
        "nearest_station": "池田駅 徒歩5分",
        "when": {
            "open_days": "每日（周二闭馆）",
            "open_hours": "9:30-16:00（最终入场15:30）",
            "last_entry": "15:30",
            "closed_notes": "每周二及年末年始闭馆"
        },
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 800, "budget_tier": "free"},
        "review_signals": {
            "google_rating": 4.2, "google_review_count": 14000,
            "dimension_scores": {"scenery": 4, "cultural_depth": 7, "accessibility": 7, "crowd_comfort": 7, "uniqueness": 8, "value_for_money": 9},
            "positive_tags": ["入馆免费性价比极高", "DIY杯面专属体验有趣", "安藤百福发明史展示深度好", "亲子互动极佳"],
            "negative_tags": ["规模较小1-2小时足够", "距大阪市区需约30分钟", "DIY体验需要排队等候"]
        },
        "queue_wait_minutes": 30,
        "corridor_tags": ["ikeda"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "世界首个方便面发明者安藤百福的纪念博物馆，DIY专属原创杯面体验是全球独家，入馆免费极具性价比，是亲子家庭的高评价活动选择。",
            "what_to_expect": "展馆分为安藤百福创业历程展示区与鸡汤拉面体验区。500日元可DIY专属杯面，选汤底、配料并亲手装填。建议上午前往，DIY体验排队较短。从梅田坐阪急约20分钟。",
            "skip_if": "行程非常紧张且以市中心为核心的旅行者可跳过，横滨也有同类博物馆（规模更大）。"
        }
    }
}

event_enrichments = {
    "osa_tenjin_matsuri": {
        "city_code": "osaka", "prefecture": "大阪府",
        "corridor_tags": ["osaka_castle", "umeda"],
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 3000, "budget_tier": "free"},
        "descriptions": {
            "why_selected": "日本三大祭之一，每年7月25日的船渡御将约3000名装束华美的参列者分乘100余艘船只游行大川，配合5000发烟花，是大阪夏日最高规格的祭典体验。",
            "what_to_expect": "24日为宵宫，25日为本宫（高潮）。傍晚约17时起船渡御开始，约21时烟花结束。大川沿岸提前几小时占据位置，部分餐厅提供付费观览席。",
            "skip_if": "不能接受极端拥挤人群的旅行者需谨慎，本宫当日人流极大，交通可能严重拥堵。"
        }
    },
    "osa_hikari_renaissance": {
        "city_code": "osaka", "prefecture": "大阪府",
        "corridor_tags": ["osaka_castle", "umeda"],
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 1000, "budget_tier": "free"},
        "descriptions": {
            "why_selected": "大阪最大规模的冬季灯光节，中央公会堂等近代建筑上的3D光雕投影与御堂筋数公里的彩灯长廊同时开启，是大阪12月的标志性活动。",
            "what_to_expect": "中之岛区域有光雕投影秀（中央公会堂、市役所等），御堂筋有彩灯树，可安排1-2小时游览。圣诞市集同期举办，热甘酒与烤肠是必选。",
            "skip_if": "冬季天气寒冷，不喜户外活动者可缩短游览时间，主要光雕秀约20分钟一循环。"
        }
    },
    "osa_sakura": {
        "city_code": "osaka", "prefecture": "大阪府",
        "corridor_tags": ["osaka_castle", "umeda", "sumiyoshi"],
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 2000, "budget_tier": "free"},
        "descriptions": {
            "why_selected": "大阪城公园樱花与金色天守阁的组合是关西赏樱最经典的画面；造币局樱花通道有约130种珍稀品种，是全日本最权威的赏樱圣地之一，每年仅开放约一周。",
            "what_to_expect": "大阪城公园约3000棵樱花，西之丸庭园最为集中（需购票）。毛马樱之宫公园大川两岸约4700棵樱花可免费观赏。造币局通り抜け约4月中旬（比一般花期晚）开放，每年日期公布在官方网站。",
            "skip_if": "花期短暂，需精确卡好日期，前一周或后一周来访将错过高峰，届时普通公园樱花已落。"
        }
    },
    "osa_sumiyoshi_shogatsu": {
        "city_code": "osaka", "prefecture": "大阪府",
        "corridor_tags": ["sumiyoshi"],
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 1000, "budget_tier": "free"},
        "descriptions": {
            "why_selected": "住吉大社是关西最热门的新年参拜神社之一，三天合计超过200万人参拜，传统的御神籤、破魔矢和初诣氛围是体验日本新年文化的绝佳机会。",
            "what_to_expect": "元旦凌晨过后人流最为密集，1月1-3日均可前往，越晚越人少。境内有传统新年食摊（甘酒、烤年糕）。太鼓桥前人流大，注意安全。",
            "skip_if": "极度怕挤或行程在元旦后的旅行者可平日游览住吉大社本体（无需赶初诣人流）。"
        }
    },
    "osa_minoo_koyo": {
        "city_code": "osaka", "prefecture": "大阪府",
        "corridor_tags": ["minoo"],
        "cost": {"admission_jpy": 0, "typical_spend_jpy": 1000, "budget_tier": "free"},
        "descriptions": {
            "why_selected": "大阪近郊赏枫首选地，箕面川沿岸枫树在11月中旬进入最佳状态，与瀑布的组合极具视觉冲击力，沿路限定贩售的炸枫叶天妇罗是全球唯一的特色小吃。",
            "what_to_expect": "红叶期间周末人流较大，推荐工作日前往。从箕面站步行约40分钟到达瀑布，沿途可购买炸枫叶（约200-300日元）。11月中旬为红叶盛期，具体日期每年略有不同。",
            "skip_if": "错过11月中旬至12月初的红叶期则观赏价值大幅下降，非该时段访客可在行程中低优先级处理。"
        }
    }
}

for spot in data["spots"]:
    sid = spot["id"]
    if sid in spot_enrichments:
        for k, v in spot_enrichments[sid].items():
            spot[k] = v

for event in data["seasonal_events"]:
    eid = event["id"]
    if eid in event_enrichments:
        for k, v in event_enrichments[eid].items():
            event[k] = v

with open(SRC, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

spots_enriched = sum(1 for s in data["spots"] if "city_code" in s)
events_enriched = sum(1 for e in data["seasonal_events"] if "city_code" in e)
print(f"Spots enriched: {spots_enriched}/{len(data['spots'])}")
print(f"Events enriched: {events_enriched}/{len(data['seasonal_events'])}")
