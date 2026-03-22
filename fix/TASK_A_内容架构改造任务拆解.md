# A. 内容架构与生成链路改造 — 任务拆解（v3 城市圈版）

> 创建时间：2026-03-22（v2 修订）
> 核心原则：**能改一行解决的不新建文件，能复用现有逻辑的不重写，但效果优先**

---

## 现有代码复用评估

| 现有代码 | 复用程度 | 说明 |
|---------|---------|------|
| `report_generator._collect_plan_data()` | ✅ 100% 复用 | 只需在返回值上扩充几个字段 |
| `report_generator._build_system_prompt()` | ✅ 100% 复用 | 角色预热逻辑完整 |
| `report_generator._ai_call_with_retry()` | ✅ 100% 复用 | 重试+质检机制完整 |
| `report_generator._try_reuse_fragments()` | ✅ 100% 复用 | 片段复用保持不动 |
| `report_generator.STATIC_PREP` | ✅ 100% 复用 | 静态准备事项 |
| `report_generator._clean_json()` | ✅ 100% 复用 | JSON 清洗 |
| `assembler.py` 全部 | ✅ 100% 不动 | 装配逻辑是上游，本次不改 |
| `renderer.py` | ⚠️ 90% 复用 | 加 v2 分支即可（~30行） |
| `generate_trip.py` | ⚠️ 95% 复用 | 调用入口小改（~10行） |
| `quality_gate.py` | ⚠️ 80% 复用 | 追加 5 个 STR grader |
| `report_generator._P_OVERVIEW` | 🔄 重写 prompt | 从自由发挥改成约束下解释 |
| `report_generator._P_DAILY` | 🔄 重写 prompt | 注入 8 个结构字段作为约束 |
| `report_generator._trigger_conditional()` | 🔄 替换 | 从 12 行硬编码改成规则引擎 |
| `report_generator.generate_report()` | 🔄 改造核心 | 在 AI 前插入骨架计算+结构检查 |

---

## 实际要做的事（按执行顺序）

### T1 — 新建 `report_schema.py`（类型定义）
**级别：低级 AI 可做**
**文件：新建 `app/domains/planning/report_schema.py`**
**工作量：~150 行 Pydantic 模型**

纯类型定义，无逻辑。把设计文档 §5-§7 的 TypeScript interface 翻译为 Pydantic BaseModel。

核心类：`ReportPayloadV2`, `DaySection`, `DaySlot`, `DesignBrief`, `OverviewSection`, `ConditionalSection`, `BookingAlertItem`, `ProfileSummary`, `HighlightCard`, `ExecutionNotes`, `PlanBOption`, `QualityFlags`

---

### T2 — 在 `_collect_plan_data()` 返回值中扩充结构字段
**级别：高级 AI**
**文件：修改 `app/domains/planning/report_generator.py`**
**工作量：~80 行新增逻辑**

在现有 `_collect_plan_data()` 返回的 `days_list` 中，**每天额外计算 8 个字段**：

```python
# 在现有 item_dicts 构建完成后，追加：
day_dict["primary_area"] = _calc_primary_area(item_dicts)      # 出现最多的 area
day_dict["secondary_area"] = _calc_secondary_area(item_dicts)  # 第二高频 area
day_dict["day_goal"] = _calc_day_goal(day_theme, primary_area) # theme + area 拼装
day_dict["must_keep"] = _calc_must_keep(item_dicts)            # data_tier=S 或 rating≥4.3 最高分
day_dict["first_cut"] = _calc_first_cut(item_dicts)            # is_optional 或 data_tier=B 最低分
day_dict["start_anchor"] = item_dicts[0]["name"] if item_dicts else ""
day_dict["end_anchor"] = item_dicts[-1]["name"] if item_dicts else ""
day_dict["route_integrity_score"] = _calc_integrity(item_dicts)  # 区域跳跃扣分
```

**这些都是 pure Python 规则计算，不走 AI，不查额外表。**

需要在 `_collect_plan_data()` 中对 items 多查几个字段（`data_tier`, `google_rating`, `is_optional`）——现有代码已经在 entity 上取了 `google_rating`，只需补 `data_tier`。

---

### T3 — 重写 AI prompt：`_P_OVERVIEW` 和 `_P_DAILY`
**级别：高级 AI**
**文件：修改 `app/domains/planning/report_generator.py`**
**工作量：~60 行 prompt 重写**

**核心变化：把 8 个结构字段注入 prompt，AI 只负责解释。**

现有 `_P_DAILY` 让 AI 自由发挥 `execution_overview.area` / `intensity`，改成：

```
以下信息已经确定，不要修改：
- 主区域：{primary_area}
- 副区域：{secondary_area}
- 今天主线：{day_goal}
- 最不能砍：{must_keep}
- 晚了先砍：{first_cut}
- 起点：{start_anchor}，终点：{end_anchor}

你只需要写：
1. 为什么这样排（3-5 个判断）
2. 亮点体验描述（每个 2-3 句话）
3. 风险/雨天/体力备选
```

现有 `_P_OVERVIEW` 类似改造：注入 `design_brief`（从 profile + route 特征规则推导），AI 只润色。

---

### T4 — 替换 `_trigger_conditional()`
**级别：高级 AI**
**文件：修改 `app/domains/planning/report_generator.py`（或新建 `condition_triggers.py`）**
**工作量：~60 行**

现有 12 行太简陋，替换为基于规则的触发器。可以直接在 `report_generator.py` 内改（函数不大），不一定要新建文件。

```python
def _trigger_conditional(day_num: int, total: int, items: list[dict], day_context: dict) -> list[str]:
    pages = []
    # 交通页：第一/最后天、跨城
    if day_num == 1 or day_num == total:
        pages.append("transport")
    # 酒店页：第一天、换区
    if day_num == 1 or day_context.get("hotel_changed"):
        pages.append("hotel")
    # 餐厅页：有高评分/高价餐厅
    for it in items:
        if it.get("entity_type") == "restaurant":
            r = it.get("google_rating")
            if r and float(r) >= 4.0:
                pages.append("restaurant")
                break
    # 出片页：trigger_tags 含视觉关键词
    visual_tags = {"sakura", "night_view", "sea", "mountain", "sunset"}
    if set(day_context.get("trigger_tags", [])) & visual_tags:
        pages.append("photo")
    return list(set(pages))  # 去重
```

---

### T5 — 改造 `generate_report()` 主函数：插入骨架→检查→AI 解释→v2 组装
**级别：高级 AI**
**文件：修改 `app/domains/planning/report_generator.py`**
**工作量：~100 行改造（核心函数约 140 行，改动 ~70%）**
**依赖：T2, T3, T4**

这是最关键的改动。现有 `generate_report()` 的流程：

```
collect → fragment_reuse → overview_prompt → daily_prompt → assemble_v1
```

改成：

```
collect（含 8 字段）→ fragment_reuse → structure_check → overview_prompt_v2 → daily_prompt_v2 → assemble_v2
```

**具体改动点：**

1. `_collect_plan_data()` 返回的 days 已经有 8 个结构字段（T2）
2. 新增 `_build_design_brief()` — 从 profile + days 特征推导路线策略（规则，~30行）
3. 新增 `_check_structure()` — 在 AI 前做 5 类检查（~40行，或调 `structure_guardrails.py`）
4. `overview_prompt` 用新版 `_P_OVERVIEW`，注入 design_brief
5. `daily_prompt` 用新版 `_P_DAILY`，注入 8 个字段
6. 最终组装改成 `report_payload_v2` 格式，加 `"schema_version": "v2"`
7. AI 输出 JSON 的 quality checker 也要对应更新

**v1 兼容：** 在 report 顶层加 `"schema_version": "v2"` 字段，renderer 检测到就走 v2 模板。

---

### T6 — renderer.py 加 v2 分支 + v2 模板
**级别：低级 AI 可做**
**文件：修改 `renderer.py`（~30行）+ 新建 `templates/itinerary_v2.html`**
**依赖：T5**

renderer 改动很小：

```python
async def _build_render_context(session, plan):
    # ... 现有逻辑 ...
    rc = plan.report_content or {}
    if rc.get("schema_version") == "v2":
        return _build_render_context_v2(rc, rendered_days)
    return { ... 现有返回 ... }
```

模板 `itinerary_v2.html` 基于现有 `itinerary_default.html` 改，新增：
- design_brief 总纲块
- 每天 must_keep / first_cut 提示
- reasoning 块
- 条件页按 section_type 渲染

---

### T7 — quality_gate.py 追加 5 个 STR grader
**级别：低级 AI 可做**
**文件：修改 `app/core/quality_gate.py`**
**工作量：~80 行**
**依赖：T5（需要 v2 payload 才能检查）**

在现有 `run_quality_gate()` 中追加对 v2 payload 的结构检查：
- STR-01：总纲完整性
- STR-02：日主线完整性
- STR-03：标题与正文一致性
- STR-04：结构性去重
- STR-05：条件页触发正确性

---

## 任务总结（精简版）

| ID | 做什么 | 级别 | 依赖 | 文件改动 |
|----|--------|------|------|---------|
| T1 | schema 类型定义 | 低级 | 无 | 新建 1 文件 |
| T2 | _collect_plan_data 扩充 8 字段 | 高级 | T1 | 改 report_generator.py |
| T3 | 重写 AI prompt | 高级 | T2 | 改 report_generator.py |
| T4 | 替换 _trigger_conditional | 高级 | T2 | 改 report_generator.py |
| T5 | 改造 generate_report 主函数 | 高级 | T2,T3,T4 | 改 report_generator.py |
| T6 | renderer v2 + 模板 | 低级 | T5 | 改 renderer.py + 新建模板 |
| T7 | 追加 STR grader | 低级 | T5 | 改 quality_gate.py |

## ✅ 已完成的高级 AI 任务（Phase 0-3 + I3）

| 文件 | 任务 | 状态 |
|------|------|------|
| `app/db/models/city_circles.py` | D1-D4: 4张新表 (city_circles, activity_clusters, circle_entity_roles, hotel_strategy_presets) | ✅ |
| `app/db/models/business.py` | D6: TripProfile 补 12 个新字段 | ✅ |
| `app/db/models/__init__.py` | 注册新 model | ✅ |
| `app/domains/planning/eligibility_gate.py` | G1: 资格过滤门 (EG-001~007) | ✅ |
| `app/domains/planning/precheck_gate.py` | G2: 前置可规避风险检查 (PC-001~005) | ✅ |
| `app/domains/planning/city_circle_selector.py` | L1: 城市圈选择器 (8维评分) | ✅ |
| `app/domains/planning/major_activity_ranker.py` | L2: 主要活动排序器 (risk不参与评分) | ✅ |
| `app/domains/planning/hotel_base_builder.py` | L3: 酒店基点策略生成器 | ✅ |
| `app/domains/planning/route_skeleton_builder.py` | S1: 日骨架生成器 (DayFrame 11字段) | ✅ |
| `app/domains/planning/fallback_router.py` | I3: 分阶段降级兼容层 (F-01~04) | ✅ |

## 待做的低级 AI 任务

| 文件 | 任务 | 状态 |
|------|------|------|
| `scripts/seed_kansai_circle.py` | D5: 关西城市圈种子数据 | ✅ |
| `app/domains/planning/secondary_filler.py` | S2: 次要活动填充 | ✅ |
| `app/domains/planning/meal_flex_filler.py` | S3: 餐厅填充 | ✅ |
| `app/domains/planning/report_schema.py` | P1: 更新 vNext payload (扩充 SelectedCircleInfo / DayFrameInfo / HotelBaseInfo) | ✅ |
| `app/domains/rendering/renderer.py` | T7a: v2 分支 | ✅ |
| `templates/itinerary_v2.html` | T7b: 新模板 | ✅ |
| `app/core/quality_gate.py` | T7: STR grader | ✅ |

## ✅ 已完成的高级 AI 任务（全部）

| 文件 | 任务 | 状态 |
|------|------|------|
| `app/domains/planning/report_generator.py` | P2: 接城市圈输出改造（generate_report_v2） | ✅ |
| `app/domains/ranking/scorer.py` | R2: theme_match → context_fit 层，area_efficiency → itinerary_fit 层 | ✅ |
| `app/domains/planning/itinerary_fit_scorer.py` | R3: 日内适配评分（5维：corridor/sequence/time/backtrack/rhythm） | ✅ |
| `app/workers/jobs/generate_trip.py` | I1: 主流程改造（城市圈链路优先，失败 fallback 旧模板） | ✅ |

注意：T2/T3/T4/T5 实际上都是改同一个文件 `report_generator.py`，所以最好**一口气做完 T2-T5**，避免多次修改同一文件的冲突。

---

## 实际执行策略

**第一轮（高级 AI 集中做）：**
1. 新建 `report_schema.py`（T1）
2. 一口气改造 `report_generator.py`（T2+T3+T4+T5 合并）

**第二轮（低级 AI 可做）：**
3. renderer v2 分支 + v2 模板（T6）
4. quality_gate 追加 STR grader（T7）

**不额外新建的文件：**
- ~~`day_skeleton_builder.py`~~ → 直接在 `_collect_plan_data()` 里加
- ~~`fact_slots.py`~~ → 快照表尚未建好，先跳过，后续再接
- ~~`structure_guardrails.py`~~ → 先内联在 `generate_report()` 里，如果复杂了再抽出去
- ~~`condition_triggers.py`~~ → 先内联替换 `_trigger_conditional()`