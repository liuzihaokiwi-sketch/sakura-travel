## 11. 片段攻略库：必须成为默认生成策略

### 11.1 核心思想
不要每单从零生成整份攻略。  
应该优先复用数据库里已验证的“片段攻略”。

### 11.2 片段不是整份旧攻略
片段库里存的是：
- 路线片段
- 决策片段
- 体验片段
- 附录片段

并且存的不是最终大段成文，而是：
- 核心骨架
- 适用条件
- 关联实体
- 风险提示
- 可复用理由
- Plan B 模式

### 11.3 为什么必须这样做
- 更 grounded，减少幻觉
- 更省 token
- 更少人工复验
- 更容易把历史成功经验沉淀下来

---

## 12. 片段攻略库 Schema（最小可用版）

### 12.1 主表：guide_fragments
每条记录代表一个可复用攻略片段。

> ⚠️ 已实现版本见 `app/db/models/fragments.py`，以代码为准。

实际字段（对齐实现）：
- fragment_id (UUID)
- fragment_type（route / decision / experience / logistics / dining / tips）
- title, summary
- city_code, area_code
- theme_families (JSONB 数组，支持多值匹配)
- party_types (JSONB 数组)
- budget_levels (JSONB 数组)
- season_tags (JSONB 数组)
- day_index_hint (建议放在第几天)
- duration_slot (morning / afternoon / evening / full_day / half_day)
- body_skeleton (JSONB 骨架结构)
- body_prose (润色文案)
- body_html (渲染 HTML)
- quality_score (0-10)
- source_type (manual / ai_generated / distilled / imported)
- source_trip_id
- author, version
- status (draft / active / deprecated / archived)
- is_active
- created_at, updated_at, last_used_at

### 12.2 关联表：fragment_entities
存片段和实体之间的关系。

> ⚠️ 已实现版本见 `app/db/models/fragments.py`，以代码为准。

实际字段（对齐实现）：
- fragment_id
- entity_id (FK → entity_base)
- entity_role（primary / secondary / alternative / nearby）
- slot_order (排列顺序)
- is_replaceable (是否可被同类替换)

### 12.3 向量表：fragment_embeddings
用于做语义召回。

建议字段：
- fragment_id
- embedding_model
- embedding_vector
- embedding_text
- updated_at

### 12.4 兼容表：fragment_compatibility
用于判断片段和片段能不能拼。

建议字段：
- left_fragment_id
- right_fragment_id
- compatibility_score
- reason_codes
- hard_block

### 12.5 统计表：fragment_usage_stats
记录片段复用效果。

建议字段：
- fragment_id
- hit_count
- accepted_count
- edited_count
- rejected_count
- avg_user_rating
- preview_unlock_rate
- post_edit_rate
- refund_risk_score
- updated_at

### 12.6 回库队列：fragment_distillation_queue
用于从已交付攻略反向沉淀新片段。

建议字段：
- queue_id
- source_plan_id
- source_day_id
- candidate_fragment_type
- extract_status
- extracted_payload
- reviewer_note
- created_at
- updated_at

---

## 13. 片段库里到底存什么

### 应该存
- 路线骨架
- 核心高光
- 为什么这样排
- 适用人群
- 适用节奏
- 适用预算偏向
- 关键风险
- Plan B 方向

### 不应该存太死
- 精确到分钟的时间轴
- 实时价格
- 实时营业状态
- 某次订单特定航班
- 某次订单特定酒店房态

这些应该交给动态快照层补，不该固化在片段里。

---

## 14. 片段复用流程（正式版）

### Step 1：标准化画像
输入：
- 目的地
- 天数
- 同行人
- 偏好
- 预算偏向
- 熟悉度
- 多城 / 深玩
- 固定约束

输出：
- normalized_trip_profile

### Step 2：先做 metadata filter
先按结构化字段过滤：
- city
- theme_family
- trip_style
- suitable_for
- season
- familiarity
- budget_bias
- verified_status
- is_active

### Step 3：再做语义召回
在过滤后的集合里做 embedding / semantic retrieval，找更接近当前画像的片段。

### Step 4：硬规则过滤
把命中的片段丢进硬规则闸门：
- 时间冲突
- 固定事件冲突
- 同行体力不合
- 酒店依赖冲突
- 预算越界
- 季节性不匹配

### Step 5：软规则重排
通过硬过滤后，用软规则表 + weight packs 重新排序。

### Step 6：片段装配
按顺序拼：
1. 总纲片段
2. 每日主路线片段
3. 决策片段
4. 体验片段
5. 条件页片段
6. 附录片段

### Step 7：动态快照补槽
只补少量高时效信息：
- 酒店/餐厅营业状态
- 花期 / 天气 / 节庆窗口
- 重点体验可预约性

### Step 8：AI 少量解释
AI 只负责：
- 总设计思路
- 今日为什么这样排
- 个性化亮点解释
- 少量语气润色

### Step 9：质量门控
检查：
- 总纲完整
- 每天固定骨架完整
- 条件页触发合理
- 事实没过期
- 是否需要人工复核

---

## 15. 命中 / 不命中策略（必须分 4 档）

> ⚠️ 已实现版本见 `app/domains/planning/fragment_reuse.py` HitTier，以代码为准。

### A 档：强命中（final_score ≥ 0.7 且 quality ≥ 7）
条件：
- metadata + embedding + 硬规则 + 软规则全通过
- 质量分 ≥ 7

策略：
- 直接复用骨架
- 只做轻量替换和 AI 润色
- 默认不需要人工复核

### B 档：普通命中（final_score ≥ 0.4）
条件：
- 通过硬规则，综合评分中等

策略：
- 复用骨架
- 替换部分实体
- 重写少量解释
- 重新过硬规则与软规则

### C 档：弱命中（final_score < 0.4 但通过硬规则）
条件：
- 通过硬规则但综合评分低
- 无更好替代时仍可采用

策略：
- 复用骨架但大幅补充
- AI 补衔接说明
- 默认黄灯审核

### D 档：不命中（未通过硬规则）
条件：
- 硬规则不通过
- 或无任何候选片段

策略：
- gap 标记为 ai_generate
- 从实体池重新装配
- 生成后进入 review
- 好的结果后续蒸馏回片段库

---

## 16. 硬规则表 / 软规则表在这里怎么接

### 16.1 硬规则表
硬规则表不负责“谁更讨喜”，只负责：
- 过滤
- 拦截
- 质量门控

它在系统中的位置：
1. 片段召回后的第一道 gate
2. 装配完成后的 quality gate

### 16.2 软规则表
软规则表负责：
- 片段 rerank
- 免费样片更容易成交
- 完整攻略更少后悔
- 自助微调候选更容易被接受

软规则表建议至少维护这些维度：
- emotional_value
- shareability
- taste_signal
- localness
- uniqueness
- smoothness
- pacing_fit
- food_confidence
- photo_potential
- recovery_friendliness
- premium_feel
- preview_conversion_power
- confidence_of_choice
- redo_resistance

### 16.3 客群权重包
最小先覆盖：
- couple
- besties
- friends_small_group
- parents
- family_child
- first_time_fit
- repeat_fit
- deep_stay

### 16.4 阶段权重包
至少覆盖：
- preview_day1
- standard
- premium
- self_serve_tuning

---

