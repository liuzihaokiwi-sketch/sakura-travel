"""Phase B: 匹配最佳 hotelId。

增强算法：
1. 硬过滤：country != 日本 / Japan → 淘汰
2. 含关系评分：如果 our_name 的核心词（去除城市/酒店后缀后）出现在 ctrip_name 里 → bonus +0.25
3. 综合 = 名字相似度 * 0.6 + 含关系 bonus * 0.25 + 城市命中 * 0.15
4. 阈值 0.45（放宽）

未命中 / 低分 → 标 unverified，但仍保留 ctrip_id 作为"候选"供人工核对。
"""
import json
import re
import sys
from pathlib import Path
from difflib import SequenceMatcher


CITY_CN_MAP = {
    'kyoto': {'京都', '京都府'},
    'osaka': {'大阪', '大阪府'},
    'kobe': {'神户', '神戶', '兵库', '兵庫'},
    'nara': {'奈良', '奈良县', '奈良県'},
    'arima': {'有马', '神户', '兵库', '兵庫'},
    'kinosaki': {'城崎', '丰冈', '豐岡', '兵库', '兵庫'},
    'koyasan': {'高野山', '和歌山'},
    'shirahama': {'白滨', '白浜', '和歌山'},
}


def normalize(s: str) -> str:
    if not s:
        return ''
    s = s.lower()
    # 去标点、空格
    s = re.sub(r'[()（）・·\s\-_,\.，。/\&]+', '', s)
    # 繁简
    conv = str.maketrans({'館':'馆', '駅':'驿', '條':'条', '舊':'旧', '鐵':'铁', '團':'团',
                          '樓':'楼', '飯':'饭', '顧':'顾', '寧':'宁', '賓':'宾', '號':'号',
                          '園':'园', '壓':'压', '寶':'宝', '羅':'罗', '輪':'轮', '頓':'顿',
                          '張':'张', '區':'区', '場':'场', '東':'东', '長':'长', '龍':'龙',
                          '萬':'万', '興':'兴', '華':'华'})
    s = s.translate(conv)
    return s


def extract_core_tokens(name: str) -> set[str]:
    """从酒店名提取核心词：去掉城市/通用词/数字。"""
    n = normalize(name)
    # 去掉常见后缀
    for suf in ['酒店', '饭店', '旅馆', '宾馆', '民宿', '公寓', 'hotel', 'resort',
                '京都', '大阪', '神户', '奈良', '有马', '城崎', '高野山', '白滨',
                'kyoto', 'osaka', 'kobe', 'nara']:
        n = n.replace(suf, '')
    # 拆分 2-4 字片段
    tokens = set()
    if len(n) >= 2:
        tokens.add(n[:4])
        tokens.add(n[:3])
        tokens.add(n[:2])
    return {t for t in tokens if len(t) >= 2}


def name_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def contains_score(our_name: str, ctrip_name: str) -> float:
    """our_name 的核心词是否出现在 ctrip_name 中。"""
    our_norm = normalize(our_name)
    ctrip_norm = normalize(ctrip_name)
    if not our_norm or not ctrip_norm:
        return 0
    # 如果 our_name 完整出现在 ctrip_name → 1.0
    if our_norm in ctrip_norm:
        return 1.0
    if ctrip_norm in our_norm:
        return 0.9
    # 计算 our_name 字符有多少出现在 ctrip_name 里（连续的）
    # 用最长公共子串
    longest = 0
    for i in range(len(our_norm)):
        for j in range(i + 2, len(our_norm) + 1):
            if our_norm[i:j] in ctrip_norm:
                longest = max(longest, j - i)
    if len(our_norm) == 0:
        return 0
    return longest / len(our_norm)


def match_one(record: dict) -> dict:
    our_id = record['our_id']
    our_name_zh = record.get('our_name_zh', '')
    our_name_ja = record.get('our_name_ja', '')
    our_city = record.get('our_city', '')
    matches = record.get('matches', [])

    if not matches:
        return {
            'our_id': our_id,
            'our_name_zh': our_name_zh,
            'our_city': our_city,
            'ctrip_id': None,
            'match_score': 0,
            'match_reason': 'no_match_from_api',
            'unverified': True
        }

    city_tokens = CITY_CN_MAP.get(our_city, set())

    scored = []
    for m in matches:
        ctrip_word = m.get('word', '') or ''
        ctrip_ename = m.get('eName', '') or ''
        ctrip_city = m.get('cityName', '') or ''
        ctrip_country = m.get('countryName', '') or ''

        # 硬过滤 1：必须是日本酒店
        if ctrip_country and '日本' not in ctrip_country and 'japan' not in ctrip_country.lower():
            continue

        city_hit = any(tok in ctrip_city for tok in city_tokens) if city_tokens else True

        # 相似度 和 包含度 两套算法取高
        sim_zh = name_similarity(ctrip_word, our_name_zh)
        sim_ja_vs_word = name_similarity(ctrip_word, our_name_ja)
        sim_ja_vs_ename = name_similarity(ctrip_ename, our_name_ja)
        best_sim = max(sim_zh, sim_ja_vs_word, sim_ja_vs_ename)

        cont_zh = contains_score(our_name_zh, ctrip_word)
        cont_ja = contains_score(our_name_ja, ctrip_word) if our_name_ja else 0
        cont_ja_e = contains_score(our_name_ja, ctrip_ename) if (our_name_ja and ctrip_ename) else 0
        best_cont = max(cont_zh, cont_ja, cont_ja_e)

        # 加权
        score = best_sim * 0.55 + best_cont * 0.30 + (0.15 if city_hit else 0)

        scored.append({
            'match': m,
            'score': score,
            'sim': best_sim,
            'cont': best_cont,
            'city_hit': city_hit
        })

    if not scored:
        return {
            'our_id': our_id,
            'our_name_zh': our_name_zh,
            'our_city': our_city,
            'ctrip_id': None,
            'match_score': 0,
            'match_reason': 'all_matches_outside_japan',
            'unverified': True
        }

    scored.sort(key=lambda x: x['score'], reverse=True)
    best = scored[0]

    # 多阈值判断
    # 放行条件：score>=0.65 OR (score>=0.5 且 city_hit 且 (sim>=0.4 或 cont>=0.6))
    if best['score'] >= 0.65:
        unverified = False
        tag = 'high_confidence'
    elif best['score'] >= 0.5 and best['city_hit'] and (best['sim'] >= 0.4 or best['cont'] >= 0.6):
        unverified = False
        tag = 'medium_confidence'
    elif best['score'] >= 0.45 and best['city_hit']:
        unverified = False
        tag = 'low_confidence'
    else:
        unverified = True
        tag = 'unverified'

    reason = f"sim={best['sim']:.2f} cont={best['cont']:.2f} city_hit={best['city_hit']} score={best['score']:.2f} tag={tag}"

    return {
        'our_id': our_id,
        'our_name_zh': our_name_zh,
        'our_city': our_city,
        'ctrip_id': best['match'].get('id'),
        'ctrip_name': best['match'].get('word'),
        'ctrip_ename': best['match'].get('eName'),
        'ctrip_lat': best['match'].get('gLat'),
        'ctrip_lon': best['match'].get('gLon'),
        'ctrip_city_name': best['match'].get('cityName'),
        'match_score': round(best['score'], 3),
        'name_sim': round(best['sim'], 3),
        'contains_score': round(best['cont'], 3),
        'match_reason': reason,
        'unverified': unverified,
    }


def main():
    src = sys.argv[1]
    dst = sys.argv[2]

    records = json.loads(Path(src).read_text(encoding='utf-8'))
    results = [match_one(r) for r in records]

    Path(dst).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')

    total = len(results)
    matched = sum(1 for r in results if not r['unverified'])
    unverified = total - matched
    print(f'Total: {total}')
    print(f'Matched: {matched}  ({matched*100/total:.1f}%)')
    print(f'Unverified: {unverified}  ({unverified*100/total:.1f}%)')

    from collections import Counter
    by_city = Counter()
    by_city_unv = Counter()
    for r in results:
        by_city[r['our_city']] += 1
        if r['unverified']:
            by_city_unv[r['our_city']] += 1
    print('\nBy city (matched / total):')
    for city, total_c in sorted(by_city.items(), key=lambda x: -x[1]):
        unv = by_city_unv[city]
        print(f'  {city:12s} {total_c - unv:3d} / {total_c:3d}  ({(total_c - unv)*100/total_c:.0f}%)')


if __name__ == '__main__':
    main()
