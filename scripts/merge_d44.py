"""D44 entity 合并 + 修复·一次性脚本。

修复内容：
1. 清掉 _meta 头
2. 法隆寺/唐招提/药师 area 修正（horyuji / nishinokyo）
3. area_registry 加 5 个新区（kobe_suma, kobe_nada, nipponbashi, horyuji, nishinokyo）
4. 把 _d44_*.json 合并到 kyoto.json / osaka.json / other.json
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
ENT_DIR = ROOT / "japan/kansai/entities"
REGISTRY_PATH = ROOT / "japan/kansai/area_registry.json"

# 1. 加 area_registry 新区
NEW_AREAS = [
    {"area": "kobe_suma", "type": "日归动线", "city": "神户"},
    {"area": "kobe_nada", "type": "日归动线", "city": "神户"},
    {"area": "nipponbashi", "type": "日归动线", "city": "大阪"},
    {"area": "horyuji", "type": "景点单日", "city": "奈良"},
    {"area": "nishinokyo", "type": "日归动线", "city": "奈良"},
]

reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
existing_areas = {r["area"] for r in reg}
for na in NEW_AREAS:
    if na["area"] not in existing_areas:
        reg.append(na)
        print(f"  + area_registry: {na['area']} ({na['type']}, {na['city']})")
REGISTRY_PATH.write_text(
    json.dumps(reg, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

# 2. 修正法隆寺/唐招提/药师 area
AREA_FIXES = {
    "nar_horyuji": "horyuji",
    "nar_toshodaiji": "nishinokyo",
    "nar_yakushiji": "nishinokyo",
}

# 3. 加载新增 + 修复 + 合并
def load_clean(p):
    d = json.loads(p.read_text(encoding="utf-8"))
    # 清掉 _meta 等非 entity 头
    return {k: v for k, v in d.items() if isinstance(v, dict) and v.get("entity_id")}


for src_name, dst_name in [
    ("_d44_kyoto.json", "kyoto.json"),
    ("_d44_osaka.json", "osaka.json"),
    ("_d44_other.json", "other.json"),
]:
    src = ENT_DIR / src_name
    dst = ENT_DIR / dst_name
    if not src.exists():
        continue
    new = load_clean(src)
    # 修 area
    for eid, fix_area in AREA_FIXES.items():
        if eid in new:
            old_area = new[eid].get("area")
            new[eid]["area"] = fix_area
            print(f"  area fix: {eid} {old_area} → {fix_area}")
    # 合并到主文件
    main = json.loads(dst.read_text(encoding="utf-8"))
    overlap = set(new.keys()) & set(main.keys())
    if overlap:
        print(f"  [WARN] {dst_name} 重复 entity_id: {overlap}")
    main.update(new)
    dst.write_text(
        json.dumps(main, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  {dst_name}: 合并 {len(new)} 条 → 总 {len(main)}")
    # 删除 _d44_*.json
    src.unlink()
    print(f"  rm {src_name}")
