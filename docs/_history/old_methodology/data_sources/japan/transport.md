# 日本交通数据源

> 版本: 1.0
> 更新: 2026-04-10
> 适用: 路线规划、换乘查询、交通通票

---

## 一、路线/时刻表

| 数据源 | 域名 | 三轴角色 | 访问方式 | 备注 |
|--------|------|---------|---------|------|
| **乗換案内（Jorudan）** | jorudan.co.jp | execution（路线+时刻表） | API 可用 / WebFetch | 日本电车/公交时刻表，路线计算的最权威源 |
| **Google Directions API** | maps.google.com | execution（路线计算） | API（需 Key） | 支持 transit 模式，全球通用 |
| **Google Routes API** | maps.google.com | execution（批量矩阵） | API `computeRouteMatrix`（transit 上限 100 elements，必须带 field mask） | Step 9 稀疏矩阵用 |
| **NAVITIME** | navitime.co.jp | execution | API 付费 / WebFetch | 日本本土路线应用 |
| **ekitan** | ekitan.com | execution | WebFetch | 车站时刻表 |

---

## 二、交通通票

| 数据源 | 说明 |
|--------|------|
| `data/seed/transport_passes.json` | 项目内部维护的通票数据库 |
| JR 各公司官网（JR West / JR East / JR Kyushu 等） | JR Pass 各区域版本 |
| 各私铁官网（阪急/阪神/近铁/京阪等） | 私铁通票 |
| JNTO 交通专页 | 官方综合信息 |

### 常用通票

- **JR Pass 全国版** — 外国人专属，jrpass.com
- **关西周游卡（KANSAI THRU PASS）** — 私铁+地铁+巴士
- **关西广域周游券** — JR West 关西+广岛
- **大阪周游卡（Osaka Amazing Pass）** — 大阪市内
- **京都观光一日券** — 巴士+地铁

---

## 三、换乘/路线博客（参考级）

| 网站 | 域名 | 访问方式 | 实战价值 |
|------|------|---------|---------|
| **换乘案内の案内君** | anneijun.com | WebFetch | 中文换乘攻略，带 CNY 价格 |
| **一直玩的馬摩** | massi.tw | OpenCLI | Tabelog 使用教学+交通 |

---

## 四、搜索词模板

| 语言 | 搜索词 |
|------|-------|
| 日文 | `"{出発} から {目的地} 乗換"` |
| 日文 | `"{城市} 交通パス"` |
| 简中 | `"{城市}交通攻略"` |
| 简中 | `"关西 JR Pass"` |
| 英文 | `"{city} japan train pass"` |

---

## 五、API 注意事项

### Google Routes API

- `computeRouteMatrix` transit 模式上限 **100 elements**
- 必须带 **field mask**，否则按最高 SKU 计费
- 项目内 Step 9 不做全量 N×N POI 矩阵，只算稀疏矩阵（当日活动+候补+住宿）

### Rakuten / Jorudan

- Rakuten Travel API 可用于酒店，不适用于交通
- Jorudan 官方 API 需付费注册

---

## 六、三轴分配

| 场景 | 主源 | 辅助 |
|------|------|------|
| 单次路线查询 | Jorudan / Google Directions | ekitan |
| 批量路线矩阵 | Google Routes API | - |
| 通票推荐 | `transport_passes.json` + JR 官网 | JNTO |
| 时刻表确认 | Jorudan | ekitan |
