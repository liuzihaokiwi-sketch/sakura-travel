"""模板时间装配引擎（D39·2026-04-24）。

输入：模板 JSON + 用户出门档（8/9/10 点）
输出：每个 slot 的实际时间

设计：
- 模板时间用相对偏移：start+0h00-+1h00 / lunch+0h00-+1h30 / dinner+0h00-+2h00
- 三个锚点各自按档位平移（午餐晚餐是生理约束，不跟早出门整体前移）：

  | 档位 | start | lunch | dinner |
  |------|-------|-------|--------|
  | 8 点 | 08:00 | 12:00 | 18:00 |
  | 9 点 | 09:00 | 12:30 | 18:30 |
  | 10点 | 10:00 | 13:00 | 19:00 |

- 时间约束（小火车/预订/日出等）：装配层允许用户出门 ±20 分钟微调 start 锚点，
  lunch/dinner 锚点不动（吃饭时间只按档位走，不跟约束走）。
  超过 20 分钟 → 判定不兼容，换模板。

- fixed_early：独立模板，slots 直接写绝对时间，不走本引擎平移。
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


PACE_ANCHORS = {
    "08:00": {"start": "08:00", "lunch": "12:00", "dinner": "18:00"},
    "09:00": {"start": "09:00", "lunch": "12:30", "dinner": "18:30"},
    "10:00": {"start": "10:00", "lunch": "13:00", "dinner": "19:00"},
}

# 有时间约束的模板允许 start 锚点 ±20 分钟微调，lunch/dinner 不动
ELASTIC_WINDOW_MIN = 20


def parse_offset(expr: str) -> int:
    """解析 "+1h30" / "-0h20" → 分钟数（带符号）。"""
    m = re.fullmatch(r"([+-])(\d+)h(\d+)", expr.strip())
    if not m:
        raise ValueError(f"非法偏移表达式: {expr}")
    sign = 1 if m.group(1) == "+" else -1
    return sign * (int(m.group(2)) * 60 + int(m.group(3)))


def hm_to_min(hm: str) -> int:
    h, m = hm.split(":")
    return int(h) * 60 + int(m)


def min_to_hm(total: int) -> str:
    total = total % (24 * 60)
    return f"{total // 60:02d}:{total % 60:02d}"


BASE_ANCHORS = PACE_ANCHORS["09:00"]  # 9 点档作为模板书写基准


def nearest_anchor(abs_min: int) -> str:
    """绝对时刻就近归到 start/lunch/dinner 锚点。"""
    return min(
        BASE_ANCHORS,
        key=lambda k: abs(abs_min - hm_to_min(BASE_ANCHORS[k])),
    )


def resolve_time(expr: str, anchors: dict[str, str]) -> tuple[str, str]:
    """模板 slot time → (start, end) 实际绝对时间。

    支持两种写法（推荐绝对时间，AI 写作更自然）：
      - "09:00-10:00"           绝对时间（9 点档基准），引擎就近归锚点自动平移 ✅ 推荐
      - "start+0h00-+1h00"      显式相对锚点（留给极特殊情况）
    """
    expr = expr.strip()

    # 绝对时间（9 点档基准）：按就近锚点自动平移
    m = re.fullmatch(r"(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})", expr)
    if m:
        orig_start = int(m.group(1)) * 60 + int(m.group(2))
        orig_end = int(m.group(3)) * 60 + int(m.group(4))
        key = nearest_anchor(orig_start)
        base_min = hm_to_min(BASE_ANCHORS[key])
        off_s = orig_start - base_min
        off_e = orig_end - base_min
        target = hm_to_min(anchors[key])
        return min_to_hm(target + off_s), min_to_hm(target + off_e)

    # 显式相对锚点（不推荐常用）
    m = re.fullmatch(r"(start|lunch|dinner)([+-]\d+h\d+)-([+-]\d+h\d+)", expr)
    if m:
        anchor_key = m.group(1)
        off_start = parse_offset(m.group(2))
        off_end = parse_offset(m.group(3))
        base = hm_to_min(anchors[anchor_key])
        return min_to_hm(base + off_start), min_to_hm(base + off_end)

    raise ValueError(f"无法解析: {expr}（需 'HH:MM-HH:MM' 或 'start/lunch/dinner+偏移-偏移'）")


def check_compatibility(template: dict, user_pace: str) -> tuple[bool, str]:
    """检查模板和用户档是否兼容。

    返回 (是否兼容, 提示信息)。

    - flexible / soft：总是兼容
    - hard：需要装配层根据约束时刻独立判断（目前仅返回提醒，实际判断靠装配层读 time_sensitivity_note）
    """
    sens = template.get("time_sensitivity", "flexible")
    if sens == "flexible":
        return True, ""
    if sens == "soft":
        note = template.get("time_sensitivity_note", "")
        return True, f"⚠️ soft 模板：{note}（装配层可用 ±20 分钟微调 start）"
    if sens == "hard":
        note = template.get("time_sensitivity_note", "")
        return True, f"🔴 hard 模板：{note}（装配层必须按约束时刻判用户档兼容性）"
    return True, ""


def assemble(template: dict, user_pace: str, start_shift_min: int = 0) -> list[dict]:
    """模板 + 用户档 → slot 实际时间。

    start_shift_min: start 锚点微调（±20 分钟内），仅 soft / hard 模板可用。
                     lunch/dinner 锚点始终不动。
    """
    if user_pace not in PACE_ANCHORS:
        raise ValueError(f"非法 pace: {user_pace}（需 08:00/09:00/10:00）")
    if abs(start_shift_min) > ELASTIC_WINDOW_MIN:
        raise ValueError(
            f"start 微调 {start_shift_min} 分钟超过 ±{ELASTIC_WINDOW_MIN}，"
            f"应判定模板不兼容换模板"
        )
    if start_shift_min != 0:
        sens = template.get("time_sensitivity", "flexible")
        if sens == "flexible":
            raise ValueError(
                f"flexible 模板不允许 start 微调（当前 shift={start_shift_min}）。"
                f"仅 soft / hard 模板可用 ±20 分钟弹性"
            )

    base = PACE_ANCHORS[user_pace]
    anchors = {
        "start": min_to_hm(hm_to_min(base["start"]) + start_shift_min),
        "lunch": base["lunch"],
        "dinner": base["dinner"],
    }

    result = []
    for slot in template.get("slots", []):
        expr = slot.get("time", "")
        try:
            start, end = resolve_time(expr, anchors)
        except Exception as e:
            result.append({"time_expr": expr, "error": str(e)})
            continue
        entry = {
            "time_expr": expr,
            "time": f"{start}-{end}",
            "main": slot.get("main", []),
        }
        if slot.get("optional"):
            entry["optional"] = slot["optional"]
        result.append(entry)
    return result


def main() -> None:
    if len(sys.argv) < 3:
        print("用法: python assemble_schedule.py <template.json> <user_pace> [start_shift_min]")
        print("  user_pace: 08:00 / 09:00 / 10:00")
        print("  start_shift_min: 可选，±20 范围内，用于时间约束模板（默认 0）")
        sys.exit(1)

    tpl_path = Path(sys.argv[1])
    user_pace = sys.argv[2]
    shift = int(sys.argv[3]) if len(sys.argv) > 3 else 0

    template = json.loads(tpl_path.read_text(encoding="utf-8"))
    _, compat_msg = check_compatibility(template, user_pace)
    result = assemble(template, user_pace, shift)

    print(f"模板: {template.get('template_id')}")
    print(f"时间敏感度: {template.get('time_sensitivity', 'flexible')}")
    if compat_msg:
        print(compat_msg)
    print(f"出门档: {user_pace}  start 微调: {shift:+d} 分钟")
    base = PACE_ANCHORS[user_pace]
    actual_start = min_to_hm(hm_to_min(base["start"]) + shift)
    print(f"锚点: start={actual_start}  lunch={base['lunch']}（不受 shift 影响）  dinner={base['dinner']}（不受 shift 影响）")
    print("---")
    for slot in result:
        expr = slot.get("time_expr", "")
        if "error" in slot:
            print(f"  ❌ {expr}: {slot['error']}")
        else:
            print(f"  {slot['time']}  ← {expr}")


if __name__ == "__main__":
    main()
