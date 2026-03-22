## 7. 三个 grader rubric 模板

我建议你先只做 3 个 grader，足够覆盖核心。

---

## Grader A：结构完整性 Rubric

### 目标
检查输出是不是“符合产品定义的攻略”，而不是只看文案好不好。

### 打分维度（0-5）
1. 是否有总纲
2. 是否有每日固定骨架
3. 条件页触发是否合理
4. 首日/末日是否匹配到离约束
5. 免费/标准/尊享边界是否清楚

### 判分模板
- 5 分：结构完整且无明显缺漏
- 4 分：基本完整，少量模块弱
- 3 分：结构存在，但缺 1 个核心模块
- 2 分：结构不稳定，多个模块缺失
- 1 分：明显不符合产品定义
- 0 分：输出失效或严重偏离

### grader prompt 模板
```text
你是“结构完整性审查员”。
请根据以下标准对输出的攻略结构打分（0-5）：
1. 是否有总纲
2. 是否有每日固定骨架
3. 条件页是否触发合理
4. 首日末日是否与约束一致
5. 产品边界是否正确

请输出：
- total_score
- per_dimension_scores
- pass_or_fail
- failure_reasons
- minimal_fix_suggestions
```

---

## Grader B：规划与约束质量 Rubric

### 目标
检查路线、节奏、预算、约束是否合理。

### 打分维度（0-5）
1. 顺路性
2. 节奏适配
3. 到离时间一致性
4. 固定事件处理合理性
5. 预算偏向一致性
6. 同行人与体力适配度
7. 是否明显少踩坑

### 判分模板
- 5 分：明显顺、稳、贴合约束
- 4 分：整体合理，少量可优化
- 3 分：局部存在不顺或冲突
- 2 分：约束处理较差，用户大概率会改
- 1 分：规划明显不可信
- 0 分：严重冲突，不可交付

### grader prompt 模板
```text
你是“路线规划质量审查员”。
请从以下维度对攻略打分（0-5）：
1. 顺路性
2. 节奏适配
3. 到离时间一致性
4. 固定事件处理
5. 预算偏向一致性
6. 同行人与体力适配度
7. 少踩坑程度

请输出：
- total_score
- per_dimension_scores
- risk_level
- likely_user_complaints
- minimal_fix_suggestions
```

---

## Grader C：用户感知价值 Rubric

### 目标
检查用户会不会觉得“值、懂我、愿意买/愿意推荐”。

### 打分维度（0-5）
1. 是否像为这个人写的
2. 是否有专业判断感
3. 是否有记忆点
4. 是否有情绪价值 / 分享感
5. 是否会让用户更敢下单
6. 是否会降低大改概率

### 判分模板
- 5 分：明显有“值”和“懂我”的感觉
- 4 分：大体有价值感，但记忆点不足
- 3 分：像合格模板，但不够打动人
- 2 分：太模板化，缺少理由和温度
- 1 分：用户很可能觉得不值钱
- 0 分：明显失败

### grader prompt 模板
```text
你是“用户感知价值审查员”。
请从以下维度给攻略打分（0-5）：
1. 是否像为这个人写的
2. 是否有专业判断感
3. 是否有记忆点
4. 是否有情绪价值/分享感
5. 是否会让用户更敢下单
6. 是否会降低大改概率

请输出：
- total_score
- per_dimension_scores
- strongest_points
- weakest_points
- user_likelihood_to_pay
- minimal_fix_suggestions
```

---

## 8. grader 运行方式（推荐）

### 最简单可用做法
每个 case 跑完后：
1. 保存生成结果
2. 保存 trace
3. 调 3 个 grader
4. 汇总成一份 `eval_run_report`

### 输出结构建议
```json
{
  "case_id": "case_01_tokyo_first_time_couple",
  "run_id": "...",
  "model_version": "...",
  "structure_score": 4.6,
  "planning_score": 4.1,
  "value_score": 4.4,
  "hard_failures": [],
  "soft_risks": ["evening density slightly high"],
  "used_fragments": ["frag_tokyo_west_day1", "frag_shibuya_evening"],
  "blocked_fragments": ["frag_asakusa_dense_loop"],
  "final_status": "pass"
}
```

---

## 9. 评测飞轮中还必须考虑的所有内容

下面这些是“不能漏”的完整清单。

### 9.1 数据与版本
每次运行至少记：
- profile_version
- fragment_catalog_version
- hard_rules_version
- soft_rules_version
- scorer_version
- planner_version
- renderer_version
- grader_version

### 9.2 trace
每次生成必须保留：
- 画像标准化结果
- 命中的片段
- 被硬规则挡掉的片段
- 软规则排序结果
- 装配后的日程骨架
- AI 润色前后差异
- 质量门控结果

### 9.3 失败归因标签
固定失败标签，不要临时乱写：
- profile_parse_error
- fragment_recall_error
- hard_rule_miss
- soft_rerank_error
- assembly_error
- copywriter_error
- rendering_error
- policy_boundary_error

### 9.4 回归门槛
建议最小发布门槛：
- 20 个首批 case 全跑
- structure 平均分 ≥ 4.2
- planning 平均分 ≥ 4.0
- value 平均分 ≥ 4.0
- 红色失败 = 0
- regression case 不退化

### 9.5 数据回写
线上真实单必须回写：
- 用户满意度
- 是否大改
- 哪些片段被换掉
- 哪些片段最容易推动付费
- 哪些片段最容易被投诉

### 9.6 用例扩张策略
首批 20 个后，扩成：
- 50 个稳定回归集
- 20 个复杂约束集
- 20 个高价值成交集
- 线上事故集持续补充

### 9.7 片段库联动
评测不能脱离片段库。
每个 case 最好写明：
- 应命中哪些 fragment
- 不应命中哪些 fragment
- 哪种 fallback 是可接受的

### 9.8 人工审核触发
即使 grader 通过，以下情况也建议人工抽样：
- 高客单
- 低命中率
- 冷门城市
- 多个固定约束冲突
- 熟客 + 一地深玩 + 高预算这类高价值单

### 9.9 管理端可视化
建议评测结果接到后台“生成追踪中心”：
- case 维度看分数
- run 维度看 trace
- fragment 维度看命中/被挡/被换
- 失败维度看分类统计

### 9.10 文档与制度
你必须把这件事正式写进项目文档：
- 完整攻略生成的任何重要改动，都必须过 eval
- 没有 eval，不算完成
- 线上翻车必须回写为 case

---

## 10. 先后顺序（实际落地推荐）

### P0：一周内必须完成
- 建 20 个 case 文件
- 建 3 个 rubric
- 能手动跑一轮
- 出 baseline 报告

### P1：接下来两周
- 接入自动化运行
- 接入 trace 存储
- 接入 fragment 命中记录
- 接入失败归因

### P2：再下一步
- 接入管理端可视化
- 加回归准入门槛
- 加线上事故自动沉淀 case
- 加 A/B 对比面板

---

## 11. 你要参与哪些环节（最简版）

你只需要亲自参与这 5 件事：

### 1）拍板首批 20 个 case 的方向
不是写文件，而是确认：
- 我们最想卖给谁
- 哪些单最值钱
- 哪些翻车最致命

### 2）拍板 grader 的成功标准
尤其是“什么才叫值”“什么才叫懂我”“什么才叫少踩坑”。
这一步只能你定，不要交给 code AI。

### 3）看每轮最重要的 5 个失败样本
你不需要看 100 个样本，只看：
- 高价值单失败
- 回归单退化
- 你直觉觉得“不对味”的样本

### 4）拍板 trade-off
比如：
- 是优先保顺路，还是优先保高光？
- 是优先保成交力，还是优先保保守稳妥？
- 熟客路线到底要小众到什么程度？

### 5）确认哪些失败样本要升级为长期 regression case
这一步关系到系统长期是否会越来越稳。

除此之外，
- case 编排
- grader 跑分
- trace 收集
- 回归脚本
- 仪表盘
都可以让 code AI 和 API AI 去做。

---

## 12. 最终一句话

**这套评测飞轮的目标不是“让 AI 更会写”，而是让“完整攻略生成”变成一个可测、可比、可复盘、可持续变强的产品系统。**
