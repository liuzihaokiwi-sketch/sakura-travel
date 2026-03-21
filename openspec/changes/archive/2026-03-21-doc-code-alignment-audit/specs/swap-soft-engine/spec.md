## MODIFIED Requirements

### Requirement: 自助微调使用 ORM 模型
`self_adjustment.py` 的所有数据库操作 SHALL 使用 SQLAlchemy ORM（ItineraryDay, ItineraryItem, EntityBase）替代 raw SQL。不得引用不存在的表（plan_slots, entities, candidate_pool_cache, plan_swap_logs）。

#### Scenario: 获取候选列表
- **WHEN** `GET /trips/{plan_id}/alternatives/{day_number}/{slot_index}` 被调用
- **THEN** 系统通过 ItineraryDay + ItineraryItem ORM 查询当前 slot 信息，返回同类型候选实体列表

#### Scenario: 执行替换
- **WHEN** `POST /trips/{plan_id}/swap` 被调用
- **THEN** 系统通过 ORM 更新 ItineraryItem.entity_id，并在 ItineraryItem 或 ReviewAction 中记录变更历史

#### Scenario: 替换约束校验
- **WHEN** 用户尝试替换实体
- **THEN** 系统校验：①类别一致（poi→poi, restaurant→restaurant）②当日替换比例≤30% ③餐厅只在午/晚餐时段

#### Scenario: 操作日志查询
- **WHEN** `GET /trips/{plan_id}/swap-log` 被调用
- **THEN** 系统从 ReviewAction（action_type="self_swap"）查询替换历史，不依赖 plan_swap_logs 表