# Strategic Upgrade — 系统快速参考手册

> 版本：v1.0 | 完成日期：2026-03-21
> 涵盖：T1-T29 全部实现的系统组件、API 端点、CLI 命令、数据库表

---

## 一、新增 API 端点汇总

### 自助微调（T13/T14）
| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/trips/{plan_id}/alternatives/{day}/{slot}` | 拉取候选替换列表 |
| `POST` | `/trips/{plan_id}/swap` | 执行景点替换（含约束校验） |
| `GET` | `/trips/{plan_id}/swap-log` | 查看替换操作历史 |

### 节奏切换（T5.6，已有）
| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/trips/{id}/intensity` | 获取当前节奏 |
| `POST` | `/trips/{id}/intensity` | 切换轻松/适中/密集节奏 |

### 配置（T1.4，已有）
| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/config/product-tiers` | 拉取产品定价配置 |

### 分享卡（T4.2，已有）
| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/share/card?plan_id=...&variant=day1` | 生成分享卡 PNG |

---

## 二、新增数据库表汇总（迁移顺序）

### 迁移 20260321_150000（Phase 2-4）
| 表名 | 用途 | 关键字段 |
|------|------|---------|
| `entity_alternatives` | 实体候选替换池 | source_entity_id, alt_entity_id, similarity_score, swap_safe |
| `candidate_pool_cache` | 方案级候选缓存 | plan_id, day_number, slot_index, candidates(JSONB) |
| `plan_swap_logs` | 自助替换日志 | plan_id, old_entity_id, new_entity_id, status |
| `user_entity_feedback` | 旅行后反馈 | entity_id, visited, rating, verified |
| `city_monthly_context` | 城市月度上下文 | city_code, month, comfort_score, crowd_level |
| `entity_time_window_scores` | 实体六维交叉评分 | entity_id, month, time_slot, crowd_score, photo_score |
| `seasonal_events` | 花期/节庆日历 | city_code, event_type, month_start, crowd_impact |
| `transit_matrix` | 区域间交通矩阵 | from_area, to_area, transit_mode, duration_min_avg |

### 迁移 20260321_160000（Phase 5-6）
| 表名 | 用途 | 关键字段 |
|------|------|---------|
| `plan_review_reports` | T22-T25 四维评审报告 | plan_id, overall_score, passed, comments(JSONB), slot_boundaries(JSONB) |
| `entity_data_conflicts` | T26 数据冲突待审 | entity_id, old_data, new_data, conflicts, resolved |
| `invite_codes` | T29 邀请码 | invite_code(PK), order_id, discount_cny, reward_cny, total_uses |
| `invite_rewards` | T29 返现记录 | invite_code, triggered_order_id, reward_cny, status |

### orders 表新增字段
- `invite_code_used` — 使用的邀请码
- `discount_applied_cny` — 实际折扣金额

---

## 三、新增前端组件汇总

| 组件/路由 | 路径 | 用途 |
|---------|------|------|
| `SwapDrawer` | `web/components/swap/SwapDrawer.tsx` | 「换一换」底部抽屉+候选卡片 |
| 预览页 | `web/app/preview/[id]/page.tsx` | 完整重写：SpotCard展开/MOCK fallback/微信复制 |
| Alternatives API | `web/app/api/trips/[planId]/alternatives/.../route.ts` | 候选列表代理 |
| Swap API | `web/app/api/trips/[planId]/swap/route.ts` | 替换+日志代理 |
| 分享回流页 | `web/app/s/[card_id]/page.tsx` | 分享卡回流处理 |
| 转化看板 | `web/app/admin/conversion/page.tsx` | 预览→购买漏斗分析 |

---

## 四、新增脚本工具汇总

### 候选池预计算（T12）
```bash
# 为单个方案预计算
python -m app.workers.scripts.candidate_pool_precompute --plan-id <uuid>

# 批量计算所有未缓存方案
python -m app.workers.scripts.candidate_pool_precompute --all --city tokyo
```

### 数据维护流水线（T26/T27/T28/T29）
```bash
# T26: 更新单个实体的数据（dry-run 模式）
python -m app.workers.scripts.data_pipeline update-entity \
  --entity-id <uuid> \
  --info "浅草寺营业时间已更新为6:00-17:00，2024年3月起" \
  --dry-run

# T27: 处理用户旅行后反馈，标记已验证实体
python -m app.workers.scripts.data_pipeline process-feedback --city tokyo

# T28: 注册新城市（北海道/冲绳/名古屋）
python -m app.workers.scripts.data_pipeline register-city --city hokkaido
python -m app.workers.scripts.data_pipeline register-city --city okinawa
python -m app.workers.scripts.data_pipeline register-city --city nagoya

# T29: 为已付费订单生成邀请码
python -m app.workers.scripts.data_pipeline gen-invite --order-id <uuid>
```

---

## 五、核心系统模块架构

```
生成流程（generate_trip ARQ Job）
├── Step 1: assemble_trip（装配结构化行程）
├── Step 2: enrich_itinerary_with_copy（AI文案润色）
├── Step 2.5: run_quality_gate（T5, 11条硬规则校验）
│   └── 未通过 → trip.status = "review"（转人工）
└── Step 3: 多层评审
    ├── run_review_with_retry（旧评审流水线）
    └── run_multi_model_review（T22-T25, 四维并行）
        ├── run_planner_model（T22: 路线/时间/体力）
        ├── run_persona_model（T23: 用户视角）
        ├── run_ops_model（T24: 预约/排队/风险）
        └── run_guard_model（T25: slot 微调边界）
        └── → 写入 plan_review_reports

自助微调（self_adjustment API）
├── GET /alternatives → candidate_pool_cache → entity_alternatives
├── POST /swap → 约束校验 → plan_slots UPDATE → plan_swap_logs
└── GET /swap-log → 历史记录

数据壁垒（Data Moat）
├── transit_matrix（区域交通矩阵）
├── entity_time_window_scores（六维评分，含 user_verified 来源）
├── seasonal_events（花期/节庆）
├── city_monthly_context（月度气候上下文）
└── user_entity_feedback → process_user_feedback_batch → verified 标记

运营工具
├── xiaohongshu-content-matrix.md（5类内容模板+4周计划）
├── post-trip-followup-sop.md（回访话术+入库规则）
└── data_pipeline.py（T26/T27/T28/T29 CLI）
```

---

## 六、质量门控规则速查（T5）

| 规则 | 编号 | 类型 | 阈值 |
|------|------|------|------|
| 景点数量 | QTY-01 | Hard | 每天 ≥ 3 个 |
| 餐厅覆盖 | QTY-02 | Hard | 每天 ≥ 1 家 |
| 交通说明 | QTY-03 | Soft | 每天应有 |
| 时间段分配 | QTY-04 | Soft | 上午/下午均有 |
| 体力均衡 | QTY-05 | Soft | 高体力≤60%/天 |
| 实体存在性 | QTY-06 | Hard | entity_id 必须在库中 |
| 数据新鲜度 | QTY-07 | Soft | 实体 updated_at < 6 个月 |
| 推荐理由 | QTY-08 | Hard | 每个景点必须有 reason |
| 避坑提醒 | QTY-09 | Soft | ≥ 50% 景点有 avoid_tip |
| 图片覆盖 | QTY-10 | Soft | ≥ 30% 景点有 cover_image_url |
| 禁用词 | QTY-11 | Hard | AI/算法/系统 等禁止出现 |

---

## 七、T29 邀请码规则

- **触发条件**：订单状态为 `paid` 或 `delivered`
- **被邀请者**：首单立减 ¥50（通过 `discount_applied_cny` 字段）
- **邀请者**：每成功带新1人 → +¥50 返现（`invite_rewards.status = pending`）
- **上限**：单个邀请码最多使用 10 次（`max_uses = 10`）
- **返现兑现**：下次下单时自动抵扣（需人工或自动化兑现流程接入）
- **分享文案**：
  ```
  我用这个行程规划服务为去日本做了完美攻略！
  首单立减¥50，用我的邀请码：XXXXXXXX
  链接：https://trip.ai/quiz?invite=XXXXXXXX
  ```

---

## 八、下一步建议

| 优先级 | 操作 | 说明 |
|--------|------|------|
| 🔴 立即 | 运行数据库迁移 | `alembic upgrade head` |
| 🔴 立即 | 种子用户招募（T16） | 5-10人免费试用，收集首批反馈 |
| 🟡 本周 | 小红书首篇发布（T15） | 东京经典5日 Day1 攻略 |
| 🟡 本周 | 旅行后回访脚本上线 | 对已有订单发送回访话术 |
| 🟢 下周 | T9 配图爬虫 | Top 100 实体图片收集 |
| 🟢 下周 | 北海道/冲绳试运营 | `register-city hokkaido` 后配置模板 |
