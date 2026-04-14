## ADDED Requirements

### Requirement: Service advantage grid with real data
The custom service page at `/custom` SHALL display a grid of service advantages, each backed by real project data. Advantages MUST include:
1. **路线规划引擎** — 8条精品路线模板（3-8天），覆盖东京/关西/联程
2. **4种场景适配** — 情侣/家庭/独旅/闺蜜，自动调整推荐权重
3. **9维偏好匹配** — 购物/美食/温泉/自然/文化/动漫/亲子/夜生活/出片问卷
4. **12维智能评分** — Google+Tabelog+Booking 三平台数据融合评分
5. **Tabelog 严选餐厅** — 仅 3.5+入选，最高4.68分，含招牌菜/人均/预约指引
6. **16套杂志级PDF** — 可打印的旅行杂志排版，含每日时间轴
7. **11个数据爬虫** — 覆盖 Google Flights/Booking/Tabelog/携程/Agoda 等全渠道
8. **55+活动祭典** — 夜樱/花火/市集/祭典全覆盖
9. **143个目的地** — JNTO日本国家旅游局官方目的地数据
10. **旅居日本团队** — 人工验证，实地走过每条路线
11. **顺路串联不走回头路** — 按区域聚合景点，Pass最省方案自动计算
12. **出片保证** — 最佳时段+小众机位+错峰路线

#### Scenario: Advantage grid displays all 12 items
- **WHEN** user opens `/custom`
- **THEN** all 12 advantage items are displayed in a responsive grid with icons, titles, concrete data numbers, and brief descriptions

#### Scenario: Each card shows real numbers
- **WHEN** viewing the "路线规划引擎" card
- **THEN** the card shows "8条路线 · 3-8天" with a route icon, not vague marketing copy

### Requirement: Contrast with AI competitors
Each advantage card SHALL include a red "pain point" callout showing what generic AI tools get wrong, contrasted with an orange "our solution" showing the real capability.

#### Scenario: AI contrast display
- **WHEN** viewing the "Tabelog 严选餐厅" card
- **THEN** red callout shows "❌ AI推荐的餐厅已倒闭/评分虚高" and orange callout shows "✅ Tabelog 3.5+才入选，最高4.68"

### Requirement: 4-step process flow
The page SHALL display a clear 4-step process: 1) 加微信备注「樱花」 2) 告知日期城市人数 3) 免费获取1天攻略 4) 满意再付费。Each step SHALL have a numbered badge with warm gradient styling.

#### Scenario: Process steps visible
- **WHEN** user views the custom service page
- **THEN** 4 steps are displayed vertically with numbered badges, clear labels, and sub-descriptions

### Requirement: WeChat CTA module
The page SHALL prominently display the WeChat ID `Kiwi_iloveu_O-o` with a one-click copy button. The CTA area SHALL use dark background with gradient text for the WeChat ID.

#### Scenario: Copy WeChat ID
- **WHEN** user clicks "复制微信号" button
- **THEN** `Kiwi_iloveu_O-o` is copied to clipboard and button text changes to "✅ 已复制!" for 1.5 seconds

### Requirement: Trust indicators
The page SHALL display trust indicators: "🔒 不满意不收费", "🌸 已服务200+", "🎁 首次免费体验" prominently near the CTA area.

#### Scenario: Trust signals visible with CTA
- **WHEN** user sees the WeChat CTA module
- **THEN** at least 3 trust indicators are displayed adjacent to the CTA button

### Requirement: Single-screen layout on desktop
The entire custom service page SHALL fit within one viewport on desktop (1920×1080) without scrolling. On mobile, scrolling is acceptable but the CTA MUST be visible in the first viewport.

#### Scenario: No-scroll desktop
- **WHEN** viewing `/custom` on a 1920×1080 display
- **THEN** all content fits within the viewport with `h-screen overflow-hidden`

#### Scenario: Mobile CTA first-screen
- **WHEN** viewing `/custom` on a 375×812 mobile screen
- **THEN** the WeChat CTA button and "免费体验" messaging are visible without scrolling
