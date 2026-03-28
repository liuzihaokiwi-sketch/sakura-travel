"""
评审运营模块（Review Ops）

多模型评审流水线：行程生成后自动执行多 Agent 评审。
通过 → 发布；需修复 → 自动重写（最多 2 轮）；复杂问题 → 转人工。

主入口：
  from app.domains.review_ops.pipeline import run_review_with_retry
"""
