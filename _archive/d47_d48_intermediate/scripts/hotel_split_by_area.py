"""把单一 hotels__kansai.json 拆成 city/area 多文件·对齐餐厅/stops 结构."""
from __future__ import annotations
import io, json, sys, shutil
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SRC = Path("japan/kansai/hotels/data/hotels__kansai.json")
ROOT = Path("japan/kansai/hotels")

# city -> dir name (与餐厅/stops 对齐)
CITY_DIR = {
    "京都": "kyoto",
    "大阪": "osaka",
    "神户": "kobe_area",
    "奈良": "other/nara",
    "城崎": "other/kinosaki",
    "高野山": "other/koyasan",
    "白浜": "other/shirahama",
}

def main() -> None:
    apply = "--apply" in sys.argv
    data = json.loads(SRC.read_text(encoding="utf-8"))
    bucket: dict[tuple[str,str], list[dict]] = defaultdict(list)
    for h in data:
        city = h["city"]; area = h["area"]
        d = CITY_DIR.get(city)
        if d is None:
            print(f"WARN unknown city {city} for {h['id']}"); continue
        bucket[(d, area)].append(h)

    print(f"将拆出 {len(bucket)} 个文件:")
    for (d, area), hs in sorted(bucket.items()):
        print(f"  {ROOT / d / (area + '.json')}: {len(hs)} hotels")

    if not apply:
        print("\n[DRY-RUN]"); return

    # 新建目录 + 写文件
    for (d, area), hs in bucket.items():
        target_dir = ROOT / d
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / f"{area}.json"
        target_file.write_text(json.dumps(hs, ensure_ascii=False, indent=2), encoding="utf-8")

    # 删旧 data/
    old_data = ROOT / "data"
    if old_data.exists():
        shutil.rmtree(old_data)
        print(f"\n删除旧目录 {old_data}")

    print("\n[APPLIED]")

if __name__ == "__main__":
    main()
