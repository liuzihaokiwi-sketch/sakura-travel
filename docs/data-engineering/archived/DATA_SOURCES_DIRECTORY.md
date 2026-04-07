# 数据源目录

> 版本: 1.0
> 更新: 2026-04-01
> 用途: 所有可用数据源的完整登记，按类型和优先级分类

**原则：这个目录不是固定的。每采集一个新城市，都要先搜索补充新的数据源。**

搜索方法（通用流程）：
```
→ 搜索 "{城市}美食攻略 博客" / "{城市} food blog"
→ 搜索 "{城市}住宿推荐 攻略"
→ 搜索 "{城市}景点 必去 2025"
→ 搜索 台湾/香港旅游博主对该城市的攻略
→ 搜索 日文 "{城市} グルメ ブログ おすすめ"
→ 把发现的新网站加入本目录
```

---

## 一、权威评分平台（P0 — 可作为唯一来源）

### 餐厅

| 平台 | URL | 覆盖 | 可信度 | 获取方式 | 备注 |
|------|-----|------|--------|---------|------|
| **Tabelog（食べログ）** | tabelog.com | 日本全国88万+餐厅 | S级 | 百名店名单WebFetch / 搜索页WebFetch / 评分需逐家查 | 日本最权威餐厅评分。Tabelog单独可以打S级可信度 |
| **米其林指南** | guide.michelin.com | 全球 | S级 | 年度名单WebFetch | 国际权威，偏高端 |
| **Google Maps** | maps.google.com | 全球 | A级 | Places API ($17/1000请求) | 最大样本量，坐标+营业时间+评分 |

### 酒店

| 平台 | URL | 覆盖 | 可信度 | 获取方式 | 备注 |
|------|-----|------|--------|---------|------|
| **一休.com** | ikyu.com | 日本高端住宿 | S级 | WebFetch搜索结果 | 日本高端旅馆首选 |
| **楽天トラベル** | travel.rakuten.co.jp | 日本全国 | S级 | Travel API（需注册） | 日本最大OTA |
| **じゃらん** | jalan.net | 日本全国 | A级 | WebFetch | 日本家庭客偏好 |
| **携程Trip.com** | trip.com | 全球 | A级 | WebFetch/API | 携程单独可以打A级可信度。中国游客真实评分+人民币价格 |
| **Booking.com** | booking.com | 全球 | A级 | Affiliate API | 国际评分体系(1-10) |

### 景点

| 平台 | URL | 覆盖 | 可信度 | 获取方式 | 备注 |
|------|-----|------|--------|---------|------|
| **japan-guide.com** | japan-guide.com | 日本全国 | S级 | WebFetch各城市页 | 英文最权威日本旅游指南 |
| **JNTO** | japan-travel.cn / japan.travel | 日本全国 | S级 | WebFetch | 日本政府官方 |
| **Google Maps** | maps.google.com | 全球 | A级 | Places API | 评分+评论数+坐标 |

---

## 二、中国游客平台（P1 — 需配合P0使用，但对目标用户极重要）

| 平台 | URL | 类型 | 获取方式 | 特别价值 |
|------|-----|------|---------|---------|
| **携程Trip.com** | trip.com | 酒店+景点+餐厅 | WebFetch/API | 中国游客评分、人民币价格、中文评论 |
| **小红书** | xiaohongshu.com | 全品类UGC | OpenCLI+Chrome | 中国游客真实体验、热门度、避坑信息。要提前到第二优先级使用 |
| **马蜂窝** | mafengwo.cn | 景点+餐厅攻略 | WebFetch | 中国游客攻略，量大 |
| **大众点评（海外版）** | dianping.com | 餐厅 | WebFetch | 中国游客餐厅评分 |
| **穷游网** | qyer.com | 攻略+游记 | WebFetch | 深度攻略 |
| **知乎** | zhihu.com | 问答+攻略 | WebFetch | 深度讨论和真实经验分享 |

---

## 三、日本本地美食/旅行平台（P1）

| 平台 | URL | 类型 | 获取方式 | 特别价值 |
|------|-----|------|---------|---------|
| **GURUNAVI（ぐるなび）** | gurunavi.com | 餐厅信息+预约 | WebFetch | 多语言，菜单/座席/人均消费信息全 |
| **Hot Pepper** | hotpepper.jp | 餐厅+优惠券 | WebFetch | 日本三大美食网站之一 |
| **Retty** | retty.me | 餐厅社区 | WebFetch | 偏大众口味，实名推荐 |
| **SAVOR JAPAN** | savorjapan.com | 餐厅（面向外国人） | WebFetch | 多语言，有年度Best Restaurant排行 |
| **楽天トラベル 旅めしランキング** | travel.rakuten.co.jp/mytrip/gourmet | 各地美食排名 | WebFetch | 按地区排名 |
| **4travel.jp（フォートラベル）** | 4travel.jp | 游记+评分 | WebFetch | 日本人游记，含评分 |
| **TripAdvisor** | tripadvisor.com | 全品类 | API/WebFetch | 国际游客排名 |

---

## 四、中文攻略网站（P2 — 交叉验证+补充）

### 台湾博主/攻略站（繁体中文，高质量日本攻略）

| 网站 | URL | 特色 | 备注 |
|------|-----|------|------|
| **乐吃购！日本** | letsgojp.com / letsgojp.cn | 台湾+香港旅客专属日本攻略 | 分城市分区域，美食/景点/住宿全覆盖 |
| **Klook部落格** | klook.com/zh-TW/blog | 景点+美食推荐 | 有具体餐厅推荐 |
| **KKday** | kkday.com | 活动+体验 | 体验类活动信息丰富 |
| **凱的日本食尚日記** | kaikk.tw | 日本美食专精 | 用户推荐 |
| **帶你去旅行（Bring You）** | bring-you.info | 日本深度攻略 | 用户推荐 |
| **小兔小安旅遊札記** | mimigo.tw | 日本旅游 | 用户推荐 |
| **Funliday** | funliday.com | 行程规划+攻略 | 用户推荐 |
| **James的旅遊日記** | jamesdiscover.tw | 日本旅游攻略 | 用户推荐 |
| **水晶安蹄** | auntie.tw | 日本美食攻略 | 大阪心斋桥/难波/道顿堀详细 |
| **一直玩的馬摩** | massi.tw | Tabelog使用教学 | 实用工具类 |
| **痞客邦PIXNET** | pixnet.net | 部落格平台 | 搜索"{城市}美食"可找到大量博主 |

### 香港攻略站

| 网站 | URL | 特色 | 备注 |
|------|-----|------|------|
| **ufood.com.hk** | ufood.com.hk | 美食情报 | 用户推荐 |
| **新假期（Weekend HK）** | weekendhk.com | 旅游+美食 | 日本旅游专题多 |
| **永安旅游** | wingontravel.com | 旅行团+攻略 | 日本旅游App推荐 |
| **Time Out Hong Kong** | timeout.com.hk | 生活+美食 | 有日本餐厅专题 |
| **Harper's BAZAAR HK** | harpersbazaar.com.hk | 高端生活 | 日本料理推荐 |

### 酒店专精攻略站

| 网站 | URL | 特色 | 备注 |
|------|-----|------|------|
| **乐活的大方** | bigfang.tw | 新开幕饭店整理、区域住宿攻略 | 大阪/东京新酒店信息更新快 |
| **tahokkaido.com** | tahokkaido.com | 日本各城市住宿全攻略 | 有具体入住体验 |
| **letsgokyoto.com** | letsgokyoto.com | 京都住宿专精 | 用户推荐 |
| **metronine.osaka** | metronine.osaka | 大阪官方旅游资讯 | 区域住宿推荐 |

### 简体中文攻略站

| 网站 | URL | 特色 | 备注 |
|------|-----|------|------|
| **allabout-japan.com** | allabout-japan.com | 日本深度攻略 | 已爬取130+条目 |
| **MATCHA** | matcha-jp.com | 多语种日本攻略 | 覆盖面广 |
| **Japaholic（日本迷）** | japaholic.cn | 日本资讯 | 有Tabelog百名店信息 |
| **十六番** | 16fan.com | 旅游攻略 | 日本美食总攻略 |
| **默默答** | toplanit.com | 旅游攻略 | 美食推荐有评分 |

### 英文攻略/博主

| 网站 | URL | 特色 | 备注 |
|------|-----|------|------|
| **Go With Mark Hazyl** | gowithmarkhazyl.com | 旅行博客 | 用户推荐 |
| **When The Travel Begins** | wenthetravelbegins.com | 旅行博客，含大阪45+餐厅 | 用户推荐 |
| **Food Sake Tokyo** | foodsaketokyo.com | 东京美食专家 | 出版过同名书 |
| **byFood** | byfood.com | 日本美食博客集合 | 有10大博客推荐 |
| **GOOD LUCK TRIP** | gltjp.com | 日本旅游攻略 | 英文，按城市分品类推荐 |
| **ANA日本旅游推荐** | ana.co.jp/zh/cn/japan-travel-planner | 全日空官方 | 各城市游玩路线 |

### 日文旅行博客/平台

| 网站 | URL | 特色 | 备注 |
|------|-----|------|------|
| **にほんブログ村** | blogmura.com | 日本最大博客排名 | 旅行+美食分类 |
| **旅Pocket（旅工房）** | tabikobo.com/tabi-pocket | 都道府县美食61选 | 按地区分类全 |
| **じゃらんnet 读物** | jalan.net/news | 地方美食+最新景点 | 日本人视角 |

---

## 五、酒店专用数据源

| 平台 | URL | 特色 | 获取方式 |
|------|-----|------|---------|
| **一休.com** | ikyu.com | 日本高端住宿权威 | WebFetch |
| **楽天トラベル** | travel.rakuten.co.jp | 日本最大，全价位 | Travel API |
| **じゃらん** | jalan.net | 日本家庭客 | WebFetch |
| **携程Trip.com** | trip.com | 中国游客评分+人民币价格 | WebFetch/API |
| **Booking.com** | booking.com | 国际评分(1-10分) | Affiliate API |
| **Agoda** | agoda.com | 常有最低价 | WebFetch |
| **Hotels.com** | hotels.com | 国际 | WebFetch |
| **Relux** | rlx.jp | 日本高级旅馆 | WebFetch |
| **Extrabux推荐列表** | extrabux.com | 日本订房网站汇总 | WebFetch |

---

## 六、特殊数据源

| 平台 | URL | 用途 | 备注 |
|------|-----|------|------|
| **Activity Japan** | activityjapan.com | 体验活动预订 | 中文版可用 |
| **乗換案内** | jorudan.co.jp | 交通时刻表 | API可用 |
| **日本气象厅** | jma.go.jp | 历史气候数据 | 预计算用 |
| **Google Directions API** | — | 路线计算 | API |

---

## 七、数据源发现流程（通用——每个新城市必做）

```
Step 1: 搜索中文攻略
  → "{城市}美食攻略" / "{城市}必吃"
  → "{城市}住宿推荐" / "{城市}住哪里"
  → "{城市}景点 必去"
  → 记录出现的博客/网站URL

Step 2: 搜索台湾/香港博主
  → "{城市}自由行 美食 部落格"（繁体）
  → "{城市}攻略 推薦"（繁体）
  → 痞客邦搜索 "{城市}"

Step 3: 搜索日文
  → "{城市} グルメ ブログ おすすめ"
  → "{城市} 観光 ランキング"
  → tabelog.com 该城市页面

Step 4: 搜索英文
  → "best restaurants in {city} japan"
  → "best hotels in {city} japan blog"
  → "{city} japan travel guide"

Step 5: 整合
  → 去重
  → 评估每个新发现的网站的覆盖范围和可信度
  → 加入本目录
  → 标注获取方式（WebFetch/API/手动）
```

**不要跳过这个步骤。每个城市都有本地特色攻略站。**

---

## 八、可信度评级规则

| 数据来源 | 可信度 | 可否作为唯一来源 |
|----------|--------|----------------|
| Tabelog评分 | S级 |  可以（餐厅） |
| 米其林 | S级 |  可以（高端餐厅） |
| 携程Trip评分 | A级 |  可以（酒店） |
| 一休/楽天评分 | S级 |  可以（酒店） |
| Google Maps | A级 |  可以（景点坐标+评分） |
| japan-guide | S级 |  可以（景点） |
| Booking.com | A级 |  需配合其他源 |
| 小红书 | B级 |  必须交叉验证 |
| 攻略网站 | B级 |  必须交叉验证 |
| AI知识 | C级 |  绝不可以 |
