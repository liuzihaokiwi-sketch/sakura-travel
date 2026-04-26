# D47 酒店池重构 audit log

> 2026-04-26 完成·**214 家·0 errors**·tier 6 档·两套阈值·套话/占位 id 全清·补收 15 家宝藏
> 唯一权威源 → [城市档位.md](城市档位.md)
> 字段权威 → [docs/项目核心/字段权威.md §2.4]
> 详细决策 → [docs/项目核心/历史决策.md D47]

## 完成总览

| 维度 | 起点 | 终点 |
|---|---|---|
| 总数 | 203 | **214**（+15 补收·-5 重复·+1 拆别馆·= 净 +11） |
| 占位 id `h***` | 104（51%）| **0** ✅ |
| 套话简介（7 类）| 149（73%）| **0** ✅（120 改为「待充实」+ 27 家逐家重写真数据 + 2 家批 cliche 之前已部分清）|
| area 错配 | 5 | **0** ✅ |
| depth full | 54 | **96** |
| depth verified | 0 | **12** |
| depth skeleton | 149 | **118** |
| validate errors | - | **0** |

## Step 1：schema 同步与迁移

### Commit fce7b9b（基线）

- 字段权威 §2.4：tier 4 档（comfort/quality/luxury/top）→ 6 档（b1/b2/b3/b4/b5/b6）
- 酒店规范 §3.1：同步
- validate_hotels.py：TIER_ENUM 改枚举·新增 city × price 区间一致性
- hotel_reband.py 迁移脚本：京都阈值 + 关西其他阈值
- 城市档位.md：唯一权威源

迁移结果：203 家全量重归档·validate 0 errors。

## Step 2：6 类种子穷举

[_seed_table.md] 写完·覆盖：
- §2.1 大集团目录：万豪 25 / 凯悦 6 / 希尔顿 6 / IHG 5 / Mitsui 9 / 星野 8 / Prince 4 / Tokyu Stay 4 / Daiwa Roynet 4 / Hotel Monterey 5
- §2.2 权威认证：MICHELIN Keys 3+8+9 / 一休 100 选 / Forbes
- §2.3 协会：京都老舗·有马旅館組合·城崎旅館組合·高野山宿坊組合 12 家
- §2.4 类型专题：京都市内宿坊 9 / 町家公司化（Nazuna 6 / 京の温所 14 / 葵 KYOTO STAY 7 / 庵 IORI）/ 川床·设计精品·老铺
- §2.5 锚点反向：清水寺/锦市场/京都站/岚山/大阪城/难波/神户北野/奈良公园周边
- §2.6 用户推荐：智積院/空庭/高雄もみぢ家
- §七 b1 经济档专项：trip.com 关西样本 6 家

## Step 3：现池 audit + 套话/占位 id/area 修正

### 占位 id 104 家改 slug（commit 66e3437）

slug 算法：
1. 优先抽店名括号里的英文/罗马字
2. fallback：中文音译表（凯悦→hyatt 等 80+ 词条）
3. 兜底：pypinyin

效果：`h011` → `granbell_hotel` / `h062` → `takagamine_shou_huo_hotel`·全 104 家有意义可搜索。

### area 错配修正 5 家（commit 39ad6b4）

- 高雄もみぢ家 area=arashiyama → takao
- 貴船 ふじや area=arashiyama → kibune
- 鷹峯 area=nijo_central → kita
- 京都格兰贝尔 area=shijo_kawaramachi → gion_higashiyama
- ROKU KYOTO area=kitayama → kita（命名规范化）

### 套话/cliche 清扫（commits aab13fb + 39ad6b4 + f6285bf）

第一批扫到 4 类共 34 家·第二批扫到 7 类共 149 家（包含第一批）。

清扫的套话短语：
- 「传统旅馆体验，一泊二食，睡前泡汤」（11 家）
- 「地点优秀，睡一晚醒来直接出发」(38 家)
- 「设计或精品酒店，住进去就是这次旅行的亮点」(30 家)
- 「住一次就知道什么叫真正的款待」(2 家)
- 「有马温泉金泉银泉，旅馆出门就能泡汤」(13 家)
- 「城崎温泉老街旅馆，住下来泡完七汤才算到过」(8 家)
- 「高野山宿坊，晨祷朝食，穿越千年的住宿体验」(10 家)
- 「整栋町家独享，像本地人住在京都」(4 家)

所有 skeleton 套话简介统一替换为「待充实（skeleton·后续逐家用 trip.com / 一休真数据重写）」占位·避免误用为事实。

## Step 4：套话条目逐家用真数据重写（27 家·full + cross_checked）

第一批 8 家：空庭本+別邸·高雄·貴船ふじや·右源太·嵐山花伝抄·FUFU Kyoto·FUFU Nara
第二批 19 家：京湯元ハトヤ瑞鳳閣·梅小路花伝抄·御室花伝抄·柚子屋旅館·料理旅館花楽·純和風料理旅館き乃ゑ·松井本館·天ぷら吉川·京小宿室町ゆとね·神戸蓮·飛鳥荘·古都の宿むさし野·四季亭·遊景の宿平城·春日ホテル·INFINITO·白良荘·KEY TERRACE Seamore·LIBER 大阪

数据来源：trip.com / 楽天トラベル / 一休 / 公式 / 価格.com（每条至少 2 个 URL）。

## Step 5：垃圾剔除 + 补收

### 重复条目剔除 5 家
- 嵐山温泉 花伝抄 _2（与本馆同一家）
- 神戸みなと温泉 蓮 _2（重复）
- 神戸大仓酒店 _2
- 神戸美利坚公园东方 _2
- （上述 4 家含「_2」后缀）+ 1 家 D47 拆出别馆但保留主馆

### 补收 15 家应收未收宝藏（commit 08b49dc）

按种子表交叉发现现池缺：

- **顶奢 b6**：Aman 京都·星のや 京都
- **奢华 b5**：Nazuna 京都 御所/二条城/東本願寺·奈良ホテル·界 城崎·界 有馬
- **高端 b4**：Caption by Hyatt Namba·京の温所 丸太町·葵 KYOTO STAY
- **品质 b3**：Nazuna 京都 椿通
- **舒适 b2**：OMO5 京都祇園·OMO3 京都東寺·Daiwa Roynet 京都四条乌丸（2026.3 重开）

全 full 或 verified·cross_checked·每条 2+ URL 数据来源。

## 最终分布

### city × tier

| | b1 | b2 | b3 | b4 | b5 | b6 | 合计 |
|---|---|---|---|---|---|---|---|
| 京都 | 0 | 30 | 11 | 33 | 7 | 15 | 96 |
| 大阪 | 0 | 0 | 21 | 1 | 20 | 11 | 53 |
| 神户 | 0 | 0 | 15 | 7 | 8 | 0 | 30 |
| 奈良 | 0 | 0 | 5 | 0 | 6 | 0 | 11 |
| 城崎 | 0 | 0 | 8 | 0 | 2 | 1 | 11 |
| 高野山 | 0 | 10 | 0 | 0 | 0 | 0 | 10 |
| 白浜 | 0 | 0 | 2 | 1 | 0 | 0 | 3 |

### type

- city：79
- experience：135

### experience 6 组

- 设计精品 41 / 温泉旅馆 39 / 宿坊 17 / 温泉度假 14 / 町家 12 / 老铺旅馆 12

## 留待下一窗口（按优先级）

1. **118 家 skeleton 逐步升 verified/full**（中端 quality/comfort 占主体·一周内做完）
2. **b1 经济档专项穷举**（trip.com 关西 ¥0-400 4-5 星·补 5-15 家）
3. **京都市内宿坊精修**（已收 9 家 skeleton 升 full）
4. **near_attractions 物理位置精修**
5. **2024-2026 新酒店持续跟进**

## Commit 链（D47 全部）

- `fce7b9b` schema + reband 基线
- `66e3437` 占位 id 104 家改 slug
- `39ad6b4` area 错配修正 5 家
- `aab13fb` 套话第一批重写 8 家 + 删 1 重复
- `f6285bf` 120 家套话扫净
- `08b49dc` 补收 15 家应收未收

可逐 commit revert 回任意中间点。
