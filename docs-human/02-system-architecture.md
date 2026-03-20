# 系统架构

## 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户端 (Next.js 14)                    │
│  /           首页引流                                     │
│  /quiz       5步问卷                                     │
│  /pricing    三档对比                                     │
│  /plan/[id]  杂志级行程交付                                │
│  /submitted  提交成功+微信引导                              │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS / JSON
┌──────────────────────┴──────────────────────────────────┐
│                 FastAPI API Gateway                       │
│  /quiz         问卷提交 → trip_requests 表                 │
│  /orders       订单 CRUD + 状态机                          │
│  /orders/{id}/modify  结构化修改请求                        │
│  /admin/reviews/*     审核操作                             │
│  /admin/sync/{city}   数据采集触发                          │
└──────────────────────┬──────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
┌──────────────┐ ┌───────────┐ ┌───────────┐
│  PostgreSQL  │ │   Redis   │ │ arq Worker│
│  35+ 张表    │ │ 缓存+队列  │ │ 异步任务   │
└──────────────┘ └───────────┘ └───────────┘
```

## 领域边界 (DDD)

| 领域 | 路径 | 职责 |
|------|------|------|
| **catalog** | `app/domains/catalog/` | 实体管理（POI/酒店/餐厅）、数据采集、GPT 标签 |
| **ranking** | `app/domains/ranking/` | 三层评分引擎（Base + Context + Editorial） |
| **planning** | `app/domains/planning/` | 行程装配、AI 文案润色、路线矩阵 |
| **rendering** | `app/domains/rendering/` | Jinja2 模板渲染 → HTML/PDF |
| **geography** | `app/domains/geography/` | 区域路由、城市间路线选择、种子数据 |
| **flights** | `app/domains/flights/` | 机票特价监控（Amadeus API） |

## 数据流

```
问卷提交 → TripRequest 写入 DB
         → arq Job: generate_trip
           → geography: 选择路线模板
           → catalog: 获取候选实体
           → ranking: 按偏好评分排序
           → planning: 装配行程 + 生成文案
           → rendering: 渲染 HTML/PDF
         → Order.status = review
         → 人工审核
         → Order.status = delivered
         → 微信通知用户
```

## 管理后台

独立的 `/admin` 路由（密码保护），提供：
- 三列看板：待处理 / 审核中 / 已交付
- 单订单审核页：左右分栏（预览 + 编辑）
- 快捷键：⌘S 保存，⌘Enter 发布