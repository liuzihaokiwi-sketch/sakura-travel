"""D47 占位 id 改 slug.

规则：
- 旧 id 形如 `kyo_shijo_kawaramachi_h291` → 用 note.店名 抽英文/罗马字
- 优先抽英文（Hotel/Sora Niwa/...） 退而抽日文罗马字
- slug = lower + replace [\\s\\-/] → _ + 去除非 [a-z0-9_]
- 拼回：`{城市前缀}_{area}_{slug}`
- 防重复：若已存在，追加 _2 _3

干跑（dry-run）输出对照表，--apply 时执行。
"""
from __future__ import annotations

import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DATA = Path("japan/kansai/hotels/data/hotels__kansai.json")

PLACEHOLDER_RE = re.compile(r"^(.*?)_h\d{2,4}$")  # group(1) = prefix


try:
    from pypinyin import lazy_pinyin
    HAS_PINYIN = True
except ImportError:
    HAS_PINYIN = False


# 中文音译外来词 → 拉丁原名（按出现频率高到低排）
TRANSLITERATION = {
    # 集团品牌
    "丽思卡尔顿": "ritz_carlton",
    "丽思": "ritz",
    "万豪": "marriott",
    "凯悦": "hyatt",
    "希尔顿": "hilton",
    "洲际": "intercontinental",
    "瑞吉": "st_regis",
    "丽嘉皇家": "rihga_royal",
    "丽嘉": "rihga",
    "皇家花园": "royal_park",
    "皇家公园": "royal_park",
    "蒙特利": "monterey",
    "格兰维亚": "granvia",
    "格兰": "grand",
    "格兰贝尔": "granbell",
    "宜必思": "ibis",
    "诺富特": "novotel",
    "格拉斯丽": "gracery",
    "雅乐轩": "aloft",
    "万怡": "courtyard",
    "莫西": "moxy",
    "万丽": "renaissance",
    "威斯汀": "westin",
    "喜来登": "sheraton",
    "都酒店": "miyako",
    "环球港": "universal_port",
    "环球港口": "universal_port",
    "环球影城": "universal",
    "假日": "holiday_inn",
    "皇冠假日": "crowne_plaza",
    "尊贵": "premio",
    "维斯塔": "vista",
    "维斯塔尊贵": "vista_premio",
    "嘉佩乐": "capella",
    "悦榕庄": "banyan_tree",
    "六善": "six_senses",
    "柏悦": "park_hyatt",
    "凯悦摄政": "hyatt_regency",
    "凯悦嘉轩": "hyatt_place",
    "凯悦凯逸": "caption_by_hyatt",
    "豪华精选": "luxury_collection",
    "傲途格": "autograph",
    "华尔道夫": "waldorf_astoria",
    "康莱德": "conrad",
    "逸林": "doubletree",
    "嘉信": "kanopy",
    "格芮精选": "canopy",
    "森林": "roku",
    "梦想": "dream",
    "智选假日": "holiday_inn_express",
    "贝斯特韦斯特": "best_western",
    "钴蓝": "cobalt",
    "依斯柏席昂": "espacion",
    "莱弗利": "lively",
    "京瓷": "kyocera",
    "门": "gate",
    "格兰德": "grande",
    "京阪": "keihan",
    "近铁": "kintetsu",
    "京急": "keikyu",
    "阪急": "hankyu",
    "阪神": "hanshin",
    "皇家公园": "royal_park",
    "三井花园": "mitsui_garden",
    "三井": "mitsui",
    "千禧": "millennium",
    "甘酸浆": "hoshakuji",
    "御宿野乃": "onyado_nono",
    "拉斯维特": "la_suite",
    "翠岚": "suiran",
    "智积院": "chishakuin",
    "知恩院": "chion_in",
    "仁和寺": "ninnaji",
    "御室": "omuro",
    "妙心寺": "myoshinji",
    "妙顕寺": "myokenji",
    "立本寺": "ryuhonji",
    "鹿王院": "rokuoin",
    "浄蓮華院": "joren_geiin",
    "和顺": "wajun",
    "花传抄": "kadensho",
    "悠洛悦苑": "yuraku_etsuen",
    # 区位词
    "中之岛": "nakanoshima",
    "梅田": "umeda",
    "心斋桥": "shinsaibashi",
    "难波": "namba",
    "道顿堀": "dotonbori",
    "天王寺": "tennoji",
    "本町": "honmachi",
    "堂岛": "dojima",
    "天保山": "tempozan",
    "御堂筋": "midosuji",
    "新地": "shinchi",
    "心斋桥筋": "shinsaibashi_suji",
    "祇园": "gion",
    "東山": "higashiyama",
    "東山三条": "higashiyama_sanjo",
    "高雄": "takao",
    "岚山": "arashiyama",
    "渡月": "togetsu",
    "鹰峰": "takagamine",
    "鞍马": "kurama",
    "贵船": "kibune",
    "宇治": "uji",
    "嵯峨": "saga",
    "嵯峨野": "sagano",
    "二条城": "nijo_castle",
    "二条": "nijo",
    "三条": "sanjo",
    "四条": "shijo",
    "五条": "gojo",
    "六条": "rokujo",
    "七条": "shichijo",
    "八条": "hachijo",
    "九条": "kujo",
    "京都站": "kyoto_station",
    "梅小路": "umekoji",
    "河原町": "kawaramachi",
    "乌丸": "karasuma",
    "西阵": "nishijin",
    "北野": "kitano",
    "御所": "gosho",
    "鞍马口": "kuramaguchi",
    "墨染": "sumizome",
    "深草": "fukakusa",
    # 后缀
    "酒店": "hotel",
    "饭店": "hotel",
    "大饭店": "hotel",
    "大酒店": "hotel",
    "宾馆": "hotel",
    "旅馆": "ryokan",
    "旅馆别馆": "ryokan_bekkan",
    "新馆": "shinkan",
    "本馆": "honkan",
    "别馆": "bekkan",
    "別邸": "bettei",
    "别邸": "bettei",
    "御殿": "goten",
    "山庄": "sanso",
}


def transliterate(text: str) -> str:
    """中文音译外来词 → 拉丁原名。按词典最长匹配优先。"""
    result = []
    i = 0
    keys = sorted(TRANSLITERATION.keys(), key=len, reverse=True)
    while i < len(text):
        matched = False
        for k in keys:
            if text[i:i + len(k)] == k:
                result.append(TRANSLITERATION[k])
                i += len(k)
                matched = True
                break
        if not matched:
            ch = text[i]
            if "一" <= ch <= "鿿":  # 汉字
                if HAS_PINYIN:
                    py = lazy_pinyin(ch)
                    if py:
                        result.append(py[0])
            elif ch.isspace() or ch in "·-/、，。:：;；":
                result.append("_")
            elif ch.isalnum():
                result.append(ch.lower())
            i += 1
    return "_".join(p for p in result if p.strip())


def name_to_slug(name: str) -> str:
    """从店名抽 slug。优先英文/罗马字·fallback 中文转拼音。"""
    if not name:
        return ""

    # 抽括号里所有内容
    parens = re.findall(r"[（\(]([^）\)]+)[）\)]", name)
    candidates = list(parens)
    # 主名（括号外）
    main = re.sub(r"[（\(].*?[）\)]", "", name).strip()
    candidates.append(main)

    # 在候选里挑「英文为主」的（拉丁字符占比高）
    best = None
    best_ratio = 0
    for c in candidates:
        if not c:
            continue
        latin = sum(1 for ch in c if "a" <= ch.lower() <= "z" or ch.isdigit() or ch == " ")
        ratio = latin / max(len(c), 1)
        if ratio > best_ratio and latin >= 4:
            best_ratio = ratio
            best = c

    if best:
        src = best
    else:
        # 没英文 → 用主名（中文）走音译表
        src_clean = main if main else (candidates[0] if candidates else name)
        # 砍掉日文括号内容
        src_clean = re.sub(r"[（\(].*?[）\)]", "", src_clean).strip()
        # 砍掉城市前缀（太通用）
        for prefix in ["京都", "大阪", "神户", "奈良", "有马", "城崎", "高野山", "白浜"]:
            if src_clean.startswith(prefix) and len(src_clean) > len(prefix) + 2:
                src_clean = src_clean[len(prefix):]
                break
        src = transliterate(src_clean)

    # 砍 / 之后的副名
    src = src.split("/")[0].strip()
    # 砍逗号之后
    src = src.split(",")[0].strip()

    # 转 slug
    slug = src.lower()
    slug = re.sub(r"[\s\-]+", "_", slug)
    slug = re.sub(r"[^a-z0-9_]", "", slug)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug


def main() -> None:
    apply = "--apply" in sys.argv
    data = json.loads(DATA.read_text(encoding="utf-8"))
    existing = {h["id"] for h in data}

    changes = []
    new_ids_seen = set()

    for h in data:
        old = h["id"]
        m = PLACEHOLDER_RE.match(old)
        if not m:
            continue
        prefix = m.group(1)
        name = h.get("note", {}).get("店名", "")
        slug = name_to_slug(name)
        if not slug:
            changes.append((old, "FAIL_EMPTY_SLUG", name[:40]))
            continue

        new = f"{prefix}_{slug}"
        # 防重复：跟现有 id（除自己外）+ 已分配的新 id
        candidate = new
        n = 2
        while candidate in (existing - {old}) or candidate in new_ids_seen:
            candidate = f"{new}_{n}"
            n += 1
        new_ids_seen.add(candidate)
        changes.append((old, candidate, name[:40]))
        if apply and candidate != old:
            h["id"] = candidate

    print(f"total candidates: {len(changes)}")
    fail = [c for c in changes if c[1] == "FAIL_EMPTY_SLUG"]
    print(f"failures (empty slug): {len(fail)}")
    print()
    print("Sample (first 30):")
    for old, new, name in changes[:30]:
        print(f"  {old:55} → {new:55} | {name}")
    if len(changes) > 30:
        print(f"  ... +{len(changes) - 30} more")

    if fail:
        print("\n---- failures ----")
        for old, _, name in fail[:20]:
            print(f"  {old:55} | name=「{name}」")

    if apply:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[APPLIED] written to {DATA}")
    else:
        print("\n[DRY-RUN]")


if __name__ == "__main__":
    main()
