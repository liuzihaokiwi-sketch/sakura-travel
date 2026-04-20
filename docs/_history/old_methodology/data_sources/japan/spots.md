# 日本景点数据源

> 版本: 1.0
> 更新: 2026-04-10
> 适用: 日本圈景点/体验活动采集

---

## 一、P0 权威源

| 数据源 | 域名 | 三轴角色 | 访问方式 | 备注 |
|--------|------|---------|---------|------|
| **japan-guide.com** | japan-guide.com | quality 主骨架 | WebFetch `japan-guide.com/e/e{id}.html` | 英文最权威日本旅游指南。编辑等级（top/recommended/featured）直接映射景点 grade |
| **JNTO** | japan.travel / japan-travel.cn | quality 权威 | WebFetch `japan.travel/en/destinations/kansai/{city}/` | 日本政府官方，覆盖全国 |
| **Google Maps** | maps.google.com | execution（坐标+营业+热度） | Places API | 评分+评论量+营业状态。城市内相对比较，不做跨品类 quality 主源 |

### japan-guide 编辑等级映射

| japan-guide 等级 | 我们的 grade |
|-----------------|------------|
| Top Attraction | heritage_s 或 A |
| Recommended | A 或 B |
| More Attractions | B 或 C |

**Google 评论量是补充信号，不是主骨架。** 很多文化名片评论量不过万但绝对值得去。

---

## 二、P1 辅助源

| 数据源 | 域名 | 三轴角色 | 访问方式 | 备注 |
|--------|------|---------|---------|------|
| **携程 Trip.com** | trip.com | traveler_fit 主信号 | WebFetch / OpenCLI | Trip.Best 多因子算法排名（评分+评论+销量），景点常用 5 分制 |
| **小红书** | xiaohongshu.com | traveler_fit 体验细节 | OpenCLI `xiaohongshu search` | 中国游客热门度、排队实况、近期波动 |
| **TripAdvisor** | tripadvisor.com | traveler_fit 国际游客 | WebFetch `tripadvisor.com/Attractions-g{id}-{City}.html` | 国际游客排名 |
| **马蜂窝** | mafengwo.cn | traveler_fit 补充 | WebFetch | 景点攻略量大 |

---

## 三、体验活动/workshop 专用

| 数据源 | 域名 | 三轴角色 | 访问方式 | 备注 |
|--------|------|---------|---------|------|
| **Activity Japan** | activityjapan.com | execution 体验活动 | WebFetch（中文版可用） | 体验类活动预订，含体验活动信息 |
| **KKday** | kkday.com | execution 体验活动 | WebFetch | 活动+体验，信息丰富 |
| **Klook** | klook.com | execution 体验活动 | WebFetch | 活动预订 |
| **Viator** | viator.com | execution 体验活动 | WebFetch | TripAdvisor 旗下活动预订 |

---

## 四、P2 独立攻略站

### 英文编辑站

| 网站 | 域名 | 访问方式 | 实战价值 |
|------|------|---------|---------|
| Inside Kyoto | insidekyoto.com | WebFetch | 京都景点深度指南+区域分析 |
| Inside Osaka | insideosaka.com | WebFetch | 大阪景点深度指南 |
| MATCHA | matcha-jp.com | WebFetch | 多语言，覆盖面广 |
| GOOD LUCK TRIP | gltjp.com | WebFetch | 按城市分品类推荐 |
| ANA 日本旅游推荐 | ana.co.jp/zh/cn/japan-travel-planner | WebFetch | 全日空官方，各城市游玩路线 |

### 中文综合

| 网站 | 域名 | 访问方式 | 实战价值 |
|------|------|---------|---------|
| 穷游网 | qyer.com | WebFetch | 中国游客深度攻略 |
| 马蜂窝 | mafengwo.cn | WebFetch | 景点攻略+游记 |
| 知乎 | zhihu.com | WebFetch | 深度讨论 |
| allabout-japan.com | allabout-japan.com | WebFetch | 日本深度攻略 |
| 乐吃购 | letsgojp.com | WebFetch 被 403（WebSearch 间接） | 台湾/香港旅客专属日本攻略 |

### 日文专业

| 网站 | 域名 | 访问方式 | 实战价值 |
|------|------|---------|---------|
| じゃらん news | jalan.net/news | WebFetch | 最新景点资讯 |
| 旅 Pocket | tabikobo.com/tabi-pocket | WebFetch | 都道府县分类 |

### 台湾博主

| 网站 | 域名 | 访问方式 | 实战价值 |
|------|------|---------|---------|
| 帶你去旅行（BringYou） | bring-you.info | OpenCLI | 京都景点+深度攻略 |
| 小兔小安旅遊札記 | mimigo.tw | OpenCLI | 景点+食宿综合 |
| Funliday | funliday.com | WebFetch | 行程规划+攻略 |
| James 的旅遊日記 | jamesdiscover.tw | WebFetch | 日本旅游攻略 |

### 新景点专门站

| 网站 | 域名 | 说明 |
|------|------|------|
| nara-canoco.com | nara-canoco.com | 奈良新景点 2025 |

---

## 五、季节/节庆数据源

| 数据源 | 域名 | 访问方式 | 特别价值 |
|--------|------|---------|---------|
| **日本气象厅（JMA）** | jma.go.jp | WebFetch | 历史气候数据、樱花/红叶预测 |
| **Weathernews** | weathernews.jp | WebFetch | 樱花预测、赏枫预测 |
| 各神社/寺院官方网站 | - | WebFetch | 祭典日程、特别公开日 |

---

## 六、搜索词模板

| 语言 | 搜索词 |
|------|-------|
| 英文 | `"japan-guide {city}"` |
| 英文 | `"{city} japan travel guide"` |
| 日文 | `"{城市} 観光 おすすめ スポット"` |
| 日文 | `"{城市} 穴場 スポット"` |
| 日文 | `"{城市} 観光 ランキング"` |
| 简中 | `"{城市}景点 必去 推荐"` |
| 简中 | `"{城市}小众景点"` |
| 简中 | `"{城市}必去"` |
| 繁体台 | `"{城市}景點 推薦"` |

---

## 七、访问问题与替代方案

**WebFetch 可用:** japan-guide.com, japan.travel, tripadvisor.com, insidekyoto.com, insideosaka.com, matcha-jp.com, gltjp.com

**WebFetch 被阻止（用 OpenCLI）:** bring-you.info, mimigo.tw, livejapan.com, letsgojp.com

---

## 八、三轴分配（快速参考）

| 景点类型 | quality 主源 | traveler_fit | execution |
|---------|------------|-------------|-----------|
| heritage_s（文化/历史） | JNTO + japan-guide "Top" + 世界遗产/国宝 | 携程/小红书 | Google Maps + 官网 |
| popular_s（大众热门） | Google 评论量前 10% + 携程热度 | 小红书热度+携程排名 | Google Maps + 官网 |
| A 级常规景点 | japan-guide "Recommended" | 携程 | Google Maps |
| 体验活动 | japan-guide + 专业源 | 小红书 | Activity Japan/KKday/Klook |
