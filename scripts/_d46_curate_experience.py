"""精修体验型 6 组关键代表酒店。

覆盖 6 组：
- 老铺旅馆: 炭屋（已加俵屋/柊家）+ 丸福楼
- 温泉旅馆: 兵卫向阳阁（有马）+ 西村屋本馆（城崎）
- 设计精品: Hotel She / OMO5 / Ace Hotel / Hotel Kanra
- 宿坊: 智积院已精·高野山宿坊批量精
"""
from __future__ import annotations
import io, json, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
HOTELS = REPO / "japan/kansai/hotels/data/hotels__kansai.json"

CURATIONS = {
    "kyo_shijo_kawaramachi_sumiya": {
        "id": "kyo_nakagyo_sumiya",
        "city": "京都",
        "area": "nakagyo",
        "near_attractions": [{"entity_id": "kyo_pontocho", "walk_min": 4}],
        "tier": "top",
        "type": "experience",
        "price_cny_per_night": [3200, 5500],
        "depth": "full",
        "season_months": None,
        "note": {
            "店名": "炭屋旅馆（炭屋旅館 / Sumiya Ryokan）",
            "简介": "京都老铺三件套之一·跟俵屋/柊家齐名·150 年历史。19 间客房一泊二食含京懐石+茶道仪式·走「茶之心」路线。住客可参加女将主持的早朝茶事。比俵屋亲民·体验更聚焦。",
            "亮点": ["老铺旅馆", "150 年历史", "茶道体验", "京懐石", "京都老铺三件套"],
            "地址": "京都市中京区麸屋町通三条下ル白壁町 431（地铁烏丸御池站步行 7 分·京都市役所前 5 分）",
            "房型": "本馆和室 / 离れ·全部一泊二食",
            "含早": "含·京风朝食",
            "价格": "一泊二食 ¥55,000-¥90,000/人（约 ¥2,800-¥4,500 RMB·樱花/红叶 ¥100,000+）",
            "预约": "电话/邮件直接·提前 2 个月·英文 OK",
            "到店提醒": "Check-in 15:00 / Check-out 11:00·可申请茶道体验",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://www.sumiyaryokan.com/", "https://www.relais-chateaux.com/us/japan/sumiya-kyoto"],
        "最后核实": "2026-04-26",
    },
    "kyo_shijo_kawaramachi_h338": {
        "id": "kyo_nakagyo_marufukuro",
        "city": "京都",
        "area": "nakagyo",
        "near_attractions": [{"entity_id": "kyo_pontocho", "walk_min": 5}],
        "tier": "top",
        "type": "experience",
        "price_cny_per_night": [4000, 8000],
        "depth": "full",
        "season_months": None,
        "note": {
            "店名": "丸福楼（Marufukuro / 丸福樓）",
            "简介": "任天堂创业地（1889 年山内房治郎花札工房）2022 年改建·18 间客房+任天堂收藏品。任系粉丝必住·安藤忠雄+真田大设计。MICHELIN One Key。但不是只为粉丝——和洋融合的精致住宿体验也是顶级的。",
            "亮点": ["设计精品", "任天堂创业地", "MICHELIN One Key", "安藤忠雄设计", "粉丝朝圣"],
            "地址": "京都市下京区鍵屋町 342（京阪清水五条站步行 5 分）",
            "房型": "豪华和室 / 套房",
            "含早": "含·料亭「夢果」朝食",
            "价格": "平季 ¥4,000-5,500 / 旺季 ¥6,500-8,000+",
            "预约": "官网·提前 60 天",
            "到店提醒": "Check-in 15:00 / Check-out 12:00·任天堂收藏室住客限定",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://marufukuro.com/", "https://hotels.ctrip.com/hotels/55966174.html"],
        "最后核实": "2026-04-26",
    },
    "arm_arima_onsen_h266": {
        "id": "arm_arima_hyoe_koyokaku",
        "city": "神户",
        "area": "arima",
        "near_attractions": [{"entity_id": "arm_arima_onsen", "walk_min": 2}, {"entity_id": "arm_kin_no_yu", "walk_min": 5}],
        "tier": "luxury",
        "type": "experience",
        "price_cny_per_night": [1500, 3500],
        "depth": "full",
        "season_months": None,
        "note": {
            "店名": "兵卫向阳阁（兵衛向陽閣 / Hyoe Koyokaku）",
            "简介": "有马温泉历史最久的旅馆之一·700 年历史·丰臣秀吉曾住。150 间客房·全部一泊二食·金泉露天风吕是有马温泉地标。有马的「住宿即体验」代表。家庭/老人客群最爱（无障碍设施完善）。",
            "亮点": ["温泉旅馆", "700 年历史", "金泉露天", "有马代表", "丰臣秀吉宿"],
            "地址": "神戸市北区有馬町 1904（神鉄有馬温泉站步行 7 分·神户三宫站电铁 30 分）",
            "房型": "和室 / 和洋室·全部一泊二食",
            "含早": "含·会席朝食",
            "价格": "一泊二食 ¥30,000-¥70,000/人（约 ¥1,500-¥3,500 RMB·新年/盆 ¥100,000+）",
            "预约": "官网 / 一休 / 楽天·提前 2 个月",
            "到店提醒": "Check-in 14:00 / Check-out 11:00·门口接神户三宫站班车（预约制）",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://www.hyoe.co.jp/", "https://hotels.ctrip.com/hotels/675125.html"],
        "最后核实": "2026-04-26",
    },
    "kns_kinosaki_onsen_h276": {
        "id": "kns_kinosaki_nishimuraya_honkan",
        "city": "城崎",
        "area": "kinosaki",
        "near_attractions": [{"entity_id": "kns_kinosaki", "walk_min": 3}],
        "tier": "top",
        "type": "experience",
        "price_cny_per_night": [3500, 7000],
        "depth": "full",
        "season_months": [11, 12, 1, 2, 3],  # 蟹季冬季最佳
        "depth": "full",
        "note": {
            "店名": "西村屋本馆（西村屋本館 / Nishimuraya Honkan）",
            "简介": "城崎温泉创业 160 年的老铺·34 间客房·全部一泊二食。冬季松叶蟹会席（11月-3月）是城崎最有名的·MICHELIN Two Keys。城崎温泉外汤巡也是这家附属体验。",
            "亮点": ["温泉旅馆", "MICHELIN Two Keys", "松叶蟹会席", "160 年老铺", "城崎代表"],
            "地址": "兵庫県豊岡市城崎町湯島 469（JR 城崎温泉站步行 5 分）",
            "房型": "本馆和室 / 平田館·全部一泊二食",
            "含早": "含",
            "价格": "一泊二食冬蟹季 ¥80,000-¥150,000/人（约 ¥4,000-¥7,500 RMB）·非蟹季 ¥45,000-",
            "预约": "官网 / 一休·蟹季提前 6 个月",
            "到店提醒": "Check-in 15:00 / Check-out 10:00·浴衣外汤巡含·蟹季限活蟹",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://www.nishimuraya.ne.jp/honkan/", "https://www.relais-chateaux.com/us/japan/nishimuraya-kinosaki"],
        "最后核实": "2026-04-26",
    },
    "kyo_nijo_central_ace_hotel_kyoto": {
        "id": "kyo_nakagyo_ace_hotel_kyoto",
        "city": "京都",
        "area": "nakagyo",
        "near_attractions": [{"entity_id": "kyo_nijo_castle", "walk_min": 5}],
        "tier": "luxury",
        "type": "experience",
        "price_cny_per_night": [1800, 3500],
        "depth": "full",
        "season_months": None,
        "note": {
            "店名": "艾斯酒店京都（Ace Hotel Kyoto / エースホテル京都）",
            "简介": "2020 年开业·新风馆·隈研吾设计+Commune Design 联手·213 间客房。设计酒店爱好者必住·全京都最潮酷酒店。地铁烏丸御池站直结·楼下含蓝瓶咖啡/Stumptown。MICHELIN One Key。",
            "亮点": ["设计精品", "MICHELIN One Key", "隈研吾设计", "Ace Hotel 全球品牌", "新风馆"],
            "地址": "京都市中京区車屋町 245-2（地铁烏丸御池站直结）",
            "房型": "豪华 / 行政 / 套房·全部 30+ 平米",
            "含早": "可选·楼下蓝瓶咖啡",
            "价格": "淡季 ¥1,200 / 平季 ¥1,800-2,400 / 旺季 ¥3,000-3,500",
            "预约": "官网 / 携程",
            "到店提醒": "Check-in 15:00 / Check-out 12:00·楼下店开到深夜",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://acehotel.com/kyoto/", "https://hotels.ctrip.com/hotels/22515018.html"],
        "最后核实": "2026-04-26",
    },
    "kyo_kyoto_station_hotel_kanra_kyoto": {
        "id": "kyo_kyoto_station_hotel_kanra_kyoto",
        "city": "京都",
        "area": "kyoto_station",
        "near_attractions": [{"entity_id": "kyo_railway_museum", "walk_min": 10}],
        "tier": "luxury",
        "type": "experience",
        "price_cny_per_night": [1500, 3000],
        "depth": "full",
        "season_months": None,
        "note": {
            "店名": "Hotel Kanra Kyoto（ホテルカンラ京都）",
            "简介": "京都站七条·39 间客房+町家融合设计·全部带桧木浴缸（30 平米起）。京町家爱好者+设计酒店爱好者交集。性价比比柏悦/丽思高·体验上有同等心思。MICHELIN One Key。",
            "亮点": ["町家", "MICHELIN One Key", "桧木浴缸", "全房 30+ 平米", "京都站近"],
            "地址": "京都市下京区烏丸通六条下ル北町 190（地铁五条站步行 5 分）",
            "房型": "豪华和室 / 套房·全部带桧木浴缸",
            "含早": "可选·和食/西食",
            "价格": "淡季 ¥1,000 / 平季 ¥1,500-2,000 / 旺季 ¥2,500-3,000",
            "预约": "官网 / 携程",
            "到店提醒": "Check-in 15:00 / Check-out 12:00",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://www.uds-hotels.com/kanra/", "https://hotels.ctrip.com/hotels/2199704.html"],
        "最后核实": "2026-04-26",
    },
    "kyo_kyoto_station_hotel_she_kyoto": {
        "id": "kyo_kyoto_station_hotel_she_kyoto",
        "city": "京都",
        "area": "kyoto_station",
        "near_attractions": [{"entity_id": "kyo_railway_museum", "walk_min": 12}],
        "tier": "quality",
        "type": "experience",
        "price_cny_per_night": [800, 1800],
        "depth": "full",
        "season_months": None,
        "note": {
            "店名": "Hotel She Kyoto（ホテル シー 京都）",
            "简介": "2017 年开业·京都站九条·小型设计型酒店·30 间客房。每间客房有 Vintage 唱机+黑胶碟·设计酒店爱好者+音乐爱好者必去。性价比超高·年轻情侣/学生最爱。",
            "亮点": ["设计精品", "Vintage 唱机", "性价比", "音乐爱好者"],
            "地址": "京都市南区東九条東岩本町 31（地铁九条站步行 5 分）",
            "房型": "标准 / 套房",
            "含早": "可选·楼下 Cafe",
            "价格": "淡季 ¥500 / 平季 ¥800-1,200 / 旺季 ¥1,500-1,800",
            "预约": "官网 / 携程",
            "到店提醒": "Check-in 15:00 / Check-out 11:00",
        },
        "可信度": "single_source",
        "数据来源": ["https://hotelsher.com/kyoto/"],
        "最后核实": "2026-04-26",
    },
    "kyo_shijo_kawaramachi_omo5_by": {
        "id": "kyo_nakagyo_omo5_kyoto_sanjo",
        "city": "京都",
        "area": "nakagyo",
        "near_attractions": [{"entity_id": "kyo_pontocho", "walk_min": 5}],
        "tier": "quality",
        "type": "experience",
        "price_cny_per_night": [800, 1800],
        "depth": "full",
        "season_months": None,
        "note": {
            "店名": "OMO5 京都三条 by 星野度假村（OMO5 京都三条 by 星野リゾート）",
            "简介": "2022 年开业·星野 OMO 系列京都三条店·115 间客房·走「都市观光」概念。OMO Ranger（御乐人员）带住客深度逛三条商店街是签名体验。性价比+体验双优·设计型连锁的最佳示范。",
            "亮点": ["设计精品", "OMO Ranger 体验", "性价比", "三条商店街"],
            "地址": "京都市中京区三条通木屋町東入ル中島町 96（地铁三条京阪站步行 1 分）",
            "房型": "标准 / 上层套房",
            "含早": "可选",
            "价格": "淡季 ¥600 / 平季 ¥800-1,200 / 旺季 ¥1,500-1,800",
            "预约": "官网 / 携程 / 星野预约",
            "到店提醒": "Check-in 15:00 / Check-out 11:00·OMO Ranger 早晚团活动免费",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://hoshinoresorts.com/en/hotels/omo5kyotosanjo/", "https://hotels.ctrip.com/hotels/91891948.html"],
        "最后核实": "2026-04-26",
    },
}


def main():
    with open(HOTELS, encoding="utf-8") as f:
        pool = json.load(f)

    pool_by_id = {h["id"]: h for h in pool}

    updated = 0
    new_ids = {}

    for key, curation in CURATIONS.items():
        if key not in pool_by_id:
            print(f"⚠ 未找到 {key}")
            continue
        for k, v in curation.items():
            pool_by_id[key][k] = v
        new_id = curation.get("id", key)
        if new_id != key:
            new_ids[key] = new_id
        updated += 1

    for old_id, new_id in new_ids.items():
        h = pool_by_id[old_id]
        h["id"] = new_id

    with open(HOTELS, "w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)

    print(f"✓ 体验型精修 {updated} 家")


if __name__ == "__main__":
    main()
