## Context

Phase 0 完成了数据底座（实体 Catalog + 评分引擎 + Editorial Boost），系统现在能召回排序后的 POI/餐厅/酒店列表，但还不能把这些实体组装成一份用户可用的攻略产品。

Phase 1 的核心挑战是：**在质量（杂志级排版）和速度（24h 交付）之间找到正确的平衡点**。

当前约束：
- 不能让用户等超过 24 小时（基础版承诺）
- 攻略质量必须超过市面上 100-200 元的定制攻略
- 基础版不需要个性化输入（选场景就行），可以用模板装配
- 初期手动接单，不需要支付自动化

---

## Goals / Non-Goals

**Goals:**

- 实现基于**路线模板**的行程装配引擎（5 条经典路线覆盖主要场景）
- 实现**杂志级 HTML/CSS 渲染**，支持 PDF + H5 双格式导出
- 实现 **AI 文案润色层**（LLM 只改表达，不改事实）
- 实现完整的**异步生成管线**（generate_trip → run_guardrails → render_export）
- 实现 **plan_artifacts 追溯链路**（每次生成可复现）
- 支撑 19.9 基础版的完整生产闭环

**Non-Goals:**

- 基于用户个人输入的个性化编排（Phase 2 的事）
- 酒店动态报价接入（Phase 2+ 的事）
- 自动化支付流程（初期手动）
- 多语言渲染（初期只做中文）
- 实时交通数据（v1 用估算 / Google Routes 静态缓存）

---

## Decisions

### D1：行程编排策略 — 模板装配 vs 动态规划

**决策：Phase 1 用「模板装配」，不做动态规划**

| 选项 | 优点 | 缺点 |
|------|------|------|
| 模板装配（选择） | 快速实现、结果可预期、质量可控 | 灵活性低，覆盖场景有限 |
| 动态规划 | 灵活、个性化强 | 实现复杂、质量不稳定、调试难 |

理由：19.9 基础版本来就是「选场景」，不是「输入需求」，模板装配完全够用。动态规划留给 Phase 2 个性化定制。

模板结构：
```
route_template
  ├── meta（名称、天数、城市、场景适配）
  ├── days[]
  │   ├── day_num
  │   ├── theme（当日主题，如"东京历史文化"）
  │   ├── time_blocks[]
  │   │   ├── time_slot（morning/afternoon/evening）
  │   │   ├── slot_type（poi/restaurant/hotel_area/transport）
  │   │   ├── tags_required（召回条件，如 culture_history>=3）
  │   │   └── fallback_entity_id（保底实体 ID）
  │   └── transport_notes（当日交通说明）
  └── scene_variants（不同场景的参数覆盖，如 couple/family/solo）
```

### D2：渲染方案 — WeasyPrint vs Puppeteer vs Playwright

**决策：WeasyPrint（Python 原生）+ 静态 HTML 预览**

| 选项 | 优点 | 缺点 |
|------|------|------|
| WeasyPrint（选择） | Python 原生、无需 Node、CSS Print 支持好 | 复杂 CSS 兼容有限制、字体需系统安装 |
| Puppeteer/Playwright | CSS 支持完整、像素精准 | 需要 Node 环境、Docker 镜像更重 |

理由：技术栈全 Python，WeasyPrint 够用，PDF 质量满足需求。字体问题通过 Docker 镜像预装解决（Noto Sans CJK）。

H5 预览用 Jinja2 渲染静态 HTML，存对象存储，发分享链接。

### D3：AI 文案润色时机 — 装配前 vs 装配后

**决策：装配后润色，以结构化 JSON 为输入**

装配完成后，行程已经是确定的结构化数据（哪天去哪、什么顺序），再把每个实体的基础信息喂给 LLM，让它只生成「一句话描述」和「小 Tips」，不改变事实。

这样：
- LLM 的幻觉风险被隔离（事实已锁定，LLM 只改表达）
- 每个实体描述独立生成，可缓存复用
- 调试容易（JSON → HTML 链路清晰）

### D4：异步生成管线 — arq Job vs Celery vs 同步

**决策：复用现有 arq，不引入 Celery**

Phase 0 已用 arq 实现 score_entities，保持一致性。生成管线拆成三个串行 Job：

```
generate_trip(trip_id)
  → 装配行程 → 写 itinerary_plans/days/items
  → 调用 run_guardrails(trip_id)
    → 审核规则检查 → 写 review_jobs
    → 如 pass：调用 render_export(trip_id)
      → WeasyPrint PDF + 静态 HTML → 写 export_assets
```

Job 之间通过 Redis enqueue 串联，每个 Job 完成后更新 trip_requests.status。

### D5：CSS 模板设计原则

**决策：「Magazine Clean」主题，一套主题多个变体**

设计原则：
- 高留白、大图、简洁字体（Noto Sans SC + 衬线标题）
- 封面全屏图 + 路线标题
- 每日行程用卡片式布局（时间轴 + 实体卡片）
- 实体卡片：图片 + 名称 + 标签徽章 + 一句话描述 + 实用信息（营业时间/交通）
- 颜色体系：暖白底色 + 深灰文字 + 日式和风强调色（朱红/深绿/靛蓝）

初期只做一套「magazine_clean」主题，后续场景（情侣/亲子/轻奢）通过 CSS 变量覆盖实现变体。

---

## Risks / Trade-offs

| 风险 | 描述 | 缓解方案 |
|------|------|---------|
| WeasyPrint 字体问题 | CJK 字体渲染缺失或错误 | Docker 镜像预装 Noto Sans CJK，CI 验证截图对比 |
| 模板覆盖场景有限 | 5 条路线无法覆盖所有用户需求 | 先覆盖最高频场景（东京/关西），场景外拒单或降级处理 |
| LLM 文案幻觉 | GPT 生成不符合实体实际情况的描述 | prompt 严格约束（禁止添加未提供信息），审核规则检查关键词 |
| Google Routes API 成本 | 大量实体对的距离查询 | 写入 route_matrix_cache，相同城市对复用，TTL 30天 |
| entity_media 图片不足 | 部分实体没有图片导致卡片丑 | fallback 到城市默认图片 + 图标占位，审核规则 soft_fail |
| 渲染耗时过长 | WeasyPrint 大文档渲染慢 | 异步 Job + 进度推送，H5 预览先出，PDF 后台生成 |

---

## Migration Plan

1. **数据库**：Phase 0 的表结构已覆盖（itinerary_plans/days/items/export_jobs/export_assets/plan_artifacts），无需新增迁移
2. **路线模板种子数据**：通过 `scripts/load_route_templates.py` 一次性写入 route_templates 表
3. **渲染依赖**：Docker 镜像新增 WeasyPrint + Noto Sans CJK（Dockerfile 更新）
4. **静态文件存储**：初期用本地 `/exports/` 目录 + nginx 服务，对象存储 Phase 2 接入
5. **上线顺序**：路线模板 → 装配引擎 → 文案润色 → 渲染 → 导出管线 → API 接入

回滚：所有新能力独立模块，回滚只需注释 arq functions 注册 + 关闭路由，不影响 Phase 0 功能。

---

## Open Questions

1. **路线模板种子数据内容**：5 条经典路线的具体每日安排由谁来审定？建议：系统生成初稿，你做最终校准
2. **图片来源**：entity_media 表数据量是否足够？Phase 0 的 Google Places 采集是否已经获取了 photo 信息？
3. **H5 分享方式**：是做带参数的链接（无登录可看）还是需要登录？初期建议无登录直接访问
4. **初期交付方式**：手动接单时，是你手动跑生成脚本，还是要一个简单的触发界面？
