# Content Assembly · 真实范例

> 路径、字段、命令均取自仓库真实文件（2026-07-09 核）。模板字段以 `scripts/validate_template.py` 为准。

## 层职责速查（改动前先对号入座）

| 层 | 真实路径 | 管什么 |
|---|---|---|
| plan | `japan/kansai/plans/` | 跨天城市顺序、住宿模式、表单契约、路线取舍 |
| catalog | `japan/kansai/plans/catalog/` | 候选池、季节池、半日池（如 `pool_selectable.json`, `seasons.json`） |
| 模板 | `japan/kansai/templates/{city}/{area}/N.json` | 一天/半天的执行时间线 |
| 动线说明 | `japan/kansai/templates/{city}/{area}/动线说明.md` | 何时用/何时不用/为什么存在（≤80-120 行 5 段） |
| 事实层 | `entities/ restaurants/ hotels/ stops/` | 复用事实数据（切到 `travel-ai-data-collection`） |
| resources | 路线目录 `resources.json` | 该路线的本地资源联动 |
| transport | `transport.json` | 机读移动信息 + 展示文案 |

**渲染逻辑/页面样式/图片路径/CSS 不进 plan 或 template JSON**（切到 `handbook-system-rendering`）。

## 模板真实字段（照抄 validator·`scripts/validate_template.py`）

- 顶层必填：`template_id, applicable_dates, note, slots`
- 顶层可选：`variant_label, contingencies`（`contingencies` key ∈ `{rain_light, rain_heavy, crowd, indoor_backup, late_start}`）
- 半日专用（按需）：`default_duration_option, duration_options, copy_variants, nearby_food`
- `slots` 段有 `time_window ∈ {morning, afternoon, evening, night}`；每段 `main` 桶至少 1 项
- 真开放时间用 `free_time`，别留空 slot；`meal` 用 `meal_type`/`meal_area` 不锁定餐厅；`hotel` 不指向固定 hotel entity

## 范例 1：一个真实的路线目录长什么样（`templates/kyoto/arashiyama/`）

```text
japan/kansai/templates/kyoto/arashiyama/
  动线说明.md        ← 何时用岚山线 / 何时不用 / 为什么（散文，不是字段）
  N.json             ← 当天执行时间线（模板字段见上）
```

`动线说明.md` 是唯一存在的一批真实动线文件（京都 10 条、大阪 6 条、other 7 条，见 `find japan/kansai -name 动线说明.md`）。⚠️ **不存在 `templates/koyo_9d/` 目录**——红叶 9 日书是打样本，handoff 在 `_tmp/handoff/CURRENT_1_koyo9d_book.md`，不要引用不存在的模板路径。

## 范例 2：最小层正确改动的判断链

需求「岚山这天下午想加个备选雨天点」：

1. 定位对象 → 岚山当天 `templates/kyoto/arashiyama/N.json`（模板层，不是 plan 层）。
2. 先看动线结论 → 读同目录 `动线说明.md` 确认岚山线适用条件，再看该路线 research 有没有雨天替代结论。
3. 最小改动 → 在对应 slot 段加 `contingencies.rain_light` 备份项，**不新增字段**（rain_light 已在白名单）。
4. 若需要全新字段/枚举 → 先改 `docs/项目核心/字段权威.md`，再改模板（禁止反向）。
5. 若改动引出渲染需求 → 用文字描述给渲染线，不把样式编码进模板 JSON。

## 范例 3：改完怎么验证（真实命令）

```powershell
.\.venv\Scripts\python.exe scripts\validate_template.py japan\kansai\templates
.\.venv\Scripts\python.exe -m pytest app\tests\test_plan_contract.py -q
```

只改了数据池文件时，另跑对应 validator（切到 `travel-ai-data-collection`）。把 `合计/PASS/FAIL` 完整输出贴进汇报——不口头声称跑过。commit 时 `pre-commit` hook 会再跑一遍数据池 validator 兜底。
