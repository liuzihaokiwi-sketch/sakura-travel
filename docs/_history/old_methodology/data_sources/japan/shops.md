# 日本店铺/购物数据源

> 版本: 1.0
> 更新: 2026-04-10
> 适用: 宝藏店铺、古着、杂货、市集、伴手礼

**重要:** 店铺不同类型有不同的最佳来源，**不能全靠小红书**。日文来源通常比中文来源更准确。

---

## 一、按店铺类型分数据源

### 古着/中古（vintage/furugi）

| 网站 | 域名 | 访问方式 | 实战价值 |
|------|------|---------|---------|
| **thisismedia** | media.thisisgallery.com | OpenCLI web read | 京都古着 22 选+大阪古着 12 选，最详细的古着店指南 |
| **F-STREET** | f-street.org | WebFetch | 古着/中古店门户（关西最全），大阪/东京古着店最全信息 |
| **VINTY** | vinty.jp | WebSearch 间接 | 古着屋/ヴィンテージ专门检索 |
| **古着屋巡りマップ MEGURU** | furugi-meguru.com | WebSearch 间接 | 关西古着屋地图指南 |
| **JAM TRADING** | jamtrading.jp | WebFetch | 大阪美国村古着屋 40 选地图 |
| **DRESS CODE.** | fukulow.info | WebFetch | 京都古着屋 9 选（ヴィンテージ重视） |
| **装苑 ONLINE** | soen.tokyo | WebFetch | 编辑型推荐，有深度 |
| **ELLE HK** | elle.com.hk | WebFetch | 京都中古店 6 大必逛（2025），奢侈品二手 |
| **WAmazing** | tw.wamazing.com | WebFetch | 日本二手商店 10 间推荐 |

### 杂货/生活风格（zakka）

| 网站 | 域名 | 访问方式 | 实战价值 |
|------|------|---------|---------|
| **Hanako Web** | hanako.tokyo | WebFetch | 中崎町古着+雑货特集（Hanako 编辑精选） |
| **ことりっぷ cottrip** | co-trip.jp | OpenCLI web read | 中崎町レトロ雑货 4 选 |
| **かんでん WITH YOU** | media.kepco.co.jp | WebFetch | 京都雑货 8 选+古着 6 选+独立书店+神户雑货 7 选 |
| **GOOD LUCK TRIP** | gltjp.com | WebFetch | 中崎町攻略 |
| **Pen / Casa BRUTUS** | pen-online.com / casabrutus.com | WebFetch | 设计媒体，生活方式精选 |
| **豆瓣** | douban.com | WebFetch | 京都私藏清单（咖啡/器皿/伴手礼） |

### 书店/唱片

| 网站 | 域名 | 访问方式 | 实战价值 |
|------|------|---------|---------|
| **CINRA** | cinra.net | WebSearch 间接 | 京都个性派书店特集 |
| **Recoya** | recoya.net | WebSearch 间接 | 京都唱片店 49 家指南 |

### 工艺/特产（craft / local_specialty）

| 数据源 | 类型 | 说明 |
|--------|------|------|
| 各产业协会官网（如京焼清水焼協会） | 官方 | 传统工艺源头 |
| JNTO 工艺/购物页面 | 官方 | 政府官方工艺介绍 |
| 百货地下食品层 | 官方 | 伴手礼权威 |
| 机场免税店名录 | 官方 | 伴手礼验证 |
| **Japan Shopping Now** | japanshopping.org | WebFetch | 官方访日购物信息站，按店型分类 |
| **Leaf KYOTO** | leafkyoto.net | WebSearch 间接 | 京都站伴手礼 16 选+蚤市 12 选 |

### 综合推荐

| 网站 | 域名 | 访问方式 | 实战价值 |
|------|------|---------|---------|
| **aumo** | aumo.jp | WebSearch 间接 | 古着 6 选 |
| **icotto** | icotto.jp | WebFetch | 古着 16 选 |
| **関西おでかけ手帖** | odekake.osakagas.co.jp | WebFetch | 综合店铺攻略 |

---

## 二、市集/蚤の市专门

| 网站 | 域名 | 说明 |
|------|------|------|
| **tedukuri-ichi.com** | tedukuri-ichi.com | 百万遍手作市+梅小路手作市官网 |
| **heiannominoichi.jp** | heiannominoichi.jp | 平安蚤市官网 |
| **fmfm.jp** | fmfm.jp | 全国跳蚤市场/市集指南 |
| **kyoto-1banchi.com** | kyoto-1banchi.com | 京都蚤市年度日历 |

---

## 三、商店街专用

| 数据源 | 类型 | 说明 |
|--------|------|------|
| 各商店街公式サイト | 官方 | 店铺一览、营业信息 |
| 地元新聞（関西おでかけ） | 媒体 | 商店街特色报道 |

---

## 四、traveler_fit 源

| 数据源 | 域名 | 访问方式 | 备注 |
|--------|------|---------|------|
| **小红书** | xiaohongshu.com | OpenCLI | 宝藏店铺发现主要渠道，中国游客购物体验 |
| **携程 Trip.com** | trip.com | WebFetch | 中国游客购物评分 |

---

## 五、搜索词模板

| 语言 | 搜索词 |
|------|-------|
| 日文 | `"{城市} 古着屋 おすすめ"` |
| 日文 | `"{城市} 雑貨屋 おすすめ ブログ"` |
| 日文 | `"{城市} 独立書店"` |
| 日文 | `"{城市} 伝統工芸 ショップ"` |
| 日文 | `"{城市} 商店街 おすすめ"` |
| 日文 | `"{城市} 蚤の市"` |
| 简中 | `"{城市}宝藏店铺 小众"` |
| 简中 | `"{城市}中古店 推荐"` |
| 简中 | `"{城市}必逛"` |
| 英文 | `"{city} vintage shops"` |
| 英文 | `"{city} japan shopping guide"` |

---

## 六、访问问题与替代方案

**WebFetch 可用:** f-street.org, fukulow.info, media.kepco.co.jp, hanako.tokyo, gltjp.com, japanshopping.org, icotto.jp

**WebFetch 被阻止（用 OpenCLI）:** media.thisisgallery.com, co-trip.jp

**被 WebFetch 但可 WebSearch 间接获取:** vinty.jp, furugi-meguru.com, cinra.net, recoya.net, aumo.jp, leafkyoto.net

---

## 七、坐标获取策略（省 Google API）

```
优先免费方式:
1. 店铺官网（日本店铺官网常有地图）
2. Google Maps 手动搜索（浏览器，不用 API）
3. OpenStreetMap
4. 攻略站文章中的地图信息
5. 商店街官网通常有地图

最后才用 Google Places API。
```

---

## 八、店铺不需要完整三轴

店铺是"惊喜层"不是"骨架层"，不需要和餐厅/酒店同重量的三轴评分。

**评价方式:** 用 `selection_level`（must_visit / recommended / worth_checking）做粗粒度分层，不做 grade S/A/B/C。

**来源证据标准:** 至少 2 个来源，且至少 1 个专业/官方/编辑源（如 F-STREET、装苑、Hanako、官方商店街）。仅小红书 1 篇提及不够。
