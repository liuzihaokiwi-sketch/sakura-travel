# A. 内容架构与生成链路改造设计

> 面向：AI 程序员 / 后端 / 内容装配 / 评测
> 
> 目标：只解决“第一部分——大的内容逻辑、大的内容缺失”，暂不处理视觉排版细节与图片策略。
> 
> 约束：尽量兼容现有片段复用、3 层报告结构、H5/PDF 双交付，不做大规模推倒重来。

---

## 1. 这份设计要解决什么

当前生成结果的主要问题不是文案不够多，而是**内容结构没有形成一个“决策型攻略”**：

1. 总纲说“每天只深耕 1–2 个街区”，但日内实际仍会跨区跳转。
2. 每天标题、时间轴、解释、亮点之间没有被同一套约束绑定，容易出现“标题说 A，正文在写 B”。
3. 用户真正需要的决策信息缺失：住哪里、为什么这样排、今天最该保什么、晚了先砍什么、哪些要提前订、最后一天是否适合返程。
4. 事实信息与策略信息混写，导致过期信息一旦混入，会直接损坏整份攻略可信度。
5. 当前内容看起来“很满”，但用户无法快速理解这趟行程的主线、取舍和执行边界。

所以本次改造的核心不是“再多写一些块”，而是：

- 把攻略从“景点介绍合集”改成“路线决策说明书”
- 让总纲 / 每天 / 条件页由同一套 schema 驱动
- 把高时效事实与低时效决策拆开
- 让 AI 只负责解释，不负责决定整体结构

---

## 2. 非目标

这份设计**不处理**下面事项：

1. 页面视觉风格大改
2. 图片资源策略和图片审核
3. 更细的文案语气优化
4. 支付、订单、客服 SOP 改造
5. 复杂旅中模式

这些内容后续可在第二阶段继续做。

---

## 3. 必须遵守的上游约束

### 3.1 不改变总交付哲学
沿用项目既有原则：

- 整份攻略必须保持 **3 层结构**
  - 总纲
  - 每天固定骨架
  - 条件页
- 不靠 token 堆厚度，要靠结构、条件触发、模板块和少量 AI 解释来堆值感。

### 3.2 不破坏片段库复用方向
沿用现有主链路：

- 先 profile normalization
- 再 fragment retrieval
- 再硬规则过滤
- 再软规则重排
- 再骨架装配
- 再动态快照补槽
- 最后 AI 少量解释

### 3.3 不立刻大改底层核心表
优先方案：

- 复用现有 `itinerary_plans / itinerary_days / itinerary_items / plan_artifacts / export_assets`
- 新内容结构先落到一个 `report_payload_v2` JSON 载荷中
- 先让生成与渲染吃同一份 payload
- 核心表迁移放后面

---

## 4. 新的内容哲学：攻略 = 决策文档，而不是地点列表

新的正文必须先回答 4 件事：

1. 为什么这份路线这样设计
2. 这份路线优先满足了什么
3. 它放弃了什么
4. 用户每天如何执行，以及出了问题先砍谁

也就是说，生成目标要从：

- “给我写一份东京 5 天攻略”

切换为：

- “在用户约束下，输出一份结构化、可执行、可解释、可删减的路线决策文档”

---

## 5. 新的核心数据模型（report_payload_v2）

建议不要再让 renderer 直接吃零散文案块，而是统一吃一个**结构化报告 payload**。

```ts
interface ReportPayloadV2 {
  meta: ReportMeta;
  profile_summary: ProfileSummary;
  design_brief: DesignBrief;
  overview: OverviewSection;
  booking_alerts: BookingAlertSection;
  prep_notes: PrepNotesSection;
  days: DaySection[];
  conditional_sections: ConditionalSection[];
  quality_flags: QualityFlags;
  versioning: VersioningInfo;
}
```

### 5.1 meta

```ts
interface ReportMeta {
  trip_id: string;
  destination: string;
  total_days: number;
  language: "zh-CN" | "en" | "ja";
  render_mode: "web" | "pdf" | "shared";
  schema_version: "v2";
}
```

### 5.2 profile_summary

只保留跟路线设计相关的标准化画像，不要原样回填整个表单。

```ts
interface ProfileSummary {
  party_type: string;
  pace_preference: "light" | "balanced" | "dense";
  budget_bias: string;
  trip_goals: string[];
  hard_constraints: string[];
  avoid_list: string[];
  hotel_constraints: HotelConstraintSummary[];
}
```

### 5.3 design_brief

这是总纲第一页的真相源，不再由 AI 自由发挥。

```ts
interface DesignBrief {
  route_strategy: string[];          // 如“先东后西”“最后一天轻收尾”
  tradeoffs: string[];               // 如“放弃 teamLab，保留节奏与晚餐体验”
  stay_strategy: string[];           // 如“全程单酒店，减少搬运行李”
  budget_strategy: string[];         // 如“高价餐集中后半段”
  execution_principles: string[];    // 如“每天最多 2 个区域”
}
```

### 5.4 overview

```ts
interface OverviewSection {
  route_summary: RouteSummaryCard[];
  intensity_map: DayIntensity[];
  anchor_events: AnchorEvent[];
  hotel_changes: HotelChange[];
  trip_highlights: string[];
}
```

### 5.5 booking_alerts / prep_notes

继续保留，但改成结构化，不再直接存大段 prose。

```ts
interface BookingAlertItem {
  entity_id?: string;
  label: string;
  booking_level: "must_book" | "should_book" | "good_to_book" | "walkin_ok";
  deadline_hint: string;
  impact_if_missed: string;
  fallback_label?: string;
}
```

---

## 6. 每天的最小真相源：DaySection

每天不再只是“timeline + 几段文案”，而是必须有一个完整的 `DaySection`。

```ts
interface DaySection {
  day_index: number;
  title: string;
  primary_area: string;
  secondary_area?: string;
  day_goal: string;
  intensity: "light" | "balanced" | "dense";
  start_anchor: string;
  end_anchor: string;
  must_keep: string;
  first_cut: string;
  route_integrity_score: number;
  risks: DayRisk[];
  slots: DaySlot[];
  reasoning: string[];
  highlights: HighlightCard[];
  execution_notes: ExecutionNotes;
  plan_b: PlanBOption[];
  trigger_tags: string[];
}
```

### 6.1 每天必须新增的 8 个字段

这是本次改造里最关键的一步：

1. `primary_area`
2. `secondary_area?`
3. `day_goal`
4. `must_keep`
5. `first_cut`
6. `start_anchor`
7. `end_anchor`
8. `route_integrity_score`

这 8 个字段一旦成为真相源，很多问题就能在生成前被挡住：

- 标题与正文不一致
- 当天没有主线
- 最后一天还在乱跳点
- 用户不知道保什么砍什么

### 6.2 DaySlot

```ts
interface DaySlot {
  slot_index: number;
  kind: "poi" | "restaurant" | "hotel" | "activity" | "transit" | "buffer";
  entity_id?: string;
  title: string;
  area: string;
  start_time_hint?: string;
  duration_mins?: number;
  booking_required?: boolean;
  weather_dependency?: "low" | "medium" | "high";
  replaceable?: boolean;
  replacement_pool?: string[];
}
```

注意：

- `activity` 必须作为一等公民加入 schema，不能再全部假装成 POI
- `buffer` 必须显式存在，否则最后一天和晚餐前的缓冲永远会被写没

---

## 7. 条件页触发逻辑改造

项目已有条件页概念，但当前更像“有就塞一点”。新方案要把条件页做成**显式规则**。

```ts
interface ConditionalSection {
  section_type:
    | "hotel"
    | "restaurant"
    | "transport"
    | "photo"
    | "budget"
    | "extra";
  trigger_reason: string;
  related_day_indexes: number[];
  payload: unknown;
}
```

### 7.1 触发器必须程序化

#### 酒店页触发
- 新入住
- 换区
- 酒店本身是体验核心
- 酒店决定第二天起点/终点

#### 餐厅页触发
- 纪念日 / 高价餐 / 稀缺预约
- 对当天节奏和时间约束很强
- 该餐是“这一天最不能砍的事”

#### 交通页触发
- 跨城
- 机场日
- 温泉区/郊区
- 复杂换乘 > 2 次

#### 出片页触发
- 强视觉主线日
- 夜景 / 樱花 / 海景 / 山景 / 高审美酒店

#### 预算页触发
- 某天明显高消费
- 容易花冤枉钱
- 需要引导“钱该花在哪儿”

### 7.2 禁止“为了显得厚而触发”
条件页不是凑页数工具。触发逻辑要写进代码，并在评测里校验。

---

## 8. 生成链路怎么改（兼容现有架构）

以 `workers/jobs/generate_trip.py` / `app/domains/planning/assembler.py` 为主线，建议拆成下面 8 步。

### Step 1：标准化画像
输入来自 `trip_profiles` / 明细表单，输出 `planning_profile`。

新增要求：
- 把“住哪里 / 是否换酒店 / 最后一天返程压力”明确进画像
- 把“可晚起 / 不想早起 / 不想太晚回”做成显式布尔约束
- 把“纪念日晚餐 / 购物 / 出片优先”从 loose tags 提升为 route-affecting flags

### Step 2：先生成日级骨架，不直接生成正文
新增中间产物：`day_skeletons`

```ts
interface DaySkeleton {
  day_index: number;
  title_candidate: string;
  primary_area: string;
  secondary_area?: string;
  target_intensity: string;
  must_keep_candidate: string;
  first_cut_candidate: string;
  slot_candidates: SlotCandidate[];
}
```

### Step 3：片段库命中改成“骨架优先”
片段复用不再主要复用 prose，而是优先复用：

- route skeleton
- decision fragment
- risk fragment
- plan B fragment

也就是：

- 先拿骨架和判断
- 后拿文案

### Step 4：装配前做 5 类结构检查

1. **日标题一致性检查**
   - 标题区域是否真的在 slot 中出现
   - 标题关键词是否至少覆盖 `primary_area`

2. **区域跳跃检查**
   - 默认每天只允许 1 个主区域，最多 1 个副区域
   - 超限则降分或打黄灯

3. **重复实体检查**
   - 同一天不得出现重复景点 / 同义重复

4. **最后一天返程检查**
   - 若有返程/收尾约束，必须保留 buffer

5. **主线完整性检查**
   - `must_keep` 必须来自实际 slot
   - `first_cut` 必须是可替换或可删除 slot

### Step 5：动态快照只补“硬事实位”
动态层只填这几类内容：

- 营业状态
- 是否需要预约
- 开放时间窗口
- 门票价格区间
- 休馆/休业风险
- 季节/天气依赖

不要让快照层改路线主线。

### Step 6：AI 只写 4 类内容

1. 总设计思路
2. 每天为什么这样排
3. 亮点解释
4. 少量语气润色

禁止 AI 直接负责：

- 决定 day title
- 决定 must_keep / first_cut
- 决定条件页是否触发
- 生成未经校验的营业信息

### Step 7：质量门控升级为“结构门控 + 事实门控”

#### 结构门控
- 总纲 4 节是否齐全
- 每天 4 节是否齐全
- 条件页是否按规则触发
- 日主线是否明确
- 是否存在重复点 / 假标题 / 伪顺路

#### 事实门控
- 预约信息是否来自快照层
- 价格是否为快照层产物
- 开放时间是否为快照层产物
- 过期字段是否进入 AI prose

### Step 8：再渲染，不反过来让模板兜底
模板只负责展示结构，不再承担纠错责任。

---

## 9. 建议新增的程序模块

### 9.1 领域层
建议新增：

- `app/domains/planning/report_schema.py`
  - 定义 `ReportPayloadV2`、`DaySection`、`ConditionalSection`
- `app/domains/planning/day_skeleton_builder.py`
  - 负责先出日级骨架
- `app/domains/planning/structure_guardrails.py`
  - 负责标题一致性、区域跳跃、重复实体、返程缓冲校验
- `app/domains/planning/condition_triggers.py`
  - 负责酒店/餐厅/交通/预算/出片页触发
- `app/domains/planning/fact_slots.py`
  - 负责把动态快照注入结构化 fact slots

### 9.2 复用已有模块
尽量复用：

- `planning/assembler.py`：改为 orchestrator，不再同时做“规划 + 文案 + 渲染预处理”
- `planning/copywriter.py`：只做 AI explanation
- `domains/rendering/renderer.py`：只吃 `report_payload_v2`

---

## 10. 数据落地建议：先轻迁移，不大动主表

### 10.1 最小可用落地法
优先新增一个 artifact 层 JSON：

```json
{
  "artifact_type": "report_payload_v2",
  "schema_version": "v2",
  "payload": { ... }
}
```

挂载位置建议二选一：

1. `plan_artifacts`
2. `export_assets`

### 10.2 暂时不要做的事

- 不要立即把所有 section 拆成很多新表
- 不要先做复杂 CMS
- 不要先做内容编辑后台
- 不要先做媒体系统联动

先把生成质量和渲染一致性打稳。

---

## 11. 必须新增的评测项

现有评测里需要补一组“内容结构完整性 grader”。

### 11.1 新 grader 维度

#### G1：总纲完整性
检查是否包含：
- 设计依据
- 总览
- 预约提醒
- 准备事项

#### G2：日主线完整性
检查是否包含：
- 主区域
- 当天目标
- must_keep
- first_cut
- 风险
- plan B

#### G3：标题与正文一致性
检查：
- day title 是否覆盖 primary area
- title 中的关键区域/活动是否实际存在

#### G4：结构性去重
检查：
- 同天是否出现重复实体
- 同类型信息是否在多个 section 机械重复

#### G5：条件页触发正确性
检查：
- 该触发的是否触发
- 不该触发的是否乱触发

### 11.2 样例回归 case
至少加入下面 case：

1. 最后一天轻收尾 + 购物 + 返程
2. 单酒店 5 天不换区
3. 已订酒店且不接受换酒店
4. 高价晚餐为主锚点
5. 带父母低体力
6. 樱花季强人流
7. 雨天替代方案
8. 纪念日晚餐 + 夜景

---

## 12. P0 / P1 实施顺序

### P0（先把内容逻辑立起来）
1. 定义 `ReportPayloadV2`
2. 定义 `DaySection` 必填字段
3. 实现 `day_skeleton_builder`
4. 实现 `structure_guardrails`
5. 实现 `condition_triggers`
6. 把 AI prose 改成只写 explanation
7. renderer 改吃结构化 payload
8. 补 8–10 个结构 grader

### P1（再增强）
1. 引入更细的 route integrity scoring
2. 条件页权重优化
3. 媒体槽位接入
4. 自助微调回写 day skeleton
5. 高价值片段自动蒸馏回库

---

## 13. 验收标准

上线前至少满足：

1. 任意一天都能明确回答：
   - 今天主线是什么
   - 今天最不能砍什么
   - 晚了先砍什么
2. 标题、时间轴、解释、亮点一致
3. 每天最多 2 个区域，超限必须显式解释
4. 最后一天默认存在收尾/返程缓冲
5. 条件页触发不再机械重复
6. 动态事实信息不由 AI 自造
7. Web/PDF 均吃同一份 `report_payload_v2`

---

## 14. 给实现者的建议

### 最重要的实现原则

先把“内容结构正确”做出来，再去谈“写得好不好看”。

工程上最值得坚持的顺序是：

1. schema
2. skeleton
3. guardrails
4. fact injection
5. AI explanation
6. render

不要反过来从模板倒推结构，也不要再让一个大 prompt 同时负责路线、解释、事实和排版。

