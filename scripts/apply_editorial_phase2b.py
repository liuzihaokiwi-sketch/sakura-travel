"""
Apply editorial judgments directly to restaurants_ledger_phase2b.json.
No API calls — judgments are inline based on domain expertise.
"""

import json

LEDGER_PATH = "data/kansai_spots/phase2_ledger/restaurants_ledger_phase2b.json"

# fmt: off
JUDGMENTS = {
    # ── AKASHI (明石焼き x5) ─────────────────────────────────────────────────
    "あかし多幸": {
        "grade": "B",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "魚棚商店街老店，明石焼的定番体验地，数据源单一但符合旅游动线，顺路必尝。",
    },
    "いづも": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "明石焼代表店之一，macaro-ni推荐收录，无Tabelog评分支撑，作为旅游导览备选。",
    },
    "たこ磯": {
        "grade": "B",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "魚棚内老字号，鱼介高汤版明石焼口碑佳，在地人下厨也去的小店，代表本地正宗风味。",
    },
    "ふなまち": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "borderline候选，无评分数据支撑，仅tanosu来源，在明石焼激烈竞争中无明显优势。",
    },
    "よこ井": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "borderline候选，同类信息源重复收录，缺乏独立评分，作为兜底备选。",
    },

    # ── HYOGO / KOBE ─────────────────────────────────────────────────────────
    # 串炸
    "あさひ 尼崎本店": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.44偏低，组内底端，尼崎串炸无显著记录，borderline勉强收录。",
    },
    "あんしゃん亭": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.48，组内前1/3，苦楽園口小众串炸店，价格合理适合顺路午餐。",
    },
    "おでんと串カツ姫路のお店": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.46，在姬路串炸中属中段，关东煮+串炸组合有特色但数据支撑弱，borderline收录。",
    },
    "まこと": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "三宮串炸，Tabelog 3.53/base_score 4.25，口碑在组内后段，位置便利是主要优势。",
    },
    "やす桜": {
        "grade": "A",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "三宮串炸top10%，Tabelog 3.59在该赛道属高分，本地常客口碑稳定，神户串炸首选之一。",
    },
    "ステラ": {
        "grade": "A",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.58，兵库串炸后15%，大物站小众精选，base_score 4.625显示竞争力强。",
    },
    "フレンチ串揚げ・炭焼き BEIGNET ASHIYA": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "芦屋法式串炸，西洋+串炸融合有差异化，Tabelog 3.56在走廊内属中段，适合有猎奇心的游客。",
    },
    "串かつ あーぼん": {
        "grade": "S",
        "selection_tags": ["local_benchmark", "traveler_hot"],
        "one_line_editorial_note": "Tabelog 4.39全兵库串炸最高分之一，打出駅小店但名气已在食客圈广传，值得专程。",
    },
    "串かつ 船越": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "摩耶駅串炸，Tabelog 3.53/borderline，位置稍偏，口碑中等，顺路三宫可考虑。",
    },
    "舞子 串の助": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "西舞子駅串炸，Tabelog 3.51，组内前半段，明石一日游顺路选项，性价比合理。",
    },
    # 洋食（神户）
    "かくいにいくか": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.58但base_score仅2.5，borderline洋食，无显著口碑故事，勉强收录。",
    },
    "アングル": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.68，组内后25%，塚口的街坊洋食屋，午间套餐受上班族好评，顺路性价比好。",
    },
    "グリル末松": {
        "grade": "A",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "三宮洋食名店，Tabelog 3.69是神户洋食类top20%，半世纪老店，炸猪排和蛋包饭是招牌。",
    },
    "マルシェ": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.61，组内前1/3，花隈隐世洋食小店，性价比好但位置不在主动线。",
    },
    "伊藤グリル": {
        "grade": "B",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "元町老字号洋食，Tabelog 3.63/borderline，神户洋食文化代表之一，中国游客常提及。",
    },
    "欧風料理 もん": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "三宮欧风料理，Tabelog 3.69/borderline，在神户洋食密集区属中等，顺路可去。",
    },
    "洋食SAEKI": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "岩屋洋食，Tabelog 3.61/borderline，非主动线，与同赛道竞争店相比无突出理由。",
    },
    "洋食の朝日": {
        "grade": "A",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "Tabelog 3.72是神户洋食top10%，西元町老字号，熟客常年排队，牛肉炖饭是神户本地标志性菜品。",
    },
    "麗皮": {
        "grade": "A",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.94在兵库洋食类位居前5%，三宮高评分洋食，值得列为神户洋食首推。",
    },
    "神戸トルコライス": {
        "grade": "B",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "Tabelog 3.62，神户名物土耳其饭（炸猪排+拿坡里意面+咖喱米饭），游客必试代表菜之一。",
    },
    # 烧肉（兵库）
    "満月": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.74，兵库烧肉组内后30%，西元町居酒屋风烧肉，适合晚餐顺路一起。",
    },
    "炭焼塩ホルモン『あ』神戸酒場": {
        "grade": "A",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "Tabelog 3.89是兵库盐内脏赛道后10%，三宮盐烤内脏专门店，中国游客小红书高提及，晚餐首选。",
    },
    "焼肉 加茂川": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.64/borderline，兵库烧肉组内前20%，位置远离主动线，无专程理由。",
    },
    "焼肉bue": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.69/borderline，新神户烧肉，位置在新干线站附近，适合途经打卡。",
    },
    "焼肉ぜん": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "三宮烧肉，Tabelog 3.73/borderline，口碑中等，预算合理，适合顺路晚餐。",
    },
    "雄三郎": {
        "grade": "A",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "Tabelog 3.76，三宮烧肉组内后20%，本地高人气店，和牛内脏质优，值得专程的神户烧肉选择。",
    },
    "韓国料理 釜山": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.75，尼崎韩国烧肉，有在地韩国社区背书，食材接近本场，价格实惠。",
    },
    "肉ベース": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.64/borderline，小野市远离主要游览区，对一般观光客无专程价值。",
    },
    "肉料理 二月九日": {
        "grade": "A",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "Tabelog 3.92在兵库烧肉类后5%，加东市专程肉料理，食材精选，本地美食达人力荐。",
    },
    "肉料理　樹": {
        "grade": "A",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.78兵库烧肉后15%，西脇市肉料理精选，质量稳定，适合兵库广域周游时顺路。",
    },

    # ── KYOTO ────────────────────────────────────────────────────────────────
    # cafe / 喫茶
    "ELEPHANT FACTORY COFFEE": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "河原町隐秘咖啡馆，leafkyoto推荐但无Tabelog分数，borderline收录，无明确区分同类的理由。",
    },
    "イノダコーヒ 本店": {
        "grade": "A",
        "selection_tags": ["city_icon", "traveler_hot"],
        "one_line_editorial_note": "京都百年老铺，三条堺町本店是京都咖啡文化符号，中国游客必到打卡，代表京都独有的喫茶文化。",
    },
    "ひつじ": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.84，京都咖啡后16%，丸太町静谧咖啡馆，适合哲学之道周边散步后歇脚。",
    },
    "グラン・ヴァニーユ": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.78，祇园周边法式甜品咖啡馆，下午茶场景优，适合女性游客顺路消费。",
    },
    "ザ リビング パビリオン by アマン": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.79/borderline，Aman京都附属咖啡室，环境极佳但价格偏高，适合有预算的住客或专门打卡者。",
    },
    "パティスリー エス サロン": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.82/borderline，京都市役所周边法式甜品店，甜品水准高但位置偏离主动线。",
    },
    "パティスリー タンドレス": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.84，京都咖啡后16%，一乗寺法式甜品专门店，拉面街外的意外甜品打卡地。",
    },
    "大極殿本舗 六角店": {
        "grade": "B",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "Tabelog 3.77，祇园附近京都老铺甜品，名物冰室（水菓子）是京都季节限定，游客高度关注。",
    },
    "茶寮 宝泉": {
        "grade": "A",
        "selection_tags": ["local_benchmark", "traveler_hot"],
        "one_line_editorial_note": "Tabelog 3.87后5%，高出町柳名刹抹茶甜品，庭园清幽、金时氷美名远播，是京都和菓子体验的标杆。",
    },
    "鍵善良房 四条本店": {
        "grade": "A",
        "selection_tags": ["city_icon", "traveler_hot"],
        "one_line_editorial_note": "Tabelog 3.78，祇园名铺，葛切（くずきり）是京都代名词，中国游客必打卡，代表京都甘味文化。",
    },
    # 居酒屋
    "KANEGURA": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.65/borderline，四条居酒屋组内后段，在京都居酒屋激烈竞争中无突出理由专程。",
    },
    "たかつじ 佳粋": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.68/borderline，组内前半段但居酒屋赛道对游客吸引力弱，建议优先选其他品类。",
    },
    "オテルドゥオガワ": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.74，祇园居酒屋组内后21%，法语店名与京都风格搭出独特风情，创意料理+清酒适合晚餐。",
    },
    "祇園ろはん": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.74，祇园居酒屋后21%，京食材搭配自然酒，小圈子口碑不错，适合祇园夜游晚餐。",
    },
    "酒処 てらやま": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.69，祇园居酒屋后37%，清酒种类丰富，价格适中，适合游客小酌探访。",
    },
    # 拉面（京都）
    "あいつのラーメン かたぐるま": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "retty来源、无Tabelog评分，左京区拉面候选，哲学之道周边备选但无专程依据。",
    },
    "ますたに": {
        "grade": "A",
        "selection_tags": ["city_icon", "traveler_hot"],
        "one_line_editorial_note": "银阁寺附近老字号，京都背脂拉面发源地之一，Tabelog排行榜常客，是了解京都ラーメン文化的必去。",
    },
    "めん馬鹿一代": {
        "grade": "B",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "一乗寺拉面激战区名店，焰焰鬼火拉面表演性十足，游客记录度高，适合追求体验感的年轻旅客。",
    },
    "らぁ麺 とうひち": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.73，组内后36%，修学院站清汤细面，低调精品店风格，喜欢清淡拉面的游客适合。",
    },
    "ラーメン二郎 京都店": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "二郎系在京都有狂热粉丝，borderline收录，但大份量油腻风格对中国游客适配度一般，不做首推。",
    },
    "五行ラーメン": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "无Tabelog评分，ai_generated数据，京都拉面赛道信息不足，无法支撑推荐。",
    },
    "俺のラーメン あっぱれ屋": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.73/borderline，城阳市偏远，不在主要游览动线，对一般旅游行程无价值。",
    },
    "天下一品 総本店": {
        "grade": "B",
        "selection_tags": ["city_icon"],
        "one_line_editorial_note": "天下一品总本店在一乗寺，浓厚鸡骨汤是全国连锁起点，不少人专程来总店朝圣，有城市符号意义。",
    },
    "吟醸らーめん 久保田": {
        "grade": "A",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "Tabelog 3.74，组内后14%，五条站清淡系拉面精品，京都风格吟酿汤底，本地行家推崇。",
    },
    "麦の夜明け": {
        "grade": "A",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.74，下京区组内后14%，小麦风味清汤拉面颇受好评，距离京都站近，适合收尾一顿。",
    },
    # 荞麦
    "おがわ": {
        "grade": "A",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "Tabelog 3.72，京都荞麦后11%，北大路手打荞麦，精细的江户前风格，本地食客长年常客。",
    },
    "十五": {
        "grade": "A",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.71，京都荞麦后17%，左京区安静小店，主打粗粒荞麦，适合文人区氛围的午餐体验。",
    },
    "手打ち蕎麦 かね井": {
        "grade": "A",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.70，京都荞麦后22%，北区老字号，农村风味荞麦、手打麺条香气足，附近金阁寺顺路。",
    },
    "蕎麦 ろうじな": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.65/borderline，组内前半段，京都荞麦赛道竞争激烈，无突出于同赛道选手的理由。",
    },
    "蕎麦屋 にこら": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.65/borderline，与「蕎麦 ろうじな」同分，上京区位置偏，对游客便利性不足。",
    },
    # 日本料理（京都）
    "にくの匠 三芳": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 4.47是组内亮眼成绩，祇园牛肉料理专门店，borderline因高消费门槛，值得有预算者纳入。",
    },
    "凌霄": {
        "grade": "S",
        "selection_tags": ["city_icon", "local_benchmark"],
        "one_line_editorial_note": "米其林二星，东山区正宗怀石，炭火割烹精髓，京都最高水准日本料理之一，值得专程安排。",
    },
    "啐啄 つか本": {
        "grade": "A",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "Tabelog 4.55是祇园日本料理赛道高分，名厨主持的割烹，兼有怀石精神与主厨创意，值得专程。",
    },
    "富小路 やま岸": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 4.51/borderline，河原町怀石，组内后32%评分偏低，但高人气难预约，行程余量足时值得一试。",
    },
    "山荘 京大和": {
        "grade": "S",
        "selection_tags": ["city_icon", "local_benchmark"],
        "one_line_editorial_note": "米其林二星，东山区料亭，园林景观与料理并重，是京都最具代表性的高端奢华日料体验。",
    },
    "建仁寺 祇園 丸山": {
        "grade": "S",
        "selection_tags": ["city_icon", "local_benchmark"],
        "one_line_editorial_note": "米其林二星，祇园最老牌怀石料亭之一，建仁寺旁历史环境+精致料理，京都顶级餐饮地标。",
    },
    "炭火割烹 いふき": {
        "grade": "A",
        "selection_tags": [],
        "one_line_editorial_note": "米其林二星/borderline，东山炭火割烹，食材直火精髓，预约窗口小，有预算愿提前计划者首选。",
    },
    "祇園 にしかわ": {
        "grade": "A",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "米其林二星/borderline，祇园割烹名店，比凌霄更亲民但同样严谨，适合首次体验京都高端日料。",
    },
    "緒方": {
        "grade": "S",
        "selection_tags": ["city_icon", "local_benchmark"],
        "one_line_editorial_note": "Tabelog 4.57+米其林二星，组内后16%，祇园怀石顶峰，当代京料理最高水准代表，日本食评界反复点名。",
    },
    "道人": {
        "grade": "S",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "Tabelog 4.65是京都日本料理类最高分之一，三条京阪怀石，业界公认米其林级水准，为此特地访京值得。",
    },
    # 甜品（京都）
    "アッサンブラージュ カキモト": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.86，组内后29%，左京区创意和法融合甜品，适合散步到修学院附近时探访。",
    },
    "パティスリーエス": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.79/borderline，甜品组内前1/3但竞争甚激，无超出同类店的显著理由。",
    },
    "嘯月": {
        "grade": "A",
        "selection_tags": ["local_benchmark", "traveler_hot"],
        "one_line_editorial_note": "Tabelog 4.03，京都甜品后14%，北区完全预约制老铺，代表京都最精致上生和菓子体验，开始被中国游客发现。",
    },
    "川端道喜": {
        "grade": "A",
        "selection_tags": ["city_icon"],
        "one_line_editorial_note": "Tabelog 3.85，北区600年御用和菓子老铺，粽子（ちまき）历史意义超乎料理本身，京都文化必了解的存在。",
    },
    "御菓子司 塩芳軒": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.80/borderline，西陣百年老铺，季节上生菓子精致，适合上京区散步时顺道购入伴手礼。",
    },
    # 街头小食（京都錦）
    "のとよ": {
        "grade": "B",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "錦市場川魚专门店，鱼串新鲜可外带，是錦市场必逛食べ歩き节奏的核心体验之一。",
    },
    "のとよ(錦市場)": {
        "grade": "B",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "同上条目（錦市场同名分店），錦市场食べ歩き场景不可缺，游客打卡流量高。",
    },
    "カリカリ博士(錦市場)": {
        "grade": "B",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "錦市场章鱼烧名摊，街头小食即食体验，是游客錦市场路线的标配打卡点。",
    },
    "三木鶏卵(錦市場)": {
        "grade": "B",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "錦市场出汁卷鸡蛋专门摊，现卷热腾腾即食，是最能代表錦市场食べ歩き风情的小摊之一。",
    },
    "京のお肉処 弘 錦店": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "錦市场肉串摊，borderline收录，funliday来源数据弱，与其他錦市场摊位相比无独特卖点。",
    },

    # ── NARA ─────────────────────────────────────────────────────────────────
    # 荞麦
    "かおく": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.49/borderline，天理市荞麦，奈良荞麦组内底端，无专程理由。",
    },
    "そば処 風庵": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.46/borderline，十津川村深山荞麦，景致好但太偏，观光客几乎不会在行程内。",
    },
    "一如庵": {
        "grade": "A",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "Tabelog 3.75，奈良荞麦后6%，宇陀市手打荞麦，绑定室生寺文化游，食材自家种植，值得专程。",
    },
    "手打ちそば はやし": {
        "grade": "A",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.72，奈良荞麦后18%，廣陵町手打荞麦，静谧田园风貌，是奈良荞麦赛道高性价比选项。",
    },
    "蕎麦がき屋": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.57，桜井市荞麦团子专门，有趣的特色菜式，顺路三輪明神参拜时适合体验。",
    },
    # 乌冬
    "はるりん": {
        "grade": "A",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "Tabelog 3.56，奈良公园周边乌冬top16%，鹿走廊旁人气高，游客参观奈良公园后午餐首选。",
    },
    "与喜饂飩": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.52，奈良乌冬后32%，桜井市手打乌冬，配合長谷寺或三輪参拜路线顺路。",
    },
    "国境食堂": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.49/borderline，奈良公园内乌冬，位置便利是最大优势，游客最易路过进入。",
    },
    "大和本陣": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.46/borderline，五条市乌冬，评分低且偏远，对一般奈良游客无价值。",
    },
    "情熱うどん 荒木伝次郎": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.54，橿原市乌冬后26%，武将命名的个性小店，搭配飞鸟巡游路线顺路合适。",
    },
    "満天うどん カジバノバカヂカラ": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.47/borderline，大和郡山乌冬，评分在组内后段，无突出优势。",
    },
    "重乃井 奈良店": {
        "grade": "A",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "Tabelog 3.56，奈良公园乌冬后16%，有连锁背书+位置优势，是游客在鹿苑午餐的高性价比选择。",
    },
    "釜揚げうどん 鈴庵": {
        "grade": "A",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "Tabelog 3.70，奈良乌冬top5%，北葛城郡釜揚げ专门店，精致汤底受本地人高度认可，远胜同类。",
    },
    "釜粋": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.45/borderline，奈良公园乌冬评分偏低，同区有更好选择如はるりん。",
    },
    "麺喰": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.55，奈良公园乌冬后21%，亲子面条体验可选，价格实惠，顺路可一试。",
    },

    # ── OSAKA ─────────────────────────────────────────────────────────────────
    # 咖喱
    "BOTANI:CURRY 梅田店": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.80，梅田咖喱后31%，植物性咖喱理念契合健康潮流，对素食游客有额外吸引力。",
    },
    "Ghar": {
        "grade": "A",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "Tabelog 3.92是大阪咖喱组内顶层12%，肥后桥印度风味咖喱，食材精选、辛辣层次感被专业食评高评。",
    },
    "Mカッセ": {
        "grade": "A",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.82，大阪咖喱后19%，粉浜隐世欧风咖喱，汤底浓醇与众不同，是本地达人收藏级别的店。",
    },
    "SOMA": {
        "grade": "B",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "中津香料咖喱，osakalucci推荐，大阪スパイスカレー热潮代表之一，游客人气高。",
    },
    "curry bar nidomi": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.81，谷町四丁目香料咖喱后25%，大阪咖喱热代表小店，价格合理环境轻松。",
    },
    "シバケン": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.75/borderline，野江内代咖喱，位置偏离，与梅田/难波主动线差距大，不值专程。",
    },
    "スパイス料理ナッラマナム": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.78/borderline，堺筋本町印度香料菜，偏商务区，游客动线触及率低。",
    },
    "橋本屋": {
        "grade": "A",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "Tabelog 4.09，大阪咖喱后6%，長堀橋欧风咖喱百年老铺，酱料自制、口感厚重，业界反复点名。",
    },
    "渡邊咖喱": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "borderline，北新地欧风咖喱无Tabelog评分，仅haraheri来源，相比同赛道有Tabelog支撑的店竞争力弱。",
    },
    "白銀亭 本店": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "borderline，肥後橋欧风咖喱无Tabelog评分，ai_generated数据，推荐依据不足。",
    },
    # 乌冬（大阪）
    "Udon Kyutaro": {
        "grade": "A",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "Tabelog 3.80，本町乌冬后15%，出汁讲究、面条手工，外国游客友好，是大阪乌冬赛道高人气目的地。",
    },
    "手打ちうどん 上を向いて": {
        "grade": "A",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "Tabelog 3.82，大阪乌冬后10%，守口市手打乌冬，本地圈子高口碑，在该组内评分靠前。",
    },
    "手造りうどん 楽々": {
        "grade": "A",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "Tabelog 3.92，大阪乌冬后5%，郡市手打乌冬，汤底浓厚自然，在地人推崇，是该类别罕见4分以上水准。",
    },
    # 拉面（大阪）
    "いかれたヌードル フィッシュトンズ": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.74，大阪拉面前5%/borderline，西大橋鱼介风味拉面，有风格区分度，值得关注。",
    },
    "らーめん弥七": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.76，中津拉面后41%，梅田周边常规选项，距主动线近，顺路可安排。",
    },
    "らーめん颯人": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.76，南森町拉面后41%，价格合理，游览天神桥筋商店街时顺路午餐佳选。",
    },
    "ラーメン人生JET": {
        "grade": "A",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "Tabelog 3.77，大阪拉面后12%，福島浓厚系拉面精品，熟客持续回头，是梅田周边值得专程的店。",
    },
    "中華そば うえまち": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.76，谷町六丁目中华清汤拉面后41%，传统正统风味，顺路可去。",
    },
    "洛二神": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.74/borderline，天神橋筋六丁目鸡白汤，梅田周边备选，borderline因竞争激烈。",
    },
    "手打ち麺 やす田": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.75，新大阪周边，手打面条口感差异化，适合新干线出发前或抵达后轻松一顿。",
    },
    "烈志笑魚油 麺香房 三く": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.75/borderline，新福島鱼介拉面，在大阪同赛道中无突出优势。",
    },
    "燃えよ麺助": {
        "grade": "A",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "Tabelog 3.77，福島拉面后12%，担担风浓厚系，SNS爆红级高颜值碗面，梅田拉面首推之一。",
    },
    "麺や而今 大東本店": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.75/borderline，大東市鸡白汤，位置远离市中心，一般旅游行程触及不到。",
    },
    # 大阪烧（お好み焼き）
    "お好み たまちゃん viva": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.66，心斋桥大阪烧后29%，位置便利，餐厅氛围热闹，适合游客难波区晚餐。",
    },
    "お好み焼 オモニ 本店": {
        "grade": "B",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "Tabelog 3.65，鶴橋朝鲜系大阪烧，在地韩国食材市场旁，代表大阪朝鲜文化影响的特色菜系。",
    },
    "お好み焼 千草": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.65，天満大阪烧后47%，老牌大众化，适合游天神筋商店街时顺路午餐。",
    },
    "お好み焼き ちとせ": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.66，弁天町大阪烧后29%，本地住宅区街坊店，食材扎实，性价比好。",
    },
    "お好み焼き 味乃家": {
        "grade": "B",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "难波老字号大阪烧，tabelog matome收录，游客高流量区域必吃标配，中国游客常写入行程。",
    },
    "お好み焼き 福太郎": {
        "grade": "B",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "难波大阪烧知名店，tabelog收录/borderline，是中国旅游攻略中难波大阪烧的常见推荐。",
    },
    "お好み焼き 美津の": {
        "grade": "A",
        "selection_tags": ["city_icon", "traveler_hot"],
        "one_line_editorial_note": "道頓堀老字号，大阪烧界最知名的门店之一，中国游客必打卡，代表大阪烧的城市名片级存在。",
    },
    "たぴおか食堂": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.65/borderline，寺田町大阪烧，位置非主动线，与难波/心斋桥选项相比缺乏选择理由。",
    },
    "御好焼 月之家": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "无地址区域信息+ai_generated数据，borderline收录但推荐依据极弱，不列入首推。",
    },
    "鉄板焼き Oribe": {
        "grade": "A",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.69，心斋桥大阪烧后6%，主厨铁板烧概念将大阪烧精致化，是大阪烧升级版体验。",
    },
    # 荞麦（大阪）
    "そば切り 荒凡夫": {
        "grade": "A",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "Tabelog 3.71，大阪荞麦后25%，难波桥附近精品荞麦，刀工细腻，本地荞麦圈有口碑。",
    },
    "そば切り文目堂": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.70/borderline，谷町六丁目荞麦，与荒凡夫相近但分数略低，无明显差异化优势。",
    },
    "なにわ翁": {
        "grade": "C",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.68/borderline，难波桥荞麦后45%，在竞争激烈的大阪荞麦赛道中无亮点。",
    },
    "まき埜": {
        "grade": "A",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 3.74，大阪荞麦后15%，福島精品荞麦，汤底讲究，值得在梅田周边游览时特地安排。",
    },
    "蕎麦 たかま": {
        "grade": "A",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "Tabelog 3.75，大阪荞麦后5%，天満橋附近顶级手打荞麦，产地直送食材，是大阪荞麦首推之选。",
    },
    # 章鱼烧（大阪）
    "たこ家道頓堀くくる 本店": {
        "grade": "A",
        "selection_tags": ["city_icon", "traveler_hot"],
        "one_line_editorial_note": "道頓堀知名章鱼烧，品牌化运营且选址核心地标，中国游客必打卡，是大阪章鱼烧赛道首选之一。",
    },
    "たこ焼十八番": {
        "grade": "B",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "道頓堀章鱼烧连锁，JAL推荐，位置好、出品稳定，适合难波游览顺路购入。",
    },
    "たこ焼道楽 わなか 千日前本店": {
        "grade": "A",
        "selection_tags": ["city_icon", "traveler_hot"],
        "one_line_editorial_note": "千日前本店，外皮酥脆是招牌，haraheri收录，在大阪章鱼烧圈内高知名度，游客行程标配。",
    },
    "わなか(たこ焼道楽)": {
        "grade": "B",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "わなか分店/borderline，道楽品牌延伸，地理覆盖难波区，方便在主游区购入，与本店差异不大。",
    },
    "わなか(黒門市場)": {
        "grade": "B",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "黑门市场分店/borderline，嵌入黑门市场购物动线，是游客顺路打卡章鱼烧的便利选择。",
    },
    # 串炸（大阪）
    "てんぐ": {
        "grade": "B",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "新世界（动物园前）串炸，retty收录，新世界名物体验不可缺，游客到新世界必吃串炸。",
    },
    "串かつ じゃんじゃん": {
        "grade": "A",
        "selection_tags": ["city_icon", "traveler_hot"],
        "one_line_editorial_note": "新世界串炸老字号，osakalucci推荐，通天阁下方位置是大阪串炸文化的标志性体验地点。",
    },
    "串かつ じゃんじゃん 新世界本店": {
        "grade": "A",
        "selection_tags": ["city_icon", "traveler_hot"],
        "one_line_editorial_note": "与上条目为同一品牌不同入口，新世界本店是大阪串炸地标，游客必体验，城市符号级存在。",
    },
    "串かつ 横綱": {
        "grade": "B",
        "selection_tags": ["traveler_hot"],
        "one_line_editorial_note": "新世界串炸连锁/borderline，知名度略逊于だるま，但连锁规模意味着候位时间短，实用备选。",
    },
    "元祖串かつ だるま 新世界総本店": {
        "grade": "A",
        "selection_tags": ["city_icon", "traveler_hot"],
        "one_line_editorial_note": "大阪串炸第一品牌总本店，osakalucci收录，通天阁下方地标店，是外国游客大阪饮食必到清单。",
    },
    # 烧肉（大阪）
    "つねちゃん": {
        "grade": "A",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "Tabelog 4.17，大阪烧肉后11%，堺市内脏烧肉専門店，价格实惠+高评分，是大阪烧肉赛道性价比顶选。",
    },
    "京洛焼肉 ぽめ": {
        "grade": "A",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 4.09，大阪烧肉后16%，長堀橋京风高品质烧肉，性价比与食材质量均优，值得专程晚餐。",
    },
    "生ホルモン処 おさむちゃん": {
        "grade": "A",
        "selection_tags": ["local_benchmark"],
        "one_line_editorial_note": "Tabelog 4.21，大阪烧肉后5%，堺市生内脏专门店，食材极鲜/价格亲民，大阪烧肉达人首推。",
    },
    "瀧川": {
        "grade": "B",
        "selection_tags": [],
        "one_line_editorial_note": "Tabelog 4.05/borderline，难波烧肉后21%，价格偏高但食材质量稳定，适合大阪最后一顿晚餐。",
    },
}
# fmt: on


def main():
    with open(LEDGER_PATH, encoding="utf-8") as f:
        data = json.load(f)

    updated = 0
    not_found = []

    for item in data:
        if item.get("selection_status") not in ("selected", "borderline"):
            continue
        name = item.get("name_ja", "")
        j = JUDGMENTS.get(name)
        if j is None:
            not_found.append(name)
            continue
        item["grade"] = j["grade"]
        item["selection_tags"] = j["selection_tags"]
        item["one_line_editorial_note"] = j["one_line_editorial_note"]
        item["opus_reviewed"] = True
        updated += 1

    with open(LEDGER_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Updated: {updated}")
    if not_found:
        print(f"NOT FOUND ({len(not_found)}):")
        for n in not_found:
            print(f"  {n!r}")


if __name__ == "__main__":
    main()
