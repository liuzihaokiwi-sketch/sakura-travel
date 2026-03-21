"""
软规则评分子系统（Soft Rule Scoring Subsystem）

在现有的 system_score + context_score 两层评分之上，叠加第三层——
soft_rule_score，用于量化"什么叫讨喜、值得付费、值得分享"。

模块结构：
  - dimensions.py      : 12 个软规则维度定义 + 校验
  - weight_packs.py    : 客群/阶段权重包管理
  - estimators/        : 维度分计算器（AI/统计/人工）
  - pipeline.py        : 批量计算管线
  - preview_engine.py  : 免费预览选天引擎
  - swap_engine.py     : 自助微调候选排序引擎

评分公式（启用软规则后）：
  candidate_score = 0.45 × system_score
                  + 0.30 × context_score
                  + 0.25 × soft_rule_score
                  - risk_penalty
  final_entity_score = candidate_score + editorial_boost

退化模式（软规则分不存在时）：
  candidate_score = 0.60 × system_score
                  + 0.40 × context_score
                  - risk_penalty
"""
