# 内容引擎

## 小红书内容策略

### 内容支柱（Content Pillars）

| 支柱 | 比例 | 内容类型 | 目标 |
|---|---|---|---|
| 实用攻略 | 40% | 「东京 5 天不踩坑路线」「京都一日最优顺序」 | SEO + 收藏 |
| 痛点共鸣 | 25% | 「花两周做攻略 vs 拿到就能出发」 | 引发讨论 + 转化 |
| 视觉种草 | 20% | 樱花/美食/和服实拍大图 | 曝光 + 涨粉 |
| 用户案例 | 15% | 「客户反馈：第一次不用做功课的旅行」 | 信任 + 转化 |

### 排期节奏

- **日常**：每周 3-4 篇图文笔记
- **旺季前**（樱花季/红叶季/暑假前 2 个月）：加密到每天 1 篇
- **热点借势**：签证政策变化、航班特价、节日活动

### 素材来源

1. **系统自动生成**：Satori 批量导出城市封面卡片（1080x1350）
2. **Playwright 截图**：将交付页截图为分享图（1080x1080 朋友圈 / 1080x1350 小红书）
3. **杂志模板渲染**：Jinja2 模板渲染后截图，作为攻略实拍效果展示
4. **用户授权转载**：征得同意后使用用户旅行实拍

### 导流路径

```
小红书笔记 → 个人主页（置顶引导） → 微信添加规划师
                                    ↓
                              发送免费预览链接 → 转化
```

## 内容生成工具链

| 工具 | 位置 | 用途 |
|---|---|---|
| Satori | `web/scripts/export-satori.ts` | 批量生成城市/景点卡片图 |
| Playwright | `web/scripts/export-playwright.ts` | 交付页截图为分享图 |
| Jinja2 杂志模板 | `templates/magazine/` | 渲染各类页面（封面、日卡、餐厅报告等） |
| WeasyPrint | `app/domains/rendering/renderer.py` | HTML → PDF |

## 模板清单

`templates/magazine/` 下包含 16 个 Jinja2 模板：
cover, day_card, entity_card, hotel_area, hotel_list_simple, hotel_report,
restaurant_report, compare_report, photo_guide, instagrammable_guide,
pre_trip_guide, safety_guide, savings_summary, tips_page, avoid_traps, base