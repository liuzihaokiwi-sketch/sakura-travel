# 日本数据源

按品类分文件，每个文件独立完整。

| 品类 | 文件 |
|------|------|
| 吃（餐厅） | [restaurants.md](restaurants.md) |
| 住（酒店/旅馆） | [hotels.md](hotels.md) |
| 玩（景点/体验） | [spots.md](spots.md) |
| 买（店铺/购物） | [shops.md](shops.md) |
| 行（交通） | [transport.md](transport.md) |
| 季节活动（樱花/红叶/祭典） | [seasonal.md](seasonal.md) |

---

## 通用原则

**可信度分级:**
- **P0** 权威源 — 可作为 quality 轴唯一来源
- **P1** 辅助源 — 需配合 P0，对中国游客极重要
- **P2** 参考源 — 交叉验证、独立站 indie_quotes
- **P3** AI 知识库 — 不可用于生产，必须标 `ai_generated`

**三轴角色:**
- `quality` — 品质/专业性/口碑
- `traveler_fit` — 中国游客实际满意度
- `execution` — 营业状态/坐标/预约/排队

详见 [methodology/master-guide.md](../../methodology/master-guide.md) 三轴判断模型章节。

---

## 工具说明

- **OpenCLI** 配置见 [ops/tools-setup.md](../../ops/tools-setup.md)
- **WebFetch** 是 Claude Code 内置，对大部分站点可用
- **WebSearch** 用于被阻止站的间接访问
- **API**（Google Maps / Rakuten Travel）需配置 Key
