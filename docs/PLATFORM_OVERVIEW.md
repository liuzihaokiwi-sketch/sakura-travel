# Japan Travel AI — 平台功能全景
> 最后更新: 2026-03-19 23:33
> 项目路径: /Users/yanghailin/projects/travel-ai

## 一、系统架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户层 (Frontend)                         │
│  对话式意图解析 → 偏好问卷 → 行程预览 → PDF/H5 攻略下载          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────────┐
│                     API 接入层 (FastAPI)                         │
│  /chat/*  /trips/*  /products  /pois/*  /admin/*  /ops/*        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                     领域逻辑层 (Domains)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ catalog  │ │ ranking  │ │ planning │ │rendering │          │
│  │ 数据目录  │ │ 智能排序  │ │ 行程规划  │ │ 渲染导出  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ flights  │ │geography │ │ intake   │ │live_inv  │          │
│  │ 机票监控  │ │ 区域路由  │ │ 意图解析  │ │ 实时天气  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                     数据层 (PostgreSQL + Redis)                   │
│  A层-目录(8表) B层-业务(7表) C层-派生(4表) D层-快照(2表)         │
│  共 ~21 张表                                                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                     数据采集层 (Crawlers)                         │
│  Google Flights │ Booking/携程 │ Tabelog │ JNTO │ VELTRA │ ... │
└─────────────────────────────────────────────────────────────────┘
```

## 二、数据采集层 (scripts/crawlers/)

| 功能模块 | 数据源 | 状态 | 采集内容 |
|---|---|---|---|
| ✈️ 机票采集 | Google Flights | ✅ | 航班号/航司/时间/价格 (Lite+Full+Calendar) |
| 🏨 酒店采集 | Booking/携程/Agoda/Jalan | ✅ | 名称/星级/价格/评分/坐标 |
| 🍜 餐厅采集 | Tabelog | ✅ | 名称/评分/预算/地址/坐标/分类 |
| 🎌 活动采集 | japan-guide.com | ✅ | 节日/樱花/红叶 (12节日+43樱花点) |
| 🏯 官方景点 | JNTO + GO TOKYO | ✅ | 143目的地+62景点+15季节指南 |
| 🎿 体验活动 | VELTRA | ⚠️ | 活动名/价格/评分/时长 (23条/页) |
| 📖 攻略文章 | 樂吃購/MATCHA/小红书 | ❌ | 待修复 |

## 三、数据目录层 (app/domains/catalog/)

| 功能 | 说明 |
|---|---|
| CTI 实体模型 | 中心表 entity_base + 扩展表 pois/hotels/restaurants |
| 多维标签 | entity_tags — 4命名空间: feature/audience/theme/avoid |
| 媒体资源 | entity_media — 图片/视频 + 封面标记 |
| 编辑标注 | entity_editor_notes — boost/避雷/季节提示/内行秘诀 |
| 酒店区域导览 | hotel_area_guide — 周边景点+交通提示 |
| 一键采集 | POST /admin/sync/{city} — AI生成 or 真实爬虫 |
| Google Places | 同步 Google 地图数据 |
| AI 数据生成 | Claude AI 生成景点/餐厅/酒店数据 (离线可用) |
| GPT 标签 | 自动为实体打标签 |

## 四、智能排序层 (app/domains/ranking/)

| 功能 | 说明 |
|---|---|
| 多维度评分 | 平台评分归一化 + 新鲜度衰减 + 风险惩罚 |
| 主题权重 | 根据用户问卷计算偏好权重 (文化/美食/自然/购物/亲子...) |
| 亲和度 | 实体与场景/人群的适配度计算 |
| 编辑加权 | 人工 boost -8~+8 覆盖算法分 |
| 上下文排序 | 结合天气/季节/时间段的实时排序 |

## 五、行程规划引擎 (app/domains/planning/ + trip_core/)

| 功能 | 说明 |
|---|---|
| 模板系统 | 路线模板 + 场景变体 (情侣/家庭/独旅/闺蜜) |
| 候选填充 | 按 slot 类型从 DB 取候选 → 标签过滤 → 排序 |
| 日程构建 | 按时间轴排列每日行程 + 游览时长 + 路程估算 |
| 费用估算 | 每日开销预估 (门票+餐饮+交通) |
| AI 文案 | GPT 为每个景点生成个性化推荐语 |
| 交通矩阵 | route_matrix_cache 表已建 (实现待完成) |

## 六、渲染输出层 (app/domains/rendering/)

| 功能 | 说明 |
|---|---|
| HTML 渲染 | Jinja2 模板，杂志级排版 |
| PDF 渲染 | HTML → PDF 转换 |
| H5 预览 | 手机端可访问的预览页面 |

## 七、API 端点全表 (app/api/)

| 路由 | 方法 | 功能 |
|---|---|---|
| /chat/start | POST | AI 对话 — 解析旅行意图 |
| /chat/refine | POST | AI 对话 — 追问补充 |
| /chat/confirm | POST | AI 对话 — 确认并创建行程 |
| /trips | POST | 创建行程请求 |
| /trips/{id} | GET | 查看行程详情 |
| /trips/{id}/status | GET | 查看行程状态 |
| /trips/{id}/profile-questions | GET | 获取偏好问卷 |
| /trips/{id}/questionnaire | POST | 提交偏好问卷 |
| /trips/{id}/recommendations | GET | 获取推荐方案 |
| /trips/{id}/generate | POST | 触发行程生成 (异步 202) |
| /trips/{id}/plan | GET | 获取生成的行程计划 |
| /trips/{id}/export | POST | 导出 HTML/PDF |
| /trips/{id}/preview | GET | H5 预览链接 |
| /trips/{id}/exports | GET | PDF 下载列表 |
| /products | GET | 商品 SKU 列表 |
| /products/{id} | GET | 商品详情 |
| /pois/search | GET | 景点搜索 |
| /pois/{id} | GET | 景点详情 |
| /cities | GET | 城市列表 |
| /admin/sync/{city} | POST | 管理员一键采集 |
| /admin/sync-all | POST | 管理员批量采集 |
| /ops/* | GET/POST | 运营后台 (编辑标注/实体管理/排序调试) |
| /health | GET | 健康检查 |

## 八、后台任务 (app/workers/jobs/)

| Worker | 功能 |
|---|---|
| generate_plan.py | 异步行程规划 |
| generate_trip.py | 完整行程生成流水线 |
| render_export.py | HTML/PDF 渲染导出 |
| run_guardrails.py | 行程质量校验 |
| scan_flight_prices.py | 机票价格定期扫描 |
| score_entities.py | 实体评分批量计算 |

## 九、数据库表 (~21张)

| 层级 | 表名 | 说明 |
|---|---|---|
| **A-目录** | entity_base | 所有实体中心表 |
| | pois | 景点扩展 |
| | hotels | 酒店扩展 |
| | restaurants | 餐厅扩展 |
| | entity_tags | 多维标签 |
| | entity_media | 媒体资源 |
| | entity_editor_notes | 编辑标注 |
| | hotel_area_guide | 酒店周边导览 |
| **B-业务** | trip_requests | 行程请求 |
| | trip_days | 行程天 |
| | trip_day_items | 行程项 |
| | planner_runs | 规划运行记录 |
| | export_assets | 导出资产 |
| | route_templates | 路线模板 |
| | route_template_slots | 模板插槽 |
| **C-派生** | entity_scores | 实体评分 |
| | itinerary_scores | 行程评分 |
| | candidate_sets | 候选集 |
| | route_matrix_cache | 交通矩阵缓存 |
| **D-快照** | flight_offer_snapshots | 机票价格快照 |
| | hotel_price_snapshots | 酒店价格快照 |
