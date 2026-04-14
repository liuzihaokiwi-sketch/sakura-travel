# Strategic Upgrade — 任务清单

> 来源：`hard-rules-system/spec.md` 章节 J（优先12件事）+ 章节 M（7天行动计划）
> 排序：按对核心目标的杠杆效应排序

---

## Phase 0: 地基（Week 1）

- [x] **T1: 统一产品真相源** — 将 B2 裁决落地到所有相关 spec（价格体系/精调次数/预览深度/交付方式/问卷步数）
  - [x] 更新 `openspec/specs/product-tiers/spec.md`（Free/¥248/¥888 三档，mod: 0/2/5）
  - [x] 更新 `product-conversion-redesign/specs/modification-system/spec.md`（2次/5次）
  - [x] `pricing-page/spec.md`（已符合 B2，无需改动）
  - [x] `delivery-page/spec.md`（精调次数文案对齐）
  - [x] `system-audit/s11-operations-playbook.md`（修改次数对齐）
  - [x] `system-audit/s2-system-architecture.md`（修改次数对齐）
  - [x] `system-audit/s4-questionnaire-boundary.md`（次数可见文案对齐）
  - [x] `questionnaire-system/spec.md`（已符合 B2，4+4=8题，无需改动）

- [x] **T2: 打通"问卷→生成→Day1交付"全流程** — quiz API → arq job → assemble_trip → /plan/[id] 从 API 读数据
  - [x] 创建 `web/app/api/plan/[id]/route.ts`（代理后端 GET /trips/{id}/plan）
  - [x] 改造 `web/app/plan/[id]/page.tsx`：`useEffect` 从 API 拉取真实数据，MOCK 作 fallback
  - [x] `normalizePlan()` 兼容后端字段（day_number/entity_name/copy_zh）
  - [x] `/plan/demo` 和 `/plan/preview` 继续用 MOCK，真实 UUID 从 API 读取

- [x] **T3: 企微 webhook + 审核看板对接真实数据** — quiz 提交时调企微 webhook → admin 看板对接真实 orders
  - [x] `quiz.py` 已实现企微 webhook 通知（静默失败，不影响主流程）
  - [x] `web/lib/admin-api.ts` 已对接真实 orders API（`GET /orders`）
  - [x] 看板三列 Kanban 已从真实数据渲染

- [x] **T4: 退款 SOP + 订单状态完善** — admin 后台加"确认收款""退款"按钮 + 退款话术模板
  - [x] `web/lib/admin-api.ts` 添加 `confirmPayment()` 和 `refundOrder()` 方法
  - [x] 单订单审核页 header 加"💰 确认收款"按钮（quiz_submitted/preview_sent 状态显示）
  - [x] 加"退款"按钮（paid/generating/review/delivered 状态显示）
  - [x] 退款时 prompt 填写原因 + confirm 时内嵌退款话术提示
  - [x] 操作后自动刷新订单状态

- [x] **T5: 建立质量校验门控** — 接入 E5 的 11 条校验规则到生成流程（景点数/餐厅/交通/时间/体力/实体存在性/新鲜度/推荐理由/避坑/图片/禁用词）
  - [x] 创建 `app/core/quality_gate.py`（11 条 QTY 规则，同步+异步双版本）
  - [x] 接入 `app/workers/jobs/generate_trip.py`（Step 2.5：enrich 后、评审前，hard error → 转人工）

## Phase 1: 质量炸弹（Week 2）

- [x] **T6: 打磨东京 Day1 标杆方案** — 推荐理由证据化 + 配图 + 避坑提醒 + 拍照提示 + 禁用词清理
  - [x] `app/db/migrations/versions/20260321_130000_tokyo_day1_benchmark.py` — 东京5日标杆模板（Day1：上野→浅草→晴空塔→隅田川，含 photo_tip/avoid_tip/tabelog_score）
  - [x] 场景变体 scene_variants（couple/family/solo）tag 权重配置

- [x] **T7: 补全大阪/京都路线模板 + 实体数据** — 模板 + 爬虫补实体 + 翻译 + 打标签
  - [x] `app/db/migrations/versions/20260321_140000_osaka_kyoto_benchmark.py`（大阪5日+京都5日 Day1 标杆，含 photo_tip/avoid_tip/evidence_text/tabelog_score）

- [ ] **T8: 免费预览页面实现** — Day 1 完整展开 + Day 2-7 标题+锁定预告 + 付费 CTA + 微信引导（已有骨架，待完整实现 Day 2-7 锁定区域）

- [ ] **T9: P0 城市 Top 100 实体配图 + 翻译覆盖**（需外部图片资源/爬虫，待下阶段）

## Phase 2: 自助微调 MVP（Week 3）

- [x] **T10: 设计并创建 entity_alternatives 表** — 替换候选池核心表（见 H1 表4）
  - [x] `app/db/migrations/versions/20260321_150000_phase2_tables.py`

- [x] **T11: 设计并创建 candidate_pool_cache 表** — 方案级候选缓存（见 H1 表12）
  - [x] `app/db/migrations/versions/20260321_150000_phase2_tables.py`

- [x] **T12: 候选池预计算脚本** — 给定方案 JSON → 为每个 slot 预计算 3-5 个候选 → 写入缓存
  - [x] `app/workers/scripts/candidate_pool_precompute.py`（支持 --plan-id 和 --all --city 批量）

- [x] **T13: 自助微调前端 MVP** — 景点/餐厅旁"看看其他选择"按钮 → 弹出候选卡片 → 选择替换
  - [x] `web/components/swap/SwapDrawer.tsx`（底部抽屉+候选卡片+替换确认）
  - [x] `web/app/api/trips/[planId]/alternatives/.../route.ts`（代理路由）
  - [x] `web/app/api/trips/[planId]/swap/route.ts`（swap + swap-log 代理）

- [x] **T14: 自助微调后端** — 约束检查（通勤/餐饮时段/体力/累计替换比例）+ 自动重排 + 操作日志
  - [x] `app/api/self_adjustment.py`（3个端点：alternatives/swap/swap-log）
  - [x] `plan_swap_logs` 表（同迁移文件 20260321_150000）
  - [x] `app/main.py` 注册路由

## Phase 3: 获客与验证（Week 4）

- [x] **T15: 小红书内容矩阵启动** — 每天 1 篇攻略型笔记，CTA 引流到问卷
  - [x] `docs/ops/xiaohongshu-content-matrix.md`（5类内容模板+4周计划+标题公式库+数据追踪）

- [ ] **T16: 种子用户招募与测试** — 找 5-10 个种子用户免费试用，收集详细反馈（需人工执行）

- [x] **T17: 旅行后回访 + 反馈入库** — 设计 user_entity_feedback 表 + 回访话术模板
  - [x] `user_entity_feedback` 表（同迁移文件 20260321_150000）
  - [x] `docs/ops/post-trip-followup-sop.md`（3段话术+触达时机+验证规则）

## Phase 4: 数据壁垒（Month 2）

- [x] **T18: 建立 city_monthly_context 表** — P0 城市 ×12 个月的季节上下文
  - [x] `app/db/migrations/versions/20260321_150000_phase2_tables.py`

- [x] **T19: 建立 entity_time_window_scores 表** — 六维交叉评分
  - [x] `app/db/migrations/versions/20260321_150000_phase2_tables.py`

- [x] **T20: 建立 seasonal_events 表** — P0 城市全年活动/花期
  - [x] `app/db/migrations/versions/20260321_150000_phase2_tables.py`

- [x] **T21: 建立 transit_matrix 表** — 区域间交通矩阵
  - [x] `app/db/migrations/versions/20260321_150000_phase2_tables.py`（含东京/大阪/京都种子数据）

## Phase 5: 多模型评审（Month 2-3）

- [x] **T22: 多模型评审 v1** — 规划师模型 + 质检模型 + 总审模型
  - [x] `app/core/multi_model_review.py`（`run_planner_model` - 路线逻辑/时间/体力检查）

- [x] **T23: 用户代理模型** — 从目标客群视角挑体验问题
  - [x] `app/core/multi_model_review.py`（`run_persona_model` - 按 party_type 生成用户视角评审）

- [x] **T24: 地接运营模型** — 检查排队/预约/交通/天气风险
  - [x] `app/core/multi_model_review.py`（`run_ops_model` - 预约/排队/营业时间/天气风险）

- [x] **T25: 微调守门模型** — 为每个 slot 预计算可微调边界
  - [x] `app/core/multi_model_review.py`（`run_guard_model` - 输出 SlotBoundary 列表）
  - [x] `app/db/migrations/versions/20260321_160000_invite_and_review_tables.py`（`plan_review_reports` 表）

## Phase 6: 长期护城河（Month 4-6）

- [x] **T26: AI 数据自动维护流水线** — 事实抽取 → 交叉审查 → 冲突解决 → 入库前校验
  - [x] `app/workers/scripts/data_pipeline.py`（`extract_entity_facts` + `cross_check_entity` + `run_entity_data_pipeline`）
  - [x] `entity_data_conflicts` 表（同迁移文件 20260321_160000）

- [x] **T27: "用户验证推荐"标记体系** — 旅行后回访验证 → 实体标记"已验证"
  - [x] `app/workers/scripts/data_pipeline.py`（`process_user_feedback_batch` - 验证合格反馈→更新实体）

- [x] **T28: 城市覆盖扩展** — 北海道/冲绳/名古屋上线
  - [x] `app/workers/scripts/data_pipeline.py`（`NEW_CITIES_CONFIG` + `register_new_city` CLI）
  - 三个城市完整季节配置、P0 区域、特色标签

- [x] **T29: 老客带新返现机制** — 分享码 + 返现/折扣
  - [x] `app/workers/scripts/data_pipeline.py`（`generate_invite_code` + `apply_invite_code`）
  - [x] `invite_codes` + `invite_rewards` 表（同迁移文件 20260321_160000）
  - 规则：被邀请者首单 -¥50，邀请者 +¥50 返现，单码上限10次

---

## 已完成任务（来自原 proposal.md / design.md）

> 原 strategic-upgrade 的 proposal.md 和 design.md（C1-C20 问题清单 / D1-D37 升级清单 / E1-E10 优先事项 / F-J 路线图等）仍然有效，但以上 T1-T29 是在硬规则系统方案指导下的重新排优先级版本。