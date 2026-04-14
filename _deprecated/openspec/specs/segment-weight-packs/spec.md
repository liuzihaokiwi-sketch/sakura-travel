## ADDED Requirements

### Requirement: 客群权重包定义

系统 SHALL 支持 7 个客群权重包（segment weight packs），每个权重包定义该客群最在意和不在意的软规则维度权重分配。权重包 SHALL 存储在 segment_weight_packs 表中，支持运行时动态调整。

| 客群 ID | 中文名 | 核心目标 |
|---------|--------|---------|
| couple | 情侣 | 浪漫氛围、出片、记忆点 |
| besties | 闺蜜好友 | 分享感、出片、轻松 |
| friends_small_group | 朋友结伴 | 丰富体验、高效、夜间 |
| parents | 带父母 | 舒适、少折腾、餐饮确定 |
| family_child | 带孩子 | 安全、恢复友好、餐饮 |
| first_time_fit | 首次赴日双人自由行 | 确定感、顺滑、专业感 |
| repeat_fit | 二刷日本 | 当地感、记忆点、新鲜 |

每个权重包 SHALL 包含：
- pack_id: VARCHAR 唯一标识
- name_cn: 中文名
- description: 核心目标描述
- weights: JSONB — 12 个维度的权重值
- top_dimensions: 最在意的 6-8 个维度列表
- low_dimensions: 不太在意的维度列表
- day1_trigger: 对免费 Day 1 最敏感的触发点描述
- repurchase_trigger: 对复购最敏感的触发点描述
- tuning_sensitivity: 对自助微调最敏感的模块列表
- version: INT 版本号
- updated_at: TIMESTAMP

#### Scenario: 加载情侣权重包

- **WHEN** 调用 `get_segment_weight_pack("couple")`
- **THEN** 返回 couple 权重包，weights 中 emotional_value / shareability / memory_point 权重较高，smoothness / recovery_friendliness 权重较低

#### Scenario: 加载所有权重包

- **WHEN** 调用 `get_all_segment_weight_packs()`
- **THEN** 返回 7 个权重包，每个 weights 的 12 维度权重之和在 0.99-1.01 范围内

#### Scenario: 动态更新权重包

- **WHEN** 调用 `update_segment_weight_pack("couple", new_weights)` 且 new_weights 权重总和为 1.0
- **THEN** couple 权重包 weights 被更新，version +1，updated_at 刷新

### Requirement: 客群权重包 v1 种子值

系统 SHALL 提供以下 v1 默认种子权重值：

**couple（情侣）**：
- 高权重：emotional_value=0.16, shareability=0.14, memory_point=0.13, relaxation_feel=0.10
- 中权重：localness=0.09, food_certainty=0.08, professional_judgement_feel=0.07, night_completion=0.08
- 低权重：smoothness=0.06, recovery_friendliness=0.04, weather_resilience_soft=0.03, preview_conversion_power=0.02
- Day 1 触发点：有明确的约会感氛围场景 + 出片点
- 复购触发点：记忆点够独特、不是"谁都能找到的攻略"

**besties（闺蜜好友）**：
- 高权重：shareability=0.16, emotional_value=0.13, relaxation_feel=0.12, memory_point=0.10
- 中权重：food_certainty=0.09, localness=0.08, night_completion=0.09, smoothness=0.07
- 低权重：recovery_friendliness=0.05, weather_resilience_soft=0.04, professional_judgement_feel=0.04, preview_conversion_power=0.03
- Day 1 触发点：高出片回报 + 闺蜜合照场景
- 复购触发点：内容值得在朋友圈晒

**parents（带父母）**：
- 高权重：smoothness=0.15, recovery_friendliness=0.13, food_certainty=0.13, relaxation_feel=0.12
- 中权重：emotional_value=0.08, professional_judgement_feel=0.09, weather_resilience_soft=0.08, localness=0.06
- 低权重：shareability=0.05, memory_point=0.05, night_completion=0.04, preview_conversion_power=0.02
- Day 1 触发点：行程节奏松弛 + 餐厅确定 + 交通方便
- 复购触发点：父母体验好没有不开心

**family_child（带孩子）**：
- 高权重：smoothness=0.14, recovery_friendliness=0.14, food_certainty=0.12, weather_resilience_soft=0.10
- 中权重：emotional_value=0.08, relaxation_feel=0.10, memory_point=0.07, professional_judgement_feel=0.07
- 低权重：shareability=0.06, localness=0.05, night_completion=0.04, preview_conversion_power=0.03
- Day 1 触发点：明确的亲子友好内容 + 雨天备案
- 复购触发点：全家体验顺畅无负担

**first_time_fit（首次赴日双人自由行）**：
- 高权重：smoothness=0.14, professional_judgement_feel=0.13, food_certainty=0.11, preview_conversion_power=0.10
- 中权重：emotional_value=0.09, relaxation_feel=0.09, memory_point=0.08, shareability=0.08
- 低权重：localness=0.06, night_completion=0.05, recovery_friendliness=0.04, weather_resilience_soft=0.03
- Day 1 触发点：确定感 + "按这个走不会出错"
- 复购触发点：第一次就很顺、建立信任

**friends_small_group（朋友结伴）**：
- 高权重：memory_point=0.13, night_completion=0.12, emotional_value=0.11, shareability=0.11
- 中权重：food_certainty=0.09, localness=0.09, smoothness=0.08, relaxation_feel=0.08
- 低权重：recovery_friendliness=0.06, weather_resilience_soft=0.05, professional_judgement_feel=0.05, preview_conversion_power=0.03
- Day 1 触发点：有明确的"高光时刻" + 夜间活动
- 复购触发点：朋友们都觉得好玩

**repeat_fit（二刷日本）**：
- 高权重：localness=0.16, memory_point=0.14, emotional_value=0.12, food_certainty=0.10
- 中权重：relaxation_feel=0.09, shareability=0.08, professional_judgement_feel=0.08, night_completion=0.07
- 低权重：smoothness=0.06, recovery_friendliness=0.04, weather_resilience_soft=0.03, preview_conversion_power=0.03
- Day 1 触发点："这些地方我自己找不到" 的惊喜感
- 复购触发点：确实推荐了非主流好去处

#### Scenario: 种子数据加载

- **WHEN** 系统首次初始化或运行 seed 脚本
- **THEN** 7 个客群权重包被写入 segment_weight_packs 表，所有 weights 总和均为 1.00

#### Scenario: 种子值可被覆盖

- **WHEN** 管理员通过 API 更新 couple 的 emotional_value 权重从 0.16 改为 0.18
- **THEN** couple 权重包更新成功，version 递增，其他维度权重不受影响（但需管理员确保总和为 1.00）

### Requirement: 客群权重包数据表

系统 SHALL 创建 segment_weight_packs 表：

| 字段 | 类型 | 说明 |
|------|------|------|
| pack_id | VARCHAR(50) PK | 客群标识 |
| name_cn | VARCHAR(100) | 中文名 |
| description | TEXT | 核心目标描述 |
| weights | JSONB NOT NULL | 12 维度权重 |
| top_dimensions | JSONB | 最在意的维度列表 |
| low_dimensions | JSONB | 不太在意的维度列表 |
| day1_trigger | TEXT | Day 1 敏感触发点 |
| repurchase_trigger | TEXT | 复购触发点 |
| tuning_sensitivity | JSONB | 微调敏感模块 |
| version | INT DEFAULT 1 | 版本号 |
| updated_at | TIMESTAMP | 更新时间 |

#### Scenario: 表创建

- **WHEN** 运行数据库迁移
- **THEN** segment_weight_packs 表被创建，pack_id 为主键
