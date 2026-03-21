# Do Not Break（AI 版）

## 最高风险文件
这些文件一旦修改，会直接影响全局输出或系统可用性。

- `app/domains/ranking/scorer.py`：三层评分核心
- `app/domains/planning/assembler.py`：行程装配核心
- `app/db/models/business.py`：订单、请求、画像等核心业务表
- `app/db/models/catalog.py`：实体主表和扩展表
- `app/main.py`：应用入口
- `app/db/session.py`：数据库连接
- `web/lib/data.ts`：/rush 实时数据加载器

## 修改前必须做的事
1. 先读依赖关系
2. 先确认是否已有测试或验证脚本
3. 先确认是不是“产品文档要改”而不是“代码先改”
4. 改 ORM 字段前先想迁移

## 当前最常见误改风险
- 把旧 SKU 逻辑硬删，导致订单和产品接口坏掉
- 改 scorer 但没重新验证排序质量
- 改 assembler 但没验证 PDF/H5 结构
- 改 `/rush` 数据字段导致页面白屏
- 改首页首屏结构却不验证移动端

## 数据文件不可删除
- `data/seed/entity_affinity_seed_v1.json`
- `data/seed/p0_route_skeleton_templates_v1.json`
- `data/seed/japan_region_usertype_matrix_v1.json`
- `data/seed/context_score_design.json`
- `data/seed/questionnaire_to_theme_weights_rules_v1.json`
- `data/sakura/sakura_rush_scores.json`
- `data/sakura/weathernews_all_spots.json`
- `data/sakura/jma/jma_city_truth_2026.json`
- `data/route_templates/*.json`

## 修改后最少验证
- API 能启动
- 前端首页可打开
- `/rush` 不白屏
- 一条行程生成链路能跑通
- PDF 导出不报错
