# 增长模块任务清单

> 独立于主链，可并行启动。交给 Sonnet 执行。
> 本文档直接作为 Sonnet 的任务输入。

---

## 执行说明

- 所有任务和主链代码零耦合，不动 `app/domains/planning/` 和 `app/domains/rendering/`
- 新代码放 `app/domains/content_marketing/` 和 `web/app/tools/`
- 每个任务标注了建议的模型配置

---

## 轨道 G1：营销内容生成后端（🤖 Sonnet, thinking off, 快速执行）

> **注意：项目中已有小红书图片生成 API**：
> - `/api/share/xhs` — Satori 动态生成 PNG，5种卡片类型
> - `web/lib/card-templates.ts` — 卡片 React 模板（462行）
> - `web/lib/photo-cache.ts` — 照片缓存
> - `web/lib/data.ts` — rush 数据读取
>
> 已有系统是**图片卡片生成**（景点数据→社交分享图）。
> 新增的是**文案生成**（实体数据→小红书图文/抖音脚本/公众号文章）。
> 两者互补：已有系统出图，新系统出文。

### G1.1 创建 content_marketing 模块骨架

```
模型: sonnet, thinking: off
预估: 1h
```

创建目录结构和基础文件：

```
app/domains/content_marketing/
  __init__.py
  topic_pool.py           # 选题库：YAML/JSON 定义选题模板
  generator_base.py       # 生成器基类（输入选题+数据 → 输出图文）
  generators/
    __init__.py
    xiaohongshu_post.py   # 小红书图文生成器
    douyin_script.py      # 抖音视频脚本生成器
    wechat_article.py     # 公众号文章生成器
  templates/
    __init__.py
    city_guide.py         # "X天Y城市攻略要点"
    food_ranking.py       # "必吃N家XX"
    budget_breakdown.py   # "去XX花多少钱"
    seasonal_special.py   # "XX赏樱/赏枫最佳时间"
    avoid_traps.py        # "千万别踩的N个坑"
    comparison.py         # "A vs B 到底选哪个"
```

要求：
- generator_base 定义统一接口：`generate(topic, context) → ContentOutput`
- ContentOutput 包含：title, body, image_hints[], hashtags[], cta_text
- topic_pool 支持从 YAML 文件加载选题列表

### G1.2 实现小红书图文生成器

```
模型: sonnet, thinking: off
预估: 3h
依赖: G1.1
```

实现 `xiaohongshu_post.py`：
- 输入：选题模板 + 实体数据（从 DB 读）
- 调用 gpt-4o 生成小红书风格图文（emoji丰富、分段短、有"划重点"）
- 输出：标题、正文（分段）、图片建议（用哪些实体的图）、标签列表
- 内置 6 个模板对应 6 种内容类型

prompt 风格要求：
- 口语化、像朋友分享不像广告
- 有具体数字和细节（"排队大概15分钟"不是"可能要排队"）
- 结尾带轻 CTA（"想要完整行程可以私信/看主页"）

### G1.3 实现抖音视频脚本生成器

```
模型: sonnet, thinking: off
预估: 2h
依赖: G1.1
```

实现 `douyin_script.py`：
- 输入：选题模板 + 实体数据
- 输出：视频脚本（开头hook + 主体内容 + 结尾CTA），每段标注预计时长
- 视频总长控制在 60-90 秒
- hook 要求前 3 秒抓人（"去京都千万别XX"/"这家拉面排队1小时也值"）

### G1.4 实现选题自动建议

```
模型: sonnet, thinking: on（需要推理季节+数据匹配）
预估: 2h
依赖: G1.1
```

在 `topic_pool.py` 中实现 `suggest_topics(current_date, entity_stats)` 函数：
- 读取当前日期 → 匹配季节活动（樱花季前1个月自动建议赏樱内容）
- 读取实体库统计 → 哪个圈数据最丰富就优先建议该圈
- 输出：推荐选题列表，按优先级排序，含理由

### G1.5 批量生成 CLI 脚本

```
模型: sonnet, thinking: off
预估: 1h
依赖: G1.2, G1.3
```

创建 `scripts/generate_marketing_content.py`：
- `--platform xhs` 或 `--platform douyin`
- `--count 5` 生成5篇
- `--topic food_ranking --circle kansai` 指定选题和城市圈
- `--suggest` 自动建议选题并生成
- 输出到 `output/marketing/` 目录，每篇一个 markdown 文件

### G1.6 审查+重构已有 XHS 卡片系统

```
模型: sonnet, thinking: on（需要评估现有代码质量）
预估: 3h
```

审查已有代码（不假设都能复用）：
- `web/app/api/share/xhs/route.ts` — XHS 图片生成 API
- `web/lib/card-templates.ts` — 5种卡片模板（462行）
- `web/lib/satori.ts` — Satori 渲染配置
- `web/lib/photo-cache.ts` — 照片缓存
- `web/lib/rush-data.ts` — 数据读取（421行）
- `web/app/rush/RushClient.tsx` — 樱花客户端（343行）
- `web/app/s/[card_id]/page.tsx` — 分享落地页
- `web/data/sakura/` — 花期数据

评估标准：
1. 代码质量是否达标（类型安全、错误处理、可维护性）
2. 数据结构是否合理（能否扩展到红叶/其他城市圈）
3. 卡片模板是否通用化（还是 hardcode 了太多）
4. 渲染性能是否 OK
5. 和新的实体库/城市圈结构是否对齐

输出：
- 哪些可以直接复用
- 哪些需要重构
- 哪些应该删除重建
- 具体的重构任务列表（如有）

---

## 轨道 G2：独立工具页前端（🤖 Sonnet, thinking off, 快速执行）

> **注意：项目中已有以下基础设施，不要重建**：
> - `/rush` 樱花追踪页（240+景点，6数据源，ISR 30min）→ `web/app/rush/`
> - `/api/share/xhs` 小红书图片生成 API（Satori+resvg，5种卡片）→ `web/app/api/share/xhs/`
> - 社交卡片系统 → `web/lib/card-templates.ts` + `satori.ts` + `photo-cache.ts`
> - 分享落地页 `/s/[card_id]` → `web/app/s/[card_id]/`
> - 樱花数据 → `web/data/sakura/`（JMA + WeatherNews JSON）
>
> 以下任务基于已有代码扩展，不重复造轮子。

### G2.0 工具页通用布局 + 索引

```
模型: sonnet, thinking: off
预估: 1h
```

创建 `web/app/tools/layout.tsx`：
- 顶部：简洁导航（logo + 工具列表）
- 底部：固定引导栏 "想要完整定制行程？7天手账 ¥198 →"（链接到下单页）
- 响应式，移动端优先

创建 `web/app/tools/page.tsx`：
- 工具卡片网格（图标+标题+一句话描述）
- 包含：樱花追踪（链接到已有 /rush）、红叶预报、预算计算器、行李清单、交通卡选择

### G2.1 改造现有樱花页 + 新建红叶预报

```
模型: sonnet, thinking: off
预估: 2h
依赖: G2.0
```

**樱花页（已有 /rush，改造）**：
- 在 `/tools/sakura` 创建一个重定向或别名指向已有的 `/rush`
- 或将 `/rush` 内容迁移到 `/tools/sakura`（更规范）
- 在现有 RushClient.tsx 底部加 CTA 引导栏："想要一份完整的赏樱行程？"
- 确保现有数据源（`web/data/sakura/`）和 ISR 机制不被破坏

**红叶预报页（新建）**：
- 创建 `web/app/tools/koyo/page.tsx`
- 复用 RushClient 的组件结构和样式
- 数据源：新建 `web/data/koyo/` 目录，前期硬编码关西/关东/北海道红叶数据
- 内容：各地区红叶见顷预测 + 推荐赏枫地点 + 小贴士

### G2.2 旅行预算计算器

```
模型: sonnet, thinking: on（需要设计交互逻辑）
预估: 4h
依赖: G2.0
```

创建 `web/app/tools/budget/page.tsx`：
- 用户选择：目的地城市圈 + 天数 + 人数 + 预算档位(低/中/高/超高)
- 自动计算并展示：
  - 每日预估花费（住宿/餐饮/交通/门票/购物）
  - 总预算范围
  - "你的预算够不够"判断
  - 省钱建议 2-3 条
- 数据来源：实体库的 budget_tier + 城市圈平均消费数据
- 底部 CTA："想要精确到每餐每景点的行程？"

### G2.3 行李清单生成器

```
模型: sonnet, thinking: off
预估: 2h
依赖: G2.0
```

创建 `web/app/tools/packing/page.tsx`：
- 用户选择：目的地 + 季节 + 天数 + 特殊需求（带娃/温泉/登山）
- 自动生成勾选式行李清单（证件/衣物/电子设备/洗护/药品/其他）
- 根据选择动态调整（冬天加保暖、温泉加泳衣、带娃加儿童用品）
- 可打印/截图保存
- 底部 CTA

### G2.4 交通卡选择器

```
模型: sonnet, thinking: on（需要推理哪张卡最划算）
预估: 3h
依赖: G2.0
```

创建 `web/app/tools/transport-pass/page.tsx`：
- 用户输入：去哪些城市 + 天数
- 系统推荐：适合的交通卡/通票
  - ICOCA / Suica（通用）
  - JR Kansai Wide Area Pass（关西广域）
  - Kansai Thru Pass（关西私铁）
  - JR Pass 全国版
- 每张卡标注：价格、覆盖范围、适合场景、购买方式
- "你的行程最适合：XXX，预计省 ¥YYY"

### G2.5 工具页索引

```
模型: sonnet, thinking: off
预估: 1h
依赖: G2.1-G2.4
```

创建 `web/app/tools/page.tsx`：
- 工具卡片网格展示（图标+标题+一句话描述）
- 链接到各子页面
- SEO 优化

---

## 轨道 G3：UTM 追踪（🤖 Sonnet, thinking: off）

### G3.1 UTM 参数采集

```
模型: sonnet, thinking: off
预估: 2h
```

- 在下单/表单提交时记录 URL 中的 UTM 参数
- 存入 TripRequest 或单独的 `marketing_attribution` 表
- 字段：utm_source, utm_medium, utm_campaign, utm_content, referral_code

### G3.2 工具页+内容带参

```
模型: sonnet, thinking: off
预估: 1h
依赖: G2.0
```

- 工具页底部 CTA 链接自动带 `?from=sakura_tool` 等参数
- 营销内容输出时自动附带追踪链接

---

## 并行执行计划

```
Week 1（和主链 Phase 1 并行）:

  Sonnet 实例 1（后端）:
    G1.1 模块骨架          1h
    G1.2 小红书生成器       3h
    G1.3 抖音脚本生成器     2h
    G1.4 选题建议           2h
    G1.5 CLI 脚本           1h
                           ───
                           ~9h = 1-2天

  Sonnet 实例 2（前端）:
    G2.0 通用布局           1h
    G2.1 樱花+红叶预报      3h
    G2.2 预算计算器          4h
    G2.3 行李清单            2h
    G2.4 交通卡选择器        3h
    G2.5 索引页              1h
                           ───
                           ~14h = 2-3天

  Sonnet 实例 3（追踪）:
    G3.1 UTM 采集           2h
    G3.2 带参链接            1h
                           ───
                           ~3h

三条轨道完全并行，无依赖关系。
```

---

## 验收标准

| 模块 | 验收 |
|------|------|
| 营销生成 | 运行 `python scripts/generate_marketing_content.py --platform xhs --count 3 --circle kansai`，输出3篇可直接发布的小红书图文 |
| 工具页 | 访问 `/tools/sakura` 能看到樱花预报，底部有 CTA 引导 |
| UTM | 从工具页点击 CTA 下单，TripRequest 中能看到 utm_source |
