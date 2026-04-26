"""酒店池字段校验脚本（D46 重写）。

用法：
    python scripts/validate_hotels.py japan/kansai/hotels/
    python scripts/validate_hotels.py japan/kansai/hotels/data/hotels__kansai.json

校验规则参考：
    docs/项目核心/字段权威.md §2.4 hotels
    docs/操作SOP/上线前/数据池构建/酒店规范.md

设计原则：
- 字段白名单（9 系统 + 9 note + 3 元数据）= 防膨胀（铁律 1）
- 枚举严校验（tier 4 英文档 / type 2 类 / experience 6 组软约束）
- 体验型 6 组写在 note.亮点 第一项·validator FAIL 强约束
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent

# ============================================================
# 系统字段（9 个）
# ============================================================
SYS_REQUIRED = {
    "id", "city", "area", "near_attractions",
    "tier", "type", "price_cny_per_night",
}
SYS_OPTIONAL = {"season_months", "depth"}
SYS_ALLOWED = SYS_REQUIRED | SYS_OPTIONAL

# 元数据（3 个·全必填）
META_REQUIRED = {"可信度", "数据来源", "最后核实"}

# 顶层允许字段 = 系统字段 + note + 元数据
TOP_ALLOWED = SYS_ALLOWED | META_REQUIRED | {"note"}

# ============================================================
# note 字段（9 个）
# ============================================================
NOTE_REQUIRED = {"店名"}  # 总是必填
NOTE_FULL_REQUIRED = {"店名", "简介", "亮点", "地址", "房型", "价格", "预约"}  # full 时必填
NOTE_OPTIONAL = {"含早", "到店提醒"}
NOTE_ALLOWED = NOTE_FULL_REQUIRED | NOTE_OPTIONAL

# ============================================================
# 枚举（D47·6 档·按城市分档）
# ============================================================
TIER_ENUM = {"b1", "b2", "b3", "b4", "b5", "b6"}
TYPE_ENUM = {"city", "experience"}
DEPTH_ENUM = {"skeleton", "verified", "full"}
TRUST_ENUM = {"verified", "cross_checked", "single_source", "ai_generated"}

# 体验型 6 组（软字段·写在 note.亮点 第一项）
EXPERIENCE_GROUPS = {
    "温泉旅馆", "老铺旅馆", "宿坊", "町家", "温泉度假", "设计精品",
}

# 对外名（生成报错信息时用）
TIER_NAMES = {
    "b1": "经济", "b2": "舒适", "b3": "品质",
    "b4": "高端", "b5": "奢华", "b6": "顶奢",
}

# tier × city × price 一致性（平季中位区间·D47）
# 京都阈值（trip.com 京都 9 档压缩成 6）
TIER_PRICE_KYOTO = {
    "b1": (0, 500),
    "b2": (500, 950),
    "b3": (950, 1200),
    "b4": (1200, 2000),
    "b5": (2000, 3500),
    "b6": (3500, 99999),
}
# 关西其他城市阈值（trip.com 关西 6 档 1:1）
TIER_PRICE_OTHER = {
    "b1": (0, 400),
    "b2": (400, 600),
    "b3": (600, 850),
    "b4": (850, 1250),
    "b5": (1250, 2050),
    "b6": (2050, 99999),
}

URL_RE = re.compile(r"^https?://", re.I)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_item(it: dict, idx: int, file: Path,
                  area_registry: set[str] | None,
                  entity_ids: set[str] | None) -> list[str]:
    errors: list[str] = []

    if not isinstance(it, dict):
        errors.append(f"{file.name}#{idx} 不是 dict")
        return errors

    hid = it.get("id", f"<no-id#{idx}>")

    # --- 顶层字段白名单 ---
    unknown = set(it.keys()) - TOP_ALLOWED
    if unknown:
        errors.append(f"{file.name}::{hid} 含未知字段（防膨胀）: {sorted(unknown)}")

    # --- 系统必填 ---
    missing = SYS_REQUIRED - set(it.keys())
    if missing:
        errors.append(f"{file.name}::{hid} 缺系统必填: {sorted(missing)}")

    # --- 元数据必填 ---
    meta_missing = META_REQUIRED - set(it.keys())
    if meta_missing:
        errors.append(f"{file.name}::{hid} 缺元数据必填: {sorted(meta_missing)}")

    # --- area ---
    if area_registry is not None and "area" in it and it["area"] not in area_registry:
        errors.append(f"{file.name}::{hid} area='{it['area']}' 不在 area_registry")

    # --- near_attractions ---
    if "near_attractions" in it:
        na = it["near_attractions"]
        if not isinstance(na, list) or len(na) == 0:
            errors.append(f"{file.name}::{hid} near_attractions 必须 ≥1 个对象")
        else:
            for j, item in enumerate(na):
                if not isinstance(item, dict) or "entity_id" not in item or "walk_min" not in item:
                    errors.append(f"{file.name}::{hid} near_attractions[{j}] 缺 entity_id/walk_min")
                    continue
                if entity_ids is not None and item["entity_id"] not in entity_ids:
                    errors.append(f"{file.name}::{hid} near_attractions[{j}].entity_id='{item['entity_id']}' 不在 entities/")
                if not isinstance(item["walk_min"], (int, float)):
                    errors.append(f"{file.name}::{hid} near_attractions[{j}].walk_min 非数字")

    # --- tier ---
    tier = it.get("tier")
    if tier and tier not in TIER_ENUM:
        errors.append(f"{file.name}::{hid} tier='{tier}' 不在枚举: {sorted(TIER_ENUM)}")

    # --- type ---
    htype = it.get("type")
    if htype and htype not in TYPE_ENUM:
        errors.append(f"{file.name}::{hid} type='{htype}' 不在枚举: {sorted(TYPE_ENUM)}")

    # --- price_cny_per_night ---
    if "price_cny_per_night" in it:
        pr = it["price_cny_per_night"]
        if not isinstance(pr, list) or len(pr) != 2:
            errors.append(f"{file.name}::{hid} price_cny_per_night 必须 [平季中位, 旺季中位] 长度 2")
        else:
            lo, hi = pr
            if not (isinstance(lo, (int, float)) and isinstance(hi, (int, float))):
                errors.append(f"{file.name}::{hid} price_cny_per_night 元素非数字")
            elif lo == hi:
                errors.append(f"{file.name}::{hid} price_cny_per_night min=max（必须给区间）")
            elif lo > hi:
                errors.append(f"{file.name}::{hid} price_cny_per_night min > max")
            elif tier and tier in TIER_ENUM:
                # 警告·非 FAIL：tier × city × 平季中位区间一致性（D47）
                city = it.get("city", "")
                table = TIER_PRICE_KYOTO if city == "京都" else TIER_PRICE_OTHER
                t_lo, t_hi = table[tier]
                if lo < t_lo * 0.7 or lo > t_hi * 1.3:
                    name = TIER_NAMES.get(tier, tier)
                    errors.append(f"{file.name}::{hid} ⚠ tier='{tier}'({name}) city={city} 但平季中位 {lo} 偏离区间 [{t_lo}, {t_hi}]")

    # --- season_months ---
    if "season_months" in it and it["season_months"] is not None:
        sm = it["season_months"]
        if not isinstance(sm, list) or any(not (isinstance(m, int) and 1 <= m <= 12) for m in sm):
            errors.append(f"{file.name}::{hid} season_months 必须 null 或 1-12 整数数组")

    # --- depth ---
    depth = it.get("depth", "skeleton")
    if depth not in DEPTH_ENUM:
        errors.append(f"{file.name}::{hid} depth='{depth}' 不在枚举")

    # --- note ---
    note = it.get("note")
    if note is None:
        errors.append(f"{file.name}::{hid} 缺 note 块")
    elif not isinstance(note, dict):
        errors.append(f"{file.name}::{hid} note 非 dict")
    else:
        # note 字段白名单
        n_unknown = set(note.keys()) - NOTE_ALLOWED
        if n_unknown:
            errors.append(f"{file.name}::{hid} note 含未知字段: {sorted(n_unknown)}")

        # 店名总是必填
        if "店名" not in note or not note["店名"]:
            errors.append(f"{file.name}::{hid} note.店名 必填")

        # full depth 时·full 必填字段必须齐
        if depth == "full":
            n_missing = NOTE_FULL_REQUIRED - set(note.keys())
            if n_missing:
                errors.append(f"{file.name}::{hid} depth=full 但 note 缺必填: {sorted(n_missing)}（建议降 verified/skeleton）")

        # 体验型 6 组软约束（FAIL）
        if htype == "experience":
            highlights = note.get("亮点")
            if not isinstance(highlights, list) or len(highlights) == 0:
                errors.append(f"{file.name}::{hid} type=experience 但 note.亮点 为空")
            else:
                first = highlights[0]
                if first not in EXPERIENCE_GROUPS:
                    errors.append(f"{file.name}::{hid} type=experience 但 note.亮点[0]='{first}' 不在 6 组（{sorted(EXPERIENCE_GROUPS)}）")

    # --- 元数据值校验 ---
    trust = it.get("可信度")
    if trust:
        if trust not in TRUST_ENUM:
            errors.append(f"{file.name}::{hid} 可信度='{trust}' 不在枚举")
        elif trust == "ai_generated":
            errors.append(f"{file.name}::{hid} 可信度=ai_generated 禁止上生产")

    sources = it.get("数据来源")
    if sources is not None:
        if not isinstance(sources, list) or len(sources) == 0:
            errors.append(f"{file.name}::{hid} 数据来源 必须 ≥1 URL")
        else:
            bad_urls = [s for s in sources if not isinstance(s, str) or not URL_RE.match(s)]
            if bad_urls:
                errors.append(f"{file.name}::{hid} 数据来源 含非 URL: {bad_urls}")

    last = it.get("最后核实")
    if last is not None and (not isinstance(last, str) or not DATE_RE.match(last)):
        errors.append(f"{file.name}::{hid} 最后核实 必须 YYYY-MM-DD: '{last}'")

    return errors


def load_area_registry(circle_root: Path) -> set[str] | None:
    p = circle_root / "area_registry.json"
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            # list[dict{"area": ..., ...}] 或 list[str]
            result = set()
            for it in data:
                if isinstance(it, str):
                    result.add(it)
                elif isinstance(it, dict) and "area" in it:
                    result.add(it["area"])
            return result if result else None
        if isinstance(data, dict):
            keys = set()
            for k, v in data.items():
                if isinstance(v, list):
                    keys.update(v)
                else:
                    keys.add(k)
            return keys
    except Exception:
        return None
    return None


def load_entity_ids(circle_root: Path) -> set[str] | None:
    ent_dir = circle_root / "entities"
    if not ent_dir.is_dir():
        return None
    ids: set[str] = set()
    for f in ent_dir.rglob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for it in data:
                    if isinstance(it, dict):
                        eid = it.get("entity_id") or it.get("id")
                        if eid:
                            ids.add(eid)
        except Exception:
            continue
    return ids if ids else None


def find_circle_root(file: Path) -> Path | None:
    """从 hotels json 路径反推圈根目录（含 area_registry.json 的目录）。"""
    cur = file.parent
    while cur != cur.parent:
        if (cur / "area_registry.json").exists():
            return cur
        cur = cur.parent
    return None


def validate_file(file: Path) -> tuple[int, int, list[str]]:
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except Exception as e:
        return 0, 1, [f"{file.name} JSON 解析失败: {e}"]

    if not isinstance(data, list):
        return 0, 1, [f"{file.name} 顶层非 list（酒店池约定 list of dict）"]

    circle_root = find_circle_root(file)
    area_registry = load_area_registry(circle_root) if circle_root else None
    entity_ids = load_entity_ids(circle_root) if circle_root else None

    errors: list[str] = []
    seen_ids: set[str] = set()

    for i, it in enumerate(data):
        errors.extend(validate_item(it, i, file, area_registry, entity_ids))
        if isinstance(it, dict) and "id" in it:
            if it["id"] in seen_ids:
                errors.append(f"{file.name}::{it['id']} 重复 ID")
            seen_ids.add(it["id"])

    return len(data), len(errors), errors


def collect_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix == ".json" else []
    if target.is_dir():
        return sorted(target.rglob("hotels__*.json"))
    return []


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("用法: python scripts/validate_hotels.py <file_or_dir>")
        return 2

    target = Path(argv[1]).resolve()
    files = collect_files(target)
    if not files:
        print(f"未找到酒店 JSON 文件: {target}")
        return 2

    total = 0
    total_errors = 0
    all_msgs: list[str] = []
    file_results = []

    for f in files:
        cnt, errs, msgs = validate_file(f)
        total += cnt
        total_errors += errs
        all_msgs.extend(msgs)
        file_results.append((str(f.relative_to(REPO_ROOT)), cnt, errs))

    print("=" * 60)
    print("酒店池校验结果（D46 SOP）")
    print("=" * 60)
    for path, cnt, errs in file_results:
        status = "PASS" if errs == 0 else "FAIL"
        print(f"  [{status}] {path}  ({cnt} hotels, {errs} errors)")
    print("-" * 60)
    print(f"合计: {total} hotels, {total_errors} errors")

    if all_msgs:
        print()
        print("详细错误（前 200 条）:")
        for m in all_msgs[:200]:
            print(f"  - {m}")
        if len(all_msgs) > 200:
            print(f"  ... 还有 {len(all_msgs) - 200} 条未显示")

    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
