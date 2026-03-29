# 前端重构任务清单

> 交给 Sonnet 执行。按批次排列，批次1最优先。
> 设计参考见 `docs/FRONTEND_DESIGN_SPEC.md`（含重构背景、设计参考网站、色彩方案）。

---

## 执行前须知

**设计参考网站**（Sonnet 在实现前用 WebFetch 看以下网站，提取视觉风格）：

产品质感参考：
- **Craft.do** (craft.do) — 暖米色底色、纸质纹理感、圆角、慢过渡动画 → 参考底色和纸质感
- **Headspace** (headspace.com) — 暖米白#F9F4F2、自定义圆润字体、SVG装饰点缀 → 参考表单引导流程

高端旅行定制参考：
- **Boutique Japan** (boutiquejapan.com) — 全幅实拍hero、105条评价展示、行业认证logo → 参考信任感构建
- **The Japan Concierge** (thejapanconcierge.com) — 奶油底色、高质量摄影、"先了解你再设计"姿态 → 参考服务气质
- **Jacada Travel** (jacadatravel.com/asia/japan/) — 视频hero、金色线条图标、浅棕/白交替分区 → 参考视觉节奏

日式手账美学参考：
- **Bungu Store** (bungu.store) — 纯白+深棕+金色点缀、极简网格 → 参考日式克制美学

**色彩体系**：
```
主色（底色）: #FBF7F0（暖米白，纸张感）
强调（CTA）: #C65D3E（赤茶色）
标题: #2D4A3E（墨绿）
正文: #3D3029（深棕，不用纯黑）
点缀: #E8A0BF（樱粉）/ #D4A855（金）
```

**字体**：
- 中文标题：思源宋体（Noto Serif CJK SC）
- 中文正文：思源黑体（Noto Sans CJK SC）
- 英文/数字：Inter

**设计气质**：温暖 > 酷炫，留白 > 堆满，实物感 > 数字感，一句话 > 一段话

---

## 批次1：核心流程页（🤖 Sonnet, thinking: on）

这4个页面是新流程的骨干，必须先完成。

### F1.1 更新全局 layout + 色彩体系

```
模型: sonnet, thinking: off
预估: 2h
```

改 `web/app/layout.tsx`：
- 网站标题改为品牌名（不再是"Sakura Rush"）
- 删除 SakuraParticles 组件
- 更新 metadata（title/description/OG）
- 引入新字体（思源宋体 + 思源黑体）
- 更新 `globals.css` 色彩变量为上述色彩体系
- Navbar 简化：logo + 首页 + 工具 + FAQ + 管理后台入口

### F1.2 下单页 `/order`

```
模型: sonnet, thinking: on（需要设计交互逻辑）
预估: 4h
```

新建 `web/app/order/page.tsx`：
- 天数选择器（5-14天，按钮组，默认选7）
- 国内/国外切换
- 动态计价显示（公式：¥198 + (天数-7) × ¥20，国外+¥30）
- 11天+ 自动显示"拆为两册 +¥29"提示
- 支付按钮（前期：显示微信/支付宝二维码或客服联系方式）
- 含：退款政策说明、产品包含内容、信任标签
- 页面设计参考 Airbnb 预订确认页的简洁感

### F1.3 V3 八屏表单 `/form/[code]`

```
模型: sonnet, thinking: on（最复杂的页面）
预估: 8h
```

重建 `web/app/form/[code]/page.tsx`：
- 按 `docs/product/travel_form_multistep_frontend_v3.md` 完整实现8屏+确认页
- 需实现：
  - 顶部进度条（当前屏/总屏数）
  - 每屏一个主问题
  - 必填屏（1-4）不可跳过
  - 选填屏（5-8）明确标注"可跳过"
  - 第5屏包含避雷选项（"我可以接受"勾选框，默认不勾）
  - 动态表单：支持草稿保存（zustand + localStorage 暂存，定期 PATCH 到后端）
  - 第9屏确认页：汇总所有已填信息
  - 提交后提示"30分钟内可撤回"
- API：
  - GET `/api/forms/[code]` 加载已保存数据
  - PATCH `/api/forms/[code]` 每屏切换时自动保存
  - POST `/api/forms/[code]/submit` 最终提交
- 文案语气按 V3 文档要求（温暖、不像录单）
- 页面设计参考 Headspace 的 onboarding 流程

### F1.4 手账查看页 `/guide/[code]`

```
模型: sonnet, thinking: on（三段结构 + 状态管理）
预估: 8h
```

新建 `web/app/guide/[code]/page.tsx`：

**状态1：等待生成中**
- 显示"正在为您定制手账..."
- 预计时间倒计时
- 可以重新查看已提交的表单信息

**状态2：前置层可查看（Part1 + Part2）**
- 按 SERVICE_FLOW.md 的三段结构渲染
- Part1 精华展示：封面/地图/气质/亮点/酒店/餐厅/预算/准备（全部大方展示，不模糊）
- Part2 预约行动清单：按紧急度分组（🔴🟡🟢），含链接和截止日
- 剧透页分隔
- Part3 锁定区域：显示每天标题但内容模糊 + 🔒
- 底部：[我要修改方案] [确认，解锁全部]

**状态3：已确认/已解锁**
- Part3 完全展开：每天6页详细执行
- 旅后层：购物/预算回顾/照片页/心情页
- 顶部：PDF下载按钮
- 底部：复购引导（"看看其他城市圈→"）

- API：
  - GET `/api/guide/[code]` 获取状态 + 数据
  - POST `/api/guide/[code]/confirm` 确认解锁
- 每个页面组件复用已有 `web/components/report/page-types/`（评估后可复用的部分）
- 页面设计参考 Craft.do 的文档展示风格 + Apple 的产品展示感

### F1.5 AI 修改对话页 `/guide/[code]/modify`

```
模型: sonnet, thinking: on（对话式交互）
预估: 5h
```

新建 `web/app/guide/[code]/modify/page.tsx`：
- 对话式 UI（类似简化版 ChatGPT）
- 用户输入大白话修改意见
- AI 返回理解确认（"是我理解的这样吗？"）
- 用户可继续补充
- 满意后点"确认这次修改"
- 修改后显示进度（"正在调整中…约5分钟"）
- 完成后自动返回 `/guide/[code]`（刷新数据）
- API：
  - POST `/api/guide/[code]/modify` 发送修改意见
  - GET `/api/guide/[code]/modify/status` 轮询修改进度
- 一轮修改限制：确认后页面变为只读 + 提示"如需再次修改请联系客服"

---

## 批次2：首页 + 品牌（🤖 Sonnet, thinking: off 为主）

### F2.1 首页重建

```
模型: sonnet, thinking: on（整体布局设计）
预估: 6h
```

重建 `web/app/page.tsx`：
- 按 FRONTEND_REDESIGN.md 第四节的 wireframe 实现
- Hero：产品主图（手账本实拍）+ 一句话 + 价格 + CTA
- 展示区：手账本内容展示（可用翻页动画或卡片切换）
- 样本展示：3个城市圈的旧攻略卡片（图片+标题+CTA）
- 流程4步：图标+标题+说明
- 信任区：退款/修改/速度
- FAQ 3条
- 底部 CTA

### F2.2 FAQ 更新

```
模型: sonnet, thinking: off
预估: 1h
```

更新 `web/app/faq/page.tsx`：
- 问题更新为匹配新定价（¥198起）和新流程
- 删除关于三档定价、免费版、尊享版的问题
- 新增：天数怎么算价格、什么时候能收到、怎么修改、退款政策

### F2.3 删除废弃页面

```
模型: sonnet, thinking: off
预估: 1h
```

删除或移入 archive：
- `web/app/quiz/`
- `web/app/sample/`
- `web/app/preview/`
- `web/app/pricing/`
- `web/app/submitted/`
- `web/app/plan/[id]/upgrade/`
- `web/app/custom/`（评估后决定删除还是更新）
- `web/components/landing/HeroSection.tsx`（樱花主题 hero，替换）
- `web/components/landing/DataAuthority.tsx`（樱花数据权威性展示）

### F2.4 Navbar + FloatingCTA 更新

```
模型: sonnet, thinking: off
预估: 2h
```

- Navbar：品牌 logo + 首页 / 工具 / FAQ / 联系我们
- FloatingCTA：移动端底部固定栏 → "7天手账 ¥198 · 开始定制"
- 删除所有"复制微信号"CTA（前期保留一个联系方式入口即可）

---

## 批次3：工具页（见 TASKS_GROWTH.md G2 轨道）

已在 TASKS_GROWTH.md 中详细定义，此处不重复。

---

## 批次4：清理 + 管理后台（🤖 Sonnet, thinking: off）

### F4.1 管理后台状态更新

```
模型: sonnet, thinking: off
预估: 3h
```

- 订单看板列名更新匹配新状态机
- 订单详情页显示：专属码、天数、计价明细
- Review 页增加前置层预览渲染

### F4.2 API 路由清理

```
模型: sonnet, thinking: off
预估: 2h
```

- 新增 `/api/guide/[code]` — 手账查看数据
- 新增 `/api/guide/[code]/confirm` — 确认解锁
- 新增 `/api/guide/[code]/modify` — AI 修改
- 新增 `/api/forms/[code]` — V3 表单 CRUD
- 新增 `/api/order` — 下单 + 计价
- 清理不再使用的 API 路由

### F4.3 旧页面组件评估复用

```
模型: sonnet, thinking: on（需要评估代码质量）
预估: 2h
```

评估已有组件哪些可复用：
- `web/components/report/page-types/` — 20+ 页面类型组件，可能可复用于 `/guide/[code]`
- `web/components/custom/` — 部分可用于首页
- `web/lib/satori.ts` + `card-templates.ts` — 社交卡片生成
- `web/lib/animations.ts` — 动画配置

输出：复用清单 + 需改造清单 + 删除清单

---

## 并行执行计划

```
批次1（核心，串行，因为有依赖）:
  F1.1 layout       2h  ──→ 所有页面依赖新样式
  F1.2 /order       4h  ──→ 独立
  F1.3 /form        8h  ──→ 独立
  F1.4 /guide       8h  ──→ 最复杂
  F1.5 /modify      5h  ──→ 依赖 F1.4
                    ───
                    ~27h = 3-4天

  ⚠️ F1.1 必须先完成（其他页面依赖样式）
  ⚠️ F1.2/F1.3/F1.4 可以并行（3个 Sonnet 实例）
  ⚠️ F1.5 等 F1.4 完成后再做

批次2（可与批次1后半段并行）:
  F2.1 首页         6h
  F2.2 FAQ          1h
  F2.3 删除旧页面    1h
  F2.4 导航栏        2h
                    ───
                    ~10h = 1-2天

批次3: 见 TASKS_GROWTH.md

批次4（最后收尾）:
  F4.1 管理后台      3h
  F4.2 API 清理      2h
  F4.3 组件评估      2h
                    ───
                    ~7h = 1天
```

---

## 验收标准

| 里程碑 | 验收 |
|--------|------|
| 批次1完成 | 新流程可跑通：下单→填表→生成→查看前置层→修改→解锁 |
| 批次2完成 | 首页展示品牌正确，旧页面全部清理，无死链 |
| 批次4完成 | 管理后台能看到新流程订单，所有 API 对齐 |
