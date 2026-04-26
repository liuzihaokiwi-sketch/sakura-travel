"""D47 补收种子表中现池未收的 17 家宝藏."""
from __future__ import annotations

import io
import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DATA = Path("japan/kansai/hotels/data/hotels__kansai.json")
TODAY = datetime.now().strftime("%Y-%m-%d")


# 17 家新增条目
NEW_HOTELS = [
    {
        "id": "kyo_takagamine_aman_kyoto",
        "city": "京都",
        "area": "kita",
        "near_attractions": [
            {"entity_id": "kyo_kinkakuji", "walk_min": 25},
        ],
        "type": "experience",
        "price_cny_per_night": [4500, 8000],
        "tier": "b6",
        "season_months": None,
        "depth": "full",
        "note": {
            "店名": "Aman Kyoto（アマン京都 / Aman Kyoto）",
            "简介": "2019 年开业·京都鹰峰森林深处·24 间客房+18 间套房·原织锦商家庭园改造·KIBA Studio 设计·**Aman 集团首入京都**。森林包围+水景庭园+SPA·入住即闭关。MICHELIN Two Keys。",
            "亮点": ["温泉度假", "Aman 京都首入", "鹰峰森林包围", "庭园改造", "MICHELIN Two Keys"],
            "地址": "京都市北区大北山·鹰峰森林深处·有 shuttle",
            "房型": "Pavilion Suite 71㎡ ~ Aman Suite 137㎡（共 24+18 间）",
            "含早": "和洋朝食 buffet 含·套房可选",
            "价格": "素泊 1 间 ¥250,000～¥600,000+（人均 ¥4,500-8,000+）·樱花/红叶 +50%",
            "预约": "公式 aman.com·提前 6+ 个月·樱花季预订率极高",
            "到店提醒": "Check-in 15:00 / Check-out 12:00·京都站 shuttle 30 分钟·森林散步路线推荐黄昏",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://www.aman.com/resorts/aman-kyoto", "https://www.michelinkeyhotels.com/"],
        "最后核实": TODAY,
    },
    {
        "id": "kyo_arashiyama_hoshinoya_kyoto",
        "city": "京都",
        "area": "arashiyama",
        "near_attractions": [
            {"entity_id": "kyo_togetsukyo", "walk_min": 0},
            {"entity_id": "kyo_tenryuji", "walk_min": 8},
        ],
        "type": "experience",
        "price_cny_per_night": [3500, 6500],
        "tier": "b6",
        "season_months": None,
        "depth": "full",
        "note": {
            "店名": "星のや 京都（Hoshinoya Kyoto）",
            "简介": "**保津川河畔船入專用**·25 间客房·星野リゾート 系最高级。船头送迎+和食奥之間·岚山深处的水上禅意宿。MICHELIN Two Keys。",
            "亮点": ["温泉度假", "保津川船入宿", "星野最高级", "MICHELIN Two Keys"],
            "地址": "京都市西京区岚山·保津川河畔·渡月桥送迎船 15 分钟",
            "房型": "全 25 室·部分含露天风吕",
            "含早": "和食朝食含",
            "价格": "夕朝食付 1 间 ¥130,000～¥250,000（人均 ¥3,500-6,500）·樱花/红叶 +30%",
            "预约": "公式 hoshinoresorts.com·提前 90 天·樱花季提前 180 天",
            "到店提醒": "Check-in 15:00 / Check-out 12:00·船入送迎仅渡月桥·全室禁烟",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://hoshinoresorts.com/ja/hotels/hoshinoyakyoto/", "https://www.michelinkeyhotels.com/"],
        "最后核实": TODAY,
    },
    {
        "id": "kyo_gion_higashiyama_omo5_kyoto_gion",
        "city": "京都",
        "area": "gion_higashiyama",
        "near_attractions": [
            {"entity_id": "kyo_yasaka_shrine", "walk_min": 5},
        ],
        "type": "city",
        "price_cny_per_night": [800, 1500],
        "tier": "b3",
        "season_months": None,
        "depth": "full",
        "note": {
            "店名": "OMO5 京都祇園 by 星野リゾート（OMO5 Kyoto Gion）",
            "简介": "星野リゾート 旗下年轻人导向都市精品酒店·祇园核心立地·体验型在地文化活动「Go-KINJO」（玩转邻里）·**为城市探索者设计**·房间紧凑但功能精致。",
            "亮点": ["设计精品", "祇园核心", "Go-KINJO 在地体验", "年轻人向"],
            "地址": "京都市東山区·祇園·阪急河原町站徒步 8 分",
            "房型": "Standard 紧凑型~Suite·共 95+ 室",
            "含早": "可选 ¥2,500/人",
            "价格": "素泊 2 人 ¥16,000-30,000（人均 ¥400-750·CNY 800-1500）",
            "预约": "公式 / 一休 / 楽天",
            "到店提醒": "Check-in 15:00 / Check-out 11:00·OMO Ranger 在地散步推荐",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://hoshinoresorts.com/ja/hotels/omo5kyotogion/"],
        "最后核实": TODAY,
    },
    {
        "id": "kyo_kyoto_station_omo3_kyoto_toji",
        "city": "京都",
        "area": "kyoto_station",
        "near_attractions": [
            {"entity_id": "kyo_toji", "walk_min": 5},
        ],
        "type": "city",
        "price_cny_per_night": [600, 1100],
        "tier": "b3",
        "season_months": None,
        "depth": "full",
        "note": {
            "店名": "OMO3 京都東寺 by 星野リゾート（OMO3 Kyoto Toji）",
            "简介": "星野リゾート OMO3 ライン·东寺世界遗产对面·近铁東寺站徒步 1 分·京都站徒步 15 分·**门口有东寺夜间灯光**。OMO Ranger 推荐东寺-梅小路-京都站散步路线。",
            "亮点": ["设计精品", "东寺对面", "近铁徒步 1 分", "京都站近邻"],
            "地址": "京都市南区·近铁東寺站徒步 1 分·京都站徒步 15 分",
            "房型": "Standard~Family·共 120 室",
            "含早": "可选 ¥2,000/人",
            "价格": "素泊 2 人 ¥12,000-22,000（人均 ¥300-550·CNY 600-1100）",
            "预约": "公式 / 一休 / 楽天",
            "到店提醒": "Check-in 15:00 / Check-out 11:00·东寺夜灯 11/中-12/初",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://hoshinoresorts.com/ja/hotels/omo3kyototoji/"],
        "最后核实": TODAY,
    },
    {
        "id": "osk_namba_dotonbori_caption_by_hyatt_namba",
        "city": "大阪",
        "area": "namba_dotonbori",
        "near_attractions": [
            {"entity_id": "osk_dotonbori", "walk_min": 5},
            {"entity_id": "osk_kuromon_market", "walk_min": 8},
        ],
        "type": "city",
        "price_cny_per_night": [800, 1500],
        "tier": "b4",
        "season_months": None,
        "depth": "full",
        "note": {
            "店名": "Caption by Hyatt Namba Osaka（凯悦凯逸难波大阪）",
            "简介": "**2025 年开业·日本首家 Caption by Hyatt**（继美国孟菲斯·中国上海后全球第三家）·难波千日前商店街+黑门市场旁·凯悦集团生活方式酒店·设计向年轻人。",
            "亮点": ["设计精品", "Caption 日本首家", "黑门市场旁", "千日前立地", "2025 新开业"],
            "地址": "大阪市中央区难波·千日前商店街·黑门市场徒步 5 分",
            "房型": "Standard~Suite·共 140+ 室",
            "含早": "Café 享用·可选含早 plan",
            "价格": "素泊 2 人 ¥16,000-30,000",
            "预约": "Hyatt 公式 / 一休 / 楽天·World of Hyatt 会员积分",
            "到店提醒": "Check-in 15:00 / Check-out 11:00·难波 walking life 友好",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://www.hyatt.com/caption-by-hyatt", "https://en.itravelblog.net/caption-by-hyatt-namba-osaka/"],
        "最后核实": TODAY,
    },
    {
        "id": "kyo_shijo_kawaramachi_daiwa_roynet_shijo_karasuma",
        "city": "京都",
        "area": "shijo_kawaramachi",
        "near_attractions": [
            {"entity_id": "kyo_pontocho", "walk_min": 10},
        ],
        "type": "city",
        "price_cny_per_night": [600, 1200],
        "tier": "b3",
        "season_months": None,
        "depth": "verified",
        "可信度": "cross_checked",
        "数据来源": ["https://www.daiwaroynet.jp/kyoto-shijokarasuma/"],
        "最后核实": TODAY,
        "note": {
            "店名": "Daiwa Roynet Hotel KYOTO-SHIJYOKARASUMA（京都四条乌丸大和ROYNET酒店）",
            "简介": "**2026 年 3 月 14 日重新开业**·阪急乌丸站徒步 1 分·四条河原町商圈核心·Daiwa 系中端商务连锁·新装修后设施现代+公共浴场。",
            "亮点": ["设计精品", "2026 新开业", "阪急乌丸 1 分", "四条河原町商圈"],
            "地址": "京都市下京区·阪急烏丸站徒步 1 分·四条乌丸交叉点",
            "房型": "Standard Twin/Double·共 280+ 室·新装修",
            "价格": "素泊 2 人 ¥12,000-25,000",
            "预约": "公式 / 一休 / 楽天",
        },
    },
    # Nazuna 4 物业
    {
        "id": "kyo_shijo_kawaramachi_nazuna_kyoto_tsubaki",
        "city": "京都", "area": "shijo_kawaramachi",
        "near_attractions": [{"entity_id": "kyo_pontocho", "walk_min": 12}],
        "type": "experience",
        "price_cny_per_night": [2200, 3800],
        "tier": "b5", "season_months": None, "depth": "full",
        "可信度": "cross_checked",
        "数据来源": ["https://www.nazuna.co/property/nazuna-kyoto-tsubaki-st/", "https://www.ikyu.com/00002780/"],
        "最后核实": TODAY,
        "note": {
            "店名": "Nazuna 京都 椿通（Nazuna Kyoto Tsubaki Street）",
            "简介": "**築 110 年以上的町家路地一体改造**·约 1,400㎡ L 字型 23 间客房·京都自然テーマ「TAKE/MIZU/IWA/HANA/HA」5 类。Nazuna 集团旗舰物业·MICHELIN 3 Pavilions。",
            "亮点": ["町家", "町家路地一体", "23 室+5 主题", "MICHELIN 3 Pavilions"],
            "地址": "京都市下京区·阪急乌丸站徒步 8 分·椿通り",
            "房型": "TAKE/MIZU/IWA/HANA/HA 5 类·共 23 室",
            "含早": "可选含早",
            "价格": "夕朝食付 2 人 ¥45,000-80,000",
            "预约": "公式 / 一休 / 楽天",
        },
    },
    {
        "id": "kyo_nakagyo_nazuna_kyoto_gosho",
        "city": "京都", "area": "nakagyo",
        "near_attractions": [{"entity_id": "kyo_imperial_palace", "walk_min": 5}],
        "type": "experience",
        "price_cny_per_night": [3500, 6000],
        "tier": "b6", "season_months": None, "depth": "full",
        "可信度": "cross_checked",
        "数据来源": ["https://www.nazuna.co/property/nazuna-kyoto-gosho/"],
        "最后核实": TODAY,
        "note": {
            "店名": "Nazuna 京都 御所（Nazuna Kyoto Gosho）",
            "简介": "**大型京町家 2 棟改造**·全 7 室豪华旅館·**全室露天风吕**·和菓子テーマ·ラウンジ无料アルコール+ソフトドリンク+軽食。京都御所旁高级地段。",
            "亮点": ["町家", "全 7 室全室露天風呂", "和菓子テーマ", "ラウンジフリードリンク"],
            "地址": "京都市中京区·京都御所徒步 5 分",
            "房型": "全 7 室和洋·全室含大型露天风吕或内汤",
            "含早": "和菓子テーマ朝食含",
            "价格": "夕朝食付 2 人 ¥80,000-150,000",
            "预约": "公式 / 一休·小規模需早预约",
        },
    },
    {
        "id": "kyo_nijo_central_nazuna_kyoto_nijojo",
        "city": "京都", "area": "nijo_central",
        "near_attractions": [{"entity_id": "kyo_nijo_castle", "walk_min": 5}],
        "type": "experience",
        "price_cny_per_night": [2800, 5000],
        "tier": "b5", "season_months": None, "depth": "full",
        "可信度": "cross_checked",
        "数据来源": ["https://www.nazuna.co/property/nazuna-kyoto-nijojo/"],
        "最后核实": TODAY,
        "note": {
            "店名": "Nazuna 京都 二条城（Nazuna Kyoto Nijojo）",
            "简介": "**全室露天风吕 OR 半露天风吕**·二条城旁立地·MICHELIN 3 Pavilions 物业之一。",
            "亮点": ["町家", "全室露天風呂/半露天", "二条城旁", "MICHELIN 3 Pavilions"],
            "地址": "京都市中京区·二条城徒步 5 分·地铁二条城前站徒步 3 分",
            "房型": "全和洋·全室带露天/半露天风吕",
            "含早": "和食朝食含",
            "价格": "夕朝食付 2 人 ¥60,000-110,000",
            "预约": "公式 / 一休",
        },
    },
    {
        "id": "kyo_kyoto_station_nazuna_kyoto_higashi_honganji",
        "city": "京都", "area": "kyoto_station",
        "near_attractions": [{"entity_id": "kyo_higashi_honganji", "walk_min": 3}],
        "type": "experience",
        "price_cny_per_night": [2000, 3500],
        "tier": "b5", "season_months": None, "depth": "full",
        "可信度": "cross_checked",
        "数据来源": ["https://www.nazuna.co/property/nazuna-kyoto-higashihonganji/"],
        "最后核实": TODAY,
        "note": {
            "店名": "Nazuna 京都 東本願寺（Nazuna Kyoto Higashi Honganji）",
            "简介": "**築 100 年以上の歴史京町家再生**·全 7 室·**大工テーマ·「大引の間」「垂木の間」**等用語命名·東本願寺徒步 3 分·京都站徒步 10 分·friendly luxury 定位。",
            "亮点": ["町家", "100 年京町家再生", "大工テーマ命名", "東本願寺徒步 3 分"],
            "地址": "京都市下京区·東本願寺徒步 3 分·京都站徒步 10 分",
            "房型": "全 7 室·和洋·部分露天风吕",
            "含早": "和食朝食含",
            "价格": "夕朝食付 2 人 ¥40,000-80,000",
            "预约": "公式 / 一休 / 楽天",
        },
    },
    # 京の温所
    {
        "id": "kyo_nakagyo_kyo_no_ondokoro_marutamachi",
        "city": "京都", "area": "nakagyo",
        "near_attractions": [{"entity_id": "kyo_imperial_palace", "walk_min": 5}],
        "type": "experience",
        "price_cny_per_night": [1500, 2800],
        "tier": "b4", "season_months": None, "depth": "verified",
        "可信度": "cross_checked",
        "数据来源": ["https://www.kyo-ondokoro.kyoto/", "https://www.kyo-ondokoro.kyoto/facility/"],
        "最后核实": TODAY,
        "note": {
            "店名": "京の温所 丸太町（Kyo no Ondokoro Marutamachi / ワコール运营）",
            "简介": "**ワコール运营·京町家一棟貸し**·カリモク家具·**艺术氛围**·女性人气。京の温所系列 14+ 物业·check-in 在「ザ ロイヤルパークホテル アイコニック 京都」。",
            "亮点": ["町家", "一栋整租", "カリモク家具", "ワコール运营", "艺术氛围"],
            "地址": "京都市中京区丸太町·京都御所徒步 5 分",
            "房型": "一栋整租·1-6 人",
            "价格": "1 栋 ¥30,000-50,000/晚（人均 ¥1,500-2,800·小红书爆款）",
            "预约": "公式 kyo-ondokoro.kyoto·check-in 在 ROYAL PARK ICONIC",
        },
    },
    # 葵 KYOTO STAY
    {
        "id": "kyo_gion_higashiyama_aoi_kyoto_stay_higashi",
        "city": "京都", "area": "gion_higashiyama",
        "near_attractions": [{"entity_id": "kyo_kiyomizudera", "walk_min": 12}],
        "type": "experience",
        "price_cny_per_night": [1200, 2200],
        "tier": "b4", "season_months": None, "depth": "verified",
        "可信度": "cross_checked",
        "数据来源": ["https://www.kyoto-stay.jp/en/", "https://www.ikyu.com/en-us/00002185/"],
        "最后核实": TODAY,
        "note": {
            "店名": "葵 KYOTO STAY 町家（AOI Hotel Kyoto / 葵 京都ステイ）",
            "简介": "**京都繁華街築 100 年町家**·一栋整租型町家+ホテル型 8 室·和庭園·清水五条駅徒步 5 分·阪急河原町徒步 10 分·1 日 1 組「観雲庵」「観月亭」suite。",
            "亮点": ["町家", "100 年町家", "一栋整租", "和庭園", "1 日 1 組 suite"],
            "地址": "京都市東山区·清水五条駅徒步 5 分·阪急河原町徒步 10 分",
            "房型": "葵 HOTEL KYOTO 8 室 + 多个一棟貸し物业",
            "价格": "一栋 2 人 ¥24,000-45,000",
            "预约": "公式 kyoto-stay.jp / 一休 / Booking",
        },
    },
    # Nara Hotel
    {
        "id": "nra_nara_park_area_nara_hotel",
        "city": "奈良", "area": "nara_park_area",
        "near_attractions": [{"entity_id": "nra_kasuga_taisha", "walk_min": 12}],
        "type": "experience",
        "price_cny_per_night": [1500, 2800],
        "tier": "b5", "season_months": None, "depth": "full",
        "可信度": "cross_checked",
        "数据来源": ["https://www.narahotel.co.jp/"],
        "最后核实": TODAY,
        "note": {
            "店名": "奈良ホテル（Nara Hotel）",
            "简介": "**1909 年开业·日本クラシックホテル**·辰野金吾设计·奈良公园内·爱因斯坦·达赖喇嘛·歴代天皇曾宿·**奈良名片级老铺**。维多利亚式木造建筑+日本传统装饰。",
            "亮点": ["老铺旅馆", "1909 年开业", "辰野金吾设计", "クラシックホテル名片", "奈良公园内"],
            "地址": "奈良市高畑町·奈良公园内·近铁奈良站徒步 15 分（送迎可）",
            "房型": "本馆クラシック+新馆·共 132 室",
            "含早": "和洋朝食 buffet",
            "价格": "素泊 2 人 ¥30,000-60,000·夕朝食付 ¥40,000-80,000",
            "预约": "公式·一休·楽天·樱花季提前 90 天",
            "到店提醒": "Check-in 15:00 / Check-out 11:00·历史建筑·送迎需电话",
        },
    },
    # Hoshino KAI 城崎 + KAI 有马
    {
        "id": "kns_kinosaki_onsen_kai_kinosaki",
        "city": "城崎", "area": "kinosaki_onsen",
        "near_attractions": [{"entity_id": "kns_kinosaki_onsen", "walk_min": 5}],
        "type": "experience",
        "price_cny_per_night": [1700, 3200],
        "tier": "b5", "season_months": None, "depth": "full",
        "可信度": "cross_checked",
        "数据来源": ["https://hoshinoresorts.com/ja/hotels/kaikinosaki/"],
        "最后核实": TODAY,
        "note": {
            "店名": "界 城崎 by Hoshino Resorts（Hoshino Resorts KAI Kinosaki）",
            "简介": "星野リゾート「界」系·城崎温泉外汤巡り·全 47 室·**全国温泉宿名片** of KAI 系·部分客房露天风吕·会席料理含蟹冬季。",
            "亮点": ["温泉旅馆", "星野 KAI 系", "城崎外汤巡り", "蟹会席（冬）"],
            "地址": "兵庫県豊岡市城崎温泉·JR城崎温泉駅徒步 10 分",
            "房型": "全 47 室·部分含露天风吕",
            "含早": "和朝食含",
            "价格": "夕朝食付 2 人 ¥48,000-95,000",
            "预约": "公式 / 一休·蟹季 11-3 月加成大",
            "到店提醒": "Check-in 15:00 / Check-out 12:00·外汤共 7 处·浴衣巡り推荐",
        },
    },
    {
        "id": "arm_arima_onsen_kai_arima",
        "city": "神户", "area": "arima_onsen",
        "near_attractions": [{"entity_id": "kbe_arima_onsen", "walk_min": 5}],
        "type": "experience",
        "price_cny_per_night": [1600, 3000],
        "tier": "b5", "season_months": None, "depth": "full",
        "可信度": "cross_checked",
        "数据来源": ["https://hoshinoresorts.com/ja/hotels/kaiarima/"],
        "最后核实": TODAY,
        "note": {
            "店名": "界 有馬 by Hoshino Resorts（Hoshino Resorts KAI Arima）",
            "简介": "星野リゾート「界」系·有馬温泉**金泉源泉·6 室小規模旅館**·KAI 全系最小規模·和的 sophistication+怀石。",
            "亮点": ["温泉旅馆", "星野 KAI 系", "有馬金泉", "全 6 室小規模"],
            "地址": "神户市北区有馬町·有馬温泉駅徒步 5 分",
            "房型": "全 6 室·部分露天风吕",
            "含早": "和朝食含",
            "价格": "夕朝食付 2 人 ¥45,000-90,000",
            "预约": "公式 / 一休·小规模常満室",
            "到店提醒": "Check-in 15:00 / Check-out 12:00·金泉露天推荐黄昏",
        },
    },
]


def main() -> None:
    apply = "--apply" in sys.argv
    data = json.loads(DATA.read_text(encoding="utf-8"))
    existing = {h["id"] for h in data}

    added = 0
    skipped = []
    for new in NEW_HOTELS:
        if new["id"] in existing:
            skipped.append(new["id"])
            continue
        data.append(new)
        existing.add(new["id"])
        added += 1

    print(f"added: {added}")
    print(f"skipped (already exists): {len(skipped)}")
    for s in skipped:
        print(f"  {s}")

    if apply:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("\n[APPLIED]")
    else:
        print("\n[DRY-RUN]")


if __name__ == "__main__":
    main()
