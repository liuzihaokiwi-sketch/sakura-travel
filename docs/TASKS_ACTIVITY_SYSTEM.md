# 活动簇系统：问题清单与任务规划

> 最后更新: 2026-03-29

---

## 一、当前问题总览

### P0：阻塞性问题（不修会导致生成失败）

#### 1. 活动簇→实体绑定缺失

**现象**：329个活动簇入库了，1581+个实体入库了，但两者之间没有关联。决策链选中"河口湖·富士景观温泉驻留线"后，去 DB 找实体时找不到富士山。

**根因**：实体采集按 city_code 盲拉（"给我东京的寺庙"），活动簇按旅行逻辑定义（"富士山观景线"包含河口湖+富士五合目+天上山缆车"）。两套数据独立生成，没有从活动簇反推需要哪些实体。

**典型案例**：
- 东京圈"富士山观景线" → DB 里没有富士山实体（不在 tokyo 市内）
- 关西圈"姬路城日归" → himeji 不在采集城市列表里
- 北海道"知床自然线" → shiretoko 的 POI 可能没被拉到
- 活动簇 notes 写"清水寺→二年坂→八坂神社"，但 DB 里的京都 POI 是一堆随机的小景点

**影响**：activity_cluster 选中 → route_skeleton 安排 → fill_secondary 找实体 → 找不到 → 行程空洞

---

### P1：影响质量的问题

#### 2. 北海道/九州 B 级 buffer 活动严重不足

| 圈 | B 级数量 | B 占比 | 问题 |
|---|---|---|---|
| 北海道 | 3 | 10% | 没有足够的恢复/缓冲活动来穿插在 peak 之间 |
| 九州 | 3 | 14% | 同上 |
| 中部 | 6 | 20% | 勉强够用 |
| 关西 | 6 | 20% | 勉强够用 |

节奏编排的硬规则是"peak 后必须跟 recovery 或 contrast"，但如果 B 级池子只有 3 个，很快就会用完或重复。

**需要补充的方向**：
- 温泉街散步线（别府铁轮、登别、由布院已有，但北海道缺定山溪/洞爷散步）
- 车站/商圈购物补位线
- 夜宵/居酒屋补位线
- 咖啡/甜品下午茶线
- 市场/朝市补位线

#### 3. 体验类型分布不均

shrine（寺社）和 citynight（都市夜景）加起来占 30%+。一个跨两个圈的用户（如关西+中部）很容易连续出现"又是寺庙""又是夜景"。

**需要重新审视的**：
- 部分 shrine 可能更适合标为 locallife（如"二条城+西阵织会馆"是文化体验不只是寺社）
- 部分 citynight 可能更适合标为 food（如"博多屋台夜食文化线"主角是吃不是夜景）

#### 4. 关西圈旧 seed 数据混乱

关西圈的数据分散在 4 个文件里（seed_kansai_circle.py / seed_kansai_extended_circles.py / seed_kansai_supplemental_clusters.py / seed_kansai_v2_clusters.py），导致：
- 部分活动缺 city_code（旧数据）
- 部分活动缺 experience_family/rhythm_role/energy_level（旧数据）
- 有重复和矛盾（如 Luminarie 出现两次，USJ 同时在 S 和 B 级）
- 酒店住法预设混入了活动列表

#### 5. 缺少到达日/离开日/雨天备选标记

没有一个活动簇明确标注"这是到达日适合的轻活动"或"这是雨天的室内替代"。

当前只有北疆的"乌鲁木齐集散缓冲线"做了到达日标记。博物馆线、购物线、室内市场线天然适合雨天，但没有系统标记。

#### 6. 缺冲绳圈完整活动簇

冲绳在 seed_all_circles.py 里只有 7 个基础簇，没有在 mojor/ 里补充过。作为日本热门度假圈，至少需要 15-20 个。

#### 7. 缺广东圈（潮汕）

完全没有活动簇数据。

---

### P2：优化项

#### 8. 亲子活动线不足

只有主题乐园（USJ/迪士尼/长隆/三丽鸥），缺非乐园型亲子活动：
- 动物园/水族馆专线（旭山动物园已有，但海游馆只是大阪城市线的一部分）
- 科技馆/博物馆亲子线
- 手工体验线（陶艺/和菓子制作/扎染等）
- 农场/牧场体验线

#### 9. 购物专线覆盖不足

大阪心斋桥、银座、表参道、香港海港城/铜锣湾这类强购物目的地，要么缺要么只是 B 级。对购物型用户来说，这些可能是 A 级甚至 S 级。

#### 10. 季节活动可以更细

- 大阪造币局樱花通（关西樱花季没有独立出来）
- 东京高尾山红叶（标的是 mountain 不是 flower，节奏编排时不会被当作花景处理）
- 京都夜樱/夜枫特别开放（当前樱花/红叶总线没有区分白天版和夜间版）

---

## 二、修复任务

### Task 1：活动簇→实体绑定（P0）

**目标**：每个 S/A 级活动簇的核心景点在 DB 里都有对应实体，且建立了 circle_entity_roles 关联。

**方案**：给 ActivityCluster 加 `anchor_entities` JSONB 字段，直接声明每个簇需要的核心实体。

```python
# 数据示例
anchor_entities: [
    {"name": "富士山五合目", "type": "poi", "role": "anchor"},
    {"name": "河口湖", "type": "poi", "role": "anchor"},
    {"name": "天上山缆车", "type": "poi", "role": "secondary"},
    {"name": "浅间神社", "type": "poi", "role": "secondary"},
]
```

**为什么选这个方案而不是从 notes 反推**：
- 生成活动簇时顺便让 AI 输出 anchor_entities，问"这个活动需要哪些景点"比"从描述里提取景点名"准确得多
- 结果持久化到字段里，bootstrap 脚本直接读，不用每次重新调 AI
- notes 里可能没写的景点（如"富士山"只是描述性出现），anchor_entities 里一定会有

**步骤**：

```
1. ActivityCluster 加 anchor_entities JSONB 字段（nullable，migration）

2. 给现有 329 个活动簇补 anchor_entities
   - 由执行任务的 AI（Claude Opus 4.6）直接完成
   - 读 name_zh + notes + city_code，输出每个簇的核心实体列表
   - 不需要额外调 GPT，Claude Opus 4.6 有足够的地理知识
   - 执行模式：不开 thinking（任务明确，不需要长推理，直接输出结构化数据）

3. 对比 DB 找缺口
   - 拿 anchor_entities 里的 name vs entity_base.name_zh
   - 输出：缺失实体列表，S 级活动簇的最优先

4. 定向生成缺失实体
   - 调 AI 按名字精确生成（"给我富士山五合目的详细数据"）
   - 写入 entity_base + pois/restaurants/hotels 子表

5. 自动建立 cluster → entity 绑定
   - 从 anchor_entities 读 name → 匹配 entity_base.name_zh → 写入 circle_entity_roles
```

**AI 执行规范**：
- 模型：Claude Opus 4.6（地理知识准确，结构化输出稳定）
- Thinking 模式：关闭（任务是结构化数据填充，不需要长链推理）
- 每次处理一个城市圈的所有活动簇（约 20-60 个），避免上下文过长
- 输出格式：直接输出可入库的 JSON，不需要解释

**产出文件**：
- Migration: `20260329_anchor_entities_field.py`
- `scripts/populate_anchor_entities.py`（补字段）
- `scripts/sync_entity_gaps.py`（找缺口 + 定向生成 + 绑定，合为一个脚本）

**验收**：
- 每个 S 级活动簇的 anchor_entities 非空
- anchor_entities 里的每个实体在 entity_base 里都有对应记录
- 每个 S 级活动簇至少有 2 个 anchor_poi 在 circle_entity_roles 里

---

### Task 2：补北海道/九州 B 级 buffer（P1）

**目标**：北海道 B 级从 3→8，九州 B 级从 3→8。

**北海道需要补**：
- 札幌·狸小路商店街购物线 (B, locallife, utility, low)
- 札幌·二条市场朝食线 (B, food, utility, low)
- 函馆·金森红砖仓库购物线 (B, locallife, utility, low)
- 小樽·寿司屋通美食线 (B, food, recovery, low)
- 温泉旅馆·一泊二食休息线 (B, onsen, recovery, low)

**九州需要补**：
- 别府·铁轮温泉街散步线（已有但确认入库）
- 福冈·天神地下街购物线（已有但确认入库）
- 鹿儿岛·天文馆通美食线（已有但确认入库）
- 由布院·�的之坪手工艺甜品街线 (B, locallife, recovery, low)
- 长崎·新地中华街美食补位线 (B, food, utility, low)

---

### Task 3：清理关西圈数据（P1）

**目标**：关西圈从 4 个分散的 seed 文件统一为 1 个权威源。

**步骤**：
1. 合并 4 个文件的数据，去重
2. 修正所有缺失的 city_code / experience_family / rhythm_role / energy_level
3. 修正等级矛盾（USJ 不能同时是 S 和 B）
4. 删除混入的非活动数据（酒店住法预设）
5. 输出一个统一的 `scripts/seed_kansai_unified_clusters.py`

---

### Task 4：加到达日/雨天标记（P1）

在 ActivityCluster 上加两个 tag 字段（或复用现有 JSONB 字段）：

```python
# 方案 A：在现有 profile_fit JSONB 里加标签
profile_fit: ["arrival_friendly", "rainy_day_ok", ...]

# 方案 B：在 notes 里约定格式
notes: "...。[标签: 到达日适合, 雨天可用]"

# 方案 C：新增字段（最干净但改动最大）
arrival_friendly: bool    # 到达日/离开日适合（半天、不累、离车站近）
indoor_friendly: bool     # 雨天可用（全室内或主要室内）
```

推荐方案 A，改动最小，profile_fit 本身就是标签列表。

---

### Task 5：补冲绳圈（P2）

需要约 15-20 个活动簇，覆盖：
- 那霸市区：国际通、首里城、波上宫
- 北部：美丽海水族馆、古宇利岛、名护菠萝园
- 中部：美国村、残波岬、万座毛
- 南部：斋场御�的、知念岬、玉泉洞
- 离岛：庆良间浮潜、座间味、�的嘉敷
- 季节：海开（4月）、花火、冬季�的鱼

---

### Task 6：体验类型重标记（P2）

审核所有 shrine 和 citynight 标记的活动，判断是否需要重新归类：

| 当前标记 | 活动 | 建议改为 |
|---------|------|---------|
| shrine | 京都·二条城+西阵织会馆 | locallife（文化体验不只是寺社） |
| shrine | 高山·春秋祭季节线 | flower（季节节庆更准确） |
| citynight | 福冈·博多屋台夜食文化线 | food（主角是吃） |
| citynight | 广州·琶醍江边夜生活线 | 保持 citynight（主角是夜生活） |
| shrine | 大阪·天神祭船渡御烟花线 | flower 或新增 festival 类型 |

---

## 三、未来新城市圈的自动化流程

### 设计原则：人工只做决策，不做执行

**人工参与**：决定做哪个圈、审核最终输出、提供图片素材
**全自动**：活动簇生成、质量检查、实体采集、绑定、知识包、验证

### 一条命令搞定一个新城市圈

```bash
python scripts/bootstrap_circle.py --circle okinawa_island \
    --name-zh "冲绳海岛圈" \
    --base-cities naha \
    --extension-cities ishigaki,miyako,kerama \
    --region japan
```

这个脚本自动执行以下所有步骤，无需人工介入（除非报错）：

---

#### Step 1：自动定义城市圈（脚本执行）

- 检查 circle_id 是否全局唯一
- 检查所有 city_code 在 CITY_MAP 里存在（不存在则自动加入）
- 写入 city_circles 表

#### Step 2：自动生成活动簇 + anchor_entities（AI 生成 + 自动校验）

由 Claude Opus 4.6 直接生成活动簇数据，**同时输出 anchor_entities**。

prompt 模板：
```
对于每个活动簇，除了标准字段外，还需要输出 anchor_entities：
该活动线路涉及的所有具体景点/餐厅名称，每个标注 type(poi/restaurant/hotel) 和 role(anchor/secondary)。
```

**自动校验规则**（生成后立即检查，不合格自动修复或重试）：
```python
def validate_clusters(clusters: list[dict]) -> list[str]:
    errors = []
    # 1. city_code 必须在 CITY_MAP
    # 2. 必须有 experience_family / rhythm_role / energy_level
    # 3. B 级占比 >= 20%
    # 4. experience_family 分布：任一类型不超过 35%
    # 5. 至少 1 个 arrival_friendly（到达日适合）
    # 6. notes 非空且 >= 20 字
    # 7. seasonality 非空
    # 8. 无重复 cluster_id
    # 9. anchor_entities 非空且每个有 name/type/role
    # 10. S 级簇的 anchor_entities >= 3 个
    return errors
```

**AI 执行规范**：
- 模型：Claude Opus 4.6（地理知识准确，结构化输出稳定）
- Thinking 模式：关闭（结构化数据填充任务，不需要长链推理）
- 每次处理一个城市圈，避免上下文过长

#### Step 3：自动实体采集 + 绑定

anchor_entities 字段声明了每个簇需要什么实体，bootstrap 脚本直接读字段：

```python
async def bootstrap_entities(circle_id: str):
    # 1. 从 anchor_entities 字段读核心实体名（不再从 notes 解析）
    needed = read_anchor_entities_from_db(circle_id)

    # 2. 对比 entity_base，找缺失的
    missing = find_missing(needed)

    # 3. 定向生成缺失实体（按名字精确生成）
    for entity in missing:
        await generate_entity_by_name(entity["name"], entity["city_code"], entity["type"])

    # 4. 自动建 circle_entity_roles 绑定
    await bind_anchor_entities_to_roles(circle_id)

    # 5. 补充城市基础数据兜底
    await run_city_pipeline_for_circle(circle_id)
```

**不再需要**：regex 解析、人工跑多个脚本、手动审核缺口。

#### Step 4：自动生成知识包和内容包

调用 AI 生成，模板已有（kansai/hokkaido 作为参考）：

```python
async def generate_circle_knowledge(circle_id: str, region: str):
    # AI 生成 8 个 section（机场交通/IC卡/通信/行李/支付/App/紧急/季节）
    # 自动写入 circle_knowledge/{circle}.py
    # 自动注册到 __init__.py

async def generate_circle_content(circle_id: str):
    # AI 生成 persona + 静态出发准备
    # 自动写入 circle_content/{circle}.py
```

#### Step 5：自动验证

```python
def validate_circle_complete(circle_id: str) -> dict:
    return {
        "clusters_count": ...,          # >= 15
        "s_level_count": ...,           # >= 3
        "b_level_ratio": ...,           # >= 0.20
        "entity_coverage": ...,         # S级簇的实体覆盖率 >= 90%
        "entity_roles_bound": ...,      # 每个簇至少 1 个 anchor_poi
        "knowledge_pack": ...,          # 非 None
        "content_pack": ...,            # 有 PERSONA_NAME
        "tests_passed": ...,            # pytest 全绿
        "page_pipeline_ok": ...,        # demo 输出有真实景点名
    }
```

全部通过 → 圈上线。任何一项不通过 → 自动定位问题并修复。

#### Step 6：图片素材（唯一需要人工的环节）

这是唯一无法完全自动化的步骤——需要人工找图/拍图/买图。

但可以辅助自动化：
- 自动生成 manifest.json 骨架（entity_map key 从 DB 拿）
- 自动检查哪些 S 级实体还没图
- 未来可接 Unsplash/Pexels API 自动拉 placeholder 图

---

### 与当前手动流程的对比

| 环节 | 当前（手动） | 未来（自动） |
|------|------------|------------|
| 定义城市圈 | 手写 seed 代码 | `--circle xxx` 一个参数 |
| 生成活动簇 | GPT prompt → 人工审核 → 手动转 seed | AI 生成 → 自动校验 → 直接入库 |
| 活动簇质量检查 | 人工逐个看 city_code/等级/字段 | `validate_clusters()` 自动检查 |
| 实体采集 | 按城市盲拉 + 人工发现缺口 | 从活动簇反推 → 定向采集 → 自动绑定 |
| 知识包 | 人工写 Python 文件 | AI 生成 → 自动写入 → 自动注册 |
| 验证 | 人工跑脚本看输出 | `validate_circle_complete()` 一键检查 |
| 图片素材 | 人工准备 | **仍需人工**（可接 API 辅助） |
| **总人工时间** | **8-12 小时** | **30 分钟（审核 + 图片）** |

---

## 四、优先级排序

| 序号 | 任务 | 优先级 | 预估工时 | 依赖 |
|------|------|--------|---------|------|
| 1 | 活动簇→实体绑定 | **P0** | 4h | 无 |
| 2 | 补北海道/九州 B 级 | P1 | 1h | 无 |
| 3 | 清理关西圈数据 | P1 | 2h | 无 |
| 4 | 加到达日/雨天标记 | P1 | 1h | 无 |
| 5 | 补冲绳圈 | P2 | 3h | 无 |
| 6 | 体验类型重标记 | P2 | 1h | 无 |
| 7 | 补广东（潮汕）圈 | P2 | 3h | 无 |
| 8 | 补亲子/购物专线 | P2 | 2h | 无 |
