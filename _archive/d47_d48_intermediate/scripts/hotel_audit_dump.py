"""D47 现池 203 家 audit dump.

输出 markdown 报告：
- 占位 id (h***)
- 套话简介
- 数据来源 URL（ctrip 错位/空占位）
- area 与 city 是否合理
- depth × note 完整度
- tier × city × price 区间是否对得上

输出 → japan/kansai/hotels/_d47_audit_table.md
"""
from __future__ import annotations

import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DATA = Path("japan/kansai/hotels/data/hotels__kansai.json")
OUT = Path("japan/kansai/hotels/_d47_audit_table.md")

CLICHE_PHRASES = ["传统旅馆体验", "一泊二食，睡前泡汤", "睡前泡汤",
                  "传统和风，一泊二食"]
PLACEHOLDER_RE = re.compile(r"_h\d{2,4}$")

TIER_NAMES = {"b1": "经济", "b2": "舒适", "b3": "品质",
              "b4": "高端", "b5": "奢华", "b6": "顶奢"}

KYOTO_BANDS = [("b1", 0, 500), ("b2", 500, 950), ("b3", 950, 1200),
               ("b4", 1200, 2000), ("b5", 2000, 3500), ("b6", 3500, 10**9)]
OTHER_BANDS = [("b1", 0, 400), ("b2", 400, 600), ("b3", 600, 850),
               ("b4", 850, 1250), ("b5", 1250, 2050), ("b6", 2050, 10**9)]


def expected_band(median: float, city: str) -> str:
    table = KYOTO_BANDS if city == "京都" else OTHER_BANDS
    for code, lo, hi in table:
        if lo <= median < hi:
            return code
    return table[-1][0]


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))

    flagged = []
    placeholder = []
    cliche = []
    bad_url = []
    tier_mismatch = []
    skeleton_full_mismatch = []

    for h in data:
        hid = h["id"]
        name = h.get("note", {}).get("店名", "")
        intro = h.get("note", {}).get("简介", "")
        sources = h.get("数据来源", [])
        depth = h.get("depth", "skeleton")
        tier = h.get("tier", "")
        city = h.get("city", "")
        prices = h.get("price_cny_per_night", [])

        flags = []

        if PLACEHOLDER_RE.search(hid):
            flags.append("PLACEHOLDER_ID")
            placeholder.append(hid)

        if any(p in intro for p in CLICHE_PHRASES):
            flags.append("CLICHE")
            cliche.append(hid)

        if not sources or all(s == "https://hotels.ctrip.com/" for s in sources):
            flags.append("EMPTY_URL")
            bad_url.append(hid)

        if depth == "full" and not all(k in h.get("note", {}) for k in ["简介", "亮点", "地址", "房型", "价格", "预约"]):
            flags.append("DEPTH_FULL_INCOMPLETE")
            skeleton_full_mismatch.append(hid)

        if prices and len(prices) >= 1:
            exp = expected_band(prices[0], city)
            if tier != exp:
                flags.append(f"TIER_MISMATCH(exp={exp})")
                tier_mismatch.append(hid)

        if flags:
            flagged.append((hid, name[:40], city, tier, depth, prices, flags))

    # 分类统计
    print(f"total={len(data)} | flagged={len(flagged)}")
    print(f"  PLACEHOLDER_ID:        {len(placeholder)}")
    print(f"  CLICHE:                {len(cliche)}")
    print(f"  EMPTY_URL:             {len(bad_url)}")
    print(f"  DEPTH_FULL_INCOMPLETE: {len(skeleton_full_mismatch)}")
    print(f"  TIER_MISMATCH:         {len(tier_mismatch)}")

    # 写 markdown
    lines = []
    lines.append("# D47 现池 203 家 audit table\n")
    lines.append(f"自动 dump·{len(flagged)} 家有 flag·待 Step 4 逐家迭代修改\n\n")
    lines.append("## 各 flag 计数\n")
    lines.append(f"- **PLACEHOLDER_ID**（占位 id h***）：{len(placeholder)}")
    lines.append(f"- **CLICHE**（套话简介）：{len(cliche)}")
    lines.append(f"- **EMPTY_URL**（数据来源仅 hotels.ctrip.com/ 占位）：{len(bad_url)}")
    lines.append(f"- **DEPTH_FULL_INCOMPLETE**（depth=full 但 note 缺必填）：{len(skeleton_full_mismatch)}")
    lines.append(f"- **TIER_MISMATCH**（迁移前 tier 跟 D47 阈值不符）：{len(tier_mismatch)}")
    lines.append("")

    lines.append("## flag 明细（按 city 分组）\n")
    by_city = defaultdict(list)
    for row in flagged:
        by_city[row[2]].append(row)
    for city in sorted(by_city.keys()):
        rows = by_city[city]
        lines.append(f"### {city}（{len(rows)} 家）\n")
        lines.append("| id | 店名 | tier | depth | 平季中位 | flags |")
        lines.append("|---|---|---|---|---|---|")
        for hid, name, _, tier, depth, prices, flags in rows:
            mid = prices[0] if prices else "-"
            t_name = TIER_NAMES.get(tier, tier)
            lines.append(f"| `{hid}` | {name} | {tier}({t_name}) | {depth} | {mid} | {', '.join(flags)} |")
        lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWritten: {OUT}")


if __name__ == "__main__":
    main()
