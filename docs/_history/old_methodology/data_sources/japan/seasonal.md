# 日本季节活动数据源

> 版本: 1.0
> 更新: 2026-04-10（基于真实访问/搜索核实）
> 适用: 樱花 / 红叶 / 祭典 / 灯光 / 特别公开 数据采集

---

## 核心分层

季节活动数据需要回答**两个不同的问题**，对应两类数据源：

| 问题 | 数据类型 | 主要来源 |
|------|---------|---------|
| **哪里好看？** 景点排名、各地名所推荐 | 景点排名源 | walkerplus / japan-guide / さくらの会 |
| **什么时候去？** 开花/满开/红叶高峰预测 | 预测/实时情报源 | 気象庁 / tenki.jp / weathernews / n-kishou |

两类不能混用：walkerplus 告诉你「吉野山是樱花圣地」，但不告诉你今年几月满开；气象庁告诉你开花日期，但不做景点推荐排名。

---

## 一、景点排名源（哪里好看）

### 1. hanami.walkerplus.com — 樱花名所排名

| 项目 | 内容 |
|------|------|
| 运营 | KADOKAWA（ウォーカープラス） |
| 覆盖 | 全日本，全国约 1,400 处 |
| 数据类型 | 景点排名（访问量/想去/去了好三种维度）+ 各景点见顶预测时间段 |
| 排名依据 | 1. 访问量（PV）排名；2. 用户"想去"投票；3. 用户"去了好"投票（含历年累积） |
| 权威指标 | 「日本さくらの会」さくら名所100選 标签（国家级认定，可过滤） |
| 访问方式 | WebFetch（待核实）/ WebSearch 间接 |
| 地区过滤 | 可按都道府县、エリア过滤 |
| 更新节奏 | 每年 1-2 月上线新季，12 月后结束更新 |
| 备注 | 投票含历年累积，老名所分数高，新景点有劣势 |

关键 URL：
- 全国人气排名：`https://hanami.walkerplus.com/ranking/`
- 想去排名：`https://hanami.walkerplus.com/ranking/mitai/`
- 去了好排名：`https://hanami.walkerplus.com/ranking/yokatta/`
- さくら名所100選：`https://hanami.walkerplus.com/list/ss0001/`

### 2. koyo.walkerplus.com — 红叶名所排名

| 项目 | 内容 |
|------|------|
| 运营 | KADOKAWA（ウォーカープラス） |
| 覆盖 | 全日本，全国约 1,190 处 |
| 数据类型 | 景点排名 + 各景点见顶预测时间段 + 实时情报 |
| 排名依据 | 与 hanami 相同：PV / 想去 / 去了好 三维度 |
| 访问方式 | WebFetch 被阻（待核实）/ WebSearch 间接 |
| 更新节奏 | 每年 9 月上线新季 |

关键 URL：
- 全国人气排名：`https://koyo.walkerplus.com/ranking/`
- 行った良かった：`https://koyo.walkerplus.com/ranking/yokatta/`
- 京都府：`https://koyo.walkerplus.com/ranking/yokatta/ar0726/`

### 3. japan-guide.com — 编辑评级（景点深度）

| 项目 | 内容 |
|------|------|
| 运营 | japan-guide.com（外国人向け日本旅行ガイド） |
| 覆盖 | 全日本主要城市，以关西/关东/东北覆盖最深 |
| 数据类型 | 编辑评级（best/outstanding/recommended） + 各景点典型花期时段 + 特色说明 |
| 访问方式 | WebFetch 可用 |
| 权威性 | 人工编辑，不是算法排序，与 JNTO 互为参照 |

关键 URL：
- 全国最佳：`https://www.japan-guide.com/e/e2011_where.html`
- 京都樱花：`https://www.japan-guide.com/e/e3951.html`
- 红叶同理，搜 `japan-guide.com koyo {city}` 可得对应页

### 4. sakuranokai.or.jp — 日本さくらの会（国家级权威）

| 项目 | 内容 |
|------|------|
| 运营 | 公益财団法人 日本さくらの会（1964年设立） |
| 数据类型 | さくら名所100選：1990年选定，各都道府県至少1处，国家复数省厅后援 |
| 访问方式 | WebFetch（官网）/ 名单 PDF 下载 |
| 使用方式 | 作为 S 级景点认定参考。名所100選内的景点可直接视为高可信度推荐 |
| 备注 | 选定于 1990 年，不会再更新；某些新兴名所不在列表中 |

---

## 二、预测/实时情报源（什么时候去）

### 1. 気象庁（JMA）— 官方标本木数据

| 项目 | 内容 |
|------|------|
| 运营 | 日本国土交通省 気象庁 |
| 覆盖 | 全国 58 地点标本木（奄美/冲绳 5 地点不预测，实际预测 53 地点） |
| 数据类型 | 官方开花日/满开日记录（标本木，ソメイヨシノ为主） + 历史数据（1953年起） |
| 访问方式 | WebFetch（data.jma.go.jp，政府域名，通常可访问） |
| 权威性 | **最高权威**，是所有其他预测服务的基准数据 |
| 局限 | 只有 58 个标本木地点，不代表观光名所；不做「名所级」预测 |
| 历史数据 | 开花日历史表格可 WebFetch 直接获取，用于填 occurrences |

关键 URL：
- 2026年数据：`https://www.data.jma.go.jp/sakura/data/sakura_kaika.html`
- 历史数据 2021-2025：`https://www.data.jma.go.jp/sakura/data/sakura003_07.html`
- 完整数据目录：`https://www.data.jma.go.jp/sakura/data/`
- 红叶（カエデ/イチョウ）：同站，`/kouyou/` 路径

### 2. tenki.jp — 日本気象協会（景点级预测）

| 项目 | 内容 |
|------|------|
| 运营 | 一般財団法人 日本気象協会 |
| 覆盖 | 全日本，樱花/红叶均有各都道府县景点级预测 |
| 数据类型 | 开花/满开预测 + 见顶时期预测 + 各名所天气预报 |
| 访问方式 | WebFetch 被网络策略拦截（本次核实）；改用 WebSearch 间接获取 |
| 更新节奏 | 樱花：1月底开始发布预测，每周更新；红叶：9月开始，2026年9月更新 |
| 特点 | 日本气象协会官方，与 JMA 标本木数据配合使用 |

关键 URL：
- 樱花预测：`https://tenki.jp/sakura/expectation/`
- 樱花名所：`https://tenki.jp/sakura/`
- 红叶排名：`https://tenki.jp/kouyou/ranking/index.html`
- 红叶见顶：`https://tenki.jp/kouyou/`

### 3. weathernews.jp — Weathernews（最广覆盖+用户实况）

| 项目 | 内容 |
|------|------|
| 运营 | ウェザーニューズ（东证上市，独立气象公司） |
| 覆盖 | 樱花：全国约 1,400 地点；红叶：全国约 1,200 地点 |
| 数据类型 | 气温模拟预测（10,000 通りシミュレーション）+ 用户投稿实况照片 + 景点排名 |
| 访问方式 | WebFetch 被拦截（本次核实）；改用 WebSearch 间接 |
| 特点 | 覆盖地点最广；有用户报告的实时「今見頃かどうか」；红叶名所人气排名与 walkerplus 互为参照 |
| 更新节奏 | 每年 8 月开始发布红叶预测，每周更新实况 |

关键 URL：
- 樱花：`https://weathernews.jp/sakura/`
- 红叶排名：`https://weathernews.jp/koyo/ranking.html`
- 红叶实况：`https://weathernews.jp/koyo/`

### 4. sakura.weathermap.jp + n-kishou.com — 日本気象株式会社

| 项目 | 内容 |
|------|------|
| 运营 | 日本気象株式会社（n-kishou.com，独立气象公司） |
| 覆盖 | 全国约 1,000 处名所；标本木预测 53 地点（与 JMA 相同） |
| 数据类型 | 高精度开花/满开预测（AI 长期预测 + 10,000 通りシミュレーション）+ 红叶見頃予想 |
| 访问方式 | `sakura.weathermap.jp`（WebFetch 待核实）/ `n-kishou.co.jp`（WebSearch 间接） |
| 特点 | 从本季（2026）开始导入 AI 长期预测；在海外 11 国 App Store 旅行类付费榜 No.1 |
| 红叶 | `https://s.n-kishou.co.jp/w/sp/koyo/koyoyoso_hw` |

---

## 三、祭典 / 灯光 / 特别公开 数据源

这三类与樱花/红叶不同——没有「预测」，主要是时间表查询。

### 1. 京都観光Navi（kyoto.travel）

| 项目 | 内容 |
|------|------|
| 运营 | 京都市観光協会 |
| 覆盖 | 京都（关西祭典最权威） |
| 数据类型 | 祭典日程（祇園祭/天神祭/葵祭等）+ 特别参拝时间（春秋特別公開）+ 灯光日程 |
| 访问方式 | WebFetch（待核实）/ WebSearch |
| 更新节奏 | 每年 1-2 月公布当年日程 |

### 2. 各寺社官方网站

适用于：灯光特别参拜（清水寺春季夜间/高台寺/永観堂/东福寺等）、秋季特别公开时间

- 确认方式：WebSearch `"{寺社名} 2026 特別拝観 ライトアップ 期間"` 
- 必须每年重新确认，日期年年微调

### 3. 関西観光本部 / visitkinki.jp

| 项目 | 内容 |
|------|------|
| 运营 | 関西広域連合 観光部門 |
| 覆盖 | 关西整圈（大阪/京都/兵库/奈良/和歌山/滋贺/鸟取） |
| 访问方式 | WebFetch（待核实）/ WebSearch |
| 用途 | 跨城市比较，找关西整圈的祭典/季节活动日程 |

---

## 四、访问方式汇总

| 数据源 | WebFetch | WebSearch | OpenCLI | 备注 |
|--------|---------|-----------|---------|------|
| 気象庁 data.jma.go.jp | 待核实（政府域名，理论可行） | ✓ | — | 历史数据表格建议 WebFetch |
| tenki.jp | ✗（本次被拦截） | ✓ | — | 改用 WebSearch 间接 |
| weathernews.jp | ✗（本次被拦截） | ✓ | — | 改用 WebSearch |
| sakura.weathermap.jp | 待核实 | ✓ | — | |
| hanami.walkerplus.com | 待核实 | ✓ | — | |
| koyo.walkerplus.com | ✗（本次被拦截） | ✓ | — | |
| japan-guide.com | ✓ | ✓ | — | 可直接 WebFetch |
| sakuranokai.or.jp | 待核实 | ✓ | — | PDF 可下载 |
| kyoto.travel | 待核实 | ✓ | — | |

**「待核实」的访问方式：下次使用前先用 WebFetch 测一次，记录结果后去掉"待核实"标记。**

---

## 五、三轴分配

| 判断轴 | 主要来源 | 备注 |
|--------|---------|------|
| **quality**（哪里值得去） | japan-guide 编辑评级 + さくら名所100選 | 不受投票人数影响的固定权威 |
| **traveler_fit**（游客热度） | walkerplus 人气排名 / weathernews 排名 | 反映大众关注度 |
| **execution**（时间安排） | JMA 标本木 + tenki.jp + weathernews | 三个来源交叉核实；JMA 最权威但点数少 |

---

## 六、采集流程建议

### 判断「哪里好看」
```
1. japan-guide 编辑页 → 找该城市/地区 cherry blossom / autumn foliage 专题
2. walkerplus 排名 → 按都道府县筛选，取「行って良かった」前10
3. さくら名所100選 → 核对该地区是否有入选，入选=直接S/A级
```

### 判断「什么时候去」
```
1. JMA 标本木数据 → 查该地区最近标本木的历史开花日均值（用于 occurrence.phases.peak_start/end）
2. weathernews 预测（覆盖最广）→ 核实具体名所的见顶日期
3. tenki.jp → 第二来源交叉验证
4. 祭典/灯光/特别公开 → 当年官方网站确认（每年微调，不可依赖历史数据）
```
