# 独立攻略站目录

> 提取自 docs/data-engineering/TOOLS_SETUP.md 4.5节
> 2026-04-02 基于关西四大品类采集实战更新（酒店375+精品店141+餐厅1099+POI261）
> 四大品类: 景=景点 餐=餐厅 宿=酒店 店=精品店

---

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
| 凯的日本食尚日记 | kaikk.tw | OpenCLI | 餐/店 | 美食/购物深度，大阪必吃18间+神户牛精选 |
| BringYou | bring-you.info | OpenCLI | 宿/景 | 京都Top30住宿 |
| TISS玩味食尚 | tisshuang.com | WebFetch | 餐(神戸牛) | 神户牛排专题最详尽，Mouriya百年老店等 |
| Sweet Bites甜點生活 | sweetbiteslab.com | WebFetch | 餐(甜品) | 京都法式甜点/咖啡厅专项 |
| 小布少爺 | boo2k.com | WebFetch | 餐 | 京都百年老店30+间+米其林餐厅 |
| 西北旅行社 | northwest-travel.com | WebFetch | 餐 | 京都/大阪高端怀石+米其林 |
| Wen the Travel Begins | wenthetravelbegins.com | WebFetch | 餐 | 大阪45+家实吃，英文，住大阪两个月 |

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
| Inside Kyoto | insidekyoto.com | WebFetch | 宿/景/店 | 京都住宿区域分析最权威英文指南+空庭テラス专文(insidekyoto.com/best-kyoto-restaurants返回404) |
| Inside Osaka | insideosaka.com | WebFetch | 宿/景/餐 | 同作者，大阪80+餐厅按菜系分类，best-osaka-restaurants可用 |
| Will Fly for Food | willflyforfood.net | WebFetch | 餐 | 大阪25家/京都实访食べ歩き，独立博客 |
| KyotoFoodie | kyotofoodie.com | WebFetch | 餐 | 京都饮食文化专项，两位长居京都作者 |
| Migrationology | migrationology.com | WebFetch | 餐 | 大阪平价到中档，知名美食旅行博主 |
| Japanese Food Guide | japanesefoodguide.com | WebFetch | 餐 | 道顿堀12家专项，在日10年加拿大籍 |
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