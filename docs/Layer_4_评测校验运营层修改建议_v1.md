# Layer 4：评测、校验与运营层修改建议 v1

## 结论

当前 Layer 4 的方向是对的，但还不够完整。

它现在更像：
- 结构校验
- fallback
- 版本兼容
- 未来的 live risk / trace / eval

也就是以“前置检查”和“兼容兜底”为主。

真正要把 Layer 4 做成完整闭环，还需要补成四段：
1. 输入前校验
2. 生成后评审
3. 运营修正与灰度发布
4. 用户反馈回流

建议不要把 Layer 4 只理解为 quality gate，而要理解为：
**质量门 + 审核门 + 运营门 + 学习门。**

---

## 一、建议直接纳入 Layer 4 的新增模块

### 1. 表单输入级校验（前置于 Layer 2）
建议把 `validation/engine.py` 正式纳入 Layer 4。

原因：
- 它解决的是“用户输入能不能进入生成链路”
- 这不是 Layer 2 的实体资格过滤，而是更上游的表单质量控制
- 红灯不通过时，不应浪费生成资源

建议新增模块：
- input_validation_engine
- input_validation_result
- followup_question_router

建议状态：
- 红灯：阻断生成
- 黄灯：允许生成，但增加 explain / risk badge
- 绿灯：正常进入 Layer 2

---

### 2. 生成后 AI 评审（review_ops pipeline）
建议把 `review_ops/pipeline.py` 正式纳入 Layer 4，而不是继续做外围工具。

建议作为：
- post_generation_review_pipeline

建议角色：
- QA Checker
- User Proxy
- Ops Proxy
- Tuning Guard
- Final Judge

建议输出：
- hard_fail_issues[]
- soft_fail_issues[]
- user_proxy_highlights[]
- user_proxy_complaints[]
- ops_issues[]
- tunable_modules[]
- locked_modules[]
- final_verdict
- rewrite_needed

建议用途：
- hard_fail -> 阻断发布 / 强制 fallback
- complaints -> 回写 explain 的 expected_tradeoff
- tunable_modules -> 前端“换一个”开关
- highlights -> Layer 3 情绪价值文案增强

---

### 3. feedback/distillation 反馈回流
建议把 `feedback/distillation.py` 正式纳入 Layer 4，而不是继续只服务旧 fragment 复用。

建议拆成：
- feedback_ingestion
- feedback_scoring_update
- distillation_queue
- human_review_for_distilled_candidates

建议回流目标：
- entity_base_quality_adjustment
- activity_cluster_weight_adjustment
- city_circle_satisfaction_signal
- reusable_decision_pattern_candidates

建议注意：
- 不要直接把单次差评写死到主评分
- 需要时间窗口、样本数门槛、置信度衰减

---

### 4. route_matrix / swap_safety / offline_eval 的正式归位
这几个能力不建议漂在外围。

建议：
- `route_matrix`：仍属于 Layer 2 主链输入，但其缓存命中率、调用失败率、数据过期率，应纳入 Layer 4 监控
- `swap_safety`：适合放在 Layer 4 的 post-check，而不是主排程链核心中
- `offline_eval`：正式纳入 Layer 4，作为回归检测和切换前安全网

---

## 二、对当前任务表的具体修改意见

### 1. “trace 输出”不够，建议拆成两类
当前写的是：
- `generation_step_runs` 表：每阶段 `(result, trace)` 写入

建议拆成：

#### A. generation_decisions
存结构化决策结果
- circle_selection
- major_activity_plan
- hotel_strategy
- skeleton
- secondary_fill
- meal_fill
- report_payload_meta
- fallback_events
- review_results_summary

#### B. generation_step_runs
存执行日志与运行信息
- started_at
- finished_at
- duration_ms
- status
- input_hash
- output_hash
- error_code
- trace_text

也就是：
- decisions = 给业务和复盘看
- step_runs = 给工程和排障看

---

### 2. “实时风险监控”要提前定义触发与动作，不要只写模块名
建议把 `live_risk_monitor.py` 拆成明确规则：

#### 监控时间窗
- T-72h
- T-24h
- T-6h
- 当天清晨

#### 风险来源
- 天气预警
- 海况 / 船班
- 山路 / 徒步封闭
- 列车延误 / 停运
- 景点临时关闭

#### 动作
- 仅提示
- 自动挂 risk_badge
- 触发 fallback 推荐
- 强制重算 day_frame
- 推送用户确认

建议把这部分写成规则表，而不是写死在代码里。

---

### 3. grader 评测不要只写“待建”，要先定评分维度
建议先固定 grader 维度：
- structure_integrity
- factual_reliability
- feasibility
- preference_match
- pacing_quality
- diversity_balance
- emotional_value
- fallback_quality

并区分：
- 自动 grader
- 人工 grader
- 差异分析

---

### 4. 运营修正规则建议显式建模，不要散落在后台逻辑里
当前你写的是：
- cluster_locked / priority / risk_badge 等

建议正式建模为：
- operator_overrides
- operator_override_targets
- operator_override_reason_codes
- effective_time_range
- scope (entity / cluster / circle / plan)

这样后面：
- 节假日特殊规则
- 短期封闭
- 某活动暂时不推荐
- 某酒店强推 / 弱推

都可以统一处理。

---

### 5. 版本号管理不要只给 report_content.schema_version
建议最少拆成：
- profile_version
- circle_data_version
- entity_snapshot_version
- scorer_version
- planner_version
- report_schema_version
- page_template_version
- review_pipeline_version

因为后面出了问题，你要知道是：
- 数据变了
- 评分变了
- 规划器变了
- 渲染层变了
- 审核器变了

---

## 三、建议把 Layer 4 从“一个层”拆成四个子阶段

### L4-A 输入前校验
解决：用户输入是否能进生成链路

包含：
- validation_engine
- input completeness checks
- red/yellow/green decision
- followup question routing

### L4-B 生成后质量门
解决：生成结果结构上、事实上、执行上是否可发布

包含：
- quality_gate
- swap_safety post-check
- review_ops pipeline
- fallback trigger

### L4-C 运营与灰度层
解决：出了问题怎么控、怎么回滚、怎么人工干预

包含：
- operator overrides
- version pinning
- feature flags
- rollout / rollback
- live_risk_monitor

### L4-D 学习闭环层
解决：系统怎么越用越好

包含：
- feedback ingestion
- distillation
- offline eval
- grader comparison
- weight adjustment proposals

---

## 四、优先级建议

### P0（最先补）
1. validation/engine 接入 Layer 4 前置
2. generation_decisions + generation_step_runs 拆分
3. offline_eval 正式接入 shadow write 后流程
4. review_ops pipeline 接到 ReportPayloadV2 / 新 itinerary 结果

### P1
5. live_risk_monitor 规则化
6. operator_overrides 数据模型
7. grader 维度固定 + case 集合建设

### P2
8. feedback/distillation 扩展到 circle / cluster / entity
9. 版本管理全链路化
10. rollout / rollback / feature flag 成熟化

---

## 五、我对当前 Layer 4 的最终判断

当前表里列的 Layer 4，已经有了“校验层”的雏形，但还不是完整的运营闭环。

更准确地说，它现在完成了：
- 结构校验
- fallback
- 兼容

但还缺：
- 输入前校验
- 生成后评审
- 运营控制
- 用户反馈飞轮

所以我建议你把 Layer 4 的定义改成：

> 回答：结果对不对？出了问题怎么办？怎么安全发布？怎么持续变好？

这会比现在更完整。
