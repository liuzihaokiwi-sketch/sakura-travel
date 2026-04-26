"""Phase C: 解析携程酒店详情页 HTML，提取 13 个详情层字段。

关键数据结构:
  - "hotelBaseInfo": 权威元信息（starInfo / nameInfo / newHighlights）
  - "newHighlights.list[].tagTitle": 酒店特色标签（温泉泡汤/SPA/日式早餐/亲子...）
  - "wholePoiInfoList": POI 列表（地铁/火车站/景点 + 距离）
  - subScore 多次出现（评分项）
  - positiveCommentTags / commentTag / goodCommentTag: 好评关键词
  - 开业年 / 房间数：详情页没直接暴露，从介绍文本或用户评论推断风险高 → 留空
"""
import json
import re
import sys
from pathlib import Path


# 特色标签 → 字段映射
ONSEN_TAGS = {'温泉泡汤', '私汤', '温泉', '天然温泉', '露天温泉', '温泉池'}
SHUTTLE_TAGS = {'免费接送', '免费机场接送', '免费班车', '免费接站', '接驳车', '免费机场班车'}
KID_TAGS = {'亲子', '亲子酒店', '亲子房', '儿童乐园', '超赞亲子', '儿童菜单', '亲子主题'}
BREAKFAST_EXCELLENT_TAGS = {'丰盛早餐', '早餐很棒', '精致早餐', '日式早餐', '西式早餐', '自助早餐', '早餐超赞', '早餐丰富'}


def extract_next_f_chunks(html: str) -> str:
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', html, re.DOTALL)
    joined_raw = ''.join(chunks)
    try:
        return json.loads('"' + joined_raw + '"')
    except Exception:
        try:
            return joined_raw.encode().decode('unicode_escape')
        except Exception:
            return joined_raw


def find_json_block(text: str, marker: str, start_pos: int = 0) -> str | None:
    idx = text.find(f'"{marker}":', start_pos)
    if idx < 0:
        return None
    start = idx + len(f'"{marker}":')
    if start >= len(text):
        return None
    c = text[start]
    if c == '{':
        open_c, close_c = '{', '}'
    elif c == '[':
        open_c, close_c = '[', ']'
    else:
        end = start
        while end < len(text) and text[end] not in ',}]':
            end += 1
        return text[start:end]
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if esc:
            esc = False
            continue
        if ch == '\\':
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
        if in_str:
            continue
        if ch == open_c:
            depth += 1
        elif ch == close_c:
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def parse_highlight_tags(text: str) -> set[str]:
    """从 hotelBaseInfo.newHighlights.list 抓所有 tagTitle。"""
    tags = set()
    # 只在 hotelBaseInfo 上下文内抓（避免评论里的 tagTitle 污染）
    base = find_json_block(text, 'hotelBaseInfo')
    if not base:
        return tags
    # 只抓 newHighlights 内的
    hl_idx = base.find('"newHighlights"')
    if hl_idx < 0:
        return tags
    hl_block = base[hl_idx:hl_idx + 10000]
    for m in re.finditer(r'"tagTitle":"([^"]{1,15})"', hl_block):
        tags.add(m.group(1))
    return tags


def parse_subscores(text: str) -> dict:
    sub = {}
    # 优先 scoreDetail: [{showName, showScore, showType}]
    block = find_json_block(text, 'scoreDetail')
    if block:
        for m in re.finditer(r'"showName":"([^"]{1,8})"[^{}]{0,100}"showScore":"([0-9.]+)"', block):
            c, n = m.group(1), m.group(2)
            mapping = {'卫生': 'hygiene', '设施': 'facility', '环境': 'environment', '服务': 'service'}
            if c in mapping:
                try:
                    v = float(n)
                    if 0 < v <= 5.0:
                        sub[mapping[c]] = v
                except ValueError:
                    pass
    # 次选 subScore:[{content, number}]
    if len(sub) < 3:
        for m in re.finditer(r'"content":"([^"]{1,8})"[^{}]{0,100}"number":"([0-9.]+)"', text):
            c, n = m.group(1), m.group(2)
            mapping = {'卫生': 'hygiene', '设施': 'facility', '环境': 'environment', '服务': 'service'}
            if c in mapping and mapping[c] not in sub:
                try:
                    v = float(n)
                    if 0 < v <= 5.0:
                        sub[mapping[c]] = v
                except ValueError:
                    pass
    return sub if len(sub) >= 3 else {}


def parse_nearest_station(text: str) -> tuple[str, int] | None:
    block = find_json_block(text, 'wholePoiInfoList')
    if not block:
        return None
    try:
        pois = json.loads(block)
    except Exception:
        return None
    best = None
    for p in pois:
        t = p.get('type', '')
        if t not in ('metro', 'station', 'subway'):
            continue
        name = p.get('poiName') or p.get('desc')
        dist_raw = p.get('walkDriveDistance') or p.get('distance', '')
        try:
            dist_m = int(float(dist_raw))
        except (TypeError, ValueError):
            m = re.search(r'([\d.]+)\s*(米|公里|千米|km)', str(dist_raw))
            if not m:
                continue
            v = float(m.group(1))
            if m.group(2) in ('公里', '千米', 'km'):
                v *= 1000
            dist_m = int(v)
        if not name:
            continue
        if best is None or dist_m < best[1]:
            best = (name, dist_m)
    return best


def parse_review_keywords(text: str) -> list[str]:
    keywords = []
    seen = set()
    # 优先找 goodCommentTags / commentTagList 结构
    for marker in ['goodCommentTags', 'commentTagList', 'positiveCommentTags']:
        block = find_json_block(text, marker)
        if block:
            for m in re.finditer(r'"(?:tagName|name|content|goodTagName)":"([^"]{2,15})"', block):
                tag = m.group(1)
                if tag in seen:
                    continue
                if tag in ('卫生', '设施', '环境', '服务', '位置', '综合'):
                    continue
                seen.add(tag)
                keywords.append(tag)
                if len(keywords) >= 20:
                    return keywords
    return keywords


def parse(html_path: str) -> dict:
    html = Path(html_path).read_text(encoding='utf-8', errors='replace')
    text = extract_next_f_chunks(html)
    if not text:
        text = html

    result = {}
    tags = parse_highlight_tags(text)

    # ---- detailDescPopTags 结构化字段（权威）----
    pop_block = find_json_block(text, 'detailDescPopTags')
    if pop_block:
        try:
            pops = json.loads(pop_block)
            for p in pops:
                t = p.get('type', '')
                v = p.get('value', '')
                if t == 'openTime':
                    m = re.search(r'(\d{4})', v)
                    if m:
                        y = int(m.group(1))
                        if 1900 < y < 2030:
                            result['opened_year'] = y
                elif t == 'fitmentTime':
                    m = re.search(r'(\d{4})', v)
                    if m:
                        y = int(m.group(1))
                        if 1900 < y < 2030:
                            result['renovated_year'] = y
                elif t == 'roomNum':
                    m = re.search(r'(\d+)', v)
                    if m:
                        n = int(m.group(1))
                        if 1 <= n <= 5000:
                            result['room_count'] = n
        except Exception:
            pass

    # ---- fallback: hotelOverview-label_item HTML ----
    if 'opened_year' not in result or 'room_count' not in result:
        overview_items = re.findall(r'hotelOverview-label_item[^>]*>([^<]{2,50})</li>', html)
        for item in overview_items:
            if '开业' in item and 'opened_year' not in result:
                m = re.search(r'(\d{4})', item)
                if m:
                    y = int(m.group(1))
                    if 1900 < y < 2030:
                        result['opened_year'] = y
            elif ('装修' in item or '翻新' in item) and 'renovated_year' not in result:
                m = re.search(r'(\d{4})', item)
                if m:
                    y = int(m.group(1))
                    if 1900 < y < 2030:
                        result['renovated_year'] = y
            elif ('客房数' in item or '房间数' in item) and 'room_count' not in result:
                m = re.search(r'(\d+)', item)
                if m:
                    n = int(m.group(1))
                    if 1 <= n <= 5000:
                        result['room_count'] = n

    # ---- hotelComment: 总评分 + 点评数 ----
    comment_block = find_json_block(text, 'hotelComment')
    if comment_block:
        cm = re.search(r'"score":"([0-9.]+)"', comment_block)
        if cm:
            try:
                v = float(cm.group(1))
                if 0 < v <= 5.0:
                    result['ctrip_rating'] = v
            except ValueError:
                pass
        tc = re.search(r'"totalComment":(\d+)', comment_block)
        if tc:
            result['ctrip_review_count'] = int(tc.group(1))

    # ---- 特色识别 ----
    if tags & ONSEN_TAGS or any('温泉' in t for t in tags):
        result['has_onsen_bath'] = True
    if tags & SHUTTLE_TAGS or any('接送' in t or '接站' in t or '班车' in t for t in tags):
        result['free_shuttle'] = True
    if tags & KID_TAGS or any('亲子' in t or '儿童' in t for t in tags):
        result['kid_friendly'] = True

    # ---- subscores ----
    subs = parse_subscores(text)
    if subs:
        result['rating_subscores'] = subs

    # ---- nearest station ----
    st = parse_nearest_station(text)
    if st:
        result['nearest_station'], result['nearest_station_distance_m'] = st

    # ---- review keywords ----
    kws = parse_review_keywords(text)
    if kws:
        result['review_keywords'] = kws

    # ---- breakfast ----
    has_breakfast_tag = any('早餐' in t for t in tags)
    if has_breakfast_tag:
        # 特色里提到早餐 → 大概率 excellent（携程只有真值得才加 tag）
        result['breakfast'] = 'included'
        result['breakfast_highlight'] = 'excellent'
    else:
        # 其次：review_keywords 里有早餐正面词
        breakfast_kws = [k for k in kws if '早餐' in k]
        if breakfast_kws:
            positive = ['丰盛', '好吃', '棒', '美味', '精致', '多样', '赞', '鲜', '超赞', '丰富']
            value = ['性价比', '划算', '实惠', '超值']
            if any(any(p in k for p in positive) for k in breakfast_kws):
                result['breakfast_highlight'] = 'excellent'
            elif any(any(p in k for p in value) for k in breakfast_kws):
                result['breakfast_highlight'] = 'value_for_money'

    # opened_year / renovated_year / room_count：详情页暴露不完整，统一留空（硬规：不瞎猜）

    return result


def main():
    src = sys.argv[1]
    data = parse(src)
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
