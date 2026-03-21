# Data Models（AI 版）

## 目标
让 AI 快速知道“当前库里有什么”，并知道哪些模型是旧结构，哪些是可延续基础。

## 当前四层
1. Catalog：实体、标签、媒体、编辑备注
2. Snapshots：外部时效数据快照
3. Derived：评分、行程、导出、产物
4. Business：用户、订单、请求、画像、版本、审核

## 仍然有效的核心模型
### Catalog
- `entity_base`
- `pois`
- `hotels`
- `restaurants`
- `entity_tags`
- `entity_media`
- `entity_editor_notes`
- `hotel_area_guide`

### Derived
- `entity_scores`
- `itinerary_plans`
- `itinerary_days`
- `itinerary_items`
- `itinerary_scores`
- `route_templates`
- `export_jobs`
- `export_assets`
- `plan_artifacts`
- `route_matrix_cache`

### Business
- `users`
- `orders`
- `trip_requests`
- `trip_profiles`
- `trip_versions`
- `review_jobs`
- `review_actions`

## 旧结构但仍可能被调用的模型
### `product_sku`
这是现有代码事实，但不是最终产品模型。  
当前新方向是：
- 前台少套餐
- 后台多维映射

因此后续不要继续把 `product_sku` 当成完整产品真相源，尤其不要从它反推前台产品定义。

## 反馈与增长相关模型（需特别记住）
代码和旧文档里还涉及：
- `user_entity_feedback`
- 可能存在的 `entity_time_window_scores` / crowd 类派生分层
- 订单、反馈、复购意向的业务扩展字段

AI 在改动反馈/复购相关功能时，不要只盯 `orders` 和 `trip_profiles`。

## 当前缺少但新方向需要的概念层
这些不一定都要立刻变成表，但 AI 应知道后续会需要：
- 主题家族
- 时间扩展包
- 预算偏向
- 免费体验边界
- 自助微调配置
- 条件页触发规则
- 预览钩子配置

## 真相源边界
- 数据模型文档描述的是“当前代码现实”
- 产品定义真相源在 `product-scope.md` 和人类产品文档中
- 如果 DB 结构和产品定义冲突，先标冲突，不要假装数据库已经迁移完成

## 结论
当前数据库仍可继续用，但 AI 在做设计时要把“旧 SKU 结构”和“新产品结构”分开理解；涉及反馈、复购、体验版、主题层时，不能只盯旧表名推断产品逻辑。
