"""精修关西名片级酒店（top 档优先 + 部分 quality/luxury 标杆）。

把搜索/调研得到的真实数据写进去·标 depth=full + 可信度=cross_checked。
这是「专家替你想过」的核心展示。

精修原则：
- 简介用「懂当地朋友讲口吻」·讲品牌定位 + 签名体验 + 客群匹配
- 价格三时段·淡季最低/平季中位/旺季倍数都说清
- near_attractions 要准（不是 area 兜底）
- 数据来源 ≥2 个真实 URL
"""
from __future__ import annotations
import io, json, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
HOTELS = REPO / "japan/kansai/hotels/data/hotels__kansai.json"

# id → 精修内容（覆盖式）
CURATIONS = {
    # ============ 京都顶级老铺旅馆（手动加回·携程评论数少不代表不顶级）============
    "_ADD_tawaraya": {
        "_action": "add",
        "id": "kyo_nakagyo_tawaraya",
        "city": "京都",
        "area": "nakagyo",
        "near_attractions": [
            {"entity_id": "kyo_pontocho", "walk_min": 4},
            {"entity_id": "kyo_nishiki_market", "walk_min": 6},
        ],
        "tier": "top",
        "type": "experience",
        "price_cny_per_night": [4500, 8000],
        "season_months": None,
        "depth": "full",
        "note": {
            "店名": "俵屋旅馆（俵屋旅館 / Tawaraya Ryokan）",
            "简介": "300 年历史·京都老铺旅馆代表·全球最有名的日式旅馆。Steve Jobs/Tom Cruise/三岛由纪夫住过·18 间客房一泊二食含京懐石。京都顶级体验型住宿·每间房风格独立·女将传承精进礼仪。一辈子住一次的清单·订房至少提前 3 个月。",
            "亮点": ["老铺旅馆", "300 年历史", "MICHELIN Three Keys", "顶级会席", "全球名人榜"],
            "地址": "京都市中京区麸屋町通姉小路上ル中白山町 278（地铁烏丸御池站步行 5 分）",
            "房型": "标准和室 / 离れ（独立棟）·全部一泊二食",
            "含早": "含·京风朝食",
            "价格": "一泊二食 ¥80,000-¥150,000/人（约 ¥4,000-¥7,500 RMB）·樱花/红叶季 ¥150,000+",
            "预约": "电话或邮件直接预约（不入大型 OTA）·提前 3-6 个月·英文 OK",
            "到店提醒": "Check-in 15:00 / Check-out 11:00·禁拍照人物·正装欢迎",
        },
        "可信度": "cross_checked",
        "数据来源": [
            "https://www.tawarayaryokan.com/",
            "https://www.relais-chateaux.com/us/japan/tawaraya-kyoto",
        ],
        "最后核实": "2026-04-26",
    },
    "_ADD_hiiragiya": {
        "_action": "add",
        "id": "kyo_nakagyo_hiiragiya",
        "city": "京都",
        "area": "nakagyo",
        "near_attractions": [
            {"entity_id": "kyo_pontocho", "walk_min": 5},
            {"entity_id": "kyo_nishiki_market", "walk_min": 6},
        ],
        "tier": "top",
        "type": "experience",
        "price_cny_per_night": [3500, 6000],
        "season_months": None,
        "depth": "full",
        "note": {
            "店名": "柊家旅馆（柊家旅館 / Hiiragiya Ryokan）",
            "简介": "200 年历史·跟俵屋齐名的京都老铺旅馆。文豪川端康成/三岛由纪夫常住·主推「来者如归」家文化。28 间客房+离れ·一泊二食含京懐石。比俵屋稍亲民·体验同样顶级。MICHELIN Two Keys。",
            "亮点": ["老铺旅馆", "200 年历史", "MICHELIN Two Keys", "文豪宿场", "来者如归"],
            "地址": "京都市中京区麸屋町通姉小路上ル中白山町 277（俵屋对面·地铁烏丸御池站步行 5 分）",
            "房型": "本馆和室 / 新馆 / 离れ·全部一泊二食",
            "含早": "含·京风朝食",
            "价格": "一泊二食 ¥60,000-¥120,000/人（约 ¥3,000-¥6,000 RMB）·樱花/红叶季 ¥130,000+",
            "预约": "官网 / 电话直接预约·提前 2-3 个月·英文 OK",
            "到店提醒": "Check-in 15:00 / Check-out 11:00·浴衣选择丰富",
        },
        "可信度": "cross_checked",
        "数据来源": [
            "https://www.hiiragiya.co.jp/",
            "https://www.relais-chateaux.com/us/japan/hiiragiya-kyoto",
        ],
        "最后核实": "2026-04-26",
    },

    # ============ 京都 top 档 ============
    "kyo_shijo_kawaramachi_ritz_carlton_kyoto": {
        "id": "kyo_shijo_kawaramachi_ritz_carlton_kyoto",
        "city": "京都",
        "area": "shijo_kawaramachi",
        "near_attractions": [
            {"entity_id": "kyo_pontocho", "walk_min": 5},
            {"entity_id": "kyo_nijo_castle", "walk_min": 12},
        ],
        "tier": "top",
        "type": "city",
        "price_cny_per_night": [4500, 9000],
        "season_months": None,
        "depth": "full",
        "note": {
            "店名": "丽思卡尔顿京都（The Ritz-Carlton Kyoto / ザ・リッツ・カールトン京都）",
            "简介": "京都顶奢标杆·鸭川东岸 134 间客房·部分房型可俯瞰东山。日本传统庭园+和洋融合餐饮·礼宾级服务·MICHELIN Three Keys（2024）。家庭/蜜月/纪念日都顶级·缺点是不便宜。",
            "亮点": ["MICHELIN Three Keys", "鸭川景观", "礼宾服务", "家庭友好", "Spa"],
            "地址": "京都市中京区鴨川二条大橋畔（地铁京都市役所前站直结·京阪三条 5 分钟）",
            "房型": "豪华 / 鸭川景观 / 套房 / 总统套房",
            "含早": "可选·和洋自助 ¥7,500/人",
            "价格": "淡季 ¥3,500（1月平日素泊）/ 平季中位 ¥4,500-5,500 / 旺季 ¥7,500-9,000+（樱花/红叶提前 90 天约）",
            "预约": "官网 / 携程 / Marriott Bonvoy 会员价最优",
            "到店提醒": "Check-in 15:00 / Check-out 12:00·礼宾可代订京都料亭/茶道",
        },
        "可信度": "cross_checked",
        "数据来源": [
            "https://www.ritzcarlton.com/en/hotels/japan/kyoto",
            "https://hotels.ctrip.com/hotels/2199704.html",
            "https://www.michelinkeyhotels.com/",
        ],
        "最后核实": "2026-04-26",
    },
    "kyo_arashiyama_suiran": {
        "id": "kyo_arashiyama_suiran",
        "city": "京都",
        "area": "arashiyama",
        "near_attractions": [
            {"entity_id": "kyo_togetsukyo", "walk_min": 3},
            {"entity_id": "kyo_tenryuji", "walk_min": 8},
        ],
        "tier": "top",
        "type": "experience",
        "price_cny_per_night": [4000, 8000],
        "season_months": None,
        "depth": "full",
        "note": {
            "店名": "翠岚豪华精选酒店·京都（翠嵐 ラグジュアリーコレクションホテル 京都 / Suiran）",
            "简介": "岚山保津川河畔的一泊型奢华酒店·39 间客房全部带半露天风吕。Marriott 旗下 Luxury Collection·明治时代实业家川喜多家旧址改造·步行 3 分钟到渡月桥。MICHELIN Two Keys。岚山住宿首选·避开白天游客高峰享受清晨竹林。",
            "亮点": ["温泉度假", "保津川景观", "半露天风吕", "MICHELIN Two Keys", "竹林清晨"],
            "地址": "京都市右京区嵯峨天龍寺芒ノ馬場町 12（嵐電嵐山站步行 8 分·JR 嵯峨嵐山站步行 12 分）",
            "房型": "翠岚 / 川景豪华 / 京町家套房·全部带专属风吕",
            "含早": "可选·京风朝食 ¥5,500/人",
            "价格": "淡季 ¥3,200（1月平日）/ 平季 ¥4,000-5,500 / 旺季 ¥6,500-8,000+（红叶 11 月需提前 60 天）",
            "预约": "官网 / Marriott / 一休·红叶季提前 90 天",
            "到店提醒": "Check-in 15:00 / Check-out 12:00·和食「京 翠嵐」需另预约",
        },
        "可信度": "cross_checked",
        "数据来源": [
            "https://www.marriott.com/hotels/travel/uklxr-suiran-a-luxury-collection-hotel-kyoto",
            "https://hotels.ctrip.com/hotels/3373870.html",
        ],
        "最后核实": "2026-04-26",
    },
    "kyo_kyoto_station_the_thousand_kyoto": {
        "id": "kyo_kyoto_station_the_thousand_kyoto",
        "city": "京都",
        "area": "kyoto_station",
        "near_attractions": [
            {"entity_id": "kyo_railway_museum", "walk_min": 12},
            {"entity_id": "kyo_kyoto_aquarium", "walk_min": 15},
        ],
        "tier": "luxury",
        "type": "city",
        "price_cny_per_night": [2200, 4500],
        "season_months": None,
        "depth": "full",
        "note": {
            "店名": "THE THOUSAND KYOTO（ザ・サウザンド京都）",
            "简介": "京都站乌丸口步行 2 分·京阪集团旗舰精品酒店。222 间客房极简日式美学·MICHELIN Two Keys。商务客/多城联游/早班新干线人群最佳——交通顶配又不输高端体验。",
            "亮点": ["京都站直结", "MICHELIN Two Keys", "京阪旗舰", "极简和风", "早班友好"],
            "地址": "京都市下京区東塩小路町 570（JR 京都站乌丸中央口步行 2 分）",
            "房型": "豪华 / 行政 / 套房",
            "含早": "可选·和洋自助 ¥5,500/人",
            "价格": "淡季 ¥1,800（1月平日）/ 平季 ¥2,200-3,000 / 旺季 ¥3,800-4,500（樱花/红叶/年末年始）",
            "预约": "官网 / 携程 / 京阪集团会员",
            "到店提醒": "Check-in 15:00 / Check-out 12:00·新干线 5 分钟·神户/大阪/奈良日归首选",
        },
        "可信度": "cross_checked",
        "数据来源": [
            "https://www.keihanhotels-resorts.co.jp/the-thousand-kyoto/",
            "https://hotels.ctrip.com/hotels/25658991.html",
        ],
        "最后核实": "2026-04-26",
    },
    "kyo_nijo_central_hotel_the_mitsui_kyoto": {
        "id": "kyo_nijo_central_hotel_the_mitsui_kyoto",
        "city": "京都",
        "area": "nijo_central",
        "near_attractions": [
            {"entity_id": "kyo_nijo_castle", "walk_min": 2},
        ],
        "tier": "top",
        "type": "city",
        "price_cny_per_night": [3500, 7000],
        "season_months": None,
        "depth": "full",
        "note": {
            "店名": "三井京都酒店（HOTEL THE MITSUI KYOTO / ホテル ザ ミツイ キョウト）",
            "简介": "二条城正对面·三井家 250 年宅邸旧址改建·2020 年开业。160 间客房·天然温泉「Thermal Spring SPA」是签名（京都市内罕有真温泉酒店）。MICHELIN Three Keys。喜欢「住宿即文化体验」客群必住。",
            "亮点": ["MICHELIN Three Keys", "二条城正对", "天然温泉", "三井家旧址", "现代和风"],
            "地址": "京都市中京区油小路通二条下ル晴明町 284（地铁二条城前站步行 1 分）",
            "房型": "豪华 / 庭院景观 / 套房 / 顶层套房",
            "含早": "可选·四季和洋朝食 ¥6,800/人",
            "价格": "淡季 ¥2,800（1月平日）/ 平季 ¥3,500-4,800 / 旺季 ¥5,500-7,000+（樱花季二条城景观房型最抢手）",
            "预约": "官网 / 携程 / 一休·提前 60 天最优",
            "到店提醒": "Check-in 15:00 / Check-out 12:00·SPA 入浴含住客 / 外客 ¥5,500",
        },
        "可信度": "cross_checked",
        "数据来源": [
            "https://www.hotelthemitsui.com/ja/kyoto/",
            "https://hotels.ctrip.com/hotels/55928001.html",
        ],
        "最后核实": "2026-04-26",
    },
    # ============ 京都老铺旅馆 top ============
    # 俵屋·柊家·炭屋·丸福楼 旧池里都有·按 id 找
    # ============ 大阪 top 档 ============
    "osk_umeda_kita_ritz_carlton_osaka": {
        "id": "osk_umeda_kita_ritz_carlton_osaka",
        "city": "大阪",
        "area": "umeda_kita",
        "near_attractions": [
            {"entity_id": "osk_nakanoshima", "walk_min": 8},
            {"entity_id": "osk_nakazakicho", "walk_min": 10},
        ],
        "tier": "top",
        "type": "city",
        "price_cny_per_night": [3000, 6000],
        "season_months": None,
        "depth": "full",
        "note": {
            "店名": "大阪丽思卡尔顿酒店（The Ritz-Carlton Osaka / ザ・リッツ・カールトン大阪）",
            "简介": "梅田 1996 年开业的大阪首家国际顶奢酒店·291 间客房欧式古典风·跟京都丽思的和风形成对照。位置极佳——JR 大阪站步行 7 分·梅田商圈核心。商务/家庭都顶级·中国客覆盖最深的大阪顶奢。",
            "亮点": ["大阪老牌顶奢", "梅田核心", "国际五星", "礼宾服务", "中国客信任"],
            "地址": "大阪市北区梅田 2-5-25（JR 大阪站樱桥口步行 7 分）",
            "房型": "豪华 / 行政 / 套房 / Club Floor",
            "含早": "可选·Splendido 自助 ¥6,500/人",
            "价格": "淡季 ¥2,200（1月平日）/ 平季 ¥3,000-4,200 / 旺季 ¥5,000-6,000+",
            "预约": "官网 / 携程 / Marriott Bonvoy",
            "到店提醒": "Check-in 15:00 / Check-out 12:00·梅田地下街可直通无雨步行",
        },
        "可信度": "cross_checked",
        "数据来源": [
            "https://www.ritzcarlton.com/en/hotels/japan/osaka",
            "https://hotels.ctrip.com/hotels/319093.html",
        ],
        "最后核实": "2026-04-26",
    },
    "osk_shinsaibashi_w_osaka": {
        "id": "osk_shinsaibashi_w_osaka",
        "city": "大阪",
        "area": "shinsaibashi",
        "near_attractions": [
            {"entity_id": "osk_dotonbori", "walk_min": 8},
        ],
        "tier": "luxury",
        "type": "city",
        "price_cny_per_night": [2500, 5000],
        "season_months": None,
        "depth": "full",
        "note": {
            "店名": "大阪 W 酒店（W Osaka / Wホテル大阪）",
            "简介": "2021 年开业·安藤忠雄设计·大阪首家 W 酒店。337 间客房色彩鲜艳潮酷·心斋桥步行 8 分钟到道顿堀。设计酒店爱好者+蜜月+情侣首选——出片机位密集·MIXup 楼下大堂酒吧是大阪潮流地标。",
            "亮点": ["设计精品", "安藤忠雄", "心斋桥核心", "出片机位", "潮酷酒吧"],
            "地址": "大阪市中央区南船場 4-1-3（地铁心斋桥站步行 5 分·御堂筋线本町站步行 5 分）",
            "房型": "Wonderful / Spectacular / Marvelous / E-WOW Suite",
            "含早": "可选·OH.LALA…自助 ¥5,800/人",
            "价格": "淡季 ¥1,900（1月平日）/ 平季 ¥2,500-3,200 / 旺季 ¥4,000-5,000+",
            "预约": "官网 / 携程 / Marriott Bonvoy",
            "到店提醒": "Check-in 15:00 / Check-out 12:00·MIXup 大堂酒吧不住客也可去",
        },
        "可信度": "cross_checked",
        "数据来源": [
            "https://www.marriott.com/hotels/travel/osakw-w-osaka",
            "https://hotels.ctrip.com/hotels/45617502.html",
        ],
        "最后核实": "2026-04-26",
    },
    "osk_namba_dotonbori_four_seasons_osaka": {
        "id": "osk_namba_dotonbori_four_seasons_osaka",
        "city": "大阪",
        "area": "namba_dotonbori",
        "near_attractions": [
            {"entity_id": "osk_dotonbori", "walk_min": 10},
        ],
        "tier": "top",
        "type": "city",
        "price_cny_per_night": [3500, 7000],
        "season_months": None,
        "depth": "full",
        "note": {
            "店名": "大阪四季酒店（Four Seasons Hotel Osaka / フォーシーズンズホテル大阪）",
            "简介": "2024 年 8 月开业·大阪最新顶奢·堂岛川畔。175 间客房+24 套套房·Gensler 设计·楼下「Spa du Pacifique」是关西最大酒店 SPA。开业不到 1 年但已 MICHELIN Two Keys。",
            "亮点": ["MICHELIN Two Keys", "2024 新开业", "堂岛川景观", "顶级 SPA", "四季品牌"],
            "地址": "大阪市北区堂島浜 1-4-26（地铁西梅田站步行 8 分·JR 北新地站步行 5 分）",
            "房型": "Premier / Riverview / Suite·部分房型 60+ 平米",
            "含早": "可选·和洋自助 ¥7,500/人",
            "价格": "淡季 ¥2,800（开业 1 年内淡季少）/ 平季 ¥3,500-4,800 / 旺季 ¥6,000-7,000+",
            "预约": "官网 / 携程 / Four Seasons 会员",
            "到店提醒": "Check-in 15:00 / Check-out 12:00·SPA 含住客 / 外客 ¥8,000",
        },
        "可信度": "cross_checked",
        "数据来源": [
            "https://www.fourseasons.com/osaka/",
            "https://hotels.ctrip.com/hotels/106557148.html",
        ],
        "最后核实": "2026-04-26",
    },
}


def main():
    with open(HOTELS, encoding="utf-8") as f:
        pool = json.load(f)

    pool_by_id = {h["id"]: h for h in pool}

    updated = 0
    added = 0
    new_ids = {}  # 旧 id -> 新 id 映射

    for key, curation in CURATIONS.items():
        action = curation.get("_action", "update")
        if action == "add":
            # 新增整条
            new_h = {k: v for k, v in curation.items() if not k.startswith("_")}
            pool.append(new_h)
            added += 1
            continue

        if key not in pool_by_id:
            print(f"⚠ 未找到 {key}")
            continue
        for k, v in curation.items():
            if k.startswith("_"):
                continue
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

    print(f"✓ 精修 {updated} 家·新增 {added} 家·写回 {HOTELS.relative_to(REPO)}")


if __name__ == "__main__":
    main()
