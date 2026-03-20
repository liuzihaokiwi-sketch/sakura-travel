# 攻略生成流程

## 概述

从用户提交问卷到攻略交付，整个流程由 arq Worker 异步执行，分为 6 个阶段。

## 阶段 1：需求标准化 (normalize_trip_profile)

- **输入**：用户原始问卷数据（`trip_requests.raw_input`）
- **处理**：将自由文本/选择转化为结构化画像（`TripProfile`）
  - 城市列表 + 每城停留天数
  - 出行日期范围
  - 同行人类型（solo/couple/family_child/...）+ 人数
  - 预算级别（budget/mid/premium/luxury）
  - 偏好标签（must_have / nice_to_have / avoid）
- **输出**：`trip_profiles` 表一条记录

## 阶段 2：路线选择 (generate_plan)

- **输入**：TripProfile
- **处理**：
  1. 根据用户画像推荐区域（`geography/region_router.py`）
  2. 匹配路线模板（`geography/route_selector.py`，`data/route_templates/` 中预定义）
  3. 按天数裁剪模板
- **输出**：`itinerary_plans` + `itinerary_days` 骨架

## 阶段 3：候选填充 (generate_trip)

- **输入**：行程骨架 + 每天的 slot 定义
- **处理**：
  1. 加载路线模板 → `planning/assembler.py` 的 `assemble_trip()`
  2. 按 slot 类型（poi/restaurant/hotel）查询候选实体
  3. 根据 `entity_scores` 排序，匹配用户偏好标签过滤
  4. AI 文案润色（`planning/copywriter.py`）：为每个推荐实体生成一句话描述 + Tips
  5. 路线矩阵计算（`planning/route_matrix.py`）：两点间交通时间
- **输出**：填充完成的 `itinerary_items`

## 阶段 4：护栏检查 (run_guardrails)

- **输入**：完整行程方案
- **处理**：自动化质量检测
  - 每天行程时间是否合理（不超过 12 小时）
  - 交通衔接是否顺畅
  - 是否有重复实体
  - 餐厅推荐是否覆盖午晚餐
- **输出**：检查通过 → 进入渲染；未通过 → 标记问题、可能重新生成

## 阶段 5：渲染导出 (render_export)

- **输入**：通过护栏的行程方案
- **处理**：
  1. Jinja2 模板渲染（`templates/magazine/` 杂志风模板集）
  2. HTML → WeasyPrint PDF
  3. 生成 H5 网页版
  4. 可选：Satori 生成分享卡片 / Playwright 截图
- **输出**：`export_assets` 表存储 URL

## 阶段 6：人工审核 → 交付

- 生成完成后状态变为 `review`
- 管理后台审核页面预览行程，可做结构化修改
- 审核通过后状态变为 `delivered`
- 用户通过微信收到交付链接，打开 `/plan/[id]` 查看