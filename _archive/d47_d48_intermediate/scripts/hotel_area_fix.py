"""D47 area 错配修正（手工 audit 后）.

修正 4 家：
- kyo_nijo_central_takagamine_shou_huo_hotel: nijo_central → kitayama (鷹峯)
- kyo_shijo_kawaramachi_granbell_hotel: shijo_kawaramachi → gion_higashiyama
- kyo_kita_roku_kyoto_lxr: kita → kitayama (鷹峯)
- kyo_arashiyama_hong_ye_jia_honkan_takao_sanso: arashiyama → takao
- kyo_arashiyama_kibune_teng_wu: arashiyama → kibune

同时 id 里的 area 段也要同步改。
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DATA = Path("japan/kansai/hotels/data/hotels__kansai.json")

FIXES = [
    # (old_id, new_area)
    ("kyo_nijo_central_takagamine_shou_huo_hotel", "kitayama"),
    ("kyo_shijo_kawaramachi_granbell_hotel", "gion_higashiyama"),
    ("kyo_kita_roku_kyoto_lxr", "kitayama"),
    ("kyo_arashiyama_hong_ye_jia_honkan_takao_sanso", "takao"),
    ("kyo_arashiyama_kibune_teng_wu", "kibune"),
]


def main() -> None:
    apply = "--apply" in sys.argv
    data = json.loads(DATA.read_text(encoding="utf-8"))

    by_id = {h["id"]: h for h in data}
    existing = set(by_id)

    changes = []
    for old_id, new_area in FIXES:
        h = by_id.get(old_id)
        if not h:
            print(f"NOT FOUND: {old_id}")
            continue
        old_area = h["area"]
        # id 里的 area 段也要同步改：拆解 "kyo_<area>_<slug>"
        parts = old_id.split("_", 2)  # kyo, area, slug
        if len(parts) < 3:
            new_id = old_id  # 无法重组
        else:
            city_prefix = parts[0]
            slug = parts[2]
            # 注意 area 可能含下划线如 nijo_central·所以这里要更精细
            # 取已知 old_area 替换
            if old_id.startswith(f"{city_prefix}_{old_area}_"):
                new_id = f"{city_prefix}_{new_area}_{old_id[len(city_prefix)+1+len(old_area)+1:]}"
            else:
                new_id = old_id
        changes.append((old_id, new_id, old_area, new_area))
        if apply:
            h["area"] = new_area
            if new_id != old_id:
                # 防重
                candidate = new_id
                n = 2
                while candidate in (existing - {old_id}):
                    candidate = f"{new_id}_{n}"
                    n += 1
                h["id"] = candidate
                existing.discard(old_id)
                existing.add(candidate)

    print(f"changes: {len(changes)}")
    for old_id, new_id, old_area, new_area in changes:
        print(f"  {old_id}")
        print(f"    area: {old_area} → {new_area}")
        if old_id != new_id:
            print(f"    id:   → {new_id}")

    if apply:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("\n[APPLIED]")
    else:
        print("\n[DRY-RUN]")


if __name__ == "__main__":
    main()
