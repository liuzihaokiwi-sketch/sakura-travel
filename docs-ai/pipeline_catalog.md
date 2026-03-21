# Pipeline Catalog（AI 版）

## 当前最重要的 5 条管线

### 1. 问卷画像管线
输入：问卷 raw_input  
输出：`trip_profiles`

### 2. 行程骨架生成管线
输入：`trip_request_id`  
输出：`itinerary_plans` + `itinerary_days`

### 3. 行程详情填充管线
输入：`trip_request_id`  
输出：`itinerary_items`

### 4. 护栏检查管线
输入：`plan_id`  
输出：检查结果 + 状态

### 5. 导出交付管线
输入：`plan_id`  
输出：PDF / H5 资产

## 数据采集管线
- `catalog/pipeline.py`
- `scripts/crawl_orchestrator.py`
- `scripts/crawlers/sakura_pipeline/*`

## 当前产品新方向尚未完全入管线的部分
- 免费体验版钩子生成
- 自助微调闭环
- 条件页触发系统
- 预算偏向影响逻辑

## AI 使用原则
- 先在现有主链路上改，少发明新链路
- 新方向优先做“插入式增强”，不要先推翻所有旧 pipeline
