## 1. 精调次数动态化（中低级 AI 可执行）

- [ ] 1.1 在 `app/api/modifications.py` 中新增 `get_max_modifications(sku_id, db)` 函数：先从 SKU features.max_modifications 读取，fallback 到 `{standard_248: 1, premium_888: 3, basic_free: 0}` map。~1h
- [ ] 1.2 重构 `submit_modification` 端点，将 `SKU_MAX_MODIFICATIONS` 硬编码替换为调用 `get_max_modifications`。~30min
- [ ] 1.3 重构 `list_modifications` 端点，同样使用 `get_max_modifications`。~15min
- [ ] 1.4 验证：在无 DB 的情况下 fallback 值正确返回。~15min

## 2. products.py fallback 对齐三档（中低级 AI 可执行）

- [ ] 2.1 替换 `_FALLBACK_PRODUCTS` 列表：改为 3 个 SkuItem（basic_free ¥0, standard_248 ¥248, premium_888 ¥888），features 包含 `max_modifications` 和正确的 `sections` 列表。~1h
- [ ] 2.2 验证 `GET /products` 在 DB 为空时返回三档 fallback 数据，价格和 includes 文案正确。~15min

## 3. PDF 水印实现（高级 AI 推荐）

- [ ] 3.1 修改 `app/domains/rendering/renderer.py` 的 `render_html` 和 `_build_render_context` 函数，增加 `order_id` 可选参数，生成 `watermark_text` 传入模板 context。~1h
- [ ] 3.2 在 `templates/itinerary_default.html` footer 区域添加水印 CSS + HTML（position:fixed, bottom-right, opacity 0.12, 8px 字号）。~30min
- [ ] 3.3 在 `templates/magazine/base.html.j2` 的 `<body>` 末尾添加通用水印 block，供子模板继承。~30min
- [ ] 3.4 修改 `app/api/trips_generate.py` 的 `export_plan` 端点，查询关联 order_id 并传入 render_html。~30min
- [ ] 3.5 验证：生成的 HTML 和 PDF 包含正确水印文案，无 order_id 时显示 fallback 文案。~30min
  - 依赖：3.1, 3.2, 3.3, 3.4

## 4. self_adjustment.py ORM 迁移（高级 AI 推荐）

- [ ] 4.1 重写 `get_alternatives` 端点：用 ItineraryDay/ItineraryItem ORM 查询当前 slot 的实体信息，用 `fetch_slot_candidates`（从 assembler 复用）召回同类候选。~2h
- [ ] 4.2 重写 `execute_swap` 端点：用 ORM 更新 ItineraryItem.entity_id，约束校验改为 ORM 查询（当日 item 数、已替换数），操作日志写入 ReviewAction（action_type="self_swap"）。~2h
- [ ] 4.3 重写 `get_swap_log` 端点：从 ReviewAction（action_type="self_swap"）查询历史。~30min
- [ ] 4.4 移除所有 raw SQL 的 `text()` 调用和对 plan_slots/entities/candidate_pool_cache/plan_swap_logs 的引用。~15min
  - 依赖：4.1, 4.2, 4.3
- [ ] 4.5 验证：三个端点不再 500，能正常返回（即使数据为空也返回空列表而非报错）。~30min
  - 依赖：4.4

## 5. 订单状态机文档对齐（中低级 AI 可执行）

- [ ] 5.1 更新 `docs-human/05-delivery-workflow.md` 的状态流转图：改为 `quiz_submitted → preview_sent → paid → generating → review → delivered`，与代码一致。~15min
- [ ] 5.2 更新 `docs-human/02-system-architecture.md` 中引用的状态说明，确保与代码状态机一致。~15min

## 6. 攻略生成结构增强（高级 AI 推荐）

- [ ] 6.1 在 `assembler.py` 的 `assemble_trip` 函数末尾，向 `plan_metadata` 写入 `overview_page` 字段（从已装配数据汇总 cities + total_days + top3 实体 + theme）。~1h
  - 依赖：无
- [ ] 6.2 在 `assembler.py` 的 `assemble_trip` 函数末尾，扫描已选实体的 tags，自动判断是否触发条件页（onsen→温泉礼仪，nightlife→夜生活安全 etc.），写入 `plan_metadata.conditional_pages`。~1.5h
  - 依赖：无
- [ ] 6.3 验证：生成一条行程后，plan_metadata 包含 overview_page 和 conditional_pages 字段。~30min
  - 依赖：6.1, 6.2

## 7. 前端精调次数硬编码标记（不修改，仅记录）

> 以下文件包含需要后续单独修改的精调次数硬编码，本次不处理：
> - `web/app/page.tsx` 第351行（"含 2 次免费精调"）、第369行
> - `web/app/pricing/page.tsx` 第62行（"2 次行程精调"）、第73行（"5 次行程精调"）
> - `web/app/pricing/PricingClient.tsx` 第107行
> - `web/app/plan/[id]/page.tsx` 第367行（"剩余2次"）
> - `web/app/plan/[id]/upgrade/page.tsx` 第12行（"5次行程精调"）