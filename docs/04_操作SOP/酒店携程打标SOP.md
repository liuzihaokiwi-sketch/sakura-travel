# 酒店携程分级打标 SOP（执行提示词）

> 给下一个 AI 执行者的完整指令。此任务全部工作都必须按本文档执行。

## 一、任务目标

把 `japan/kansai/assembly/hotels/data/hotels__kansai.json` 中 387 家酒店，按**携程原生分级（4档）+ 我们自加奢华档（1档）+ 体验型独立标签**重新打标，并**顺带采集评分/早餐/酒店类型等附加字段**（筛选一次就能拿到的信息全部收割）。

**交付物**：
1. 改后的 `hotels__kansai.json`：
   - `budget_tier` 字段从现有 `economy/mid/high/luxury` 改为 `economy/comfort/premier/luxury/ultra_luxury`
   - **列表层字段**（opencli record 抓列表 API 批量拿）
     - `experience_tags`（数组，可选，枚举：`onsen_ryokan / japanese_ryokan / shukubo / machiya / minshuku`）
     - `ctrip_rating`（浮点 0-5.0，综合评分）
     - `ctrip_hotel_type`（枚举：`hotel / ryokan / minshuku / hostel / resort / apartment`）
   - **详情层字段**（opencli record 抓详情页 API 或 WebFetch 兜底）
     - `opened_year`（整数，开业年——判断酒店新旧）
     - `renovated_year`（整数，最近翻新年——翻新后体验接近新酒店）
     - `room_count`（整数，房间数——小于 30 间通常是精品/设计酒店或温泉旅馆）
     - `rating_subscores`（对象：`{hygiene, facility, environment, service}` 浮点——辨别"综合 4.5 但服务差"这类品控陷阱）
     - `breakfast_highlight`（枚举：`excellent / value_for_money / none` —— `excellent` 早餐本身是体验亮点；`value_for_money` 性价比高值得推；`none` 普通不提。**只标有特色的**，不值得提的留空）
     - `kid_friendly`（布尔，儿童政策→true/false）
     - `free_shuttle`（布尔，有免费接站/班车）
     - `has_onsen_bath`（布尔，酒店内有温泉浴场）
     - `nearest_station`（字符串，最近地铁/JR站名）
     - `nearest_station_distance_m`（整数，米）
     - `review_keywords`（数组，好评关键词如"私汤舒适/景观很棒/亲子房/中文服务"——**最高价值字段**，直接对应"懂当地人会挑的理由"）
2. 打标依据记录：`scripts/hotel_ctrip_tagging_log.md` — 每家酒店在携程筛选结果里命中哪档的证据截图或酒店名清单

## 二、必读上下文

1. `CLAUDE.md` — 6 条红线特别是"数据真实性"：打标必须有证据，不推断
2. `docs/03_数据契约/SCHEMA.md` — `budget_tier` 枚举值修订需先改 SCHEMA 再改数据
3. 当前 `budget_tier` 分布：economy 126 / mid 154 / high 46 / luxury 61

## 三、核心原则（必读）

### 携程网页端分级（本项目采用）

截图已确认，携程京都酒店筛选页面的分级只有 4 档：

| 携程标签 | 新字段值 | 说明 |
|---|---|---|
| 2钻及以下\|经济 | `economy` | 快捷/青年旅舍 |
| 3钻\|舒适 | `comfort` | 中端连锁（原 `mid`） |
| 4钻\|高档 | `premier` | 高档精品（原 `high`） |
| 5钻\|豪华 | `luxury` | 豪华型（原 `luxury` 中的大部分） |

### 我们自加一档

| 新字段值 | 说明 | 装配规则 |
|---|---|---|
| `ultra_luxury` | 携程 5 钻里最顶端——¥80000 JPY+/人·泊、丽思/四季/星のや/翠岚/三井/Aman/Park Hyatt/Amanemu | **默认不入模板**，留客服奢华定制场景调用 |

**`ultra_luxury` 筛选规则**（二选一满足即可）：
- 品牌白名单：Ritz-Carlton / Four Seasons / Aman / Park Hyatt / Hoshinoya (星のや) / Suiran (翠岚) / HOTEL THE MITSUI / Amanemu / Six Senses / Bulgari
- 价格门槛：`price_range_jpy.low >= 60000`（人均一晚 ¥3000 CNY 起）

### 体验型独立标签（不替换 budget_tier，是附加字段）

从携程热门筛选直接复用：

| experience_tag | 携程对应 | 识别依据 |
|---|---|---|
| `onsen_ryokan` | 温泉 | area 在 arima_onsen/kinosaki_onsen/shirahama 或酒店名含"温泉" |
| `japanese_ryokan` | 日式旅馆 | 酒店名含「旅館」「旅馆」「庵」且非温泉乡 |
| `shukubo` | 宿坊 | area 在 koyasan_temple |
| `machiya` | 町家（京都专属） | city=kyoto 且 name 含「町家」「町屋」 |
| `minshuku` | 民宿/超赞民宿 | 携程筛选命中"民宿"或"超赞民宿" |

## 四、执行步骤（60 次筛选法）

### Step 1：SCHEMA 改动先于数据改动

先改 `docs/03_数据契约/SCHEMA.md`：

**改字段**：`budget_tier` 枚举
- 旧：`economy / mid / high / luxury`
- 新：`economy / comfort / premier / luxury / ultra_luxury`

**加字段**：
- 列表层：`experience_tags` / `ctrip_rating` / `ctrip_review_count` / `ctrip_hotel_type` / `breakfast`（详细枚举见 §一）
- 详情层：`opened_year` / `renovated_year` / `room_count` / `rating_subscores` / `kid_friendly` / `pet_allowed` / `free_shuttle` / `has_onsen_bath` / `nearest_station` / `nearest_station_distance_m` / `review_keywords`

改完后在 `docs/02_历史决策/DECISIONS.md` 追加 D41 条目（日期、为什么五档 budget_tier、为什么分列表层/详情层两批字段、review_keywords 为什么是最高价值字段）。

### Step 2：确认 opencli 浏览器桥接通

```bash
cd /d/projects/projects/travel-ai/opencli-main && node dist/main.js doctor
```

必须三行都 `[OK]`：
```
[OK] Daemon: running on port 19825
[OK] Extension: connected (v1.5.5+)
[OK] Connectivity: connected
```

**如果 Extension 未连接**：请用户打开 Chrome，确保 opencli Browser Bridge 扩展装了且启用。（扩展没装的话 record/explore 都跑不了）

### Step 3：用 explore 探一次携程列表页 API 结构

**这步是一次性的**——探明列表 API 的 endpoint + 参数 + 返回字段结构，之后脚本化调用不需要每次手动操作。

```bash
cd /d/projects/projects/travel-ai/opencli-main
node dist/main.js explore "https://hotels.ctrip.com/hotels/list?city=734" \
  --site ctrip_hotels --goal "列出京都酒店，抓钻级筛选 API 的 request/response 结构" \
  --wait 5 --click "5钻|豪华,4钻|高档,3钻|舒适,2钻及以下|经济" 2>&1 | tee /d/tmp/ctrip_explore_log.txt
```

- `--click` 让 opencli 自动点击 4 个钻级筛选，触发 4 次列表 API 请求
- 输出会包含：API URL / 请求参数 / 返回 JSON 字段结构
- 完成后读 `/d/tmp/ctrip_explore_log.txt` 找到列表 API 的 URL 模板（通常形如 `/restapi/soa2/xxxxx/HotelList`）

### Step 4：启动 record 补抓用户手动筛选

explore 可能漏掉某些筛选（如"温泉/日式旅馆"热门筛选）。启动 record 让用户手动点：

```bash
cd /d/projects/projects/travel-ai/opencli-main
node dist/main.js record "https://hotels.ctrip.com/hotels/list?city=734" \
  --site ctrip_hotels --out /d/tmp/ctrip_record --timeout 1800000 --poll 2000
```

（30 分钟 timeout；city=734 是京都；--out 指定抓包输出目录）

**给用户的操作指令原话**（不要改）：

> 浏览器已打开携程京都酒店列表页。请你按下面顺序各点一次（每次点完等列表刷新 3-5 秒再点下一个）：
>
> 1. 左侧「热门筛选」点「温泉」→ 等刷新
> 2. 清掉，点「日式旅馆」→ 等刷新
> 3. 清掉，点「民宿」→ 等刷新
> 4. 清掉，点「超赞民宿」→ 等刷新
>
> 然后**任选一家酒店点开详情页**，停留 5 秒让我抓详情页 API。
>
> 完成后告诉我，我停 record。

完成后：
```bash
ls /d/tmp/ctrip_record/
cat /d/tmp/ctrip_record/*.yaml
cat /d/tmp/ctrip_record/raw/*.json | head -200
```

### Step 4：让用户按下面清单在浏览器里操作

**给用户的指令原话**（不要改）：

> 浏览器已打开携程京都酒店列表页。请你按以下顺序操作：
>
> **京都站——**
> 1. 顶部搜索框定位到「京都站及周边」（或点左侧"位置"→"热门筛选"→"京都站及周边"）
> 2. 左侧"星级/钻级"点「5钻|豪华」→ 等列表刷新 → **把当前结果页滚动到底**（触发分页加载）
> 3. 点「4钻|高档」替换 5 钻筛选 → 滚到底
> 4. 点「3钻|舒适」替换 → 滚到底
> 5. 点「2钻及以下|经济」替换 → 滚到底
> 6. 清掉钻级筛选，点「热门筛选」→「温泉」→ 滚到底；清掉再点「日式旅馆」→ 滚到底；清掉再点「民宿」→ 滚到底
>
> **换京都其他区**（依次）：四条河原町 / 祇园 / 岚山 / 二条城 —— 每区重复上面 4 钻级 + 3 体验标签
>
> **换城市**（右上角重新搜）：大阪（各区：梅田/难波/心斋桥/本町/天王寺/海湾）/ 神户（三宫/北野/港区/南京町/海湾）/ 奈良（奈良公园）/ 有马温泉 / 城崎温泉 / 高野山 / 白浜
>
> 每档筛选完点「显示结果」后滚动到底，再换下一档。

### Step 5：生成脚本化调用（synthesize）

基于 explore + record 抓到的 API 结构，生成可脚本化的 YAML 命令：

```bash
cd /d/projects/projects/travel-ai/opencli-main
node dist/main.js synthesize ctrip_hotels --from /d/tmp/ctrip_record --out /d/tmp/ctrip_cli
```

这一步生成一套 `ctrip_hotels hotel-list` / `ctrip_hotels hotel-detail` 子命令，后续 60 次筛选不用再开浏览器：

```bash
# 示例：批量查询京都 5 钻豪华酒店
node dist/main.js ctrip_hotels hotel-list --city 734 --star 5 --format json > kyoto_luxury.json

# 示例：查单家酒店详情
node dist/main.js ctrip_hotels hotel-detail --id 705879 --format json > taketoritei.json
```

**关键字段映射**（对照我们要的 10 个字段）：

列表 API 通常返回：
- `hotelId` / `hotelName` / `hotelNameEn` → 匹配 387 家
- `starLevel` / `diamondLevel` → `budget_tier`
- `commentScore` → `ctrip_rating`
- `hotelType` → `ctrip_hotel_type`
- `tags` 数组可能含"温泉/日式旅馆" → `experience_tags`

详情 API 通常返回：
- `openYear` / `renovationYear` → `opened_year` / `renovated_year`
- `roomCount` / `totalRooms` → `room_count`
- `subScores` / `ratingDetails` 含 hygiene/facility/environment/service → `rating_subscores`
- `breakfastInfo` / `mealPlan` + 好评关键词含"早餐" → `breakfast_highlight`（需要人工判断或规则：评分>4.5 且关键词含"早餐棒/丰盛/好吃"→`excellent`；含"早餐划算/性价比"→`value_for_money`；其他→空）
- `kidPolicy` / `childFriendly` → `kid_friendly`
- `freeShuttle` / `transportService` → `free_shuttle`
- `hasOnsen` / `onsenFacility` → `has_onsen_bath`
- `nearestMetro` / `metroDistance` → `nearest_station` + `nearest_station_distance_m`
- `positiveCommentTags` / `reviewKeywords` → `review_keywords`

### Step 6：批量跑全量采集

写一个 shell 脚本，按（城市 × 钻级档 × 体验标签）组合批量调 opencli：

```bash
# scripts/fetch_ctrip_hotels.sh
CITIES=("734:京都" "2:大阪" "16:神户" "698:奈良" "732:有马" "733:城崎" "2027:高野山" "735:白浜")
STARS=(2 3 4 5)
TAGS=("温泉" "日式旅馆" "民宿" "超赞民宿")

for c in "${CITIES[@]}"; do
  cid="${c%%:*}"; cname="${c##*:}"
  for s in "${STARS[@]}"; do
    node dist/main.js ctrip_hotels hotel-list --city $cid --star $s \
      --format json > /d/tmp/ctrip_dump/${cname}_star${s}.json
    sleep 3  # 避免风控
  done
  for t in "${TAGS[@]}"; do
    node dist/main.js ctrip_hotels hotel-list --city $cid --tag "$t" \
      --format json > /d/tmp/ctrip_dump/${cname}_tag_${t}.json
    sleep 3
  done
done
```

运行约 15-20 分钟，产出 ~64 份 JSON。

### Step 7：匹配 + 打标 + 补详情

写 Python 脚本 `scripts/match_ctrip_to_hotels.py`：

1. 加载我们 387 家和携程 64 份 JSON
2. 按 `name_ja` / `name_zh` 做名称匹配（精确→去符号→substring）
3. 匹配上的酒店：
   - 从列表数据填 5 个列表层字段
   - 记录 `hotelId`，下一步批量调详情 API
4. 匹配不上的酒店标 `unverified` 留白
5. 对匹配上的酒店批量调 `hotel-detail`：

```bash
# 按 hotelId 列表批量跑
cat /d/tmp/matched_hotel_ids.txt | while read id; do
  node dist/main.js ctrip_hotels hotel-detail --id $id --format json \
    > /d/tmp/ctrip_details/$id.json
  sleep 2
done
```

6. 再跑一次 Python 脚本把详情字段合并到 `hotels__kansai.json`

### Step 6：匹配 387 家

对比 `hotels__kansai.json` 里的 `name_ja` / `name_zh` 和携程抓到的酒店名：

**匹配策略**（按优先级）：
1. 精确匹配 `name_ja` 或 `name_zh` 全字符串
2. 去掉空格/符号后再匹配
3. 用携程原文的关键名（如"丽思卡尔顿"/"四季"）做 substring 匹配
4. 找不到的酒店记到 `unmatched.md`，**不许自己推断**，留着下一步手工补

### Step 7：打标并更新 JSON

对每家匹配上的酒店：
- `budget_tier` 设为携程对应档（`economy / comfort / premier / luxury`）
- 触发 `ultra_luxury` 条件的（品牌白名单 OR 价格 ≥60000 JPY）覆盖为 `ultra_luxury`
- `experience_tags` 按 §三规则加标
- `ctrip_rating` 填携程评分（如 4.7）
- `ctrip_review_count` 填点评数（如 523）
- `breakfast` 从 breakfastInfo 字段判断（含"含早"→included / "可选"→optional / 其他→none）
- `ctrip_hotel_type` 从 hotelType 字段映射到我们五档枚举

对匹配不上的酒店（比如携程搜索没出现）：
- **保留原 budget_tier 不动**（从 `mid/high` 迁到 `comfort/premier` 等同义映射），在日志里标 `unverified`
- 评分/早餐/类型等字段**留空**不填（宁可少数据也不瞎猜）
- **不许瞎猜**——不确定的优先保守放低一档

### Step 8：交付

1. 改完 `hotels__kansai.json`
2. 跑 `python scripts/validate_template.py` 确认无破坏（validator 会检 budget_tier 枚举）
3. 粘完整 validate 输出到消息（禁止只口头说"跑过"）
4. 交付清单：
   - 五档分布数 `economy/comfort/premier/luxury/ultra_luxury` 每档多少家
   - `experience_tags` 命中数（每个 tag 多少家）
   - `ctrip_rating` / `breakfast` / `ctrip_hotel_type` 三个附加字段的覆盖率（填了的占比）
   - `unmatched.md` — 携程没抓到的酒店清单
   - `unverified` 标注的酒店数

## 五、硬规则（违反即返工）

1. **不许自己给酒店打钻级**——必须是携程筛选结果里见过的才打。没见过的走"保守降一档"路径。
2. **不许改 validator**——如果 validate 报错就修数据，不修 validator。
3. **不许批量找替换**——387 家一家一家核对，匹配不上就标 unmatched。
4. **人民币单位**——文档里所有价格统一人民币，日元在括号里补（全项目规范）。
5. **只汇报卡点**——每完成一个城市跑到 Step 4-7 时汇报一次，中间过程不要絮絮叨叨。

## 六、卡住怎么办

- **携程被风控**：换 trip.com 国际版（`hk.trip.com/hotels/kyoto-hotels-s734`）
- **opencli record 抓不到 API**：改用 WebFetch 爬携程静态筛选结果页
- **酒店名匹配率 <60%**：停下来汇报，不要硬推进，大概率是字段清洗问题

## 七、完成标准

- [ ] SCHEMA.md 加了新枚举
- [ ] DECISIONS.md 有 D41 条目
- [ ] 387 家每家都有明确 `budget_tier`（五档之一）
- [ ] 体验型酒店至少 50+ 家有 `experience_tags`
- [ ] 评分/早餐/酒店类型三字段覆盖率 ≥70%
- [ ] validate 87/87 PASS
- [ ] 匹配率 ≥80%，unmatched <80 家
- [ ] `ultra_luxury` 档预计 15-25 家（不会更多，关西真正奢华就这个量）
