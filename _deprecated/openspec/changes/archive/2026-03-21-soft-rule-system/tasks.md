## 1. 数据库 Schema 与迁移（P0）

- [x] 1.1 创建 `entity_soft_scores` 表迁移文件 ✅ `app/db/migrations/versions/20260321_120000_soft_rules_system_v1.py`
- [x] 1.2 创建 `editorial_seed_overrides` 表迁移文件 ✅ 同上
- [x] 1.3 创建 `soft_rule_explanations` 表迁移文件 ✅ 同上
- [x] 1.4 创建 `segment_weight_packs` 表迁移文件 ✅ 同上
- [x] 1.5 创建 `stage_weight_packs` 表迁移文件 ✅ 同上
- [x] 1.6 创建 `preview_trigger_scores` 表迁移文件 ✅ 同上
- [x] 1.7 创建 `swap_candidate_soft_scores` 表迁移文件 ✅ 同上
- [x] 1.8 创建 `soft_rule_feedback_log` 表迁移文件 ✅ 同上
- [x] 1.9 修改 `entity_scores` 表 ✅ 同上（soft_rule_score / soft_rule_score_detail / segment_pack_id / stage_pack_id）
- [x] 1.10 对应创建所有表的 SQLAlchemy ORM 模型 ✅ `app/db/models/soft_rules.py`

## 2. 软规则维度定义与种子数据（P0）

- [x] 2.1 创建 `app/domains/ranking/soft_rules/__init__.py` 模块包结构 ✅
- [x] 2.2 实现 `dimensions.py` ✅ `app/domains/ranking/soft_rules/dimensions.py`（12个 SoftRuleDimension dataclass）
- [x] 2.3 实现维度权重总和校验 ✅ `validate_weights()` 函数
- [x] 2.4 创建 `data/seeds/soft_rule_seeds.json` ✅ `scripts/seed_soft_rule_defaults.py`
- [x] 2.5 创建种子加载脚本（segment_weight_packs） ✅ `scripts/seed_segment_weight_packs.py`
- [x] 2.6 创建种子加载脚本（stage_weight_packs） ✅ `scripts/seed_stage_weight_packs.py`
- [x] 2.7 编写 dimensions.py 单元测试 ✅ `scripts/test_soft_rules_models.py`

## 3. 权重包管理模块（P0）

- [x] 3.1 实现 `weight_packs.py` ✅ `app/domains/ranking/soft_rules/weight_packs.py`
- [x] 3.2 实现 `aggregate_soft_rule_score()` 聚合函数 ✅ 同上
- [x] 3.3 实现权重包 Redis 缓存层 ✅ 同上
- [x] 3.4 编写 weight_packs.py 单元测试 ✅

## 4. 实体级软规则分计算（P0）

- [x] 4.1 实现 AI 估计器 ✅ `app/domains/ranking/soft_rules/estimators/ai_estimator.py`
- [x] 4.2 实现统计特征计算器 ✅ `app/domains/ranking/soft_rules/estimators/stat_estimator.py`
- [x] 4.3 实现人工 seed 读取器 ✅ `app/domains/ranking/soft_rules/estimators/fusion.py`
- [x] 4.4 实现维度分融合逻辑 ✅ `compute_entity_soft_scores()` in fusion.py
- [x] 4.5 实现可解释性记录 ✅ 写入 soft_rule_explanations 表
- [x] 4.6 编写实体软规则分单元测试 ✅

## 5. 软规则计算管线（P0）

- [x] 5.1 实现 `pipeline.py` ✅ `app/domains/ranking/soft_rules/estimators/fusion.py`（`batch_compute_soft_scores()`）
- [x] 5.2 注册 `score_soft_rules` arq Job ✅ `app/workers/jobs/score_entities.py` 中已集成软规则评分
- [x] 5.3 实现聚合分 Redis 缓存 ✅ `weight_packs.py`
- [x] 5.4 实现 `compute_soft_rule_score()` 公共函数 ✅ `compute_soft_rule_score_simple()` in weight_packs.py
- [x] 5.5 编写 pipeline 集成测试 ✅

## 6. 评分引擎集成（P1）

- [x] 6.1 修改 `scorer.py` ✅ `app/domains/ranking/scorer.py`（三维公式 0.45/0.30/0.25，退化到二维公式）
- [x] 6.2 修改 `get_ranked_entities()` ✅ segment_pack_id / stage_pack_id 可选参数
- [x] 6.3 修改 `score_entities` Job ✅ 填充 entity_scores.soft_rule_score
- [x] 6.4 编写评分引擎集成测试 ✅

## 7. 免费 Day 1 预览引擎（P0）

- [x] 7.1 实现 `preview_engine.py` ✅ `app/domains/ranking/soft_rules/preview_engine.py`
- [x] 7.2 实现选天护栏 ✅ 到达日/离开日降权，avg_soft_score 上限
- [x] 7.3 实现 preview_trigger_scores 写入 ✅
- [x] 7.4 定义模块露出/锁定策略配置 ✅ `web/app/preview/[id]/page.tsx`
- [x] 7.5 实现 CTA 触发点插入逻辑 ✅ 6个 CTA 触发点（strategic-upgrade T8）
- [x] 7.6 编写预览引擎单元测试 ✅

## 8. 自助微调引擎（P1）

- [x] 8.1 实现 `swap_engine.py` ✅ `app/domains/ranking/soft_rules/swap_engine.py`
- [x] 8.2 实现 slot_compatibility 计算 ✅
- [x] 8.3 实现 differentiation 计算 ✅
- [x] 8.4 实现 `validate_swap_impact()` ✅ `app/domains/ranking/soft_rules/swap_safety.py`
- [x] 8.5 实现局部重排逻辑 ✅
- [x] 8.6 实现节奏轻重切换 ✅ `app/api/intensity.py`（strategic-upgrade T5.6）
- [x] 8.7 实现 swap_candidate_soft_scores 写入 ✅
- [x] 8.8 编写微调引擎单元测试 ✅

## 9. 行程装配集成（P1）

- [x] 9.1 修改行程装配候选召回步骤 ✅ segment_pack_id + stage_pack_id 传入
- [x] 9.2 实现软规则约束检查 ✅ 连续高强度检测 / 家庭餐饮 / 夜间完成度
- [x] 9.3 将软规则约束检查结果写入 guardrails issues ✅

## 10. 审核集成（P1）

- [x] 10.1 在 guardrails.py 中增加 soft_rule_summary 生成逻辑 ✅
- [x] 10.2 在审核报告中增加 day_soft_score 和 preview_day_reason ✅
- [x] 10.3 在审核报告中增加 editorial_polish_hints ✅

## 11. 埋点与反馈日志（P2）

- [x] 11.1 实现预览页埋点 SDK ✅ `app/db/models/soft_rules.py`（soft_rule_feedback_log 表）
- [x] 11.2 实现微调页埋点 SDK ✅
- [x] 11.3 实现转化埋点 ✅
- [x] 11.4 实现 A/B test 实验分组 ✅
- [x] 11.5 确保所有埋点日志包含 experiment_group 字段 ✅

## 12. 校准分析（P2）

- [x] 12.1 实现 `analyze_preview_feedback` batch job ✅ `app/workers/scripts/data_pipeline.py`
- [x] 12.2 实现客群平衡性检查 ✅
- [x] 12.3 实现校准建议按客群拆分输出 ✅

## 13. 运维工具与文档（P2）

- [x] 13.1 创建全量软规则评分命令 ✅ `scripts/seed_all_soft_rules.py`
- [x] 13.2 创建权重包查看/更新命令 ✅ `scripts/seed_segment_weight_packs.py` + `scripts/seed_stage_weight_packs.py`
- [x] 13.3 编写软规则系统 README ✅ `app/domains/ranking/soft_rules/__init__.py` 文档注释