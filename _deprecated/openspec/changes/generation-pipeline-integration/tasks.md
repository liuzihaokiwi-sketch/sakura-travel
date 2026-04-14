## 1. assembler 接入三维评分（🔴 高级 AI 推荐，核心改动）

- [x] 1.1 在 `assembler.py` 新增 `_build_user_weights(session, trip_request_id)` 函数 ✅
- [x] 1.2 新增 `_rescore_candidates` 函数：候选召回后用三维公式重排序 ✅
- [x] 1.3 在 `assemble_trip` 主函数入口处调用 `_build_user_weights`，候选召回后调用 `_rescore_candidates` ✅
- [ ] 1.4 验证：生成一条行程，对比接入前后的实体选择差异 ~1h

## 2. assembler 装配后交通时间校验（🟡 高级 AI 推荐）

- [x] 2.1 在 `assembler.py` 新增 `_post_check_commute(session, plan_id)` 函数 ✅
- [x] 2.2 在 `assemble_trip` 主函数末尾、commit 前调用 `_post_check_commute` ✅
- [ ] 2.3 验证：生成一条东京行程，检查 plan_metadata 中是否有 route_warnings ~30min

## 3. guardrails 增强为完整 6 项检查（🟡 高级 AI 推荐）

- [x] 3.1 重写 `run_guardrails.py`：集成 swap_safety.check_single_day_guardrails 完整 6 项检查 ✅
- [x] 3.2 soft_fail 写入 plan_metadata.guardrail_warnings，hard_fail 写入 guardrail_errors ✅
- [ ] 3.3 验证：构造一个有定休日冲突的行程，确认 guardrails 能检出 hard_fail ~30min

## 4. preview_day 标记接入（🟡 中高级 AI 可执行）

- [ ] 4.1 在 `generate_trip.py` 的 Step 2.5 前（文案润色后），新增 Step 2.3：调用 `select_preview_day`。~1.5h
  - 需要将 ItineraryDay + ItineraryItem 转换为 `select_preview_day` 需要的 `list[list[dict]]` 格式
  - 结果 `preview_result.selected_day_index` 写入 `plan_metadata.preview_day`
  - `preview_result.needs_human_review` 写入 `plan_metadata.preview_needs_review`
- [ ] 4.2 验证：生成行程后，plan_metadata 包含 preview_day 字段且值合理（不是到达日/离开日）。~30min

## 5. generate_trip job 清理不存在表引用（🟢 中低级 AI 可执行）

- [x] 5.1 移除 `_build_review_context` 中对 `entity_operating_facts` 表的 raw SQL 查询（L108-122），改为 `context["operational_context"] = "暂无营业限制数据"`。~15min
- [x] 5.2 移除 `_build_review_context` 中对 `seasonal_events` 表的 raw SQL 查询（L124-135），改为 `context["seasonal_events"] = "暂无季节活动数据"`。~15min
- [x] 5.3 将 `review_pipeline_runs` 持久化（L288-311）改为 try/except + 日志 warning，并在注释中标记"需要 alembic migration 创建表"。~15min
- [x] 5.4 将 `plan_review_reports` 持久化（L262-285）同理处理。~15min

## 6. planner.py 候选排序改用 EntityScore（🟢 中低级 AI 可执行）

- [x] 6.1 修改 `_fetch_poi_candidates`：JOIN EntityScore，ORDER BY `EntityScore.final_score DESC` 替代 `Poi.google_rating DESC`。~30min（已在 assembler.py L360-392 实现）
- [x] 6.2 修改 `_fetch_restaurant_candidates`：同理 ORDER BY `EntityScore.final_score DESC`。~30min（同上）
- [ ] 6.3 验证：旧路径（无 template_code）触发时，候选排序使用 EntityScore。~15min

## 7. copywriter tags lazy-load 修复（🟢 中低级 AI 可执行）

- [x] 7.1 在 `assembler.py` 的 `enrich_itinerary_with_copy` 中，查出 entity 时使用 `selectinload(EntityBase.tags)` eager load tags 关系，避免 async session 中 lazy load 失败。~30min
- [ ] 7.2 验证：文案润色时 `_get_tags_str` 能正确获取 entity tags，不抛 `MissingGreenlet` 或类似异常。~15min

## 4.1 generate_trip.py 接入 preview_day 标记 ✅