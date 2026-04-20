"""
扫描所有 kansai days/*.json，找并修复裸双引号（JSON 字符串内部未转义的 "）
策略：把文本内容里的中文引号 " " 统一替换为「」，避免破坏 JSON 结构
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONTENT = ROOT / "content" / "kansai"

# 中文直引号（\u201c \u201d）→ 日文引号（\u300c \u300d）
# 但 okazaki 的问题是 ASCII 双引号 0x22 出现在 JSON 字符串内
# 需要手动处理：在 JSON string 值内部的裸 " 改成 「」

def fix_file(fp: Path) -> bool:
    """返回 True 表示有修改"""
    content = fp.read_text(encoding="utf-8")

    # 替换中文引号
    fixed = content.replace("\u201c", "\u300c").replace("\u201d", "\u300d")

    if fixed != content:
        fp.write_text(fixed, encoding="utf-8")
        print(f"Fixed curly quotes: {fp.name}")
        return True
    return False


def check_and_report(fp: Path):
    import json
    content = fp.read_text(encoding="utf-8")
    try:
        json.loads(content)
    except json.JSONDecodeError as e:
        lines = content.split("\n")
        bad_line = lines[e.lineno - 1]
        snippet = bad_line[max(0, e.colno - 40): e.colno + 20]
        print(f"STILL BROKEN: {fp.name} line {e.lineno} col {e.colno}")
        # Find ascii double quotes in the bad line (not at start/end of structural positions)
        for idx, ch in enumerate(bad_line):
            if ch == '"' and idx > 0:
                ctx = bad_line[max(0, idx-15): idx+15]
                print(f"  Quote at col {idx}: ...{ctx}...")


if __name__ == "__main__":
    import json

    all_files = [f for f in CONTENT.rglob("days/*.json") if not f.name.startswith("_")]

    print("=== Step 1: Fix curly quotes ===")
    for f in all_files:
        fix_file(f)

    print("\n=== Step 2: Validate all JSON ===")
    errors = []
    for f in all_files:
        try:
            json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f)

    if not errors:
        print("All JSON valid!")
    else:
        print(f"{len(errors)} files still broken:")
        for f in errors:
            check_and_report(f)
