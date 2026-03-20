# 任务对半分工 (2 个 AI 并行)
> 更新时间: 2026-03-19 23:05
> 项目路径: /Users/yanghailin/projects/travel-ai

## 总览

| 类别 | 总任务数 | 已完成 | 剩余 |
|---|---|---|---|
| 爬虫开发 | 11 模块 | 5 ✅ 测试通过 | 4 待测试 + 2 废弃 |
| Phase 0 数据层 | 42 子任务 | 41 ✅ | 1 ❌ (GPT标签) |
| Phase 1 行程引擎 | 47 子任务 | 28 ✅ | 19 ❌ |
| 爬虫→系统集成 | 6 任务 | 0 | 6 ❌ |

**剩余总计: ~30 项任务**，对半分为 **AI-A (15项)** 和 **AI-B (15项)**。

---

## AI-A: 爬虫验证 + 数据集成 + 交通矩阵

> 重点: 确保数据流从爬虫 → DB 全链路打通

### A1. 爬虫测试验证 (4项)
```
❌ A1.1 测试 experiences.py (KKday/Klook/VELTRA)
    → python scripts/experience_crawl.py --city tokyo --limit 10
❌ A1.2 测试 letsgojp.py (樂吃購)
    → python scripts/guide_crawl.py --source letsgojp --city tokyo --limit 10
❌ A1.3 测试 matcha.py (MATCHA)
    → python scripts/guide_crawl.py --source matcha --city tokyo --limit 10
❌ A1.4 测试 xiaohongshu.py (小红书)
    → python scripts/guide_crawl.py --source xiaohongshu --keyword "东京攻略" --limit 10
```

### A2. 爬虫→DB 数据集成 (5项)
```
❌ A2.1 Google Flights → flight_offer_snapshots 表写入
    文件: app/domains/flights/price_monitor.py + scripts/flight_crawl.py
    逻辑: 调用 GoogleFlightsCrawler.search_flights_full() → 写入 flight_offer_snapshots
❌ A2.2 酒店爬虫 → hotels 表 / entity_base 表写入
    文件: app/domains/catalog/pipeline.py
    逻辑: HotelCrawler 结果 → upsert hotels + entity_base
❌ A2.3 JNTO景点 → entity_base 表写入
    文件: app/domains/catalog/pipeline.py
    逻辑: JNTOCrawler.gotokyo_spots → upsert entity_base(type=poi)
❌ A2.4 活动/体验数据 → 新建 events/experiences 表 或复用 entity_base
    文件: DB migration + pipeline
❌ A2.5 统一采集调度器 (把所有爬虫串联成 daily job)
    文件: scripts/crawl.py 增强 或 新建 scripts/crawl_all.py
```

### A3. Phase 1 — 交通矩阵 G6 (6项)
```
❌ A3.1 创建 app/domains/planning/route_matrix.py
    实现 get_travel_time(origin_id, dest_id, mode, session, redis_client)
❌ A3.2 Google Routes API 调用 (Transit + Walk)
❌ A3.3 Redis / DB 双层缓存
❌ A3.4 fallback 估算 (步行15分/公交30分)
❌ A3.5 scripts/prebuild_route_matrix.py 批量预计算
❌ A3.6 entity_card.html.j2 注入交通时间
```

**AI-A 总计: 15 项**

---

## AI-B: API 接入层 + 端到端验证 + 收尾

> 重点: 确保用户可以触发完整的行程生成流程

### B1. Phase 0 收尾 (2项)
```
❌ B1.1 GPT标签生成 (需要 OPENAI_API_KEY)
    → python scripts/generate_tags.py --city tokyo
    → python scripts/generate_tags.py --city osaka
    → python scripts/generate_tags.py --city kyoto
❌ B1.2 G1.4 验证模板加载到 route_templates 表
    → python scripts/load_route_templates.py
    → 检查 5 条记录 + slots 总数
```

### B2. Phase 1 — API 接入层 G7 (5项)
```
❌ B2.1 创建 app/api/products.py
    实现 GET /products (返回 19.9 基础版 SKU)
❌ B2.2 实现 POST /trips/{id}/generate
    接收 template_code + scene → enqueue generate_trip → 返回 202
❌ B2.3 实现 GET /trips/{id}/preview
    返回 H5 预览 URL (从 export_assets 查询)
❌ B2.4 实现 GET /trips/{id}/exports
    返回 PDF 下载链接列表
❌ B2.5 在 app/main.py 中注册新路由
```

### B3. Phase 1 — 端到端验证 G8 (8项)
```
❌ B3.1 运行完整生成流程: POST /trips/{id}/generate → 等完成 → GET preview
❌ B3.2 验证 PDF 可打开, 中文正常, 杂志级排版
❌ B3.3 验证 H5 预览手机端可访问
❌ B3.4 验证 planner_runs 追溯记录完整
❌ B3.5 验证 trip_requests.status 流转正确
❌ B3.6 生成 tokyo_classic_5d/couple 攻略 → 人工检查
❌ B3.7 生成 kansai_classic_6d/family 攻略 → 人工检查
❌ B3.8 更新 README.md (Phase 1 命令+API 端点)
```

**AI-B 总计: 15 项**

---

## 快速启动 Prompt

### 给 AI-A 的 prompt:
```
看 scripts/crawlers/AI_TASK_SPLIT_V2.md 的 AI-A 部分。

你负责 3 个方向:
1. 验证 4 个未测试爬虫(experiences/letsgojp/matcha/xiaohongshu)，修 bug 到能跑通
2. 把爬虫数据接入 DB (flight_offer_snapshots/hotels/entity_base)
3. 实现交通矩阵 route_matrix.py (G6)

先从 A1 爬虫验证开始，逐个跑 CLI 命令看输出，有问题就修。
```

### 给 AI-B 的 prompt:
```
看 scripts/crawlers/AI_TASK_SPLIT_V2.md 的 AI-B 部分。

你负责 3 个方向:
1. Phase 0 收尾 (GPT标签 + 模板验证)
2. Phase 1 API 接入层 (products/generate/preview/exports)
3. 端到端验证 (完整行程生成流程)

先从 B1 收尾开始，然后 B2 写 API，最后 B3 跑全链路验证。

注意: B1.1 需要配置 OPENAI_API_KEY 环境变量。
```

---

## 依赖关系

```
A1 (爬虫验证) ──→ A2 (数据集成) ──→ B3 (端到端验证)
                                      ↑
B1 (Phase 0收尾) ──→ B2 (API层) ─────┘
                                      ↑
A3 (交通矩阵) ───────────────────────┘
```

A 和 B 大部分可并行，只有 B3 端到端验证 依赖 A2 数据集成完成。
