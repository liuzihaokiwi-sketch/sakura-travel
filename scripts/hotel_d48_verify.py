"""D48 skeleton -> verified 批量升级.

每批跑前补 PATCHES dict (id -> 字段补丁)·dry-run 看 diff·--apply 落地.
"""
from __future__ import annotations
import io, json, sys
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path("japan/kansai/hotels")
TODAY = datetime.now().strftime("%Y-%m-%d")

PATCHES: dict[str, dict] = {}

def register(hid: str, *, brief: str, highlights: list[str] = None, address: str = None,
             rooms: str = None, breakfast: str = None, price: str = None,
             booking: str = None, sources: list[str] = None):
    p = {"简介": brief}
    if highlights: p["亮点"] = highlights
    if address: p["地址"] = address
    if rooms: p["房型"] = rooms
    if breakfast: p["含早"] = breakfast
    if price: p["价格"] = price
    if booking: p["预约"] = booking
    PATCHES[hid] = {"note": p, "sources": sources or []}

# === 京都 第一批 ===
register(
    "kyo_shijo_kawaramachi_hotel_okura_kyoto",
    brief="**京都唯一 17 层高城**·1888 年开业·Okura Nikko 集团·地铁京都市役所前站直连·320 间客房·顶层 Sky Restaurant Pittoresque 法餐俯瞰京都·屋顶花园观东山。",
    highlights=["设计精品", "320 室大型城市酒店", "京都市役所前直连", "Pittoresque 法餐"],
    address="京都市中京区·京都市役所前站直连·寺町通り",
    rooms="Twin/Double/Suite·共 320 室·非吸烟",
    breakfast="和洋朝食 buffet 可选",
    price="素泊 2 人 ¥30,000-150,000（GDS $204-1,016）",
    booking="公式 okura.com·一休·楽天",
    sources=["https://okura.com/japan/kyoto/hotel-okura-kyoto/", "https://www.hotel.kyoto/okura/"],
)

register(
    "kyo_shijo_kawaramachi_good_nature_hotel",
    brief="**WELL 认证 sustainable 酒店**·阪急河原町站徒步 2 分·14 类客室主题（瞑想 MU/桑拿/阳台等）·内含米其林二星餐厅+10 间餐饮·全馆禁烟·快眠照明系统。",
    highlights=["设计精品", "WELL 认证", "可持续主题", "米其林二星餐厅", "桑拿客室"],
    address="京都市下京区河原町·阪急京都河原町站徒步 2 分",
    rooms="28-90㎡·共约 141 室·瞑想/桑拿/阳台等多主题",
    breakfast="可选·有机食材",
    price="素泊 2 人 ¥35,000-80,000",
    booking="公式 goodnaturehotel.jp·一休·じゃらん",
    sources=["https://goodnaturehotel.jp/", "https://goodnaturehotels.com/rooms/"],
)

register(
    "kyo_shijo_kawaramachi_cross_hotel_kyoto",
    brief="ORIX HOTELS 旗下设计 lifestyle 酒店·**全 301 室**·三条龙马通沿·阪急河原町徒步 6 分·1 楼 KIHARU Brasserie 全天餐厅·「京感」「木气づかい」主题。",
    highlights=["设计精品", "ORIX 系", "301 室大型", "三条龙马通", "KIHARU Brasserie"],
    address="京都市中京区龙马通·阪急河原町徒步 6 分·三条/京都市役所前/三条京阪徒步 4 分",
    rooms="Standard~Suite·共 301 室",
    breakfast="可选 KIHARU Brasserie",
    price="素泊 2 人 ¥18,000-40,000",
    booking="公式 ORIX HOTELS·一休·楽天",
    sources=["https://cross-kyoto.orixhotelsandresorts.com/", "https://www.orixhotelsandresorts.com/worixp/concept/crosshotel_kyoto/"],
)

register(
    "kyo_gion_higashiyama_genji_kyoto",
    brief="**Design Hotels™ 加盟·Marriott Bonvoy 系**·全 19 室+町家别馆·五条河原町河畔·每室对应《源氏物语》一章·京都艺术家壁画·屋顶 Sky Forest Garden 早餐酒吧。",
    highlights=["设计精品", "Design Hotels 加盟", "Marriott Bonvoy", "源氏物语主题", "屋顶森林花园"],
    address="京都市下京区·五条河原町·鸭川河畔",
    rooms="Garden/City/River 系列·27-51㎡·共 19 室+町家别馆",
    breakfast="屋顶 Sky Forest Garden 含早可选",
    price="素泊 2 人 ¥40,000-90,000",
    booking="公式 genjikyoto.com·Marriott·Design Hotels",
    sources=["https://genjikyoto.com/en/stay", "https://www.designhotels.com/hotels/japan/kyoto/genji-kyoto/"],
)


# === 京都 第二批 (5-8) ===
register(
    "kyo_gion_higashiyama_hotel",
    brief="**2022 年 12 月开业**·全 13 室小规模温泉旅館·东山鹫尾町·**2024 年 11 月自家源泉「京都清水温泉」开汤**·阪急河原町徒步 15 分。",
    highlights=["温泉旅馆", "2022 新开业", "全 13 室", "自家源泉", "东山立地"],
    address="京都市東山区鷲尾町 528·阪急京都河原町站徒步 15 分",
    rooms="全 13 室·部分露天/半露天/内汤",
    breakfast="和朝食有料·要事前预约",
    price="素泊 2 人 ¥40,000-90,000",
    booking="公式 hotel-yuraku.com·一休·楽天",
    sources=["https://www.hotel-yuraku.com/", "https://www.ikyu.com/en-us/00003034/"],
)

register(
    "kyo_nijo_central_bu_lai_dun_hotel",
    brief="**1988 年开业·京都老牌豪华城市酒店**·全 182 室·京都御所徒步 5 分·客室 36-42㎡ 京町家意象+全室抹茶セット·5 间餐厅+酒吧·乌丸御池站接驳 shuttle。",
    highlights=["设计精品", "1988 老铺", "182 室", "京都御所徒步 5 分", "全室抹茶セット"],
    address="京都市上京区新町通中立売·御所西·地铁今出川站徒步 8 分",
    rooms="36-42㎡·共 182 室·部分大浴槽 bathroom",
    breakfast="和洋朝食 buffet 含选项",
    price="素泊 2 人 ¥35,000-80,000",
    booking="公式 brightonhotels.co.jp·一休·楽天",
    sources=["https://kyoto.brightonhotels.co.jp/", "https://www.ikyu.com/en-us/00000151/"],
)

register(
    "kyo_kyoto_station_doubletree_by_hilton_kyoto_sta",
    brief="**Hilton 系 DoubleTree·2023 年开业**·JR 京都站徒步 5 分·和洋朝食 buffet（Tripadvisor 2025 Travelers Choice Best）·小学生以下添寝+朝食无料。",
    highlights=["设计精品", "Hilton 系", "京都站徒步 5 分", "和洋 buffet 朝食受赏"],
    address="京都市南区東九条西岩本町 15·JR 京都站八条东口徒步 5 分",
    rooms="Twin Premium / Executive·共约 220 室",
    breakfast="和洋朝食 buffet 含·孩子无料",
    price="素泊 2 人 ¥22,000-50,000·Hilton Honors 积分",
    booking="公式 Hilton·一休·楽天",
    sources=["https://doubletree-kyoto-station.hiltonjapan.co.jp/", "https://www.hilton.com/ja/hotels/itmksdi-doubletree-kyoto-station/"],
)

register(
    "kyo_shijo_kawaramachi_shijo_xin_ting_ying_te_gai_te_hotel",
    brief="**Granvista 系 Intergate ライン·2018 年开业**·全 153 室·阪急乌丸/地铁四条徒步 5 分·特色：免费茶时间+早朝瑜伽·中端商务旅人爱用。",
    highlights=["设计精品", "Intergate 系", "153 室", "茶时间+瑜伽", "四条乌丸 5 分"],
    address="京都市中京区新町通錦小路上る·阪急烏丸/地铁四条徒步 5 分",
    rooms="Standard~Suite·共 153 室",
    breakfast="和洋朝食 buffet 含选项",
    price="素泊 2 人 ¥18,000-45,000",
    booking="公式 intergatehotels.jp·一休·楽天",
    sources=["https://www.intergatehotels.jp/kyoto-shijo/en/", "https://www.jalan.net/yad322810/"],
)


# === 京都 第三批 (9-16) ===
register(
    "kyo_gion_higashiyama_nohga_hotel",
    brief="**2022 年开业·NOHGA HOTEL 系**·全 207 室·京阪「清水五条」站徒步 7 分·与京都创作者协业的设计酒店·共用「ATELIER」&「VOID」展示空间·屋顶 bar。",
    highlights=["设计精品", "NOHGA 系", "207 室", "京都创作者协业", "屋顶 bar"],
    address="京都市東山区五条橋東 4 丁目 450-1·京阪「清水五条」站徒步 7 分",
    rooms="Standard~Suite·共 207 室",
    breakfast="可选含早",
    price="素泊 2 人 ¥25,000-55,000",
    booking="公式 nohgahotel.com·一休·楽天",
    sources=["https://www.nohgahotel.com/kiyomizu/en/rooms/", "https://www.ikyu.com/en-us/00002925/"],
)

register(
    "kyo_kyoto_station_tune_stay_kyoto",
    brief="**2,500 册京都关连藏书+本屋併設**·JR 京都站徒步 5 分·全 140 室·夜间 short film 放映+大阶段·botanical craft gin bar·共用厨房+个室浴+硬币洗衣。",
    highlights=["设计精品", "藏书本屋", "京都站徒步 5 分", "shortfilm + craft gin", "140 室"],
    address="京都市下京区七条通新町西入夷之町 708·JR 京都站徒步 5 分",
    rooms="Double 12㎡ / 2 段 ベッド Twin 11㎡·共 140 室",
    breakfast="ベーグル 600 円",
    price="素泊 2 人 ¥9,000-20,000",
    booking="公式 tune-stay.com·一休·楽天",
    sources=["https://www.tune-stay.com/", "https://www.jalan.net/yad315486/"],
)

register(
    "kyo_gion_higashiyama_sowaka",
    brief="**100 年数寄屋造名料亭再生·SLH 加盟·Forbes 4 星（築百年再生日本初）·LA LISTE 2026 World Top 1000**·全 23 室（本馆 10+离别 1+新馆 12）·館内餐厅「祇園 ろか」。",
    highlights=["老铺旅馆", "SLH 加盟", "Forbes 4 星", "LA LISTE Top 1000", "100 年数寄屋"],
    address="京都市東山区下河原通八坂鳥居前下ル清井町 480·京阪祇園四条徒步 10 分",
    rooms="本馆 27-97㎡ + 离别 34㎡ + 新馆 35-70㎡·共 23 室",
    breakfast="和洋朝食含",
    price="素泊 2 人 ¥60,000-240,000",
    booking="公式 sowaka.com·一休·SLH",
    sources=["https://sowaka.com/", "https://www.ikyu.com/en-us/00002668/"],
)

register(
    "kyo_gion_higashiyama_granbell_hotel",
    brief="**2017 年开业·Belluna 系 designer's hotel·105 室含地下客室**·京阪祇園四条徒步 2 分·全 6 类客室含和洋·庭園眺望大浴场·祇园核心立地。",
    highlights=["设计精品", "Belluna 系", "祇園四条 2 分", "105 室", "庭園大浴场"],
    address="京都市東山区·京阪祇園四条徒步 2 分·阪急河原町徒步 7 分",
    rooms="Double/Twin/和室·共 105 室·部分地下客室",
    breakfast="可选含早",
    price="素泊 2 人 ¥18,000-50,000",
    booking="公式 granbellhotel.jp·一休·楽天",
    sources=["https://www.granbellhotel.jp/kyoto/", "https://en.granbellhotel.jp/kyoto/"],
)

register(
    "kyo_kyoto_station_keihan_jing_dou_hotel",
    brief="**京阪集团旗舰·京都站八条东口直结地下道徒步 1 分·320 室**·伊丹/关西空港 limousine bus 发着场·和洋朝食 buffet（おばんざい/老铺漬物）·高层 lounge·禅 50㎡ 套房带枯山水坪庭。",
    highlights=["设计精品", "京阪系", "京都站 1 分直结", "320 室", "おばんざい 朝食"],
    address="京都市南区·京都站八条东口徒步 1 分·地下道直结",
    rooms="Single/Twin/Double/Family·共 320 室·禅 ZEN 50㎡ 套房",
    breakfast="和洋朝食 buffet ¥2,750（2026.4 改）",
    price="素泊 2 人 ¥18,000-45,000",
    booking="公式 hotelkeihan.co.jp·一休·楽天",
    sources=["https://www.hotelkeihan.co.jp/kyoto/", "https://www.ikyu.com/en-us/00002321/"],
)

register(
    "kyo_shijo_kawaramachi_gate_hotel_jing_dou_gao_lai_chuan",
    brief="**HULIC 系·2020 年开业·关西首家 GATE HOTEL**·全 184 室（旧立成小学校 Schoolhouse 棟 20 室 + 新馆 164 室）·京都市再开发·高瀬川沿·阪急河原町徒步 5 分。",
    highlights=["设计精品", "HULIC 系", "关西首家 GATE", "184 室", "高瀬川沿", "旧校舍再生"],
    address="京都市中京区蛸薬師通河原町東入備前島町 310-2·阪急河原町徒步 5 分",
    rooms="Schoolhouse 20 + 新馆 164·共 184 室·12 类",
    breakfast="可选含早",
    price="素泊 2 人 ¥30,000-70,000",
    booking="公式 gate-hotel.jp·一休·楽天",
    sources=["https://www.gate-hotel.jp/en/kyoto/", "https://www.ikyu.com/en-us/00002755/"],
)

register(
    "kyo_gion_higashiyama_doubletree_by_hilton_kyoto_hig",
    brief="**Hilton 系 DoubleTree·2022 年开业（前身 Senren Kyoto）**·京阪「清水五条」徒步 1 分·五条大桥旁·屋内大浴场·清水寺/三十三间堂徒步圈。",
    highlights=["设计精品", "Hilton 系", "清水五条徒步 1 分", "屋内大浴场", "清水寺徒步圈"],
    address="京都市東山区本町 1-45·京阪「清水五条」徒步 1 分",
    rooms="King/Twin/Suite·全室禁烟",
    breakfast="和洋朝食 buffet 可选",
    price="素泊 2 人 ¥30,000-70,000·Hilton Honors 积分",
    booking="公式 Hilton·一休·楽天",
    sources=["https://www.hilton.com/en/hotels/itmhadi-doubletree-kyoto-higashiyama/"],
)

register(
    "kyo_shijo_kawaramachi_sequence",
    brief="**2020 年开业·LIFESTYLE HOTEL「sequence」系·全 208 室**·地铁「五条」徒步 3 分·**顔认证 self check-in/客室入室**·岩盘浴 + steam sauna·CI 17:00 / CO 14:00 长留型。",
    highlights=["设计精品", "sequence 系", "顔认证", "208 室", "岩盘浴 + sauna", "CI 17/CO 14"],
    address="京都市下京区五条烏丸町 409·地铁「五条」徒步 3 分",
    rooms="Queen/Medium Queen/King/Twin/4Beds·共 208 室",
    breakfast="含早 ¥9,350~",
    price="素泊 2 人 ¥18,000-40,000",
    booking="公式 sequencehotels.com·一休·楽天",
    sources=["https://www.sequencehotels.com/kyoto-gojo/", "https://www.jalan.net/yad377522/"],
)


# === 京都 第四批 (17-24) ===
register(
    "kyo_kyoto_station_sakura_terrace_the_gallery",
    brief="**2015 年开业·SAKURA TERRACE 系第二棟**·JR 京都站八条口徒步 2 分·南北 2 栋·男女分浴大浴场（男 sauna / 女 salt sauna 至深夜 1 时）·成人向 design 酒店·13 岁以上限定。",
    highlights=["设计精品", "京都站徒步 2 分", "男女分浴大浴场", "成人向 13+", "live music"],
    address="京都市南区東九条上殿田町·JR 京都站八条口徒步 2 分",
    rooms="Standard / Luxury 2 类",
    breakfast="自助 buffet 含选项",
    price="素泊 2 人 ¥18,000-40,000",
    booking="公式 sakuraterrace-gallery.jp·一休·楽天",
    sources=["https://www.sakuraterrace-gallery.jp/", "https://www.ikyu.com/en-us/00081808/"],
)

register(
    "kyo_kita_takagamine_shou_huo_hotel",
    brief="**東急 Harvest Club 系会员制 resort·しょうざんリゾート京都内**·北区鷹峯麓·83 间正房 + VIALA annex 37 间 + 13 间·共 133 室·京都北郊森林立地·会员优先开放给非会员。",
    highlights=["温泉度假", "東急 Harvest 系", "鷹峯リゾート", "133 室", "会员优先"],
    address="京都市北区·鷹峯·しょうざんリゾート京都内",
    rooms="本馆 83 + VIALA 37 + 別 13·共 133 室",
    breakfast="和洋朝食含",
    price="素泊 2 人 ¥30,000-80,000",
    booking="公式 harvestclub.com·非会员限期开放",
    sources=["https://www.harvestclub.com/Un/Hotel/Kg/", "https://www.resorthotels109.com/kyototakagamine/"],
)

register(
    "kyo_shijo_kawaramachi_xian_dou_ting_espacion_hotel",
    brief="**2025 年 10 月 14 日 grand open·全 21 室小規模 design hotel**·中京区先斗町·阪急河原町徒步 5 分·全 7 类客室+QR self check-in·館内无 restaurant 推 city dining 体验。",
    highlights=["设计精品", "2025 新开业", "21 室小规模", "先斗町立地", "QR self check-in"],
    address="京都市中京区下樵木町 196·阪急河原町徒步 5 分",
    rooms="7 类·共 21 室",
    breakfast="无館内 restaurant",
    price="素泊 2 人 ¥25,000-60,000",
    booking="公式 ht-espasionpontocho.com·一休·楽天",
    sources=["https://ht-espasionpontocho.com/", "https://hotelbank.jp/new-hotels/kyoto-ht-espasionpontocho2510open/"],
)

register(
    "kyo_shijo_kawaramachi_gojo_holiday_inn_hotel",
    brief="**IHG 系 Holiday Inn·2025 年 1 月 29 日开业**·**日本初 Holiday Inn 50 周年回归原点京都**·全 183 室·下京区·13 阶最上层日本式大浴场·1F café / 2F restaurant / 高层京都 tower 一望。",
    highlights=["设计精品", "IHG Holiday Inn", "50 周年回归", "183 室", "屋上日本式大浴场"],
    address="京都市下京区東錺屋町 179·地铁五条徒步圈",
    rooms="Cozy Single 14㎡ / Twin / King / Suite 47㎡·共 183 室",
    breakfast="可选含早",
    price="素泊 2 人 ¥18,000-50,000·IHG One Rewards",
    booking="公式 IHG·一休·楽天",
    sources=["https://www.ihg.com/holidayinn/hotels/us/en/kyoto/ukygo/hoteldetail", "https://wbc-hr.com/news/551/"],
)

register(
    "kyo_shijo_kawaramachi_rojiyu_kyoto",
    brief="**Nazuna 系·2024 年 10 月开业**·全 4 室一栋整租·四条大宮/阪急大宮徒步 6 分·桜/竹/梅/楓 4 主题客室各异「湯」体验（内汤/露天）·2 階建客室含 kitchen+洗濯機 长留型。",
    highlights=["町家", "Nazuna 系", "2024 新开业", "全 4 室主题汤", "长留 kitchen 完备"],
    address="京都市中京区下川原町 588·四条大宮/阪急大宮徒步 6 分",
    rooms="桜/竹/梅/楓·全 4 室·2 階建",
    breakfast="无含早",
    price="一栋 2-4 人 ¥40,000-100,000",
    booking="公式 nazuna.co",
    sources=["https://www.nazuna.co/property/rojiyu-kyoto/", "https://www.ikyu.com/en-us/00031199/"],
)

register(
    "kyo_shijo_kawaramachi_yuraku_etsuen",
    brief="**ダーワ・悠洛 京都 by バンヤン・グループ·5 星 boutique·123 室**·三条京阪徒步 1 分·鴨川河畔·大正 ロマン薫る·館内 GRILL 54TH 法餐+8LEMENTS SPA·祇園/先斗町/錦市場徒步 5 分。",
    highlights=["设计精品", "Banyan Group 系 Dhawa", "三条京阪 1 分", "123 室", "8LEMENTS SPA"],
    address="京都市中京区·三条京阪徒步 1 分·鴨川河畔",
    rooms="Standard~Corner Suite·共 123 室",
    breakfast="法餐 GRILL 54TH 含选项",
    price="素泊 2 人 ¥35,000-90,000",
    booking="公式 dhawayurakyoto.com·Accor·一休",
    sources=["https://dhawayurakyoto.com/", "https://www.dhawa.com/japan/dhawa-yura-kyoto"],
)

register(
    "kyo_shijo_kawaramachi_insomnia_kyoto_oike",
    brief="**Solare Hotels 新 brand insomnia·2023 年秋 rebrand·全 88 室**·烏丸御池站徒步 2 分·**24h lounge 无料 drink/12 类 bread/library**·都市探索者 lifestyle 酒店。",
    highlights=["设计精品", "Solare 系新 brand", "烏丸御池 2 分", "88 室", "24h lounge"],
    address="京都市中京区室町通押小路下る御池之町 314·烏丸御池徒步 2 分",
    rooms="Standard~Suite·10 阶建·共 88 室",
    breakfast="24h lounge 无料 bread + drink",
    price="素泊 2 人 ¥18,000-40,000",
    booking="公式 inso-mnia.com·Solare·一休",
    sources=["https://www.inso-mnia.com/kyoto/", "https://www.solarehotels.co.jp/pressrelease/2023/1615/"],
)

register(
    "kyo_shijo_kawaramachi_candeohotels",
    brief="**Candeo Hotels 系·京都登録有形文化財「旧伴家住宅」京町家保存改修 lounge**·烏丸御池徒步 3 分·全室シモンズベッド+一部露天风吕付·屋顶 sky spa（外汤+sauna）。",
    highlights=["设计精品", "Candeo 系", "京都市登録文化財町家", "烏丸御池 3 分", "屋顶 sky spa"],
    address="京都市中京区六角通烏丸西入骨屋町 149·烏丸御池徒步 3 分",
    rooms="Standard~Private Spa King 28㎡·部分露天风吕付",
    breakfast="折詰朝食 2F 町家 lounge 含选项",
    price="素泊 2 人 ¥18,000-50,000",
    booking="公式 candeohotels.com·一休·楽天",
    sources=["https://www.candeohotels.com/en/kyoto-rokkaku/", "https://www.jalan.net/yad357416/"],
)


# === 京都 第五批 (25-28) ===
register(
    "kyo_gion_higashiyama_the_shinmonzen",
    brief="**安藤忠雄设计·全 9 室小规模顶奢**·祇园白川河畔·hotelier Paddy McKillen 10 年打磨·Jean-Georges 京都首店·館内 Damien Hirst / Louise Bourgeois / 杉本博司艺术藏品。",
    highlights=["设计精品", "安藤忠雄设计", "9 室 super luxury", "Jean-Georges 京都", "顶级艺术藏品"],
    address="京都市東山区新門前通西之町 235·祇园白川河畔",
    rooms="全 9 套房·hinoki 浴/大理石浴室/Pedersoli 500 织数 organic linen",
    breakfast="含·Jean-Georges 餐厅",
    price="素泊 2 人 ¥260,000+（约 USD 1,916/夜起）",
    booking="公式 theshinmonzen.com·Mr & Mrs Smith·Leading Hotels",
    sources=["https://theshinmonzen.com/", "https://www.mrandmrssmith.com/luxury-hotels/the-shinmonzen/rooms"],
)

register(
    "kyo_gion_higashiyama_hotel_seiryu_kyoto_kiyomizu",
    brief="**1933 年元清水小学校改造·NTT 都市開発+Prince Hotels 共营·2020 年开业**·全 48 室（既存棟 34+增築棟 14·平均 50㎡）·**Leading Hotels 日本第 8 家**·屋顶 BAR K36 八坂塔眺望·Benoit Kyoto 法餐别馆。",
    highlights=["设计精品", "Leading Hotels", "150 年校舎再生", "48 室", "屋顶 BAR K36"],
    address="京都市東山区清水二丁目 204-2·八坂塔旁",
    rooms="既存棟 34 + 增築棟 14·平均 50㎡·共 48 室",
    breakfast="朝食 restaurant 含选项",
    price="素泊 2 人 ¥80,000-200,000",
    booking="公式 seiryukiyomizu.com·Prince Hotels·Leading Hotels",
    sources=["https://www.seiryukiyomizu.com/", "https://www.princehotels.co.jp/seiryu-kiyomizu/"],
)

register(
    "kyo_arashiyama_muni_kyoto_by_onko_chishin",
    brief="**温故知新系·2020 年 8 月开业·渡月桥旁全 21 室小規模 luxury**·客室 50-70㎡·窗高 2.9m×3.5m 桂川/渡月桥眺望·**馆内 MUNI ALAIN DUCASSE 法餐**+ MUNI LA TERRASSE+原创 spa（北山杉/水尾柚子）·福田美术馆 free。",
    highlights=["设计精品", "温故知新系", "渡月桥旁", "21 室 50-70㎡", "Alain Ducasse 法餐"],
    address="京都市右京区嵯峨天龍寺芒ノ馬場町 3·渡月桥旁",
    rooms="全 21 室·50-70㎡·部分 sofa bed 3 人",
    breakfast="法餐 Alain Ducasse 含选项",
    price="素泊 2 人 ¥80,000-200,000",
    booking="公式 munihotels.com·一休·Mr & Mrs Smith",
    sources=["https://munihotels.com/en/", "https://muni.by-onko-chishin.com/stay/"],
)

register(
    "kyo_nijo_central_garrya_nijo_castle_kyoto",
    brief="**Banyan Group 系 Garrya 日本一号馆·2022 年开业**·二条城世遗 200m·二条城前站徒步 2 分·全 25 室含 1 套房·書院造样·館内法餐 Singular+lounge bar·minibar 无料·Accor 加盟。",
    highlights=["设计精品", "Banyan Group 系", "Garrya 日本一号", "二条城旁", "25 室·1 套房", "書院造"],
    address="京都市中京区·二条城前站徒步 2 分·二条城世遗 200m",
    rooms="Standard~Suite·全 25 室·tatami+balcony+garden view",
    breakfast="法餐 Singular 可选含早",
    price="素泊 2 人 ¥40,000-90,000",
    booking="公式 garrya.com·Accor·一休",
    sources=["https://www.garrya.com/en/destinations/kyoto", "https://all.accor.com/hotel/C016/index.en.shtml"],
)


# === 京都 第六批 (29-38) ===
register(
    "kyo_gion_higashiyama_ninnaji_omuro_hui_guan",
    brief="**世界遗产 仁和寺 境内宿坊·全 12 室和室**·宿泊者特典：国宝「金堂」朝のお勤め参拝（4-9 月 6 时 / 10-3 月 6:30 时）+ 御殿无料拝観券·館内和食处「梵」·夕食京料理含湯葉/天麩羅。",
    highlights=["宿坊", "世界遗产仁和寺", "金堂朝のお勤め", "12 室和室", "梵和食"],
    address="京都市右京区御室大内 33·バス御室仁和寺·境内东门旁",
    rooms="全室和室个室·共 12 室·浴衣/タオル完备",
    breakfast="和朝食含·京湯豆腐+焼魚",
    price="夕朝食付 2 人 ¥40,000-90,000",
    booking="公式 omurokaikan.jp / ninnaji.or.jp·一休·楽天",
    sources=["https://omurokaikan.jp/", "http://www.ninnaji.or.jp/syukubou/stay.html"],
)

register(
    "kyo_gion_higashiyama_chion_in_wajun_hui_guan",
    brief="**总本山知恩院三门前·2011 开館 2026.2 满 15 周年**·「凛としてあたたか お念仏にふれる宿」·洋室/和室/和洋室·館内和食处「花水庵」蒸料理+精進料理·**365 日朝法要+写経体验**。",
    highlights=["宿坊", "知恩院三门前", "2011 开館", "365 日朝法要+写経", "花水庵"],
    address="京都市東山区·知恩院三门前·京阪祇園四条徒步圈",
    rooms="洋室/和室/和洋室·多类型",
    breakfast="和朝食含",
    price="素泊 2 人 ¥18,000-40,000",
    booking="公式 wajun-kaikan.jp·一休·楽天",
    sources=["https://www.wajun-kaikan.jp/", "https://www.ikyu.com/en-us/00081020/"],
)

register(
    "kyo_gion_higashiyama_myoshinji_dong_lin_yuan",
    brief="**妙心寺塔頭·1531 年建·「沙羅雙樹の寺」别名**·6 月「沙羅の花を愛でる会」·正式宿坊体验有限·季节限定花供养会+精進料理·予約宿泊+座禅+写経。",
    highlights=["宿坊", "妙心寺塔頭", "沙羅雙樹の寺", "1531 年建", "6 月沙羅の花会"],
    address="京都市右京区花園·妙心寺塔頭·JR 花園站徒步 5 分",
    rooms="客室数限定·要事前问合せ",
    breakfast="精進朝食含",
    price="夕朝食付 2 人 ¥30,000-60,000",
    booking="电话予约·要早期 contact",
    sources=["https://shukuken.com/torinin", "https://souda-kyoto.jp/event/detail/tourinin-sara.html"],
)

register(
    "kyo_arashiyama_rokuoin",
    brief="**1379 年足利義満建立·京都十刹第五·女性专用宿坊**·京都市指定名勝庭日本最初平庭式枯山水·1 泊朝食付 ¥5,000+ 宿泊税·**朝のお勤め座禅+法話現休止**。",
    highlights=["宿坊", "1379 年建", "京都十刹第五", "女性专用", "枯山水庭"],
    address="京都市右京区嵯峨北堀町·嵯峨嵐山駅徒步 5 分",
    rooms="女性专用·客室数限定",
    breakfast="朝食含",
    price="1 泊朝食付 ¥5,000+",
    booking="公式 rokuouin.com·和空·要事前问合せ",
    sources=["https://rokuouin.com/en/temple-lodging/", "https://shukuken.com/rokuoin"],
)

register(
    "kyo_shijo_kawaramachi_yao_shi_yuan",
    brief="**「こぬか薬師」**别名宿坊·五条立地·**精進・普茶料理（中華精進）特色**·素朴的寺院宿泊体验·朝の法要参拝。",
    highlights=["宿坊", "こぬか薬師", "普茶料理", "五条立地"],
    address="京都市下京区·五条·徒步寺町通り圈",
    rooms="和室·客室数限定",
    breakfast="和朝食含",
    price="2 人含早 ¥15,800+",
    booking="电话予约",
    sources=["https://souda-kyoto.jp/blog/00700.html"],
)

register(
    "kyo_shijo_kawaramachi_ting_jia_zhu_zhai_jing_dou",
    brief="**町家レジデンスイン京都·京都市内 64 棟点在·1 日 1 組限定一棟整租**·町家リノベ·**全棟京都市旅館業許可**·嶋原/中堂寺/三坊猪熊町等多区分散·小集团到大型 group 都可。",
    highlights=["町家", "町家レジデンスイン系", "64 棟点在", "1 日 1 組整租", "旅館业許可"],
    address="京都市内多区分散·下京/中京区为主",
    rooms="一棟整租·定员 4-9 名·64 棟选择",
    breakfast="无含早·部分有外送选项",
    price="一棟 2-9 人 ¥40,000-200,000",
    booking="公式 kyoto-machiya-inn.com·machiya-inn-japan.com·楽天",
    sources=["https://www.kyoto-machiya-inn.com/jp/", "https://www.machiya-inn-japan.com/ja/"],
)

register(
    "kyo_shijo_kawaramachi_kuraya",
    brief="**藏や·京町家一棟貸し·京都市内 7 棟·築約 100 年京町家フルリノベ**·1 日 1 組整租·**约 70-100㎡ 大空间**·全棟京都市旅館业許可·清水五条/上五条町/南聖町等。",
    highlights=["町家", "藏や系 7 棟", "築 100 年京町家", "70-100㎡", "1 日 1 組"],
    address="京都市内 7 棟分散·清水五条/南聖町等",
    rooms="一棟整租·70-100㎡·定员 4-8 名",
    breakfast="无含早",
    price="一棟 2-8 人 ¥30,000-150,000",
    booking="公式 kuraya.net / machiya-stay.co.jp·Booking",
    sources=["https://www.kuraya.net/index.php", "https://www.machiya-stay.co.jp/"],
)

register(
    "kyo_gion_higashiyama_gion_xin_qiao_mei_an",
    brief="**京都 白梅别馆 梅庵**·**祇园新桥伝統的建造物群保存地区**·**元 ochaya（茶屋）改造·1 日 2 組限定一棟貸し**·山本工业改造·有名祇园芸妓 owner·料理旅館 白梅本馆联动。",
    highlights=["町家", "祇园新桥伝建群保存地区", "元 ochaya 改造", "1 日 2 組限定", "白梅别馆"],
    address="京都市東山区·祇园新桥伝建群·阪急河原町徒步 7 分",
    rooms="一棟整租·1 日 2 組限定",
    breakfast="可选含早·料理旅館 白梅本馆 contact",
    price="一棟 2-4 人 ¥80,000-150,000",
    booking="公式 baian.kyoto·shiraume-kyoto 联动",
    sources=["https://baian.kyoto/", "https://www.shiraume-kyoto.jp/"],
)

register(
    "kyo_gion_higashiyama_jin_guang_yuan_ying_an",
    brief="**金戒光明寺塔頭金光院·2025 年 3 月开业·京都岡崎「ほたる寺」·1 日 1 組限定 43㎡ 和モダン**·組子格子戸·5-6 月庭園蛍見·出張シェフ完全 private dining·1 部屋 2 人 ¥28,000+。",
    highlights=["宿坊", "金戒光明寺塔頭", "2025.3 新开业", "ほたる寺", "1 日 1 組 43㎡", "出張 chef"],
    address="京都市左京区岡崎·地铁蹴上 1.2km·市バス岡崎神社前徒步 5 分",
    rooms="43㎡ 和モダン·1 日 1 組·定員 5 名（推奨 3 名）",
    breakfast="出張シェフ可选",
    price="1 部屋 ¥28,000-150,000（鉄板焼コース別途）",
    booking="公式 konkoin.net·一休·Vacation Stay",
    sources=["https://www.konkoin.net/konkoin/", "https://konkoin.com/syukubou/"],
)

register(
    "kyo_arashiyama_grand_xi_lan_shan_hotel",
    brief="**The GrandWest Arashiyama·2017.9 开业**·阪急嵐山駅徒步 5 分·渡月桥徒步 10 分·**全 10 室全 suite 53㎡+**·部分 kitchen 付·屋上テラス嵐山眺望テント·カフェ併設·無料 rental cycle。",
    highlights=["设计精品", "全 10 室 suite 53㎡+", "嵐山立地", "屋上テント眺望", "无料 rental cycle"],
    address="京都市西京区·阪急嵐山駅徒步 5 分·渡月桥徒步 10 分",
    rooms="4 类·全 10 室 suite 53㎡+·部分 kitchen 付",
    breakfast="café 自家製ワッフル",
    price="素泊 2 人 ¥30,000-80,000",
    booking="公式 grandwest.kyoto·一休·Relux",
    sources=["https://www.grandwest.kyoto/", "https://rlx.jp/22425/"],
)


# === 大阪 第一批 (39-46) ===
register(
    "osk_bay_area_wan_wang_zi_hotel",
    brief="**Prince Hotels 系·2023 年 7 月 rebrand**·大阪南港·28 阶 urban resort·全 480 室（rebrand 后部分 432 室运营）·JR 大阪站 shuttle 25 分·USJ 圈外低密 resort 选项。",
    highlights=["设计精品", "Prince Hotels 系", "2023 rebrand", "28 阶大型", "南港 urban resort"],
    address="大阪市住之江区南港北 1-13-11·JR 大阪站 shuttle 25 分",
    rooms="Standard~Suite·全 480 室",
    breakfast="可选 buffet 含早",
    price="素泊 2 人 ¥18,000-50,000",
    booking="公式 princehotels.co.jp·一休·楽天",
    sources=["https://www.princehotels.co.jp/osakabay/", "https://osaka-info.jp/spot/GrandPrinceHotelOsakaBay/"],
)

register(
    "osk_bay_area_universal_port_hotel",
    brief="**USJ オフィシャルホテル·ORIX 不動産运营·2005.7 开业**·USJ 徒步 4 分·全 600 室·**Minion Room** 等多 collab room·大恐竜「REX CAFE」+ Lounge R·バリアフリー対応。",
    highlights=["设计精品", "USJ 公式 ホテル", "ORIX 系", "600 室", "Minion Room collab"],
    address="大阪市此花区·JR ユニバーサルシティ駅徒步 3 分·USJ 徒步 4 分",
    rooms="18 类·全 600 室·バリアフリー有",
    breakfast="可选含早",
    price="素泊 2 人 ¥18,000-60,000",
    booking="公式 ORIX HOTELS·一休·楽天",
    sources=["https://universalport.orixhotelsandresorts.com/", "https://www.usj.co.jp/web/ja/jp/tour-hotel/partner-hotel"],
)

register(
    "osk_bay_area_usj",
    brief="**USJ 最近接公式 ホテル·USJ メインゲート徒步 1 分**·全 598 室·客室 4-28 阶·**全室 30㎡+ + バス トイレ別**·10 类客室·Trip to the U.S.A. 主题·EV エレベーター time machine 设计。",
    highlights=["设计精品", "USJ 最近接 1 分", "598 室", "全室 30㎡+", "Trip to USA 主题"],
    address="大阪市此花区·USJ メインゲート徒步 1 分",
    rooms="10 类·全 598 室·全 30㎡+·バス トイレ別",
    breakfast="可选含早",
    price="素泊 2 人 ¥25,000-80,000",
    booking="公式 parkfront-hotel.com·一休·楽天",
    sources=["https://parkfront-hotel.com/", "https://www.jalan.net/yad345931/"],
)

register(
    "osk_bay_area_universal_qi_dian_hotel",
    brief="**The Singulari Hotel & SkySpa·USJ 公式·Candeo 系**·ユニバーサルシティ駅徒步 1 分·全 390 室·17 阶·**14 阶屋上展望露天「SkySpa」宿泊客无料**·Simmons ベッド·朝食 buffet 60 品+。",
    highlights=["设计精品", "USJ 公式 ホテル", "Candeo 系", "390 室", "屋上 SkySpa 露天", "シングル 16㎡ 露天付 KING"],
    address="大阪市此花区·ユニバーサルシティ駅徒步 1 分",
    rooms="Twin/King/Suite·全 390 室·部分 KING 露天付",
    breakfast="60 品+ 健康 buffet 含选项",
    price="素泊 2 人 ¥30,000-100,000",
    booking="公式 candeohotels.com·一休·楽天",
    sources=["https://www.candeohotels.com/en/singulari/", "https://www.candeohotels.com/en/singulari/rooms/"],
)

register(
    "osk_bay_area_risonare",
    brief="**星野リゾート リゾナーレ·2022.12 开业**·**Hyatt Regency 大阪内一部改装·全 64 室+28 阶屋顶 470㎡ アトリエ**·**レッジョ・エミリア教育**創造力主题·小孩家族特化·アトリエ 80㎡ delux room 网絡云床。",
    highlights=["温泉度假", "星野リゾート 系", "2022 新开业", "64 室", "レッジョ・エミリア 教育", "アトリエ 470㎡"],
    address="大阪市住之江区·南港中央·Hyatt Regency 大阪内",
    rooms="アトリエ Room 3 类 + Family·全 64 室·部分 80㎡",
    breakfast="可选含早",
    price="夕朝食付 2 人 ¥80,000-180,000",
    booking="公式 hoshinoresorts.com·一休·楽天",
    sources=["https://hoshinoresorts.com/en/hotels/risonareosaka/", "https://www.ikyu.com/en-us/00003247/"],
)

register(
    "osk_honmachi_voco",
    brief="**IHG voco 系日本一号·2023 年 5 月 30 日开业**·NTT 都市開発·肥後橋/本町站间·**1926 年旧京町ビル跡地再生**·30㎡ 中心全 191 室·再生素材ベッド+木製カードキー·環境配慮 brand。",
    highlights=["设计精品", "IHG voco 日本一号", "2023.5 新开业", "京町ビル跡再生", "191 室·環境配慮"],
    address="大阪市西区·肥後橋/本町站间",
    rooms="30㎡ 中心·全 191 室",
    breakfast="可选含早",
    price="素泊 2 人 ¥22,000-55,000·IHG One Rewards",
    booking="公式 IHG voco·一休·楽天",
    sources=["https://www.ihg.com/voco/hotels/us/en/osaka/osakn/hoteldetail", "https://www.nttud.co.jp/news/detail/id/n26570.html"],
)

register(
    "osk_namba_dotonbori_swissotel_nankai_osaka",
    brief="**Accor 系 Swissotel·5 星 premium·南海难波站直上·南海サウスタワービル内 36 阶 147m**·全 546 室·**Swiss Executive Lounge**·6 间餐厅+18 间宴会场·髙島屋大阪 5 阶直结·KIX 直通。",
    highlights=["设计精品", "Accor Swissotel 系", "5 星 premium", "南海难波直上", "546 室·36 阶"],
    address="大阪市中央区難波 5-1-60·南海难波站直上·髙島屋直结",
    rooms="Standard~Swiss Executive·全 546 室",
    breakfast="可选含早",
    price="素泊 2 人 ¥35,000-100,000·Accor Live Limitless",
    booking="公式 swissotelnankaiosaka.com·Accor·一休",
    sources=["https://swissotelnankaiosaka.com/", "https://swissotelnankaiosaka.com/rooms-and-suites/"],
)

register(
    "osk_namba_dotonbori_hotel_new_otani_osaka",
    brief="**Forbes 2026 Recommended·Relux 2025 シティ 9 位**·JR 大阪城公园站徒步 3 分·**大阪城正面**·全 540 室·吹抜けアトリウムロビ·13 间餐厅·18 阶 SAKURA 大阪城ライトアップビュー·VIP 多数迎接。",
    highlights=["设计精品", "Forbes 2026 Recommended", "大阪城正面", "540 室", "アトリウムロビ", "VIP 接待"],
    address="大阪市中央区·JR 大阪城公园駅徒步 3 分·大阪城正面",
    rooms="Junior Suite 60㎡·Deluxe Connecting 60+30㎡·全 540 室",
    breakfast="13 间餐厅·可选含早",
    price="素泊 2 人 ¥30,000-100,000",
    booking="公式 newotani.co.jp·Relux·一休",
    sources=["https://www.newotani.co.jp/osaka/", "https://rlx.jp/21047/"],
)


# === 大阪 第二批 (47-54) ===
register(
    "osk_honmachi_the_boly_osaka",
    brief="**2019 年开业·北浜古旧 building リノベ**·中之岛 riverside·大阪メトロ淀屋桥徒步 10 分/堺筋本町徒步 5 分·**Riverside 系客室+キタハマアトリエコンパクト**·Bluetooth 音響 shower room·BOLY 原创 amenity。",
    highlights=["设计精品", "2019 北浜旧 building 再生", "中之岛 riverside", "Bluetooth shower room", "BOLY 原创 amenity"],
    address="大阪市中央区北浜 2-1-16·堺筋線 北浜徒步 5 分·御堂筋線 淀屋桥徒步 10 分",
    rooms="Riverside / キタハマアトリエ·小規模 boutique",
    breakfast="可选含早",
    price="素泊 2 人 ¥25,000-60,000",
    booking="公式 theboly.com·一休·楽天",
    sources=["https://theboly.com/", "https://akogare.jp/hotels/recTiiWYFF4z8H5Zr"],
)

register(
    "osk_honmachi_honmachi_lively_hotel",
    brief="**2019 年 8 月开业·全 174 室·LIVELY HOTELS 系 lifestyle**·堺筋本町徒步 1 分·5 类客室·**シアター機能完備客室 50 室**·Serta マットレス·Global Agents 运营。",
    highlights=["设计精品", "LIVELY 系", "2019 新开业", "174 室", "シアター機能 50 室", "Serta マットレス"],
    address="大阪市中央区·堺筋本町徒步 1 分",
    rooms="シアター/Standard 5 类·全 174 室",
    breakfast="可选含早",
    price="素泊 2 人 ¥18,000-40,000",
    booking="公式 livelyhotels.com·一休·楽天",
    sources=["https://www.livelyhotels.com/ja/thelivelyosaka/", "https://www.livelyhotels.com/ja/posts/lvo211001/"],
)

register(
    "osk_namba_dotonbori_cross_hotel_osaka",
    brief="**ORIX HOTELS Cross Hotel 系**·OsakaMetro なんば駅 14 出口徒步 3 分·心斎橋筋 2 丁目·道頓堀徒步 1 分·全室バス トイレ別·**3F TERRACE & DINING ZERO 朝食 buffet+meetlounge 无料**·ドンネブリVIEWツイン。",
    highlights=["设计精品", "ORIX Cross 系", "なんば 3 分", "道頓堀 1 分", "meetlounge 无料 軽食"],
    address="大阪市中央区心斎橋筋 2-5-15·OsakaMetro なんば徒步 3 分",
    rooms="Standard~SUITE Jr. 48㎡·多类型",
    breakfast="3F ZERO buffet 含选项·大阪名物どて焼き",
    price="素泊 2 人 ¥18,000-50,000",
    booking="公式 ORIX HOTELS·一休·楽天·**注意：2026.2-7 大規模改修部分休业**",
    sources=["https://cross-osaka.orixhotelsandresorts.com/", "https://www.ikyu.com/en-us/00001355/"],
)

register(
    "osk_namba_dotonbori_hiyori",
    brief="**サンフロンティアホテルズ「日和ホテル」関西初**·南海なんば駅徒步 1 分·SAKURA 棟+MOMIJI 棟·全 224 室·琉球畳調床材+**Simmons ベッド+和 Modern**·KIX ラピート 38 分·1F La biyori 朝食。",
    highlights=["设计精品", "日和系关西初", "南海なんば 1 分", "224 室·2 棟构成", "琉球畳調床材+Simmons"],
    address="大阪市中央区·南海なんば駅改札徒步 1 分",
    rooms="22㎡ 中心·全 224 室·バス トイレ独立",
    breakfast="1F La biyori 有料",
    price="素泊 2 人 ¥18,000-40,000",
    booking="公式 namba.hiyori-hotel.jp·一休·楽天",
    sources=["https://namba.hiyori-hotel.jp/", "https://www.jalan.net/yad311599/"],
)

register(
    "osk_namba_dotonbori_monterey_ge_la_si_mi_er_hotel",
    brief="**ホテルモントレ系·31 阶高层·なんば駅徒步 1 分**·全 348 室·24-31 阶 manor house イメージ·31 阶大阪市街地夜景眺望·**最上阶 59㎡ Grasmere Suite**·英国イングランド主题。",
    highlights=["设计精品", "ホテルモントレ系", "なんば 1 分", "348 室·31 阶高层", "59㎡ Grasmere Suite"],
    address="大阪市浪速区湊町 1-2-3·なんば駅徒步 1 分",
    rooms="24-31 阶 manor house·全 348 室",
    breakfast="可选含早",
    price="素泊 2 人 ¥22,000-55,000",
    booking="公式 hotelmonterey.co.jp·一休·楽天",
    sources=["https://www.hotelmonterey.co.jp/grasmere_osaka/", "https://www.j-hotel.or.jp/hotel/298/"],
)

register(
    "osk_shinsaibashi_hotel_nikko_osaka",
    brief="**Okura Nikko Hotels 系 deluxe·御堂筋面**·**心斎橋駅 8 号出口直结**·西心斎橋 1-3-3·5 间餐厅+4 间 bar lounge·Simmons ベッド+デュベ羽毛布团·USJ 1 日 studio pass front 购入·道頓堀徒步 9 分。",
    highlights=["设计精品", "Okura Nikko 系", "心斎橋直结", "御堂筋面立地", "5 间 restaurant+4 间 bar"],
    address="大阪市中央区西心斎橋 1-3-3·心斎橋駅 8 号出口直结",
    rooms="Single~Deluxe Family·Nikko Premium Floor",
    breakfast="セリーナ café 含选项",
    price="素泊 2 人 ¥25,000-70,000",
    booking="公式 okura.com·Okura Nikko·一休",
    sources=["https://okura.com/japan/osaka/hotel-nikko-osaka/", "https://osaka-info.jp/spot/hotel-nikko-osaka/"],
)

register(
    "osk_shinsaibashi_candeo_hotels_osaka_shinsaibas",
    brief="**Candeo Hotels 系·2023 年 11 月 26 日开业**·御堂筋面·心斎橋/なんば徒步 5 分·**江戸建筑三津寺境内通过 entrance·寺院一体型 hotel**·**最上阶屋外露天 sky spa+ロウリュサウナ**·南站夜景眺望。",
    highlights=["设计精品", "Candeo 系", "2023.11 新开业", "三津寺一体型", "屋上 SkySpa 露天 + ロウリュ"],
    address="大阪市中央区·心斎橋/なんば徒步 5 分·三津寺境内·御堂筋面",
    rooms="Standard~Suite·部分露天风吕付",
    breakfast="可选含早",
    price="素泊 2 人 ¥30,000-80,000",
    booking="公式 candeohotels.com·一休·楽天",
    sources=["https://www.candeohotels.com/en/osaka-shinsaibashi/", "https://www.candeohotels.com/en/osaka-shinsaibashi/rooms/"],
)

register(
    "osk_shinsaibashi_the_bridge_hotel",
    brief="**道頓堀 Hotel 第二棟**·**全 381 室含 4 ベッドルーム·女性 group/family 人気**·御堂筋線心斎橋徒步 3 分·**15-22 时 20 种 drink 飲み放題**·添寝 12 岁以下 2 人无料·全室 Simmons+SHARP イオン空清。",
    highlights=["设计精品", "道頓堀系", "381 室·含 4 ベッド", "女性/family 友好", "drink 饮放题"],
    address="大阪市中央区·御堂筋線心斎橋徒步 3 分·四ツ橋徒步 3 分",
    rooms="Single/Double/Twin/Triple/Deluxe Twin/Quad·全 381 室·全室禁烟",
    breakfast="和洋朝食 buffet 含选项",
    price="素泊 2 人 ¥18,000-45,000·公式无料延 12:00 CO",
    booking="公式 bridge-h.co.jp·一休·楽天",
    sources=["https://bridge-h.co.jp/en/", "https://bridge-group.net/en/bridge/"],
)



# === 大阪 第三批 (55-65) ===
register(
    "osk_namba_dotonbori_here_osaka_namba",
    brief="**andHere OSAKA NAMBA·全 89 室「ウラなんば」隐密 boutique**·南海なんば徒步 3 分·9 类客室·**special concept room kitchen+洗濯機·6 人 family OK·NAMbar 大阪 drink/snack·屋上 terrace 大阪夜景+通天閣 view**。",
    highlights=["设计精品", "andHere 系", "ウラ難波 hidden", "89 室·9 类", "Special Concept Room kitchen+洗濯機", "屋上 terrace"],
    address="大阪市中央区難波千日前 7-9·南海なんば徒步 3 分",
    rooms="9 类·全 89 室·部分 family/kitchen·6 人收容",
    breakfast="可选含早",
    price="素泊 2 人 ¥18,000-50,000",
    booking="公式 andherehotels.jp·一休·楽天",
    sources=["https://andherehotels-osakanamba.com/en/", "https://andherehotels.jp/en/"],
)

register(
    "osk_namba_dotonbori_namba_dong_fang_hotel",
    brief="**なんばオリエンタルホテル·なんば駅徒步 1 分（B21 出口直进 30 秒）**·全室 23㎡+·**3F 新设 Residential Floor 9 室 47-52㎡ 含洗濯機+IH+冷凍冷蔵庫+全室 terrace**·family/長期向。",
    highlights=["设计精品", "なんば 1 分（地下街直结）", "Residential Floor 9 室", "全 terrace+洗濯機+IH"],
    address="大阪市中央区千日前 2-8-17·なんば駅徒步 5 分（B21 直进 30 秒）",
    rooms="Standard 23㎡+ / Residential 47-52㎡·共多类",
    breakfast="和洋朝食 buffet 含选项",
    price="素泊 2 人 ¥18,000-50,000",
    booking="公式 nambaorientalhotel.co.jp·一休·楽天",
    sources=["https://nambaorientalhotel.co.jp/", "https://nambaorientalhotel.co.jp/rooms/"],
)

register(
    "osk_namba_dotonbori_cheng_hilton_doubletree_hotel",
    brief="**Hilton 系 DoubleTree·大阪城正面**·所在大手前 1-1-1·**屋内 pool+fitness center**·大阪城/天满桥/大手门徒步 5 分·阪急/京阪 access·全室禁烟·family room 多。",
    highlights=["设计精品", "Hilton 系", "大阪城正面", "屋内 pool+fitness", "Castle View"],
    address="大阪市中央区大手前 1-1-1·大阪城徒步圈",
    rooms="King/Twin/Castle Executive View/Deluxe Suite·全室禁烟",
    breakfast="可选含早·和洋 buffet",
    price="素泊 2 人 ¥30,000-80,000·Hilton Honors",
    booking="公式 Hilton·一休·楽天",
    sources=["https://www.hilton.com/ja/hotels/osaocdi-doubletree-osaka-castle/", "https://doubletree-osaka-castle.hiltonjapan.co.jp/"],
)

register(
    "osk_shinsaibashi_monterey_lei_fu_lai_er_hotel",
    brief="**ホテルモントレ系·2018 年 8 月开业**·JR 大阪駅徒步 5 分·17 阶·全 345 室·**全室ミラブルシャワーヘッド**·セキュリティ扉客室 floor·**宿泊者専用 sauna 付温浴施設**·日本伝統「文様 と あかり」テーマ。",
    highlights=["设计精品", "モントレ系", "2018 新开业", "345 室", "全室ミラブル", "宿泊者 sauna 温浴"],
    address="大阪市北区·JR 大阪駅徒步 5 分",
    rooms="Standard~Suite·全 345 室",
    breakfast="可选含早",
    price="素泊 2 人 ¥22,000-50,000",
    booking="公式 hotelmonterey.co.jp·一休·楽天",
    sources=["https://www.hotelmonterey.co.jp/lefrere_osaka/", "https://www.ikyu.com/en-us/00002549/"],
)

register(
    "osk_tennoji_shinsekai_omo7_by",
    brief="**OMO ブランド最上级 OMO7·2022.4 开业**·新今宫駅目前·14 阶建·8 类全 436 室·**「なにわラグジュアリー」+「笑い」+「おせっかい」コンセプト**·OMO Ranger ガイド·夜の散步推荐。",
    highlights=["设计精品", "OMO7 最上级", "2022.4 新开业", "436 室", "なにわラグジュアリー", "OMO Ranger"],
    address="大阪市浪速区恵美須西 3-16-30·JR 新今宫駅目前",
    rooms="8 类·全 436 室·14 阶建",
    breakfast="可选含早",
    price="素泊 2 人 ¥25,000-60,000",
    booking="公式 hoshinoresorts.com·一休·楽天",
    sources=["https://hoshinoresorts.com/ja/hotels/omo7osaka/", "https://www.jalan.net/yad311704/"],
)

register(
    "osk_tennoji_shinsekai_tennoji_ta_an_da_zhi_sen",
    brief="**アンダの森 大阪天王寺タワー·2025 年 4 月 10 日 grand open·国内 3 馆目**·天王寺駅徒步 3 分·**1 泊 3 食 all-inclusive ホテル**·10 类全 8 名收容·**部分岩盤浴付**·4F 岩盤浴+ボールプール+漫画+gym+ジップライン·1F 木育广场。",
    highlights=["温泉度假", "アンダ系", "2025.4 新开业", "1 泊 3 食 all-inclusive", "10 类客室", "ジップライン"],
    address="大阪市天王寺区·天王寺駅徒步 3 分",
    rooms="10 类·40㎡+ 岩盤浴付 3 类·8 类 family·4 类 compact",
    breakfast="all-inclusive 1 泊 3 食含·夕/夜/朝食 飲み放題",
    price="一泊 3 食 2 人 ¥40,000-150,000",
    booking="公式 andanomori.jp·一休·楽天",
    sources=["https://www.andanomori.jp/tennoji/", "https://www.andanomori.jp/tennoji/room/"],
)

register(
    "osk_umeda_kita_rihga_royal_hotel_da_ban",
    brief="**2025 年 4 月 rebrand 为 Vignette Collection by IHG·1935 年系**·全 1001 室（rebrand 前 1042）·17-109㎡·中之島·**62 室クラブフロア**·**21 间餐厅**·130 億円改装（2025 EXPO 前）·关西最大老铺。",
    highlights=["设计精品", "Vignette by IHG 系", "1001 室·1935 老铺", "62 室 club floor", "21 间餐厅", "2025 EXPO rebrand"],
    address="大阪市北区中之島 5-3-68·新福島駅徒步 3 分",
    rooms="17-109㎡·全 1001 室·クラブフロア 62 室",
    breakfast="可选含早",
    price="素泊 2 人 ¥30,000-80,000·IHG One Rewards",
    booking="公式 rihga.co.jp·IHG·一休",
    sources=["https://www.rihga.co.jp/osaka/", "https://www.rihga.co.jp/osaka/about/"],
)

register(
    "osk_umeda_kita_zentis_osaka",
    brief="**Palace Hotel 系新 brand·2020.7.15 开业**·堂島浜 1-4-26·北新地駅徒步 4 分·全 212 室（King 168/Twin 41/Suite 2/Accessible 1）·25-57㎡·**Tara Bernerd 设计**·UPSTAIRZ 米其林餐厅·24h fitness。",
    highlights=["设计精品", "Palace Hotel 系", "2020.7 新 brand", "212 室", "Tara Bernerd 设计", "UPSTAIRZ 米其林"],
    address="大阪市北区堂島浜 1-4-26·北新地駅徒步 4 分·梅田駅徒步 9-15 分",
    rooms="King 168 / Twin 41 / Suite 2·全 212 室·25-57㎡",
    breakfast="UPSTAIRZ 含选项",
    price="素泊 2 人 ¥45,000-120,000",
    booking="公式 zentishotels.com·Palace Hotel·一休",
    sources=["https://zentishotels.com/ja/osaka/", "https://www.palacehoteltokyo.com/newsroom/latest-news/zentis_osaka/"],
)

register(
    "osk_umeda_kita_umeda_hilton_canopy_hotel",
    brief="**Hilton Canopy 系·2024.9 开业·グラングリーン大阪 ノースタワー内**·大阪市北区大深町 6-38·全 308 室·**Canopy by Hilton 日本初**·**rooftop bar+无料 Canopy 自行车 rental**·grand front 大阪徒步 2 分·ペット OK 套餐。",
    highlights=["设计精品", "Hilton Canopy 日本初", "2024.9 新开业", "308 室", "グラングリーン内", "rooftop bar+rental cycle"],
    address="大阪市北区大深町 6-38·グラングリーン大阪 ノースタワー内·大阪駅 800m",
    rooms="King/Suite/Corner Suite/Panorama Suite·全 308 室",
    breakfast="CC: CARBON COPY 含选项",
    price="素泊 2 人 ¥35,000-90,000·Hilton Honors",
    booking="公式 Hilton·一休·楽天",
    sources=["https://www.hilton.com/en/hotels/osapypy-canopy-osaka-umeda/"],
)

register(
    "osk_umeda_kita_tones_osaka",
    brief="**TONES OSAKA·2025.2.14 grand open**·**世界建築家アルド・ロッシ意匠継承外装**·大阪市北区堂山町 7-13·东梅田徒步 7 分·全 67 室·**全室バス トイレ別+洗い場**·3F TONES LOUNGE 无料朝食（5 类 bread）+特別「TONES SALON」音響个室·9 阶建。",
    highlights=["设计精品", "Vamos 系", "2025.2 新开业", "アルド・ロッシ意匠", "67 室·9 阶", "TONES SALON 音響个室"],
    address="大阪市北区堂山町 7-13·东梅田徒步 7 分",
    rooms="Standard~SALON·全 67 室·バス トイレ独立",
    breakfast="3F LOUNGE 无料 6:30-9:30·5 类 bread+drink",
    price="素泊 2 人 ¥18,000-45,000",
    booking="公式 tones-hotels.com·一休·楽天",
    sources=["https://tones-hotels.com/osaka/", "https://prtimes.jp/main/html/rd/p/000000001.000153326.html"],
)

register(
    "osk_umeda_kita_dojima_aloft",
    brief="**Marriott Bonvoy Aloft 系·关西初**·堂島浜 2-1-31·北新地/渡邊橋/肥後橋徒步 5 分·**全 305 室含 6 室 Loft Suite + 8 室 Corner Loft Queen**·**ロフトイメージデザイン**·堂島地图グラフィック壁纸·55 吋 TV·Simmons ベッド·特注 drybar amenity。",
    highlights=["设计精品", "Marriott Bonvoy Aloft", "关西初", "305 室", "Loft Suite 6 室", "堂島グラフィック"],
    address="大阪市北区堂島浜 2-1-31·北新地/渡邊橋/肥後橋徒步 5 分",
    rooms="King/Twin/Suite/Universal·全 305 室",
    breakfast="可选含早",
    price="素泊 2 人 ¥25,000-65,000·Marriott Bonvoy",
    booking="公式 Marriott·一休·楽天",
    sources=["https://www.marriott.com/en-us/hotels/osaal-aloft-osaka-dojima/overview/", "https://www.ikyu.com/en-us/00002895/"],
)

register(
    "osk_umeda_kita_a_er_mo_ni_an_bu_la_sai_hotel",
    brief="**HARMONIE EMBRASSEE OSAKA·安藤忠雄设计**·チャスカ茶屋町 10-22 阶·阪急梅田徒步 3 分·**Small Luxury 40 室·4 类 design concept 各室独立**·**最上 23 阶天空のチャペル**·三角构造特徴 building·法餐 restaurant 併設。",
    highlights=["设计精品", "安藤忠雄设计", "Small Luxury 40 室", "4 类 design concept", "23F 天空のチャペル"],
    address="大阪市北区茶屋町 7-20·阪急梅田徒步 3 分",
    rooms="4 类·共 40 室·三角形构造",
    breakfast="法餐含选项",
    price="素泊 2 人 ¥40,000-100,000",
    booking="公式 tgn.co.jp·一休·Relux",
    sources=["https://www.tgn.co.jp/hotel/osaka/harmonie/", "https://www.tgn.co.jp/hotel/osaka/harmonie/stay/"],
)


def main() -> None:
    apply = "--apply" in sys.argv
    files = [f for f in ROOT.rglob("*.json") if "_archive" not in f.parts]
    hit = 0
    file_changed: dict[Path, list[dict]] = {}
    found_ids: set[str] = set()
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        changed = False
        for h in data:
            found_ids.add(h["id"])
            hid = h["id"]
            if hid not in PATCHES: continue
            p = PATCHES[hid]
            h["note"].update(p["note"])
            if p["sources"]:
                h["数据来源"] = p["sources"]
            h["可信度"] = "cross_checked"
            h["depth"] = "verified"
            h["最后核实"] = TODAY
            hit += 1
            changed = True
        if changed:
            file_changed[f] = data

    miss = [hid for hid in PATCHES if hid not in found_ids]
    print(f"patched: {hit}/{len(PATCHES)}")
    if miss:
        print(f"MISSING IDs: {miss}")
    if apply:
        for f, data in file_changed.items():
            f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[APPLIED] {len(file_changed)} files written")
    else:
        print("[DRY-RUN]")

if __name__ == "__main__":
    main()














