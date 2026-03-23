"""Replace local display mappings in run_regression.py with display_registry import."""
import pathlib

p = pathlib.Path("scripts/run_regression.py")
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)

# Find start (line containing "显示名映射") and end (line starting with "def _area_zh")
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if "显示名映射" in line and start_idx is None:
        start_idx = i
    if line.startswith("def _area_zh") and start_idx is not None:
        end_idx = i
        break

if start_idx is None or end_idx is None:
    print(f"ERROR: start={start_idx} end={end_idx}")
    raise SystemExit(1)

print(f"Replacing lines {start_idx+1} to {end_idx+1}")

replacement = """\
# -- display_registry import (single source of truth) --

from app.domains.planning.display_registry import (
    CORRIDOR_ZH as _CZH,
    CITY_ZH as _CITY_ZH,
    AREA_ZH as _AREA_ZH,
    CUISINE_ZH as _CUISINE_ZH,
    DAY_TYPE_ZH as _DAY_TYPE_ZH,
    INTENSITY_ZH as _INTENSITY_ZH,
    MEAL_ZH as _MEAL_ZH,
    RAW_KEY_BLACKLIST,
    sanitize as _san,
    display_corridor as _corr_zh,
    display_city as _city_zh,
    display_area as _area_zh,
)

"""

new_lines = lines[:start_idx] + [replacement] + lines[end_idx+1:]
p.write_text("".join(new_lines), encoding="utf-8")
print(f"OK: removed {end_idx - start_idx + 1} lines, inserted import block")
