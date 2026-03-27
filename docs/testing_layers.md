# Testing Layers: L2/L3 Blocker 与 Legacy Compatibility

## 文档定位

本文档只定义测试分层、CI 阻塞语义与 legacy 兼容基线。

它不重新定义 L2/L3 业务主链，也不把 compatibility 测试混写成架构收口证明。

## 边界对齐

### 已废弃前提

当前测试口径不再建立在以下旧前提上：

- 旧长链路 e2e/PDF 回归可以单独充当新链主证明
- Japan-only 假设仍可作为默认测试边界
- 只要结果能导出，就可以视为 L3 blocker 通过

### 新边界下发生变化的层

本次测试口径变化涉及：

- CI 层：从“phase2 + legacy”混合口径，改成 `L2 blocker / L3 blocker / legacy compatibility` 三层
- 验收层：把 blocker 通过与 compatibility 保留显式分开
- 交付层：L3 blocker 以 handbook delivery 主支路为准，不再以旧 report/PDF 路径代替

### 仍然有效的历史缺口

以下历史缺口在测试层面仍然有效：

- old decision chain and new decision chain coexist
- old rendering chain and new rendering chain coexist
- truth sources remain distributed
- quality and operations remain distributed

### 为什么当前阶段先做分层收口，而不是继续堆功能测试

当前风险不是“某个单点功能还没测”，而是“不同测试在证明不同东西，却被汇报成同一种通过”。

如果不先冻结测试分层，团队很容易继续把以下状态混在一起：

- 新链 blocker 通过
- 兼容旧链仍能跑通
- 老导出链还能产物
- report/day-first 展示还没退场

所以当前阶段先把 blocker 与 compatibility 的边界写清楚，再扩展更多测试。

## 三层测试定义

### `l2_contract_blocker`

定位：

- contract-first 的 L2 主阻塞层
- 证明 Layer 2 主 contract、主字段、主约束与主证据链没有退化

它不证明：

- legacy 入口已删除
- 所有输入字段都已完全收口
- L3 handbook delivery 已统一完成

### `l3_handbook_delivery_blocker`

定位：

- handbook delivery acceptance 的 L3 主阻塞层
- 证明 `page_models -> page_overrides -> shared_export_contract` 这条主交付支路可被验收

它不证明：

- 所有前端页面都已 page-model-first
- 所有导出入口都已完全脱离 legacy report 语义
- 整个仓库的渲染链已经统一完成

### `legacy_compatibility`

定位：

- 旧链路、旧 schema、旧 e2e、旧 PDF 的兼容性基线
- 默认是可见但非阻塞的兼容层

它证明的是：

- 旧路径还没有完全失效
- 当前兼容面有没有意外塌掉

它不证明的是：

- 新链 blocker 已通过
- 新架构收口已经完成

### 兼容别名

- `phase2_acceptance` 仍保留为历史别名
- 当前应将其理解为映射到 `l2_contract_blocker` 的历史命名，而不是单独的架构层

## 团队执行入口

### 默认入口

`python scripts/ci/run_dual_track_tests.py`

默认顺序：

1. `l2_contract_blocker`
2. `l3_handbook_delivery_blocker`
3. `legacy_compatibility`

### 子入口

- `python scripts/ci/run_dual_track_tests.py --l2-only`
  - 只运行 L2 blocker
- `python scripts/ci/run_dual_track_tests.py --l3-only`
  - 只运行 L3 blocker
- `python scripts/ci/run_dual_track_tests.py --blockers-only`
  - 只运行 L2/L3 两层 blocker
- `python scripts/ci/run_dual_track_tests.py --legacy-only`
  - 只运行 legacy compatibility
- `python scripts/ci/run_dual_track_tests.py --strict-legacy`
  - 在全量流程下把 legacy 失败升级成阻塞

## 自动分类规则

实现位置：`tests/conftest.py`

### 1. `l2_contract_blocker`

包括：

- `tests/test_phase2_*.py`
- `tests/e2e/test_full_pipeline.py` 中以 `test_phase2_` 开头的节点

### 2. `l3_handbook_delivery_blocker`

包括：

- `tests/test_layer2_delivery_handoff.py`
- `tests/test_shared_export_contract.py`
- `tests/test_handbook_delivery_acceptance.py`
- `tests/test_page_editing_workflow.py`
- `tests/test_page_edit_api_workflow.py`

### 3. `legacy_compatibility`

包括：

- `tests/e2e/test_full_pipeline.py` 中非 `test_phase2_` 节点
- `tests/test_regression_submission_normalize_constraints_ranking.py`
- `tests/test_pdf_watermark.py`

## CI 映射

`.github/workflows/ci.yml` 当前应表达为：

1. L2 contract-first blocker：阻塞
2. L3 handbook delivery blocker：阻塞
3. legacy compatibility baseline：默认非阻塞，可 `continue-on-error: true`

失败语义：

- L2 或 L3 任一失败：PR 合并阻塞
- legacy 失败：默认只做兼容性提醒，不自动等同 blocker 红灯

## Nightly Legacy Monitoring

### 最小保留方案

独立工作流：`.github/workflows/legacy-compat-nightly.yml`

执行入口：

- 定时 `cron` 每日运行
- 支持 `workflow_dispatch`
- 只执行 `python scripts/ci/run_dual_track_tests.py --legacy-only`

### 留痕产物

- `ci_logs/legacy-nightly/junit.xml`
- `ci_logs/legacy-nightly/pytest.log`
- `ci_logs/legacy-nightly/summary.md`
- `ci_logs/legacy-nightly/failed_tests.txt`

同时把摘要同步写入 `GITHUB_STEP_SUMMARY`。

### 口径说明

- nightly legacy 失败不阻塞日常 PR 合并
- nightly 自身应继续标红，作为持续可见的兼容性监控信号

## 本轮仍未覆盖的范围

以下内容不在本轮测试分层收口内：

- 没有把全部历史测试一次性重分层
- 暂未建立 marker 维度趋势报表或自动开 issue
- 暂未把 legacy 失败做自动分级告警策略
- 暂未把所有 report-first 页面改造成 L3 blocker 范围

## 最终口径

当前建议团队统一采用以下解释：

- `blocker green` 只代表主收口阻塞层通过
- `legacy compatibility green` 只代表兼容面当前未塌
- 两者不能互相替代
- legacy 测试仍有价值，但不再作为 L2/L3 主证明

