# 实体评价维度设计

> 核心原则：评价服务于**行程决策**，不是写大众点评。
> 用户拿着手账本在旅途中用，需要的是"去不去"、"怎么去"、"注意什么"，不是"好不好吃"的主观讨论。

---

## 设计思路

每个实体存两类信息：
1. **结构化维度评分**（0-5 或枚举值）— 供推荐算法使用
2. **一句话评价摘要**（自然语言）— 展示在手账本上给用户看

评价来源：从 Tabelog/大众点评/Jalan 等平台的真实用户评论中，用 AI 提取总结。
过滤标准：
- 跳过纯情绪评价（"太棒了！"、"垃圾！"）
- 保留有具体细节的评价（"叉烧口感偏硬但汤底浓郁"）
- 负面评价只保留高频出现的（多人反复提到才算客观问题）

---

## 一、餐厅评价维度

### 结构化维度（算法用）

| 维度 | 字段名 | 类型 | 说明 |
|------|--------|------|------|
| 招牌菜明确度 | `signature_dish_clarity` | 枚举 clear/vague/none | 有没有一道"来了必点"的菜 |
| 排队风险 | `queue_risk` | 枚举 none/low/medium/high | 是否经常排队、排多久 |
| 预约难度 | `reservation_difficulty` | 枚举 walk_in/easy/hard/impossible | 能否直接去、需不需要提前订 |
| 语言友好度 | `language_friendliness` | 枚举 japanese_only/menu_ok/english_ok | 有没有中英文菜单或图片菜单 |
| 支付方式 | `payment_method` | 枚举 cash_only/card_ok | 很多日本小店只收现金 |
| 性价比感知 | `value_perception` | 枚举 below/fair/above | 大多数评论觉得值不值 |

### 一句话摘要（手账本用）

| 摘要类型 | 字段名 | 示例 |
|----------|--------|------|
| 推荐理由 | `why_go` | "二条市场最老的海鲜盖饭店，三色丼是招牌" |
| 实用提醒 | `practical_tip` | "只收现金，11点前去不用排队，招牌是�的鱿鱼刺身盖饭" |
| 如果不去 | `skip_if` | "不吃生鲜的话可以跳过，改去旁边的汤咖喱店" |

---

## 二、景点/活动评价维度

### 结构化维度（算法用）

| 维度 | 字段名 | 类型 | 说明 |
|------|--------|------|------|
| 最佳时段 | `best_timing` | 字符串 | "早上8-9点/日落前1小时/红叶季" |
| 天气敏感度 | `weather_sensitivity` | 枚举 any/prefer_clear/rain_ruins | 下雨天去是否影响体验 |
| 体力要求 | `physical_demand` | 枚举 easy/moderate/demanding | 老人小孩能不能去 |
| 拍照价值 | `photo_value` | 枚举 low/medium/high/iconic | 值不值得专门去拍照 |
| 人群密度 | `crowd_pattern` | 字符串 | "旅行团10-14点集中，建议早上或傍晚" |
| 停留弹性 | `duration_flexibility` | 枚举 fixed/flexible | 是否可以快速看完或者慢慢逛 |
| 儿童适合度 | `child_friendly` | 枚举 not_suitable/ok/great | 带孩子合不合适 |
| 季节依赖 | `season_dependency` | 枚举 any_season/specific_season | 是否只有特定季节值得去 |

### 一句话摘要（手账本用）

| 摘要类型 | 字段名 | 示例 |
|----------|--------|------|
| 推荐理由 | `why_go` | "北海道最大的地狱谷，硫磺蒸汽从地面喷出，视觉冲击力强" |
| 最佳体验方式 | `best_experience` | "沿木栈道走一圈约30分钟，到大汤沼可以泡免费足汤" |
| 实用提醒 | `practical_tip` | "停车场免费但车位少，建议坐巴士到登别温泉站步行10分钟" |
| 如果不去 | `skip_if` | "对硫磺味敏感的话会不舒服，可以改去附近的熊牧场" |

---

## 三、酒店评价维度

### 结构化维度（算法用）

| 维度 | 字段名 | 类型 | 说明 |
|------|--------|------|------|
| 位置便利度 | `location_convenience` | 枚举 remote/ok/convenient/excellent | 离车站/景点远不远 |
| 房间状况 | `room_condition` | 枚举 dated/acceptable/good/excellent | 设施新旧程度 |
| 温泉/浴场 | `bath_quality` | 枚举 none/basic/good/exceptional | 日本酒店的核心卖点 |
| 早餐评价 | `breakfast_quality` | 枚举 none/basic/good/highlight | 是否值得在酒店吃早餐 |
| 隔音情况 | `soundproofing` | 枚举 poor/acceptable/good | 高频差评维度 |
| 性价比 | `value_perception` | 枚举 below/fair/above | 评论中对价格的普遍感受 |
| 适合人群 | `best_for` | 字符串[] | ["couple","family","solo","business"] |

### 一句话摘要（手账本用）

| 摘要类型 | 字段名 | 示例 |
|----------|--------|------|
| 推荐理由 | `why_stay` | "露天风吕能看到洞爷湖全景，性价比是这一带最高的" |
| 实用提醒 | `practical_tip` | "check-in 15:00，建议先寄存行李去湖边逛，晚餐怀石料理需提前告知过敏原" |
| 注意事项 | `heads_up` | "靠马路的房间有噪音，订房时备注要湖景侧" |

---

## 四、特色店铺评价维度

### 结构化维度（算法用）

| 维度 | 字段名 | 类型 | 说明 |
|------|--------|------|------|
| 特色品类 | `specialty_type` | 字符串 | "手工玻璃/本地特产/老字号和果子" |
| 价格区间 | `price_feel` | 枚举 affordable/moderate/premium | 买手信的心理价位 |
| 可逛时长 | `browse_time` | 字符串 | "10-20分钟" |
| 购买必要性 | `must_buy` | 枚举 browse_only/worth_buying/must_buy | 是不是路过进去看看就行 |

### 一句话摘要（手账本用）

| 摘要类型 | 字段名 | 示例 |
|----------|--------|------|
| 推荐理由 | `why_go` | "小樽最有名的音乐盒工坊，可以现场定制刻字" |
| 实用提醒 | `practical_tip` | "二楼的限定款比一楼贵但更精致，预算3000日元左右" |

---

## 五、数据库存储方案

复用现有 `entity_descriptions` 表，扩展 description_type：

```
现有 type:
  official_summary / generated_short / generated_reason /
  expectation_hint / operator_override / why_selected /
  what_to_expect / who_it_is_for / skip_if / ordering_hint

新增 type:
  review_why_go          — 推荐理由（一句话）
  review_practical_tip   — 实用提醒
  review_skip_if         — 如果不去/不住的替代建议
  review_best_experience — 最佳体验方式（景点专用）
  review_heads_up        — 注意事项（酒店专用）
```

结构化维度存在 `entity_review_signals` 表（已有），扩展字段：

```sql
-- 已有字段：rating_source, aggregate_rating, review_count,
--           positive_tags, negative_tags, summary_tags,
--           queue_risk_level, confidence_score

-- 扩展为 JSONB 存储各维度：
ALTER TABLE entity_review_signals
ADD COLUMN dimension_scores JSONB;
-- 示例值：
-- {"queue_risk": "high", "language_friendliness": "menu_ok",
--  "payment_method": "cash_only", "value_perception": "above",
--  "signature_dish_clarity": "clear"}
```

---

## 六、评价生成流程

```
1. 爬虫从权威源拉取评论原文（Tabelog 前 50 条、Jalan 前 30 条等）
2. 存入 source_snapshots（原始数据保存）
3. AI 读取评论原文，执行：
   a. 过滤无信息量的评论（纯情绪、太短、明显水军）
   b. 提取结构化维度（从评论中判断 queue_risk 等）
   c. 生成一句话摘要（每个维度一句，从真实评论中提炼）
   d. 标注信息来源（"综合 Tabelog 47 条评论提取"）
4. 写入 entity_descriptions + entity_review_signals
5. trust_status = 'unverified'（AI 提取的，需人工抽查）
```

关键：AI 的输入是**真实评论文本**，输出是**结构化提取**，不是凭空编写。
如果某个维度在评论中完全没人提到，就留空，不猜。
