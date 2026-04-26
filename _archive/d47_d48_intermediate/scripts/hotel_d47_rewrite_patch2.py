"""D47 套话重写 patch 第二批·21 家.

完成 29 - 8（已做） = 21 家。
"""
from __future__ import annotations

import io
import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DATA = Path("japan/kansai/hotels/data/hotels__kansai.json")
TODAY = datetime.now().strftime("%Y-%m-%d")

PATCHES = {
    # 京都 b2 区: 套话条目（中端体验）
    "kyo_shijo_kawaramachi_jing_xiao_su_shi_ting_tang_yin": {
        "depth": "verified",
        "可信度": "single_source",
        "数据来源": ["https://www.kogosi.com/yutone/"],
        "最后核实": TODAY,
        "note": {
            "店名": "京小宿 室町 ゆとね（Kogosi Muromachi Yutone）",
            "简介": "京都室町地区·町家小宿·一棟貸切·全 4 室·烏丸御池站徒步 5 分。京都市中心立地+町家氛围·适合追求京都生活感的客人。",
            "亮点": ["町家", "一棟貸切", "市中心", "全 4 室小宿"],
            "地址": "京都市中京区室町通·烏丸御池站徒步 5 分",
            "价格": "平季 2 人 ¥30,000-40,000 素泊（人均 ¥1,500-2,000·京都 b3 中端）",
            "预约": "公式 / 一休·小宿需提前预约",
        },
    },
    "kyo_gion_higashiyama_liao_li_ryokan_hua_le": {
        "depth": "verified",
        "可信度": "single_source",
        "数据来源": ["https://travel.kakaku.com/yad/10049565/"],
        "最后核实": TODAY,
        "note": {
            "店名": "料理旅館 花楽（Karaku Ryokan）",
            "简介": "祇园·八坂神社+高台寺中间·料理旅館·展望风吕付特别室口碑佳。京懐石部屋食 11 品·上品京都らしい味。大浴场宽敞。",
            "亮点": ["老铺旅馆", "祇园核心立地", "京懐石部屋食 11 品", "展望风吕付客室"],
            "地址": "京都市東山区·八坂神社徒步 5 分·京阪祇园四条站徒步 10 分",
            "价格": "夕朝食付 2 人 ¥25,000-40,000（人均 ¥1,250-2,000）",
            "预约": "公式 / 価格.com / 楽天·部屋食预约可指定",
        },
    },
    "kyo_kyoto_station_umekoji_kadensho": {
        "depth": "full",
        "可信度": "cross_checked",
        "数据来源": [
            "https://dormy-hotels.com/resort/hotels/umekoji_kadensho/",
            "https://www.ikyu.com/en-us/00002982/",
        ],
        "最后核实": TODAY,
        "note": {
            "店名": "京都 梅小路 花伝抄（共立リゾート Umekoji Kadensho）",
            "简介": "2022 年春开业·全 180 间和的城市酒店·JR梅小路京都西站徒步 2 分·京都站徒步 10 分·梅小路公园隣接。天然温泉大浴场+5 个无料贷切风吕（其中 3 个露天·樽风吕·桑拿·岩盤浴）。共立リゾート系·和食会席+おばんざい朝食 buffet。",
            "亮点": ["温泉度假", "梅小路公园", "5 个无料贷切风吕", "京都站徒步 10 分"],
            "地址": "京都市下京区·JR梅小路京都西站徒步 2 分",
            "房型": "全 180 室和洋室+和室",
            "含早": "おばんざい和洋 buffet",
            "价格": "素泊 2 人 ¥25,000-35,000 / 朝食付 ¥30,000+ / 夕朝食付 ¥38,000+",
            "预约": "公式 / 一休 / 楽天·先得 60 天最大 20%OFF",
            "到店提醒": "Check-in 15:00 / Check-out 11:00·5 贷切风吕无料·樱花季提前 60 天",
        },
    },
    "kyo_gion_higashiyama_omuro_kadensho": {
        "depth": "verified",
        "可信度": "single_source",
        "数据来源": ["https://dormy-hotels.com/"],
        "最后核实": TODAY,
        "note": {
            "店名": "御室花伝抄（Omuro Kadensho 共立リゾート）",
            "简介": "共立リゾート「花伝抄」3 棟之一（与梅小路·嵐山温泉並列）·御室仁和寺周边。同共立リゾート系·有贷切风吕+和食会席·偏家族向。",
            "亮点": ["温泉度假", "御室仁和寺周边", "贷切风吕"],
            "地址": "京都市右京区·御室仁和寺站近·area 实为 omuro/右京·跟 gion_higashiyama area 不符 → 待迁",
            "价格": "素泊 2 人 ¥20,000-30,000",
            "预约": "公式 / 一休 / 楽天",
        },
    },
    "kbe_harborland_meriken_gang_wen_quan_lian": {
        "depth": "full",
        "可信度": "cross_checked",
        "数据来源": [
            "https://ren-onsen.jp/",
            "https://www.ikyu.com/en-us/00002179/",
            "https://travel.kakaku.com/yad/11382410/",
        ],
        "最后核实": TODAY,
        "note": {
            "店名": "神户みなと温泉 蓮（Kobe Minato Onsen Ren）",
            "简介": "「温泉宿・ホテル総選挙 2025」**4 年连续全国 1 位**。地下 1,150m 自家天然温泉·三宫站专用无料 shuttle 5 分。**全 50 室以上+全室 terrace 海景 270°**·部分海侧スイート可看神户港夜景。厚生労働大臣認定「温泉利用型健康増進施設」+「運動型」西日本首例。",
            "亮点": ["温泉度假", "全国 1 位 4 连冠", "270°海景全室terrace", "三宫无料 shuttle"],
            "地址": "神户市中央区·三宫站无料 shuttle 5 分·新港埠头",
            "房型": "全 50 室以上·标准 50㎡+·海景 deluxe·港 suite",
            "含早": "和洋 buffet 含",
            "价格": "素泊 2 人 ¥32,560～·朝食付 ¥37,180～·夕朝食付 ¥44,000～·VIP券 ¥88,300-236,150",
            "预约": "公式 / 一休 / 楽天 / 价格.com·樱花季预订爆满",
            "到店提醒": "Check-in 15:00 / Check-out 11:00·shuttle 三宫北口·健康增进施設积分使用可",
        },
    },
    "kbe_harborland_meriken_gang_wen_quan_lian_2": {
        "_action": "delete_duplicate",
        "_reason": "与 kbe_harborland_meriken_gang_wen_quan_lian 是同一家·已删（保留前者）",
    },
    "nra_nara_park_area_chun_ri_hotel": {
        "depth": "verified",
        "可信度": "single_source",
        "数据来源": ["https://travel.yahoo.co.jp/00002012/"],
        "最后核实": TODAY,
        "note": {
            "店名": "春日ホテル（Kasuga Hotel）",
            "简介": "近铁奈良站徒步 1 分·奈良观光名宿·奈良公园徒步 5 分·東大寺/興福寺/春日大社全域 walking distance。中端家族向温泉旅馆。",
            "亮点": ["温泉旅馆", "近铁奈良站徒步 1 分", "奈良公园近邻", "中端家族向"],
            "地址": "奈良市·近铁奈良站徒步 1 分",
            "价格": "素泊 2 人 ¥18,000-30,000·夕朝食付 ¥25,000-40,000",
            "预约": "公式 / 一休 / 楽天",
        },
    },
    "shr_shirahama_infinito_hotel_spa_nanki_shira": {
        "depth": "full",
        "可信度": "cross_checked",
        "数据来源": [
            "https://hotel-infinito.co.jp/",
            "https://www.ikyu.com/en-us/00002384/",
            "https://travel.kakaku.com/yad/10050072/",
        ],
        "最后核实": TODAY,
        "note": {
            "店名": "INFINITO HOTEL & SPA 南紀白浜（Infinito Hotel & Spa）",
            "简介": "2017 年 4 月 rebrand·太平洋一望高台立地·**1400 余年历史源泉「行幸の湯」掛け流し**·BVLGARI amenity·海侧客房 panorama 海岸线。意大利「ジョヴァンニ」+ 和食「凪」·インフィニティ視野是签名。",
            "亮点": ["温泉度假", "1400 年源泉掛け流し", "panorama 海景", "BVLGARI amenity"],
            "地址": "和歌山県白浜町·南紀白浜駅 shuttle·白良浜 5 分",
            "房型": "海侧/山侧 deluxe·suite",
            "含早": "和洋 buffet 含",
            "价格": "素泊 2 人 ¥46,200～·朝食付 ¥46,000～·夕朝食付 ¥56,100～",
            "预约": "公式 / 一休 / JTB·BVLGARI amenity 整体 brand 統一",
            "到店提醒": "Check-in 15:00 / Check-out 11:00·南紀白浜駅 shuttle 預约·インフィニティ视野推荐黄昏",
        },
    },
    "shr_shirahama_shiraraso_grand_hotel": {
        "depth": "full",
        "可信度": "cross_checked",
        "数据来源": [
            "https://www.shiraraso.co.jp/",
            "https://jp.trip.com/hotels/shirahama-hotel-detail-705027/shiraraso-grand-hotel/",
            "https://www.tripadvisor.com/Hotel_Review-g1121351-d1165617-Reviews-Shiraraso_Grand_Hotel-Shirahama_cho_Nishimuro_gun_Wakayama_Prefecture_Kinki.html",
        ],
        "最后核实": TODAY,
        "note": {
            "店名": "白良荘グランドホテル（Shiraraso Grand Hotel）",
            "简介": "**白良浜真ん前**·全 100 室海景+浴衣·屋内温泉+开放露天风吕·咖啡厅+酒吧。Tripadvisor 白浜 22 ホテル 中 2 位·Booking 9.2 高评（カップル评）。日本三古湯白浜温泉。",
            "亮点": ["温泉旅馆", "白良浜真ん前", "海景全室", "日本三古湯"],
            "地址": "和歌山県白浜町·白良浜徒步 30 秒",
            "房型": "和室+和洋室·全 100 室·海景客房",
            "含早": "和食 buffet 含",
            "价格": "素泊 2 人 ¥18,000-30,000·夕朝食付 ¥30,000-50,000",
            "预约": "公式 / Trip.com / 楽天 / Booking",
            "到店提醒": "Check-in 15:00 / Check-out 10:00·夏季白良浜爆满建议提前预约",
        },
    },
    "shr_shirahama_shirahama_key_terrace_hotel_se": {
        "depth": "full",
        "可信度": "cross_checked",
        "数据来源": [
            "https://www.keyterrace.co.jp/",
            "https://travel.kakaku.com/yad/10050069/",
        ],
        "最后核实": TODAY,
        "note": {
            "店名": "SHIRAHAMA KEY TERRACE HOTEL SEAMORE（ホテルシーモア）",
            "简介": "2018 年 3 月大规模 renewal·**全 160 室海景**·绝景温泉+波の音露天风吕+くえ会席·开放 terrace+ベーカリー+泳池。じゃらん风吕/夕食/接客/朝食/清潔感全项高评。",
            "亮点": ["温泉度假", "2018 renewal", "全 160 室海景", "波音露天风吕", "くえ会席"],
            "地址": "和歌山県白浜町·南紀白浜駅 shuttle",
            "房型": "全 160 室·海景客房·和室+和洋室",
            "含早": "buffet 含",
            "价格": "素泊 2 人 ¥8,360～·朝食付 ¥12,400～·夕朝食付 ¥18,700～",
            "预约": "公式 / じゃらん / 楽天",
            "到店提醒": "Check-in 15:00 / Check-out 10:00·shuttle 南紀白浜駅·泳池夏季",
        },
    },
    "osk_bay_area_liber": {
        "depth": "full",
        "可信度": "cross_checked",
        "数据来源": [
            "https://hotel-liber.jp/",
            "https://www.ikyu.com/00002636/review/",
            "https://travel.kakaku.com/yad/11766916/",
        ],
        "最后核实": TODAY,
        "note": {
            "店名": "リーベルホテル大阪（LIBER HOTEL OSAKA）",
            "简介": "USJ 徒步 13 分·JR桜島駅徒步 1 分·**大阪最大级 ホテル**·大阪湾 panorama terrace·天然温泉大浴场+露天风吕+ドライサウナ。女湯水深 1m+炭酸风吕。MUJI room（无印良品）特别 12 室。",
            "亮点": ["温泉度假", "USJ 徒步 13 分", "大阪湾 terrace", "MUJI room 12 室"],
            "地址": "大阪市此花区·JR桜島駅徒步 1 分·USJ 13 分",
            "房型": "deluxe·suite·MUJI room 12 室",
            "含早": "和洋 buffet 含",
            "价格": "素泊 2 人 ¥30,000-50,000·朝食付 +¥3,000",
            "预约": "公式 / 一休 / 楽天·USJ 套票预订有",
            "到店提醒": "Check-in 15:00 / Check-out 11:00·USJ 套票 + park-side suite",
        },
    },
    "kyo_kyoto_station_jing_tang_yuan_jiu_wu_rui_feng_ge": {
        "depth": "verified",
        "可信度": "single_source",
        "数据来源": [
            "https://kyoto-hatoya.jp/",
            "https://travel.kakaku.com/yad/10049448/",
        ],
        "最后核实": TODAY,
        "note": {
            "店名": "京湯元 ハトヤ瑞鳳閣（Kyoto Hatoya Zuihokaku）",
            "简介": "**JR 京都站徒步 5 分**·**地下 910m 自家源泉天然温泉**·新撰组ゆかりの地（前有石碑）·和洋室/和室/洋室·京唐紙壁纸+障子·館内 700 種モルトウイスキーバー。",
            "亮点": ["温泉旅馆", "JR京都站徒步 5 分", "自家源泉地下 910m", "新撰组ゆかり"],
            "地址": "京都市下京区·JR京都站徒步 5 分",
            "房型": "和洋室+和室+洋室",
            "含早": "京都料理朝食含·絹ごし豆腐",
            "价格": "素泊 2 人 ¥18,000-30,000·夕朝食付 ¥25,000-40,000",
            "预约": "公式 / 一休 / 价格.com",
        },
    },
    "kyo_shijo_kawaramachi_song_jing_honkan": {
        "depth": "verified",
        "可信度": "single_source",
        "数据来源": ["https://travel.kakaku.com/yad/10049543/"],
        "最后核实": TODAY,
        "note": {
            "店名": "松井本館（Matsui Honkan）",
            "简介": "阪急四条烏丸/地下铁四条站徒步 8 分·**数寄屋門+川島織物+伝統木工**·大浴场看坪庭瀑布。京懐石夕食+老铺豆腐店湯豆腐朝食。畳+ベッド和洋室·和柄 デュベ.",
            "亮点": ["老铺旅馆", "数寄屋門", "坪庭大浴场", "京懐石"],
            "地址": "京都市下京区·阪急四条烏丸/地铁四条站徒步 8 分",
            "房型": "和室+和洋室·部分坪庭付",
            "价格": "夕朝食付 2 人 ¥35,000-60,000",
            "预约": "公式 / 一休 / 楽天",
        },
    },
    "kyo_shijo_kawaramachi_tian_fu_luo_ji_chuan": {
        "depth": "verified",
        "可信度": "single_source",
        "数据来源": ["https://www.yoshikawa-inn.com/"],
        "最后核实": TODAY,
        "note": {
            "店名": "天ぷら吉川（Yoshikawa Tempura Ryokan）",
            "简介": "京都 富小路·天ぷら名店併設の老铺料亭旅館·小規模奥座敷型·一品天ぷら+京料理。料理重視の客人定番。",
            "亮点": ["老铺旅馆", "天ぷら老店", "小规模奥座敷"],
            "地址": "京都市中京区富小路·烏丸御池徒步 10 分",
            "价格": "夕朝食付 2 人 ¥40,000-80,000",
            "预约": "公式·小規模需早预约",
        },
    },
    "kyo_gion_higashiyama_you_zi_wu_ryokan": {
        "depth": "full",
        "可信度": "cross_checked",
        "数据来源": [
            "https://www.yuzuyaryokan.com/",
            "https://www.ikyu.com/en-us/00001115/",
            "https://travel.kakaku.com/yad/10060187/",
        ],
        "最后核实": TODAY,
        "note": {
            "店名": "京都祇園 柚子屋旅館（Yuzuya Ryokan）",
            "简介": "**八坂神社の隣**·京阪祇園四条站徒步 7 分·**檜の柚子风吕**（柚子浮かぶ）·京野菜+水尾柚子料理·全室 2 階。Tripadvisor 京都 346 中 37 位·全室 2 階+无停车场（13 岁以下不可）。",
            "亮点": ["老铺旅馆", "八坂神社隣", "檜柚子风吕", "祇园核心"],
            "地址": "京都市東山区祇園·京阪祇園四条站徒步 7 分",
            "房型": "和室·全室 2 階·部分露天",
            "含早": "京都和朝食含",
            "价格": "夕朝食付 2 人 ¥60,500～·美食旅 plan",
            "预约": "公式 / じゃらん / 楽天 / 一休·13 岁以下不可入住",
            "到店提醒": "Check-in 15:00 / Check-out 10:00·全室 2 階阶梯·无停车场",
        },
    },
    "kyo_gion_higashiyama_chun_he_feng_liao_li_ryokan_ji_nai_hui": {
        "depth": "verified",
        "可信度": "single_source",
        "数据来源": ["https://kinoe.com/"],
        "最后核实": TODAY,
        "note": {
            "店名": "純和風料理旅館 き乃ゑ（Kinoe Ryokan）",
            "简介": "祇园·純和風小規模料理旅館·京懐石+部屋食·体感旧京都。",
            "亮点": ["老铺旅馆", "祇园", "京懐石部屋食", "纯和风小宿"],
            "地址": "京都市東山区·祇園周边",
            "价格": "夕朝食付 2 人 ¥35,000-60,000",
            "预约": "公式·小規模需早预约",
        },
    },
    "nra_nara_park_area_gu_dou_zhi_su_wu_cang_ye": {
        "depth": "full",
        "可信度": "cross_checked",
        "数据来源": [
            "https://www.nara-musashino.com/",
            "https://www.tripadvisor.com/Hotel_Review-g298198-d1087681-Reviews-Kotonoyado_Musashino-Nara_Nara_Prefecture_Kinki.html",
        ],
        "最后核实": TODAY,
        "note": {
            "店名": "古都の宿 むさし野（Kotonoyado Musashino）",
            "简介": "**奈良最古のお宿**·江戸時代から·若草山のぞむ深緑·純和風旅館。**谷崎潤一郎・山岡鉄舟ら文人墨客御用達**·奈良公園内立地·四季京懐石部屋食。Tripadvisor 奈良 38 ホテル 4 位（98 评价）。",
            "亮点": ["老铺旅馆", "奈良最古", "若草山眺望", "文人墨客御用达"],
            "地址": "奈良市春日野町·奈良公園内·近鉄奈良站徒步 25 分（送迎可）",
            "房型": "和室·部分若草山景",
            "含早": "京懐石部屋食",
            "价格": "夕朝食付 2 人 ¥40,000-80,000",
            "预约": "公式 / 一休 / 楽天",
        },
    },
    "nra_nara_park_area_you_jing_zhi_su_ping_cheng": {
        "depth": "verified",
        "可信度": "single_source",
        "数据来源": ["https://yukei.jp/"],
        "最后核实": TODAY,
        "note": {
            "店名": "遊景の宿 平城（Yukei no Yado Heijo）",
            "简介": "奈良市内·料亭旅館·奈良の四季的部屋食·中端体验。",
            "亮点": ["老铺旅馆", "奈良市内", "料亭旅馆"],
            "地址": "奈良市·近鉄奈良站近邻",
            "价格": "夕朝食付 2 人 ¥30,000-50,000",
            "预约": "公式 / 一休 / 楽天",
        },
    },
    "nra_nara_park_area_si_ji_ting": {
        "depth": "full",
        "可信度": "cross_checked",
        "数据来源": ["https://shikitei.com/", "https://www.ikyu.com/00002012/"],
        "最后核实": TODAY,
        "note": {
            "店名": "四季亭（Shikitei）",
            "简介": "**百余年の歴史と近代美**·奈良公园周边·和の落ち着き·中等規模料理旅館。",
            "亮点": ["老铺旅馆", "百余年", "奈良公园周边"],
            "地址": "奈良市·奈良公园近邻",
            "价格": "素泊 2 人 ¥46,200～·夕朝食付 ¥66,000～",
            "预约": "公式 / 一休 / 楽天",
        },
    },
    "nra_nara_park_area_fei_niao_zhuang": {
        "depth": "full",
        "可信度": "cross_checked",
        "数据来源": [
            "https://www.asukasou.com/",
            "https://www.ikyu.com/00002162/",
            "https://www.jalan.net/yad333870/",
        ],
        "最后核实": TODAY,
        "note": {
            "店名": "古都奈良の宿 飛鳥荘（Asukaso）",
            "简介": "**興福寺五重塔目前·屋上展望露天风吕**（炭酸カルシウム人工温泉水）·近鉄奈良站徒步 8 分·興福寺/奈良公园/ならまち walking distance。**Yahoo!トラベル 4.71**（奈良评价 TOP3）·料亭旅館·黒毛和牛+月替会席。",
            "亮点": ["温泉旅馆", "興福寺五重塔目前", "屋上展望风吕", "Yahoo 4.71"],
            "地址": "奈良市高畑町·近鉄奈良站徒步 8 分",
            "房型": "和室+リニューアルレジデンス（ベッド+リビング分离）+バリアフリー",
            "含早": "京懐石朝食",
            "价格": "夕朝食付 2 人 ¥25,740～（じゃらん）",
            "预约": "公式 / 一休 / 楽天·興福寺正面客房早预约",
            "到店提醒": "Check-in 15:00 / Check-out 10:00·屋上展望风吕看興福寺五重塔",
        },
    },
}


def main() -> None:
    apply = "--apply" in sys.argv
    data = json.loads(DATA.read_text(encoding="utf-8"))
    by_id = {h["id"]: h for h in data}

    delete_ids = []
    updated = 0
    not_found = []

    for hid, patch in PATCHES.items():
        if hid not in by_id:
            not_found.append(hid)
            continue
        h = by_id[hid]
        if patch.get("_action") == "delete_duplicate":
            delete_ids.append(hid)
            continue
        for k, v in patch.items():
            if k.startswith("_"):
                continue
            h[k] = v
        updated += 1

    if delete_ids:
        data = [h for h in data if h["id"] not in delete_ids]

    print(f"updated: {updated}")
    print(f"deleted: {len(delete_ids)} → {delete_ids}")
    print(f"not_found: {len(not_found)} → {not_found}")

    if apply:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("\n[APPLIED]")
    else:
        print("\n[DRY-RUN]")


if __name__ == "__main__":
    main()
