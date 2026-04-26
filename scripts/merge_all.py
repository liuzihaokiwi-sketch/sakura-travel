"""Phase D: 合并所有采集结果写回 hotels__kansai.json。

输入：
  - hotels__kansai.json (原始)
  - ctrip_matched_all.json (首轮 search)
  - ctrip_retry.json (补救轮 search)
  - ctrip_details/*.html (详情页)
  - ULTRA_LUXURY_BRANDS (常量)

输出：
  - hotels__kansai.json (原地更新 budget_tier + 13 新字段)
  - scripts/hotel_ctrip_tagging_log.md (打标依据记录)
  - /d/tmp/unmatched.md (未匹配清单)

合并顺序：
  1. 重跑匹配（合并首轮+补救的 matches）
  2. 对每家酒店：
     a) 计算新 budget_tier：ultra_luxury 白名单/价格 → 否则旧 mid→comfort / high→premier / luxury→luxury 同义映射
     b) 如果匹配命中：填 ctrip_rating / ctrip_review_count / ctrip_hotel_type / experience_tags
     c) 如果有详情页：填 13 详情层字段
  3. unverified 酒店：只做 budget_tier 同义映射，其他字段留空
"""
import json
import re
import sys
from pathlib import Path
from difflib import SequenceMatcher


HOTELS_FILE = Path('d:/projects/projects/travel-ai/japan/kansai/assembly/hotels/data/hotels__kansai.json')
SEARCH_FILE = Path('d:/tmp/ctrip_matched_all.json')
RETRY_FILE = Path('d:/tmp/ctrip_retry.json')
ROUND3_FILE = Path('d:/tmp/ctrip_round3.json')
DETAILS_DIR = Path('d:/tmp/ctrip_details')
LOG_FILE = Path('d:/projects/projects/travel-ai/scripts/hotel_ctrip_tagging_log.md')
UNMATCHED_FILE = Path('d:/tmp/unmatched.md')


# ultra_luxury 品牌白名单（按 SOP §三）
ULTRA_LUXURY_BRANDS = [
    'ritz-carlton', 'ritz carlton', '丽思卡尔顿',
    'four seasons', '四季',
    'aman ', 'amanemu',
    'park hyatt', '柏悦',
    'hoshinoya', '星のや', '星野屋',
    'suiran', '翠岚',
    'mitsui', '三井',
    'six senses', '六善',
    'bulgari', '宝格丽',
    'banyan tree', '悦榕庄',  # 虽然 SOP 没列，实为同档奢华
    'park hyatt', 'mandarin oriental', '文华东方',
    'st. regis', '瑞吉',
    'rosewood', '瑰丽',
]


CITY_CN_MAP = {
    'kyoto': {'京都', '京都府'},
    'osaka': {'大阪', '大阪府'},
    'kobe': {'神户', '神戶', '兵库', '兵庫'},
    'nara': {'奈良'},
    'arima': {'有马', '神户', '兵库'},
    'kinosaki': {'城崎', '丰冈', '兵库'},
    'koyasan': {'高野山', '和歌山'},
    'shirahama': {'白滨', '白浜', '和歌山'},
}


def normalize(s: str) -> str:
    if not s:
        return ''
    s = s.lower()
    s = re.sub(r'[()（）・·\s\-_,\.，。/\&]+', '', s)
    return s


def name_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def contains_score(our: str, ctrip: str) -> float:
    ourn = normalize(our)
    cn = normalize(ctrip)
    if not ourn or not cn:
        return 0
    if ourn in cn:
        return 1.0
    if cn in ourn:
        return 0.9
    longest = 0
    for i in range(len(ourn)):
        for j in range(i + 2, len(ourn) + 1):
            if ourn[i:j] in cn:
                longest = max(longest, j - i)
    return longest / len(ourn) if ourn else 0


def best_match(our_hotel: dict, candidates: list[dict]) -> tuple[dict | None, dict]:
    """返回 (best_candidate, scoring_info)。"""
    city_tokens = CITY_CN_MAP.get(our_hotel['city'], set())
    our_zh = our_hotel.get('name_zh', '')
    our_ja = our_hotel.get('name_ja', '')
    scored = []
    for m in candidates:
        country = (m.get('countryName') or '').lower()
        if country and '日本' not in (m.get('countryName') or '') and 'japan' not in country:
            continue
        city_hit = any(tok in (m.get('cityName') or '') for tok in city_tokens) if city_tokens else True
        sim = max(
            name_similarity(m.get('word', ''), our_zh),
            name_similarity(m.get('word', ''), our_ja),
            name_similarity(m.get('eName', ''), our_ja),
        )
        cont = max(
            contains_score(our_zh, m.get('word', '')),
            contains_score(our_ja, m.get('word', '') or m.get('eName', '')),
        )
        score = sim * 0.55 + cont * 0.30 + (0.15 if city_hit else 0)
        scored.append({'match': m, 'score': score, 'sim': sim, 'cont': cont, 'city_hit': city_hit})
    if not scored:
        return None, {'reason': 'no_japan_match'}
    scored.sort(key=lambda x: x['score'], reverse=True)
    best = scored[0]
    return best['match'], {
        'score': round(best['score'], 3),
        'sim': round(best['sim'], 3),
        'cont': round(best['cont'], 3),
        'city_hit': best['city_hit']
    }


def decide_budget_tier(old_tier: str, name_zh: str, name_ja: str, ctrip_star: int | None, price_low_jpy: int) -> tuple[str, str]:
    """返回 (new_tier, reason)"""
    # ultra_luxury 优先判断
    name_lc = f'{name_zh} {name_ja}'.lower()
    brand_hit = None
    for b in ULTRA_LUXURY_BRANDS:
        if b.lower() in name_lc:
            brand_hit = b
            break
    if brand_hit:
        return 'ultra_luxury', f'品牌白名单:{brand_hit}'
    if price_low_jpy and price_low_jpy >= 60000:
        return 'ultra_luxury', f'价格门槛 low_jpy={price_low_jpy} ≥60000'

    # 有携程 star 数据 → 权威映射
    if ctrip_star is not None:
        if ctrip_star >= 5:
            return 'luxury', f'ctrip star={ctrip_star}'
        if ctrip_star == 4:
            return 'premier', f'ctrip star={ctrip_star}'
        if ctrip_star == 3:
            return 'comfort', f'ctrip star={ctrip_star}'
        if ctrip_star <= 2:
            return 'economy', f'ctrip star={ctrip_star}'

    # 旧 tier 同义映射（unverified fallback）
    mapping = {
        'economy': 'economy',
        'mid': 'comfort',
        'high': 'premier',
        'luxury': 'luxury',
    }
    return mapping.get(old_tier, old_tier), f'同义映射 {old_tier}→'


def derive_experience_tags(hotel: dict, ctrip_hotel_type: str | None) -> list[str]:
    """根据 area / name / hotelType 推导 experience_tags"""
    tags = []
    area = hotel.get('area', '')
    name_zh = hotel.get('name_zh', '')
    name_ja = hotel.get('name_ja', '')

    # onsen_ryokan
    if area in ('arima', 'kinosaki', 'arima_onsen', 'kinosaki_onsen', 'shirahama'):
        tags.append('onsen_ryokan')
    elif '温泉' in (name_zh + name_ja):
        tags.append('onsen_ryokan')

    # japanese_ryokan
    if any(s in (name_zh + name_ja) for s in ['旅館', '旅馆', '庵', '御宿', 'Ryokan']):
        if 'onsen_ryokan' not in tags:
            tags.append('japanese_ryokan')

    # shukubo
    if area in ('koyasan', 'koyasan_temple') or '宿坊' in (name_zh + name_ja):
        tags.append('shukubo')

    # machiya
    if hotel.get('city') == 'kyoto':
        if any(s in (name_zh + name_ja) for s in ['町家', '町屋', '京町家']):
            tags.append('machiya')

    # minshuku
    if any(s in (name_zh + name_ja) for s in ['民宿', 'Minshuku']):
        tags.append('minshuku')

    return tags


def map_ctrip_hotel_type(ctrip_star: int | None, ctrip_raw_type: str | None, our_tags: list[str]) -> str | None:
    """携程 hotelType(NORMAL/HOMESTAY...) → 我们的 enum。"""
    if ctrip_raw_type:
        rt = ctrip_raw_type.upper()
        if rt in ('HOMESTAY', 'APARTMENT', 'MINSHUKU'):
            return 'apartment' if rt == 'APARTMENT' else 'minshuku'
    if 'shukubo' in our_tags:
        return 'hotel'  # 宿坊 是寺庙住宿，归 hotel
    if 'onsen_ryokan' in our_tags or 'japanese_ryokan' in our_tags:
        return 'ryokan'
    if 'minshuku' in our_tags:
        return 'minshuku'
    return 'hotel'


def main():
    hotels = json.loads(HOTELS_FILE.read_text(encoding='utf-8'))
    search = {r['our_id']: r for r in json.loads(SEARCH_FILE.read_text(encoding='utf-8'))}
    retry_data = {r['our_id']: r for r in json.loads(RETRY_FILE.read_text(encoding='utf-8'))} if RETRY_FILE.exists() else {}
    round3_data = {r['our_id']: r for r in json.loads(ROUND3_FILE.read_text(encoding='utf-8'))} if ROUND3_FILE.exists() else {}

    # 导入详情解析器
    sys.path.insert(0, str(Path(__file__).parent))
    from parse_ctrip_detail import parse as parse_detail

    log_lines = ['# 酒店携程打标日志（D41）', '',
                 '> 2026-04-25 生成。记录每家酒店 budget_tier 变更和附加字段来源。']
    unmatched_lines = ['# 未匹配酒店清单（unverified）', '']

    stats = {'matched': 0, 'unverified': 0, 'ultra_luxury': 0,
             'with_details': 0, 'exp_tags': 0,
             'tier_dist': {}}

    for h in hotels:
        our_id = h['id']
        # 合并 first-round + retry 的候选
        sres = search.get(our_id, {})
        rres = retry_data.get(our_id, {})
        all_candidates = []
        all_candidates.extend(sres.get('matches', []) or [])
        all_candidates.extend(rres.get('matches', []) or [])
        r3 = round3_data.get(our_id, {})
        all_candidates.extend(r3.get('matches', []) or [])

        # 去重（按 id）
        seen = set()
        dedup = []
        for c in all_candidates:
            cid = c.get('id')
            if cid and cid not in seen:
                seen.add(cid)
                dedup.append(c)

        best, info = best_match(h, dedup) if dedup else (None, {})

        # 匹配置信判断
        matched = False
        if best:
            score = info.get('score', 0)
            sim = info.get('sim', 0)
            cont = info.get('cont', 0)
            city_hit = info.get('city_hit', False)
            if score >= 0.65:
                matched = True
            elif score >= 0.5 and city_hit and (sim >= 0.4 or cont >= 0.6):
                matched = True
            elif score >= 0.45 and city_hit and cont >= 0.7:
                matched = True

        # ---- 清除旧字段准备写新 ----
        old_tier = h.get('budget_tier', 'mid')
        price_low_jpy = h.get('price_range_jpy', {}).get('low', 0)

        # 决定新 budget_tier
        ctrip_star = None
        if matched and best:
            # 携程 API 返回的 cStar 通常是 0；真正的钻级要从列表页 hotelStar 取
            # 这里先没有，用于之后的详情页（hotelBaseInfo.starInfo.level）
            pass

        # 解析详情页（如果有）
        detail_data = {}
        if matched and best and (DETAILS_DIR / f'{best.get("id")}.html').exists():
            try:
                detail_data = parse_detail(str(DETAILS_DIR / f'{best.get("id")}.html'))
                # 从详情页 text 里额外抓 starInfo.level
                import re as _re
                raw_html = (DETAILS_DIR / f'{best.get("id")}.html').read_text(encoding='utf-8', errors='replace')
                m = _re.search(r'"starInfo":\{"level":(\d+)', raw_html)
                if m:
                    ctrip_star = int(m.group(1))
                stats['with_details'] += 1
            except Exception as e:
                log_lines.append(f'  ! 详情解析失败 {our_id}: {e}')

        new_tier, tier_reason = decide_budget_tier(old_tier, h.get('name_zh', ''), h.get('name_ja', ''), ctrip_star, price_low_jpy)
        h['budget_tier'] = new_tier
        stats['tier_dist'].setdefault(new_tier, 0)
        stats['tier_dist'][new_tier] += 1
        if new_tier == 'ultra_luxury':
            stats['ultra_luxury'] += 1

        # experience_tags
        exp_tags = derive_experience_tags(h, None)
        if exp_tags:
            h['experience_tags'] = exp_tags
            stats['exp_tags'] += 1

        # 如果有匹配，写附加字段
        if matched and best:
            stats['matched'] += 1
            # ctrip_rating 从详情页或 cStar
            if detail_data.get('rating_subscores'):
                h['rating_subscores'] = detail_data['rating_subscores']
                # ctrip_rating 也可从 subscores 平均
                vals = list(detail_data['rating_subscores'].values())
                if vals:
                    h['ctrip_rating'] = round(sum(vals) / len(vals), 1)
            # ctrip_review_count 从详情页 hotelComment
            if detail_data.get('ctrip_review_count') is not None:
                h['ctrip_review_count'] = detail_data['ctrip_review_count']
            # ctrip_rating 优先用详情页的 hotelComment.score（比 subscores 平均更权威）
            if detail_data.get('ctrip_rating') is not None:
                h['ctrip_rating'] = detail_data['ctrip_rating']
            # 详情层字段
            for k in ['has_onsen_bath', 'free_shuttle', 'kid_friendly',
                      'nearest_station', 'nearest_station_distance_m',
                      'review_keywords', 'breakfast', 'breakfast_highlight',
                      'opened_year', 'renovated_year', 'room_count']:
                if k in detail_data:
                    h[k] = detail_data[k]
            # hotel type
            hotel_type = map_ctrip_hotel_type(ctrip_star, best.get('hotelType'), exp_tags)
            if hotel_type:
                h['ctrip_hotel_type'] = hotel_type

            log_lines.append(f'- {our_id} ({h["name_zh"]}) ← ctrip {best.get("id")} ({best.get("word")})  [{tier_reason}] score={info.get("score")} details_fields={len(detail_data)}')
        else:
            stats['unverified'] += 1
            unmatched_lines.append(f'- {our_id}: {h["name_zh"]} | {h.get("name_ja","")} | city={h["city"]} area={h.get("area","")} | old_tier={old_tier}→{new_tier}')
            log_lines.append(f'- {our_id} ({h["name_zh"]}) **UNVERIFIED** [{tier_reason}]')

    # 写回
    HOTELS_FILE.write_text(json.dumps(hotels, ensure_ascii=False, indent=2), encoding='utf-8')
    LOG_FILE.write_text('\n'.join(log_lines), encoding='utf-8')
    UNMATCHED_FILE.write_text('\n'.join(unmatched_lines), encoding='utf-8')

    # summary
    print('=' * 60)
    print(f'Total hotels: {len(hotels)}')
    print(f'Matched (wrote ctrip fields): {stats["matched"]}')
    print(f'Unverified (only budget_tier same-meaning map): {stats["unverified"]}')
    print(f'With detail page data: {stats["with_details"]}')
    print(f'With experience_tags: {stats["exp_tags"]}')
    print()
    print('budget_tier distribution (new):')
    for t in ['economy', 'comfort', 'premier', 'luxury', 'ultra_luxury']:
        print(f'  {t:15s} {stats["tier_dist"].get(t, 0)}')


if __name__ == '__main__':
    main()
