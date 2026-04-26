"""合并 first-round 和 retry 的候选，输出最终 best_match.json。"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from merge_all import best_match

HOTELS = Path('d:/projects/projects/travel-ai/japan/kansai/assembly/hotels/data/hotels__kansai.json')
# 使用备份做读取（JSON 已被我们 cp 过，但未修改）
BACKUP = Path('d:/tmp/hotels__kansai.backup.json')
SEARCH = Path('d:/tmp/ctrip_matched_all.json')
RETRY = Path('d:/tmp/ctrip_retry.json')
OUT = Path('d:/tmp/ctrip_final_match.json')


def main():
    hotels = json.loads(BACKUP.read_text(encoding='utf-8'))
    search = {r['our_id']: r for r in json.loads(SEARCH.read_text(encoding='utf-8'))}
    retry = {r['our_id']: r for r in json.loads(RETRY.read_text(encoding='utf-8'))} if RETRY.exists() else {}

    results = []
    for h in hotels:
        cands = []
        cands.extend((search.get(h['id']) or {}).get('matches') or [])
        cands.extend((retry.get(h['id']) or {}).get('matches') or [])
        # 去重
        seen = set()
        dedup = []
        for c in cands:
            cid = c.get('id')
            if cid and cid not in seen:
                seen.add(cid)
                dedup.append(c)

        best, info = best_match(h, dedup) if dedup else (None, {})
        unverified = True
        if best:
            s = info.get('score', 0)
            sim = info.get('sim', 0)
            cont = info.get('cont', 0)
            city_hit = info.get('city_hit', False)
            if s >= 0.65 or (s >= 0.5 and city_hit and (sim >= 0.4 or cont >= 0.6)) or (s >= 0.45 and city_hit and cont >= 0.7):
                unverified = False

        r = {
            'our_id': h['id'],
            'our_name_zh': h.get('name_zh', ''),
            'our_city': h['city'],
            'ctrip_id': best.get('id') if best else None,
            'ctrip_name': best.get('word') if best else None,
            'ctrip_lat': best.get('gLat') if best else None,
            'ctrip_lon': best.get('gLon') if best else None,
            'match_score': info.get('score', 0),
            'name_sim': info.get('sim', 0),
            'contains_score': info.get('cont', 0),
            'city_hit': info.get('city_hit', False),
            'unverified': unverified,
        }
        results.append(r)

    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    total = len(results)
    matched = sum(1 for r in results if not r['unverified'])
    print(f'Total: {total}  Matched: {matched} ({matched*100/total:.1f}%)  Unverified: {total - matched}')


if __name__ == '__main__':
    main()
