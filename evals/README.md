# 评测飞轮目录说明
# 
# evals/
# ├── cases/          ← 评测用例 YAML（按类型分目录）
# │   ├── standard/   ← 标准用例（6条）
# │   ├── high_value/ ← 高价值用例（4条）
# │   ├── constrained/← 复杂约束用例（4条）
# │   ├── edge/       ← 边界用例（3条）
# │   └── regression/ ← 回归用例（3条，已发现bug后固化）
# ├── rubrics/        ← 评分维度定义 YAML
# ├── runs/           ← 每次评测运行结果 JSON（gitignore大文件）
# ├── failure_analysis/ ← 失败归因报告
# └── graders/        ← grader 模块（在 app/evals/graders/ 中实现）
#
# 使用方式：
#   python -m app.evals.cli run --suite regression
#   python -m app.evals.cli run --case C001
#   python -m app.evals.cli compare run-A run-B

## Contract V2 Matrix (offline_eval)

For contract-native coverage, use `app.domains.evaluation.offline_eval` with
`data/eval/eval_cases_v2_contract.json`.

`run_eval(...)` now returns `EvalReport.matrix_summary` with:

- `city_circle`: covered/missing city circles and per-circle smoke/strong counts
- `scenario_type`: covered/missing key scenario types
- `contract_semantics`: covered/missing key contract semantics
- `assertion_levels`: smoke vs strong case split
