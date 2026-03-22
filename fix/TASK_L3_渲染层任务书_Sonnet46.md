# Layer 3: 报告与渲染层 — Sonnet 4.6 任务书

> 创建：2026-03-22
> 执行者：Sonnet 4.6（全部任务）
> 依据：docs/Layer_3_报告与渲染层补充设计方案_v1.md + report/ 全部文档
> 前置完成：Layer 1 (T1-T15) ✅, Layer 2 Phase A+B (E1-E6a) ✅, Layer 4 补充接入 ✅

---

## 执行顺序（严格按序）

### Phase 1：后端页面系统基座（必须先做，后面所有任务依赖它）
L3-01 → L3-02 → L3-03 → L3-04 → L3-05

### Phase 2：前端页型组件（可并行，但依赖 Phase 1）
L3-06 ~ L3-12 可并行

### Phase 3：PDF 导出与校验
L3-13 → L3-14

---

## Phase 1：后端页面系统基座

### L3-01: ReportPayloadV2 扩字段

**文件**: `app/domains/planning/report_schema.py`

**任务**: 在现有 `ReportPayloadV2` 基础上新增以下 Pydantic model 和字段：

```python
# 1. 新增 PreferenceFulfillmentItem
class PreferenceFulfillmentItem(BaseModel):
    preference_text: str           # 用户原始偏好文本
    fulfillment_type: Literal["fully_met", "partially_met", "traded_off", "not_applicable"]
    evidence: str                  # 哪个活动/酒店/安排兑现了这个偏好
    object_ref: Optional[str]      # entity_id 或 cluster_id
    explanation: str = ""

# 2. 新增 SkippedOption
class SkippedOption(BaseModel):
    name: str
    entity_type: str               # poi / restaurant / hotel
    why_skipped: str               # "距离过远" / "时间窗冲突" / "容量不足"
    would_fit_if: Optional[str]    # "如果多一天可以加入"

# 3. 新增 ChapterSummary
class ChapterSummary(BaseModel):
    chapter_id: str
    title: str
    subtitle: Optional[str] = None
    goal: str = ""
    mood: str = ""
    covered_days: List[int] = Field(default_factory=list)

# 4. 新增 EmotionalGoal
class EmotionalGoal(BaseModel):
    day_index: int
    mood_keyword: str              # "惊喜" / "安静" / "探索" / "放松" / "热闹"
    mood_sentence: str             # "今天的节奏是慢下来，在鸭川边散步"

# 5. 新增 RiskWatchItem
class RiskWatchItem(BaseModel):
    entity_id: Optional[str] = None
    risk_type: str                 # "closed_day" / "reservation_needed" / "seasonal" / "weather"
    description: str
    action_required: Optional[str] = None
    day_index: Optional[int] = None

# 6. 在 ReportPayloadV2 中新增字段:
class ReportPayloadV2(BaseModel):
    # ... 现有字段保留 ...
    preference_fulfillment: List[PreferenceFulfillmentItem] = Field(default_factory=list)
    skipped_options: List[SkippedOption] = Field(default_factory=list)
    chapter_summaries: List[ChapterSummary] = Field(default_factory=list)
    emotional_goals: List[EmotionalGoal] = Field(default_factory=list)
    risk_watch_items: List[RiskWatchItem] = Field(default_factory=list)
    selection_evidence: List[dict] = Field(default_factory=list)
```

**注意**: 不删任何现有字段，纯追加。

---

### L3-02: page_type 注册表

**文件**: 新建 `app/domains/rendering/page_type_registry.py`

**任务**: 创建页型注册表，纯 Python dict 结构（不进 DB）。

```python
from dataclasses import dataclass, field

@dataclass
class PageTypeDefinition:
    page_type: str
    topic_family: str              # "frontmatter" / "chapter" / "daily" / "detail" / "special" / "appendix"
    default_size: str              # "full" / "half" / "dual-half"
    required_slots: list[str]      # ["heading", "hero"]
    optional_slots: list[str]      # ["highlight", "evidence", "utility"]
    visual_priority: list[str]     # 渲染优先级（从上到下）
    mergeable_with: list[str]      # 可合并的页型
    print_constraints: list[str]   # ["break-before: always"]
    web_constraints: list[str]     # []
    primary_promise: str           # "告诉你为什么这样玩"

# 注册以下 17 种页型（参考 report/01_页型总表 + report/04_数据协议）:
PAGE_TYPE_REGISTRY: dict[str, PageTypeDefinition] = {
    "cover": ...,
    "toc": ...,
    "preference_fulfillment": ...,
    "major_activity_overview": ...,
    "route_overview": ...,
    "hotel_strategy": ...,
    "booking_window": ...,
    "departure_prep": ...,
    "live_notice": ...,
    "chapter_opener": ...,
    "day_execution": ...,
    "major_activity_detail": ...,
    "hotel_detail": ...,
    "restaurant_detail": ...,
    "photo_theme_detail": ...,
    "transit_detail": ...,
    "supplemental_spots": ...,
}
```

**填充规则**:
- 固定前置页(cover~live_notice): topic_family="frontmatter", print_constraints=["break-before: always"]
- chapter_opener: topic_family="chapter"
- day_execution: topic_family="daily"
- detail 页: topic_family="detail"
- primary_promise 参考 report/01 §4 的描述

提供 `get_page_type(name: str) -> PageTypeDefinition` 查询函数。

---

### L3-03: ChapterPlanner

**文件**: 新建 `app/domains/rendering/chapter_planner.py`

**输入**: `ReportPayloadV2`
**输出**: `list[ChapterPlan]`

```python
@dataclass
class ChapterPlan:
    chapter_id: str                # "ch_frontmatter" / "ch_kansai" / "ch_tokyo" / "ch_appendix"
    chapter_type: str              # "frontmatter" / "circle" / "days" / "special" / "appendix"
    title: str
    subtitle: Optional[str] = None
    goal: Optional[str] = None
    mood: Optional[str] = None
    covered_days: list[int] = field(default_factory=list)
    primary_circle_id: Optional[str] = None
    trigger_reason: Optional[str] = None
    importance: str = "high"       # "high" / "medium" / "low"
```

**规则**（参考 report/01 §3）:
1. 所有报告都有 `ch_frontmatter`（封面→动态注意事项）
2. 3-5 天: 不拆章节，所有天放一个 `ch_days` 里
3. 6-8 天: 如果跨 2 个城市圈，按圈拆 `ch_{circle_id}`
4. 9-14 天: 必须按城市圈拆章节，每个圈一个 chapter
5. 所有报告都有 `ch_appendix`

函数签名: `def plan_chapters(payload: ReportPayloadV2) -> list[ChapterPlan]`

---

### L3-04: PagePlanner

**文件**: 新建 `app/domains/rendering/page_planner.py`

**输入**: `list[ChapterPlan]` + `ReportPayloadV2`
**输出**: `list[PagePlan]`

```python
@dataclass
class PageObjectRef:
    object_type: str        # "entity" / "cluster" / "day" / "chapter" / "trip"
    object_id: str
    role: str = ""          # "primary" / "secondary"

@dataclass
class PagePlan:
    page_id: str            # "page_cover" / "page_day_3" / "page_hotel_xxx"
    page_order: int
    chapter_id: str
    page_type: str          # 对应 PAGE_TYPE_REGISTRY 的 key
    page_size: str          # "full" / "half" / "dual-half"
    topic_family: str
    object_refs: list[PageObjectRef] = field(default_factory=list)
    required_slots: list[str] = field(default_factory=list)
    optional_slots: list[str] = field(default_factory=list)
    trigger_reason: Optional[str] = None
    merge_policy: Optional[str] = None
    overflow_policy: Optional[str] = None
    priority: int = 50
    day_index: Optional[int] = None
```

**生成规则**（严格按 report/01 §6 + §8 的优先级）:

固定前置页（按序）:
1. cover → 2. toc → 3. preference_fulfillment → 4. major_activity_overview
→ 5. route_overview → 6. hotel_strategy → 7. booking_window → 8. departure_prep → 9. live_notice

章节主体（对每个 chapter）:
10. chapter_opener（仅 circle 类型章节）
11. 每天: day_execution（1天1页）
12. 主要活动: major_activity_detail（每个 S/A 级活动 1 页）
13. 酒店: hotel_detail（每个主酒店 1 页）
14. 餐厅: restaurant_detail（主要餐厅整页，次要餐厅合并半页）
15. 拍摄: photo_theme_detail
16. 交通: transit_detail（仅复杂交通日）
17. 补充: supplemental_spots

**页数控制规则**（参考 report/01 §7）:
- 3-5 天: 展开型，detail 页多
- 6-8 天: 平衡型，次要餐厅/拍摄开始合并
- 9-14 天: 章节型，次要内容进章节附页

函数签名: `def plan_pages(chapters: list[ChapterPlan], payload: ReportPayloadV2) -> list[PagePlan]`

---

### L3-05: PageViewModelBuilder

**文件**: 新建 `app/domains/rendering/page_view_model.py`

**输入**: `list[PagePlan]` + `ReportPayloadV2` + fragment outputs
**输出**: `dict[str, PageViewModel]` (page_id → view model)

```python
@dataclass
class HeadingVM:
    title: str
    subtitle: Optional[str] = None
    page_number: Optional[int] = None

@dataclass
class HeroVM:
    image_url: Optional[str] = None
    image_alt: str = ""
    orientation: str = "landscape"     # landscape / portrait / square
    caption: Optional[str] = None

@dataclass
class SectionVM:
    section_type: str                  # "timeline" / "key_reasons" / "stat_strip" / "entity_card" / "text_block" / "risk_card" / "choice_card"
    heading: Optional[str] = None
    content: Any = None                # 各 section_type 自定义结构

@dataclass
class FooterVM:
    page_number: Optional[int] = None
    chapter_title: Optional[str] = None

@dataclass
class PageViewModel:
    page_id: str
    page_type: str
    page_size: str
    heading: HeadingVM
    hero: Optional[HeroVM] = None
    sections: list[SectionVM] = field(default_factory=list)
    footer: Optional[FooterVM] = None
    day_index: Optional[int] = None
    chapter_id: Optional[str] = None
```

**任务**: 为每种 page_type 写一个 `_build_{page_type}_vm()` 函数，从 payload 中取数据填充 PageViewModel。

至少实现以下页型的 builder:
- `_build_cover_vm`
- `_build_toc_vm`
- `_build_preference_fulfillment_vm`
- `_build_day_execution_vm`
- `_build_hotel_detail_vm`
- `_build_restaurant_detail_vm`

其他页型可以先返回骨架 VM（heading + 空 sections），后续再填充。

主函数签名: `def build_view_models(pages: list[PagePlan], payload: ReportPayloadV2) -> dict[str, PageViewModel]`

---

## Phase 2：前端页型组件

**技术栈**: Next.js App Router + React Server Components + TypeScript + Tailwind CSS + shadcn/ui

### L3-06: TypeScript 类型定义

**文件**: 新建 `web/lib/report/types.ts`

**任务**: 把 Phase 1 的 Python dataclass 翻译为 TypeScript interface:
- `PagePlan`
- `PageViewModel`
- `HeadingVM` / `HeroVM` / `SectionVM` / `FooterVM`
- `ChapterPlan`
- `PageTypeDefinition`
- `ReportPayload`（只包含前端需要的字段）

同步新建 `web/lib/report/registry.ts`:
- 导出 `PAGE_TYPE_REGISTRY` 的 TS 版本
- 导出 `getPageComponent(pageType: string): React.ComponentType<PageViewModel>`

---

### L3-07: PageShell 组件

**文件**: 新建 `web/components/report/PageShell.tsx`

**任务**: 创建页面外壳组件:
- A4 纸张尺寸容器 (210mm × 297mm)
- 内边距安全区
- 页眉（章节标题 + 页码）
- 页脚（品牌 + 页码）
- `@media print` 的 `break-before: always`
- 接收 `children` + `pageSize` + `pageNumber` + `chapterTitle` props

---

### L3-08: 固定前置页组件（6 个）

**文件**: 新建 `web/components/report/page-types/` 下:
- `CoverPage.tsx` — 封面（hero image + trip title + dates + party type）
- `TocPage.tsx` — 目录（章节列表 + 页码跳转）
- `PreferencePage.tsx` — 偏好兑现页（用户偏好 → 兑现证据列表）
- `MajorActivityOverviewPage.tsx` — 主要活动总表
- `RouteOverviewPage.tsx` — 大路线总览
- `HotelStrategyPage.tsx` — 酒店策略总览

**数据源**: 每个组件接收对应的 `PageViewModel` 作为 props，不自己 fetch 数据。

**样式要求**:
- 参考 report/05_设计感规则
- 每页有明确的 hero_zone / highlight_zone / evidence_zone / utility_zone 四区划分
- 使用 Tailwind + shadcn/ui Card/Badge/Separator

---

### L3-09: 每日执行页组件

**文件**: 新建 `web/components/report/page-types/DayExecutionPage.tsx`

**任务**: 每日执行页是攻略主体，需要包含:
- 日期 + 天数标签
- 当日情绪目标（mood_sentence）
- Timeline 时间轴（按 sort_order 排列的 items）
- 每个 item: 时间 / 名称 / 类型图标 / 时长 / 简要说明
- 当日酒店标记
- 当日走廊标识
- 当日 intensity 标识（light/balanced/dense 用不同颜色）

---

### L3-10: 酒店详情页组件

**文件**: 新建 `web/components/report/page-types/HotelDetailPage.tsx`

**内容**:
- 酒店名称 + hero image
- why_selected（决策理由）
- 基本信息（地址/交通/价格带）
- 服务天数（served_days）
- 周边便利设施
- check-in/check-out 提示

---

### L3-11: 餐厅详情页组件

**文件**: 新建 `web/components/report/page-types/RestaurantDetailPage.tsx`

**内容**:
- 餐厅名称 + hero image
- why_selected
- 料理类型 / 价格带 / Tabelog 评分
- 推荐菜品
- 预约提示（requires_advance_booking）
- 哪天哪餐吃（day_index + meal_type）

---

### L3-12: 章节 opener 页组件

**文件**: 新建 `web/components/report/page-types/ChapterOpenerPage.tsx`

**内容**:
- 城市圈名称 + hero image（大图）
- chapter goal + mood
- covered_days 概览
- 本章节亮点预览（1-3 个）

---

## Phase 3：PDF 导出与校验

### L3-13: 报告 API 端点

**文件**: 新建 `web/app/api/report/[planId]/pages/route.ts`

**任务**: 创建 API 端点，返回:
```typescript
{
  meta: ReportMeta,
  page_plan: PagePlan[],
  page_models: Record<string, PageViewModel>
}
```

数据来源: 调用后端 `/api/plans/{planId}/report` 获取 `report_content` JSONB，然后在前端 server-side 转换为 page_plan + page_models。

如果后端还没有对应 API，可以先从数据库直读（通过 Prisma 或 fetch internal API）。

---

### L3-14: 页面级校验

**文件**: 新建 `app/domains/rendering/page_validator.py`

**任务**: 实现 6 条校验规则（参考 docs/Layer_3 §6.8）:

```python
PAGE_001: 每页必须有明确 page_type（在 PAGE_TYPE_REGISTRY 中存在）
PAGE_002: required_slots 不得缺失（检查 PageViewModel.sections 是否覆盖）
PAGE_003: primary_promise 不得和 topic_family 冲突
PAGE_004: 同类对象不得重复占页（同一 entity_id 不得出现在多个 detail 页）
PAGE_005: full size 页的对象不得被压成 half（检查 page_size vs required_slots 数量）
PAGE_006: print variant 不得 overflow（sections 数量 × 预估高度 ≤ A4 安全高度）
```

函数签名: `def validate_page_plan(pages: list[PagePlan], view_models: dict[str, PageViewModel]) -> list[ValidationIssue]`

返回 `ValidationIssue(page_id, rule_code, severity, message)`。

---

## 方案审计补充（原文档设计问题 + 优化项）

以下是对 `Layer_3_报告与渲染层补充设计方案_v1.md` 和 `report/` 文档审计后发现的问题，已融入任务。

---

### 问题 F1: 目录页码是 chicken-and-egg 问题（影响 L3-05, L3-08）

**问题**: TocPage 需要知道其他页的页码，但页码要等所有页布局完才能确定。如果 PageViewModelBuilder 在构建 toc_vm 时还没有页码信息，目录就是空的。

**解决方案**: 在 L3-05 中，`build_view_models()` 必须分两遍执行：
1. **第一遍**: 构建所有非 toc 页的 VM，同时按 page_order 分配页码
2. **第二遍**: 用已确定的页码回填 toc VM

```python
def build_view_models(pages, payload):
    # Pass 1: 非 toc 页
    page_number_map = {}  # page_id → page_number
    current_page = 1
    for page in pages:
        page_number_map[page.page_id] = current_page
        current_page += 1  # 或根据 page_size 判断是否占 2 页

    # Pass 2: toc 页用 page_number_map 构建
    ...
```

Sonnet 4.6 在实现 L3-05 时必须用这个两遍模式。

---

### 问题 F2: 条件页触发逻辑不够明确（影响 L3-04）

**问题**: PagePlanner 的前置页中，booking_window / departure_prep / live_notice 不是所有行程都有。原文档没说清楚触发条件是什么。

**解决方案**: 在 L3-04 的 PagePlanner 中，以下页型为**条件触发**，必须检查数据是否存在：

```python
# 条件页触发规则（PagePlanner 必须实现）
CONDITIONAL_PAGES = {
    "preference_fulfillment": lambda p: len(p.preference_fulfillment) > 0,
    "booking_window":         lambda p: any(
        d.get("booking_items") for d in p.days
    ) or len(p.risk_watch_items) > 0,
    "departure_prep":         True,  # 始终生成（有静态块）
    "live_notice":            lambda p: any(
        r.risk_type in ("weather", "seasonal") for r in p.risk_watch_items
    ),
    "photo_theme_detail":     lambda p: len(p.photo_themes or []) > 0,
    "transit_detail":         lambda p: any(
        f.get("day_type") == "transfer" for f in (p.day_frames or [])
    ),
    "supplemental_spots":     lambda p: len(p.supplemental_items or []) > 0,
}
```

数据不足的条件页直接跳过，不生成空页。page_order 不因跳过而断号（自动重排）。

---

### 问题 F3: 多圈行程时 ReportPayloadV2 只有单圈（影响 L3-01, L3-03）

**问题**: 当前 `ReportPayloadV2.meta.circle` 是 `Optional[SelectedCircleInfo]`（单圈）。但 9-14 天行程可能跨 2-3 个城市圈。ChapterPlanner 需要知道每天属于哪个圈才能按圈拆章节。

**解决方案**: 在 L3-01 中，ReportPayloadV2 新增:

```python
class ReportPayloadV2(BaseModel):
    # ... 现有字段 ...
    circles: List[SelectedCircleInfo] = Field(
        default_factory=list,
        description="多圈行程时，按顺序列出所有城市圈"
    )
    day_circle_map: dict[int, str] = Field(
        default_factory=dict,
        description="day_index → circle_id 映射，ChapterPlanner 用"
    )
```

ChapterPlanner (L3-03) 的章节拆分规则改为：
- 如果 `len(payload.circles) <= 1` → 不拆章节
- 如果 `len(payload.circles) >= 2` 且 `total_days >= 6` → 按 `day_circle_map` 拆章节

---

### 问题 F4: hero image 来源未定义（影响 L3-08 ~ L3-12 所有含 hero 的页）

**问题**: HeroVM 需要 `image_url`，但当前 entity_base 没有 `hero_image_url` 字段。EntityMedia 表有图片，但没有明确的"哪张图做 hero"的优先级逻辑。

**解决方案**: 在 L3-05 中，PageViewModelBuilder 需要一个 `_resolve_hero_image()` 辅助函数:

```python
def _resolve_hero_image(
    entity_id: Optional[str],
    entity_type: str,
    page_type: str,
    payload: ReportPayloadV2,
) -> Optional[HeroVM]:
    """
    图片解析优先级：
    1. page_hero_registry 表（L1 已建）有该 entity 的 hero 配置 → 直接用
    2. entity_media 表中 media_type="hero" 的图片
    3. entity_media 表中 sort_order 最小的图片
    4. 页型默认 placeholder（如 "/assets/placeholders/hotel_default.jpg"）
    5. None（前端组件需要处理无图状态）
    """
```

前端组件（L3-08~12）必须处理 `hero = null` 的情况，显示优雅的无图布局而不是空白。

---

### 问题 F5: 餐厅 dual-half 合并规则不明确（影响 L3-04）

**问题**: 文档说"次要餐厅合并半页"，但什么算"次要"？两个半页怎么配对？

**解决方案**: 在 L3-04 的 PagePlanner 中明确：

```python
# 餐厅页合并规则
# 1. "主要餐厅" = meal style 为 "destination_meal" 或 restaurant 的 role 为 "anchor"
# 2. "次要餐厅" = meal style 为 "route_meal" 或 "quick"
# 3. 主要餐厅 → page_size="full"
# 4. 次要餐厅 → page_size="half"，两两配对进同一个 "dual-half" 页
# 5. 如果次要餐厅为奇数个，最后一个单独做 "half" 页（与 supplemental_spots 合并）
# 6. 配对优先同章节 > 同天 > 同走廊
```

---

### 问题 F6: EmotionalGoal 和 PreferenceFulfillment 的数据生成者未定义（影响整个 pipeline）

**问题**: 任务书定义了数据结构，但没说**谁来填充**这些字段。如果交给 Sonnet 4.6，它可能留空。

**解决方案**: 明确生成责任链（Sonnet 4.6 只需要知道输入从哪来）：

```
EmotionalGoal:
  来源 1: route_skeleton_builder 的 DayFrame.title_hint + intensity → 规则映射
  来源 2: major_activity_ranker 的 cluster.mood_tag → 传递到对应天
  规则: intensity=light → "放松", intensity=dense → "探索",
        arrival → "初见", departure → "收官"
  填充位置: report_generator.py 的 _collect_plan_data() 中规则生成

PreferenceFulfillmentItem:
  来源 1: TripProfile.trip_goals → 原始偏好文本
  来源 2: generation_decisions 中 stage="major_activity_plan" 的 explain → evidence
  来源 3: generation_decisions 中 stage="hotel_strategy" 的 explain → evidence
  规则: 遍历 trip_goals，对每条查找 decisions 中是否有匹配的 why_selected
  填充位置: report_generator.py 的新增函数 _build_preference_fulfillment()

SkippedOption:
  来源: major_activity_ranker 中 selected=False 的 RankedMajor
  规则: 取 explain.why_not_selected 作为 why_skipped
  填充位置: report_generator.py 的新增函数 _build_skipped_options()
```

**新增任务 L3-15**: 在 `report_generator.py` 中新增 3 个函数填充上述字段。Sonnet 4.6 可以用规则实现，不需要 AI 调用。

---

### 问题 F7: print/web 双模式组件没有明确策略（影响 L3-07 ~ L3-12）

**问题**: 文档强调"同一套 page semantics 输出到 Web 和 Print"，但前端组件只写了一套。Web 有交互（跳转、hover），Print 纯静态。如果不区分，会导致 PDF 出现 hover 态或交互残留。

**解决方案**: PageShell (L3-07) 必须接收 `mode: "screen" | "print"` prop：

```tsx
// PageShell.tsx
interface PageShellProps {
  mode: "screen" | "print"
  pageSize: "full" | "half" | "dual-half"
  pageNumber?: number
  chapterTitle?: string
  children: React.ReactNode
}
```

**规则**:
- `mode="screen"`: 用 `max-w-[210mm] mx-auto` 模拟纸张，允许 scroll、anchor 跳转
- `mode="print"`: 用 `w-[210mm] h-[297mm]` 精确尺寸，`break-before: always`
- 前端组件内部用 `mode` 判断是否渲染交互元素（如 TocPage 的 anchor link）

`/plan/[id]` route 用 `mode="screen"`，`/plan/[id]/print` route 用 `mode="print"`。

---

### 问题 F8: page_plan 没有持久化（影响一致性）

**问题**: 当前设计中 page_plan 每次渲染都重新计算。如果 PDF 导出和 Web 预览之间用户数据有变化（如 entity 被标记 stale），两次渲染的 page_plan 可能不同，导致 PDF 和 Web 不一致。

**解决方案**: 在 L3-04 的 PagePlanner 输出后，立即写入 `plan_metadata.page_plan`:

```python
# page_planner.py
async def plan_pages_and_persist(
    chapters, payload, session, plan_id
) -> list[PagePlan]:
    pages = plan_pages(chapters, payload)

    # 持久化到 plan_metadata
    plan = await session.get(ItineraryPlan, plan_id)
    if plan:
        meta = plan.plan_metadata or {}
        meta["page_plan"] = [asdict(p) for p in pages]
        meta["page_plan_version"] = "1"
        plan.plan_metadata = meta
        await session.flush()

    return pages
```

后续渲染（Web/PDF）优先从 `plan_metadata.page_plan` 读取已持久化的 page_plan，避免重算。

---

### 问题 F9: 超长行程的页数爆炸（影响 L3-04）

**问题**: 14 天行程如果每天 1 页执行 + 每个活动 1 页 + 每个酒店/餐厅 1 页，可能产出 60-80 页。文档说"页数不是目标"，但没有硬上限。

**解决方案**: 在 L3-04 中增加页数预算机制：

```python
# page_planner.py
MAX_PAGES_BY_DURATION = {
    (1, 3):  25,   # 1-3 天最多 25 页
    (4, 5):  35,   # 4-5 天最多 35 页
    (6, 8):  50,   # 6-8 天最多 50 页
    (9, 14): 70,   # 9-14 天最多 70 页
}

# 超预算时的裁剪规则（按优先级从低到高裁）:
# 1. supplemental_spots → 合并或删除
# 2. transit_detail → 合并到 day_execution
# 3. 次要 restaurant_detail → 从 full 降级为 half，或合并
# 4. 次要 photo_theme_detail → 合并
# 5. 永远不裁: 固定前置页、day_execution、major_activity_detail
```

---

### 问题 F10: SectionVM.content 类型不明确（影响 L3-05, L3-06）

**问题**: `SectionVM.content: Any` 类型不安全。不同 `section_type` 需要不同的 content 结构，但 `Any` 让前端无法类型检查。

**解决方案**: 在 L3-05 和 L3-06 中，为每种 section_type 定义具体的 content 类型:

```python
# Python (L3-05)
@dataclass
class TimelineContent:
    items: list[TimelineItemVM]       # [{time, name, type_icon, duration, note}]

@dataclass
class KeyReasonsContent:
    reasons: list[str]

@dataclass
class StatStripContent:
    stats: list[dict]                 # [{label, value, unit}]

@dataclass
class EntityCardContent:
    entity_id: str
    name: str
    entity_type: str
    hero_image: Optional[str]
    tagline: str
    stats: list[dict]

@dataclass
class RiskCardContent:
    risk_type: str
    severity: str
    description: str
    action: Optional[str]

# SectionVM 改为 Union
SectionContent = Union[TimelineContent, KeyReasonsContent, StatStripContent, EntityCardContent, RiskCardContent, dict]

@dataclass
class SectionVM:
    section_type: str
    heading: Optional[str] = None
    content: SectionContent = field(default_factory=dict)
```

TypeScript 侧 (L3-06) 同理用 discriminated union:
```typescript
type SectionContent =
  | { type: "timeline"; items: TimelineItem[] }
  | { type: "key_reasons"; reasons: string[] }
  | { type: "stat_strip"; stats: Stat[] }
  | { type: "entity_card"; entity: EntityCardData }
  | { type: "risk_card"; risk: RiskCardData }
```

---

## 补充任务

### L3-15: report_generator 填充新字段（规则函数）

**文件**: 修改 `app/domains/planning/report_generator.py`

**任务**: 在 `_collect_plan_data()` 或 `generate_report_v2()` 中新增 3 个纯规则函数（不调 AI）:

1. `_build_preference_fulfillment(profile, decisions) -> list[PreferenceFulfillmentItem]`
   - 遍历 TripProfile.trip_goals
   - 对每条 goal，在 generation_decisions 中搜索匹配的 why_selected 作为 evidence
   - 没找到匹配 → fulfillment_type="not_applicable"

2. `_build_skipped_options(ranking_result) -> list[SkippedOption]`
   - 遍历 ranking_result.all_ranked 中 selected=False 的项
   - 取 explain.why_not_selected 作为 why_skipped

3. `_build_emotional_goals(day_frames) -> list[EmotionalGoal]`
   - 规则映射: intensity → mood_keyword, day_type → mood_sentence
   - arrival → "初见这座城市" / departure → "最后的散步与收官"

**注意**: 这些函数的输出要写入 ReportPayloadV2 的对应字段。

---

## 注意事项（给 Sonnet 4.6）

1. **不删任何现有代码**。所有修改都是新增文件或追加字段。
2. **report_generator.py 不改**（除了 L3-15 的 3 个新增函数）。Phase 1 只是新建渲染中间层。
3. **renderer.py 不改**。现有 Jinja 渲染保留为 fallback。
4. **每个 Python 文件头部写清楚 docstring**，说明输入/输出/依赖。
5. **前端组件必须类型安全**，所有 props 用 TypeScript interface 定义。
6. **不要在组件里 fetch 数据**。数据通过 props 从 page route 传入。
7. **print CSS 用 `@media print` 块**，不要用内联 style。
8. **PageShell 必须区分 screen/print mode**（见 F7）。
9. **build_view_models 必须两遍构建**（见 F1），先分配页码再填 toc。
10. **条件页必须检查数据是否存在再生成**（见 F2），不生成空页。
11. **SectionVM.content 必须用具体类型**（见 F10），不用 Any/dict。
12. **page_plan 生成后立即持久化到 plan_metadata**（见 F8）。
13. **超长行程必须有页数预算裁剪**（见 F9）。
14. **所有含 hero 的组件必须处理无图状态**（见 F4）。
15. **新建的目录结构**:
   ```
   app/domains/rendering/          # 新建目录
     __init__.py
     page_type_registry.py         # L3-02
     chapter_planner.py            # L3-03
     page_planner.py               # L3-04
     page_view_model.py            # L3-05
     page_validator.py             # L3-14
   web/lib/report/                 # 新建目录
     types.ts                      # L3-06
     registry.ts                   # L3-06
   web/components/report/          # 新建目录
     PageShell.tsx                  # L3-07
     page-types/                   # L3-08 ~ L3-12
   web/app/api/report/             # L3-13
   ```
