# 关西餐厅覆盖审计报告

> 自动生成，勿手改。脚本：`scripts/audit_restaurants_coverage.py`


## 主场密集区


### 东山轴（主场密集）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 3 | 怀石 | dinner、lunch | must×3 | 0.0 |
| high | 5 | 天妇罗、寿司、怀石 | dinner、lunch | must×5 | 0.0 |
| mid | 5 | 寿司、怀石、豆腐 | breakfast、dinner、lunch | must×1 recommended×4 | 4.0 |
| economy | 4 | 乌冬、洋食 | dinner、lunch | must×1 none×1 recommended×2 | 3.0 |

**停留池**：共 1 条（full 1），类型：和菓子×1

**缺口分析**

- ✅ high: full=5 (目标 4~6)，随到随吃=0
- ❌ mid: full=5 (目标 8~12)，随到随吃=4.0
- ✅ economy: full=4 (目标 4~6)，随到随吃=3.0

**assembly 候选池**：87 条（restaurants__kyoto.json(87条)）


### 心斋桥（主场密集）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 1 | 烧肉 | dinner | must×1 | 0.0 |
| mid | 1 | 河豚 | dinner、lunch | recommended×1 | 1.0 |
| economy | 2 | 大阪烧、章鱼烧 | dinner、lunch | none×2 | 1.5 |

**停留池**：共 4 条（full 4），类型：当地土特产×3、设计杂货×1

**缺口分析**

- ❌ high: full=1 (目标 4~6)，随到随吃=0
- ❌ mid: full=1 (目标 8~12)，随到随吃=1.0
- ❌ economy: full=2 (目标 4~6)，随到随吃=1.5

**assembly 候选池**：37 条（restaurants__osaka.json(37条)）


### 梅田（主场密集）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 0 | — | — | — | 0.0 |
| economy | 4 | 乌冬、咖啡、甜品 | breakfast、cafe、lunch | none×4 | 3.5 |

**停留池**：共 5 条（full 5），类型：当地土特产×2、御宅店×2、设计杂货×1

**缺口分析**

- ❌ high: full=0 (目标 4~6)，随到随吃=0
- ❌ mid: full=0 (目标 8~12)，随到随吃=0
- ✅ economy: full=4 (目标 4~6)，随到随吃=3.5

**assembly 候选池**：100 条（restaurants__osaka.json(100条)）


### 河原町-先斗町（主场密集）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 1 | 怀石 | dinner、lunch | must×1 | 0.0 |
| high | 4 | 寿喜烧、居酒屋、拉面、法餐 | dinner、lunch | must×2 none×1 recommended×1 | 1.5 |
| mid | 2 | 寿司、鳗鱼 | dinner、lunch | recommended×2 | 2.0 |
| economy | 1 | 咖啡、洋食 | breakfast、lunch | none×1 | 1.0 |

**停留池**：共 1 条（full 1），类型：喫茶店×1

**缺口分析**

- ✅ high: full=4 (目标 4~6)，随到随吃=1.5
- ❌ mid: full=2 (目标 8~12)，随到随吃=2.0
- ❌ economy: full=1 (目标 4~6)，随到随吃=1.0

**assembly 候选池**：34 条（restaurants__kyoto.json(34条)）


### 烏丸御池（主场密集）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 2 | 怀石 | dinner、lunch | must×2 | 0.0 |
| high | 4 | 怀石、烧鸟 | dinner、lunch | must×3 recommended×1 | 1.0 |
| mid | 2 | 寿司、居酒屋 | dinner、lunch | recommended×2 | 2.0 |
| economy | 1 | 咖啡、洋食 | breakfast、lunch | none×1 | 1.0 |

**停留池**：0 条

**缺口分析**

- ✅ high: full=4 (目标 4~6)，随到随吃=1.0
- ❌ mid: full=2 (目标 8~12)，随到随吃=2.0
- ❌ economy: full=1 (目标 4~6)，随到随吃=1.0

**assembly 候选池**：85 条（restaurants__kyoto.json(85条)）


### 道顿堀（主场密集）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 2 | 乌冬、大阪烧 | dinner、lunch | none×1 recommended×1 | 2.0 |
| economy | 3 | 串炸、大阪烧、拉面 | dinner、lunch | none×3 | 2.5 |

**停留池**：共 2 条（full 1），类型：工艺品×1、当地土特产×1

**缺口分析**

- ❌ high: full=0 (目标 4~6)，随到随吃=0
- ❌ mid: full=2 (目标 8~12)，随到随吃=2.0
- ⚠️ economy: full=3 (目标 4~6)，随到随吃=2.5

**assembly 候选池**：46 条（restaurants__osaka.json(46条)）


### 难波（主场密集）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 0 | — | — | — | 0.0 |
| economy | 0 | — | — | — | 0.0 |

**停留池**：共 2 条（full 2），类型：设计杂货×1、道具屋×1

**缺口分析**

- ❌ high: full=0 (目标 4~6)，随到随吃=0
- ❌ mid: full=0 (目标 8~12)，随到随吃=0
- ❌ economy: full=0 (目标 4~6)，随到随吃=0

**assembly 候选池**：46 条（restaurants__osaka.json(46条)）


## 日归动线区


### ならまち（日归动线）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 0 | — | — | — | 0.0 |
| economy | 3 | 居酒屋、日本料理 | dinner、lunch | none×3 | 3.0 |

**停留池**：共 1 条（full 1），类型：咖啡×1

**缺口分析**

- ⚠️ high: full=0 (目标 1~2)，随到随吃=0
- ❌ mid: full=0 (目标 3~4)，随到随吃=0
- ✅ economy: full=3 (目标 2~3)，随到随吃=3.0

**assembly 候选池**：10 条（restaurants__nara.json(10条)）


### 中崎町（日归动线）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 0 | — | — | — | 0.0 |
| economy | 0 | — | — | — | 0.0 |

**停留池**：共 3 条（full 3），类型：书店咖啡×1、古着×1、当地土特产×1

**缺口分析**

- ⚠️ high: full=0 (目标 1~2)，随到随吃=0
- ❌ mid: full=0 (目标 3~4)，随到随吃=0
- ❌ economy: full=0 (目标 2~3)，随到随吃=0

**assembly 候选池**：0 条（无匹配）


### 京都站（日归动线）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 1 | 中华、烧肉 | dinner、lunch | recommended×1 | 1.0 |
| mid | 1 | 天妇罗 | dinner、lunch | recommended×1 | 1.0 |
| economy | 6 | 乌冬、咖啡、居酒屋、拉面、洋食 | breakfast、dinner、lunch | none×5 recommended×1 | 5.0 |

**停留池**：共 2 条（full 2），类型：和菓子×1、甜品×1

**缺口分析**

- ✅ high: full=1 (目标 1~2)，随到随吃=1.0
- ❌ mid: full=1 (目标 3~4)，随到随吃=1.0
- ✅ economy: full=6 (目标 2~3)，随到随吃=5.0

**assembly 候选池**：20 条（restaurants__kyoto.json(20条)）


### 伏见（日归动线）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 3 | 乌冬、居酒屋 | dinner、lunch | none×1 recommended×2 | 2.5 |
| economy | 1 | 乌冬、稻荷寿司、鳗鱼 | lunch | none×1 | 1.0 |

**停留池**：共 1 条（full 1），类型：日本酒×1

**缺口分析**

- ⚠️ high: full=0 (目标 1~2)，随到随吃=0
- ✅ mid: full=3 (目标 3~4)，随到随吃=2.5
- ⚠️ economy: full=1 (目标 2~3)，随到随吃=1.0

**assembly 候选池**：9 条（restaurants__kyoto.json(9条)）


### 北区（日归动线）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 2 | 怀石 | dinner、lunch | must×2 | 0.0 |
| high | 2 | 川床、怀石 | breakfast、dinner、lunch | must×1 recommended×1 | 1.0 |
| mid | 2 | 乌冬、居酒屋 | dinner、lunch | must×1 recommended×1 | 1.0 |
| economy | 1 | 拉面 | dinner、lunch | none×1 | 0.5 |

**停留池**：共 2 条（full 2），类型：和菓子×2

**缺口分析**

- ✅ high: full=2 (目标 1~2)，随到随吃=1.0
- ⚠️ mid: full=2 (目标 3~4)，随到随吃=1.0
- ⚠️ economy: full=1 (目标 2~3)，随到随吃=0.5

**assembly 候选池**：10 条（restaurants__kobe.json(4条)、restaurants__kyoto.json(6条)）


### 堀江（日归动线）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 0 | — | — | — | 0.0 |
| economy | 0 | — | — | — | 0.0 |

**停留池**：共 1 条（full 1），类型：手工艺×1

**缺口分析**

- ⚠️ high: full=0 (目标 1~2)，随到随吃=0
- ❌ mid: full=0 (目标 3~4)，随到随吃=0
- ❌ economy: full=0 (目标 2~3)，随到随吃=0

**assembly 候选池**：0 条（无匹配）


### 天满（日归动线）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 0 | — | — | — | 0.0 |
| economy | 0 | — | — | — | 0.0 |

**停留池**：共 3 条（full 3），类型：咖啡×1、喫茶店×1、当地土特产×1

**缺口分析**

- ⚠️ high: full=0 (目标 1~2)，随到随吃=0
- ❌ mid: full=0 (目标 3~4)，随到随吃=0
- ❌ economy: full=0 (目标 2~3)，随到随吃=0

**assembly 候选池**：17 条（restaurants__osaka.json(17条)）


### 天王寺-新世界（日归动线）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 0 | — | — | — | 0.0 |
| economy | 1 | 串炸 | dinner、lunch | none×1 | 0.5 |

**停留池**：共 4 条（full 4），类型：喫茶店×2、手工艺×1、甜品×1

**缺口分析**

- ⚠️ high: full=0 (目标 1~2)，随到随吃=0
- ❌ mid: full=0 (目标 3~4)，随到随吃=0
- ⚠️ economy: full=1 (目标 2~3)，随到随吃=0.5

**assembly 候选池**：8 条（restaurants__osaka.json(8条)）


### 奈良公园（日归动线）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 2 | 怀石 | dinner、lunch | must×2 | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 2 | 甜品、荞麦 | cafe、lunch | none×2 | 1.0 |
| economy | 1 | 拉面 | dinner、lunch | none×1 | 0.5 |

**停留池**：共 3 条（full 3），类型：和菓子×1、当地土特产×1、茶寮×1

**缺口分析**

- ⚠️ high: full=0 (目标 1~2)，随到随吃=0
- ⚠️ mid: full=2 (目标 3~4)，随到随吃=1.0
- ⚠️ economy: full=1 (目标 2~3)，随到随吃=0.5

**assembly 候选池**：61 条（restaurants__nara.json(61条)）


### 姬路城周边（日归动线）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 1 | 怀石 | dinner、lunch | recommended×1 | 1.0 |
| mid | 0 | — | — | — | 0.0 |
| economy | 1 | 日本料理 | cafe、lunch | none×1 | 1.0 |

**停留池**：共 3 条（full 2），类型：咖啡×1、当地土特产×1、抹茶×1

**缺口分析**

- ✅ high: full=1 (目标 1~2)，随到随吃=1.0
- ❌ mid: full=0 (目标 3~4)，随到随吃=0
- ⚠️ economy: full=1 (目标 2~3)，随到随吃=1.0

**assembly 候选池**：0 条（无匹配）


### 岚山（日归动线）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 1 | 怀石 | dinner、lunch | must×1 | 0.0 |
| high | 5 | 怀石、法餐、精进料理、豆腐 | dinner、lunch | must×2 recommended×3 | 3.0 |
| mid | 0 | — | — | — | 0.0 |
| economy | 0 | — | — | — | 0.0 |

**停留池**：共 2 条（full 2），类型：咖啡×1、茶寮×1

**缺口分析**

- ✅ high: full=5 (目标 1~2)，随到随吃=3.0
- ❌ mid: full=0 (目标 3~4)，随到随吃=0
- ❌ economy: full=0 (目标 2~3)，随到随吃=0

**assembly 候选池**：9 条（restaurants__kyoto.json(9条)）


### 日本桥（日归动线）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 0 | — | — | — | 0.0 |
| economy | 0 | — | — | — | 0.0 |

**停留池**：共 2 条（full 2），类型：御宅店×2

**缺口分析**

- ⚠️ high: full=0 (目标 1~2)，随到随吃=0
- ❌ mid: full=0 (目标 3~4)，随到随吃=0
- ❌ economy: full=0 (目标 2~3)，随到随吃=0

**assembly 候选池**：0 条（无匹配）


### 池田（日归动线）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 0 | — | — | — | 0.0 |
| economy | 0 | — | — | — | 0.0 |

**停留池**：共 2 条（full 1），类型：喫茶店×1、工艺品×1

**缺口分析**

- ⚠️ high: full=0 (目标 1~2)，随到随吃=0
- ❌ mid: full=0 (目标 3~4)，随到随吃=0
- ❌ economy: full=0 (目标 2~3)，随到随吃=0

**assembly 候选池**：0 条（无匹配）


### 神户三宮-旧居留地（日归动线）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 3 | 寿司、怀石、烧肉 | dinner、lunch | must×2 recommended×1 | 1.0 |
| high | 1 | 烧肉 | dinner | recommended×1 | 1.0 |
| mid | 3 | 洋食、荞麦 | dinner、lunch | none×2 recommended×1 | 3.0 |
| economy | 1 | 拉面 | dinner、lunch | none×1 | 0.5 |

**停留池**：共 3 条（full 3），类型：咖啡×1、喫茶店×1、甜品×1

**缺口分析**

- ✅ high: full=1 (目标 1~2)，随到随吃=1.0
- ✅ mid: full=3 (目标 3~4)，随到随吃=3.0
- ⚠️ economy: full=1 (目标 2~3)，随到随吃=0.5

**assembly 候选池**：0 条（无匹配）


### 神户北野-元町（日归动线）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 2 | 法餐、烧肉 | dinner、lunch | recommended×2 | 2.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 2 | 居酒屋、洋食 | dinner、lunch | recommended×2 | 2.0 |
| economy | 0 | — | — | — | 0.0 |

**停留池**：共 2 条（full 1），类型：古道具×1、甜品×1

**缺口分析**

- ⚠️ high: full=0 (目标 1~2)，随到随吃=0
- ⚠️ mid: full=2 (目标 3~4)，随到随吃=2.0
- ❌ economy: full=0 (目标 2~3)，随到随吃=0

**assembly 候选池**：0 条（无匹配）


### 美国村（日归动线）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 0 | — | — | — | 0.0 |
| economy | 0 | — | — | — | 0.0 |

**停留池**：共 3 条（full 3），类型：古着×3

**缺口分析**

- ⚠️ high: full=0 (目标 1~2)，随到随吃=0
- ❌ mid: full=0 (目标 3~4)，随到随吃=0
- ❌ economy: full=0 (目标 2~3)，随到随吃=0

**assembly 候选池**：0 条（无匹配）


## 温泉宿坊区


### 城崎温泉（温泉宿坊）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 1 | 日本料理 | dinner | must×1 | 0.0 |
| high | 1 | 烧肉 | dinner、lunch | recommended×1 | 1.0 |
| mid | 0 | — | — | — | 0.0 |
| economy | 1 | 日本料理 | lunch | none×1 | 1.0 |

**停留池**：共 3 条（full 3），类型：和菓子×1、工艺品×1、当地土特产×1

**缺口分析**

- ✅ high: full=1 (目标 0~0)，随到随吃=1.0
- ⚠️ mid: full=0 (目标 1~2)，随到随吃=0
- ✅ economy: full=1 (目标 1~1)，随到随吃=1.0

**assembly 候选池**：0 条（无匹配）


### 有马温泉（温泉宿坊）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 2 | 日本料理 | lunch | none×2 | 2.0 |
| economy | 1 | 日本料理 | lunch | none×1 | 1.0 |

**停留池**：共 2 条（full 2），类型：工艺品×1、当地土特产×1

**缺口分析**

- ✅ high: full=0 (目标 0~0)，随到随吃=0
- ✅ mid: full=2 (目标 1~2)，随到随吃=2.0
- ✅ economy: full=1 (目标 1~1)，随到随吃=1.0

**assembly 候选池**：0 条（无匹配）


### 高野山（温泉宿坊）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 1 | 精进料理 | dinner、lunch | must×1 | 0.0 |
| high | 1 | 精进料理 | lunch | recommended×1 | 1.0 |
| mid | 0 | — | — | — | 0.0 |
| economy | 1 | 日本料理 | cafe、lunch | none×1 | 1.0 |

**停留池**：共 3 条（full 2），类型：和菓子×1、咖啡×1、工艺品×1

**缺口分析**

- ✅ high: full=1 (目标 0~0)，随到随吃=1.0
- ⚠️ mid: full=0 (目标 1~2)，随到随吃=0
- ✅ economy: full=1 (目标 1~1)，随到随吃=1.0

**assembly 候选池**：0 条（无匹配）


## 景点单日区


### USJ（景点单日）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 0 | — | — | — | 0.0 |
| economy | 0 | — | — | — | 0.0 |

**停留池**：共 1 条（full 1），类型：当地土特产×1

**缺口分析**

- ✅ high: full=0 (目标 0~0)，随到随吃=0
- ❌ mid: full=0 (目标 2~2)，随到随吃=0
- ❌ economy: full=0 (目标 2~2)，随到随吃=0

**assembly 候选池**：11 条（restaurants__osaka.json(11条)）


### 吉野山（景点单日）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 2 | 寿司、山菜料理、精进料理 | dinner、lunch | recommended×2 | 1.5 |
| economy | 4 | 日本料理、甜品、稻荷寿司 | cafe、lunch | none×4 | 4.0 |

**停留池**：共 6 条（full 5），类型：和菓子×2、当地土特产×3、茶寮×1

**缺口分析**

- ✅ high: full=0 (目标 0~0)，随到随吃=0
- ✅ mid: full=2 (目标 2~2)，随到随吃=1.5
- ✅ economy: full=4 (目标 2~2)，随到随吃=4.0

**assembly 候选池**：0 条（无匹配）


### 大阪城（景点单日）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 0 | — | — | — | 0.0 |
| economy | 0 | — | — | — | 0.0 |

**停留池**：共 2 条（full 2），类型：咖啡×2

**缺口分析**

- ✅ high: full=0 (目标 0~0)，随到随吃=0
- ❌ mid: full=0 (目标 2~2)，随到随吃=0
- ❌ economy: full=0 (目标 2~2)，随到随吃=0

**assembly 候选池**：0 条（无匹配）


### 天保山（景点单日）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 0 | — | — | — | 0.0 |
| economy | 0 | — | — | — | 0.0 |

**停留池**：共 1 条（full 1），类型：咖啡×1

**缺口分析**

- ✅ high: full=0 (目标 0~0)，随到随吃=0
- ❌ mid: full=0 (目标 2~2)，随到随吃=0
- ❌ economy: full=0 (目标 2~2)，随到随吃=0

**assembly 候选池**：0 条（无匹配）


### 天桥立-伊根（景点单日）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 1 | 日本料理 | dinner | must×1 | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 4 | 寿司、日本料理、海鲜、荞麦 | dinner、lunch | none×2 recommended×2 | 4.0 |
| economy | 1 | 日本料理 | lunch | none×1 | 1.0 |

**停留池**：共 6 条（full 6），类型：和菓子×1、咖啡×2、当地土特产×3

**缺口分析**

- ✅ high: full=0 (目标 0~0)，随到随吃=0
- ✅ mid: full=4 (目标 2~2)，随到随吃=4.0
- ⚠️ economy: full=1 (目标 2~2)，随到随吃=1.0

**assembly 候选池**：0 条（无匹配）


### 新地（景点单日）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 2 | 寿司、法餐 | dinner、lunch | must×2 | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 0 | — | — | — | 0.0 |
| economy | 0 | — | — | — | 0.0 |

**停留池**：0 条

**缺口分析**

- ✅ high: full=0 (目标 0~0)，随到随吃=0
- ❌ mid: full=0 (目标 2~2)，随到随吃=0
- ❌ economy: full=0 (目标 2~2)，随到随吃=0

**assembly 候选池**：0 条（无匹配）


### 熊野古道（景点单日）

**正餐 full 矩阵**

| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |
|---|---|---|---|---|---|
| showcase | 0 | — | — | — | 0.0 |
| high | 0 | — | — | — | 0.0 |
| mid | 2 | 居酒屋、日本料理 | dinner、lunch | recommended×2 | 2.0 |
| economy | 2 | 日本料理 | lunch | none×2 | 2.0 |

**停留池**：共 3 条（full 3），类型：和菓子×1、工艺品×1、当地土特产×1

**缺口分析**

- ✅ high: full=0 (目标 0~0)，随到随吃=0
- ✅ mid: full=2 (目标 2~2)，随到随吃=2.0
- ✅ economy: full=2 (目标 2~2)，随到随吃=2.0

**assembly 候选池**：0 条（无匹配）
