# 行程节奏编排原则

> 好行程不是 S 活动最多，而是峰值、对比、恢复、节奏四件事同时成立。

## 核心观点

连续 3 天寺庙会腻，连续看海也会腻，再壮丽的风景看到第 4 天也变成"又一个湖"。
真正导致审美疲劳的不是 level 重复，而是**体验形态重复**。

系统的目标不是"把最强活动排满"，而是"让每一天都有主角，但每天的主角不是同一种主角"。

---

## 三个字段

每个 ActivityCluster 标注 3 个节奏字段：

### 1. experience_family — 体验家族

解决"像不像"的问题。同族不应连续两天。

| 值 | 含义 | 典型活动 |
|---|---|---|
| flower | 花景 | 樱花线、薰衣草、红叶大轴 |
| mountain | 山景 | 富士山、立山黑部、上高地 |
| sea | 海景 | 镰仓海岸、冲绳海滩、函馆港 |
| shrine | 寺社文化 | 东山祇园、奈良公园、伏见稻荷 |
| citynight | 都市夜景 | 涩谷新宿、大阪道顿堀、维港 |
| art | 艺术展览 | 六本木艺术、teamLab、西九文化 |
| food | 美食主导 | 筑地市场、顺德美食、博多屋台 |
| locallife | 在地生活 | 下北泽、谷中银座、永庆坊 |
| themepark | 主题乐园 | USJ、迪士尼、长隆 |
| onsen | 温泉疗愈 | 有马、箱根、登别、黑川 |

### 2. rhythm_role — 节奏角色

解决"放在旅程哪里"的问题。

| 值 | 含义 | 数量建议 |
|---|---|---|
| peak | 记忆高光，承担整趟旅行的主理由 | 每 7 天行程 2-3 个 |
| contrast | 换气质，防止连续同类 | 穿插在 peak 之间 |
| recovery | 恢复体力和情绪，防疲劳 | peak 后必跟 |
| utility | 缝补时间，购物/车站/轻逛 | 按需 |

### 3. energy_level — 精力消耗

解决"累不累"的问题。

| 值 | 含义 | 典型 |
|---|---|---|
| low | 轻松，几乎不累 | 温泉、咖啡线、购物 |
| medium | 适中，正常体力消耗 | 半天步行、美食线 |
| high | 很累，全天暴走或高强度 | 全天寺社、登山、主题乐园 |

---

## 三条硬规则

### 规则 1：同族不连续

相邻两天的 `experience_family` 不能相同。

```
✗ Day 1 shrine → Day 2 shrine（连续寺庙）
✓ Day 1 shrine → Day 2 food → Day 3 shrine（中间换了气质）
```

### 规则 2：峰值要间隔

两个 `rhythm_role=peak` 之间至少隔一个 recovery 或 contrast。

```
✗ Day 1 peak → Day 2 peak → Day 3 peak（连续高潮=互相稀释）
✓ Day 1 peak → Day 2 recovery → Day 3 peak（有呼吸）
```

### 规则 3：高能要交替

`energy_level=high` 后面必须跟 medium 或 low。

```
✗ Day 1 high → Day 2 high（连续两天暴走=第三天废掉）
✓ Day 1 high → Day 2 low → Day 3 high（有恢复）
```

---

## 理想的行程节奏模式

### 4 天

```
D1: contrast (medium) — 到达+轻探索
D2: peak (high) — 主高光
D3: recovery (low) — 温泉/美食/慢节奏
D4: peak (medium) — 收尾高光
```

### 5-6 天

```
D1: contrast (medium) — 到达
D2: peak (high) — 高光 A
D3: recovery (low) — 恢复
D4: peak (high) — 高光 B（不同 family）
D5: contrast (medium) — 换气质
D6: utility (low) — 离开日
```

### 7-8 天

```
peak 不超过 3 个。因为用户会记住的高峰一般就那几个，多了不是赚，是互相冲掉。
```

---

## 日内结构

每天最多 1 个视觉主导型 anchor。

```
✓ 1 个主锚点 + 1 个异质补充 + 0-1 个低负担尾巴
✗ 3 个同类大景点堆在一天（"看了很多但记不住"）
```

---

## 实现位置

| 环节 | 文件 | 作用 |
|------|------|------|
| 数据标签 | `ActivityCluster.experience_family/rhythm_role/energy_level` | 静态标注 |
| 排程检查 | `route_skeleton_builder.py` → `apply_rhythm_check()` | 构建后调整顺序 |
| 质量评分 | `itinerary_fit_scorer.py` → `rhythm_score` | 同质惩罚 + 对比奖励 |
| 门控 | `quality_gate.py` | rhythm_score 过低触发 rewrite |
