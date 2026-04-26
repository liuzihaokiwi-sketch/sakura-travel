# 关西酒店数据池

跟 `japan/kansai/restaurants/` `japan/kansai/stops/` 平级。

- 字段规范 → [`docs/操作SOP/上线前/数据池构建/酒店规范.md`](../../../docs/操作SOP/上线前/数据池构建/酒店规范.md)
- 字段总闸 → [`docs/项目核心/字段权威.md §2.4`](../../../docs/项目核心/字段权威.md)
- tier 阈值 → [城市档位.md](城市档位.md)

## 文件

```
kyoto.json    — 京都 96 家
osaka.json    — 大阪 50 家
other.json    — 神户 28 + 奈良 11 + 城崎 8 + 高野山 10 + 白浜 3 = 60 家
城市档位.md
```

合计 206 家·全部通过 `python scripts/validate_hotels.py japan/kansai/hotels/`·0 errors。

## 历史决策

D40-D49 完整变更链 → [`docs/项目核心/历史决策.md`](../../../docs/项目核心/历史决策.md)
