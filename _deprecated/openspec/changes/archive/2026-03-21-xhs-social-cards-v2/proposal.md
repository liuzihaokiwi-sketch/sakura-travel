## Why

樱花季是最强引流窗口期（3-4月），小红书是核心获客渠道。现有 3 套 Satori 社交卡片模板存在以下问题：
1. **视觉风格脱节** — 深红黑配色 (`#1a0a0f`) 与新版 `/rush` 页面的温暖石灰 warm-50 品牌调性完全不一致
2. **品牌信息过时** — 写"4大权威数据源"，实际已升级到 6 大；缺少"能冲指数"核心概念
3. **CTA 无效** — 底部写"关注获取完整榜单"，没有引导到小红书私信转化
4. **没有利用实景图** — 数据中有 `photo` 字段但模板完全没用上，图片全是纯色块

**MVP 优先级**: P0（樱花季正在进行中 3/21，必须立即更新）

**在产品价位梯度中的作用**: 社交卡片是引流漏斗顶端——从小红书导入流量到 `/rush` 页面，然后转化到 `/quiz` 问卷，最终购买 ¥248 标准行程或 ¥888 专业行程。

## What Changes

- **删除** 现有 3 个旧模板 (xhs-cover, moment, xhs-content)，替换为 5 个新模板
- **新增** 5 种社交卡片模板，统一使用与 `/rush` 页面一致的 warm 品牌视觉：
  1. `xhs-cover` — 城市 TOP3 赏樱封面（小红书 1080×1440）
  2. `xhs-spot` — 单景点种草卡，带实景照片（小红书 1080×1440）
  3. `xhs-compare` — 多城市花期对比横图（小红书 1080×1440）
  4. `wechat-moment` — 朋友圈方图（1080×1080）
  5. `xhs-story` — 竖版 Stories（1080×1920），适合短视频封面
- **更新** CTA 文案统一引导：关注小红书账号 + 私信咨询
- **更新** 品牌元素：6 大数据源 · "能冲指数" 核心 hook · SAKURA RUSH 2026 品牌标
- **新增** 实景照片集成 — 利用 weathernews 数据中的 photo 字段作为背景图
- **更新** `export-satori.ts` 脚本支持新的 5 个模板 + 批量生成

## Capabilities

### New Capabilities
- `social-cards-v2`: 重新设计的社交卡片模板系统——5 种模板 × 多城市自动批量生成，统一品牌视觉，引导至小红书私信转化

### Modified Capabilities
<!-- 无已有 spec 需要修改 -->

## Impact

- **文件修改**: `web/scripts/export-satori.ts` 完全重写模板逻辑
- **文件修改**: `web/lib/satori.ts` 可能需要支持图片加载（远程 photo URL → Buffer）
- **依赖**: 现有 `satori` + `@resvg/resvg-js` 无需改动
- **数据依赖**: `weathernews_all_spots.json` 中的 photo/trees/lightup/meisyo100 字段
- **输出**: `output/cards/` 目录批量 PNG 文件
- **API**: `web/app/api/share/card/route.tsx` 需要更新以支持新模板
