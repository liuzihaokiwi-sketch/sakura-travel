# Module Registry（AI 版）

## 只保留 AI 最需要知道的模块

### 入口层
- `app/main.py`：FastAPI 应用入口
- `app/api/quiz.py`：问卷提交
- `app/api/trips_generate.py`：生成与导出触发
- `app/api/products.py`：产品与价格接口
- `app/api/orders.py`：订单状态流转

### 领域层
- `app/domains/intake/intent_parser.py`：意图解析
- `app/domains/geography/region_router.py`：区域推荐
- `app/domains/geography/route_selector.py`：路线模板匹配
- `app/domains/ranking/scorer.py`：评分核心
- `app/domains/ranking/queries.py`：候选查询
- `app/domains/planning/assembler.py`：行程装配
- `app/domains/planning/copywriter.py`：AI 文案润色
- `app/domains/planning/route_matrix.py`：交通矩阵
- `app/domains/rendering/renderer.py`：HTML/PDF 渲染

### Worker
- `generate_itinerary_plan`
- `generate_trip`
- `run_guardrails`
- `render_export`
- `score_entities`

### 前端核心
- `web/app/page.tsx`：首页
- `web/app/quiz/page.tsx`：问卷
- `web/app/pricing/page.tsx`：价格页
- `web/app/rush/page.tsx`：樱花页
- `web/app/plan/[id]/page.tsx`：交付页（当前仍有 mock 风险）
- `web/lib/data.ts`：樱花数据加载

## AI 注意
如果只是做产品和文档对齐，不要从所有模块开始读；只需先读以上模块。
