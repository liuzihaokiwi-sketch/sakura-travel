# 🌸 樱花预测系统 — 需求与方案
> 更新: 2026-03-20 10:40
> 两大目标: (1) 采集最靠谱数据 (2) 让用户相信我们数据很牛

---

## 一、数据可信度展示方案（视频/营销素材）

### 核心话术框架

> "我们的樱花预测不是某一个网站的搬运——
> 我们**融合了 4 大权威数据源、覆盖全日本 58 个城市 + 1000+ 赏樱景点**，
> 并根据每个数据源**过去 10 年的预测准确度**来分配权重。"

### 可视化展示数据（视频里用的数字）

| 展示项 | 数值 | 来源 |
|---|---|---|
| 数据源数量 | **4 个一级源 + N 个地方官方** | JMA/JMC/Weathernews/japan-guide |
| 覆盖城市 | **58 个城市**（JMA 标本木观测点） | JMA 官方 |
| 覆盖景点 | **1000+ 赏樱点** | JMC Sakura Navi |
| 用户实况报告 | **200万+ 份** | Weathernews "我的樱花" |
| 更新频率 | **每天 3 次**（花期内） | JMA 08:30/11:30/17:30 |
| 历史数据 | **过去 10 年** | JMA 历年开花/满开日 |
| 置信度评分 | **0-100 分** | 我们的融合算法 |

### 视频脚本亮点

```
1. "别人给你的是一个网站的预测，我们给你的是多源融合的真相"
   → 画面: 展示 4 个数据源 logo 同时汇入一个中心

2. "日本气象厅每天更新 3 次官方观测，这是城市级的金标准"
   → 画面: JMA 网站截图 + "官方标本木观测" 文字

3. "日本气象株式会社覆盖 1000+ 赏樱点，精确到每个公园"
   → 画面: 日本地图上 1000 个点亮起

4. "Weathernews 整合了 200 万+日本用户的实时报告"
   → 画面: 手机报告动画 + "200万+" 数字滚动

5. "我们根据各数据源过去 10 年的准确度来分配权重"
   → 画面: 权重饼图 JMA 100% / JMC 45% / Weathernews 35% / 地方官方 20%

6. "每个景点都有置信度评分，100 分表示官方已确认"
   → 画面: 景点卡片 + 置信度进度条 (100/90/80/55)

7. "最终你看到的，是我们系统综合分析后的最佳观赏窗口"
   → 画面: "3月28日-4月3日 最佳观赏" 日历高亮
```

### 权重可信度说明

```
权重分配理由（可以在视频中快速过）:
- JMA (置信度 100): 国家气象厅，用标准标本木观测，观测 = 事实
- JMC (权重 45%): 日本气象株式会社，专业气象公司，1000+景点覆盖
- Weathernews (权重 35%): 全球最大民间气象公司，200万+用户众包数据
- 地方官方 (权重 20%): 各景点实地确认，"今天到底开没开"最准
```

---

## 二、技术方案

### 数据层级

```
                    ┌─────────────┐
                    │   JMA 官方   │ ← 城市级金标准 (58城市, 100分)
                    └──────┬──────┘
                           │ 城市真相覆盖一切预测
              ┌────────────┼────────────┐
              ▼            ▼            ▼
    ┌─────────────┐ ┌──────────────┐ ┌────────────┐
    │ JMC (45%)   │ │ WN (35%)     │ │ 地方 (20%) │
    │ 1000 景点   │ │ 1400 景点    │ │ 夜樱/祭典  │
    └──────┬──────┘ └──────┬───────┘ └─────┬──────┘
           │               │               │
           └───────────────┼───────────────┘
                           ▼
                 ┌─────────────────┐
                 │ 加权中位数融合   │
                 │ + 置信度评分     │
                 └────────┬────────┘
                          ▼
                 ┌─────────────────┐
                 │  最终景点真相    │
                 │  bloom_date     │
                 │  best_viewing   │
                 │  confidence     │
                 └─────────────────┘
```

### 数据库表设计

#### A. city_bloom_truth (城市级官方真相)
```sql
city_code       TEXT PK     -- tokyo / kyoto / osaka
year            INT  PK
city_name_ja    TEXT        -- 東京
bloom_date      DATE        -- 开花日 (JMA观测)
full_bloom_date DATE        -- 满开日 (JMA观测)
bloom_observed  BOOL        -- true=已观测, false=预测
source          TEXT        -- 'jma'
source_url      TEXT
confidence      INT         -- 100 (JMA) / 80 (预测)
updated_at      TIMESTAMPTZ
```

#### B. spot_bloom_forecast (景点级预测融合)
```sql
spot_id         TEXT PK     -- 'shinjuku_gyoen'
city_code       TEXT FK
spot_name_ja    TEXT        -- 新宿御苑
spot_name_zh    TEXT        -- 新宿御苑
forecast_bloom  DATE        -- 融合后预测开花日
forecast_full   DATE        -- 融合后预测满开日
current_stage   TEXT        -- bud/starting/full_bloom/falling_starts...
stage_score     INT         -- 0-100 (开花进度)
best_view_start DATE
best_view_end   DATE
confidence      INT         -- 置信度 35-100
source_count    INT         -- 参与融合的数据源数量
source_refs     JSONB       -- ["jmc", "weathernews", "local"]
spread_days     INT         -- 各源预测最大差(天), 越小越可信
updated_at      TIMESTAMPTZ
```

#### C. spot_event_calendar (夜樱/祭典)
```sql
spot_id         TEXT FK
event_name      TEXT        -- '中目黒桜まつり'
event_start     DATE
event_end       DATE
illumination_start TIME     -- 18:00
illumination_end   TIME     -- 21:00
official_url    TEXT
last_checked    TIMESTAMPTZ
```

#### D. source_accuracy_history (数据源历史准确度 — 视频素材！)
```sql
source_name     TEXT        -- jma / jmc / weathernews
city_code       TEXT
year            INT
predicted_bloom DATE
actual_bloom    DATE        -- JMA 当年实际观测
error_days      INT         -- 预测误差(天)
```

### 现有代码盘点 (压缩包)

| 文件 | 状态 | 说明 |
|---|---|---|
| models.py | ✅ 可直接用 | Pydantic 模型完整 |
| utils.py | ✅ 可直接用 | fetch/write/clean 工具 |
| lexicon.py | ✅ 可直接用 | 日文状态词典 17 个映射 |
| normalize.py | ✅ 可直接用 | 状态词归一化 |
| providers/jma.py | ✅ **完整可用** | 城市级 HTML 解析，正则匹配观测数据 |
| providers/jmc.py | ⚠️ **只有元数据壳** | 只抓了首页 metadata，没解析 1000 景点 |
| providers/weathernews.py | ⚠️ **只有元数据壳** | 只抓了新闻 metadata，没解析 1400 景点 |
| providers/local_official.py | ✅ 框架可用 | 配置驱动，但只有 2 个示例站点 |
| fusion.py | ✅ **核心逻辑完整** | 加权中位数 + 置信度评分 + 城市/景点融合 |
| cli.py | ✅ 可用 | 命令行入口 |
| configs/local_sites.yaml | ⚠️ 太少 | 只有 2 个示例站点 |

### 需要补充的工作

| # | 任务 | 难度 | 优先级 | 说明 |
|---|---|---|---|---|
| 1 | **JMC 景点级 parser** | ⭐⭐⭐ | 🔴 P0 | 逆向 sakuranavi 页面/API，解析 1000 景点预测日期 |
| 2 | **Weathernews 景点级 parser** | ⭐⭐⭐ | 🔴 P0 | 逆向 weathernews.jp/sakura 的景点数据 |
| 3 | **JMA 历史数据采集** | ⭐⭐ | 🟠 P1 | 抓 10 年历史开花/满开日 → source_accuracy_history |
| 4 | **local_sites.yaml 扩充** | ⭐ | 🟡 P2 | 添加 20-30 个热门景点的本地官方页 |
| 5 | **集成到主项目** | ⭐⭐ | 🟡 P2 | 将 sakura_pipeline 整合到 travel-ai 的 scripts/crawlers/ |
| 6 | **DB 表 migration** | ⭐ | 🟡 P2 | 创建上述 4 张表 |
| 7 | **数据可视化/营销素材** | ⭐ | 🟢 P3 | 生成视频用的图表/截图 |

---

## 三、视频用数据素材生成计划

### 需要生成的图表/数据

1. **多源融合示意图** → 4 个源汇入中心的流程图
2. **日本地图覆盖图** → 58 城市 + 1000+ 景点标注
3. **置信度评分展示** → 几个景点的置信度仪表盘
4. **历史准确度对比** → "过去10年，各数据源预测误差"
5. **最佳观赏窗口日历** → 某景点的观赏日期高亮
6. **权重分配说明图** → 饼图/柱状图

### 视频话术要点

| 点 | 说什么 | 底层支撑 |
|---|---|---|
| 数据量大 | "融合 4 大权威源 + 1000+ 景点" | JMA/JMC/WN/local |
| 数据更新快 | "花期内每天更新 3 次" | JMA 更新频率 |
| 有用户反馈 | "200万+ 日本用户实时报告" | Weathernews 众包 |
| 科学权重 | "根据 10 年历史准确度分配权重" | source_accuracy_history |
| 置信度评分 | "每个景点 0-100 分置信度" | fusion.py 算法 |
| 精确到天 | "告诉你具体哪天去最好" | best_viewing_start/end |
| 实时状态 | "现在是几分咲き，值不值得去" | current_stage + stage_score |

---

## 四、实施步骤

### 立即可做（用现有代码）
1. ✅ 跑 JMA parser → 拿到今年 58 城市的真实开花数据
2. ✅ 跑 fusion → 生成城市级真相
3. ✅ 跑 local_official → 抓 GO TOKYO 赏樱页

### 本周要做
4. 逆向 JMC sakuranavi → 景点级预测 parser
5. 逆向 Weathernews → 景点级预测 parser
6. 扩充 local_sites.yaml → 20+ 热门景点

### 下周要做
7. JMA 历史数据 → 10 年对比
8. 集成到主项目
9. 生成营销素材
