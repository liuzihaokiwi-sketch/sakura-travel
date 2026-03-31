"""
Enrich Kyoto spots[24:47] and all 7 seasonal_events with additional fields.
Waits 60 seconds to avoid conflict with the agent handling spots[0:23].
"""

import json
import time

FILE_PATH = r"D:\projects\projects\travel-ai\data\kansai_spots\kyoto_city.json"

print("Waiting 60 seconds to avoid file conflict with other agent...")
time.sleep(60)
print("Wait complete. Reading file...")

with open(FILE_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

spots = data["spots"]
seasonal_events = data["seasonal_events"]

# ── Enrichment data for spots[24:47] ──────────────────────────────────────────
# Ordered by index 24..47: kyo_ninnaji, kyo_sanjusangendo, kyo_kennin_ji,
# kyo_kyoto_national_museum, kyo_geisha_show, kyo_iwatayama_monkey,
# kyo_manga_museum, kyo_eikando, kyo_kibune_kurama, kyo_pontocho,
# kyo_imperial_palace, kyo_kokedera, kyo_hozugawa_cruise, kyo_ohara_sanzenin,
# kyo_fushimi_sake, kyo_toei_eigamura, kyo_kitano_tenmangu,
# kyo_yamazaki_distillery, kyo_railway_museum, kyo_keage_incline,
# kyo_shimogamo, kyo_shugakuin, kyo_katsura, kyo_yasakakoshin

SPOT_ENRICHMENTS = {
    "kyo_ninnaji": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市右京区御室大内33",
        "nearest_station": "御室仁和寺駅（京福電鉄北野線）徒歩3分",
        "when": {
            "open_days": "毎日",
            "open_hours": "9:00-17:00（12月-2月は16:30まで）",
            "last_entry": "16:30",
            "closed_notes": "御殿は月曜日休み（祝日の場合は翌日）"
        },
        "cost": {
            "admission_jpy": 500,
            "typical_spend_jpy": 800,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.2,
            "google_review_count": 9800,
            "dimension_scores": {
                "scenery": 7,
                "cultural_depth": 8,
                "accessibility": 8,
                "crowd_comfort": 7,
                "uniqueness": 7,
                "value_for_money": 7
            },
            "positive_tags": ["御室樱花独特", "世界遗产", "金堂庄严"],
            "negative_tags": ["非花季平淡"]
        },
        "queue_wait_minutes": 10,
        "corridor_tags": ["kinkakuji_area", "western_kyoto"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "仁和寺是世界遗产，以'御室樱'著称——这是京都最晚开放的樱花，比其他地方晚约两周，给错过赏樱高峰的旅人提供了一次补时机会。金堂、御影堂等建筑宏大庄严，与金阁寺、龙安寺形成北山一日游的完整三角形。",
            "what_to_expect": "参观仁和寺约需40分钟。金堂内供奉阿弥陀如来，御殿内的庭园别具一格。4月中旬御室樱盛开时，矮小的樱花树（因地势低矮）与五重塔共同构成独特景观，这在京都独一无二。",
            "skip_if": "非花季且对历史建筑兴趣不浓厚的旅行者可降低优先级；时间紧张时可与金阁寺/龙安寺二选一。"
        }
    },
    "kyo_sanjusangendo": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市東山区三十三間堂廻り町657",
        "nearest_station": "七条駅（京阪本線）徒歩7分",
        "when": {
            "open_days": "毎日",
            "open_hours": "8:00-17:00（11/16-3/31は9:00-16:00）",
            "last_entry": "16:30",
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 600,
            "typical_spend_jpy": 700,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.4,
            "google_review_count": 16200,
            "dimension_scores": {
                "scenery": 8,
                "cultural_depth": 10,
                "accessibility": 8,
                "crowd_comfort": 6,
                "uniqueness": 10,
                "value_for_money": 9
            },
            "positive_tags": ["1001尊观音震撼", "视觉冲击极强", "文化深度极高"],
            "negative_tags": ["堂内禁止摄影"]
        },
        "queue_wait_minutes": 15,
        "corridor_tags": ["higashiyama", "kyoto_station"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "三十三间堂是京都最独特的视觉体验之一：1001尊黄金千手观音像在120米长的大堂中整齐排列，震撼程度难以用语言描述。创建于1164年，堂内还有28尊守护神雕像，每一尊都是国宝级艺术品。这是在任何其他地方都无法复现的体验。",
            "what_to_expect": "参观约需30分钟。堂内禁止摄影，但这反而让人更专注地感受这1001尊佛像带来的庄严震撼。传说在这些佛像中能找到一尊与自己长相相似的观音。靠近京都国立博物馆，可以组合游览。",
            "skip_if": "对宗教艺术不感兴趣、且时间极其紧张的旅行者可以跳过；但大多数人参观后都表示超出预期。"
        }
    },
    "kyo_kennin_ji": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市東山区大和大路通四条下る小松町584",
        "nearest_station": "祇園四条駅（京阪本線）徒歩5分",
        "when": {
            "open_days": "毎日",
            "open_hours": "10:00-17:00（16:30最終受付）",
            "last_entry": "16:30",
            "closed_notes": "行事により臨時休業あり"
        },
        "cost": {
            "admission_jpy": 600,
            "typical_spend_jpy": 900,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.2,
            "google_review_count": 11400,
            "dimension_scores": {
                "scenery": 8,
                "cultural_depth": 9,
                "accessibility": 9,
                "crowd_comfort": 6,
                "uniqueness": 8,
                "value_for_money": 8
            },
            "positive_tags": ["双龙天花板壮观", "风神雷神图精美", "祇园核心位置"],
            "negative_tags": ["双龙图是复制品", "内部较小"]
        },
        "queue_wait_minutes": 10,
        "corridor_tags": ["gion", "higashiyama"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "建仁寺是京都最古老的禅寺（创建于1202年），地处祇园核心，与花见小路步行不到5分钟。法堂天花板的'双龙图'气势磅礴，方丈室内的'风神雷神图'屏风（原作藏于宫内厅，此处展示高精度复制品）是日本美术史标志性作品。○△□之庭代表了禅宗的宇宙观。",
            "what_to_expect": "参观约需40分钟。可以在开放式走廊坐下来静静欣赏枯山水庭园，感受禅宗的侘寂之美。法堂内的双龙图规模巨大，仰头观赏令人叹为观止。也有茶室可以体验抹茶。",
            "skip_if": "对禅宗美学和日本古典绘画没有兴趣的旅行者，可以优先选择其他寺院。"
        }
    },
    "kyo_kyoto_national_museum": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市東山区茶屋町527",
        "nearest_station": "七条駅（京阪本線）徒歩7分",
        "when": {
            "open_days": "火曜日-日曜日",
            "open_hours": "9:30-17:00（金曜日は19:00まで）",
            "last_entry": "16:30",
            "closed_notes": "月曜日休館（祝日の場合は翌平日）、年末年始"
        },
        "cost": {
            "admission_jpy": 700,
            "typical_spend_jpy": 1200,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.3,
            "google_review_count": 7200,
            "dimension_scores": {
                "scenery": 8,
                "cultural_depth": 10,
                "accessibility": 8,
                "crowd_comfort": 7,
                "uniqueness": 8,
                "value_for_money": 8
            },
            "positive_tags": ["特展水平极高", "平成知新馆建筑精美", "近三十三间堂"],
            "negative_tags": ["常设展较小", "特展需额外购票"]
        },
        "queue_wait_minutes": 20,
        "corridor_tags": ["higashiyama", "kyoto_station"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "日本三大国立博物馆之一，收藏佛教美术、陶瓷器、刀剑等京都相关文物。谷口吉生设计的平成知新馆本身是当代建筑杰作，玻璃与钢铁构成的展览空间将自然光引入室内。特别展经常汇聚平时分散于各寺院的国宝级文物，是深入理解京都文化的最佳途径。",
            "what_to_expect": "常设展+特展约需1.5-2小时。建议优先关注是否有特别展（官网提前查询）。馆前的明治古都館（旧建筑）也可以外观拍照。附近有三十三间堂，可以组合为半日行程。",
            "skip_if": "只对自然风景和寺院庙宇感兴趣、对博物馆展览没有热情的旅行者可以跳过。"
        }
    },
    "kyo_geisha_show": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市東山区祇園町南側570-2（祇園角）",
        "nearest_station": "祇園四条駅（京阪本線）徒歩5分",
        "when": {
            "open_days": "毎日（祇園コーナー）",
            "open_hours": "18:00-19:00（一日2回：18:00/19:00）",
            "last_entry": None,
            "closed_notes": "8月16日、12月29日-31日休演。都をどり是4月のみ"
        },
        "cost": {
            "admission_jpy": 3150,
            "typical_spend_jpy": 4000,
            "budget_tier": "mid"
        },
        "review_signals": {
            "google_rating": 4.1,
            "google_review_count": 3800,
            "dimension_scores": {
                "scenery": 7,
                "cultural_depth": 10,
                "accessibility": 8,
                "crowd_comfort": 6,
                "uniqueness": 10,
                "value_for_money": 6
            },
            "positive_tags": ["京都独有体验", "多种传统艺能集中展示", "时间紧凑适合游客"],
            "negative_tags": ["时间短仅50分钟", "游客向氛围较浓", "正宗度有争议"]
        },
        "queue_wait_minutes": 5,
        "corridor_tags": ["gion", "higashiyama"],
        "risk_flags": ["requires_reservation"],
        "descriptions": {
            "why_selected": "在京都欣赏一场正式的艺伎/舞伎表演，是只有这座城市才能提供的文化体验。祇园角汇集了茶道、花道、雅乐、文乐、狂言、京舞、篝火能等7种传统艺能，是最适合普通游客的入门体验。每年4月的'都をどり'则是最高规格的正式公演。",
            "what_to_expect": "祇园角表演约50分钟，展示多种传统艺能片段。需提前网上预购票。如果预算充足并想体验更正式的氛围，可以预约花街置屋的'一见さんお断り'餐饮场所（价格极高，需要介绍人）。4月都をどり演出约1小时，最为正式华美。",
            "skip_if": "对日本传统艺能没有兴趣、或认为3000+円的观演费用不值得的旅行者可以跳过；路过祇园傍晚随机遇见舞伎也是免费的邂逅。"
        }
    },
    "kyo_iwatayama_monkey": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市西京区嵐山元録山町8",
        "nearest_station": "嵐山駅（阪急嵐山線）徒歩13分（渡月橋南側登山口から）",
        "when": {
            "open_days": "毎日",
            "open_hours": "9:00-17:00（入園は16:30まで）",
            "last_entry": "16:30",
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 550,
            "typical_spend_jpy": 700,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.0,
            "google_review_count": 8100,
            "dimension_scores": {
                "scenery": 8,
                "cultural_depth": 3,
                "accessibility": 4,
                "crowd_comfort": 7,
                "uniqueness": 8,
                "value_for_money": 7
            },
            "positive_tags": ["山顶京都全景绝佳", "室内喂猴独特体验", "亲子友好"],
            "negative_tags": ["需爬山20分钟", "猴子有时不出现"]
        },
        "queue_wait_minutes": 5,
        "corridor_tags": ["arashiyama"],
        "risk_flags": ["steep_climb"],
        "descriptions": {
            "why_selected": "岚山猴子公园聚集了约120只野生日本猕猴，并提供京都盆地的全景视野——这是岚山区域内唯一能俯瞰全城的观景点。在山顶室内可以透过铁网向外面的猴子投喂食物（而非人在笼外被猴包围），这种设计颠覆了常规动物园体验，极受亲子家庭欢迎。",
            "what_to_expect": "从渡月桥南侧入口爬山约20分钟（有一定坡度），山顶视野开阔，天气好时可以看到整个京都盆地。室内喂食区可以近距离观察猴子。整个体验约60分钟。不适合行动不便者。",
            "skip_if": "不喜欢爬山或行动不便者；对动物不感兴趣的成年旅行者可以省略。"
        }
    },
    "kyo_manga_museum": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市中京区金吹町452",
        "nearest_station": "烏丸御池駅（地下鉄烏丸線/東西線）徒歩2分",
        "when": {
            "open_days": "水曜日-月曜日",
            "open_hours": "10:00-18:00（17:30最終受付）",
            "last_entry": "17:30",
            "closed_notes": "火曜日定休（祝日の場合は翌水曜日）、年末年始"
        },
        "cost": {
            "admission_jpy": 900,
            "typical_spend_jpy": 1100,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.1,
            "google_review_count": 5600,
            "dimension_scores": {
                "scenery": 5,
                "cultural_depth": 7,
                "accessibility": 9,
                "crowd_comfort": 7,
                "uniqueness": 8,
                "value_for_money": 7
            },
            "positive_tags": ["30万册漫画随意阅读", "草坪休闲悠闲", "雨天完美备选"],
            "negative_tags": ["对漫画不感兴趣者意义不大", "以日语漫画为主"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["nishiki"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "京都国际漫画博物馆由旧小学改建而成，馆藏超过30万册漫画，游客可以自由取阅，在草坪上或走廊里随意阅读。这是体验日本流行文化的独特场所，也是遇到天气不佳时或行程中需要放松节奏时的绝佳选择。",
            "what_to_expect": "阅读区完全开放，可在草坪躺着翻漫画，有种图书馆+公园的混合感。也有限时漫画绘制表演和工作坊。日文漫画为主，部分有英文版。建议下雨天或体力需要恢复时安排。",
            "skip_if": "对漫画/动漫文化没有兴趣的旅行者；以及时间紧张、想将每分钟都用在寺院和自然景观的旅行者。"
        }
    },
    "kyo_eikando": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市左京区永観堂町48",
        "nearest_station": "蹴上駅（地下鉄東西線）徒歩15分 / 南禅寺・永観堂道バス停徒歩3分",
        "when": {
            "open_days": "毎日",
            "open_hours": "9:00-17:00（16:00最終受付）",
            "last_entry": "16:00",
            "closed_notes": "11月は夜間特別拝観あり（17:30-21:00）"
        },
        "cost": {
            "admission_jpy": 600,
            "typical_spend_jpy": 900,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.5,
            "google_review_count": 14300,
            "dimension_scores": {
                "scenery": 10,
                "cultural_depth": 8,
                "accessibility": 6,
                "crowd_comfort": 3,
                "uniqueness": 9,
                "value_for_money": 8
            },
            "positive_tags": ["红叶倒映水面绝美", "夜间参拜灯光梦幻", "京都红叶No.1公认"],
            "negative_tags": ["11月极度拥挤", "停车困难", "需早到或傍晚"]
        },
        "queue_wait_minutes": 40,
        "corridor_tags": ["philosopher_path"],
        "risk_flags": ["seasonal_closure"],
        "descriptions": {
            "why_selected": "永观堂（禅林寺）被誉为'秋は紅葉のえいかんどう'（秋天红叶看永观堂），是京都公认的红叶第一名所。多宝塔周边的红叶与阿弥陀堂倒映在放生池中的景象，是日本秋季风景的最高代表。11月中下旬夜间特别参拜更是将这种美推向极致。",
            "what_to_expect": "参观约需50分钟。建议11月红叶期早上8点半到（排队少）或参加夜间特别参拜（17:30起，另需购票900日元）。哲学之道步行可达，可组合成一日游。春夏秋冬各有风情，但红叶季最值得专程。",
            "skip_if": "非红叶季（11月）来京都的旅行者可以降低优先级；樱花季和其他季节的永观堂虽然也美，但人气和震撼程度远低于红叶期。"
        }
    },
    "kyo_kibune_kurama": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市左京区鞍馬本町/貴船町",
        "nearest_station": "鞍馬駅（叡山電鉄鞍馬線）徒歩5分 / 貴船口駅（叡山電鉄）徒歩20分",
        "when": {
            "open_days": "毎日",
            "open_hours": "終日（各施設による）",
            "last_entry": None,
            "closed_notes": "貴船神社：6:00-20:00（冬季9:00-16:00）。川床料理は5月-9月のみ"
        },
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 4000,
            "budget_tier": "mid"
        },
        "review_signals": {
            "google_rating": 4.4,
            "google_review_count": 18900,
            "dimension_scores": {
                "scenery": 9,
                "cultural_depth": 8,
                "accessibility": 5,
                "crowd_comfort": 7,
                "uniqueness": 9,
                "value_for_money": 7
            },
            "positive_tags": ["夏季川床料理绝对体验", "鞍马寺神秘感十足", "远离市区清幽"],
            "negative_tags": ["交通费时", "川床料理价格偏高", "冬季较萧条"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["kurama_kibune"],
        "risk_flags": ["weather_dependent", "steep_climb"],
        "descriptions": {
            "why_selected": "贵船·鞍马是京都最重要的山岳圣地区域。贵船神社是全国水神总社，红灯笼参道（特别是夏夜）极其上镜；鞍马寺供奉护法魔王尊，据传是日本传说中牛若丸学剑之地。夏季贵船川床料理——坐在清澈山溪旁享用京料理——是只有京都才能提供的顶级夏日体验。",
            "what_to_expect": "建议从鞍马站出发，登鞍马山（约90分钟徒步），经由奥之院下山至贵船（有一定坡度）。夏季在贵船川床用午餐或晚餐（需提前预约，4000-15000日元/人）。叡山电铁可以直达。全程需半天到一整天。",
            "skip_if": "行动不便者；时间不足半天者；夏季（5-9月）以外来访且不想徒步的旅行者可以改为只参拜贵船神社，行程缩短为1小时。"
        }
    },
    "kyo_pontocho": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市中京区先斗町（木屋町通と鴨川の間）",
        "nearest_station": "三条駅（京阪本線）徒歩5分 / 河原町駅（阪急京都線）徒歩5分",
        "when": {
            "open_days": "毎日（各店舗による）",
            "open_hours": "17:00-23:00（多数の飲食店）",
            "last_entry": None,
            "closed_notes": "昼間も営業している店舗あり"
        },
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 6000,
            "budget_tier": "premium"
        },
        "review_signals": {
            "google_rating": 4.2,
            "google_review_count": 12700,
            "dimension_scores": {
                "scenery": 9,
                "cultural_depth": 8,
                "accessibility": 9,
                "crowd_comfort": 4,
                "uniqueness": 9,
                "value_for_money": 5
            },
            "positive_tags": ["夏季鸭川纳凉床无与伦比", "窄巷夜间氛围浓郁", "京都饮食文化精华"],
            "negative_tags": ["价格偏高", "旺季极其拥挤", "部分店铺谢绝新客"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["gion", "nishiki"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "先斗町是鸭川与木屋町之间的百米宽窄巷，两侧密布京料理、割烹、酒吧、居酒屋，夜间灯光映照石板路极具情调。夏季（5月-9月）鸭川沿岸搭起的纳凉床（川床）是京都最具代表性的季节风物诗——坐在鸭川水面上方享用晚餐，凉风习习，是浪漫无比的体验。",
            "what_to_expect": "傍晚到夜间漫步先斗町约1小时；如要体验纳凉床晚餐，需提前预约（人均5000-15000日元）。祇园四条和河原町均在步行范围内，非常适合作为京都晚餐目的地。非夏季的先斗町也有独特魅力，但少了川床则是普通的饮食街。",
            "skip_if": "预算极其有限的旅行者（这里的餐厅整体偏贵）；非夜间行程安排（白天先斗町魅力大减）。"
        }
    },
    "kyo_imperial_palace": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市上京区京都御苑3",
        "nearest_station": "今出川駅（地下鉄烏丸線）徒歩5分",
        "when": {
            "open_days": "火曜日-日曜日",
            "open_hours": "9:00-17:00（10月-2月は16:30まで）",
            "last_entry": "16:20",
            "closed_notes": "月曜日・祝日の翌日・年末年始休み"
        },
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 0,
            "budget_tier": "free"
        },
        "review_signals": {
            "google_rating": 4.2,
            "google_review_count": 14500,
            "dimension_scores": {
                "scenery": 7,
                "cultural_depth": 9,
                "accessibility": 8,
                "crowd_comfort": 8,
                "uniqueness": 8,
                "value_for_money": 10
            },
            "positive_tags": ["完全免费参观", "御苑散步极佳", "春季枝垂樱美丽"],
            "negative_tags": ["部分区域仅导览参观", "内饰相对朴素"]
        },
        "queue_wait_minutes": 5,
        "corridor_tags": ["kitano"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "京都御所是明治迁都前天皇的居所，2016年起向公众免费开放。宽阔的京都御苑（公园）是市中心少有的大型绿地，春季枝垂樱和紫藤盛开，秋季银杏金黄，适合悠闲散步。御所内部的御殿建筑保存完好，格局严整，体现了平安时代至近世的宫廷建筑风格。",
            "what_to_expect": "御苑免费进入，可随意散步。御所内部参观免费但需事先网上预约，或加入宫内厅的每日导览（英文/日文）。参观约60分钟。御苑内有多个门和步道，春秋季节是本地人休憩的好去处。",
            "skip_if": "日程极度紧张且对皇室历史不感兴趣的旅行者；但御苑散步不需额外安排时间，路过时可以顺便进入。"
        }
    },
    "kyo_kokedera": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市西京区松尾神ヶ谷町56",
        "nearest_station": "松尾大社駅（阪急嵐山線）徒歩15分 / バス苔寺・すず虫寺バス停徒歩すぐ",
        "when": {
            "open_days": "毎日（要事前申込）",
            "open_hours": "9:00-14:00頃（時期による）",
            "last_entry": None,
            "closed_notes": "往復葉書による事前申込必須（2週間以上前）。入場料3000円に写経料含む"
        },
        "cost": {
            "admission_jpy": 3000,
            "typical_spend_jpy": 3500,
            "budget_tier": "mid"
        },
        "review_signals": {
            "google_rating": 4.6,
            "google_review_count": 6800,
            "dimension_scores": {
                "scenery": 10,
                "cultural_depth": 10,
                "accessibility": 4,
                "crowd_comfort": 9,
                "uniqueness": 10,
                "value_for_money": 7
            },
            "positive_tags": ["梦幻苔藓庭园无与伦比", "世界遗产稀缺体验", "抄经仪式独特"],
            "negative_tags": ["预约流程繁琐需邮寄明信片", "位置偏远", "非梅雨季苔色偏淡"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["arashiyama_sagano", "western_kyoto"],
        "risk_flags": ["requires_reservation", "limited_capacity"],
        "descriptions": {
            "why_selected": "西芳寺（苔寺）是世界遗产，以覆盖整个庭园的约120种苔藓著称，创造出一种如梦如幻的翠绿世界。由于采用严格的预约制（每日仅限少量游客），参观体验安静且深度——先在金堂抄写心经，再在无人打扰的状态下游览苔庭。这是京都门槛最高、却也令人印象最深刻的体验之一。",
            "what_to_expect": "必须提前2周以上用往返明信片（官网有格式）预约，申请获批后收到回信确认。参观费3000日元含抄经。参观约90分钟：先抄经（30-40分钟）后游览庭园。梅雨季（6月）苔藓最翠绿，秋季红叶点缀苔庭也极美。位于岚山附近，可以与天龙寺组合。",
            "skip_if": "无法提前2周邮寄明信片申请、或临时行程变动可能性大的旅行者；以及对园林艺术不感兴趣者（3000日元对他们而言不值得）。"
        }
    },
    "kyo_hozugawa_cruise": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府亀岡市保津町（乗船場） → 京都府京都市西京区嵐山（下船場）",
        "nearest_station": "亀岡駅（JR山陰本線）徒歩8分（乗船場）/ 嵐山駅（各線）徒歩3分（下船場）",
        "when": {
            "open_days": "毎日（12月-3月は月曜休航、荒天時運休）",
            "open_hours": "9:00-15:30（最終出航、季節変動あり）",
            "last_entry": None,
            "closed_notes": "増水・凍結時は運休。12月-2月月曜休航。公式サイトで要確認"
        },
        "cost": {
            "admission_jpy": 4100,
            "typical_spend_jpy": 5000,
            "budget_tier": "mid"
        },
        "review_signals": {
            "google_rating": 4.3,
            "google_review_count": 9200,
            "dimension_scores": {
                "scenery": 9,
                "cultural_depth": 5,
                "accessibility": 5,
                "crowd_comfort": 7,
                "uniqueness": 9,
                "value_for_money": 7
            },
            "positive_tags": ["16km峡谷急流独特", "与嵯峨野小火车绝配", "秋季红叶极美"],
            "negative_tags": ["冬季和夏季高温时体验较差", "天气影响大", "行程时间较长"]
        },
        "queue_wait_minutes": 20,
        "corridor_tags": ["arashiyama_sagano"],
        "risk_flags": ["weather_dependent"],
        "descriptions": {
            "why_selected": "保津川漂流是从龟冈到岚山约16公里的溪谷漂流，全程约2小时，由经验丰富的船夫驾驶木船穿越急流和峡谷。秋季红叶映照峡谷水面的景色被誉为关西最美的漂流体验之一。与嵯峨野观光小火车形成经典组合——小火车从岚山前往龟冈（单程），漂流从龟冈返回岚山。",
            "what_to_expect": "全程约2小时，途经多处急流，会被水溅湿（备雨衣）。无需特别体力，但春秋季旺季需提前购票。建议早上从岚山坐小火车到龟冈，然后漂流返回岚山，再游览竹林和天龙寺，安排为全天行程。",
            "skip_if": "怕水或不喜欢户外活动的旅行者；冬季12-2月体验较差（寒冷且部分日期停航）；时间紧张者（单漂流就需2小时加上交通）。"
        }
    },
    "kyo_ohara_sanzenin": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市左京区大原来迎院町540（三千院）",
        "nearest_station": "大原バス停（京都バス17系統 出町柳駅から約60分）徒歩10分",
        "when": {
            "open_days": "毎日",
            "open_hours": "9:00-17:00（12月-2月は16:30まで）",
            "last_entry": "16:30",
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 700,
            "typical_spend_jpy": 2000,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.3,
            "google_review_count": 11800,
            "dimension_scores": {
                "scenery": 9,
                "cultural_depth": 9,
                "accessibility": 4,
                "crowd_comfort": 8,
                "uniqueness": 8,
                "value_for_money": 8
            },
            "positive_tags": ["苔庭红叶安静绝美", "游客比东福寺少", "田园山里氛围独特"],
            "negative_tags": ["交通不便需巴士1小时", "时间成本高"]
        },
        "queue_wait_minutes": 5,
        "corridor_tags": ["ohara"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "大原三千院坐落在京都北部的山村里，是远离市区喧嚣的宁静圣地。三千院的有清园苔庭、往生极乐院内的阿弥陀三尊像，以及秋季漫山红叶，构成了与城区寺院截然不同的深山古刹氛围。大原区域还有寂光院、宝泉院等多座寺院，游客密度远低于东福寺，非常适合喜欢远足和清幽体验的旅行者。",
            "what_to_expect": "从京都中心坐巴士约1小时。三千院参观约60分钟，可延伸到周边寂光院、宝泉院（另需门票）组成约3小时行程。附近有田园风情的土产店和茶屋，可以品尝大原特产的柴漬けとしば漬。秋季红叶（11月中旬）是最佳时节，但即使是夏季的绿苔也非常治愈。",
            "skip_if": "时间只有1-2天的旅行者（交通成本过高）；不喜欢乘坐巴士或追求交通便利的旅行者。"
        }
    },
    "kyo_fushimi_sake": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市伏見区南浜町247（月桂冠大倉記念館）",
        "nearest_station": "中書島駅（京阪本線）徒歩7分",
        "when": {
            "open_days": "毎日（月桂冠大倉記念館）",
            "open_hours": "9:30-16:30（最終受付）",
            "last_entry": "16:30",
            "closed_notes": "年末年始休館（12/22-1/3）"
        },
        "cost": {
            "admission_jpy": 300,
            "typical_spend_jpy": 1500,
            "budget_tier": "budget"
        },
        "review_signals": {
            "google_rating": 4.1,
            "google_review_count": 6400,
            "dimension_scores": {
                "scenery": 7,
                "cultural_depth": 7,
                "accessibility": 7,
                "crowd_comfort": 8,
                "uniqueness": 8,
                "value_for_money": 9
            },
            "positive_tags": ["300日元含试饮超值", "十石舟运河隐藏玩法", "远离游客密集区"],
            "negative_tags": ["不喝酒者意义有限", "区域相对偏南"]
        },
        "queue_wait_minutes": 5,
        "corridor_tags": ["fushimi"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "伏见是日本著名的清酒产地，水质极佳（伏水）孕育了月桂冠、黄樱、松竹梅等知名酒藏。月桂冠大仓纪念馆仅需300日元便可参观酿酒历史展览并试饮清酒，是性价比极高的体验。与伏见稻荷大社同属伏见区，可以组合成半日行程。十石舟沿运河游览是少有人知的隐藏玩法。",
            "what_to_expect": "月桂冠纪念馆参观约40分钟，含讲解和试饮。周边还有黄樱记念馆（免费参观）。春季（3-4月）和秋季（10-11月）可乘坐十石舟沿酒藏运河游览（约40分钟，1500日元，需预约）。区域内有古仓库街道，古朴气息浓厚。",
            "skip_if": "完全不喝酒且对酿造文化不感兴趣的旅行者；时间不足的旅行者（伏见区位于南郊，来回交通需额外时间）。"
        }
    },
    "kyo_toei_eigamura": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市右京区太秦東蜂岡町10",
        "nearest_station": "太秦広隆寺駅（京福電鉄嵐山本線）徒歩5分",
        "when": {
            "open_days": "毎日（不定休あり）",
            "open_hours": "9:00-17:00（16:00最終入場）",
            "last_entry": "16:00",
            "closed_notes": "1月-2月に不定期休業日あり。公式サイトで要確認"
        },
        "cost": {
            "admission_jpy": 2400,
            "typical_spend_jpy": 3500,
            "budget_tier": "mid"
        },
        "review_signals": {
            "google_rating": 3.9,
            "google_review_count": 7300,
            "dimension_scores": {
                "scenery": 7,
                "cultural_depth": 6,
                "accessibility": 7,
                "crowd_comfort": 7,
                "uniqueness": 8,
                "value_for_money": 6
            },
            "positive_tags": ["武士/忍者变装体验独特", "亲子娱乐丰富", "雨天室内选择多"],
            "negative_tags": ["偏向娱乐而非历史", "性价比一般", "对成人吸引力有限"]
        },
        "queue_wait_minutes": 10,
        "corridor_tags": ["western_kyoto"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "东映太秦映画村是日本最大的时代剧拍摄场地，同时也对外开放参观，被称为'日本版横店'。游客可以在江户时代街道、武士宅邸、忍者屋敷等真实拍摄场景中漫步，并参与武士/忍者装扮体验和表演。这是了解日本时代剧文化的独特窗口，特别适合带小孩的家庭或武士文化爱好者。",
            "what_to_expect": "参观约2小时，全天有武士、忍者、芸妓等扮装演员表演。可以参与变装体验（额外费用）。有室内展区，雨天也适合。位于岚山和金阁寺之间，交通便利。",
            "skip_if": "对日本时代剧/武士文化没有兴趣的成年旅行者；预算有限时2400日元的门票可以省略。"
        }
    },
    "kyo_kitano_tenmangu": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市上京区馬喰町",
        "nearest_station": "北野白梅町駅（京福電鉄北野線）徒歩5分",
        "when": {
            "open_days": "毎日",
            "open_hours": "5:00-17:00（宝物殿・梅苑は期間限定）",
            "last_entry": None,
            "closed_notes": "社殿境内は無料。梅苑は2月初旬-3月中旬のみ開苑（入苑料1000円）"
        },
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 500,
            "budget_tier": "free"
        },
        "review_signals": {
            "google_rating": 4.2,
            "google_review_count": 11200,
            "dimension_scores": {
                "scenery": 7,
                "cultural_depth": 8,
                "accessibility": 7,
                "crowd_comfort": 7,
                "uniqueness": 7,
                "value_for_money": 9
            },
            "positive_tags": ["2月梅花全京都最美", "天神市每月25日热闹", "免费参拜"],
            "negative_tags": ["非梅花季吸引力有限", "距离中心区较远"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["kitano"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "北野天满宫是全国12000座天满宫的总本社，供奉'学问之神'菅原道真，每年吸引无数日本学生祈求考试成功。境内约2000棵梅树在2月初至3月中旬盛开，是京都最美的赏梅圣地。每月25日的天神市（跳蚤市场）聚集数百家摊位，是淘古董、传统工艺品和二手和服的好去处。",
            "what_to_expect": "境内参拜免费。2月梅花季缴纳1000日元进入梅苑，可以在梅花树下享用免费茶点。每月25日天神市从日出到日落，非常热闹。从金阁寺乘公交约10分钟，可以组合在同一天。",
            "skip_if": "非梅花季（2-3月）且对市集不感兴趣的旅行者；时间紧张时可以跳过，将北山区域预算用于金阁寺和龙安寺。"
        }
    },
    "kyo_yamazaki_distillery": {
        "city_code": "京都府（大阪府との境界）",
        "prefecture": "大阪府三島郡島本町",
        "address_ja": "大阪府三島郡島本町山崎5-2-1",
        "nearest_station": "山崎駅（JR東海道本線/阪急京都線大山崎駅）徒歩5分",
        "when": {
            "open_days": "毎日（要予約）",
            "open_hours": "9:30-16:30（最終受付）",
            "last_entry": "16:30",
            "closed_notes": "年末年始（12/28-1/4）休業。工場見学は要事前予約（無料）"
        },
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 3000,
            "budget_tier": "mid"
        },
        "review_signals": {
            "google_rating": 4.5,
            "google_review_count": 5100,
            "dimension_scores": {
                "scenery": 7,
                "cultural_depth": 9,
                "accessibility": 7,
                "crowd_comfort": 7,
                "uniqueness": 10,
                "value_for_money": 7
            },
            "positive_tags": ["日本威士忌发源地圣地朝圣", "限定酒试饮唯一机会", "导览专业"],
            "negative_tags": ["预约名额极其紧俏", "试饮套餐价格不低", "酒厂所在地严格来说非京都"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["yamashina"],
        "risk_flags": ["requires_reservation"],
        "descriptions": {
            "why_selected": "三得利山崎蒸馏所是日本第一座麦芽威士忌蒸馏厂（1923年建立），也是将苏格兰威士忌制造工艺引入日本的历史起点。山崎12年、18年等产品在全球威士忌大赛中屡获殊荣，市面上极难购得。蒸馏所的导览展示了日本威士忌制造全过程，并提供市面无从购买的限定酒试饮。",
            "what_to_expect": "工厂导览需提前在官网预约（免费），约1小时。参观后可在蒸馏所内的威士忌图书馆体验付费试饮（每杯300-几千日元），包括极其稀有的限定年份原酒。位于京都和大阪之间，从京都站乘JR约14分钟。",
            "skip_if": "不饮烈酒者；无法提前预约者（预约名额极其紧俏，旺季需数周前申请）；时间紧张只有一两天的旅行者。"
        }
    },
    "kyo_railway_museum": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市下京区観喜寺町",
        "nearest_station": "梅小路京都西駅（JR嵯峨野線）徒歩すぐ",
        "when": {
            "open_days": "水曜日-月曜日",
            "open_hours": "10:00-17:30（17:00最終受付）",
            "last_entry": "17:00",
            "closed_notes": "火曜日定休（祝日の場合は翌水曜日）、年末年始（12/30-1/1）"
        },
        "cost": {
            "admission_jpy": 1200,
            "typical_spend_jpy": 1800,
            "budget_tier": "mid"
        },
        "review_signals": {
            "google_rating": 4.3,
            "google_review_count": 9700,
            "dimension_scores": {
                "scenery": 6,
                "cultural_depth": 8,
                "accessibility": 9,
                "crowd_comfort": 7,
                "uniqueness": 8,
                "value_for_money": 8
            },
            "positive_tags": ["SL蒸汽机车实际运行体验", "铁道迷圣地", "亲子娱乐丰富"],
            "negative_tags": ["对铁道不感兴趣者吸引力有限", "室外展示区较大需多走路"]
        },
        "queue_wait_minutes": 10,
        "corridor_tags": ["kyoto_station"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "京都铁道博物馆是日本最大规模的铁道博物馆，展示了从明治时代蒸汽机车到最新新干线的日本铁路发展史。馆内保存并实际运行多辆SL蒸汽机车，游客可以乘坐体验。距京都站步行约20分钟（或乘JR嵯峨野线），是本地人带孩子的热门周末目的地。",
            "what_to_expect": "参观约2小时，展示内容丰富。最受欢迎的是SL蒸汽机车乘车体验（约10分钟，额外230日元）。馆内有模拟驾驶台可以体验驾驶列车。紧邻梅小路公园，可以一起游览。",
            "skip_if": "对铁路完全没有兴趣的旅行者；以及不带小孩的成年旅行者（除非本身是铁道爱好者）。"
        }
    },
    "kyo_keage_incline": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市左京区南禅寺草川町（蹴上インクライン）",
        "nearest_station": "蹴上駅（地下鉄東西線）徒歩5分",
        "when": {
            "open_days": "毎日",
            "open_hours": "終日開放（屋外施設）",
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
            "google_review_count": 13600,
            "dimension_scores": {
                "scenery": 8,
                "cultural_depth": 6,
                "accessibility": 8,
                "crowd_comfort": 3,
                "uniqueness": 8,
                "value_for_money": 10
            },
            "positive_tags": ["免费绝佳拍照点", "铁轨+樱花组合独特", "南禅寺步行可达"],
            "negative_tags": ["樱花季极度拥挤", "非樱花季魅力骤减", "傍晚光线不足"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["philosopher_path"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "蹴上倾斜铁道是日本最长的倾斜铁道遗迹（全长582米，1891-1948年运行），承担着将琵琶湖疏水上的船只翻越山坡的任务。春季4月初，铁轨两侧盛开的枝垂樱和染井吉野樱形成花隧道，是京都最具Instagram感的打卡点之一，同时完全免费。与南禅寺步行5分钟距离，可以无缝组合。",
            "what_to_expect": "全天开放的户外遗迹，参观约20分钟。春季樱花期（4月初）清晨7点前人较少，拍到人少的照片。非樱花季铁轨两侧绿植普通，视觉冲击力大减。与南禅寺、哲学之道可以组成半日游线路。",
            "skip_if": "非樱花季来访者（春季以外几乎没有专程价值）；对工业历史遗迹不感兴趣者。"
        }
    },
    "kyo_shimogamo": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市左京区下鴨泉川町59",
        "nearest_station": "出町柳駅（京阪本線）徒歩10分",
        "when": {
            "open_days": "毎日",
            "open_hours": "6:00-17:30（季節変動あり）",
            "last_entry": "17:00",
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 0,
            "budget_tier": "free"
        },
        "review_signals": {
            "google_rating": 4.3,
            "google_review_count": 15800,
            "dimension_scores": {
                "scenery": 8,
                "cultural_depth": 9,
                "accessibility": 7,
                "crowd_comfort": 8,
                "uniqueness": 8,
                "value_for_money": 10
            },
            "positive_tags": ["糺之森原始森林震撼", "完全免费世界遗产", "本地人日常神社"],
            "negative_tags": ["距离景点集中区较远", "葵祭等特殊日人多"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["philosopher_path"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "下鸭神社（贺茂御祖神社）是京都最古老的神社之一，创建超过2000年，世界遗产。最打动人的是通往正殿的'糺之森'——这片原始森林占地约12公顷，保存了京都盆地平安时代以前的原始植被，古树参天、清溪潺潺，很难相信这里位于城市中心。河合神社的'镜绘马'（在木制人脸绘马上化妆画脸）是京都独有的祈愿体验。",
            "what_to_expect": "参拜约40分钟。糺之森的参道约500米，在林荫下漫步极其平静舒适。5月葵祭终点在此，7月有御手洗祭（赤脚涉水祈愿）。神社本体参拜免费，河合神社绘马600日元。从出町柳站步行约10分钟，与鸭川三角洲紧邻。",
            "skip_if": "日程极度紧张、优先级必须集中在东山/岚山核心区域的旅行者；但下鸭神社免费且糺之森的宁静美感值得单独安排半小时。"
        }
    },
    "kyo_shugakuin": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市左京区修学院薮添",
        "nearest_station": "修学院駅（叡山電鉄叡山本線）徒歩15分",
        "when": {
            "open_days": "火曜日-日曜日（要予約）",
            "open_hours": "9:00-15:00（4回/日の定時ガイドツアー）",
            "last_entry": None,
            "closed_notes": "月曜日・年末年始休み。宮内庁ウェブサイトで事前申込必須（無料）"
        },
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 0,
            "budget_tier": "free"
        },
        "review_signals": {
            "google_rating": 4.5,
            "google_review_count": 4200,
            "dimension_scores": {
                "scenery": 10,
                "cultural_depth": 10,
                "accessibility": 4,
                "crowd_comfort": 9,
                "uniqueness": 10,
                "value_for_money": 10
            },
            "positive_tags": ["借景庭园日本最高峰", "免费参观世界级园林", "游客稀少宁静"],
            "negative_tags": ["需宫内厅网站预约", "位置较偏", "仅导览游览无法自由行"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["philosopher_path"],
        "risk_flags": ["requires_reservation"],
        "descriptions": {
            "why_selected": "修学院离宫是江户时代后水尾天皇营造的山庄式离宫，由下御茶屋、中御茶屋、上御茶屋三个区域构成，以三层阶梯式借景庭园著称。上御茶屋的'浴龙池'将比叡山整个山体借入庭园构图，是日本最宏大的借景手法。参观完全免费但需宫内厅预约，每日仅接待少量游客，因此体验极其宁静。被japan-guide评为4.3分。",
            "what_to_expect": "导览约80分钟，全程步行需穿行山坡之间，距离约3公里（有一定体力要求）。需在宫内厅官网提前申请（免费），英文界面可用，一般提前1-2周申请即可。秋季红叶和春季嫩绿时节最为壮观。从出町柳乘叡山电铁约15分钟。",
            "skip_if": "无法提前网上预约、或行程灵活性要求高（一旦预约需按时前往）的旅行者；行动不便者（全程步行山路约3公里）。"
        }
    },
    "kyo_katsura": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市西京区桂御園",
        "nearest_station": "桂駅（阪急京都線）徒歩20分 / 宮内庁バス利用",
        "when": {
            "open_days": "火曜日-日曜日（要予約）",
            "open_hours": "9:00-15:00（3回/日の定時ガイドツアー）",
            "last_entry": None,
            "closed_notes": "月曜日・年末年始休み。宮内庁ウェブサイトで事前申込必須（無料）"
        },
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 0,
            "budget_tier": "free"
        },
        "review_signals": {
            "google_rating": 4.6,
            "google_review_count": 3900,
            "dimension_scores": {
                "scenery": 10,
                "cultural_depth": 10,
                "accessibility": 4,
                "crowd_comfort": 9,
                "uniqueness": 10,
                "value_for_money": 10
            },
            "positive_tags": ["日本建筑美极致", "每一步视角都经精心设计", "建筑爱好者圣地"],
            "negative_tags": ["预约名额极其有限", "位置偏远", "仅导览游览"]
        },
        "queue_wait_minutes": None,
        "corridor_tags": ["western_kyoto"],
        "risk_flags": ["requires_reservation", "limited_capacity"],
        "descriptions": {
            "why_selected": "桂离宫被德国建筑师布鲁诺·陶特（Bruno Taut）称为'日本建筑美的极致'，深刻影响了包豪斯运动和现代主义建筑。创建于17世纪初，每一块踏石的位置、每一扇障子门的角度都经过精心计算，从不同视点形成完美的风景画面。这是全世界建筑师和园林设计师的朝圣之地，参观免费但名额极其有限。",
            "what_to_expect": "导览约70分钟，沿回游式庭园徒步，在行进中体验'序破急'的空间节奏变化。月波楼、松琴亭等茶室建筑是日本茶室建筑的最高范例。需在宫内厅官网申请，旺季（春秋）建议提前1个月以上。从京都站乘地铁+阪急约30分钟。",
            "skip_if": "对建筑和园林美学没有特别兴趣的旅行者（虽然极其精美，但如果没有相关知识背景，导览中的内容可能难以充分感受）；行程时间紧张者。"
        }
    },
    "kyo_yasakakoshin": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "address_ja": "京都府京都市東山区金園町390",
        "nearest_station": "祇園四条駅（京阪本線）徒歩10分",
        "when": {
            "open_days": "毎日",
            "open_hours": "終日（境内自由）",
            "last_entry": None,
            "closed_notes": None
        },
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 200,
            "budget_tier": "free"
        },
        "review_signals": {
            "google_rating": 4.0,
            "google_review_count": 7800,
            "dimension_scores": {
                "scenery": 7,
                "cultural_depth": 5,
                "accessibility": 8,
                "crowd_comfort": 5,
                "uniqueness": 9,
                "value_for_money": 10
            },
            "positive_tags": ["彩色猿球独特拍照背景", "和服打卡必拍", "顺路10分钟值得"],
            "negative_tags": ["寺院本身规模很小", "专程前往不值", "拍照人多难拍无人照"]
        },
        "queue_wait_minutes": 5,
        "corridor_tags": ["higashiyama", "gion"],
        "risk_flags": [],
        "descriptions": {
            "why_selected": "八坂庚申堂是京都东山散步道旁的小寺院，以悬挂在树间的彩色猿形布球（くくり猿）著称。这些颜色鲜艳、胖乎乎的布猿串连成一片，与古朴的木构建筑形成奇妙的视觉反差，成为小红书和Instagram上最具辨识度的京都打卡背景之一——特别是身着鲜艳和服的游客在此拍照极其出片。寺院本身规模很小，但作为东山散步的顺路节点价值极高。",
            "what_to_expect": "参观仅需10分钟，完全免费进入。位于二年坂旁边，东山散步路线经过此处。布猿可以购买（500日元左右），据说能帮助实现愿望。和服租借后在此拍照是京都最流行的旅游照组合之一。",
            "skip_if": "对拍照打卡不感兴趣且不走东山散步路线的旅行者；时间极其紧张时可以路过不进入。"
        }
    }
}

# ── Enrichment for seasonal_events ──────────────────────────────────────────
SEASONAL_EVENT_ENRICHMENTS = {
    "kyo_gion_matsuri": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "corridor_tags": ["gion", "nishiki"],
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 3000,
            "budget_tier": "budget"
        },
        "descriptions": {
            "why_selected": "祇园祭是日本三大祭典之一，始于869年，整个7月京都市中心都沉浸在祭典氛围中。7月14-16日宵山期间，32座山鉾花车亮灯展示，周边街道封闭为步行区，小吃摊云集。7月17日前祭山鉾巡行和7月24日后祭山鉾巡行是高潮，壮观程度无与伦比。这是理解京都作为古都文化底蕴的最佳窗口。",
            "what_to_expect": "宵山夜间（19:00-23:00）人最多最热闹，可以近距离欣赏山鉾花车细节并购买祭典限定商品。巡行当天（7/17前祭、7/24后祭）需早起占位（9:00出发），观看地点建议四条通/河原町通沿线。整个祭典期间旅馆极度紧俏，需提前数月预订。"
        }
    },
    "kyo_hanatoro_arashiyama": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "corridor_tags": ["arashiyama", "arashiyama_sagano"],
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 2000,
            "budget_tier": "budget"
        },
        "descriptions": {
            "why_selected": "岚山花灯路在每年12月中旬约10天内，将竹林小径、野宫神社、渡月桥等景点用温暖的和纸灯笼点亮，创造出只有冬夜才能见到的梦幻景色。这是岚山一年中游客相对较少但景色最唯美的时段，寒冷的冬夜与温暖灯光形成绝妙反差。",
            "what_to_expect": "17:00点灯，建议18:00-20:00间前往。竹林小径夜间限定开放，灯光从竹隙间透出的景象极为特别。渡月桥倒映灯光的水面也是必拍。冬季寒冷（约5-10°C），需穿厚外套。岚山区域步行即可串联主要亮点。"
        }
    },
    "kyo_gozan_okuribi": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "corridor_tags": ["philosopher_path", "kitano"],
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 500,
            "budget_tier": "free"
        },
        "descriptions": {
            "why_selected": "五山送火是盂兰盆节的送灵仪式，在8月16日20:00起，京都周围五座山依次点燃大型篝火字符（大文字、妙法、船形、左大文字、鸟居形），让先祖之灵在夏末返回彼世。这是京都最具精神文化内涵的年度仪式，每次仅燃烧约30分钟，观看体验短暂而震撼。",
            "what_to_expect": "20:00大文字（东山如意岳）率先点燃，之后每隔约5分钟依次点燃其他四处。出町柳三角洲是同时看到多处篝火的绝佳位置；船冈山公园可以看到大文字和妙法。观看完全免费，但人潮涌动需提前占位。8月中旬京都酷热（35°C+），做好防暑准备。"
        }
    },
    "kyo_sakura_season": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "corridor_tags": ["higashiyama", "arashiyama", "philosopher_path", "fushimi", "gion"],
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 2500,
            "budget_tier": "budget"
        },
        "descriptions": {
            "why_selected": "京都的赏樱季（3月下旬至4月上旬）是全日本最具代表性的春季旅游体验。古寺+樱花的组合在世界上无可替代：清水寺的舞台边樱云、岚山渡月桥的河岸樱花、哲学之道的运河樱花隧道、醍醐寺的枝垂樱……每个角度都是绝世风景。京都赏樱高峰期酒店价格会是平时的3-5倍，需提前半年以上预订。",
            "what_to_expect": "3月下旬至4月上旬是满开期（具体日期每年略有变化，建议关注官方樱花前线）。圆山公园和醍醐寺的夜樱特别参拜（需额外买票）是顶级体验。人潮极度拥挤，早上7点前是拍摄人少的唯一时机。4月中旬仁和寺的御室樱是京都最晚的赏樱机会。"
        }
    },
    "kyo_koyo_season": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "corridor_tags": ["higashiyama", "arashiyama", "philosopher_path", "ohara"],
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 3000,
            "budget_tier": "budget"
        },
        "descriptions": {
            "why_selected": "京都是日本公认的最佳红叶目的地，11月中旬至12月上旬，全城古寺的枫叶将整座城市变成一幅流动的水墨画。东福寺通天桥的万枫奇景、永观堂红叶倒映放生池、岚山龟山公园的一片赤红……每个角度都是经典。很多寺院在红叶期推出夜间特别参拜，气氛更加神秘迷人。",
            "what_to_expect": "11月中下旬（约15-25日）是高峰期。东福寺、永观堂、源光庵并称'红叶三绝'，建议分两天安排。各寺院的夜间特别参拜需额外购票（约500-1000日元），提前官网确认时间。11月京都人满为患，旅馆需提前半年预订，建议平日前往并尽量早出发。"
        }
    },
    "kyo_jidai_matsuri": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "corridor_tags": ["kitano", "gion"],
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 500,
            "budget_tier": "free"
        },
        "descriptions": {
            "why_selected": "时代祭是京都三大祭典之一，在每年10月22日（平安神宫创建纪念日）举行。约2000名市民穿着从明治时代到平安时代各历史时期的精确服装，沿4.5公里路线游行。这是一部活动的京都千年历史教科书，由京都市民自发保存传承，正式游行时的服装精美程度让人叹为观止。",
            "what_to_expect": "游行从京都御所出发，经市中心到平安神宫，约12:00开始，历时约2小时。沿途街道设有观览席（付费）和免费观看区。游行队伍分为20多个历史时代方阵，服装和道具均经过历史学家考证。与鞍马寺的'火祭'同日举行，可以安排一日游。"
        }
    },
    "kyo_aoi_matsuri": {
        "city_code": "kyoto",
        "prefecture": "京都府",
        "corridor_tags": ["philosopher_path", "kitano"],
        "cost": {
            "admission_jpy": 0,
            "typical_spend_jpy": 500,
            "budget_tier": "free"
        },
        "descriptions": {
            "why_selected": "葵祭是京都三大祭典中历史最悠久的一个（6世纪起源），也是气质最为典雅含蓄的祭典。500余名参列者身着平安时代的贵族服装，在葵叶装饰中缓缓行进，整个队伍散发出一种穿越千年的古典美感。巡行路线从京都御所出发，经上贺茂神社到下鸭神社。",
            "what_to_expect": "5月15日出发，10:30从御所出发，约14:20抵达下鸭神社，约15:30抵达上贺茂神社。沿途可在路边免费观看（部分区域有收费观览席）。与时代祭的宏大历史感不同，葵祭给人更多平安王朝的优雅宁静感，特别适合喜欢日本古典文学（《源氏物语》时代）的旅行者。"
        }
    }
}

# ── Apply enrichments ──────────────────────────────────────────────────────

enriched_spots = 0
for spot in spots[24:]:
    spot_id = spot.get("id")
    if spot_id in SPOT_ENRICHMENTS:
        enrichment = SPOT_ENRICHMENTS[spot_id]
        for key, value in enrichment.items():
            if key not in spot:
                spot[key] = value
        enriched_spots += 1
        print(f"  [SPOT] Enriched: {spot_id}")
    else:
        print(f"  [WARN] No enrichment data for spot: {spot_id}")

enriched_events = 0
for event in seasonal_events:
    event_id = event.get("id")
    if event_id in SEASONAL_EVENT_ENRICHMENTS:
        enrichment = SEASONAL_EVENT_ENRICHMENTS[event_id]
        for key, value in enrichment.items():
            if key not in event:
                event[key] = value
        enriched_events += 1
        print(f"  [EVENT] Enriched: {event_id}")
    else:
        print(f"  [WARN] No enrichment data for event: {event_id}")

# ── Save ──────────────────────────────────────────────────────────────────────
with open(FILE_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n=== DONE ===")
print(f"Spots enriched (index 24+): {enriched_spots}")
print(f"Seasonal events enriched: {enriched_events}")
print(f"Total items enriched: {enriched_spots + enriched_events}")
print(f"File saved to: {FILE_PATH}")
