"""精修关键 quality 档酒店（装配主力·首次客核心通道）。"""
from __future__ import annotations
import io, json, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
HOTELS = REPO / "japan/kansai/hotels/data/hotels__kansai.json"

CURATIONS = {
    "kyo_kyoto_station_hotel_granvia_kyoto": {
        "id": "kyo_kyoto_station_hotel_granvia_kyoto",
        "city": "京都",
        "area": "kyoto_station",
        "near_attractions": [{"entity_id": "kyo_railway_museum", "walk_min": 10}, {"entity_id": "kyo_kyoto_aquarium", "walk_min": 12}],
        "tier": "quality",
        "type": "city",
        "price_cny_per_night": [800, 1800],
        "depth": "full",
        "season_months": None,
        "note": {
            "店名": "京都格兰维亚大酒店（Hotel Granvia Kyoto / ホテルグランヴィア京都）",
            "简介": "京都站直结·535 间客房·关西多城联游/早班新干线人群首选。京都站新干线 5 分钟·神户/奈良/大阪日归无压力。中国客覆盖最深的京都中端·携程评分稳定 4.6+。",
            "亮点": ["京都站直结", "中国客信任", "新干线友好", "多城联游"],
            "地址": "京都市下京区烏丸通塩小路下ル東塩小路町 901（JR 京都站直结）",
            "房型": "豪华 / 行政 / 套房",
            "含早": "可选·和洋自助 ¥3,500/人",
            "价格": "淡季 ¥600 / 平季 ¥800-1,200 / 旺季 ¥1,500-1,800（樱花/红叶提前 60 天）",
            "预约": "官网 / 携程 / JR 西日本 plus",
            "到店提醒": "Check-in 15:00 / Check-out 12:00·新干线换乘 5 分钟",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://www.granvia-kyoto.co.jp/", "https://hotels.ctrip.com/hotels/426893.html"],
        "最后核实": "2026-04-26",
    },
    "kyo_shijo_kawaramachi_h012": {
        "id": "kyo_shijo_kawaramachi_mitsui_garden_shijo",
        "city": "京都",
        "area": "shijo_kawaramachi",
        "near_attractions": [{"entity_id": "kyo_pontocho", "walk_min": 5}],
        "tier": "quality",
        "type": "city",
        "price_cny_per_night": [700, 1500],
        "depth": "full",
        "season_months": None,
        "note": {
            "店名": "三井花园酒店京都四条（Mitsui Garden Hotel Kyoto Shijo / 三井ガーデンホテル京都四条）",
            "简介": "四条乌丸核心·三井花园连锁日系老牌·楼下大浴场是签名（住客免费）。性价比+地点+大浴场三位一体·中国客最爱的中端。",
            "亮点": ["大浴场", "三井花园连锁", "四条核心", "性价比"],
            "地址": "京都市下京区室町通仏光寺下ル白楽天町 526-7（地铁四条站步行 4 分）",
            "房型": "标准 / 豪华",
            "含早": "可选·和洋自助",
            "价格": "淡季 ¥500 / 平季 ¥700-1,000 / 旺季 ¥1,200-1,500",
            "预约": "官网 / 携程",
            "到店提醒": "Check-in 15:00 / Check-out 11:00·大浴场住客免费",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://www.gardenhotels.co.jp/kyoto-shijo/", "https://hotels.ctrip.com/hotels/693993.html"],
        "最后核实": "2026-04-26",
    },
    "kyo_shijo_kawaramachi_h031": {
        "id": "kyo_shijo_kawaramachi_hyatt_place_kyoto",
        "city": "京都",
        "area": "shijo_kawaramachi",
        "near_attractions": [{"entity_id": "kyo_pontocho", "walk_min": 4}],
        "tier": "quality",
        "type": "city",
        "price_cny_per_night": [800, 1700],
        "depth": "full",
        "season_months": None,
        "note": {
            "店名": "凯悦嘉轩京都（Hyatt Place Kyoto / ハイアットプレイス京都）",
            "简介": "2024 年开业·凯悦嘉轩品牌入京都·239 间客房+全日早餐厅。Hyatt 全球会员积分友好·商务客+多城联游客户最稳。",
            "亮点": ["2024 新开业", "Hyatt 品牌", "积分友好", "全日早餐"],
            "地址": "京都市下京区高倉通仏光寺下ル新開町 393（地铁四条站步行 5 分）",
            "房型": "标准 / 套房",
            "含早": "含·全日早餐",
            "价格": "淡季 ¥600 / 平季 ¥800-1,200 / 旺季 ¥1,400-1,700",
            "预约": "官网 / 携程 / Hyatt World",
            "到店提醒": "Check-in 15:00 / Check-out 12:00",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://www.hyatt.com/hyatt-place/itmkz-hyatt-place-kyoto/"],
        "最后核实": "2026-04-26",
    },
    "kyo_shijo_kawaramachi_h053": {
        "id": "kyo_shijo_kawaramachi_kyoto_monterey",
        "city": "京都",
        "area": "shijo_kawaramachi",
        "near_attractions": [{"entity_id": "kyo_pontocho", "walk_min": 5}],
        "tier": "quality",
        "type": "city",
        "price_cny_per_night": [700, 1500],
        "depth": "full",
        "season_months": None,
        "note": {
            "店名": "京都蒙特利酒店（Kyoto Monterey Hotel / 京都モントレホテル）",
            "简介": "四条乌丸·蒙特利日系连锁·230 间客房欧式古典风+和洋大浴场。中端最稳·价格友好·中国客覆盖深·小红书爆款常客。",
            "亮点": ["蒙特利连锁", "和洋大浴场", "性价比", "小红书爆款"],
            "地址": "京都市中京区柳馬場通御池下ル弁慶石町 56（地铁烏丸御池站步行 4 分）",
            "房型": "标准 / 豪华",
            "含早": "可选",
            "价格": "淡季 ¥500 / 平季 ¥700-1,000 / 旺季 ¥1,200-1,500",
            "预约": "官网 / 携程",
            "到店提醒": "Check-in 14:00 / Check-out 11:00·大浴场住客免费",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://www.hotelmonterey.co.jp/kyoto/", "https://hotels.ctrip.com/hotels/672632.html"],
        "最后核实": "2026-04-26",
    },
    "osk_umeda_kita_h130": {
        "id": "osk_umeda_kita_mitsui_garden_premier",
        "city": "大阪",
        "area": "umeda_kita",
        "near_attractions": [{"entity_id": "osk_nakanoshima", "walk_min": 6}],
        "tier": "quality",
        "type": "city",
        "price_cny_per_night": [800, 1700],
        "depth": "full",
        "season_months": None,
        "note": {
            "店名": "三井花园酒店大阪尊贵版（Mitsui Garden Hotel Osaka Premier / 三井ガーデンホテル大阪プレミア）",
            "简介": "梅田/淀屋桥之间·堂岛川河畔·三井花园 Premier 系列·366 间客房+顶层观景大浴场。性价比+商务+大浴场三优·中端首选。",
            "亮点": ["大浴场", "三井花园 Premier", "堂岛川景观", "商务友好"],
            "地址": "大阪市北区堂島浜 1-3-5（地铁西梅田站步行 5 分·JR 北新地步行 5 分）",
            "房型": "豪华 / 行政",
            "含早": "可选·和洋自助",
            "价格": "淡季 ¥500 / 平季 ¥800-1,200 / 旺季 ¥1,400-1,700",
            "预约": "官网 / 携程",
            "到店提醒": "Check-in 14:00 / Check-out 11:00·顶层大浴场住客免费",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://www.gardenhotels.co.jp/osaka-premier/", "https://hotels.ctrip.com/hotels/2199704.html"],
        "最后核实": "2026-04-26",
    },
    "osk_umeda_kita_h162": {
        "id": "osk_umeda_kita_osaka_monterey",
        "city": "大阪",
        "area": "umeda_kita",
        "near_attractions": [{"entity_id": "osk_nakanoshima", "walk_min": 7}],
        "tier": "quality",
        "type": "city",
        "price_cny_per_night": [600, 1300],
        "depth": "full",
        "season_months": None,
        "note": {
            "店名": "大阪蒙特利酒店（Osaka Monterey Hotel / ホテルモントレ大阪）",
            "简介": "梅田·蒙特利大阪旗舰·362 间客房+顶层 SPA。性价比+设施齐+商务友好·中国客最爱的大阪中端代表。",
            "亮点": ["蒙特利连锁", "顶层 SPA", "梅田核心", "性价比"],
            "地址": "大阪市北区中崎西 2-3-2（JR 大阪站步行 7 分）",
            "房型": "标准 / 豪华",
            "含早": "可选",
            "价格": "淡季 ¥400 / 平季 ¥600-900 / 旺季 ¥1,100-1,300",
            "预约": "官网 / 携程",
            "到店提醒": "Check-in 14:00 / Check-out 11:00",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://www.hotelmonterey.co.jp/osaka/"],
        "最后核实": "2026-04-26",
    },
    "kbe_sannomiya_h231": {
        "id": "kbe_sannomiya_kobe_monterey",
        "city": "神户",
        "area": "sannomiya",
        "near_attractions": [{"entity_id": "kob_kitano_kyoryuchi", "walk_min": 5}],
        "tier": "quality",
        "type": "city",
        "price_cny_per_night": [600, 1300],
        "depth": "full",
        "season_months": None,
        "note": {
            "店名": "神户蒙特利酒店（Kobe Monterey Hotel / ホテルモントレ神戸）",
            "简介": "神户三宮·步行 3 分到旧居留地·欧式古典风格契合神户洋馆气氛。160 间客房+和洋大浴场。三宫站方便·神户主住宿首选中端。",
            "亮点": ["蒙特利连锁", "三宮 3 分", "旧居留地步行可达", "和洋大浴场"],
            "地址": "神戸市中央区下山手通 2-11-13（JR/阪神三宮站步行 5 分）",
            "房型": "标准 / 豪华",
            "含早": "可选",
            "价格": "淡季 ¥400 / 平季 ¥600-900 / 旺季 ¥1,100-1,300",
            "预约": "官网 / 携程",
            "到店提醒": "Check-in 14:00 / Check-out 11:00",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://www.hotelmonterey.co.jp/kobe/"],
        "最后核实": "2026-04-26",
    },
    "kyo_gion_higashiyama_hotel_the_celestine_kyoto_gion": {
        "id": "kyo_gion_higashiyama_celestine_gion",
        "city": "京都",
        "area": "gion_higashiyama",
        "near_attractions": [{"entity_id": "kyo_kenninji", "walk_min": 3}, {"entity_id": "kyo_yasaka_shrine", "walk_min": 6}],
        "tier": "quality",
        "type": "city",
        "price_cny_per_night": [900, 1700],
        "depth": "full",
        "season_months": None,
        "note": {
            "店名": "祇园天琴京都酒店（Hotel The Celestine Kyoto Gion）",
            "简介": "祇园核心·建仁寺南侧·130 间客房和洋融合设计·楼下含大浴场。祇园核心便利+京风设计+中端价位的稀缺组合。",
            "亮点": ["祇园核心", "和洋融合", "大浴场", "建仁寺步行 3 分"],
            "地址": "京都市東山区高台寺南門通下河原東入八坂上町 372（京阪祇园四条站步行 12 分）",
            "房型": "豪华 / 套房",
            "含早": "可选",
            "价格": "淡季 ¥700 / 平季 ¥900-1,300 / 旺季 ¥1,500-1,700",
            "预约": "官网 / 携程",
            "到店提醒": "Check-in 15:00 / Check-out 11:00",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://www.celestinehotels.jp/kyoto-gion/"],
        "最后核实": "2026-04-26",
    },
    "kyo_kyoto_station_h015": {
        "id": "kyo_kyoto_station_miyako_hachijo",
        "city": "京都",
        "area": "kyoto_station",
        "near_attractions": [{"entity_id": "kyo_railway_museum", "walk_min": 10}],
        "tier": "quality",
        "type": "city",
        "price_cny_per_night": [600, 1400],
        "depth": "full",
        "season_months": None,
        "note": {
            "店名": "都酒店京都八条（Miyako Hotel Kyoto Hachijo / 都ホテル 京都八条）",
            "简介": "京都站八条口直结·745 间客房·京都最大体量酒店之一。多城联游/早班新干线/团队客最稳·中端价位+京都站直结的硬条件。",
            "亮点": ["京都站直结", "全京都最大", "多城联游", "团队友好"],
            "地址": "京都市南区西九条院町 17（JR 京都站八条口直结）",
            "房型": "标准 / 豪华",
            "含早": "可选",
            "价格": "淡季 ¥400 / 平季 ¥600-900 / 旺季 ¥1,100-1,400",
            "预约": "官网 / 携程",
            "到店提醒": "Check-in 14:00 / Check-out 11:00·近铁京都站对面",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://www.miyakohotels.ne.jp/kyoto-hachijo/"],
        "最后核实": "2026-04-26",
    },
    "kyo_shijo_kawaramachi_h013": {
        "id": "kyo_shijo_kawaramachi_mitsui_garden_sanjo_premier",
        "city": "京都",
        "area": "shijo_kawaramachi",
        "near_attractions": [{"entity_id": "kyo_pontocho", "walk_min": 3}],
        "tier": "quality",
        "type": "city",
        "price_cny_per_night": [900, 1700],
        "depth": "full",
        "season_months": None,
        "note": {
            "店名": "三井花园酒店京都三条尊贵版（Mitsui Garden Hotel Kyoto Sanjo Premier / 三井ガーデンホテル京都三条プレミア）",
            "简介": "三条河原町·三井花园 Premier 京都旗舰·193 间客房+顶层鸭川景观大浴场。先斗町步行 3 分·中端 Premier 性价比之王。",
            "亮点": ["大浴场", "鸭川景观", "三条核心", "Premier 系列"],
            "地址": "京都市中京区河原町通三条上ル恵比須町 434-1（地铁京都市役所前步行 3 分）",
            "房型": "豪华 / 行政",
            "含早": "可选",
            "价格": "淡季 ¥600 / 平季 ¥900-1,300 / 旺季 ¥1,400-1,700",
            "预约": "官网 / 携程",
            "到店提醒": "Check-in 14:00 / Check-out 11:00",
        },
        "可信度": "cross_checked",
        "数据来源": ["https://www.gardenhotels.co.jp/kyoto-sanjo-premier/"],
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

    print(f"✓ Quality 档精修 {updated} 家")


if __name__ == "__main__":
    main()
