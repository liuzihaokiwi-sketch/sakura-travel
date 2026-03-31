import json

with open('data/kansai_spots/kyoto_city.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

enrichments = {
    "kyo_fushimi_inari": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市伏見区深草薮之内町68番地",
        "nearest_station": "JR稲荷駅 徒歩1分 / 京阪伏見稲荷駅 徒歩5分",
        "when": {
            "open_days": "每日",
            "open_hours": "终日开放",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 500,
            "budget_tier": "free"
        },
        "review_signals": {
            "google_rating": 4.6,
            "google_review_count": 85000,
            "dimension_scores": {
                "scenery": 10,
                "cultural_depth": 9,
                "accessibility": 9,
                "crowd_comfort": 2,
                "uniqueness": 10,
                "value_for_money": 10
            },
            "positive_tags": ["千本鸟居视觉震撼", "免费入场", "清晨极少人"],
            "negative_tags": ["白天人流极大", "旺季完全无法拍空景"]
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["fushimi"],
        "risk_flags": ["steep_climb"],
        "descriptions": {
            "why_selected": "全球最辨识度的日本图腾——千本鸟居隧道，且完全免费",
            "what_to_expect": "穿越成千上万座朱红色鸟居，越往山上人越少，四ツ辻俯瞰京都全景",
            "skip_if": "不能步行爬坡、白天怕拥挤又无法早起"
        }
    },
    "kyo_kiyomizu": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市東山区清水1丁目294",
        "nearest_station": "京阪清水五条駅 徒歩25分 / 市バス清水道 徒歩10分",
        "when": {
            "open_days": "每日",
            "open_hours": "6:00-18:00",
            "last_entry": "17:30",
            "closed_notes": "夜间特别参拜另行开放（春秋季）"
        },
        "cost": {
            "admission_jpy": 500,
            "typical_spend_jpy": 1500,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.5,
            "google_review_count": 75000,
            "dimension_scores": {
                "scenery": 9,
                "cultural_depth": 9,
                "accessibility": 7,
                "crowd_comfort": 2,
                "uniqueness": 9,
                "value_for_money": 7
            },
            "positive_tags": ["清水舞台绝景", "四季皆美", "世界遗产"],
            "negative_tags": ["坡道人流密集", "旺季需排队买票"]
        },
        "queue_wait_minutes": 20,
        "corridor_tags": ["higashiyama"],
        "risk_flags": ["steep_climb"],
        "descriptions": {
            "why_selected": "世界文化遗产，悬空舞台是京都标志，春樱秋枫各有绝色",
            "what_to_expect": "登上清水舞台俯瞰山谷与京都盆地，沿清水坂石板路感受传统商业氛围",
            "skip_if": "行动不便者、极度怕拥挤者"
        }
    },
    "kyo_kinkakuji": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市北区金閣寺町1",
        "nearest_station": "市バス金閣寺道 徒歩3分 / 市バス金閣寺前 即到",
        "when": {
            "open_days": "每日",
            "open_hours": "9:00-17:00",
            "last_entry": "16:50",
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 500,
            "typical_spend_jpy": 800,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.5,
            "google_review_count": 120000,
            "dimension_scores": {
                "scenery": 9,
                "cultural_depth": 8,
                "accessibility": 7,
                "crowd_comfort": 2,
                "uniqueness": 9,
                "value_for_money": 7
            },
            "positive_tags": ["金碧辉煌视觉冲击强", "倒影如画", "世界遗产"],
            "negative_tags": ["人流极大", "单向参观路线短", "距市中心偏远"]
        },
        "queue_wait_minutes": 15,
        "corridor_tags": ["kinkakuji_area"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "金箔覆盖的舍利殿倒映在镜湖池，是全球最知名的日本建筑之一",
            "what_to_expect": "单向参观路线约35分钟，金阁在阳光下耀眼，冬季下雪时更是梦境般的场景",
            "skip_if": "二刷旅行者（体验感重复度高），希望深度文化体验者"
        }
    },
    "kyo_arashiyama_bamboo": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市右京区嵯峨小倉山田淵山町",
        "nearest_station": "嵐電嵐山駅 徒歩5分 / JR嵯峨嵐山駅 徒歩10分",
        "when": {
            "open_days": "每日",
            "open_hours": "终日开放",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 0,
            "budget_tier": "free"
        },
        "review_signals": {
            "google_rating": 4.3,
            "google_review_count": 55000,
            "dimension_scores": {
                "scenery": 9,
                "cultural_depth": 5,
                "accessibility": 8,
                "crowd_comfort": 2,
                "uniqueness": 9,
                "value_for_money": 10
            },
            "positive_tags": ["竹林隧道视觉独特", "免费", "清晨极美"],
            "negative_tags": ["白天人极多", "路段较短仅约200米"]
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["arashiyama"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "全球最知名的竹林景观，高耸的孟宗竹制造天然隧道，免费开放",
            "what_to_expect": "约200米的笔直竹林小径，风吹竹叶的沙沙声极具禅意，但白天人多难以独享",
            "skip_if": "白天旅行者（人太多），期待长时间自然徒步的旅客"
        }
    },
    "kyo_arashiyama_area": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市右京区嵯峨天龍寺芒ノ馬場町",
        "nearest_station": "嵐電嵐山駅 即到 / JR嵯峨嵐山駅 徒歩3分",
        "when": {
            "open_days": "每日",
            "open_hours": "全天区域开放（各景点有独立时间）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 3000,
            "budget_tier": "mid"
        },
        "review_signals": {
            "google_rating": 4.5,
            "google_review_count": 40000,
            "dimension_scores": {
                "scenery": 9,
                "cultural_depth": 8,
                "accessibility": 8,
                "crowd_comfort": 3,
                "uniqueness": 8,
                "value_for_money": 8
            },
            "positive_tags": ["复合型目的地半日起", "秋季红叶顶级", "交通便利"],
            "negative_tags": ["秋季红叶期渡月桥极度拥挤", "餐饮价格偏高"]
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["arashiyama", "arashiyama_sagano"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "竹林、天龙寺、渡月桥、猴子公园、小火车的超级综合目的地，半天到一天内容充实",
            "what_to_expect": "从渡月桥漫步到竹林，游览天龙寺庭园，可搭乘嵯峨野小火车穿越保津峡",
            "skip_if": "时间紧张只有半天以内、不喜欢人多热门景区"
        }
    },
    "kyo_gion": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市東山区祇園町",
        "nearest_station": "京阪祇園四条駅 徒歩5分 / 阪急京都河原町駅 徒歩10分",
        "when": {
            "open_days": "每日",
            "open_hours": "终日开放（花见小路18:00后最有氛围）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 2000,
            "budget_tier": "free"
        },
        "review_signals": {
            "google_rating": 4.4,
            "google_review_count": 35000,
            "dimension_scores": {
                "scenery": 8,
                "cultural_depth": 9,
                "accessibility": 9,
                "crowd_comfort": 4,
                "uniqueness": 9,
                "value_for_money": 9
            },
            "positive_tags": ["偶遇艺伎概率最高", "夜间氛围绝佳", "免费漫游"],
            "negative_tags": ["部分巷道禁止摄影", "饮食价格偏高"]
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["gion", "higashiyama"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "京都最具代表性的花街，傍晚时分有机会偶遇真实的艺伎或舞伎",
            "what_to_expect": "石板路两侧是百年茶屋，灯笼亮起的花见小路充满昭和时代的静谧美感",
            "skip_if": "白天到访（氛围大打折扣）、对传统文化无兴趣"
        }
    },
    "kyo_nishiki": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市中京区錦小路通",
        "nearest_station": "阪急烏丸駅 徒歩3分 / 地下鉄四条駅 徒歩5分",
        "when": {
            "open_days": "每日",
            "open_hours": "10:00-18:00（各店不同）",
            "last_entry": None,
            "closed_notes": "部分店铺周三或周四休息"
        },
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 1500,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.2,
            "google_review_count": 28000,
            "dimension_scores": {
                "scenery": 6,
                "cultural_depth": 7,
                "accessibility": 9,
                "crowd_comfort": 3,
                "uniqueness": 7,
                "value_for_money": 7
            },
            "positive_tags": ["边走边吃京都食材", "雨天友好有屋顶", "市中心位置极便利"],
            "negative_tags": ["下午店铺陆续打烊", "近年游客增多变嘈杂"]
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["nishiki"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "400年历史的京都食材街，130家专门店，腌菜、豆腐、京料理食材一网打尽",
            "what_to_expect": "拱廊街两侧各种京都特色小吃和食材店，可以边走边尝试烤豆腐串、玉子烧等",
            "skip_if": "对日本食文化无兴趣、下午晚到（店铺开始关门）"
        }
    },
    "kyo_higashiyama": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市東山区清水2丁目〜祇園",
        "nearest_station": "市バス清水道 即到 / 京阪祇園四条駅 徒歩10分（终点）",
        "when": {
            "open_days": "每日",
            "open_hours": "终日开放（各商铺9:00-18:00）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 2500,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.6,
            "google_review_count": 25000,
            "dimension_scores": {
                "scenery": 9,
                "cultural_depth": 9,
                "accessibility": 7,
                "crowd_comfort": 3,
                "uniqueness": 9,
                "value_for_money": 9
            },
            "positive_tags": ["京都精华一线串联", "穿和服散步最佳路线", "拍照点密集"],
            "negative_tags": ["坡道较多腿脚不便者累", "旺季人极多"]
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["higashiyama", "gion"],
        "risk_flags": ["steep_climb"],
        "descriptions": {
            "why_selected": "一条路串联清水寺、二三年坂、宁宁之道、八坂神社，是京都最精华的步行体验",
            "what_to_expect": "石板小路两侧是传统商铺和茶屋，下坡段景色如画，傍晚抵达祇园氛围绝佳",
            "skip_if": "行动不便、时间极紧只有2小时以内"
        }
    },
    "kyo_philosopher_path": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市左京区浄土寺石橋町〜若王子町",
        "nearest_station": "市バス銀閣寺道 徒歩5分（北端） / 地下鉄蹴上駅 徒歩15分（南端）",
        "when": {
            "open_days": "每日",
            "open_hours": "终日开放",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 500,
            "budget_tier": "free"
        },
        "review_signals": {
            "google_rating": 4.3,
            "google_review_count": 32000,
            "dimension_scores": {
                "scenery": 7,
                "cultural_depth": 6,
                "accessibility": 7,
                "crowd_comfort": 6,
                "uniqueness": 6,
                "value_for_money": 10
            },
            "positive_tags": ["春季樱花隧道绝美", "运河步道悠闲", "免费散步"],
            "negative_tags": ["非樱花季景色普通", "夏季植被茂密蚊虫多"]
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["philosopher_path"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "哲学家西田几多郎常走的2公里运河小道，春季樱花倒映水面极美",
            "what_to_expect": "沿小水渠缓步而行，两侧咖啡馆和小店点缀，连接银阁寺与南禅寺",
            "skip_if": "非樱花季来访且对运河步道兴趣一般"
        }
    },
    "kyo_ginkakuji": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市左京区銀閣寺町2",
        "nearest_station": "市バス銀閣寺道 徒歩5分",
        "when": {
            "open_days": "每日",
            "open_hours": "8:30-17:00（3月1日-11月30日） / 9:00-16:30（12月1日-2月末）",
            "last_entry": "閉館30分前",
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 500,
            "typical_spend_jpy": 700,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.3,
            "google_review_count": 42000,
            "dimension_scores": {
                "scenery": 7,
                "cultural_depth": 8,
                "accessibility": 7,
                "crowd_comfort": 5,
                "uniqueness": 7,
                "value_for_money": 6
            },
            "positive_tags": ["枯山水庭园禅意浓厚", "银砂滩独特景观", "比金阁寺人少"],
            "negative_tags": ["银阁外观不如想象中华丽", "性价比不如金阁"]
        },
        "queue_wait_minutes": 10,
        "corridor_tags": ["philosopher_path"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "室町幕府的山庄遗构，银砂滩和向月台的枯山水美学比金阁寺更耐人寻味",
            "what_to_expect": "参观银阁本堂、锦镜池庭园，登山道可俯瞰京都市区，整体禅意十足",
            "skip_if": "期待金碧辉煌的视觉冲击，或时间非常有限"
        }
    },
    "kyo_tenryuji": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市右京区嵯峨天龍寺芒ノ馬場町68",
        "nearest_station": "嵐電嵐山駅 徒歩3分 / JR嵯峨嵐山駅 徒歩13分",
        "when": {
            "open_days": "每日",
            "open_hours": "8:30-17:30（3/21-10/20） / 8:30-17:00（10/21-3/20）",
            "last_entry": "17:00",
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 500,
            "typical_spend_jpy": 800,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.4,
            "google_review_count": 38000,
            "dimension_scores": {
                "scenery": 8,
                "cultural_depth": 9,
                "accessibility": 8,
                "crowd_comfort": 5,
                "uniqueness": 8,
                "value_for_money": 7
            },
            "positive_tags": ["曹源池庭园经典构图", "后门直通竹林", "世界遗产"],
            "negative_tags": ["本堂参拜需另付费", "庭园与建筑票价分开"]
        },
        "queue_wait_minutes": 10,
        "corridor_tags": ["arashiyama"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "岚山最重要的禅寺，曹源池庭园借嵐山为背景的借景手法是日本庭园经典",
            "what_to_expect": "以嵐山群山为借景的池泉回游式庭园，后门直接通往竹林，是岚山游览的理想起点",
            "skip_if": "对日本庭园美学无感，只想看竹林的旅客"
        }
    },
    "kyo_toji": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市南区九条町1",
        "nearest_station": "近鉄東寺駅 徒歩5分 / JR京都駅 徒歩15分",
        "when": {
            "open_days": "每日",
            "open_hours": "8:00-17:00（金堂・講堂） / 境内5:00-17:00",
            "last_entry": "16:30",
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 500,
            "typical_spend_jpy": 700,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.3,
            "google_review_count": 30000,
            "dimension_scores": {
                "scenery": 8,
                "cultural_depth": 8,
                "accessibility": 9,
                "crowd_comfort": 6,
                "uniqueness": 8,
                "value_for_money": 7
            },
            "positive_tags": ["日本最高五重塔震撼", "京都站附近极便利", "每月弘法市集精彩"],
            "negative_tags": ["春季夜樱期人多", "非市集日境内较空旷"]
        },
        "queue_wait_minutes": 5,
        "corridor_tags": ["kyoto_station"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "55米高的日本最高五重塔与夜樱倒映水面，距京都站步行可达的世界遗产",
            "what_to_expect": "参观弘法大师空海创建的真言宗根本道场，讲堂内的立体曼陀罗雕刻群极具冲击力",
            "skip_if": "非每月21日弘法市来访，体验感会明显减分"
        }
    },
    "kyo_nanzenji": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市左京区南禅寺福地町86",
        "nearest_station": "地下鉄蹴上駅 徒歩10分",
        "when": {
            "open_days": "每日",
            "open_hours": "8:40-17:00（3-11月） / 8:40-16:30（12-2月）",
            "last_entry": "16:40",
            "closed_notes": "12/28-1/1休"
        },
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 1000,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.4,
            "google_review_count": 36000,
            "dimension_scores": {
                "scenery": 9,
                "cultural_depth": 9,
                "accessibility": 7,
                "crowd_comfort": 6,
                "uniqueness": 9,
                "value_for_money": 8
            },
            "positive_tags": ["水路阁砖拱桥绝美", "三门气势磅礴", "秋季红叶名所"],
            "negative_tags": ["各殿堂分开收费略繁琐", "地铁步行稍远"]
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["philosopher_path"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "临济宗总本山，明治时代留下的红砖水路阁是最意想不到的美丽建筑",
            "what_to_expect": "境内免费参观，三门、水路阁、方丈庭园各有特色，秋天枫叶包围整座寺院",
            "skip_if": "对禅寺建筑无感，只来看水路阁可能觉得专程不值"
        }
    },
    "kyo_nijo_castle": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市中京区二条通堀川西入二条城町541",
        "nearest_station": "地下鉄二条城前駅 徒歩1分",
        "when": {
            "open_days": "每日（部分特定日期休）",
            "open_hours": "8:45-17:00",
            "last_entry": "16:00",
            "closed_notes": "每年12月下旬至1月上旬部分日期休馆"
        },
        "cost": {
            "admission_jpy": 1000,
            "typical_spend_jpy": 1200,
            "budget_tier": "mid"
        },
        "review_signals": {
            "google_rating": 4.3,
            "google_review_count": 52000,
            "dimension_scores": {
                "scenery": 7,
                "cultural_depth": 9,
                "accessibility": 9,
                "crowd_comfort": 6,
                "uniqueness": 8,
                "value_for_money": 7
            },
            "positive_tags": ["莺张地板历史体验独特", "障壁画精美", "世界遗产"],
            "negative_tags": ["二之丸御殿内禁止拍照", "门票稍贵"]
        },
        "queue_wait_minutes": 15,
        "corridor_tags": ["nishiki"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "德川家康入京时的权力之座，莺张地板踩上去会发出鸟鸣——这是防刺客的精巧设计",
            "what_to_expect": "参观二之丸御殿的金碧障壁画，行走在会唱歌的地板上，感受幕府时代的政治氛围",
            "skip_if": "对日本历史不感兴趣、只看表面景观的旅客"
        }
    },
    "kyo_yasaka": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市東山区祇園町北側625",
        "nearest_station": "京阪祇園四条駅 徒歩5分",
        "when": {
            "open_days": "每日",
            "open_hours": "终日开放（社務所9:00-17:00）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 300,
            "budget_tier": "free"
        },
        "review_signals": {
            "google_rating": 4.3,
            "google_review_count": 28000,
            "dimension_scores": {
                "scenery": 7,
                "cultural_depth": 8,
                "accessibility": 9,
                "crowd_comfort": 5,
                "uniqueness": 7,
                "value_for_money": 10
            },
            "positive_tags": ["夜间灯笼氛围超好", "免费", "祇园散步终点"],
            "negative_tags": ["单独游览内容不多", "7月祇园祭期间极度拥挤"]
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["gion", "higashiyama"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "祇园地标神社，傍晚灯笼点亮后氛围极佳，是东山散步的完美收尾",
            "what_to_expect": "朱红色楼门在灯光下格外美丽，后方圆山公园可以继续漫步",
            "skip_if": "白天到访（夜间才有最佳氛围），期待深度宗教文化体验"
        }
    },
    "kyo_maruyama_park": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市東山区円山町473",
        "nearest_station": "京阪祇園四条駅 徒歩10分",
        "when": {
            "open_days": "每日",
            "open_hours": "终日开放",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 200,
            "budget_tier": "free"
        },
        "review_signals": {
            "google_rating": 4.1,
            "google_review_count": 18000,
            "dimension_scores": {
                "scenery": 6,
                "cultural_depth": 5,
                "accessibility": 9,
                "crowd_comfort": 6,
                "uniqueness": 5,
                "value_for_money": 10
            },
            "positive_tags": ["春季枝垂樱夜间点灯绝美", "免费", "紧邻八坂神社"],
            "negative_tags": ["非樱花季极普通", "不值得专程"]
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["gion", "higashiyama"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "春季枝垂樱夜间点灯是京都赏夜樱的经典场景，其他季节作为休憩空间",
            "what_to_expect": "公园中央的枝垂樱在樱花季夜晚被灯光照亮，配合周边茶屋的叫卖声氛围满满",
            "skip_if": "非樱花季造访"
        }
    },
    "kyo_ryoanji": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市右京区龍安寺御陵ノ下町13",
        "nearest_station": "京阪・市バス龍安寺前 徒歩1分",
        "when": {
            "open_days": "每日",
            "open_hours": "8:00-17:00（3-11月） / 8:30-16:30（12-2月）",
            "last_entry": "16:40",
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 600,
            "typical_spend_jpy": 800,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.2,
            "google_review_count": 35000,
            "dimension_scores": {
                "scenery": 7,
                "cultural_depth": 9,
                "accessibility": 7,
                "crowd_comfort": 5,
                "uniqueness": 10,
                "value_for_money": 6
            },
            "positive_tags": ["枯山水石庭世界最高水平", "15块石头谜题引人深思", "世界遗产"],
            "negative_tags": ["石庭前观赏走廊拥挤", "理解门槛偏高"]
        },
        "queue_wait_minutes": 5,
        "corridor_tags": ["kinkakuji_area"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "世界上最著名的枯山水石庭，15块石头的哲学谜题吸引无数人驻足沉思",
            "what_to_expect": "坐在廊下静静凝视白砂与石组，从任何角度都无法同时看到全部15块石头",
            "skip_if": "无法静下心感受枯山水美学的旅客"
        }
    },
    "kyo_kyoto_tower": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市下京区烏丸通七条下ル東塩小路町721-1",
        "nearest_station": "JR京都駅 徒歩2分",
        "when": {
            "open_days": "每日",
            "open_hours": "10:30-21:00",
            "last_entry": "20:30",
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 900,
            "typical_spend_jpy": 1000,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.0,
            "google_review_count": 22000,
            "dimension_scores": {
                "scenery": 6,
                "cultural_depth": 3,
                "accessibility": 10,
                "crowd_comfort": 7,
                "uniqueness": 4,
                "value_for_money": 5
            },
            "positive_tags": ["京都站即到极便利", "360度俯瞰京都盆地", "雨天也可观景"],
            "negative_tags": ["观景体验一般", "性价比低于预期"]
        },
        "queue_wait_minutes": 5,
        "corridor_tags": ["kyoto_station"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "京都站正对面的131米白色灯塔，是了解京都城市格局最快的观景点",
            "what_to_expect": "展望台可360度俯瞰京都市区，可以辨认金阁寺、东寺五重塔等地标方位",
            "skip_if": "预算有限、对观景台体验要求高的旅客"
        }
    },
    "kyo_kyoto_station": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市下京区烏丸通塩小路下ル東塩小路町901",
        "nearest_station": "JR京都駅 即到",
        "when": {
            "open_days": "每日",
            "open_hours": "空中径路10:00-22:00（大楼全天开放）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 500,
            "budget_tier": "free"
        },
        "review_signals": {
            "google_rating": 4.2,
            "google_review_count": 15000,
            "dimension_scores": {
                "scenery": 6,
                "cultural_depth": 4,
                "accessibility": 10,
                "crowd_comfort": 7,
                "uniqueness": 5,
                "value_for_money": 10
            },
            "positive_tags": ["空中径路免费观景", "建筑本身是杰作", "购物餐饮一体"],
            "negative_tags": ["景色不算惊艳", "大阶梯灯光秀时间不固定"]
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["kyoto_station"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "原广司设计的现代主义巨构，11层高的大阶梯和屋顶空中走廊完全免费",
            "what_to_expect": "乘电梯到顶层走空中径路俯瞰京都塔，大阶梯有时举办灯光装置艺术",
            "skip_if": "非购物/交通需求，不值得专程参观"
        }
    },
    "kyo_sagano_train": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市右京区嵯峨天龍寺車道町（嵯峨トロッコ駅起点）",
        "nearest_station": "JR嵯峨嵐山駅 徒歩3分（嵯峨トロッコ駅）",
        "when": {
            "open_days": "周三至周一（周二休，繁忙期全周运行）",
            "open_hours": "9:02-16:02（每日约8班）",
            "last_entry": None,
            "closed_notes": "12月下旬-2月末部分日期停运"
        },
        "cost": {
            "admission_jpy": 880,
            "typical_spend_jpy": 1000,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.4,
            "google_review_count": 20000,
            "dimension_scores": {
                "scenery": 9,
                "cultural_depth": 5,
                "accessibility": 7,
                "crowd_comfort": 4,
                "uniqueness": 8,
                "value_for_money": 8
            },
            "positive_tags": ["秋季红叶隧道极震撼", "开放式5号车厢体验独特", "25分钟轻松观光"],
            "negative_tags": ["旺季票需提前抢购", "5号车厢极难买到"]
        },
        "queue_wait_minutes": 20,
        "corridor_tags": ["arashiyama_sagano"],
        "risk_flags": ["requires_reservation", "weather_dependent"],
        "descriptions": {
            "why_selected": "穿越保津峡溪谷的观光列车，秋季红叶隧道是日本最美铁道景观之一",
            "what_to_expect": "25分钟的溪谷旅程，5号开放式车厢可以伸手触碰两侧树叶，搭配保津川漂流是经典组合",
            "skip_if": "非秋季或春季来访（其他季节风景大幅减分）、没有提前预订票"
        }
    },
    "kyo_kimono_experience": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市東山区（租赁店铺集中于祇园・清水寺周边）",
        "nearest_station": "京阪祇園四条駅 徒歩5分",
        "when": {
            "open_days": "每日",
            "open_hours": "9:00-18:00（需当日16:00前归还）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 3500,
            "typical_spend_jpy": 5000,
            "budget_tier": "mid"
        },
        "review_signals": {
            "google_rating": 4.5,
            "google_review_count": 18000,
            "dimension_scores": {
                "scenery": 9,
                "cultural_depth": 7,
                "accessibility": 9,
                "crowd_comfort": 6,
                "uniqueness": 8,
                "value_for_money": 7
            },
            "positive_tags": ["古街和服拍照效果极佳", "情侣闺蜜必备体验", "全套服务方便"],
            "negative_tags": ["雨天穿和服不便", "行动受限不适合爬山景点"]
        },
        "queue_wait_minutes": 30,
        "corridor_tags": ["higashiyama", "gion"],
        "risk_flags": ["requires_reservation", "weather_dependent"],
        "descriptions": {
            "why_selected": "在京都古街穿和服漫步是独一无二的体验，照片效果与身临其境感无可替代",
            "what_to_expect": "店内选衣着装约30-60分钟，之后在东山一带随意游览拍照，傍晚前归还",
            "skip_if": "雨天、行程中有大量爬山行程、对日本传统服饰兴趣不大"
        }
    },
    "kyo_matcha_experience": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市（体验教室分布于嵐山・宇治・祇园等地）",
        "nearest_station": "各教室不同，祇园周边最集中",
        "when": {
            "open_days": "每日（各教室有不同排班）",
            "open_hours": "9:00-17:00（各体验场次约1小时）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 2000,
            "typical_spend_jpy": 3000,
            "budget_tier": "mid"
        },
        "review_signals": {
            "google_rating": 4.4,
            "google_review_count": 12000,
            "dimension_scores": {
                "scenery": 7,
                "cultural_depth": 8,
                "accessibility": 7,
                "crowd_comfort": 8,
                "uniqueness": 8,
                "value_for_money": 7
            },
            "positive_tags": ["亲手点茶正宗体验", "雨天室内活动", "京都特色文化"],
            "negative_tags": ["部分教室英文讲解有限", "体验时间较短"]
        },
        "queue_wait_minutes": 0,
        "corridor_tags": ["gion", "arashiyama"],
        "risk_flags": ["requires_reservation"],
        "descriptions": {
            "why_selected": "京都是抹茶文化的发源地，在茶室亲手点一碗浓茶是感受侘寂美学的最直接方式",
            "what_to_expect": "学习茶道基本礼仪，亲手用茶筅打出抹茶，配上和菓子品茶，约60分钟",
            "skip_if": "对茶道文化完全没兴趣，预算有限"
        }
    },
    "kyo_tofukuji": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市東山区本町15丁目778",
        "nearest_station": "JR・京阪東福寺駅 徒歩10分",
        "when": {
            "open_days": "每日",
            "open_hours": "9:00-16:30（4-10月） / 8:30-16:00（11-12月初红叶期延长）",
            "last_entry": "閉門30分前",
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 600,
            "typical_spend_jpy": 800,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.3,
            "google_review_count": 25000,
            "dimension_scores": {
                "scenery": 7,
                "cultural_depth": 8,
                "accessibility": 8,
                "crowd_comfort": 5,
                "uniqueness": 8,
                "value_for_money": 7
            },
            "positive_tags": ["秋季通天桥红叶京都No.1", "方丈庭园棋盘格苔庭独特", "距京都站近"],
            "negative_tags": ["红叶季通天桥禁止拍照", "非秋季体验普通"]
        },
        "queue_wait_minutes": 30,
        "corridor_tags": ["fushimi"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "秋季红叶期通天桥下的红叶海是京都最壮观的红叶景观，平时方丈庭园也值得一看",
            "what_to_expect": "站在通天桥上俯瞰山谷满眼枫红，方丈庭园的四方形棋盘苔庭是现代枯山水佳作",
            "skip_if": "非秋季红叶期到访"
        }
    },
    "kyo_daigoji": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市伏見区醍醐東大路町22",
        "nearest_station": "地下鉄醍醐駅 徒歩10分",
        "when": {
            "open_days": "每日",
            "open_hours": "9:00-17:00（3-12月） / 9:00-16:00（1-2月）",
            "last_entry": "閉館30分前",
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 1000,
            "typical_spend_jpy": 1500,
            "budget_tier": "mid"
        },
        "review_signals": {
            "google_rating": 4.3,
            "google_review_count": 18000,
            "dimension_scores": {
                "scenery": 8,
                "cultural_depth": 9,
                "accessibility": 5,
                "crowd_comfort": 7,
                "uniqueness": 8,
                "value_for_money": 7
            },
            "positive_tags": ["春季枝垂樱绝美", "五重塔古朴庄严", "秀吉花见历史舞台"],
            "negative_tags": ["距离市中心较远", "非春季感觉一般", "门票偏贵"]
        },
        "queue_wait_minutes": 15,
        "corridor_tags": ["fushimi"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "丰臣秀吉举办著名醍醐花见之地，春季枝垂樱与五重塔的组合是京都赏樱终极画面",
            "what_to_expect": "三宝院庭园的枝垂樱盛开，伽蓝区的五重塔与古朴石灯笼构成绝美构图",
            "skip_if": "非春季赏樱期、距离较远不想花额外交通时间"
        }
    }
}

spots = data['spots']
enriched_count = 0
for spot in spots[:24]:
    sid = spot['id']
    if sid in enrichments:
        e = enrichments[sid]
        spot['city_code'] = e['city_code']
        spot['prefecture'] = e['prefecture']
        spot['address_ja'] = e['address_ja']
        spot['nearest_station'] = e['nearest_station']
        spot['when'] = e['when']
        spot['cost'] = e['cost']
        spot['review_signals'] = e['review_signals']
        spot['queue_wait_minutes'] = e['queue_wait_minutes']
        spot['corridor_tags'] = e['corridor_tags']
        spot['risk_flags'] = e['risk_flags']
        spot['descriptions'] = e['descriptions']
        enriched_count += 1
    else:
        print(f"WARNING: No enrichment data for {sid}")

with open('data/kansai_spots/kyoto_city.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Done. {enriched_count} spots enriched.")
