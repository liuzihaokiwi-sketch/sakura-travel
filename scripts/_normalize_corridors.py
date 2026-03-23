# -*- coding: utf-8 -*-
"""
scripts/_normalize_corridors.py
把 activity_clusters 里遗留的 kyo_ / osa_ 前缀 corridor key
统一迁移到无前缀的权威体系。

迁移映射：
  kyo_arashiyama   → arashiyama
  kyo_fushimi      → fushimi
  kyo_nijo         → nijo
  kyo_nishikyo     → nishikyo
  kyo_okazaki      → okazaki
  kyo_zen_garden   → zen_garden
  osa_sakurajima   → sakurajima
  osa_nakanoshima  → nakanoshima   (保留，osa_ 是区分大阪子区）

幂等：可反复运行。
"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

# 只做语义相同的合并；osa_nakanoshima 保留（和京都的地名无歧义）
REMAP = {
    "kyo_arashiyama": "arashiyama",
    "kyo_fushimi":    "fushimi",
    "kyo_nijo":       "nijo",
    "kyo_nishikyo":   "nishikyo",
    "kyo_okazaki":    "okazaki",
    "kyo_zen_garden": "zen_garden",
    "osa_sakurajima": "sakurajima",  # osa_ 前缀是冗余的，sakurajima 在大阪无歧义
}

async def main():
    async with AsyncSessionLocal() as s:
        total = 0
        for old, new in REMAP.items():
            r = await s.execute(
                text("UPDATE activity_clusters SET primary_corridor = :new WHERE primary_corridor = :old"),
                {"old": old, "new": new}
            )
            if r.rowcount:
                print(f"  UPDATED {r.rowcount:2d} rows: {old} → {new}")
                total += r.rowcount
            else:
                print(f"  SKIP (0 rows): {old}")
        await s.commit()
    print(f"\ndone: {total} rows updated")

if __name__ == "__main__":
    asyncio.run(main())
