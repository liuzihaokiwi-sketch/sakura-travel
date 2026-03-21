## ADDED Requirements

### Requirement: SEO 文本层与结构化数据

/rush 页面 MUST 包含搜索引擎可索引的文本内容，不能是纯交互型页面。每个城市区块下 MUST 有可读的文本摘要（200-300 字），包含景点名、花期日期、特色。页面 MUST 包含 JSON-LD FAQ schema。

#### Scenario: 页面标题与 meta
- **WHEN** 搜索引擎爬取 /rush
- **THEN** 页面 MUST 包含：
  - title: 「2026 日本樱花实时追踪 — 240+ 景点花期数据 | {品牌名}」
  - H1: 「2026 日本樱花实时追踪」
  - meta description: 「实时追踪全日本 240+ 赏樱景点花期数据，融合气象厅等 6 大权威数据源。查看东京、京都、大阪最新开花状态和最佳赏樱时间。」
  - canonical: `/rush`

#### Scenario: 城市区块文本摘要
- **WHEN** 搜索引擎爬取东京排行榜区块
- **THEN** 区块下方 MUST 包含可索引文本，格式如：「2026 年东京樱花预计 3 月 24 日五分咲，3 月 29 日满开。当前排名第一的赏樱景点是上野公园（约 800 棵樱花树），设有夜樱灯光至 20:00。」此文本以 `<details>` 可展开形式呈现，默认收起但搜索引擎可索引。

#### Scenario: FAQ schema
- **WHEN** 搜索引擎爬取 /rush
- **THEN** 页面 MUST 包含 JSON-LD FAQPage schema，至少 5 个 Q&A：
  1. 2026 年日本樱花什么时候开？
  2. 东京最佳赏樱景点有哪些？
  3. 京都和东京哪个赏樱更好？
  4. 日本赏樱最佳时间是几月？
  5. 夜樱是什么？哪些景点有夜樱？

#### Scenario: H2 标题层级
- **WHEN** 页面渲染
- **THEN** 每个主要区块 MUST 有语义化 H2 标题：
  - H2: 「{城市名} 赏樱景点排行」
  - H2: 「花期时间轴 — 什么时候去最好」
  - H2: 「实时樱花地图」
  - H2: 「常见问题」

---

### Requirement: /rush 页面埋点事件

/rush 页面 MUST 对以下用户行为触发埋点事件，事件通过 `track_event` 写入 user_events 表。

#### Scenario: 全链路埋点覆盖
- **WHEN** 用户在 /rush 页面进行交互
- **THEN** 以下事件 MUST 被追踪：

| event_type | 触发条件 | event_data 必含字段 |
|---|---|---|
| `rush_page_view` | 页面加载完成 | referrer, city_count, spot_count |
| `rush_city_switch` | 切换城市 Tab | from_city, to_city |
| `rush_spot_card_click` | 点击景点卡片 | spot_name, city, rank, score |
| `rush_drawer_open` | Slideover 抽屉打开 | spot_name, city |
| `rush_drawer_cta_click` | 抽屉内「加入行程」点击 | spot_name, city |
| `rush_map_interact` | 地图缩放/拖动/标记点击 | action_type, city |
| `rush_map_popup_detail` | 地图 Popup「查看详情」点击 | spot_name |
| `rush_cta_quiz` | 任何通向 /quiz 的 CTA 点击 | cta_position (hero/contextual/dedicated/drawer) |
| `rush_share_click` | 分享按钮点击 | spot_name (if spot-level), share_method |
| `rush_trust_expand` | 数据源模块展开 | — |
| `rush_scroll_depth` | 页面滚动深度 | depth_pct (25/50/75/100) |
| `rush_stay_duration` | 页面停留时长（离开时） | duration_seconds |

#### Scenario: A/B 实验位
- **WHEN** 产品需要优化转化
- **THEN** 以下 8 个位置 MUST 预留实验 ID 字段：
  1. Hero 文案变体
  2. Hero CTA 文案变体
  3. 排行榜默认城市
  4. Contextual CTA 文案
  5. 景点卡片是否显示「加入行程」角标
  6. 信任模块默认展开 vs 收起
  7. 转化层卡片顺序
  8. 是否显示 Floating CTA（预留但默认关闭）
