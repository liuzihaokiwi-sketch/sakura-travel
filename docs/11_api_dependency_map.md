# Travel AI — 全管线外部 API 依赖地图

> **版本**: v2 (2026-03-23)
> **维护者**: 架构层
> **核心原则**: 系统在运行时的核心决策链（选圈→过滤→排主活动→定住法→排骨架→填次要活动/餐厅）是确定性本地算法；但它依赖离线采集与预计算得到的外部事实数据。外部 API 主要集中在三处：离线数据采集、入口自由文本解析、出口文案与运行期风险信号。

---

## 一、主链路总览

```
用户输入
  │
  ▼
[问卷 AI 解析]                ── AI API (入口解析)
  │
  ▼
[Phase 2–3: 决策链]           ── 运行时零 API，依赖离线预计算数据
  │  city_circle_selector
  │  → eligibility_gate
  │  → major_activity_ranker
  │  → hotel_base_builder
  │  → route_skeleton_builder
  │  → secondary_filler
  │  → meal_flex_filler
  │
  ▼
[Phase 4: 文案 & 报告]       ── AI API (出口生成)
  │  copywriter
  │  → report_payload_vNext
  │  → renderer
  │
  ▼
[运行期: 风险 & 应变]        ── 天气/交通 API + AI API (风险信号)
  │  live_risk_monitor
  │  → fallback_router
  │  → quality_gate / review_ops
  │
  ▼
[输出行程]
```

**关键表述：Phase 2–3 在请求执行时不调用外部 API，但依赖离线采集和预计算后的外部数据（评分、营业信息、路线时间、搜索排名等）。**

---

## 二、离线数据采集层

这些 API 在种子数据采集/定时更新时调用，不在用户请求链路上。

| 模块 | 外部 API | 能力 | 调用频率 |
|------|---------|------|---------|
| `google_places.py` | Google Places API (v1) | 地理定位、place details、评分/评论摘要、营业信息、照片引用 | 新增实体时 / 定期刷新 |
| `route_matrix.py` | Google Routes API v2 (`computeRouteMatrix`) | 真实路线时长/距离矩阵（含公交换乘），替代 Haversine 估算 | 新增实体时 / 定期刷新 |
| `web_crawler.py` | httpx → 各旅游网站 | 抓取景点/餐厅/酒店原始信息 | 种子采集 / 增量爬取 |
| `serp_sync.py` | SerpAPI / 搜索引擎 | 搜索排名、热度信号 | 定期刷新 |

> ⚠️ **当前状态**: Google Places 和 Routes API 均未配置 Key，使用爬虫数据 + Haversine 估算作为开发期替代。Haversine 只适合开发期近似，不适合长期当城市内排程依据。

> 💰 **成本**: Routes API `computeRouteMatrix` $5/1000次（关西 1,508 对 ≈ $7.5 一次性）；Places API $17/1000次。均为缓存后极低频调用。

---

## 三、运行时 AI 调用层

### 3.1 模型分层策略

| Tier | 配置键 | 用途 | 调用频次/行程 | 推荐模型 |
|------|--------|------|-------------|---------|
| **Light** | `ai_model_light` | 标签/分类/翻译 | 0-5 次 | gpt-4o-mini / qwen-turbo |
| **Standard** | `ai_model_standard` | 文案生成/文本解析 | 8-35 次 | qwen-max / gpt-4o |
| **Strong** | `ai_model_strong` | 质量评审/复杂推理/多维评估 | 1-3 次 | claude-sonnet / claude-opus |

### 3.2 调用明细（以 6 天行程为例）

| 环节 | 模块 | Tier | 调用次数 | 估算 tokens |
|------|------|------|---------|------------|
| 问卷自由文本解析 | `quiz.py` | Light | 1 | ~500 |
| 实体文案 (每个景点/餐厅) | `copywriter.py` | Standard | 20-30 | ~12,500 |
| 总纲报告 | `report_generator.py` | Standard | 1 | ~3,000 |
| 每日攻略 | `report_generator.py` | Standard | 6 | ~13,800 |
| 质量门控评审 | `quality_gate.py` | **Strong** | 1-2 | ~4,000 |
| 不合格重写 | `report_generator.py` | Standard | 0-2 | ~3,000 |
| **合计** | | | **~35 次** | **~33,000 tokens** |

### 3.3 AI 缓存策略

两层缓存，各自独立：

| 层 | 实现 | TTL | 作用 |
|----|------|-----|------|
| **应用层结果缓存** | Redis / DB (`ai_cache.py`) | 7 天 | 相同 prompt+参数 命中缓存，零 API 调用 |
| **模型服务侧 Prompt Caching** | OpenAI/Anthropic 自动 | 会话级 | 相同前缀 prompt 降低输入 token 费用和延迟 |

> 应用层缓存是我们主动控制的，确保相同实体+场景不重复生成。模型侧 prompt caching 是服务商自动触发的，额外收益。

### 3.4 降级兜底

| 场景 | 策略 |
|------|------|
| AI 调用超时 (>3s) | 使用 DB 原始描述替代文案 |
| AI 返回格式异常 | 重试 1 次，仍失败则用模板兜底 |
| API 余额不足 | 跳过文案层，骨架直出（无文案但结构完整） |

---

## 四、运行期外部信号层

用户旅行期间的实时监控和应变。

### 4.1 外部 API

| 模块 | 外部 API | 能力 | 调用频率 |
|------|---------|------|---------|
| `weather.py` | 天气 API | 实时天气、预报、预警 | 每天 2-4 次 / 活跃行程 |
| 交通扰动检查 | Google Routes / 公交 API | 实时交通延误、停运 | 事件触发 |
| `notifier.py` | 企微/邮件/推送 | 航班变动、天气预警通知用户 | 事件触发 |

### 4.2 本地运行期控制（零 API）

| 模块 | 功能 |
|------|------|
| `live_risk_monitor` | 综合天气/交通/营业状态，计算风险等级 |
| `fallback_router` | 风险超阈值时触发备选走廊/活动替换 |
| `quality_gate` | 规则引擎四维评分（完整性/可行性/多样性/体验） |
| `review_ops` | 人工/AI 评审流水线，标记问题并触发重写 |
| `preview_selector` | 多版本选优，A/B 候选 |
| `feedback_distillation` | 用户反馈回流，微调评分权重（飞轮） |

---

## 五、中转站 vs 直连策略

| 阶段 | 方案 | 理由 |
|------|------|------|
| **本地开发** | 中转站 (`newapi.200m.997555.xyz`) | 省钱，快速验证 |
| **阿里云预发布** | 阿里云百炼 DashScope + Claude 官方 | 国内合规、延迟低、稳定 |
| **生产上线** | 官方直连（必须） | 数据安全、SLA 保障、合规 |

> ⚠️ 生产环境必须去掉中转站。用户旅行数据（日期、同行人、住址偏好）属于个人信息，过境第三方中转站有法律风险。

切换零代码改动，只需修改 `.env`：
```env
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_MODEL_STANDARD=qwen-max
AI_MODEL_STRONG=claude-sonnet-4-20250514
```

---

## 六、成本估算

### 单次 6 天行程生成

| 项目 | 成本 |
|------|------|
| AI 文案 + 报告 (~33K tokens, Standard) | ¥0.5-1.0 |
| AI 质量评审 (~4K tokens, Strong) | ¥0.3-0.5 |
| **合计** | **¥1-2 / 次** |

### 离线预计算（一次性）

| 项目 | 成本 |
|------|------|
| Google Routes 矩阵 (1,508 对) | ~$7.5 |
| Google Places 详情 (500 实体) | ~$8.5 |
| **合计** | **~$16 一次性** |

> 缓存后这些数据 30 天内不再调用。
