"""D47 套话条目逐家重写 patch.

为已经收集到真实数据的酒店重写 note 块，提升 depth 到 verified/full。

每个 patch 项：
- id: 旧 id（如有需要新 id 在脚本末尾另改）
- note: 完整新 note 块（覆盖式）
- depth: 新 depth
- 可信度: 新值
- 数据来源: 新 URL 数组
- 最后核实: 当天日期

数据来源：trip.com / 楽天トラベル / 一休 / 公式サイト / 価格.com（WebSearch 抓取）
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

# patches: dict[hid_or_alias] = {fields...}
PATCHES = {
    # 空庭テラス京都本馆
    "kyo_shijo_kawaramachi_shijo_kawaramachi_wen_quan_kong_ting_lu_tai_jing_dou": {
        "tier": "b4",  # 平季 1100·京都 b4 区间 1200-2000 接近·上调
        "price_cny_per_night": [1100, 1800],
        "depth": "full",
        "可信度": "cross_checked",
        "数据来源": [
            "https://jp.trip.com/hotels/kyoto-hotel-detail-88815812/shijo-kawaramachi-onsen-soraniwa-terrace-kyoto/",
            "https://soraniwa-hotel.jp/",
        ],
        "最后核实": TODAY,
        "note": {
            "店名": "四条河原町温泉 空庭テラス京都（Sora Niwa Terrace Kyoto）",
            "简介": "2022 年 6 月开业·京都市中心罕见的自家源泉温泉酒店·101 间客房。最上層大浴場「八坂の湯」「庭の湯」男女日替·屋上「空庭テラス」可俯瞰鸭川・八坂塔・清水寺・東山三十六峰·黄昏 16:00-18:30 免费 welcome drink 服务。注意点：trip.com 部分点评提到接待外国客时态度有差·但风吕和景观是关西市内独特卖点。",
            "亮点": ["温泉度假", "市内自家源泉", "屋上展望テラス", "东山景观", "立地优秀"],
            "地址": "京都市下京区稲荷町324·阪急京都河原町站徒步 4 分（220m）",
            "房型": "Moderate Double / Superior Double / Universal Twin（共 3 类·全 101 间）",
            "含早": "和食 ¥4,000/人·儿童同价·屋上 OR 在房享用",
            "价格": "淡季最低 ¥1,000（1月平日素泊）/ 平季中位 ¥1,100 / 旺季 ¥1,800（樱花/红叶提前 60 天约）",
            "预约": "trip.com / 一休 / 楽天 / 官网·trip 9.4/10 = 994 评论",
            "到店提醒": "Check-in 15:00 / Check-out 11:00·屋上 Bar 22:00 关·男女汤每日切换",
        },
    },
    # 空庭テラス京都 別邸
    "kyo_shijo_kawaramachi_shijo_kawaramachi_wen_quan_kong_ting_lu_tai_jing_dou_bettei": {
        "tier": "b6",  # 2人 ¥51,681 ≈ ¥1,300/人 · 但夕朝食付 110,000 ≈ ¥2,750/人 · 京都 b6 ≥3500
        "price_cny_per_night": [1900, 3200],  # 平季 ≈ ¥1,900/人 素泊·旺季 ¥3,200
        "depth": "full",
        "可信度": "cross_checked",
        "数据来源": [
            "https://shijo-bettei.jp/",
            "https://www.ikyu.com/00002981/",
            "https://www.tripadvisor.com/Hotel_Review-g298564-d25283735-Reviews-Soraniwa_Terrace_Kyoto-Kyoto_Kyoto_Prefecture_Kinki.html",
        ],
        "最后核实": TODAY,
        "note": {
            "店名": "四条河原町温泉 空庭テラス京都 別邸（Soraniwa Terrace Kyoto Bettei）",
            "简介": "2022 年 6 月开业·全 32 室客房均含露天风吕（自家源泉地下 1100m 镁含量丰富）·阪急京都河原町站徒步 1 分。专用数寄屋门设在裏通り·別邸専用フロント+冷蔵庫フリードリンク·部分客房面东山有专用 terrace。京懐石「東山」夕食 1 人也可在豪華個室+和服女性配膳。1 階大浴場「八坂の湯」「庭の湯」每日男女互换·水深 1m20cm 立位入浴·屋上「空庭テラス」无料 happy hour 16:00-18:30。",
            "亮点": ["温泉旅馆", "全室露天風呂", "自家源泉镁泉", "別邸専用門", "京懐石「東山」"],
            "地址": "京都市下京区稲荷町·阪急京都河原町站徒步 1 分（150m）",
            "房型": "全 32 室全室露天风吕·东山景观房 / 数寄屋造 / 一般客室",
            "含早": "京懐石朝食",
            "价格": "素泊 2 人 ¥51,681～（人均 ¥25,840）/ 朝食付 ¥57,763～ / 夕朝食付 110,000～（旺季加成）",
            "预约": "公式·一休·楽天·trip.com·樱花/红叶季提前 60 天",
            "到店提醒": "Check-in 15:00 / Check-out 11:00·別邸 16:00-18:30 happy hour 免费饮品·全室露天风吕推荐选东山景观房",
        },
    },
    # 高雄もみぢ家本館
    "kyo_takao_hong_ye_jia_honkan_takao_sanso": {
        "tier": "b5",  # 平季 ¥1,600 / 京都 b5 区间 1200-2000 → b4·但夕朝食付实际更贵
        "price_cny_per_night": [1500, 2400],
        "depth": "full",
        "可信度": "cross_checked",
        "数据来源": [
            "https://www.momijiya.jp/",
            "https://travel.rakuten.co.jp/HOTEL/38915/review.html",
            "https://www.ikyu.com/00002117/",
        ],
        "最后核实": TODAY,
        "note": {
            "店名": "もみぢ家本館 高雄山荘（Momijiya Honkan Takao Sanso）",
            "简介": "創業 100 余年的料亭旅館·京都右京区高雄·神護寺/西明寺/高山寺三尾中央。市内开车 30 分·与游客密集区拉开距离。**夏季川床**（5-9 月清滝川河畔）+ **秋红叶名所**（11 月中下旬）+ 冬牡丹锅四季皆有看点。客室 14 间·有大浴场+露天风吕+贷切风吕。夕食时舞妓服务+京舞鑑賞特别企画（夏季限定）。京都市内的避世名宿。",
            "亮点": ["温泉旅馆", "高雄川床发祥地", "三尾红叶名所", "舞妓京舞鑑賞", "創業 100 余年"],
            "地址": "京都市右京区梅ヶ畑高雄·周山街道（国道 162 号）·京都市内开车 30 分·有送迎",
            "房型": "本馆和室 14 室·部分有专用露天风吕",
            "含早": "和朝食含",
            "价格": "公式 ¥27,500～¥36,300（人/税込含夕朝食）·素泊几无·夏川床 / 秋红叶旺季加成大",
            "预约": "公式 / 楽天 / 一休 / JTB·送迎要电话预约·川床 5-9 月限定",
            "到店提醒": "Check-in 15:00 / Check-out 10:00·夏季雨天川床中止·夕食时间固定",
        },
    },
    # 貴船 ふじや
    "kyo_kibune_kibune_teng_wu": {
        "tier": "b6",  # 2人 ¥48,400 / 人均 ¥24,200 ≈ b6
        "price_cny_per_night": [2400, 3300],
        "depth": "full",
        "可信度": "cross_checked",
        "数据来源": [
            "http://www.kibune-fujiya.co.jp/",
            "https://www.ikyu.com/00030167/",
            "https://travel.kakaku.com/yad/10218622/",
        ],
        "最后核实": TODAY,
        "note": {
            "店名": "貴船 ふじや（元祖川床発祥の老舗料理旅館 Kibune Fujiya）",
            "简介": "天保年間（1830-1844）創業·大正後期に**川床を最初に始めた「川床発祥のお店」**。貴船神社徒步 30 秒·清流贵船川河畔。大浴场用贵船石岩風呂 + 大理石ステンドグラス風呂（贵船湧水）。鮎・川魚料理は表面パリッ骨まで食べられる·じゃらん夕食 4.6 高評価。",
            "亮点": ["温泉旅馆", "川床発祥老舗", "贵船神社徒步 30 秒", "鮎/川魚料理", "贵船湧水风吕"],
            "地址": "京都市左京区鞍馬貴船町·叡山電鉄貴船口站徒步 30 分·有送迎",
            "房型": "和室·部分有露天风吕",
            "含早": "和朝食含",
            "价格": "夕朝食付 2 人 ¥48,400～¥66,000（人均 ¥24,200～33,000）·川床料理「松」13,750 /「竹」16,280 /「梅」20,075（席料 +1,080）",
            "预约": "公式 / 一休 / じゃらん / 楽天·夏川床 5-9 月需提前·神事祭典前后満室",
            "到店提醒": "Check-in 15:00 / Check-out 10:00·雨天川床中止改室内",
        },
    },
    # 料理旅館 右源太（鞍馬・貴船）
    "kyo_arashiyama_liao_li_ryokan_you_yuan_tai": {
        "tier": "b5",  # 川床懐石 9,900-19,900 + 一泊二食 估 b5
        "price_cny_per_night": [1500, 2500],
        "depth": "full",
        "可信度": "cross_checked",
        "数据来源": [
            "https://ugenta.co.jp/",
            "https://www.ikyu.com/en-us/00001508/",
            "https://travel.kakaku.com/yad/10037782/",
        ],
        "最后核实": TODAY,
        "note": {
            "店名": "料理旅館 右源太（Kifune Ugenta）",
            "简介": "貴船川上流的料理旅館。川魚は貴船川の伏流水で 3 日間泳がせて泥抜き·素材の旨み引き出される。価格.com 客室 4.83 / 食事 4.69 / 风吕 4.75 高评価·性价比 3.92。姊妹店「左源太」更casual。叡山電鉄貴船口站徒步 30 分·出町柳站有送迎（要提前电话）。",
            "亮点": ["温泉旅馆", "貴船川上流", "3 日間泥抜き川魚", "コスパ◎", "无料送迎"],
            "地址": "京都市左京区鞍馬貴船町·叡山電鉄貴船口站徒步 30 分（送迎可）",
            "房型": "和室·部分客房面贵船川",
            "含早": "和朝食含",
            "价格": "夕朝食付 2 人 ¥30,000～·川床懐石 9,900～19,900（席料無料·3 日前需预约）",
            "预约": "公式 / 一休 / じゃらん·川床 5-9 月限定",
            "到店提醒": "Check-in 15:00 / Check-out 10:00·送迎需提前电话·区域 area=kibune（不是岚山）",
        },
        # 注意：area 已修为 arashiyama→应改为 kibune
        "_area_override": "kibune",
    },
    # 嵐山温泉 花伝抄（共立リゾート）
    "kyo_arashiyama_arashiyama_wen_quan_kadensho": {
        "tier": "b4",  # 朝食付 ¥29,800 ≈ 1人 ¥1,500·b4 区间 1200-2000
        "price_cny_per_night": [1500, 2400],
        "depth": "full",
        "可信度": "cross_checked",
        "数据来源": [
            "https://dormy-hotels.com/resort/hotels/kadensho/",
            "https://travel.kakaku.com/yad/11187393/",
            "https://www.ikyu.com/00001842/review/",
        ],
        "最后核实": TODAY,
        "note": {
            "店名": "京都 嵐山温泉 花伝抄（共立リゾート Arashiyama Onsen Kadensho）",
            "简介": "阪急嵐山駅徒步 1 分·渡月橋徒步 5 分·館内全畳敷·無仲居プライベート滞在。湯巡り含 5 个无料贷切风吕（其中 3 个露天）·館内浴衣无料·夜鳴きそば夜食·日帰り温泉「風風の湯」无料券。屋号源世阿弥「花伝書」「秘すれば花なり」。注意：嵐山立地导致大浴场国际客流量大·部分点评提到 manner 问题。",
            "亮点": ["温泉度假", "嵐山温泉自源泉", "5 个贷切风吕", "渡月桥徒步 5 分", "夜鳴きそば夜食"],
            "地址": "京都市西京区嵐山西一川町 5-4·阪急嵐山駅徒步 1 分",
            "房型": "全和室·部分露天风吕付",
            "含早": "一汁五菜「四季夕膳」+ おばんざい+ 天ぷらオーダービュッフェ",
            "价格": "素泊 2 人 ¥29,358～·朝食付 ¥29,800～·夕朝食付 ¥37,200～",
            "预约": "公式 / 一休 / じゃらん / 楽天·夕食 17:30 OR 20:00 入替制",
            "到店提醒": "Check-in 15:00 / Check-out 10:00·5 个贷切风吕无料但混雑期需现场排队·夕食 2 部入替",
        },
    },
    # 岚山温泉 花伝抄_2（重复物业·同一家·删此条）
    "kyo_arashiyama_arashiyama_wen_quan_kadensho_2": {
        "_action": "delete_duplicate",
        "_reason": "与 kyo_arashiyama_arashiyama_wen_quan_kadensho 是同一家酒店",
    },
    # FUFU Kyoto（南禅寺周边）
    "kyo_gion_higashiyama_fufu_kyoto": {
        "tier": "b6",  # 高级旅馆全室温泉
        "price_cny_per_night": [2200, 3500],
        "depth": "full",
        "可信度": "cross_checked",
        "数据来源": [
            "https://www.fufujapan.jp/",
            "https://www.tripadvisor.com/Hotel_Review-g298564-d23218091-Reviews-FUFU_KYOTO-Kyoto_Kyoto_Prefecture_Kinki.html",
        ],
        "最后核实": TODAY,
        "note": {
            "店名": "FUFU 京都（ふふ 京都）",
            "简介": "2021 年开业·南禅寺旁琵琶湖疏水沿·40 间客房·全 6 种房型从 45㎡（Comfort Twin Suite）到 91㎡（Luxury Premium Suite·望大文字山）。所有客室含天然源泉·檜風呂泡汤·设计 by Saiun Design 东京。FUFU Japan 系列（含热海·日光·奈良 by 隈研吾）·小型奢华度假村。Tripadvisor 部分点评提到 hospitality 经验偏年轻·但料理和庭园评价稳定。",
            "亮点": ["温泉度假", "南禅寺立地", "全室天然温泉檜風呂", "FUFU 系列小型奢华", "大文字山景"],
            "地址": "京都市左京区·琵琶湖疏水沿·南禅寺徒步 5 分·京都市役所前站徒步 15 分",
            "房型": "Comfort Twin Suite 45㎡ ~ Luxury Premium Suite 91㎡（共 6 种）",
            "含早": "和食朝食含",
            "价格": "夕朝食付 2 人 ¥80,000～¥150,000（人均 ¥1,800-3,500）·樱花红叶季 +30%",
            "预约": "公式 fufujapan.jp / 一休 / 楽天·提前 60 天最优",
            "到店提醒": "Check-in 15:00 / Check-out 11:00·全室温泉建议樱花红叶季·疏水歩道散步推荐",
        },
        "_area_override": "higashiyama",  # 南禅寺归 higashiyama 更准
    },
    # FUFU 奈良（隈研吾设计）
    "nra_nara_park_area_fufu_nara": {
        "tier": "b5",
        "price_cny_per_night": [1700, 2800],
        "depth": "full",
        "可信度": "cross_checked",
        "数据来源": [
            "https://www.fufujapan.jp/",
            "https://www.ikyu.com/en-us/00002739/",
        ],
        "最后核实": TODAY,
        "note": {
            "店名": "FUFU 奈良（ふふ 奈良）",
            "简介": "隈研吾设计·30 间套房全室竹林包围露天风吕·近铁奈良駅徒步 20 分（高畑町）。东大寺/兴福寺/春日大社 walking distance·奈良公园近邻。地下源泉直达 42°C 恒温·「和漢の湯」含日本当归・艾草・生姜等十余种和漢植物。设计极重隐私·Utility Box 让 staff 静默更换·几乎不与他客遭遇。一休回头客评：「这是我真正喜欢的住宿」。",
            "亮点": ["温泉度假", "全室竹林露天风吕", "隈研吾设计", "和漢源泉", "极致隐私"],
            "地址": "奈良市高畑町 1184-1·近铁奈良駅徒步 20 分·东大寺徒步 8 分",
            "房型": "30 间套房·全室带露天风吕·部分含半露天",
            "含早": "和食朝食含·屋内 OR 个室",
            "价格": "夕朝食付 2 人 ¥60,000～¥120,000（人均 ¥1,500-3,000）·樱花/红叶旺季 +30%",
            "预约": "公式 / 一休·提前 90 天樱花季",
            "到店提醒": "Check-in 15:00 / Check-out 11:00·全室温泉·近铁/JR 奈良站有送迎",
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

        # area override
        if "_area_override" in patch:
            h["area"] = patch["_area_override"]
            # id 同步重命名（拆 prefix_area_slug）
            parts = hid.split("_", 2)
            if len(parts) >= 3:
                cur_area = h.get("area", "")  # 已被改成新值
                # 找回旧 area: 从 hid 抽
                # 更直接：用 patch 提供的 area 重组
                # 但这里 hid 里的 area 段可能跟 area 字段不一致(slugify 后)·跳过 id 改
                pass

        # 应用其他字段
        for k, v in patch.items():
            if k.startswith("_"):
                continue
            h[k] = v

        updated += 1

    # 删除重复
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
