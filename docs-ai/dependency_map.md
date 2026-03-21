# Dependency Map（AI 版）

## 核心主链路
### 问卷提交 → 画像 → 方案 → 详情 → 导出
- `app/api/quiz.py`
- `workers/__main__.py::normalize_trip_profile`
- `workers/jobs/generate_plan.py`
- `workers/jobs/generate_trip.py`
- `workers/jobs/run_guardrails.py`
- `workers/jobs/render_export.py`

## 排序主链路
- `ranking/scorer.py`
- `ranking/affinity.py`
- `ranking/queries.py`
- `planning/assembler.py`

## 内容与专题页主链路
### `/rush`
- `web/app/rush/page.tsx`
- `web/lib/data.ts`
- `data/sakura/*.json`
- `web/app/rush/RushClient.tsx`

## 现阶段最不该忽略的依赖
1. `/rush` 依赖的数据文件是强耦合的
2. assembler 强依赖 ranking 结果
3. PDF 导出强依赖模板和渲染器
4. 旧产品 SKU 仍可能被订单/产品 API 调用

## AI 修改顺序建议
1. 先理解主链路
2. 再理解具体模块
3. 最后才动高风险模块
