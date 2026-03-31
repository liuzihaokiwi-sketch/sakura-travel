# 检查点 1-2 审视 + 检查点 3 任务分配

> 日期: 2026-03-31
> 审视原则: 从第一性原理出发 — 系统唯一目的是为每位用户生成一本值 298 元的手账本

---

## 一、全局健康度诊断

### 1.1 离目标还有多远？

**目标**: 用户输入"北海道5天情侣中档" → 2-4 小时后拿到一本内容饱满、信息准确的 PDF 手账本。

**当前状态**: Pipeline 端到端跑通，7 个测试用例全部 PASS（65-71/80），但生成的内容还**不能卖**。

**差距分析**:

| 维度 | 目标 | 现状 | 差距 |
|------|------|------|------|
| 每天活动数 | 4-6 POI + 2 餐厅 | 6-12 POI + 0-2 餐厅 | POI 过多但质量参差，餐厅非札幌城市几乎没有 |
| 餐厅覆盖 | 10 城市均有 | 仅 6 城市有餐厅（札幌 220，其他 1-14） | 4 个城市 0 家餐厅 |
| 营业时间 | 100% 核心实体有 | POI 2.3%，餐厅 0% | 几乎全部缺失 |
| 推荐理由 | 每个活动有 | 0% | 完全缺失 |
| 价格信息 | 核心实体有 | 餐厅 4.6% | 几乎缺失 |
| 季节适配 | best_season 覆盖 | 6.5% POI 有标注 | 大面积缺失 |
| 交通说明 | 每步有 | 0% | 完全缺失 |
| 实体图片 | 80% 有 | 未统计 | 待确认 |
| 文案质量 | 有温度的手写感 | 无文案 | 完全缺失 |

### 1.2 系统性问题（不是 bug，是架构缺陷）

| # | 问题 | 影响 | 根因 |
|---|------|------|------|
| S1 | **餐厅数据断层** | 非札幌城市午餐/晚餐无候选 | B1 Tabelog 只跑了札幌，其他城市需要 Google Places restaurant type 补充 |
| S2 | **营业时间全面缺失** | 无法做定休日检查，无法展示给用户 | Google Places API 有此数据但批量拉取时没存 |
| S3 | **core_visit_minutes 全部为 0** | skeleton 计算容量不准 | cluster 创建时没填此字段 |
| S4 | **seasonal_events 表空** | 无法提醒用户"2月有雪祭" | 数据未采集 |
| S5 | **secondary_filler + meal_filler 仍在跑** | generate_trip 浪费计算，维护负担 | timeline_filler 已替代但旧代码未清退 |
| S6 | **hokkaido_city_circle 空壳** | 3天短行程无圈可选 | 数据未绑定 |
| S7 | **best_season 大面积缺失** | 季节过滤效果有限 | 需要从实体名称/类型/seasonality 推断回填 |
| S8 | **价格信息缺失** | 无法做预算估算，无法展示 | Google Places price_level 和 Tabelog 价格未存 |

### 1.3 代码健康度

| 问题 | 严重度 | 说明 |
|------|--------|------|
| generate_trip.py 1763 行 | 中 | 太长，步骤 7-8 的旧 filler 可移除 |
| fallback_router.py 死代码 | 低 | 所有 property 返回 False |
| transaction bug 已报但未修 | 高 | trace_writer.finish_run() 异常导致 session rollback |
| itinerary_fit_scorer 空转 | 中 | 结果不传给 timeline_filler |

---

## 二、检查点 1 审视

### 已完成且质量 OK
- A1 数据源注册中心 — 10 个源，结构清晰
- A2 AI 数据清除 — 208 条标记 inactive
- A3 气候+假日表 — 120 条气候（10城x12月），35 条假日
- B2 Google Places 札幌 — 173 POI + 56 hotel，99.7% 有评分
- B5 城市特色菜系 — 29 条

### 需要补充
- **B1 Tabelog 只跑了札幌** → 其他城市餐厅数据断层
- **B2 Google Places 只跑了札幌** → 其他城市 POI 是之前 Sonnet 跑的，质量待确认
- **营业时间未采集** → Google Places API 有但没存

### 本轮修复（今天已完成）
- timeline_filler 城市映射：从 DB 查 cluster→city_code（不再硬编码前缀）
- timeline_filler 酒店坐标：从 DB 酒店实体取均值（不再硬编码）
- timeline_filler 午后评分：去掉负向惩罚
- eligibility_gate EG-005：直接读 Poi.best_season（不再依赖 tags 间接传递）
- city_circle_selector：天数限制改为软降分（3天也能去北海道）
- city_circle_selector：空壳圈检测（无 entity_roles 的圈自动拒绝）

---

## 三、检查点 2 审视

### 已完成且质量 OK
- FIX-1~4 数据修复 — 1,259 活跃实体
- C2 维度提取 — 100 个实体有 review signals，166 条描述
- C3 标签生成 — 483 条标签（5 个命名空间）
- D2 片段创建 — 30 个 day_fragments

### 质量不足之处
- **C2 覆盖率太低** — 1,259 实体中只有 100 个有 review signals（8%）
- **D2 片段内容薄** — 30 个片段，但 fragment 是否引用了真实 entity_id？需验证
- **C3 标签分布不均** — practical 267 条但 caution 仅 14 条
- **C1 评论采集未做** — C2 的维度提取缺少原始评论支撑

---

## 四、任务分配：剩余工作 + 检查点 3

### 分类原则
- **Opus**: 需要深度思考的架构决策、质量审核、跨模块协调
- **Sonnet**: 明确的数据处理、批量操作、模式化代码
- **思考强度**: 深度（需要理解全局上下文和权衡）/ 普通（有明确的输入输出规范）

---

### 第一优先级：修数据断层（不修这些，后面都白做）

#### T1. 非札幌城市餐厅数据补充 [Sonnet · 普通]
```
问题: hakodate 2家, otaru 3家, asahikawa 1家, 4个城市 0家
方案: Google Places Nearby Search, type=restaurant, 每城市拉 30-50 家
      优先拉 rating > 3.5 的
存入: entity_base + restaurants 表
验证: 每个城市至少 20 家活跃餐厅
预计: 2 小时
```

#### T2. 营业时间批量补充 [Sonnet · 普通]
```
问题: POI 2.3%, 餐厅 0% 有营业时间
方案: Google Places Details API, 批量查 opening_hours
      优先处理: 已在 day_fragments 中引用的实体 + rating > 4.0 的
存入: pois.opening_hours_json / restaurants.opening_hours_json
同时存: entity_operating_facts（提取 closed_days）
验证: 核心实体（被片段引用的）80% 有营业时间
预计: 3 小时（API 调用 + 解析）
```

#### T3. best_season 批量回填 [Sonnet · 普通]
```
问题: 只有 48/742 POI 有 best_season
方案: 规则推断（不用 AI）
  - poi_category in (ski, ski_resort) → winter
  - name 含 "花/flower/lavender" → summer
  - name 含 "雪/snow/ice/冰" → winter
  - name 含 "紅葉/紅叶/autumn" → autumn
  - name 含 "桜/cherry/sakura" → spring
  - onsen → all (全年可泡)
  - museum/shrine/temple/landmark → all
  - 从 activity_clusters.seasonality 继承（cluster 标了 winter_only → 其 anchor 实体也标 winter）
存入: pois.best_season
验证: best_season 覆盖率 > 60%
预计: 1 小时
```

#### T4. core_visit_minutes 补充 [Sonnet · 普通]
```
问题: 35 个 cluster 全部为 0
方案: 从 cluster 的 anchor 实体的 typical_duration_min 取最大值
      如果 anchor 也没有 → 按 capacity_units 推算（1.0→180min, 0.5→90min）
验证: 35 个 cluster 全部有 core_visit_minutes > 0
预计: 30 分钟
```

#### T5. 价格信息补充 [Sonnet · 普通]
```
问题: 餐厅 4.6% 有价格
方案:
  - 从 Google Places price_level (0-4) 映射到价格范围
  - Tabelog 页面有价格信息可爬
  - 最低限度: 按 cuisine_type 设默认价格带
    ramen → 800-1200 JPY
    sushi → 2000-5000 JPY
    kaiseki → 8000-20000 JPY
    izakaya → 3000-5000 JPY
    cafe → 500-1500 JPY
存入: restaurants.price_range_min_jpy / price_range_max_jpy
验证: 餐厅 80% 有价格范围
预计: 1.5 小时
```

---

### 第二优先级：内容质量提升

#### T6. 清退旧 filler 代码路径 [Opus · 深度]
```
问题: generate_trip.py 步骤 7-8 的 secondary_filler + meal_filler 仍在运行
      但其结果不传给 timeline_filler → 纯粹浪费
方案:
  1. 步骤 7-8 的候选池构建逻辑（circle_entity_roles 查询 + entity_base 补充）
     → 提取为独立函数 build_candidate_pools()
  2. secondary_filler + meal_filler 调用 → 删除
  3. itinerary_fit_scorer 如果不用 → 也删除或标记为 optional
  4. fallback_router.py 的 property 全部返回 False → 清理或删除文件
注意: 不要删 secondary_filler.py 和 meal_flex_filler.py 文件本身（可能有其他调用方）
      只从 generate_trip.py 的关键路径移除
验证: generate_trip 仍能端到端跑通，7 个测试用例不退步
思考强度: 深度 — 需要理解哪些数据流是真正在用的
预计: 2 小时
```

#### T7. transaction bug 修复 [Opus · 深度]
```
问题: trace_writer.finish_run() 异常导致 session abort
方案:
  在 generate_trip.py 的 except 块中加 savepoint 或隔离 trace 写入
  trace_writer 使用独立事务或 savepoint 写入，不影响主事务
验证: 制造 trace_writer 异常 → 主事务仍然提交 → itinerary_days/items 写入成功
思考强度: 深度 — 需要理解 async session 的事务语义
预计: 1.5 小时
```

#### T8. hokkaido_city_circle 数据填充 [Sonnet · 普通]
```
问题: hokkaido_city_circle 有定义但无 entity_roles 和 clusters
方案:
  从 hokkaido_nature_circle 复制适合短行程的子集:
  - clusters: 札幌+小樽的 cluster（约 15 个）
  - entity_roles: 对应实体绑定
  或者: 将 hokkaido_nature_circle 的 min_days 从 4 改为 2
  → 后者更简单，但前者更正确（city_circle 应该是城市圈的轻量版）
决策交给 Opus 在 T6 中一并考虑
预计: 1 小时
```

#### T9. seasonal_events 数据填充 [Sonnet · 普通]
```
问题: 表为空，无法提醒"2月有雪祭"
方案: 手动录入北海道核心季节事件（约 20 个）
  - 札幌雪祭 (2月初, sapporo, crowd_impact=5)
  - 薰衣草季 (7月, furano, crowd_impact=4)
  - 红叶季 (10月, 全域, crowd_impact=3)
  - 函馆夜景祭 (12月, hakodate, crowd_impact=2)
  - 小樽雪灯路 (2月, otaru, crowd_impact=3)
  - 登别地狱祭 (8月, noboribetsu, crowd_impact=3)
  等
存入: seasonal_events
验证: 各月份查询能返回对应事件
预计: 1 小时
```

---

### 第三优先级：检查点 3 — 模板 + PDF

#### T10. 片段文案生成 [Sonnet · 普通]（对应原 D3）
```
为 30 个 day_fragments 生成:
  - title_zh: "小樽·港町漫步半日"
  - summary_zh: 一段话描述体验
  - 每个活动的过渡文案
使用阿里 DashScope API（不用 Anthropic，高并发场景）
验证: 每个片段有 title_zh + summary_zh
预计: 2 小时
```

#### T11. 推荐理由生成 [Sonnet · 普通]（新增，对应 QTY-08）
```
问题: QTY-08 推荐理由 0% 覆盖 → 质量门控必挂
方案: 从 entity_descriptions + entity_tags + review_signals 拼接
  - "Tabelog 3.65★ 的味噌拉面名店，招牌浓厚味噌汤底"
  - "Google 4.5★ 北海道大学银杏大道，秋季必访"
  如果没有足够信息 → 从 poi_category + google_rating 生成基础版
存入: copy_enrichment 的 why_selected 字段
验证: QTY-08 通过
预计: 2 小时
```

#### T12. 交通说明生成 [Sonnet · 普通]（新增，对应 QTY-03）
```
问题: QTY-03 交通说明 0% 覆盖 → 质量门控必挂
方案:
  - timeline_filler 已经计算了 travel_from_prev_min
  - 根据距离自动生成: "步行约 8 分钟" / "JR 约 25 分钟" / "地铁约 15 分钟"
  - 城市间: "JR 特急约 3.5 小时"
存入: itinerary_item.transport_note 或 notes_zh
验证: QTY-03 通过
预计: 1.5 小时
```

#### T13. PDF 渲染完善 [Sonnet · 普通]（对应原 E2）
```
每天 5-6 个活动 + 餐厅 + 交通说明
实体图片（如果有）
实用提醒（practical_tip）
每日预算估算
Tabelog/Google 评分展示
验证: 5 天 PDF，人工检查每页内容饱满
预计: 3 小时
```

#### T14. 预制页面 [Sonnet · 普通]（对应原 E3）
```
北海道美食图鉴、行前准备、交通指南、实用信息、天气穿衣
验证: PDF 含这些页面
预计: 2 小时
```

#### T15. 端到端验证 + 质量审核 [Opus · 深度]（对应原 F1）
```
1. 跑 test_hokkaido_pipeline.py 全 7 个用例
2. 选 HK-01 生成完整 PDF
3. 逐项人工验证:
   - 地名 Google Maps 能找到
   - 营业时间正确
   - 价格准确
   - 交通合理
   - 评分来自权威源
   - 无 AI 编造内容
   - 拿着 PDF 感觉值 298 元
4. 对比 ChatGPT 生成的同需求行程
验证: 在信息准确性上有明显优势
思考强度: 深度
预计: 3 小时
```

---

## 五、执行排期

### 批次 1：数据断层修复（必须先做，后续都依赖）

| 任务 | 执行者 | 思考强度 | 依赖 | 预计 |
|------|--------|----------|------|------|
| T1 非札幌餐厅 | Sonnet | 普通 | 无 | 2h |
| T2 营业时间 | Sonnet | 普通 | 无 | 3h |
| T3 best_season 回填 | Sonnet | 普通 | 无 | 1h |
| T4 core_visit_minutes | Sonnet | 普通 | 无 | 0.5h |
| T5 价格信息 | Sonnet | 普通 | 无 | 1.5h |
| T9 seasonal_events | Sonnet | 普通 | 无 | 1h |

**全部可并行，Sonnet 一人可做，总计约 9 小时**

### 批次 2：架构清理 + 内容生成（批次 1 完成后）

| 任务 | 执行者 | 思考强度 | 依赖 | 预计 |
|------|--------|----------|------|------|
| T6 清退旧 filler | Opus | 深度 | 无 | 2h |
| T7 transaction bug | Opus | 深度 | 无 | 1.5h |
| T8 city_circle 数据 | Sonnet | 普通 | T6 决策 | 1h |
| T10 片段文案 | Sonnet | 普通 | T1 | 2h |
| T11 推荐理由 | Sonnet | 普通 | T1+T2 | 2h |
| T12 交通说明 | Sonnet | 普通 | 无 | 1.5h |

**Opus T6+T7 并行，Sonnet T8+T10+T11+T12 并行**

### 批次 3：PDF 渲染 + 终验（批次 2 完成后）

| 任务 | 执行者 | 思考强度 | 依赖 | 预计 |
|------|--------|----------|------|------|
| T13 PDF 渲染 | Sonnet | 普通 | T10+T11+T12 | 3h |
| T14 预制页面 | Sonnet | 普通 | 无 | 2h |
| T15 端到端验证 | Opus | 深度 | 全部 | 3h |

---

## 六、上线检查清单（适用于所有城市）

每个新城市上线前必须通过:

```
□ entity_base: POI >= 50, restaurant >= 20, hotel >= 10
□ 100% 实体有 lat/lng 坐标
□ 90% POI 有 google_rating
□ 80% 餐厅有 tabelog_score 或 google_rating
□ 80% 核心实体有 opening_hours_json
□ 60% POI 有 best_season 标注
□ activity_clusters >= 5，全部有 core_visit_minutes > 0
□ circle_entity_roles: anchor_poi >= 5, meal_destination >= 3
□ city_climate_monthly: 12 条（每月一条）
□ day_fragments >= 3
□ seasonal_events: 至少录入本城市核心季节事件
□ test_hokkaido_pipeline.py 跑通且 >= 48/80
```
