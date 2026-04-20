# 数据源目录

按**地域 × 品类**分文件。每个文件独立完整，含分级、访问方式、搜索词、三轴分配。

## 日本

→ [japan/](japan/) — 已建完整

| 品类 | 文件 | 说明 |
|------|------|------|
| 吃 | [japan/restaurants.md](japan/restaurants.md) | Tabelog/米其林/百名店/携程/小红书+独立站 |
| 住 | [japan/hotels.md](japan/hotels.md) | 一休/楽天/MICHELIN Keys/Forbes/携程+台湾博主/日文媒体 |
| 玩 | [japan/spots.md](japan/spots.md) | japan-guide/JNTO/Google+携程/独立站+季节数据 |
| 买 | [japan/shops.md](japan/shops.md) | F-STREET/thisismedia/Hanako 等按店铺类型分 |
| 行 | [japan/transport.md](japan/transport.md) | 乗換案内/Google Directions/通票 |

## 中国

→ [china/](china/) — 占位，开城时填充

---

## 如何使用

**场景 A：采集时找源**
1. 确定品类（吃/住/玩/买/行）
2. 打开对应文件
3. 按三轴分配表选主源+辅助源
4. 用搜索词模板发起搜索

**场景 B：遇到新博主站想评估**
1. Ctrl+F 搜域名，看是否已收录
2. 未收录则验证访问方式（WebFetch/OpenCLI/WebSearch 间接）
3. 加入对应品类文件的"独立攻略站"章节

**场景 C：源失效了**
1. 在对应文件的"访问问题与替代方案"章节加备注
2. 更新访问方式列
