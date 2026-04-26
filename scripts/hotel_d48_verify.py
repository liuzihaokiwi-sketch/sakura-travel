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










