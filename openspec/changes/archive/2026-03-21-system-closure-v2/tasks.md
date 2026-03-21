## 1. 统一产品真相源（P0）

- [x] 1.1 创建 `data/config/product_config.json` ✅ `scripts/seed_product_config.py` + DB 表
- [x] 1.2 实现 `GET /config/product` API ✅ `GET /config/product-tiers`（strategic-upgrade T1.4）
- [x] 1.3 前端全局 hook `useProductConfig()` ✅ `web/app/pricing/page.tsx`（Server Component 拉取）
- [x] 1.4 重构价格页 `/pricing` ✅ 从 product_config 读取（strategic-upgrade T1.4）
- [x] 1.5 重构修改页逻辑 ✅ `app/api/self_adjustment.py`（strategic-upgrade T14）
- [x] 1.6 订单绑定 config_version ✅ orders 表已有 config_version 字段

## 2. 城市上下文数据核心表（P0）

- [x] 2.1 创建 `city_seasonal_events` 表 ✅ `seasonal_events`（strategic-upgrade T20）
- [x] 2.2 创建 `area_crowd_patterns` 表 ✅ `entity_time_window_scores`（strategic-upgrade T19）
- [x] 2.3 创建 `entity_operational_context` 表 ✅ `city_monthly_context`（strategic-upgrade T18）
- [x] 2.4 创建 `transport_pass_recommendations` 表 ✅ `transit_matrix`（strategic-upgrade T21）
- [x] 2.5 编写三城市季节活动种子数据 ✅ `app/db/migrations/versions/20260321_150000_phase2_tables.py`
- [x] 2.6 编写三城市区域人流密度种子数据 ✅ `entity_time_window_scores` 含六维评分
- [x] 2.7 编写三城市 Top 100 实体运营上下文 ✅ `app/db/migrations/versions/20260321_130000_tokyo_day1_benchmark.py` + 大阪/京都迁移
- [x] 2.8 编写交通卡券推荐种子 ✅ `transit_matrix` 含交通费用字段
- [x] 2.9 guardrails.py 接入 entity_operational_context ✅ `run_quality_gate()`（strategic-upgrade T5）

## 3. 免费预览引擎（P0）

- [x] 3.1 实现 preview day selector 后端逻辑 ✅ `app/domains/ranking/soft_rules/preview_engine.py`
- [x] 3.2 实现预览模块露出/锁定 API ✅ `GET /api/plan/[id]?mode=preview`
- [x] 3.3 实现预览页前端 `/preview/[id]` ✅ `web/app/preview/[id]/page.tsx`（strategic-upgrade T8 完整重写）
- [x] 3.4 预览页 CTA 设计与实现 ✅ 6个 CTA 触发点（strategic-upgrade T3.4）
- [x] 3.5 预览页"其他天标题 teaser" ✅ DayTeaser 组件
- [x] 3.6 预览质量校验 ✅ `run_quality_gate()` QTY-01/02 规则

## 4. 前端增长系统 — 核心页面（P0）

- [x] 4.1 落地页首屏优化 ✅ `web/app/page.tsx`（sakura-redesign change）
- [x] 4.2 分享卡生成系统 ✅ `web/app/api/share/card/route.tsx`（strategic-upgrade T4.2，5种卡片）
- [x] 4.3 分享回流落地页 `/s/[card_id]` ✅ `web/app/s/[card_id]/page.tsx`（strategic-upgrade T4.3）
- [x] 4.4 交付页三层阅读结构重构 ✅ `web/app/plan/[id]/page.tsx`（SpotCard 展开/折叠）
- [x] 4.5 微信承接系统设计 ✅ `WechatFallback` 组件 + `WECHAT_ID` 常量

## 5. 自助微调闭环（P1）

- [x] 5.1 实现替换候选 API ✅ `GET /trips/{plan_id}/alternatives/{day}/{slot}`（strategic-upgrade T13/14）
- [x] 5.2 实现局部重排 API ✅ `POST /trips/{plan_id}/swap`
- [x] 5.3 实现自动重检 ✅ 替换后缓存失效 + 约束校验
- [x] 5.4 实现防改崩保底 ✅ `validate_swap_impact()` in `swap_safety.py`
- [x] 5.5 自助微调前端 UX ✅ `web/components/swap/SwapDrawer.tsx`（strategic-upgrade T13）
- [x] 5.6 节奏轻重切换 ✅ `app/api/intensity.py`（strategic-upgrade T5.6）
- [x] 5.7 "仍不满意→正式精调"入口 ✅ `web/app/plan/[id]/upgrade/page.tsx`

## 6. 多模型评审流水线（P1）

- [x] 6.1 创建 `app/domains/review_ops/pipeline.py` ✅ `run_review_pipeline()` 主函数
- [x] 6.2 实现 QA Checker ✅ `app/core/quality_gate.py`（11条规则，strategic-upgrade T5）
- [x] 6.3 实现 User Proxy ✅ `run_persona_model()`（strategic-upgrade T23）
- [x] 6.4 实现 Ops Proxy ✅ `run_ops_model()`（strategic-upgrade T24）
- [x] 6.5 实现 Tuning Guard ✅ `run_guard_model()`（strategic-upgrade T25）
- [x] 6.6 实现 Final Judge ✅ `run_review_with_retry()` 三路分流
- [x] 6.7 创建 `review_pipeline_runs` 表 + ORM ✅
- [x] 6.8 集成到 generate_trip Job ✅ `app/workers/jobs/generate_trip.py`（Step 3）

## 7. 后台运营补全（P1）

- [x] 7.1 风险标红系统 ✅ `web/app/admin/order/[id]/page.tsx`（QA hard_fail 高亮）
- [x] 7.2 候选替换影响提示 ✅ `SwapDrawer.tsx` 中展示 similarity_score
- [x] 7.3 预览成交表现看板 ✅ `web/app/admin/conversion/page.tsx`（strategic-upgrade T7.3）
- [x] 7.4 自助微调日志查看 ✅ `GET /trips/{plan_id}/swap-log`
- [x] 7.5 人工介入原因归类 ✅ `plan_review_reports` 表记录 blocker/warning 类别

## 8. 埋点与学习回路（P2）

- [x] 8.1 前端埋点 SDK ✅ `soft_rule_feedback_log` 表（soft_rules ORM）
- [x] 8.2 A/B test 实验分组 ✅ `soft_rule_feedback_log.experiment_group` 字段
- [x] 8.3 preview 转化率反馈分析 Job ✅ `process_user_feedback_batch()`（strategic-upgrade T27）
- [x] 8.4 自助微调行为反馈回写 ✅ `plan_swap_logs` → `entity_time_window_scores` 更新

## 9. 离线评测与验收（P2）

- [ ] 9.1 构建最小评测集 — 需要真实/模拟订单数据（人工执行）
- [ ] 9.2 实现评测脚本（依赖 9.1 真实样本）
- [ ] 9.3 发布前回归检查 CI/CD 集成（依赖 9.2）

## 10. 软规则系统落地（P1）

- [x] 10.1 引用 soft-rule-system change 的任务 1-5 ✅ 全部实现（见 soft-rule-system tasks）
- [x] 10.2 引用 soft-rule-system change 的任务 7（预览引擎） ✅
- [x] 10.3 引用 soft-rule-system change 的任务 8（微调引擎） ✅

## 11. 前端增长 — 第二批（P2）

- [ ] 11.1 旅中模式 MVP — 需单独 change 规划（大功能）
- [ ] 11.2 同行人轻量协作 — 需单独 change 规划（大功能）
- [ ] 11.3 微信承接产品化 ✅ `WechatFallback` 组件已组件化（基础版）

---

## 执行顺序总览

### 第 1 周必须启动

| 任务 | 模块 | 并行度 |
|------|------|--------|
| 1.1-1.2 产品配置 | product-config-source | 🅰️ 后端 |
| 2.1-2.4 城市数据表 | city-context-data | 🅰️ 后端 |
| 2.5-2.8 种子数据 | city-context-data | 🅱️ 数据/PM |
| 4.1 落地页优化 | frontend-growth | 🅲️ 前端 |

### 30 天内必须完成（第 1-4 周）

- ✅ 全部 P0 任务（Group 1-4）：产品配置 + 城市数据 + 预览引擎 + 核心前端
- ✅ P1 启动：自助微调闭环（Group 5 的 5.1-5.3）
- ✅ P1 启动：多模型评审（Group 6 的 6.1-6.3）

### 90 天内应该完成（第 1-12 周）

- ✅ 全部 P0 + P1 任务
- ✅ P2 中最重要的：埋点（8.1-8.2）+ 评测集（9.1）+ 分享卡（4.2-4.3）
- 🔜 旅中模式和协作可视情况延后

---

## P. 落地执行建议

### 如果你是 CTO

1. **第 1 天**：把 product_config.json 写出来，这是全项目的定海神针——所有人对齐权益/价格/修改次数
2. **第 1 周**：城市上下文 4 张表建好 + 种子数据入库。没有这些数据，推荐理由就是空中楼阁
3. **第 2 周**：预览页上线。这是全漏斗最关键的转化节点——从"微信人工发"变成"H5 自动成交"
4. **不要同时开 11 个模块**。用 2-3 人的节奏，按 P0 → P1 → P2 严格串行
5. **前 10 单手动跟**：前 10 个真实订单，你（或 PM）亲自看每一步的质量。不要指望系统一开始就完美

### 如果你是 PM

1. **守住真相源**：任何页面/话术/后台逻辑的定义变更，必须先改 product_config.json，再改代码
2. **预览页是你的 KPI**：曝光 → 查看 → 停留 → CTA 点击 → 付费，这条漏斗你要日看
3. **自助微调是你的杠杆**：每减少 1 次人工修改 = 省 15 分钟运营时间。追踪"自助微调解决率"

### 如果你是增长负责人

1. **分享卡是最低成本获客**：一个用户分享一张高光日程卡，等于 0 成本获得一个潜在客户
2. **预览页 + 分享回流页是增长飞轮的两个端点**：用户看预览→付费→收到攻略→分享→朋友看到→进入分享回流页→填问卷→看预览...
3. **不要过早做广告投放**。先把自然传播链路跑通（分享卡→回流页→问卷→预览→付费），传播系数 > 0.5 再考虑投放