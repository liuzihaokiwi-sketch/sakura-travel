# 数据第一性原理

> 从"用户拿到手账那一刻的体验"倒推，什么数据真正重要、为什么重要、怎么组织。

---

## 一、产品本质

用户付 298/348 元，拿到一本纸质手账 + 贴纸包。

手账的核心价值不是"信息量"，是**判断力** —— 替用户做了以下决定：

1. **去哪**（城市圈选择 + 活动簇排序）
2. **怎么排**（每天几点做什么、路线不走回头路）
3. **怎么吃**（哪顿吃什么、多少钱、要不要预订）
4. **住哪**（几晚住哪、换不换酒店）
5. **多少钱**（预算拆解到天）
6. **提前做什么**（哪些要订、截止日期是什么）
7. **出问题怎么办**（下雨/体力不足/订不到 的 Plan B）

用户翻开手账时，每一页要传递的信号只有一个：**"这件事我帮你想好了，你照做就行。"**

---

## 二、决策链：从用户输入到最终页面

```
用户填表（6步）
  ↓
画像标准化 → 9维主题权重（shopping/food/culture/...）
  ↓
城市圈选择（kansai_classic / tokyo_classic / ...）
  ↓
资格过滤（避雷标签、人群不适合的排除）
  ↓
主活动排名 ← system_score × 0.6 + context_score × 0.4
  ↓                               ↑
  ↓                    user_weights × entity_affinity
  ↓
酒店策略（住哪几晚、换不换）
  ↓
骨架编排（每天分配主活动 + 时间槽 + 走廊）
  ↓
次要活动填充 + 餐厅填充
  ↓
预算估算 + 预订提醒 + Plan B
  ↓
页面规划（17种页面类型 → 页数预算内排版）
  ↓
文案润色（AI 生成 mood_sentence / day_intro）
  ↓
质量门 → 多模型审核 → 发布 or 人工 or 重写
```

每一步消费的数据不同，但**最终都要落到用户看到的页面上**。

---

## 三、用户在每种页面上看到什么（倒推数据需求）

### 封面
用户看到：目的地名 + 天数 + 人群类型 + 预算档位 + 封面图
← `circle.name_zh` + `duration` + `party_type` + `budget_bias` + 封面图片

### 每日执行页（最重要的页面）
用户看到：
- 标题："Day 2 京都 | 轻松"
- 心情句："今天慢慢逛，不赶。"
- 时间线：09:00 金阁寺(90min) → 11:00 岚山竹林(60min) → 12:30 午餐·嵐山よしむら(60min) → ...
- 风险提示："金阁寺周末人多，建议9点前到"
- Plan B："如果下雨，改去京都国立博物馆"

← 需要的数据：
| 数据 | 来源 | 没有会怎样 |
|------|------|-----------|
| 地点名 `name_zh` | entity_base | 无法生成 |
| 停留时间 `typical_duration_min` | pois | 时间线不准，用默认60min |
| 营业时间 `opening_hours_json` | pois | 可能推荐闭馆时段 |
| 区域 `primary_corridor` | activity_clusters | 无法判断是否走回头路 |
| 强度 `intensity` | 计算值(pace × capacity) | 心情句没依据 |
| 排队风险 `queue_risk_level` | activity_clusters | 没有风险提示 |
| 室内外 `poi_category` | pois | Plan B 无法生成 |

### 详情页（每个 S/A 级活动一页）
用户看到：大图 + "为什么推荐这里" + 贴纸区
← `hero_image_url` + `why_selected` 文案 + entity_media

### 预订提醒页
用户看到：按截止日排序的预订清单，每条有：名称、预订方式、截止日、链接、不订的后果
← `advance_booking_days` + `booking_url` + `booking_method` + `queue_wait_typical_min`

### 餐厅页
用户看到：餐厅名 + 菜系 + 人均价格 + 是否要预订
← `cuisine_type` + `budget_lunch/dinner_jpy` + `tabelog_score` + `requires_reservation`

### 酒店策略页
用户看到：住哪 × 几晚 + 为什么选这家
← `hotel.area` + `nights` + `typical_price_min_jpy` + `why_selected`

### 预算页
用户看到：每日拆解（门票 + 餐饮 + 交通 + 住宿）+ 总预算
← `admission_fee_jpy` + `budget_lunch/dinner_jpy` + transport常量 + `typical_price_min_jpy`

### 行前准备页
用户看到：上网/支付/交通卡/行李/紧急联系
← circle_knowledge 静态文本（不依赖实体数据）

---

## 四、从页面倒推：什么数据真正重要

### 第一层：没有就无法生成（硬依赖）

这些字段缺失 = 页面空白或逻辑断裂，必须有值：

**实体层 entity_base：**
- `name_zh` — 用户看到的名字
- `city_code` — 归属城市，决定分到哪天
- `entity_type` — poi/restaurant/hotel 分流
- `lat, lng` — 路线计算、走回头路检测
- `is_active` — 过滤已关闭

**绑定层 circle_entity_roles：**
- `cluster_id → entity_id → role` — **当前 P0 断裂点**，活动簇选出来后找不到实体

**活动簇层 activity_clusters：**
- `level` (S/A/B) — 主活动排序的第一筛
- `core_visit_minutes` — 决定每天能装几个活动
- `primary_corridor` — 日内路线分组，避免跨区来回跑
- `experience_family` — 节奏检查：不连续安排同类型
- `rhythm_role` — peak/contrast/recovery 节奏编排
- `energy_level` — 体力分配

### 第二层：没有可以凑合，有了显著提升

这些字段缺失 = 系统用默认值兜底，但结果不够准确：

| 字段 | 缺失时的兜底 | 有了之后提升什么 |
|------|-------------|----------------|
| `typical_duration_min` | 默认 60min | 时间线准确度 |
| `admission_fee_jpy` | 按品类默认(寺庙500/博物馆1000) | 预算准确度 |
| `opening_hours_json` | 假设全天可访问 | 避免推荐闭馆时段 |
| `budget_lunch/dinner_jpy` | 按档位默认(800-3000) | 餐费预算准确度 |
| `cuisine_type` | 标记为"日式料理" | 餐厅多样性排序 |
| `tabelog_score / google_rating` | 默认40分(中低) | 排名信号准确度 |
| `advance_booking_days` + `booking_url` | 不显示预订提醒 | 预订页有内容 |
| `typical_price_min_jpy` (hotel) | 按档位默认(5k-40k) | 住宿预算准确度 |
| `poi_category` | 无法判断室内外 | Plan B 无法生成 |
| `hero_image_url` | 占位图 | 详情页视觉质量 |
| `why_selected` 文案 | AI 临时生成 | 推荐理由可信度 |
| `transit_minutes` | 默认15min | 日内移动时间估算 |
| `seasonality` | 不过滤 | 避免推荐淡季景点 |
| `profile_fit` | 不过滤 | 避免推荐不适合人群的活动 |

### 第三层：锦上添花

有了更好，没有不影响核心流程：

- `queue_wait_typical_min` → 风险提示更具体
- `best_season` → 季节匹配微调
- `check_in/out_time` → 首日/末日时间规划更精确
- `is_family_friendly` → 亲子过滤
- `recommendation_count_30d` → 轮换避免重复
- `fatigue_weight` → 体力消耗细化
- `corridor_tags` → 次要活动路线对齐
- `mood_sentence` (AI生成) → 情感调性
- circle_knowledge 静态文本 → 行前准备

---

## 五、评分体系的第一性原理

### 当前：二维公式

```
final = 0.60 × system_score + 0.40 × context_score
```

- **system_score**（客观质量）：google_rating + review_count + data_freshness + operational_stability
- **context_score**（主观匹配）：user_theme_weights × entity_affinity（9维 shopping/food/culture/...）

### 这够了吗？

**不够。** 有一类信息既不是客观质量、也不是主题匹配，但对攻略质量至关重要：

> "这个地方 Google 评分 4.2，主题上跟用户偏好匹配——但它到底值不值得在一本手账里占一页纸？"

两个 Google 4.2 分、同样匹配"文化"主题的寺庙，一个是金阁寺（记忆点极强、出片率高），一个是某个游客很少去的小寺（当地感强、松弛）。对不同用户，选择不同。

这就是 soft_rules 想解决的事——**体验品质的主观维度**。

### 该有几维？

原设计 12 维太多，其中一半跟已有信号重叠。从第一性原理推导，真正不可从其他字段推导的维度：

| 维度 | 衡量什么 | 为什么不能用现有字段替代 |
|------|---------|----------------------|
| **打动力** (emotional_impact) | 去了会被触动吗？会记住吗？ | google_rating 衡量的是"好不好"，不是"动不动人" |
| **出片力** (visual_reward) | 拍照/分享回报 | 没有字段衡量"出不出片" |
| **在地感** (local_authenticity) | 不模板、不游客陷阱 | google_rating 高的可能恰恰是游客陷阱 |
| **松弛度** (ease_comfort) | 不折腾、去了就放松 | energy_level 衡量的是体力消耗，不是心理感受 |
| **内行感** (expert_credibility) | 用户觉得"这个推荐很懂" | 无法从评分推导，是编辑判断 |
| **转化力** (preview_hook) | Day1 预览时能不能让用户掏钱 | 商业指标，跟质量/匹配无关 |

**6 维，每维 0-5 整数（不是 0-10 浮点），降低标注成本。**

### 三维公式（未来）

```
final = 0.45 × system_score + 0.30 × context_score + 0.25 × experience_score
```

- experience_score = segment_weights × entity_experience_dims
- segment_weights 按客群调（couple → 出片力权重高，family → 松弛度权重高）

scorer.py 已经预留了这个接口（三维公式 3D vs 退化二维公式 2D），只需要：
1. 填充 6 维体验分数据（AI 批量 + S 级人工校准）
2. 定义 5 种客群权重包
3. 传入 soft_rule_score 参数即可启用

---

## 六、数据层应该怎么组织

### 原则

1. **每个字段必须能追溯到某个页面上的某个可见元素，或某个决策步骤的某个判断**。不能追溯的就不该存在。
2. **区分"实体固有属性"和"关系属性"**。`name_zh` 是固有的，`why_selected` 是跟具体行程绑定的。
3. **区分"硬事实"和"软判断"**。营业时间是硬事实（可验证），打动力是软判断（主观评估）。
4. **数据来源决定更新策略**。平台爬取的 → 定期刷新；AI 生成的 → 人工校准后锁定；编辑人工的 → 随时可改。

### 层次结构

```
┌─────────────────────────────────────────────────────────┐
│ L0 用户输入层                                            │
│  TripProfile: party_type, duration, budget, pace,       │
│  must_have_tags, avoid_tags, theme_weights(9D)          │
└──────────────────────┬──────────────────────────────────┘
                       ↓ 匹配
┌─────────────────────────────────────────────────────────┐
│ L1 圈子层（地理分组）                                     │
│  city_circles: circle_id, base_city_codes, min/max_days │
│  circle_knowledge: 静态行前准备文本                       │
│  circle_content: 人设名/人设简介                          │
└──────────────────────┬──────────────────────────────────┘
                       ↓ 包含
┌─────────────────────────────────────────────────────────┐
│ L2 活动簇层（体验单元）                                   │
│  activity_clusters:                                      │
│    身份: cluster_id, name_zh, circle_id, city_code       │
│    排序: level(S/A/B), trip_role(anchor/enrichment/buf)  │
│    时间: core_visit_minutes, transit_minutes, slack      │
│    节奏: experience_family, rhythm_role, energy_level    │
│    约束: seasonality, profile_fit, must_have_tags        │
│    预订: reservation_pressure                            │
│    绑定: anchor_entities(声明需要哪些实体)                │
└──────────────────────┬──────────────────────────────────┘
                       ↓ 绑定（circle_entity_roles）
┌─────────────────────────────────────────────────────────┐
│ L3 实体层（具体地点）                                     │
│                                                          │
│  entity_base (所有实体共享):                              │
│    身份: entity_id, name_zh/ja/en, city_code, lat/lng   │
│    状态: is_active                                       │
│    轮换: recommendation_count_30d, last_recommended_at   │
│                                                          │
│  pois (景点特有):                                        │
│    时间: typical_duration_min, opening_hours_json        │
│    费用: admission_fee_jpy                               │
│    分类: poi_category                                    │
│    预订: requires_advance_booking, advance_booking_days  │
│    预订: booking_url                                     │
│    排队: queue_wait_typical_min                          │
│    季节: best_season                                     │
│    评分: google_rating                                   │
│                                                          │
│  restaurants (餐厅特有):                                  │
│    分类: cuisine_type                                    │
│    费用: budget_lunch_jpy, budget_dinner_jpy             │
│    评分: tabelog_score                                   │
│    预订: requires_reservation, advance_booking_days      │
│    预订: booking_url                                     │
│                                                          │
│  hotels (酒店特有):                                      │
│    分类: hotel_type                                      │
│    费用: typical_price_min_jpy                           │
│    评分: google_rating, star_rating                      │
│    时间: check_in_time, check_out_time                   │
│    适配: is_family_friendly                              │
└──────────────────────┬──────────────────────────────────┘
                       ↓ 评分
┌─────────────────────────────────────────────────────────┐
│ L4 评分层（排序依据）                                     │
│                                                          │
│  entity_scores: base_score, final_score, score_breakdown │
│    ← system_score(平台评分+数据新鲜度+运营稳定度)         │
│    ← context_score(用户主题权重 × 实体主题亲和度)         │
│    ← experience_score(6维体验品质分 × 客群权重) [未启用]  │
│    ← editorial_boost(编辑人工加减分)                     │
│    ← risk_penalty(风险扣分)                              │
│    ← rotation_penalty(轮换降权)                          │
│                                                          │
│  entity_experience_dims [新表，替代 entity_soft_scores]:  │
│    emotional_impact (0-5): 打动力                        │
│    visual_reward (0-5): 出片力                           │
│    local_authenticity (0-5): 在地感                      │
│    ease_comfort (0-5): 松弛度                            │
│    expert_credibility (0-5): 内行感                      │
│    preview_hook (0-5): 转化力                            │
│    source: ai_batch / human_calibrated                   │
│                                                          │
│  segment_weights [保留，精简]:                            │
│    couple: 出片力×2, 松弛度×1.5, 打动力×1.5             │
│    family: 松弛度×2, 打动力×1, 出片力×0.5               │
│    solo:   在地感×2, 内行感×1.5, 出片力×1               │
│    senior: 松弛度×2, 打动力×1.5, 内行感×1               │
│    group:  出片力×1.5, 打动力×1.5, 松弛度×1             │
└──────────────────────┬──────────────────────────────────┘
                       ↓ 编排
┌─────────────────────────────────────────────────────────┐
│ L5 编排层（行程结构）                                     │
│                                                          │
│  route_skeleton: day_frames × slots                      │
│    ← 时间约束: core_visit + transit + queue_buffer       │
│    ← 节奏约束: experience_family 不连续                   │
│    ←          peak 间隔 ≥1 天                            │
│    ←          energy_level 先高后低                       │
│    ← 空间约束: primary_corridor 同区优先                  │
│                                                          │
│  budget_estimator: 逐日拆解                              │
│    ← admission_fee + meal_price + transport + hotel      │
│                                                          │
│  plan_b_builder: 三种备选                                │
│    ← weather: outdoor → indoor 替换                      │
│    ← low_energy: high_intensity → low 替换               │
│    ← booking_fail: advance_booking → walk_in 替换        │
└──────────────────────┬──────────────────────────────────┘
                       ↓ 渲染
┌─────────────────────────────────────────────────────────┐
│ L6 渲染层（最终页面）                                     │
│                                                          │
│  17 种页面类型，页数预算内排版:                            │
│    封面 / 目录 / 偏好达成 / 主活动一览 / 路线一览         │
│    酒店策略 / 预订提醒 / 行前准备 / 实时风险               │
│    章节开页 / 每日执行(核心) / 活动详情 / 酒店详情         │
│    餐厅详情 / 拍照主题 / 换乘详情 / 补充景点               │
│                                                          │
│  每页 = HeadingVM + HeroVM + SectionVM[] + FooterVM      │
│       + DIY zones (贴纸区 + 手写区)                       │
│                                                          │
│  页面消费的数据全部来自 L1-L5，不直接查 DB                │
│  通过 PlanningOutput 中间结构传递                         │
└─────────────────────────────────────────────────────────┘
```

---

## 七、当前断裂点与优先级

按"对最终手账质量的影响"排序：

### P0：活动簇→实体绑定（circle_entity_roles 覆盖率 26%）

**影响**：决策链在 L2→L3 断裂。选中了"岚山竹林散步线"活动簇，但找不到岚山竹林这个 POI 实体。后面所有步骤都没有数据可用。

**修复**：populate anchor_entities → match entity_base → 自动生成缺失实体 → 写入 circle_entity_roles

### P1：第二层字段稀疏

**影响**：时间线用默认值、预算用默认值、预订提醒页为空。手账"看起来像那么回事但不准"。

**优先补充**（按对用户感知影响排序）：
1. `typical_duration_min` — 时间线准确度
2. `admission_fee_jpy` / `budget_lunch_jpy` / `budget_dinner_jpy` — 预算准确度
3. `opening_hours_json` — 避免闭馆推荐
4. `advance_booking_days` + `booking_url` — 预订提醒页
5. `hero_image_url` — 详情页视觉

### P2：体验评分（6维）启用

**影响**：当前排序只靠"好不好"(system) + "对不对口"(context)。两个评分相近的实体，无法区分哪个更值得占手账的一页纸。

**修复**：
1. 定义 6 维体验分
2. AI 批量打分（基于实体名 + 描述 + 评论摘要）
3. S 级实体人工校准
4. scorer 启用三维公式

### P3：Seed 脚本整理 + 文档统一

**影响**：不影响手账质量，但影响开发效率和数据可信度。

---

## 八、统一口径（消除文档矛盾）

以下为本项目最终采纳的标准，覆盖 DATA_STRATEGY.md / OPS_GUIDE.md / 代码中的所有矛盾：

### data_tier（数据完整度档位）
- `S`: 人工校验过的完整数据
- `A`: AI 生成 + 平台爬取，未人工校验
- `B`: 仅有基础信息（名称+坐标），细节缺失

scorer.py 中 DATA_TIER_MULTIPLIER: S=1.0, A=0.95, B=0.75

### quality_tier（内容质量档位）→ 不再使用
原设计有 1-5 数字和 S/A/B/C 字母两套，互相矛盾且无代码消费。
**统一为：不设独立的 quality_tier 字段。**
- 客观质量由 system_score 体现（google_rating + review_count + freshness）
- 体验品质由 experience_dims（6维）体现
- data_tier 管数据完整度

### budget_tier（预算档位）
统一为 4 级，与 budget_estimator.py 中的 TIER 映射表一致：
- `budget`: 经济（餐~¥1000，宿~¥8000）
- `mid`: 中档（餐¥1000-3000，宿¥8000-20000）
- `premium`: 高档（餐¥3000-8000，宿¥20000-50000）
- `luxury`: 奢华（餐¥8000+，宿¥50000+）

### arrival_friendly / indoor_friendly
归属 **activity_clusters 层**（不是实体层）。
理由：这是"这条体验线适不适合到达日/雨天"的判断，不是单个 POI 的属性。

### meal_break_minutes vs meal_buffer_minutes
删除 `meal_break_minutes`（重复字段）。保留 `meal_buffer_minutes`。

---

## 九、哪些表/字段应该清理

### 可以删除的

| 项目 | 理由 |
|------|------|
| `entity_soft_scores` 表 | 替换为精简的 `entity_experience_dims`（6维 0-5） |
| `stage_weight_packs` 表 | 阶段权重不需要独立表，用 preview_hook 维度即可 |
| `preview_trigger_scores` 表 | 用 experience_dims.preview_hook 替代 |
| `swap_candidate_soft_scores` 表 | 替换排序直接用 score 差值，不需要预计算表 |
| `soft_rule_feedback_log` 表 | 反馈回收暂无实现，删除空表 |
| `meal_break_minutes` 字段 | 与 meal_buffer_minutes 重复 |

### 应该保留但移位的

| 项目 | 当前位置 | 建议移到 |
|------|---------|---------|
| `seasonal_events` | soft_rules.py | 独立为 events 层或留在 soft_rules 但改名 |
| `transport_links` | soft_rules.py | corridors 层更合理 |
| `entity_operating_facts` | soft_rules.py | catalog 层（硬事实不是软规则） |
| `timeslot_rules` | soft_rules.py | 合并到 entity_temporal_profiles |
| `area_profiles` | soft_rules.py | corridors 层 |

### 应该保留的

| 项目 | 理由 |
|------|------|
| `segment_weight_packs` | 客群权重有用，但精简为 5 个预设 × 6 维 |
| `editorial_seed_overrides` | 人工校准入口 |
| `soft_rule_explanations` | 可解释性记录 |
| `audience_fit` | 有用，但考虑合并到 experience_dims 计算过程中 |
| `product_config` / `feature_flags` / `user_events` | 基础设施，不属于 soft_rules 层 |

---

## 十、总结：一句话

**数据的价值不在于多全，在于每个字段都能追溯到用户翻开手账时的某个具体体验。** 当前最大的问题不是字段设计（设计是好的），而是 L2→L3 的绑定断裂和 L3 层字段的填充率。先把 26% 的覆盖率拉上去，再补关键字段的值，最后启用体验评分。
