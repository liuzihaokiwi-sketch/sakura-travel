# -*- coding: utf-8 -*-
"""Fill missing coordinates and Chinese names in spots_enriched.csv.

Coordinates verified via OpenCLI google search + Wikipedia/latitude.to.
Chinese names derived from Japanese kanji to simplified Chinese conversion.
"""
import csv
from pathlib import Path

CSV_PATH = (
    Path(__file__).resolve().parent.parent
    / "data" / "kansai_spots" / "discovery_pool" / "spots_enriched.csv"
)

# Verified coordinates: name_en -> (lat, lng)
COORDS: dict[str, tuple[float, float]] = {
    "Kenninji Temple": (35.0007, 135.7708),      # latitude.to
    "Horyuji Temple": (34.6114, 135.7361),       # Wikimedia EXIF
    "Nara Park": (34.6847, 135.8393),            # latitude.to
    "Expo 70 Park": (34.8101, 135.5276),         # Wikipedia
    "Higashiyama": (34.9983, 135.7810),          # district center
    "Naramachi": (34.6789, 135.8310),            # old quarter south of Kofuku-ji
    "Koyasan Temple Lodging": (34.2131, 135.5870),  # shukubo area
    "Koyasan Pilgrimage Trails": (34.2200, 135.5900),  # Choishi-michi
    "Uji Tea Experience": (34.8896, 135.8076),   # Uji city center
    "Kinosaki Onsen": (35.6266, 134.8110),       # Wikipedia station + offset
    "Kinosaki Town Center": (35.6270, 134.8115), # main street
    "Mount Yoshino": (34.3567, 135.8706),        # Wikipedia
    "Nijo Jinya": (35.0115, 135.7505),           # near Nijo Castle
}

# Chinese names: name_en -> name_zh
NAME_ZH: dict[str, str] = {}


def _build_name_zh() -> dict[str, str]:
    """Build Chinese name mapping. Separated to avoid encoding issues in literals."""
    m: dict[str, str] = {}

    # Kyoto
    m["teamLab Biovortex"] = "teamLab\u751f\u547d\u6f29\u6da1"  # teamLab生命漩涡
    m["Higashiyama"] = "\u4e1c\u5c71"  # 东山
    m["Heian Shrine"] = "\u5e73\u5b89\u795e\u5bab"  # 平安神宫
    m["Maruyama Park"] = "\u5706\u5c71\u516c\u56ed"  # 圆山公园
    m["Fushimi Sake District"] = "\u4f0f\u89c1\u9152\u85cf"  # 伏见酒藏
    m["Shugakuin Villa"] = "\u4fee\u5b66\u9662\u79bb\u5bab"  # 修学院离宫
    m["Kibune"] = "\u8d35\u8239"  # 贵船
    m["Kurama"] = "\u978d\u9a6c"  # 鞍马
    m["Ohara"] = "\u5927\u539f"  # 大原
    m["Sanzenin Temple"] = "\u4e09\u5343\u9662"  # 三千院
    m["Takao"] = "\u9ad8\u96c4"  # 高雄
    m["Hieizan"] = "\u6bd4\u53e1\u5c71"  # 比叡山
    m["Kamo Shrines"] = "\u4e0a\u8d3a\u8302\u795e\u793e\u00b7\u4e0b\u9e2d\u795e\u793e"  # 上贺茂神社·下鸭神社
    m["Enkoji Temple"] = "\u5706\u5149\u5bfa"  # 圆光寺
    m["Manshuin Temple"] = "\u66fc\u6b8a\u9662"  # 曼殊院
    m["Toei Eigamura"] = "\u4e1c\u6620\u592a\u79e6\u6620\u753b\u6751"  # 东映太秦映画村
    m["Hozugawa River Cruise"] = "\u4fdd\u6d25\u5ddd\u6f02\u6d41"  # 保津川漂流
    m["Sagano Railway"] = "\u5d6f\u5ce8\u91ce\u5c0f\u706b\u8f66"  # 嵯峨野小火车
    m["Yamazaki Whisky Distillery"] = "\u5c71\u5d0e\u84b8\u998f\u6240"  # 山崎蒸馏所
    m["Sento Palace"] = "\u4ed9\u6d1e\u5fa1\u6240"  # 仙洞御所
    m["Nijo Jinya"] = "\u4e8c\u6761\u9635\u5c4b"  # 二条阵屋
    m["Shinnyodo Temple"] = "\u771f\u5982\u5802"  # 真如堂
    m["Shogunzuka Mound"] = "\u5c06\u519b\u51a2"  # 将军冢
    m["Daikakuji Temple"] = "\u5927\u89c9\u5bfa"  # 大觉寺
    m["Yoshiminedera"] = "\u5584\u5cf0\u5bfa"  # 善峰寺
    m["Ine"] = "\u4f0a\u6839"  # 伊根

    # Osaka
    m["Universal Studios Japan"] = "\u65e5\u672c\u73af\u7403\u5f71\u57ce"  # 日本环球影城
    m["Minami (Namba)"] = "\u96be\u6ce2"  # 难波
    m["Osaka Museum of History"] = "\u5927\u962a\u5386\u53f2\u535a\u7269\u9986"  # 大阪历史博物馆
    m["Abeno Harukas"] = "\u963f\u500d\u91ceHARUKAS"  # 阿倍野HARUKAS
    m["Kita (Umeda)"] = "\u6885\u7530"  # 梅田
    m["Osaka Station City"] = "\u5927\u962a\u7ad9\u57ce"  # 大阪站城
    m["Minoo Park"] = "\u7b95\u9762\u516c\u56ed"  # 箕面公园
    m["Tenma"] = "\u5929\u6ee1"  # 天满
    m["National Museum of Art Osaka"] = "\u56fd\u7acb\u56fd\u9645\u7f8e\u672f\u9986"  # 国立国际美术馆
    m["Osaka Science Museum"] = "\u5927\u962a\u5e02\u7acb\u79d1\u5b66\u9986"  # 大阪市立科学馆
    m["Tennoji"] = "\u5929\u738b\u5bfa"  # 天王寺
    m["Grand Front Osaka"] = "GRAND FRONT\u5927\u962a"  # GRAND FRONT大阪
    m["Mozu Tombs"] = "\u767e\u820c\u9e1f\u53e4\u5786\u7fa4"  # 百舌鸟古坟群
    m["Asahi Suita Brewery"] = "\u671d\u65e5\u5564\u9152\u5434\u7530\u5de5\u5382"  # 朝日啤酒吹田工厂
    m["Bunraku Theater"] = "\u56fd\u7acb\u6587\u4e50\u5267\u573a"  # 国立文乐剧场
    m["Bayarea (Osaka)"] = "\u5927\u962a\u6e7e\u533a"  # 大阪湾区

    # Nara
    m["Isuien Garden"] = "\u4f9d\u6c34\u56ed"  # 依水园
    m["Yakushiji Temple"] = "\u836f\u5e08\u5bfa"  # 药师寺
    m["Toshodaiji Temple"] = "\u5510\u62db\u63d0\u5bfa"  # 唐招提寺
    m["Shin-Yakushiji Temple"] = "\u65b0\u836f\u5e08\u5bfa"  # 新药师寺
    m["Nara National Museum"] = "\u5948\u826f\u56fd\u7acb\u535a\u7269\u9986"  # 奈良国立博物馆
    m["Heijo Palace"] = "\u5e73\u57ce\u5bab\u8ff9"  # 平城宫迹
    m["Yoshikien Garden"] = "\u5409\u57ce\u56ed"  # 吉城园
    m["Naramachi"] = "\u5948\u826f\u753a"  # 奈良町
    m["Wakakusayama"] = "\u82e5\u8349\u5c71"  # 若草山
    m["Kinpusenji Temple"] = "\u91d1\u5cf0\u5c71\u5bfa"  # 金峰山寺
    m["Mount Yoshino"] = "\u5409\u91ce\u5c71"  # 吉野山

    # Kobe / Hyogo
    m["Earthquake Museum"] = "\u4eba\u4e0e\u9632\u707e\u672a\u6765\u4e2d\u5fc3"  # 人与防灾未来中心
    m["Nunobiki Ropeway"] = "\u5e03\u5f15\u7d22\u9053"  # 布引索道
    m["Sorakuen Garden"] = "\u76f8\u4e50\u56ed"  # 相乐园
    m["Kitano"] = "\u5317\u91ce\u5f02\u4eba\u9986\u8857"  # 北野异人馆街
    m["Hyogo Museum of Art"] = "\u5175\u5e93\u53bf\u7acb\u7f8e\u672f\u9986"  # 兵库县立美术馆
    m["Sake Breweries (Nada)"] = "\u6ee9\u9152\u85cf"  # 滩酒藏
    m["Akashi Kaikyo Bridge"] = "\u660e\u77f3\u6d77\u5ce1\u5927\u6865"  # 明石海峡大桥
    m["Meriken Park"] = "\u7f8e\u5229\u575a\u516c\u56ed"  # 美利坚公园
    m["Mount Shosha"] = "\u4e66\u5199\u5c71"  # 书写山
    m["Kokoen Garden"] = "\u597d\u53e4\u56ed"  # 好古园
    m["Kobe City Museum"] = "\u795e\u6237\u5e02\u7acb\u535a\u7269\u9986"  # 神户市立博物馆

    # Koyasan
    m["Okunoin Temple"] = "\u5965\u4e4b\u9662"  # 奥之院
    m["Kongobuji Temple"] = "\u91d1\u521a\u5cf0\u5bfa"  # 金刚峰寺
    m["Danjo Garan"] = "\u575b\u4e0a\u4f3d\u84dd"  # 坛上伽蓝
    m["Reihokan Museum"] = "\u7075\u5b9d\u9986"  # 灵宝馆
    m["Koyasan Temple Lodging"] = "\u9ad8\u91ce\u5c71\u5bbf\u574a"  # 高野山宿坊
    m["Koyasan Pilgrimage Trails"] = "\u9ad8\u91ce\u5c71\u53c2\u8be3\u9053"  # 高野山参诣道
    m["Tokugawa Mausoleum"] = "\u5fb7\u5ddd\u5bb6\u7075\u53f0"  # 德川家灵台

    # Uji
    m["Uji Tea Experience"] = "\u5b87\u6cbb\u8336\u4f53\u9a8c"  # 宇治茶体验
    m["Mampukuji Temple"] = "\u4e07\u798f\u5bfa"  # 万福寺
    m["Ujigami Shrine"] = "\u5b87\u6cbb\u4e0a\u795e\u793e"  # 宇治上神社
    m["Nintendo Museum"] = "\u4efb\u5929\u5802\u535a\u7269\u9986"  # 任天堂博物馆
    m["Uji River"] = "\u5b87\u6cbb\u5ddd"  # 宇治川

    # Kinosaki
    m["Kinosaki Onsen"] = "\u57ce\u5d0e\u6e29\u6cc9"  # 城崎温泉
    m["Kinosaki Town Center"] = "\u57ce\u5d0e\u6e29\u6cc9\u8857"  # 城崎温泉街
    m["Onsenji Temple"] = "\u6e29\u6cc9\u5bfa"  # 温泉寺
    m["Stork Sanctuary"] = "\u4e1c\u65b9\u767d\u9e73\u4e4b\u4e61\u516c\u56ed"  # 东方白鹳之乡公园

    # Mie (Ise / Toba)
    m["Ise Grand Shrine Inner (Naiku)"] = "\u4f0a\u52bf\u795e\u5bab\u5185\u5bab"  # 伊势神宫内宫
    m["Ise Grand Shrine Outer (Geku)"] = "\u4f0a\u52bf\u795e\u5bab\u5916\u5bab"  # 伊势神宫外宫
    m["Oharaimachi & Okage Yokocho"] = "\u5fa1\u7953\u753a\u00b7\u5fa1\u836b\u6a2a\u4e01"  # 御祓町·御荫横丁
    m["Meoto Iwa"] = "\u592b\u5987\u5ca9"  # 夫妇岩
    m["Mikimoto Pearl Island"] = "\u5fa1\u6728\u672c\u73cd\u73e0\u5c9b"  # 御木本珍珠岛
    m["Toba Aquarium"] = "\u9e1f\u7fbd\u6c34\u65cf\u9986"  # 鸟羽水族馆
    m["Ago Bay"] = "\u82f1\u865e\u6e7e"  # 英虞湾

    return m


def main() -> None:
    name_zh_map = _build_name_zh()

    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    coords_filled = 0
    zh_filled = 0

    for row in rows:
        name_en = row["name_en"]

        # Fill coordinates
        if (not row["lat"] or not row["lng"]) and name_en in COORDS:
            lat, lng = COORDS[name_en]
            row["lat"] = str(lat)
            row["lng"] = str(lng)
            coords_filled += 1

        # Fill Chinese names
        if not row["name_zh"] and name_en in name_zh_map:
            row["name_zh"] = name_zh_map[name_en]
            zh_filled += 1

    # Write back
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Report
    print(f"Coordinates filled: {coords_filled}")
    print(f"Chinese names filled: {zh_filled}")

    # Remaining gaps
    still_no_coords = [r for r in rows if not r.get("lat") or not r.get("lng")]
    still_no_zh = [r for r in rows if not r.get("name_zh")]
    print(f"\nRemaining missing coords: {len(still_no_coords)}")
    for r in still_no_coords:
        print(f"  {r['name_en']}")
    print(f"Remaining missing name_zh: {len(still_no_zh)}")
    for r in still_no_zh:
        print(f"  {r['name_en']}")

    # Validate coordinates in Kansai range
    print("\n--- Coordinate validation (Kansai: lat 33.5-36.0, lng 134.0-137.0) ---")
    errors = 0
    for r in rows:
        if r["lat"] and r["lng"]:
            lat, lng = float(r["lat"]), float(r["lng"])
            if not (33.5 <= lat <= 36.0 and 134.0 <= lng <= 137.0):
                print(f"  OUT OF RANGE: {r['name_en']} ({lat}, {lng})")
                errors += 1
    if errors == 0:
        print("  All coordinates within Kansai range. OK")


if __name__ == "__main__":
    main()
