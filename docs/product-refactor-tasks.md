# 产品重构任务清单

> 基于拍板方案：免费样片 → 付费 → 详细表单 → 校验 → 生成
> 更新时间：2026-03-22

---

## 一、整体流程

```
用户进入首页 → 选 2 个字段(目的地+风格) → 自动出一日样片(在线)
  → 样片页(Day1完整 + 后续钩子锁定 + 主CTA解锁 + 次CTA微信 + PDF下载)
  → 付费 ¥248
  → 客服发详细表单链接
  → 用户填 6 步详细表单
  → 系统自动红黄绿校验
  → 客服只补红/黄问题 → 用户补填 → 重新校验
  → 全绿后触发完整攻略生成
  → 攻略交付(在线+PDF)
  → 自助微调 / 正式修改
```

---

## 二、任务分类（可并行）

### 🔴 高级 AI 任务（需要架构理解、复杂逻辑）

| ID | 任务 | 依赖 | 说明 |
|----|------|------|------|
| H1 | ✅ 样片展示页 `/sample/[id]` | L2 | Day1 时间轴 + 钩子锁定 + 主CTA + 次CTA微信(3处) + 对比表(彩色标注) + FAQ全展开 + PDF + 底部固定CTA |
| H2 | 付费后详细表单 `/detail-form/[id]` | H5,H7 | 6 步分步表单，条件触发，行内校验，单列布局，一屏不滚动 |
| H3 | 后端校验引擎 `POST /validate/{id}` | H5 | 红黄绿三层规则，返回结构化 JSON |
| H4 | 管理后台校验展示 + 补填闭环 | H3 | 红黄绿摘要卡 + 冲突清单 + 追问话术 + 一键复制 |
| H5 | 后端详细表单数据模型 + CRUD | — | `detail_forms` 表设计 + API |
| H6 | ✅ 状态流改造 | — | 全链路 11 状态统一完成。前端看板/详情页/API 全部对齐，后端 orders.py + submissions.py + quiz.py + chat.py + review.py + intensity.py + modifications.py 全部修正 |
| H7 | 目的地自动补全组件 | — | 标准化城市列表 + 搜索下拉 + place_id |

### 🟢 低级 AI 任务（模板化、配置化、可独立做）

| ID | 任务 | 依赖 | 说明 | 状态 |
|----|------|------|------|------|
| L1 | Quiz 页面重做 | — | 1 页 2 字段：目的地 6 选 1 + 风格 6 选 1，选完自动提交 | ✅ 已完成（原有实现符合规格） |
| L2 | 样片模板数据 JSON | — | 先做 tokyo_classic 1 套，后续批量 | ✅ 已完成（web/data/sample-templates.json 存在） |
| L3 | 首页 CTA 改造 | — | 主按钮→"免费看看你的行程"→跳 /quiz | ✅ 已完成（2026-03-22） |
| L4 | 去掉 Supabase 残留 | — | 删 supabase.ts、清 .env.local、清 import，移除 package.json 依赖 | ✅ 已完成（2026-03-22） |
| L5 | 废弃 /submitted 页面 | H1 | /submitted 改为 server-side redirect 到 /quiz | ✅ 已完成（2026-03-22） |
| L6 | 后端 submissions 接口适配 | — | party_type 默认 unknown，只存 dest+style | ✅ 已完成（2026-03-22） |
| L7 | 微信复制兼容 | — | 提取 lib/clipboard.ts 公共函数，全页面统一 HTTP fallback | ✅ 已完成（2026-03-22） |
| L8 | 追问话术模板 | — | 红色/黄色追问模板文案，存 data/followup_templates.json | ✅ 已完成（2026-03-22） |
| L9 | 管理后台看板过滤适配 | H6 | 看板改为 6 列，按新状态流动态渲染 | ✅ 已完成（2026-03-22，H1 真实完成后一并做了） |
| L10 | Docker Compose 配置 | — | PG + Redis + FastAPI + Next.js + Nginx，补充 deploy/init.sql | ✅ 已完成（2026-03-22） |
| L11 | 部署脚本 + 域名 HTTPS | L10 | deploy/deploy.sh，支持 --https <domain> certbot 自动申请 | ✅ 已完成（2026-03-22） |
| L12 | README / 文档更新 | 全部 | 新流程说明 + 环境变量 + 管理后台使用 | ✅ 已完成（2026-03-22，文档整合清理） |

### 并行关系图

```
可并行组 A（无依赖，立刻开始）：
  L1, L2, L3, L4, L6, L7, L8, L10, H5, H6, H7

可并行组 B（依赖组 A 部分完成）：
  H1(依赖L2), H2(依赖H5,H7), L5(依赖H1), L9(依赖H6)

可并行组 C（依赖组 B）：
  H3(依赖H5), H4(依赖H3)

最后：
  L11, L12
```

---

## 三、详细表单字段表（付费后填写，前端中文）

### Step 1：基础路线信息

**目标：先把骨架定住**

#### 必填

| 字段名 | 类型 | 输入方式 | 前端显示 |
|--------|------|---------|---------|
| trip_days | number | 单选/步进器 | 去几天 |
| destination_1 | place | 搜索下拉选择 | 主要目的地 |
| japan_familiarity | enum | 单选 | 去过日本几次 |
| trip_style | enum | 单选 | 这次更想怎么玩 |

**trip_days 选项：** 3天 / 4天 / 5天 / 6天 / 7天 / 8-10天 / 10天以上

**japan_familiarity 选项：** 第一次去 / 去过 1-2 次 / 去过很多次

**trip_style 选项：** 多城顺玩 / 一地深玩 / 还没想好

#### 建议收

| 字段名 | 类型 | 输入方式 | 前端显示 |
|--------|------|---------|---------|
| destination_2 | place | 搜索下拉选择 | 还会去哪（可选） |
| destination_3 | place | 搜索下拉选择 | 还会去哪（可选） |
| days_by_destination | object | 可选分配 | 每个地方大概待几天 |

**UI：** destination_2/3 默认不展开，点"+添加目的地"后出现

---

### Step 2：交通与固定时间

**目标：锁死不能动的约束**

#### 必填

| 字段名 | 类型 | 输入方式 | 前端显示 |
|--------|------|---------|---------|
| transport_locked | boolean | 单选 | 是否已买机票/车票 |
| arrival_date | date | 日期选择 | 到达日期 |
| arrival_time | time | 时间选择 | 到达时间 |
| arrival_place | place | 搜索下拉选择 | 到达机场/车站 |
| departure_date | date | 日期选择 | 离开日期 |
| departure_time | time | 时间选择 | 离开时间 |
| departure_place | place | 搜索下拉选择 | 离开机场/车站 |

#### 条件触发（勾选"有固定安排"后展开）

| 字段名 | 类型 | 输入方式 | 前端显示 |
|--------|------|---------|---------|
| fixed_events[] | list | 可重复表单 | 固定不可变的时间安排 |
| ├─ fixed_event_type | enum | 单选 | 类型：演出/预约/见朋友/餐厅/其它 |
| ├─ fixed_event_date | date | 日期 | 日期 |
| ├─ fixed_event_time | time | 时间 | 时间 |
| ├─ fixed_event_place | place | 搜索下拉 | 地点 |
| └─ fixed_event_note | text | 选填 | 备注 |

---

### Step 3：住宿情况

**目标：确认可调整空间**

#### 必填

| 字段名 | 类型 | 输入方式 | 前端显示 |
|--------|------|---------|---------|
| hotel_booking_status | enum | 单选 | 酒店订了吗 |
| willing_change_hotel_area | enum | 单选 | 是否接受换酒店区域 |
| want_fewer_hotel_moves | boolean | 单选 | 是否希望少换酒店 |

**hotel_booking_status 选项：** 全都没订 / 已订一部分 / 已订全部

**willing_change_hotel_area 选项：** 可以 / 尽量不要 / 不接受

#### 条件触发（不是"全没订"时展开）

| 字段名 | 类型 | 输入方式 | 前端显示 |
|--------|------|---------|---------|
| booked_hotels[] | list | 可重复表单 | 已订酒店信息 |
| ├─ booked_hotel_city | place | 搜索下拉 | 酒店所在城市/区域 |
| ├─ booked_hotel_checkin | date | 日期 | 入住日期 |
| ├─ booked_hotel_checkout | date | 日期 | 退房日期 |
| ├─ booked_hotel_name | text | 选填 | 酒店名称 |
| └─ booked_hotel_note | text | 选填 | 备注 |

---

### Step 4：同行人与风格

**目标：知道这趟到底该怎么排**

#### 必填

| 字段名 | 类型 | 输入方式 | 前端显示 |
|--------|------|---------|---------|
| travel_group | enum | 单选 | 和谁一起去 |
| vibe_preference | enum | 单选 | 这趟更想要什么感觉 |
| pace_preference | enum | 单选 | 节奏偏好 |

**travel_group 选项：** 情侣/夫妻 / 闺蜜好友 / 带父母 / 带孩子 / 独自出行 / 朋友结伴

**vibe_preference 选项：** 经典不踩坑 / 更有审美更容易出片 / 吃得更好 / 更轻松 / 更小众一点 / 温泉疗愈 / 购物为主

**pace_preference 选项：** 轻松 / 均衡 / 能接受高密度

#### 条件触发

| 条件 | 字段名 | 前端显示 |
|------|--------|---------|
| 带父母 | parent_walk_tolerance (enum: 低/中/高) | 父母步行/换乘承受度 |
| 带孩子 | child_age_band (enum: 0-3/3-6/6-12/12+) | 孩子年龄段 |
| 带孩子 | stroller_needed (boolean) | 需要推车吗 |
| 带孩子 | need_midday_rest (boolean) | 需要午休吗 |
| 情侣 | anniversary_trip (boolean) | 有纪念日安排吗 |

---

### Step 5：预算与取舍

**目标：让系统知道钱怎么花更值**

#### 必填

| 字段名 | 类型 | 输入方式 | 前端显示 |
|--------|------|---------|---------|
| budget_range | enum | 单选 | 每人预算大概多少 |
| spend_priority | enum | 单选 | 更想把钱花在哪 |

**budget_range 选项：** 5000 以下 / 5000-10000 / 10000-20000 / 20000 以上（每人，不含机票）

**spend_priority 选项：** 住得更好 / 吃得更好 / 体验更特别 / 更均衡 / 更看重整体性价比

#### 建议收

| 字段名 | 类型 | 输入方式 | 前端显示 |
|--------|------|---------|---------|
| want_onsen_ryokan | boolean | 单选 | 想住温泉旅馆吗 |
| want_special_dining | boolean | 单选 | 想安排纪念日/高光餐吗 |
| want_shopping | boolean | 单选 | 购物优先吗 |
| want_cultural_experience | boolean | 单选 | 想加文化体验吗 |
| want_photo_priority | boolean | 单选 | 希望优先出片吗 |

---

### Step 6：硬约束与避坑

**目标：减少后续返工**

#### 必填

| 字段名 | 类型 | 输入方式 | 前端显示 |
|--------|------|---------|---------|
| must_go | text list | 标签输入 | 一定要去的地方 |
| dont_want_go | text list | 标签输入 | 不想去的地方 |
| food_restrictions | enum+text | 多选+补充 | 饮食禁忌/过敏 |
| stamina_level | enum | 单选 | 体力/脚程 |

**food_restrictions 多选项：** 无 / 不吃生食 / 不吃猪肉 / 不吃牛肉 / 素食 / 海鲜过敏 / 其他（补充）

**stamina_level 选项：** 体力一般 / 正常 / 暴走无压力

#### 建议收

| 字段名 | 类型 | 输入方式 | 前端显示 |
|--------|------|---------|---------|
| dont_want_early_morning | boolean | 单选 | 不想早起 |
| dont_want_late_return | boolean | 单选 | 不想太晚回酒店 |
| accessibility_need | boolean | 单选 | 有无障碍需求吗 |
| special_notes | text | 选填 | 其他想说的 |

---

## 四、红黄绿校验规则表

### 🔴 红色：必须补充/修改，阻断生成

| 编号 | 条件 | 提示文案（中文） |
|------|------|------------|
| R1 | arrival_date 或 arrival_time 缺失 | 请补充到达日期和时间 |
| R2 | departure_date 或 departure_time 缺失 | 请补充离开日期和时间 |
| R3 | transport_locked=是，但 arrival_place 或 departure_place 缺失 | 你已表示买了机票/车票，请补充到达和离开的机场/车站 |
| R4 | destination_1 为空 | 请先选择主要目的地 |
| R5 | 有 fixed_event 但日期/时间/地点不完整 | 你有固定安排，请补全具体时间和地点 |
| R6 | hotel_booking_status ≠ 全没订，但 booked_hotels 信息不完整 | 你已表示订了酒店，请补充酒店所在区域和入住日期 |
| R7 | must_go 与 dont_want_go 出现同一地点 | 你的「一定要去」和「不想去」里有冲突地点，请确认 |
| R8 | food_restrictions 选了"其他"但补充为空 | 请补充具体的饮食禁忌 |
| R9 | departure_date 早于 arrival_date | 离开日期不能早于到达日期 |
| R10 | trip_days 与 arrival/departure 日期差 ≥2 天 | 行程天数与到离日期不一致，请确认 |

### 🟡 黄色：建议确认，客服跟进

| 编号 | 条件 | 提示文案（中文） |
|------|------|------------|
| Y1 | trip_style=一地深玩，但 destination_2/3 已填 | 你选择了一地深玩，但同时添加了多个目的地，请确认是否改为多城顺玩 |
| Y2 | spend_priority=性价比，但勾选 ≥3 个高成本体验 | 你更看重性价比，但同时选了多个高成本项目，后续可能需要取舍 |
| Y3 | pace_preference=轻松，但目的地跨度 ≥3 城 | 你希望更轻松，但当前路线可能偏折腾，后续会帮你优化 |
| Y4 | arrival_time ≥ 20:00 | 到达时间较晚，首日不适合安排重行程 |
| Y5 | departure_time ≤ 10:00 | 离开时间较早，末日建议安排轻量行程 |
| Y6 | hotel_booking_status=已订全部 且 willing_change=不接受 且 trip_style=多城 | 你已锁定住宿且不接受换区域，后续路线调整空间会变小 |
| Y7 | stamina_level=低 且 pace_preference=高密度 | 你的体力和节奏偏好可能冲突，建议确认 |
| Y8 | travel_group=带父母/带孩子 且 pace=高密度 且 trip_style=多城 | 这类同行结构下，多城高密度行程可能偏累 |

### 🟢 绿色：通过，可进入生成

满足以下条件默认绿色：
- 所有必填项齐全
- 无红色冲突
- 黄色 ≤2 条且已确认
- 到离时间、酒店、固定事件足够明确

---

## 五、追问话术模板

### 红色追问（必须补）

```
你好，这边已经开始帮你准备完整行程了 🙌
不过有 {count} 个关键信息还需要你补一下，不然会影响排路线：

{red_items}

你补完后，我们就能继续往下做～
补填链接：{form_url}
```

### 黄色追问（建议确认）

```
这边还有 {count} 个点想和你确认一下，这样做出来会更贴合你这趟：

{yellow_items}

如果不确定也没关系，我们会按更稳的方式先处理 👌
```

---

## 六、状态流

```
new                 用户刚选完目的地+风格
sample_viewed       用户看了样片
paid                用户付费了
detail_filling      客服发了详细表单链接，用户在填
detail_submitted    用户提交了详细表单
validating          系统正在校验
needs_fix           有红色/黄色问题，等用户补填
validated           全绿通过
generating          正在生成完整攻略
done                攻略生成完毕
delivered           已交付给用户
```

---

## 七、管理后台看板分列

| 列名 | 包含状态 |
|------|---------|
| 待处理 | new, sample_viewed |
| 已付费 | paid |
| 表单中 | detail_filling, detail_submitted, needs_fix |
| 待生成 | validating, validated |
| 生成中 | generating |
| 已完成 | done, delivered |

---

## 八、客服工作指南

### 免费阶段
- **不介入**，系统自动出样片

### 付费后
- 发详细表单链接给用户
- 查看后台红黄绿标记
- **只补问红色和黄色问题**
- 用追问话术模板，一键复制发给用户

### 不该做的
- ❌ 手动通读全部字段
- ❌ 手动分析路线逻辑
- ❌ 手动猜用户想去哪
- ❌ 手动清洗开放文本

### 人工介入场景
- 用户主动问问题
- 红色问题用户不理解
- 特殊需求（10人以上团、商务、无障碍）
- 退款/投诉

---

## 九、设计原则

1. 选择题优先，少开放输入
2. 条件触发，不相关的不出现
3. 地点必须标准化（搜索+下拉+place_id），不允许自由输入
4. 行内校验，不等最后报错
5. 错误提示必须具体（不写"信息有误"，写具体哪里冲突）
6. 客服是"补关键约束的人"，不是"人工解析器"
7. 主路径用网页在线展示，PDF 作为补充下载
8. 样片后留钩子，微信放次 CTA 承接高意向