# 统一评分引擎 (Scoring Engine)

## 概述
两阶段评分架构：先用系统评分产出候选排序，再用编辑修正干预 shortlist。
核心原则：系统是主排序引擎，人工经验做修正而非做真相源。

## 设计原则（第一性原理版）
1. **可解释**：每个推荐必须能拆到分项
2. **可回放**：给定相同输入+快照，必须产出相同排序
3. **可版本化**：评分公式、权重、editorial_boost 都有版本号
4. **两阶段分离**：候选排序和编辑修正是独立步骤

## 为什么不用 `final = system + owner + context - risk` 直接相加
- owner_score 过重时主观漂移太大
- 无法区分系统策略进步 vs 个人偏好变化
- 后续难以做实验和训练
- 大量实体无法逐一打 0-100 分

---

## 阶段 1：候选排序分

### 公式
```text
candidate_score = 0.60 × system_score + 0.40 × context_score - risk_penalty
```

这一阶段只决定 shortlist，不决定最终推荐。

### system_score（系统评分，0-100）
由程序自动计算，代表全网公共信号 + 事实质量。

#### 景点 system_score 分项
| 子项 | 权重 | 数据来源 |
|---|---:|---|
| 平台评分与口碑 | 25% | Google Places rating |
| 评论量置信度 | 15% | review_count 归一化 |
| 城市代表性/热度 | 15% | 搜索量/攻略提及频次 |
| 与用户主题匹配度 | 20% | tags × theme_weights 计算 |
| 区域串联效率 | 15% | 同区域 POI 密度 |
| 信息新鲜度 | 10% | freshness_ts 距今天数 |

#### 酒店 system_score 分项
| 子项 | 权重 | 数据来源 |
|---|---:|---|
| 公共评分与口碑 | 20% | Google/Booking 评分 |
| 评论量置信度 | 10% | 评论数量 |
| 交通便利度 | 20% | walk_to_station + 线路数 |
| 性价比 | 20% | 价格/星级/设施比 |
| 房型与设施完整度 | 15% | 设施标签覆盖度 |
| 取消政策/可订稳定性 | 15% | 历史可订率 |

#### 餐饮 system_score 分项
| 子项 | 权重 | 数据来源 |
|---|---:|---|
| 公共评分与口碑 | 25% | Google/Tabelog 评分 |
| 评论量置信度 | 10% | 评论数量 |
| 与时段/路线适配度 | 20% | 距离+meal_slot 匹配 |
| 价格带匹配 | 15% | 用户预算 vs 餐厅价格 |
| 预约/排队可执行性 | 15% | queue_risk + accepts_reservations |
| 菜系差异化 | 15% | 同日已推荐菜系去重 |

### context_score（场景适配分，0-100）
根据用户画像动态计算。**⚠️ 当前未实现，是最高优先级待办。**

#### 计算方式
```text
context_score = Σ(用户 theme_weight_i × 实体 theme_affinity_i) / max_possible × 100
```
其中：
- `theme_weight_i`：来自 trip_profile.theme_weights，每个主题 0.0-1.0
- `theme_affinity_i`：来自 entity_tags 表，tag_score 0-5
- `max_possible`：`Σ(theme_weight_i) × 5`（所有维度都满分的理论上限）

#### 主题维度（待从 GPT 获取精确定义）
预期 8-10 个维度：
shopping / food / culture / nature / onsen / photo_spots / comfort / art / anime / nightlife

#### 场景标签库
用户侧：family / couple / solo / elder / pet / anime / shopping / onsen / food / nature / photo / museum / theme_park / culture / nightlife / skiing / tea / luxury / budget

实体侧：每个标签 0-5 强度分

### risk_penalty（风险扣分，0-30）

#### 景点风险
| 风险项 | 扣分 |
|---|---:|
| 闭馆/营业时间不稳定 | -20 |
| 交通代价过高 | -15 |
| 强季节性未提示 | -10 |
| 过度同质化 | -5 |

#### 酒店风险
| 风险项 | 扣分 |
|---|---:|
| 动态价格波动大 | -15 |
| 交通不便 | -15 |
| 差评集中于卫生/噪音 | -20 |
| 取消政策差 | -10 |

#### 餐饮风险
| 风险项 | 扣分 |
|---|---:|
| 超长排队且无替代 | -15 |
| 时段不匹配 | -10 |
| 价格虚高 | -10 |
| 营业信息不稳 | -15 |

---

## 阶段 2：编辑修正分

### 公式
```text
final_entity_score = candidate_score + editorial_boost
```

### editorial_boost 设计
| 字段 | 类型 | 说明 |
|---|---|---|
| editorial_boost | INT | -8 到 +8，常规微调 |
| editorial_label | VARCHAR | recommended / caution / avoid / force_include / force_exclude |
| editorial_reason | TEXT | 一句话原因 |
| editorial_tags | JSONB | 补充标签（适合情侣 / 二刷日本 / 温泉党 / 雨天友好） |
| theme_affinity | JSONB | 主题亲和度（tea:5, anime:0, onsen:3…），高客单主题产品用 |
| reviewed_at | TIMESTAMP | 打分时间 |

### 特殊行为
- `force_include`：无论 candidate_score 多低，都进入 shortlist
- `force_exclude`：无论 candidate_score 多高，都从 shortlist 移除
- `recommended`：+editorial_boost 正常加分
- `caution`：标注提醒但不移除
- `avoid`：从 shortlist 移除

### 为什么 -8 到 +8 够用
- candidate_score 范围约 0-100
- ±8 约 8% 修正幅度，足以调整 shortlist 前 20 的排序
- 极端场景用 force_include / force_exclude 硬干预

---

## 行程整体评分

### 公式
```text
itinerary_score = 0.45 × feasibility_score
                + 0.30 × context_fit_score
                + 0.15 × diversity_score
                + 0.10 × editorial_score
                - itinerary_risk_penalty
```

### 行程风险扣分
| 风险项 | 扣分 |
|---|---:|
| 暴走程度过高 | -20 |
| 换乘复杂 | -15 |
| 跨区折返 | -15 |
| 用餐/闭馆时间冲突 | -20 |
| 预算失真 | -15 |

---

## 数据结构

### entity_scores（候选评分记录）
| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| entity_type | VARCHAR | poi / hotel / restaurant |
| entity_id | UUID | 对象 ID |
| trip_version_id | UUID | 关联行程版本 |
| system_score | DECIMAL(5,2) | 系统评分 0-100 |
| system_score_detail | JSONB | 分项明细 |
| context_score | DECIMAL(5,2) | 场景适配分 0-100 |
| context_score_detail | JSONB | 场景分项明细 |
| risk_penalty | DECIMAL(5,2) | 风险扣分 |
| risk_penalty_detail | JSONB | 风险分项明细 |
| candidate_score | DECIMAL(5,2) | 候选排序分 |
| editorial_boost | INT | 编辑修正 |
| final_score | DECIMAL(5,2) | 最终分 |
| score_version | VARCHAR | 评分引擎版本号 |
| calculated_at | TIMESTAMP | 计算时间 |

### entity_editor_notes（编辑修正表，独立于评分计算）
| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| entity_type | VARCHAR | poi / hotel / restaurant |
| entity_id | UUID | 对象 ID |
| editorial_boost | INT | -8 到 +8 |
| editorial_label | VARCHAR | recommended / caution / avoid / force_include / force_exclude |
| editorial_reason | TEXT | 一句话原因 |
| editorial_tags | JSONB | 补充标签 |
| theme_affinity | JSONB | 主题亲和度（高客单用） |
| editor_id | VARCHAR | 编辑者 |
| version | INT | 修正版本号 |
| updated_at | TIMESTAMP | 更新时间 |

### itinerary_scores（行程评分记录）
| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| plan_id | UUID | 关联行程 |
| feasibility_score | DECIMAL(5,2) | 可执行性分 |
| context_fit_score | DECIMAL(5,2) | 适配分 |
| diversity_score | DECIMAL(5,2) | 多样性分 |
| editorial_score | DECIMAL(5,2) | 编辑分 |
| risk_penalty | DECIMAL(5,2) | 风险扣分 |
| final_score | DECIMAL(5,2) | 行程总分 |
| score_detail | JSONB | 全部明细 |
| score_version | VARCHAR | 版本号 |
| calculated_at | TIMESTAMP | 计算时间 |

---

## 推荐解释性输出
每个推荐对象必须能输出：
- 推荐分数
- 分项分数（system / context / risk / editorial）
- 关键理由 2-3 条
- 风险提醒 1-2 条
- 为什么它比备选更适合（shortlist 对比）

---

## 触发时机
- 数据采集后自动计算 system_score
- editorial_boost 独立录入，不触发重算
- 用户画像变化时重算 context_score
- shortlist 确定后合成 final_entity_score
- 行程装配后计算 itinerary_score

---

## 实现状态

| 组件 | 状态 | 文件 | 说明 |
|---|---|---|---|
| system_score 6 维度加权 | ✅ 已实现 | `app/domains/ranking/rules.py` | POI/酒店/餐厅各 6 维度 |
| risk_penalty 风险扣分 | ✅ 已实现 | `app/domains/ranking/scorer.py` | 按 entity_type 触发扣分 |
| editorial_boost ±8 | ✅ 已实现 | `app/domains/ranking/scorer.py` | `apply_editorial_boost()` |
| data_tier 置信度折扣 | ✅ 已实现 | `app/domains/ranking/rules.py` | S=1.0, A=0.9, B=0.75 |
| score_entities 批量 Job | ✅ 已实现 | `app/workers/jobs/score_entities.py` | arq Job，分批 UPSERT |
| 单元测试 | ✅ 已实现 | `tests/test_scorer.py` | 23 个测试，全通过 |
| **context_score** | ❌ **未实现** | — | **P0 优先级**，缺主题维度定义 |
| **itinerary_score 行程评分** | ❌ 未实现 | — | P1 优先级 |
| **editorial_boost 录入 API** | ❌ 未实现 | — | P1，需要 `POST /ops/entities/{type}/{id}/editorial-score` |
| **candidate_score 合成** | ❌ 未实现 | — | 等 context_score 实现后合成 `0.60*sys + 0.40*ctx - risk` |

### 当前 scorer.py 与 spec 公式的差异
当前代码 `compute_base_score()` 的行为是：
```
base_score = system_score × tier_multiplier - risk_penalty
final_score = base_score + editorial_boost
```
spec 公式要求：
```
candidate_score = 0.60 × system_score + 0.40 × context_score - risk_penalty
final_score = candidate_score + editorial_boost
```
差异：context_score 缺失，tier_multiplier 是代码额外加的（spec 未定义但合理）。
重构计划：context_score 实现后，修改 scorer.py 对齐 spec 公式。
