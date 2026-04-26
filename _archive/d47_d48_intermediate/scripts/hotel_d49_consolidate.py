"""D49 合并 28 个 area json 为 3 个 region json."""
from __future__ import annotations
import io, json, sys, shutil
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path("japan/kansai/hotels")

CITY_TO_REGION = {
    "京都": "kyoto",
    "大阪": "osaka",
    # 其他全部归 other
    "神户": "other", "奈良": "other", "城崎": "other",
    "高野山": "other", "白浜": "other",
}

def main() -> None:
    apply = "--apply" in sys.argv

    region_buckets: dict[str, list[dict]] = {"kyoto": [], "osaka": [], "other": []}
    files_to_remove = []
    for f in ROOT.rglob("*.json"):
        if "_archive" in f.parts: continue
        data = json.loads(f.read_text(encoding="utf-8"))
        for h in data:
            region = CITY_TO_REGION.get(h["city"])
            if region is None:
                print(f"WARN unknown city {h['city']}"); continue
            region_buckets[region].append(h)
        files_to_remove.append(f)

    print("合并结果：")
    for region, hs in region_buckets.items():
        print(f"  {region}.json: {len(hs)} hotels")
    print(f"将删除 {len(files_to_remove)} 个旧 json")

    if not apply:
        print("[DRY-RUN]"); return

    # 写新 3 个
    for region, hs in region_buckets.items():
        target = ROOT / f"{region}.json"
        target.write_text(json.dumps(hs, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"写 {target}")

    # 删旧文件 + 旧目录
    for f in files_to_remove:
        f.unlink()
    for sub in ["kyoto", "osaka", "kobe_area", "other"]:
        d = ROOT / sub
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
        elif d.is_dir():
            # other 下面有子目录·递归删空
            for sub2 in d.iterdir():
                if sub2.is_dir() and not any(sub2.iterdir()):
                    sub2.rmdir()
            if not any(d.iterdir()):
                d.rmdir()
    print("[APPLIED]")

if __name__ == "__main__":
    main()
