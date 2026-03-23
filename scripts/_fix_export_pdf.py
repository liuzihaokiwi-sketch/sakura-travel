import pathlib
p = pathlib.Path("scripts/export_plan_pdf.py")
lines = p.read_text("utf-8").splitlines(True)
# lines[26] = '# ── 显示名映射...'  (0-indexed = line 27)
# lines[92] = '    return text\n'    (0-indexed = line 93)
repl = """\
# -- display_registry import (single source of truth) --
from app.domains.planning.display_registry import (
    CORRIDOR_ZH as _CORRIDOR_ZH,
    CITY_ZH as _CITY_ZH,
    AREA_ZH as _AREA_ZH,
    CUISINE_ZH as _CUISINE_ZH,
    DAY_TYPE_ZH as _DAY_TYPE_ZH,
    INTENSITY_ZH as _INTENSITY_ZH,
    MEAL_ZH as _MEAL_ZH,
    sanitize as _sanitize_text,
    display_corridor as _corridor_zh,
    display_city as _city_zh,
    display_area as _area_zh,
)

"""
new = lines[:26] + [repl] + lines[93:]
p.write_text("".join(new), "utf-8")
print(f"OK: {len(lines)} -> {len(new)} lines")
