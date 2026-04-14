# 数据采集工具设置与使用

> 版本: 2.0
> 更新: 2026-04-01

---

## 一、防止乱码规则

**所有文档和数据文件必须遵守以下规则，防止乱码:**

1. 文件编码统一使用 UTF-8 (无BOM)
2. 不使用 Unicode 特殊字符: 不用 -> 和 ├── 和 └── 等树形符号，改用 - 和 * 和缩进
3. 不使用 emoji (包括 checkmark 等符号)
4. JSON 文件写入后用 python 验证编码: `python -c "import json; json.load(open('file.json', encoding='utf-8'))"`
5. Markdown 文件写入后检查是否有乱码: `python -c "open('file.md', encoding='utf-8').read()"`
6. Windows 环境下 python 输出中文需要注意 GBK 编码问题，用 `2>&1 | cat` 或设置 `PYTHONIOENCODING=utf-8`
7. 用 `python` 而不是 `python3` (Windows 下 python3 指向 Store 安装器会弹窗)

---

## 二、工具总览

| 工具 | 用途 | 状态 |
|------|------|------|
| OpenCLI | 抓取任意网页(小红书/台湾站/日文站) | 已安装+扩展已连接 |
| WebFetch | Claude Code内置网页抓取 | 可用，部分网站被阻止 |
| WebSearch | Claude Code内置搜索 | 可用，中日英文均可 |
| Google Maps Places API | 坐标/评分/营业时间 | 需API Key |
| Rakuten Travel API | 酒店信息 | 需注册开发者 |

---

## 三、OpenCLI

### 3.1 项目位置

`d:/projects/projects/travel-ai/opencli-main/`

### 3.2 当前状态 (2026-04-01 验证通过)

```
opencli v1.5.6
Node.js: v24.13.0
Daemon: 运行中 (port 19825)
Chrome 扩展: 已连接 (v1.5.5)
```

### 3.3 Chrome 扩展安装

```
1. Chrome 打开 chrome://extensions/
2. 开启"开发者模式"
3. "加载已解压的扩展程序"
4. 选择 d:/projects/projects/travel-ai/opencli-main/extension
5. 确认扩展已启用
```

检查连接:
```bash
cd d:/projects/projects/travel-ai/opencli-main
node dist/main.js doctor
```

### 3.4 已验证可用的内置CLI命令

#### 小红书 (需要Chrome已登录小红书)

搜索笔记:
```bash
node dist/main.js xiaohongshu search "大阪美食推荐" --limit 20 -f json
```
输出: rank, title, author, likes, published_at, url

抓取单篇笔记:
```bash
node dist/main.js xiaohongshu note "<note-url-or-id>" -f json
```
输出: title, author, content, likes, collects, comments, tags

注意: 很多小红书图文笔记的正文在图片上，content 字段可能只有标签。需要结合 download 命令获取图片。

#### 携程 (公开数据)

搜索:
```bash
node dist/main.js ctrip search "大阪酒店" -f json
```

#### 其他可用命令

查看所有命令:
```bash
node dist/main.js list
```

### 3.5 探索新网站

```bash
# 分析网站结构
node dist/main.js explore "https://example.com/" --goal "描述你要找什么"

# 一键生成CLI
node dist/main.js generate "https://example.com/"

# 录制浏览器操作
node dist/main.js record "https://example.com/page"
```

### 3.6 适用场景

- 小红书: 用 xiaohongshu search/note 命令
- 台湾独立站 (.tw): WebFetch 被阻止，用 OpenCLI explore/record
- 香港站: 同上
- 日文网站: 部分 WebFetch 可用，不行就用 OpenCLI
- Tabelog 详情页: 用 OpenCLI 抓取评分和评论

---

## 四、全数据源访问方法清单 (2026-04-01 实测)

**这是跨城市圈复用的资产。** 新城市圈采集时直接参考本清单，不需要重新测试。

### 4.1 骨架源(景点)

| 数据源 | URL格式 | 获取方式 | 状态 |
|--------|---------|---------|------|
| japan-guide | japan-guide.com/e/e{id}.html | WebFetch | 可用 |
| JNTO | japan.travel/en/destinations/kansai/{city}/ | WebFetch | 可用 |
| TripAdvisor | tripadvisor.com/Attractions-g{id}-{City}.html | WebFetch | 可用 |

### 4.2 餐厅源

| 数据源 | URL格式 | 获取方式 | 状态 |
|--------|---------|---------|------|
| Tabelog排名 | tabelog.com/{prefecture}/rstLst/?SrtT=rt | WebFetch | 可用 |
| Tabelog菜系 | tabelog.com/{prefecture}/rstLst/{cuisine}/?SrtT=rt | WebFetch | 可用 |
| SAVOR JAPAN | savorjapan.com/ | WebFetch | 可用 |
| Retty | retty.me/ | WebFetch | 可用 |
| GURUNAVI | r.gnavi.co.jp/ | WebFetch | 可用 |

### 4.3 酒店源

| 数据源 | 获取方式 | 状态 | 备注 |
|--------|---------|------|------|
| 一休 ikyu.com | OpenCLI或WebSearch间接 | WebFetch被403 | 需generate CLI或用WebSearch搜排名 |
| 楽天Travel | OpenCLI或WebSearch间接 | WebFetch SSL错 | 需generate CLI |
| Booking.com | OpenCLI或WebSearch间接 | WebFetch JS阻止 | 需generate CLI |
| Google Maps | OpenCLI或WebSearch间接 | WebFetch JS阻止 | 坐标/评分/营业状态 |
| MICHELIN Guide | WebSearch | -- | 搜"MICHELIN Key {city}"获取名单 |

### 4.4 游客源

| 数据源 | 获取方式 | 命令 |
|--------|---------|------|
| 携程Trip.com | OpenCLI | `node dist/main.js ctrip search "{query}"` |
| 小红书 | OpenCLI | `node dist/main.js xiaohongshu search "{query}" --limit 20 -f json` |
| 小红书笔记 | OpenCLI | `node dist/main.js xiaohongshu note "{note-id}" -f json` |

### 4.5 独立攻略站(跨城市圈复用)

> 2026-04-02 更新: 基于关西酒店(395家)+精品店(141家)采集实战验证。
> 四大品类: 景=景点 餐=餐厅 宿=酒店 店=精品店

**台湾博主站(实住/实测体验最丰富):**

| 网站 | 域名 | 抓取方式 | 品类 | 实战价值 |
|------|------|---------|------|---------|
| Mimi韩 | mimigo.tw | OpenCLI web read | 宿/餐/景 | 京都27家/神户8家/有马12家酒店实住评测，价格+优缺点最详细 |
| 波比看世界 | bobbytravel.tw | OpenCLI web read | 宿 | 有马8家/神户12家实住，亲子视角 |
| 乐活的大方 | bigfang.tw | WebFetch | 宿 | 有马Top10地图+京都新开幕酒店，覆盖广 |
| 阿波旅行中 | april-travel-blog.com | OpenCLI web read | 宿 | 京都TOP20+大阪20间区域分析 |
| 熊猫爱吃鱼 | pandafishtravel.tw | OpenCLI web read | 宿 | 京都20间+大阪30+间，评分+价格齐全 |
| 小环妞 | wkitty.tw | OpenCLI web read | 宿 | 大阪18间实住，105KB详细内容 |
| 莉莉嗯 | lillian.tw | WebFetch | 宿 | 京都10间平价青旅/胶囊，TWD480起 |
| Let's go Kyoto | letsgokyoto.com | WebFetch(部分) | 宿 | 京都区域选择专题+20间分析+大阪14间 |
| Adventurous Mark | adventurousmark.tw | OpenCLI web read | 宿 | 京都34间+大阪29间，覆盖面最广 |
| Vivianexplore | vivianexplore.tw | OpenCLI web read | 宿 | 神户13间+有马8间 |
| kuolife | kuolife.com | OpenCLI web read | 宿 | 神户12间平价新开幕酒店 |
| Klook客路 | klook.com/zh-TW/blog | WebFetch被阻 | 宿/景 | 京都25间+有马12间(抓不到正文) |
| 乐吃购 | osaka.letsgojp.cn | WebFetch被403 | 全品类 | 京都30选+大阪27选+难波12选，信息量最大但抓不到 |
| 凯的日本食尚日记 | kaikk.tw | OpenCLI | 餐/店 | 美食/购物深度 |
| BringYou | bring-you.info | OpenCLI | 宿/景 | 京都Top30住宿 |

**香港站(价格敏感+独特视角):**

| 网站 | 域名 | 抓取方式 | 品类 | 实战价值 |
|------|------|---------|------|---------|
| HK01旅游 | hk01.com | OpenCLI(部分被阻) | 宿 | 京都新酒店25间+温泉酒店18间，港币价格 |
| U Travel | utravel.com.hk | WebSearch间接 | 宿 | 京都酒店12大推介 |
| DayDayTravel | daydaytravel.hk | robot challenge | 宿 | 15间京都酒店+旅馆(抓不到) |
| imtravelholic | imtravelholic.com | WebSearch间接 | 宿 | 京都新酒店42间+神户16间 |
| GoTrip | gotrip.hk | WebSearch间接 | 宿 | 京都酒店12间 |
| ELLE HK | elle.com.hk | WebFetch | 店 | 京都中古店6大必逛(2025)，奢侈品二手 |

**日文专业媒体(各品类的权威来源):**

| 网站 | 域名 | 抓取方式 | 品类 | 实战价值 |
|------|------|---------|------|---------|
| icotto | icotto.jp | WebFetch | 宿/餐/店 | 新开酒店17选+红叶酒店17选+料理旅馆8选+古着16选 |
| aumo | aumo.jp | WebSearch间接 | 宿/店 | 京都高级酒店22选+古着6选 |
| OZmall | ozmall.co.jp | WebSearch间接 | 宿 | 京都时尚酒店20选 |
| GOOD LUCK TRIP | gltjp.com | WebFetch | 宿/店 | 区域别推荐21选+中崎町攻略 |
| thisismedia | media.thisisgallery.com | OpenCLI web read | 店 | 京都古着22选+大阪古着12选，最详细的古着店指南 |
| VINTY | vinty.jp | WebSearch间接 | 店 | 古着屋/ヴィンテージ専門検索サイト |
| 古着屋巡りマップ MEGURU | furugi-meguru.com | WebSearch间接 | 店 | 関西古着屋マップガイド |
| CINRA | cinra.net | WebSearch間接 | 店 | 京都個性派書店特集 |
| ことりっぷ cottrip | co-trip.jp | OpenCLI web read | 店/宿 | 中崎町レトロ雑貨4選+京都紅葉温泉14選 |
| Hanako Web | hanako.tokyo | 可用 | 店 | 中崎町古着+雑貨特集(Hanako编辑精选) |
| F-STREET | f-street.org | 可用 | 店 | 古着/中古店门户(関西最全) |
| Recoya | recoya.net | WebSearch间接 | 店 | 京都レコードショップ49店舗ガイド |
| DRESS CODE. | fukulow.info | WebFetch | 店 | 京都古着屋9選(ヴィンテージ重視) |
| かんでんWITH YOU | media.kepco.co.jp | WebFetch | 店 | 京都雑貨8選+古着6選+独立書店ガイド+神戸雑貨7選 |
| 関西おでかけ手帖 | odekake.osakagas.co.jp | WebFetch(部分超時) | 宿/店 | 京都紅葉ホテル16選+京都料亭旅馆12選+京都町屋15選 |
| JAM TRADING | jamtrading.jp | WebFetch | 店 | 大阪アメ村古着屋40選マップ |
| Leaf KYOTO | leafkyoto.net | WebSearch間接 | 店 | 京都駅お土産16選+蚤の市12選 |

**日文OTA/予約サイト(评分+价格的权威):**

| 网站 | 域名 | 抓取方式 | 品类 | 实战价值 |
|------|------|---------|------|---------|
| 一休.com | ikyu.com | WebSearch間接 | 宿 | 体験型酒店排名+紅葉客室6選，403无法直接抓 |
| 楽天トラベル | travel.rakuten.co.jp | WebSearch間接 | 宿 | コスパ排名+城崎/有马排名 |
| じゃらん | jalan.net | WebSearch間接 | 宿 | 旅馆/温泉宿毎日排名 |
| マイベスト | my-best.com | WebSearch間接 | 宿 | 各エリア独自ランキング |
| JTB | jtb.co.jp | WebFetch | 宿 | 紅葉露天+温泉+懐石プラン検索 |
| Relux | rlx.jp | WebSearch間接 | 宿 | 城崎蟹旅馆6選+大浴場付京都10選 |

**英文编辑站(区域分析最透彻):**

| 网站 | 域名 | 抓取方式 | 品类 | 实战价值 |
|------|------|---------|------|---------|
| Inside Kyoto | insidekyoto.com | WebFetch | 宿/景/店 | 京都住宿区域分析最权威英文指南+空庭テラス专文 |
| Inside Osaka | insideosaka.com | WebFetch | 宿/景 | 同作者，大阪深度指南 |
| Japan Highlights | japanhighlights.com | WebFetch | 宿 | 区域分析+酒店推荐 |
| The Japan Travel Blog | thejapantravelblog.com | WebFetch | 宿 | 6区域分析 |
| Go Ask a Local | goaskalocal.com | WebFetch | 宿 | 本地人视角 |
| MATCHA | matcha-jp.com | 可用 | 景/店 | 多语言(10语言)日本旅游杂志 |
| LIVE JAPAN | livejapan.com | WebSearch間接 | 宿/店 | 综合旅游指南+秋季酒店12選 |
| Time Out | timeout.com | 可用 | 餐/店 | 国际城市指南日本版 |
| Japan Shopping Now | japanshopping.org | 可用 | 店 | 官方访日购物信息站 |

**中文综合站+社区:**

| 网站 | 域名 | 抓取方式 | 品类 | 实战价值 |
|------|------|---------|------|---------|
| 小红书 | xiaohongshu.com | OpenCLI search(note坏了) | 宿/店 | 真实住客价格+体验，搜索可用但笔记内容抓不到(2026-04) |
| 携程Trip.com | ctrip.com | OpenCLI ctrip search | 宿 | 中国游客销量+评分，搜索结果太泛适合验证阶段 |
| 知乎 | zhihu.com | WebFetch | 宿 | 京都住哪方便讨论+大阪中古店攻略 |
| 豆瓣 | douban.com | WebFetch | 店 | 京都私藏清单(咖啡/器皿/伴手礼) |
| 换乘案内の案内君 | anneijun.com | WebFetch | 宿 | 大阪百元档酒店16家，带CNY价格 |
| 日式温泉旅馆 | rishiluguan.com | WebSearch間接 | 宿 | 关西温泉旅馆排行+赏樱温泉 |
| WAmazing | tw.wamazing.com | WebFetch | 店 | 日本二手商店10間推荐 |

**权威评级(不可替代):**

| 来源 | 品类 | 获取方式 | 说明 |
|------|------|---------|------|
| MICHELIN Keys | 宿 | WebSearch | 体验型酒店最高权威，京都3Keys/2Keys/1Keys全覆盖 |
| MICHELIN Guide | 餐 | WebSearch | 餐厅星级+Bib Gourmand |
| Forbes Travel Guide | 宿 | WebSearch | 五星酒店评级 |
| Tabelog | 餐 | WebFetch(排名页可用) | 餐厅品质骨架源 |
| 百名店 | 餐 | WebSearch | Tabelog年度精选 |

**新开业/装修信息専門站:**

| 网站 | 域名 | 品类 | 说明 |
|------|------|------|------|
| ryokolink.com | ryokolink.com | 宿 | 各城市年度新开业酒店一览(最全) |
| kansai-sanpo.com | kansai-sanpo.com | 宿 | 関西新規開業ホテル(含リニューアル) |
| newaccom.com | newaccom.com | 宿 | 新しいホテル検索(神戸/奈良/全国) |
| nara-canoco.com | nara-canoco.com | 宿/景 | 奈良新スポット2025+開業情報 |

**市集/蚤の市専門:**

| 网站 | 域名 | 说明 |
|------|------|------|
| tedukuri-ichi.com | tedukuri-ichi.com | 百万遍手づくり市+梅小路手づくり市公式 |
| heiannominoichi.jp | heiannominoichi.jp | 平安蚤の市公式 |
| fmfm.jp | fmfm.jp | 全国フリマ・マルシェ・蚤の市ガイド |
| kyoto-1banchi.com | kyoto-1banchi.com | 京都蚤の市年間カレンダー |

### 4.6 被阻止站的替代方案汇总

| 被阻止 | 替代方案1 | 替代方案2 |
|--------|----------|----------|
| 一休(403) | OpenCLI generate | WebSearch "一休 {city} ランキング" |
| 楽天(SSL) | OpenCLI generate | WebSearch "楽天トラベル {city}" |
| Booking(JS) | OpenCLI generate | WebSearch "booking.com {city} top rated" |
| Google Maps(JS) | OpenCLI generate | Google Maps Places API(需Key) |
| BringYou(403) | OpenCLI | WebSearch "bring-you {city}" |
| TokyoCheapo(403) | WebSearch间接 | -- |
| LIVE JAPAN | WebSearch间接 | OpenCLI |

---

## 五、WebSearch (Claude Code 内置)

支持中日英文搜索。搜索词方法论详见 SEARCH_METHODOLOGY.md。

即使网站 WebFetch 被阻止，WebSearch 仍然能搜到该网站的摘要信息。

---

## 六、Google Maps Places API

### 用途
精确坐标、评分、评论数、营业时间、营业状态

### 费用
- Text Search: $17/1000 请求
- Place Details: $5/1000 请求
- 每城市建议控制 500 请求内 (约 $10)

### 省额度策略
- 优先用其他方式获取坐标 (官网/OSM/攻略站地图)
- 宝藏店铺类尽量不用 API
- Google API 主要用于: 批量坐标验证 + 营业状态确认

### 配置
```
环境变量: GOOGLE_MAPS_API_KEY
配置文件: .env
```

---

## 七、Rakuten Travel API

### 用途
酒店信息批量获取、评分、价格、空房

### 注册
开发者注册: https://webservice.rakuten.co.jp/

### API 文档
https://webservice.rakuten.co.jp/documentation/travel

---

## 八、工具选择决策

需要抓取网页内容:
- 网站需要登录 (小红书等) -> 用 OpenCLI
- WebFetch 能访问 -> 用 WebFetch (最方便)
- WebFetch 被阻止 -> 用 OpenCLI
- 只需要搜索摘要 -> 用 WebSearch

需要获取坐标/营业时间:
- 少量 (<20 条) -> Google Maps 手动搜索 (免费)
- 中量 (20-100 条) -> 先试官网/OSM，不够再用 API
- 大量 (>100 条) -> Google Maps Places API

需要获取酒店价格/评分:
- 日本酒店 -> Rakuten API + 一休 WebFetch/OpenCLI + 携程 WebFetch
- 国际酒店 -> Booking API + 携程 WebFetch

---

## 九、采集前检查清单

每次开始新城市圈采集前确认:

- [ ] OpenCLI daemon 运行中 (node dist/main.js doctor)
- [ ] Chrome 扩展已连接
- [ ] 小红书已在 Chrome 中登录
- [ ] Google Maps API Key 已配置 (如需使用)
- [ ] Rakuten Travel API 已注册 (如需使用)
- [ ] WebFetch/WebSearch 可正常使用
- [ ] python 命令可用 (不是 python3)
