# 日本餐厅数据源

> 版本: 1.0
> 更新: 2026-04-10
> 适用: 日本圈餐厅采集

**可信度分级:**
- **P0** 权威源 — 可作为 quality 轴唯一来源
- **P1** 辅助源 — 需配合 P0，对中国游客极重要
- **P2** 参考源 — 交叉验证、独立站 indie_quotes

**三轴角色:**
- `quality` — 品质/专业性/口碑
- `traveler_fit` — 中国游客实际满意度
- `execution` — 营业状态/预约/排队

---

## 一、P0 权威源

| 数据源 | 域名 | 三轴角色 | 访问方式 | 备注 |
|--------|------|---------|---------|------|
| **Tabelog（食べログ）** | tabelog.com | quality 主骨架 | WebFetch（排名页可用） | 日本最权威餐厅评分。城市×菜系×价格带内相对排名，不跨品类比较。3.5 在怀石是中等，在甜品已很强 |
| **Tabelog 百名店** | tabelog.com/award/hyakumeiten | quality 年度精选 | WebSearch | 各菜系前 100，Tabelog 编辑年度精选 |
| **米其林指南** | guide.michelin.com | quality 顶级权威 | WebSearch 获取年度名单 | 星级+Bib Gourmand。覆盖面有限，未入选不等于不好 |
| **Google Maps** | maps.google.com | execution（评分+营业） | Places API（$17/1000请求）| 评论量+最近评论时间+营业状态。不做 quality 主源 |

**Tabelog 访问格式:**
- 排名页: `tabelog.com/{prefecture}/rstLst/?SrtT=rt`
- 菜系排名: `tabelog.com/{prefecture}/rstLst/{cuisine}/?SrtT=rt`

---

## 二、P1 辅助源（中国游客）

| 数据源 | 域名 | 三轴角色 | 访问方式 | 备注 |
|--------|------|---------|---------|------|
| **携程 Trip.com** | trip.com | traveler_fit 主信号 | WebFetch / OpenCLI `ctrip search` | 中国游客评分+评论+人民币价格。对本产品极重要 |
| **小红书** | xiaohongshu.com | traveler_fit 体验细节 | OpenCLI `xiaohongshu search` | 高频出现=traveler_hot 信号，需去营销内容。笔记正文 2026-04 起需 OpenCLI |
| **大众点评** | dianping.com | traveler_fit 补充 | WebFetch | 必须结合评论量看，平台持续治理 AIGC/促评 |
| **马蜂窝** | mafengwo.cn | traveler_fit 补充 | WebFetch | 深度攻略，量大 |

---

## 三、P1 辅助源（日本本地）

| 数据源 | 域名 | 三轴角色 | 访问方式 | 备注 |
|--------|------|---------|---------|------|
| **GURUNAVI（ぐるなび）** | r.gnavi.co.jp | quality 辅助 | WebFetch | 多语言，菜单/座席/人均消费信息全 |
| **Retty** | retty.me | quality 辅助 | WebFetch | 偏大众口味，实名推荐 |
| **SAVOR JAPAN** | savorjapan.com | quality 辅助 | WebFetch | 面向外国人，有年度 Best Restaurant 排行 |
| **Hot Pepper** | hotpepper.jp | execution 补充 | WebFetch | 日本三大美食网站，含优惠券信息 |
| **TripAdvisor** | tripadvisor.com | traveler_fit 国际游客 | WebFetch | 国际游客排名，非中国游客主源 |

---

## 四、P2 独立攻略站

**台湾博主（美食专精）:**

| 网站 | 域名 | 访问方式 | 实战价值 |
|------|------|---------|---------|
| 凯的日本食尚日记 | kaikk.tw | OpenCLI | 关西美食深度，台湾博主 |
| 水晶安蹄 | auntie.tw | WebFetch | 大阪心斋桥/难波/道顿堀详细 |
| Klook 部落格 | klook.com/zh-TW/blog | WebFetch | 景点+美食推荐 |

**中文综合:**

| 网站 | 域名 | 访问方式 | 实战价值 |
|------|------|---------|---------|
| 乐吃购 | osaka.letsgojp.cn | WebFetch 被 403（WebSearch 间接） | 大阪/京都美食总攻略，信息量大 |
| MATCHA | matcha-jp.com | WebFetch | 多语言日本旅游杂志，覆盖广 |
| allabout-japan.com | allabout-japan.com | WebFetch | 日本深度攻略，已爬取 130+ 条目 |
| 知乎 | zhihu.com | WebFetch | 深度讨论和真实经验 |
| 十六番 | 16fan.com | WebFetch | 日本美食总攻略 |
| Japaholic（日本迷） | japaholic.cn | WebFetch | 有 Tabelog 百名店信息 |

**英文编辑站:**

| 网站 | 域名 | 访问方式 | 实战价值 |
|------|------|---------|---------|
| Time Out | timeout.com | WebFetch | 国际城市指南日本版 |
| LIVE JAPAN | livejapan.com | WebSearch 间接 | 综合旅游指南 |
| byFood | byfood.com | WebFetch | 日本美食博客集合，10 大博客推荐 |
| Food Sake Tokyo | foodsaketokyo.com | WebFetch | 东京美食专家 |

**日文专业:**

| 网站 | 域名 | 访问方式 | 实战价值 |
|------|------|---------|---------|
| 旅 Pocket（旅工房） | tabikobo.com/tabi-pocket | WebFetch | 都道府县美食 61 选，按地区分类全 |
| じゃらん news | jalan.net/news | WebFetch | 地方美食+最新景点，日本人视角 |
| 4travel.jp | 4travel.jp | WebFetch | 日本人游记+评分 |

---

## 五、搜索词模板

| 语言 | 搜索词 |
|------|-------|
| 日文 | `"{城市} {菜系} ランキング tabelog"` |
| 日文 | `"tabelog {城市} 百名店"` |
| 日文 | `"{城市} {菜系} おすすめ 食べログ"` |
| 简中 | `"{城市}美食推荐"` |
| 简中 | `"{城市}必吃"` |
| 简中 | `"{城市}{菜系}推荐"` |
| 繁体台 | `"{城市}美食 推薦 部落格"` |
| 繁体港 | `"{城市}美食 推介"` |
| 英文 | `"best {cuisine} in {city} japan"` |
| 英文 | `"{city} food guide"` |

**搜索策略:** 城市级（广）→ 区域级（深）→ 菜系/主题级（精）。每次记录搜索词+独立站 URL+高频店名。

---

## 六、访问问题与替代方案

| 被阻止 | 替代方案 |
|--------|---------|
| 乐吃购（403） | WebSearch "letsgojp {city}" |
| kaikk.tw（被阻） | OpenCLI |
| LIVE JAPAN（被阻） | WebSearch 间接 或 OpenCLI |

**WebFetch 可用:** tabelog.com, trip.com, savorjapan.com, retty.me, r.gnavi.co.jp, matcha-jp.com, auntie.tw, timeout.com

**WebFetch 被阻止（用 OpenCLI）:** livejapan.com, kaikk.tw

---

## 七、三轴分配（快速参考）

| 品类/价位 | quality 主源 | quality 辅助 | traveler_fit | execution |
|-----------|-------------|-------------|-------------|-----------|
| 餐厅 luxury/premium | Tabelog 品类排名 + 米其林 | 百名店/Google | 携程/小红书 | Google Maps + 官网 |
| 餐厅 mid/budget | Tabelog 品类排名 | 百名店/Retty | 携程/大众点评 | Google Maps + 官网 |
| 餐厅 street（街头小吃）| Google 评分+评论 | Retty/小红书 | 小红书/携程 | Google Maps + 独立站 |
