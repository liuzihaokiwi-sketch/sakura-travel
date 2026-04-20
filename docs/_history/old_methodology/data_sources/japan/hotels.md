# 日本酒店数据源

> 版本: 1.0
> 更新: 2026-04-10
> 适用: 日本圈酒店/旅馆采集

**重要:** 酒店数据源角色**按 hotel_type 不同而不同**，不是统一优先级。详见第七章三轴分配。

---

## 一、P0 权威源

| 数据源 | 域名 | 三轴角色 | 覆盖 | 访问方式 | 备注 |
|--------|------|---------|------|---------|------|
| **一休.com** | ikyu.com | quality 主源（体验型） | 全日本 | OpenCLI 或 WebSearch 间接（WebFetch 403） | 日本高端旅馆首选。多维评分（服务/设施/餐食/风吕）。商务酒店覆盖弱 |
| **楽天トラベル** | travel.rakuten.co.jp | quality 主源（功能型） | 全日本 | WebSearch 间接（WebFetch SSL 错）/ Travel API | 覆盖最广，从商务到旅馆都有。评论量大 |
| **MICHELIN Keys** | guide.michelin.com | quality 顶级权威（体验型） | 全日本 | WebSearch "MICHELIN Keys {city}" | 体验型酒店最高权威。3Keys/2Keys/1Keys 全覆盖 |
| **Forbes Travel Guide** | forbestravelguide.com | quality 国际权威 | 全日本 | WebSearch | 五星酒店评级 |
| **携程 Trip.com** | trip.com | quality+traveler_fit（功能型） | 全日本 | WebFetch / OpenCLI `ctrip search` | 功能型酒店的"品质"就是"住得顺不顺"，携程中国用户评分直接反映。体验型作为 traveler_fit+否决信号 |

### MICHELIN Keys 体系

| 等级 | 含义 | 对应 grade |
|------|------|-----------|
| Three Keys | 住宿体验最高荣誉 | S 级 |
| Two Keys | 杰出住宿 | A 级 |
| One Key | 值得特别关注 | A-B 级 |

---

## 二、P1 辅助源

| 数据源 | 域名 | 三轴角色 | 覆盖 | 访问方式 | 备注 |
|--------|------|---------|------|---------|------|
| **じゃらん** | jalan.net | quality 辅助 | 全日本 | WebSearch 间接 | 日本家庭客偏好，旅馆/温泉宿每日排名 |
| **Booking.com** | booking.com | quality 辅助 | 全日本 | OpenCLI 或 WebSearch 间接（WebFetch JS 阻止）/ Affiliate API | 国际评分体系（1-10 分），需配合其他源 |
| **Agoda** | agoda.com | quality 辅助 | 全日本 | WebFetch | 常有最低价 |
| **Relux** | rlx.jp | quality 辅助（高端） | 全日本 | WebSearch 间接 | 日本高级旅馆，城崎/有马排名 |
| **Hotels.com** | hotels.com | quality 辅助 | 全日本 | WebFetch | 国际 OTA |
| **Extrabux 推荐列表** | extrabux.com | 参考 | 全日本 | WebFetch | 日本订房网站汇总 |
| **小红书** | xiaohongshu.com | traveler_fit 体验细节 | 全日本 | OpenCLI `xiaohongshu search` | 真实住客价格+体验，搜索可用 |
| **马蜂窝** | mafengwo.cn | traveler_fit 补充 | 全日本（关西更全） | WebFetch | 关西温泉旅馆攻略最详细 |

---

## 三、P2 独立攻略站

> **关于 coverage 列的说明（2026-04-10 补）：** P2 独立站的 coverage 列目前是**据"实战价值"备注推断**得出，带 `*` 的**未经亲自访问核实**。很多博主站可能不止写关西（比如也覆盖东京/冲绳），但我没逐站打开主索引页确认。开新圈（关东/九州/北海道）前必须先实地访问去掉 `*` 标记。**不要把这一列当成事实。**

### 台湾博主站（实住评测最详细）

| 网站 | 域名 | 覆盖 | 访问方式 | 实战价值 |
|------|------|------|---------|---------|
| Mimi 韩 | mimigo.tw | 关西（京都/神户/有马）\* | OpenCLI web read | 京都 27 家/神户 8 家/有马 12 家实住评测，价格+优缺点最详细 |
| 波比看世界 | bobbytravel.tw | 关西（神户/有马）\* | OpenCLI web read | 有马 8 家/神户 12 家实住，亲子视角 |
| 乐活的大方 | bigfang.tw | 关西（京都/有马）\* | WebFetch | 有马 Top10 地图+京都新开幕酒店，覆盖广 |
| 阿波旅行中 | april-travel-blog.com | 关西（京都/大阪）\* | OpenCLI web read | 京都 TOP20+大阪 20 间区域分析 |
| 熊猫爱吃鱼 | pandafishtravel.tw | 关西（京都/大阪）\* | OpenCLI web read | 京都 20 间+大阪 30+ 间，评分+价格齐全 |
| 小环妞 | wkitty.tw | 关西（大阪）\* | OpenCLI web read | 大阪 18 间实住，内容详细 |
| 莉莉嗯 | lillian.tw | 关西（京都）\* | WebFetch | 京都 10 间平价青旅/胶囊，TWD480 起 |
| Let's go Kyoto | letsgokyoto.com | 关西（京都/大阪）\* | WebFetch（部分） | 京都区域选择专题+20 间分析+大阪 14 间 |
| Adventurous Mark | adventurousmark.tw | 关西（京都/大阪）\* | OpenCLI web read | 京都 34 间+大阪 29 间，覆盖面最广 |
| Vivianexplore | vivianexplore.tw | 关西（神户/有马）\* | OpenCLI web read | 神户 13 间+有马 8 间 |
| kuolife | kuolife.com | 关西（神户）\* | OpenCLI web read | 神户 12 间平价新开幕酒店 |
| BringYou | bring-you.info | 关西（京都）\* | OpenCLI | 京都 Top30 住宿 |
| tahokkaido.com | tahokkaido.com | 全日本\* | WebFetch | 日本各城市住宿全攻略，有具体入住体验 |

### 香港站

| 网站 | 域名 | 覆盖 | 访问方式 | 实战价值 |
|------|------|------|---------|---------|
| HK01 旅游 | hk01.com | 关西（京都）\* | OpenCLI（部分被阻） | 京都新酒店 25 间+温泉酒店 18 间，港币价格 |
| imtravelholic | imtravelholic.com | 关西（京都/神户）\* | WebSearch 间接 | 京都新酒店 42 间+神户 16 间 |
| GoTrip | gotrip.hk | 关西（京都）\* | WebSearch 间接 | 京都酒店 12 间 |
| U Travel | utravel.com.hk | 关西（京都）\* | WebSearch 间接 | 京都酒店 12 大推介 |
| 永安旅游 | wingontravel.com | 全日本\* | WebFetch | 旅行团+攻略 |

### 日文专业媒体

| 网站 | 域名 | 覆盖 | 访问方式 | 实战价值 |
|------|------|------|---------|---------|
| icotto | icotto.jp | 全日本\* | WebFetch | 新开酒店 17 选+红叶酒店 17 选+料理旅馆 8 选 |
| aumo | aumo.jp | 全日本\*（现有条目关西） | WebSearch 间接 | 京都高级酒店 22 选 |
| OZmall | ozmall.co.jp | 全日本\*（现有条目关西） | WebSearch 间接 | 京都时尚酒店 20 选 |
| GOOD LUCK TRIP | gltjp.com | 全日本\* | WebFetch | 区域别推荐 21 选 |
| JTB | jtb.co.jp | 全日本\* | WebFetch | 红叶露天+温泉+怀石套餐搜索 |
| 関西おでかけ手帖 | odekake.osakagas.co.jp | 关西\* | WebFetch（部分超时） | 京都红叶酒店 16 选+料亭旅馆 12 选+町家 15 选。据域名推断是大阪 gas 运营的关西本地媒体，未核实 |
| マイベスト | my-best.com | 全日本\* | WebSearch 间接 | 各区域独自排名 |

### 英文编辑站（区域分析最透彻）

| 网站 | 域名 | 覆盖 | 访问方式 | 实战价值 |
|------|------|------|---------|---------|
| Inside Kyoto | insidekyoto.com | 关西（京都） | WebFetch | 域名 inside**kyoto** 即是范围声明 |
| Inside Osaka | insideosaka.com | 关西（大阪） | WebFetch | 域名 inside**osaka** 即是范围声明 |
| Japan Highlights | japanhighlights.com | 全日本\* | WebFetch | 区域分析+酒店推荐 |
| The Japan Travel Blog | thejapantravelblog.com | 全日本\* | WebFetch | 6 区域分析 |
| Go Ask a Local | goaskalocal.com | 全日本\* | WebFetch | 本地人视角 |
| LIVE JAPAN | livejapan.com | 全日本\* | WebSearch 间接 | 综合旅游指南+秋季酒店 12 选 |

### 中文综合站

| 网站 | 域名 | 覆盖 | 访问方式 | 实战价值 |
|------|------|------|---------|---------|
| 日式温泉旅馆 | rishiluguan.com | 全日本（温泉）\* | WebSearch 间接 | 关西温泉旅馆排行+赏樱温泉 |
| 换乘案内の案内君 | anneijun.com | 全日本\* | WebFetch | 大阪百元档酒店 16 家，带 CNY 价格 |
| 知乎 | zhihu.com | 全日本 | WebFetch | 不是站点是平台，天然全日本 |

### 新开业专门站

| 网站 | 域名 | 覆盖 | 说明 |
|------|------|------|------|
| ryokolink.com | ryokolink.com | 全日本\* | 各城市年度新开业酒店一览（最全） |
| kansai-sanpo.com | kansai-sanpo.com | 关西 | 域名 kansai- 即是范围声明 |
| newaccom.com | newaccom.com | 全日本\* | 新酒店检索（神户/奈良/全国） |
| nara-canoco.com | nara-canoco.com | 关西（奈良） | 域名 nara- 即是范围声明 |

---

## 四、搜索词模板

| 语言 | 搜索词 |
|------|-------|
| 日文 | `"一休.com {城市} ランキング"` |
| 日文 | `"楽天トラベル {城市} 口コミ"` |
| 日文 | `"{城市} 旅館 おすすめ"` |
| 日文 | `"{城市} ホテル 新規オープン"` |
| 简中 | `"{城市}住宿推荐 攻略"` |
| 简中 | `"{城市}住哪里方便"` |
| 简中 | `"{城市}温泉旅馆推荐"` |
| 繁体台 | `"{城市}住宿 推薦 飯店"` |
| 繁体港 | `"{城市}酒店推介"` |
| 英文 | `"best hotels {city} japan blog"` |
| 英文 | `"{city} ryokan guide"` |

---

## 五、访问问题与替代方案

| 被阻止 | 替代方案 |
|--------|---------|
| 一休 ikyu.com（403） | WebSearch "一休 {city} ランキング" 或 OpenCLI generate |
| 楽天 Travel（SSL 错） | WebSearch "楽天トラベル {city}" 或 OpenCLI generate |
| Booking.com（JS 阻止） | WebSearch "booking.com {city} top rated" 或 OpenCLI generate |
| BringYou（403） | OpenCLI 或 WebSearch "bring-you {city}" |
| Klook 客路（被阻） | WebSearch 间接 |

**WebFetch 可用:** insidekyoto.com, insideosaka.com, bigfang.tw, lillian.tw, letsgokyoto.com, jtb.co.jp, icotto.jp, gltjp.com, tahokkaido.com

**WebFetch 被阻止（用 OpenCLI）:** mimigo.tw, bobbytravel.tw, adventurousmark.tw, wkitty.tw, pandafishtravel.tw, vivianexplore.tw, april-travel-blog.com, bring-you.info, hk01.com

---

## 六、价格采集

**价格必须来自 OTA 真实数据，绝不可 AI 估算。**

```
采集方法:
  一休/楽天/携程各搜索 3 个时段:
  - 淡季（1 月平日）
  - 平季（5 月平日）
  - 旺季（11 月周末/3 月下旬樱花季）

记录:
  - 最低和最高价格
  - 是否含餐、含税
  - 多平台取中位数作为参考价

输出:
  pricing.off_season_jpy: [min, max]
  pricing.regular_season_jpy: [min, max]
  pricing.peak_season_jpy: [min, max]
  pricing.price_note: "含早晚餐 / 旺季翻 3 倍 / ..."
```

---

## 七、三轴分配（快速参考）

### 体验型酒店（ryokan / luxury_ryokan / shukubo / machiya）

| 判断轴 | 主评分源 | 辅助源 |
|--------|---------|--------|
| quality | 一休评分 + MICHELIN Keys | 楽天 / Booking / Relux |
| traveler_fit | 携程 + 小红书 | 马蜂窝 / 独立站 |
| execution | Google Maps + 官方网站 | 独立站实地体验 |

携程在体验型酒店主要作为 traveler_fit 信号，但可作为 quality 的**修正项/否决项**（如多位中国游客反映服务差 → 即使一休高分也要标风险）。

### 功能型酒店（business_hotel / city_hotel / hostel / boutique）

| 判断轴 | 主评分源 | 辅助源 |
|--------|---------|--------|
| quality | 楽天 + **携程** | 一休 / Booking |
| traveler_fit | 携程 + 小红书 | 马蜂窝 / 独立站 |
| execution | Google Maps + 官方网站 | 独立站实地体验 |

功能型酒店的"品质"就是"住得顺不顺"，携程中国用户评分直接反映目标用户感知到的品质。
