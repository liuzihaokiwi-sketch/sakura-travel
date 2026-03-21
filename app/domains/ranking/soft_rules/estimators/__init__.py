"""
软规则维度估计器包（Soft Rule Estimators）

三种估计器按优先级：
  1. manual — 人工 seed / 编辑覆盖（最高优先级）
  2. stat   — 从实体属性统计计算
  3. ai     — GPT-4o-mini 批量评估（最低优先级，但覆盖面最广）

融合逻辑在 fusion.py 中实现。
"""
