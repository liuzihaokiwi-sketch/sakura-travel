# 京都餐厅区域清单（跨季节共用）

> 从 21 个早春京都模板的 meal_area 字段汇总。每个区域要维护一个独立餐厅池（`content/kansai_v2/kyoto/restaurants.json` 里按 area 字段对齐）。
> 不同频率的区域对应餐厅池的规模应该不同。
> 季节性菜品/营业窗口（如川床、牡蛎期、松茸期）放餐厅池的 seasonal_availability 字段，不放本区域清单。

---

## 汇总（按早春 21 模板引用频率排序，跨季节通用）

| area 代码 | 覆盖范围 | 模板引用次数 | 推荐餐厅池规模 | 优先级 |
|---------|---------|------|------------|------|
| `kyoto_city` | 京都市中心（通用回市区吃）| 15 | 30+ 家（涵盖所有档位和菜系，因为是大多数晚餐默认 fallback）| P1 |
| `arashiyama_central` | 岚山渡月桥周边 | 5 | 10-15 家（豆腐料理为主 + 河边茶屋）| P1 |
| `kyoto_station` | 京都站+梅小路周边 | 4 | 15-20 家（拉面小路+伊势丹餐厅街+京都站大楼）| P1 |
| `gion_pontocho` | 祇园+先斗町+木屋町 | 4 | 20-25 家（割烹+町家料理+居酒屋，覆盖情侣/闺蜜高光餐）| P1 |
| `higashiyama_south` | 清水寺+高台寺+八坂 | 2 | 10-12 家（豆腐/町家料理）| P2 |
| `northwest_kinkaku` | 金阁+龙安+北野+上七軒 | 2 | 8-10 家（北山线午餐+晚餐）| P2 |
| `karasuma_oike` | 乌丸御池+二条城周边 | 2 | 12-15 家（市中心的本地午餐选择丰富）| P2 |
| `fushimi` | 伏见稻荷+伏见酒蔵 | 2 | 8-10 家（酒蔵直营餐厅为主 + 稻荷寿司）| P2 |
| `okazaki_kyoudai` | 冈崎+平安神宫+京大 | 1 | 5-8 家（南禅寺汤豆腐 signature）| P3 |
| `kawaramachi_shijo` | 河原町+锦市场+新京極 | 1 | 15-20 家（锦市场小吃+町家料理）| P2 |
| `demachiyanagi` | 出町柳+鸭川三角洲+下鸭 | 1 | 5-8 家（京大附近学生食堂+本地拉面）| P3 |
| `ohara` | 大原山区 | 1 | 3-5 家（精进料理+本地农家餐厅）| P3 |

---

## 每个区域的特色

### `kyoto_city`（通用回市区）
用于晚餐默认 fallback——当用户选择"回市区吃"时。实际上应该是 `gion_pontocho` / `karasuma_oike` / `kawaramachi_shijo` 三个池子的组合，而不是独立池。
**建议：** 不建立 `kyoto_city` 独立池，改为装配时根据用户所在酒店位置自动选最近的 3 个区域池之一。

### `arashiyama_central`（岚山）
特色菜系：**京豆腐料理**（嵯峨豆腐森嘉、湯豆腐嵯峨野）、河边茶屋、% ARABICA 精品咖啡。
档位分布：中档偏高（岚山整体餐厅偏贵），economy 选择有限。

### `kyoto_station`（京都站）
特色：**拉面小路**（10 家拉面名店集合）、伊势丹餐厅街、京都站大楼 11F 和食/洋食街、The CUBE。
档位：economy 到 premium 全档位覆盖。

### `gion_pontocho`（祇园/先斗町）
特色：**京懐石+割烹+町家料理**（情侣/闺蜜高光餐区域）。
档位：mid-high 到 luxury 为主，economy 选择少。
注意：早春 3 月无川床（川床是 5-9 月）。季节性菜单/席位也放餐厅自己的 seasonal_availability 字段。

### `higashiyama_south`（清水寺/高台寺）
特色：**豆腐料理+おばんざい**，参道上避免（贵），往高台寺/宁宁之道方向好店多。
档位：mid 为主。

### `northwest_kinkaku`（金阁/北野）
特色：**上七軒町家料理+北山汤豆腐**。
档位：mid 为主，选择比市中心少 50%。

### `karasuma_oike`（乌丸御池/二条城）
特色：**町家割烹+创作料理+洋食**，办公街区午餐选择丰富。
档位：全覆盖，平日午餐性价比高。

### `fushimi`（伏见）
特色：**酒蔵直营餐厅**（鳥せい本店、黄樱河童王国）、**稻荷寿司**（豆腐皮包饭）。
档位：mid 为主。

### `okazaki_kyoudai`（冈崎/京大）
特色：**南禅寺汤豆腐**（奥丹南禅寺）、京大学生餐厅。
档位：两极分化——汤豆腐 premium，学生餐厅 economy。

### `kawaramachi_shijo`（河原町/锦市场）
特色：**锦市场小吃**（田中鶏卵玉子烧、京豆富藤野、多家抹茶店）、商店街轻食。
档位：economy 到 mid 为主。

### `demachiyanagi`（出町柳/下鸭）
特色：**出町ふたば豆大福**、京大附近本地拉面和定食店。
档位：economy 为主（学生街）。

### `ohara`（大原山区）
特色：**精进料理**（寺院素食）、**大原の里的农家餐厅**。
档位：economy 和 premium 都有（精进料理 premium，农家 economy）。

---

## 下一步工作

1. **建立每个区域的餐厅池文件**：`content/kansai_v2/kyoto/restaurants.json` 每家带 `area` 字段对齐本清单
2. **从旧数据迁移**：`content/kansai/kyoto/restaurants.json` 的 50+ 家餐厅按新 area 重新分类（字段按 08 文档 §8.1）
3. **补充不足的区域**：特别是 `northwest_kinkaku` / `okazaki_kyoudai` / `demachiyanagi` / `ohara` 这几个餐厅覆盖可能薄的区域
4. **考虑合并 `kyoto_city`**：建议拆分到 3 个核心市中心区域（gion_pontocho / karasuma_oike / kawaramachi_shijo），不建立通用 city 池
