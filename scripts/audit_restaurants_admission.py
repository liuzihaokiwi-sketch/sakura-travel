"""
D46 餐厅准入审计脚本

枚举权威：docs/项目核心/字段权威.md §2.5 努力档枚举（餐厅 4 档·与酒店 3 档不互通）
规则细节：docs/操作SOP/上线前/数据池构建/餐厅规范.md §3.7 + §四

- 算每条店的努力档（effortless/low_effort/medium_effort/hard_effort·餐厅 4 档专用）
- 统计努力档分布·标记违反硬比例
- 按 cuisine 类目最低覆盖检查
- 按 5 入口（Y 轴）粗判（关键词扫·细判由人工）

用法: python scripts/audit_restaurants_admission.py [japan/kansai/restaurants/]
"""

import json
import sys
import glob
import os
import collections
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')


def classify_effort(r: dict) -> str:
    """按 reservation_difficulty + queue_level + note.预约 算努力档"""
    rd = r.get('reservation_difficulty', 'none')
    ql = r.get('queue_level', 'mild')
    note = r.get('note', {}) if isinstance(r.get('note'), dict) else {}
    yuyue = (note.get('预约', '') or '').lower()
    daodian = (note.get('到店提醒', '') or '').lower()

    is_hard = any(kw in yuyue + daodian for kw in [
        '常客优先', '常客制', '熟人介绍', '月初打电话', '月初订',
        '提前 3', '提前 6', '半年', '3-6 个月', '常客'
    ])
    if rd == 'must' and is_hard:
        return 'hard_effort'
    if rd == 'must':
        return 'medium_effort'
    if rd == 'none' and ql in ('none', 'mild'):
        return 'effortless'
    if rd == 'recommended' or ql in ('mild', 'medium', 'high'):
        return 'low_effort'
    return 'low_effort'  # 兜底


def classify_y_axis(r: dict) -> set:
    """关键词粗判 5 入口·细判仍需人工"""
    note = r.get('note', {}) if isinstance(r.get('note'), dict) else {}
    text = ' '.join([
        note.get('简介', ''),
        ' '.join(note.get('亮点', []) or []),
        note.get('到店提醒', ''),
    ]).lower()
    tabelog = note.get('Tabelog 分数') or note.get('评分')
    season = r.get('season_months')
    tier = r.get('tier', '')

    hits = set()
    # A. 味道 top
    if (tabelog and tabelog >= 3.6) or any(kw in text for kw in ['米其林', '百名店', '三星', '二星', '一星']):
        hits.add('A')
    # B. 体验仪式
    if any(kw in text for kw in [
        '演出', '出片', '小红书', '旅のしおり', '重箱', '剧场', '主题',
        '古民家', '町家改造', '町屋改装', '氛围', '氛围感', '打卡', 'sns', 'fusion'
    ]):
        hits.add('B')
    # C. 本地独家
    if any(kw in text for kw in [
        '本地人', '隐家', '隐藏', '住宅区隐店', '师承', '师事', '师从',
        '游客攻略少', '中文攻略少', '冷门', '私藏'
    ]):
        hits.add('C')
    # D. 招牌代表
    if any(kw in text for kw in [
        '发祥', '元祖', '老铺', '名物', '百年', '80 年', '90 年',
        '昭和', '明治', '大正', '关西 dna', 'dna', '关西 国民', 'みんなの'
    ]):
        hits.add('D')
    # E. 景观/季节
    if season or any(kw in text for kw in [
        '川床', '红叶', '樱花', '望景', '景观', '保津川', '鸭川', '桂川',
        '夏季限定', '冬季限定', '季节限定', '春限定', '秋限定'
    ]):
        hits.add('E')

    return hits


def main(target='japan/kansai/restaurants/'):
    files = sorted(glob.glob(f'{target}/**/*.json', recursive=True))
    files = [f for f in files if '_archive' not in f]

    total = 0
    by_effort = collections.Counter()
    by_cuisine = collections.defaultdict(list)
    by_y_axis = collections.Counter()
    no_y_axis = []  # 5 入口都不命中
    hard_effort_list = []
    cuisine_to_efforts = collections.defaultdict(lambda: collections.Counter())

    for f in files:
        d = json.load(open(f, encoding='utf-8'))
        items = list(d.values()) if isinstance(d, dict) else d
        for r in items:
            if r.get('depth') == 'skeleton':
                continue
            total += 1
            effort = classify_effort(r)
            y_hits = classify_y_axis(r)

            by_effort[effort] += 1
            for cu in r.get('cuisine', []):
                by_cuisine[cu].append({
                    'id': r.get('id'),
                    'effort': effort,
                    'y': y_hits,
                    'tier': r.get('tier'),
                    '店名': (r.get('note', {}) or {}).get('店名', '') if isinstance(r.get('note'), dict) else '',
                })
                cuisine_to_efforts[cu][effort] += 1
            for y in y_hits:
                by_y_axis[y] += 1
            if not y_hits:
                no_y_axis.append({
                    'id': r.get('id'),
                    'tier': r.get('tier'),
                    '店名': (r.get('note', {}) or {}).get('店名', '') if isinstance(r.get('note'), dict) else '',
                    'tabelog': (r.get('note', {}) or {}).get('Tabelog 分数') if isinstance(r.get('note'), dict) else None,
                })
            if effort == 'hard_effort':
                hard_effort_list.append({
                    'id': r.get('id'),
                    'tier': r.get('tier'),
                    '店名': (r.get('note', {}) or {}).get('店名', '') if isinstance(r.get('note'), dict) else '',
                })

    print(f'=== D46 餐厅准入审计 ===')
    print(f'总计 {total} 条 full/verified（不含 skel）')
    print()

    # 1. 努力档分布
    print(f'--- 努力档分布（X 轴）---')
    target_pct = {'effortless': (25, 30), 'low_effort': (50, 50), 'medium_effort': (15, 20), 'hard_effort': (5, 12)}
    for effort in ['effortless', 'low_effort', 'medium_effort', 'hard_effort']:
        n = by_effort[effort]
        pct = n / total * 100 if total else 0
        lo, hi = target_pct[effort]
        if effort == 'low_effort':
            status = '✅' if pct >= 40 else '❌ 大缺·重点补'
        elif effort == 'hard_effort':
            status = '✅' if pct <= 12 else '❌ 超上限·必剔'
        else:
            status = '✅' if lo <= pct <= hi else '⚠️'
        print(f'  {effort:15s}: {n:3d} ({pct:.0f}%·目标 {lo}-{hi}%) {status}')
    print()

    # 2. Y 轴 5 入口分布
    print(f'--- Y 轴 5 入口（粗判·关键词扫）---')
    for y in ['A', 'B', 'C', 'D', 'E']:
        print(f'  {y}: {by_y_axis[y]} 条')
    print(f'  无任何入口命中: {len(no_y_axis)} 条 ❌（应剔或人工复核）')
    print()

    # 3. 类目最低覆盖
    print(f'--- 类目最低覆盖检查 ---')
    coverage_target = {
        '寿司': 5, '拉面': 5, '法餐': 5, '烧肉': 5, '鳗鱼': 3,
        '天妇罗': 3, '怀石': 8, '居酒屋': 8, '松叶蟹': 3, '神户牛': 3,
        '大阪烧': 3, '章鱼烧': 3, '串炸': 3,
    }
    for cu, target_n in coverage_target.items():
        actual = len(by_cuisine.get(cu, []))
        # 该类目的努力档分布
        eff_dist = cuisine_to_efforts[cu]
        dist_str = '/'.join(f'{eff_dist[e]}' for e in ['effortless', 'low_effort', 'medium_effort', 'hard_effort'])
        status = '✅' if actual >= target_n else f'❌ 缺 {target_n - actual}'
        print(f'  {cu:8s}: {actual:2d}/{target_n} (eff/low/med/hard = {dist_str}) {status}')
    print()

    # 4. 无 Y 轴清单（建议剔/复核）
    if no_y_axis:
        print(f'--- 无 Y 轴入口·建议剔/人工复核（前 30 条）---')
        for item in no_y_axis[:30]:
            print(f'  {item["id"]:35s} | {item["tier"]:8s} | tabelog={item["tabelog"]} | {item["店名"]}')
        if len(no_y_axis) > 30:
            print(f'  ... 还有 {len(no_y_axis) - 30} 条')
        print()

    # 5. hard_effort 清单（如超 12% 必须从这剔）
    hard_pct = by_effort['hard_effort'] / total * 100 if total else 0
    if hard_pct > 12 and hard_effort_list:
        print(f'--- hard_effort 超上限 {hard_pct:.0f}%·候选剔除清单（按 tier 排序）---')
        tier_order = {'showcase': 0, 'high': 1, 'mid': 2, 'economy': 3}
        sorted_hard = sorted(hard_effort_list, key=lambda x: tier_order.get(x['tier'], 9))
        for item in sorted_hard[:20]:
            print(f'  {item["id"]:35s} | {item["tier"]:8s} | {item["店名"]}')
    print()


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'japan/kansai/restaurants/'
    main(target)
