import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── WAKAYAMA ──────────────────────────────────────────────────────────────────
wky_path = os.path.join(BASE, "data", "kansai_spots", "wakayama.json")
with open(wky_path, encoding="utf-8") as f:
    wky = json.load(f)

new_wky_spots = [
    {
        "id": "wky_koyasan_okunoin",
        "name_zh": "\u9ad8\u91ce\u5c71\u5965\u4e4b\u9662",
        "name_ja": "\u9ad8\u91ce\u5c71\u5965\u306e\u9662",
        "name_en": "Koyasan Okunoin",
        "main_type": "fixed_spot",
        "sub_type": "history_religion",
        "grade": "A",
        "grade_reason": "\u5f18\u6cd5\u5927\u5e08\u5fa1\u5e99\u6240\u5728\uff0c20\u4e07\u57fa\u5893\u7891\u6797\u7acb\u76842km\u53c2\u9053\u662f\u65e5\u672c\u6700\u795e\u79d8\u7684\u6b65\u9053\uff0c\u82d4\u85d3\u53e4\u6749\u4e2d\u7684\u7075\u57df\u4f53\u9a8c\u65e0\u53ef\u66ff\u4ee3",
        "profile_boosts": {"culture_deep": "+1", "photo": "+1"},
        "tags": ["\u5f18\u6cd5\u5927\u5e08\u5fa1\u5e99", "20\u4e07\u57fa\u5893\u7891", "\u591c\u95f4\u53c2\u62dc", "\u7ec7\u7530\u4fe1\u957f\u4e4b\u5893", "\u4e30\u81e3\u79c0\u5409\u4e4b\u5893", "\u82d4\u85d3\u53e4\u6749"],
        "best_time": "\u591c\u95f4\u53c2\u62dc(Night Tour)\u6216\u6e05\u6668",
        "visit_minutes": 90,
        "best_season": "all",
        "coord": [34.2134, 135.6006],
        "tips": "\u591c\u95f4\u53c2\u62dc(Night Tour)\u66f4\u52a0\u9707\u649e\u3002\u4e00\u4e4b\u6865\u5230\u5fa1\u5e99\u52602km\uff0c\u6cbf\u9014\u6709\u7ec7\u7530\u4fe1\u957f\u3001\u4e30\u81e3\u79c0\u5409\u7b49\u540d\u4eba\u4e4b\u5893\u3002\u90e8\u5206\u533a\u57df\u591c\u95f4\u7981\u6b62\u62cd\u7167\uff0c\u9700\u5c0a\u91cd"
    },
    {
        "id": "wky_koyasan_shukubo",
        "name_zh": "\u9ad8\u91ce\u5c71\u5bbf\u574a\u4f53\u9a8c",
        "name_ja": "\u9ad8\u91ce\u5c71\u5bbf\u574a",
        "name_en": "Koyasan Temple Lodging (Shukubo)",
        "main_type": "experience",
        "sub_type": "cultural_exp",
        "grade": "A",
        "grade_reason": "\u5728\u5343\u5e74\u53e4\u5bfa\u4f4f\u4e00\u665a\uff0c\u4f53\u9a8c\u7cbe\u8fdb\u6599\u7406\u548c\u65e9\u8bfe\u8bf5\u7ecf\uff0c\u662f\u9ad8\u91ce\u5c71\u6700\u6df1\u5ea6\u7684\u7cbe\u795e\u4f53\u9a8c",
        "profile_boosts": {"culture_deep": "+1", "couple": "+1"},
        "tags": ["\u5bbf\u574a\u4f4f\u5bbf", "\u7cbe\u8fdb\u6599\u7406", "\u65e9\u8bfe\u8bf5\u7ecf", "\u60e0\u5149\u9662", "\u798f\u667a\u9662", "\u9700\u63d0\u524d\u9884\u7ea6"],
        "best_time": "\u8fc7\u591c\u4f53\u9a8c",
        "visit_minutes": 720,
        "best_season": "all",
        "coord": [34.2152, 135.5835],
        "tips": "\u60e0\u5149\u9662\uff08\u6709\u591c\u95f4\u5965\u4e4b\u9662\u5bfc\u89c8\uff09\u548c\u798f\u667a\u9662\uff08\u6709\u9732\u5929\u6e29\u6cc9\uff09\u6700\u53d7\u6b22\u8fce\u3002\u9700\u63d0\u524d\u9884\u7ea6\uff0c\u65fa\u5b63\u548c\u7279\u6b8a\u8282\u65e5\u9700\u63d0\u524d\u6570\u6708\u9884\u7ea6"
    },
    {
        "id": "wky_yunomine_onsen",
        "name_zh": "\u6e6f\u306e\u5cf0\u6e29\u6cc9",
        "name_ja": "\u6e6f\u306e\u5cf0\u6e29\u6cc9",
        "name_en": "Yunomine Onsen",
        "main_type": "fixed_spot",
        "sub_type": "onsen_resort",
        "grade": "B",
        "grade_reason": "\u65e5\u672c\u6700\u53e4\u8001\u7684\u6e29\u6cc9\u4e4b\u4e00\uff0c\u58f6\u6c64\u662f\u4e16\u754c\u9057\u4ea7\u4e2d\u552f\u4e00\u53ef\u4ee5\u5165\u6d74\u7684\u6e29\u6cc9\uff0c\u6781\u4e3a\u73cd\u8d35",
        "profile_boosts": {"nature_outdoor": "+1", "revisit": "+1"},
        "tags": ["\u65e5\u672c\u6700\u53e4\u8001\u6e29\u6cc9", "\u58f6\u6c64", "\u4e16\u754c\u9057\u4ea7\u5185\u6e29\u6cc9", "7\u6b21\u53d8\u8272", "\u718a\u91ce\u53e4\u9053\u9014\u4e2d"],
        "best_time": "\u5082\u664f\uff08\u6ce1\u5b8c\u6e29\u6cc9\u7559\u5bbf\uff09",
        "visit_minutes": 60,
        "best_season": "all",
        "coord": [33.8408, 135.7247],
        "tips": "\u58f6\u6c64(\u3064\u307c\u6e6f)30\u5206\u949f\u8f6e\u6362\u5236780\u65e5\u5143\uff0c\u636e\u8bf4\u4e00\u5929\u53d87\u6b21\u53d8\u8272\u3002\u662f\u4e16\u754c\u9057\u4ea7\u5185\u552f\u4e00\u53ef\u4ee5\u5165\u6d74\u7684\u8bbe\u65bd\uff0c\u5386\u53f2\u4ef7\u5024\u6781\u9ad8\u3002\u7ed3\u5408\u718a\u91ce\u53e4\u9053\u5f92\u6b65\u884c\u7a0b\u6700\u4e3a\u7406\u60f3"
    },
    {
        "id": "wky_sandanbeki_senjojiki",
        "name_zh": "\u4e09\u6bb5\u58c1\u30fb\u5343\u755f\u655f",
        "name_ja": "\u4e09\u6bb5\u58c1\u30fb\u5343\u755f\u655f",
        "name_en": "Sandanbeki Cliffs & Senjojiki Rocks",
        "main_type": "fixed_spot",
        "sub_type": "nature_scenery",
        "grade": "C",
        "grade_reason": "\u767d\u6ee8\u7684\u6d77\u8680\u5d16\u548c\u5343\u5c42\u5ca9\uff0c\u5730\u8d28\u5947\u89c2\uff0c\u9002\u5408\u4e0e\u767d\u6ee8\u6e29\u6cc9\u7ec4\u5408\u6e38\u89c8",
        "profile_boosts": {"photo": "+1"},
        "tags": ["\u6d77\u8680\u5d16", "\u5343\u5c42\u5ca9", "\u767d\u6ee8\u5730\u8d28\u5947\u89c2", "\u6d77\u8680\u6d1e\u7535\u68af", "\u65e5\u843d\u89c2\u8d4f"],
        "best_time": "\u65e5\u843d\u65f6\u5206\uff08\u5343\u755f\u655f\u67d3\u7ea2\u6700\u7f8e\uff09",
        "visit_minutes": 40,
        "best_season": "all",
        "coord": [33.6614, 135.3394],
        "tips": "\u4e09\u6bb5\u58c1\u6709\u7535\u68af\u4e0b\u5230\u6d77\u8680\u6d1e(1300\u65e5\u5143)\uff0c\u6d1e\u5185\u53ef\u770b\u5230\u53e4\u4ee3\u718a\u91ce\u6c34\u519b\u4f20\u8bf4\u9057\u8ff9\u3002\u5343\u755f\u655f\u514d\u8d39\uff0c\u65e5\u843d\u65f6\u5206\u6700\u7f8e\u3002\u4e24\u5904\u6b65\u884c\u8ddd\u79bb\u52651\u524815\u5206\u949f"
    }
]

existing_wky_ids = {s["id"] for s in wky["spots"]}
added_wky = 0
for spot in new_wky_spots:
    if spot["id"] not in existing_wky_ids:
        wky["spots"].append(spot)
        added_wky += 1
        print(f"  [wakayama] Added: {spot['id']}")
    else:
        print(f"  [wakayama] SKIPPED (exists): {spot['id']}")

with open(wky_path, "w", encoding="utf-8") as f:
    json.dump(wky, f, ensure_ascii=False, indent=2)
print(f"wakayama.json -> {len(wky['spots'])} spots total (added {added_wky})\n")


# ── SHIGA ─────────────────────────────────────────────────────────────────────
shiga_path = os.path.join(BASE, "data", "kansai_spots", "shiga.json")
with open(shiga_path, encoding="utf-8") as f:
    shiga = json.load(f)

new_shiga_spots = [
    {
        "id": "shiga_miho_museum_b",
        "name_zh": "MIHO\u7f8e\u672f\u9986",
        "name_ja": "\u30df\u30db \u30df\u30e5\u30fc\u30b8\u30a2\u30e0",
        "name_en": "MIHO Museum",
        "main_type": "fixed_spot",
        "sub_type": "culture_art",
        "grade": "B",
        "grade_reason": "\u8d1d\u8e33\u9298\u6649\u5e74\u6770\u4f5c\uff0c\u85cf\u5728\u4fe1\u4e50\u5c71\u91cc\u7684\u300c\u6843\u82b1\u6e90\u300d\u7f8e\u672f\u9986\uff0c\u5efa\u7b7480%\u85cf\u4e8e\u5c71\u4f53\uff0c\u9232\u9053\u5165\u53e3\u901a\u5411\u73bb\u7483\u7a79\u9876\u5c55\u5385",
        "profile_boosts": {"culture_deep": "+1", "photo": "+1"},
        "tags": ["\u8d1d\u8e33\u9298\u8bbe\u8ba1", "\u5efa\u7b51\u540d\u4f5c", "\u6843\u82b1\u6e90\u610f\u5883", "\u6a31\u82b1\u9232\u9053", "\u6625\u79cb\u9650\u5b9a\u5f00\u9986"],
        "best_time": "\u4e0a\u5348\u5165\u9986",
        "visit_minutes": 120,
        "best_season": "spring",
        "seasonal_highlights": ["\u6625\u5b63\u9232\u9053+\u5c71\u6a31\u7edd\u666f", "\u79cb\u5b63\u7ea2\u53f6\u4e0e\u73bb\u7483\u5efa\u7b51\u76f8\u6620"],
        "coord": [34.8872, 136.0355],
        "tips": "\u4ea4\u901a\u4e0d\u4fbf\uff08\u77f3\u5c71\u7ad9\u5750\u5df4\u58eb50\u5206\u949f\uff09\u4f46\u5024\u5f97\u3002\u7a7f\u8fc7\u9232\u9053\u770b\u5230\u7f8e\u672f\u9986\u7684\u77ac\u95f4\u50cf\u8fdb\u5165\u6843\u82b1\u6e90\u3002\u6625\u79cb\u9650\u5b9a\u5f00\u9986\uff0c\u5468\u4e00\u5468\u4e8c\u95ed\u9986\uff0c\u52a1\u5fc5\u63d0\u524d\u786e\u8ba4"
    },
    {
        "id": "shiga_chikubushima",
        "name_zh": "\u7af9\u751f\u5c9b",
        "name_ja": "\u7af9\u751f\u5cf6",
        "name_en": "Chikubushima Island",
        "main_type": "fixed_spot",
        "sub_type": "history_religion",
        "grade": "B",
        "grade_reason": "\u7405\u7436\u6e56\u4e0a\u7684\u795e\u5723\u5c0f\u5c9b\uff0c\u5b9d\u53a5\u5bfa\u4e0e\u90fd\u4e45\u592b\u987b\u9ebb\u795e\u793e\u540c\u5728\u4e00\u5c9b\uff0c\u6295\u74e6\u7247\u8bb8\u613f\u662f\u4eba\u6c14\u4f53\u9a8c",
        "profile_boosts": {"culture_deep": "+1"},
        "tags": ["\u7405\u7436\u6e56\u79bb\u5c9b", "\u5b9d\u53a5\u5bfa", "\u90fd\u4e45\u592b\u987b\u9eba\u795e\u793e", "\u304b\u308f\u3089\u3051\u6295\u3052", "\u8239\u6e38\u4f53\u9a8c"],
        "best_time": "\u4e0a\u5348\uff08\u8239\u73ed\u8f83\u591a\uff09",
        "visit_minutes": 80,
        "best_season": "all",
        "coord": [35.4217, 136.1469],
        "tips": "\u4ece\u957f\u6ee8\u5750\u8239\u523030\u5206\u949f\u3002\u6295\u74e6\u7247(\u304b\u308f\u3089\u3051\u6295\u3052)\u7a7f\u8fc7\u9e1f\u5c45\u8bb8\u613f\u662f\u4eba\u6c14\u4f53\u9a8c\u3002\u5c9b\u4e0a\u505c\u7559\u540880\u5206\u949f\uff0c\u6ce8\u610f\u672b\u73ed\u8239\u65f6\u523b\u907f\u514d\u6ede\u7559"
    }
]

existing_shiga_ids = {s["id"] for s in shiga["spots"]}
existing_shiga_names = {s.get("name_en", "") for s in shiga["spots"]}

added_shiga = 0
for spot in new_shiga_spots:
    if spot["name_en"] in existing_shiga_names:
        print(f"  [shiga] SKIPPED (name already exists): {spot['id']} / {spot['name_en']}")
        continue
    if spot["id"] not in existing_shiga_ids:
        shiga["spots"].append(spot)
        added_shiga += 1
        print(f"  [shiga] Added: {spot['id']}")
    else:
        print(f"  [shiga] SKIPPED (id exists): {spot['id']}")

with open(shiga_path, "w", encoding="utf-8") as f:
    json.dump(shiga, f, ensure_ascii=False, indent=2)
print(f"shiga.json -> {len(shiga['spots'])} spots total (added {added_shiga})\n")


# ── MIE/FUKUI/TOTTORI/TOKUSHIMA ───────────────────────────────────────────────
mie_path = os.path.join(BASE, "data", "kansai_spots", "mie_fukui_tottori_tokushima.json")
with open(mie_path, encoding="utf-8") as f:
    mie = json.load(f)

new_mie_spots = [
    {
        "id": "mie_okage_yokocho_area",
        "name_zh": "\u304a\u304b\u3052\u6a2a\u4e01",
        "name_ja": "\u304a\u304b\u3052\u6a2a\u4e01",
        "name_en": "Okage Yokocho",
        "main_type": "area_dest",
        "sub_type": "historic_district",
        "grade": "B",
        "grade_reason": "\u4f0a\u52bf\u795e\u5bab\u5185\u5bab\u524d\u7684\u6c5f\u6237\u98ce\u60c5\u5546\u5e97\u8857\uff0c\u4f0a\u52bf\u4e4c\u51ac+\u8d64\u798f\u997c\u662f\u5fc5\u5403",
        "profile_boosts": {"foodie": "+1"},
        "tags": ["\u8d64\u798f\u997c\u672c\u5e97", "\u4f0a\u52bf\u4e4c\u51ac", "\u6c5f\u6237\u60c5\u8c03", "\u5185\u5bab\u95e8\u524d", "\u6b65\u884c\u7f8e\u98df"],
        "best_time": "\u53c2\u62dc\u5185\u5bab\u540e\u4e0a\u5348",
        "visit_minutes": 60,
        "best_season": "all",
        "coord": [34.4559, 136.7262],
        "tips": "\u8d64\u798f\u672c\u5e97\u7684\u8d64\u798f\u997c\u662f\u4f0a\u52bf\u540d\u7269\u4e2d\u7684\u540d\u7269\u3002\u4f0a\u52bf\u4e4c\u51ac\u53c8\u7c97\u53c8\u8f6f\u662f\u5f53\u5730\u7279\u8272\u3002\u544a\u996d\u9ad8\u5cf0(11:30-13:00)\u6392\u961f\u957f\uff0c\u5efa\u8bae\u9519\u5f00"
    },
    {
        "id": "mie_meoto_iwa",
        "name_zh": "\u592b\u5987\u5ca9",
        "name_ja": "\u592b\u5a66\u5ca9",
        "name_en": "Meoto Iwa (Wedded Rocks)",
        "main_type": "fixed_spot",
        "sub_type": "nature_scenery",
        "grade": "C",
        "grade_reason": "\u4e8c\u89c1\u6d66\u6ce8\u8fde\u7ef3\u8fde\u63a5\u7684\u592b\u5987\u5ca9\uff0c\u65e5\u672c\u6700\u77e5\u540d\u7684\u6d77\u5cb8\u666f\u89c2\u4e4b\u4e00\uff0c\u65c1\u8fb9\u4e8c\u89c1\u5174\u7389\u795e\u793e\u9752\u86d9\u96d5\u50cf\u4f17\u591a",
        "profile_boosts": {"photo": "+1"},
        "tags": ["\u592b\u5987\u5ca9", "\u6ce8\u8fde\u7ef3", "\u4e8c\u89c1\u6d66", "\u65e5\u51fa\u5bcc\u58eb\u5c71", "\u9752\u86d9\u795e\u793e"],
        "best_time": "\u6e05\u6668\u65e5\u51fa\uff085-7\u6708\u53ef\u89c1\u65e5\u51fa+\u5bcc\u58eb\u5c71\uff09",
        "visit_minutes": 20,
        "best_season": "all",
        "seasonal_highlights": ["5-7\u6708\u6674\u5929\u53ef\u4ee5\u4ece\u5ca9\u77f3\u95f4\u770b\u5230\u65e5\u51fa+\u5bcc\u58eb\u5c71"],
        "coord": [34.5069, 136.7947],
        "tips": "5-7\u6708\u53ef\u4ee5\u4ece\u5ca9\u77f3\u95f4\u770b\u5230\u65e5\u51fa+\u5bcc\u58eb\u5c71\uff08\u5929\u6c14\u597d\u65f6\uff09\u3002\u65c1\u8fb9\u7684\u4e8c\u89c1\u5174\u7389\u795e\u793e\u6709\u5f88\u591a\u9752\u86d9\u96d5\u50cf\uff0c\u4f9b\u5949\u733f\u7530\u5f66\u5927\u795e\u3002\u4ece\u9e1f\u7fbd\u6216\u4f0a\u52bf\u4e58\u8f66\u57ea15-20\u5206\u949f"
    }
]

existing_mie_ids = {s["id"] for s in mie["spots"]}
existing_mie_names = {s.get("name_en", "") for s in mie["spots"]}

added_mie = 0
for spot in new_mie_spots:
    if spot["name_en"] in existing_mie_names:
        print(f"  [mie] SKIPPED (name already exists): {spot['id']} / {spot['name_en']}")
        continue
    if spot["id"] not in existing_mie_ids:
        mie["spots"].append(spot)
        added_mie += 1
        print(f"  [mie] Added: {spot['id']}")
    else:
        print(f"  [mie] SKIPPED (id exists): {spot['id']}")

with open(mie_path, "w", encoding="utf-8") as f:
    json.dump(mie, f, ensure_ascii=False, indent=2)
print(f"mie_fukui_tottori_tokushima.json -> {len(mie['spots'])} spots total (added {added_mie})\n")

print("Done.")
