# Travel AI — 端到端测试操作指引

> **给执行者的说明：**
> 你正在测试一个日本旅行攻略定制平台。用户提交问卷 → 看样片 → 加微信付费 →
> 填详细表单 → AI 生成攻略 → 用户查看/微调 → 旅程结束归档。
>
> **所有操作必须通过前端 API（localhost:3000）完成，禁止直接调后端（localhost:8000）。**
> 如果某一步前端没有对应接口，说明前端逻辑缺失，应该记录为 BUG 而不是绕过。
>
> **每一步都要验证返回值**，不是 200 就继续，要检查返回的 JSON 内容是否合理。

---

## 项目架构速览

```
前端: Next.js  (localhost:3000)
后端: FastAPI  (localhost:8000)
数据库: PostgreSQL + Redis（任务队列）

生成管线（v2）：
  City-Circle 链路（主）: quiz → normalize_trip_profile → _try_city_circle_pipeline
                           → major_activity_ranker → hotel_base_builder
                           → itinerary_builder → report_generator_v2 → L3 page pipeline
  旧模板链路（fallback）: assemble_trip → report_generator_v1

关键表：
  quiz_submissions  — 用户问卷记录（看板数据源）
  detail_forms      — 付费后详细表单（6步）
  trip_requests     — 行程请求（生成引擎入口）
  trip_profiles     — AI 标准化后的用户画像
  city_circles      — 城市圈定义（kansai_v1 / tokyo_v1 …）
  itinerary_plans   — 生成的攻略（含 plan_metadata）
  itinerary_days    — 每日行程
  itinerary_items   — 每日条目（景点/餐厅/交通）

关键 ID：
  submission_id   — 贯穿全流程的主 ID（quiz 提交时生成）
  form_id         — 详细表单 ID（客服创建时生成）
  trip_request_id — 行程请求 ID（触发生成时创建）
  plan_id         — 攻略 ID（city-circle 管线生成后产生）
```

---

## 后端接口快速验证（脚本）

```bash
# 验证所有 11 个核心后端端点（约 40 秒，含生成等待）
set PYTHONIOENCODING=utf-8
python scripts/verify_api.py
# 期望: 11/11 通过，WARN/SKIP 为异步等待中，不是 FAIL
```

---

## 前置检查

在开始之前，先确认两个服务都在运行：

```
GET http://localhost:3000/          → 期望 200
GET http://localhost:8000/docs      → 期望 200
```

> ⚠️ 如果任一服务挂了，先启动再测：
> - 后端: `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`
> - 前端: `cd web && npx next dev --port 3000`
> - Worker: `python -m app.workers.runner`（需要 Redis）

---

## 第一步：用户提交问卷

> **角色：用户** | **页面：/quiz**
>
> 💡 这是用户接触平台的第一步。选目的地和旅行风格，系统返回一个 submission_id，
> 后续所有操作都围绕这个 ID。

```
POST http://localhost:3000/api/quiz
Content-Type: application/json

{
  "destination": "kansai",
  "duration_days": 5,
  "party_type": "couple",
  "styles": ["food", "photo"]
}
```

**验证：**
- 返回 JSON 包含 `trip_request_id` 字段（即 submission_id）
- 记下这个 ID，后面全程使用，记为 `<SID>`

> 📌 推荐目的地：`kansai`（对应 `kansai_classic_circle`）或 `tokyo`（`tokyo_v1`）。
> 使用 kansai 可以走完整 City-Circle 链路（含圈选择/活动排序/酒店策略验证）。

---

## 第二步：用户查看 Day1 样片

> **角色：用户** | **页面：/sample/<SID>**
>
> 💡 这是一个纯展示页面，展示 AI 根据目的地生成的 Day1 样片。
> 页面底部引导用户添加微信客服。

```
GET http://localhost:3000/sample/<SID>?dest=kansai&style=food
```

**验证：**
- 返回 200
- 页面能正常渲染（如果是 curl 测试只要 200 即可）

---

## 第三步：客服推进状态（模拟线下微信沟通）

> **角色：客服/管理员** | **页面：/admin → 点卡片进入详情**
>
> 💡 现实中：用户看完样片后加微信 → 客服确认需求 → 用户微信转账。
> 这里模拟客服在后台标记状态变更。
>
> ⚠️ 状态必须按顺序推进，不能跳步。每次只能转到允许的下一个状态。

**3a. 标记"已看样片"：**
```
PATCH http://localhost:3000/api/admin/submissions?id=<SID>
Content-Type: application/json

{ "status": "sample_viewed", "notes": "客户已看样片" }
```

**3b. 确认付费：**
```
PATCH http://localhost:3000/api/admin/submissions?id=<SID>
Content-Type: application/json

{ "status": "paid", "notes": "微信转账 ¥248 已确认" }
```

**验证：**
- 每次返回 `{ "ok": true }`
- 刷新 `/admin` 看板，卡片应该从"待处理"移到"已付费"列

---

## 第四步：客服创建详细表单 & 发链接给用户

> **角色：客服** | **页面：/admin/order/<SID>**
>
> 💡 付费后客服创建一个详细表单，把链接通过微信发给用户填写。
> 这个接口是幂等的——重复调用不会创建多个表单，会返回已有的。

```
POST http://localhost:3000/api/detail-forms/<SID>/create
Content-Type: application/json

{ "submission_id": "<SID>" }
```

**验证：**
- 返回 JSON 包含 `form_id` 字段
- 记下这个 ID，记为 `<FID>`
- 表单链接为：`http://localhost:3000/detail-form/<FID>`

---

## 第五步：用户填写详细表单（6步）

> **角色：用户** | **页面：/detail-form/<FID>**
>
> 💡 用户通过客服微信发来的链接打开表单，分6步填写详细旅行需求。
> 每步通过 PATCH 保存，支持反复修改。最后点"提交"确认。
>
> ⚠️ 字段名必须和后端 ORM 模型严格一致（见下方），否则会 422。
> 关键易错字段：`accommodation_pref` 是 dict 不是 list，`food_preferences` 也是 dict。

**Step 1 — 目的地与日期：**
```
PATCH http://localhost:3000/api/detail-forms/<FID>
Content-Type: application/json

{
  "cities": [
    {"city_code": "kyoto", "city_name": "京都", "nights": 2},
    {"city_code": "osaka", "city_name": "大阪", "nights": 3}
  ],
  "travel_start_date": "2026-06-10",
  "travel_end_date": "2026-06-14",
  "duration_days": 5,
  "date_flexible": false,
  "current_step": 1
}
```

**Step 2 — 同行人信息：**
```
PATCH http://localhost:3000/api/detail-forms/<FID>
Content-Type: application/json

{
  "party_type": "couple",
  "party_size": 2,
  "party_ages": [28, 26],
  "has_elderly": false,
  "has_children": false,
  "arrival_shape": "fly_in",
  "current_step": 2
}
```
> ⚠️ `arrival_shape` 新字段：`fly_in` / `shinkansen` / `drive`

**Step 3 — 预算与住宿：**
```
PATCH http://localhost:3000/api/detail-forms/<FID>
Content-Type: application/json

{
  "budget_level": "mid",
  "budget_total_cny": 15000,
  "budget_focus": "better_food",
  "accommodation_pref": {"type": "hotel", "star_min": 3, "location_pref": "near_station"},
  "current_step": 3
}
```
> ⚠️ `accommodation_pref` 必须是 JSON 对象（dict），不是数组

**Step 4 — 兴趣偏好：**
```
PATCH http://localhost:3000/api/detail-forms/<FID>
Content-Type: application/json

{
  "must_have_tags": ["kaiseki", "arashiyama", "dotonbori", "nishiki_market"],
  "nice_to_have_tags": ["matcha_cafe", "photo_spot", "kimono_rental"],
  "avoid_tags": ["tourist_trap"],
  "food_preferences": {"must_try": ["kaiseki", "takoyaki"], "budget_per_meal": 3000},
  "theme_family": "couple_aesthetic",
  "daytrip_tolerance": "half_day",
  "current_step": 4
}
```
> ⚠️ `daytrip_tolerance` 新字段：`none` / `half_day` / `full_day`

**Step 5 — 行程节奏：**
```
PATCH http://localhost:3000/api/detail-forms/<FID>
Content-Type: application/json

{
  "pace": "moderate",
  "wake_up_time": "normal",
  "must_visit_places": ["fushimi_inari", "arashiyama", "dotonbori"],
  "free_text_wishes": "希望有一天安排岚山竹林，晚上想去道顿堀吃章鱼烧",
  "current_step": 5
}
```
> ⚠️ 字段名是 `pace`（不是 pace_preference），`must_visit_places`（不是 must_go_places）

**Step 6 — 航班与交通：**
```
PATCH http://localhost:3000/api/detail-forms/<FID>
Content-Type: application/json

{
  "flight_info": {
    "outbound": {"flight": "MU517", "arrive": "13:30", "airport": "KIX"},
    "return": {"flight": "MU518", "depart": "17:00", "airport": "KIX"}
  },
  "arrival_airport": "KIX",
  "departure_airport": "KIX",
  "has_jr_pass": true,
  "transport_pref": {"icoca": true, "pocket_wifi": true},
  "current_step": 6
}
```

**最后提交：**
```
POST http://localhost:3000/api/detail-forms/<FID>/submit
```

**验证：**
- 每个 PATCH 返回 200，response 包含更新后的完整表单数据
- submit 返回 `{ "submitted": true }`

---

## 第六步：客服推进到"生成"状态

> **角色：客服** | **页面：/admin/order/<SID>**
>
> 💡 表单提交后需要经过几个状态才能到达"生成"。
> 每个状态只能转到特定的下一个状态（见状态机）。

```
PATCH → { "status": "detail_filling" }     // paid → detail_filling
PATCH → { "status": "detail_submitted" }   // detail_filling → detail_submitted
PATCH → { "status": "validating" }         // detail_submitted → validating
PATCH → { "status": "validated" }          // validating → validated
PATCH → { "status": "generating" }         // validated → generating
```

> 每个 PATCH 都发到: `http://localhost:3000/api/admin/submissions?id=<SID>`

**验证：** 每次返回 `{ "ok": true }`

---

## 第七步：触发 AI 生成攻略（关键步骤）

> **角色：客服** | **页面：/admin/order/<SID> → 点"触发生成"按钮**
>
> 💡 生成链路说明（v2 City-Circle 主链路）：
> 1. `normalize_trip_profile` — 标准化用户画像 → TripProfile（~0.1s）
> 2. `city_circle_selector` — 选择城市圈（kansai_classic_circle 等）（~0.1s）
> 3. `eligibility_gate` — 过滤不可用活动（~0.1s）
> 4. `major_activity_ranker` — AI 主活动打分排序（~0.3s 决策链）
> 5. `hotel_base_builder` — 酒店策略生成
> 6. `itinerary_builder` — 组装 Day×Item 行程框架
> 7. `report_generator_v2` — AI 文案润色（~60s，调用 Claude/DeepSeek）
> 8. L3 page pipeline — 章节/页面/ViewModel 渲染数据
> 9. LiveRiskMonitor — 风险扫描（节假日/关闭/拥挤）
>
> ⚠️ 生成是完全异步的，返回 202 只代表已入队。
> 决策链约 0.3s 完成，AI 文案约 60s，整体 **预计 60-90 秒** 完成。
> 需要轮询 `trip_request_id/status` 等待 `status=done`。

```
POST http://localhost:3000/api/admin/submissions/<SID>/generate
```

**验证：**
- 返回 202，包含 `trip_request_id`
- 轮询状态（每 5 秒）：

```
GET http://localhost:8000/trips/<trip_request_id>/status
```

期望：`status` 从 `new` → `assembling` → `done`（约 60-90 秒）

> 如果超过 3 分钟还是 `assembling`，检查后端日志：
> ```
> # 查看最新 worker 输出
> python -m app.workers.runner
> ```

**City-Circle 链路额外验证（完整跑通后）：**
```
GET http://localhost:8000/trips/<trip_request_id>/plan
```
检查响应中的 `plan_metadata.pipeline_versions` 字段，应包含：
- `city_circle_selector`
- `major_activity_ranker`
- `hotel_strategy`

---

## 第八步：客服标记交付

> **角色：客服**

```
PATCH http://localhost:3000/api/admin/submissions?id=<SID>
Content-Type: application/json

{ "status": "delivered" }
```

**验证：** 返回 `{ "ok": true }`，看板卡片移到"已交付"列

---

## 第九步：用户查看攻略报告

> **角色：用户** | **页面：/plan/<SID>**
>
> 💡 用户通过客服微信发来的链接查看完整攻略。
> 攻略包含 Day-by-Day 行程，每天有景点、餐厅、交通安排。

```
GET http://localhost:3000/plan/<SID>
```

**验证：**
- 返回 200
- 检查 `/api/plan/<SID>` 返回的 JSON：
  - 包含 `days` 数组，长度等于 `duration_days`
  - 每个 day 包含 `day_number`, `city_code`, `items`
  - `items` 不为空，包含景点/餐厅/交通条目
  - `plan_metadata.page_pipeline` 存在（L3 渲染已完成）

---

## 第十步：用户微调报告

> **角色：用户**
>
> 💡 用户看完攻略后想改一些东西，重新打开表单链接修改。
> 修改后告诉客服，客服可以重新触发生成。

```
PATCH http://localhost:3000/api/detail-forms/<FID>
Content-Type: application/json

{
  "must_visit_places": ["fushimi_inari", "namba"],
  "free_text_wishes": "去掉岚山，改成难波逛街，想多拍照"
}
```

**验证：** 返回 200，response 中对应字段已更新

---

## 第十一步：客服大改报告

> **角色：客服** | **页面：/detail-form/<FID>**
>
> 💡 客服也可以打开同一个表单链接进行大幅修改（如换城市、改天数）。

```
PATCH http://localhost:3000/api/detail-forms/<FID>
Content-Type: application/json

{
  "cities": [
    {"city_code": "kyoto", "city_name": "京都", "nights": 2},
    {"city_code": "osaka", "city_name": "大阪", "nights": 2},
    {"city_code": "kobe", "city_name": "神户", "nights": 1}
  ],
  "duration_days": 5,
  "pace": "relaxed",
  "free_text_wishes": "客服备注：客户要求加神户一天，吃牛肉，减少赶路"
}
```

**验证：** 返回 200，`cities` 数组已变成 3 个城市

> 改完后如需重新生成攻略，重复第七步（POST .../generate）。

---

## 第十二步：标记"使用中"

> **角色：客服**
>
> 💡 攻略交付后用户进入旅行期间，标记为"使用中"。

```
PATCH http://localhost:3000/api/admin/submissions?id=<SID>
Content-Type: application/json

{ "status": "using" }
```

**验证：** 看板卡片移到"使用中 ✈️"列

---

## 第十三步：归档

> **角色：客服**
>
> 💡 旅程结束后归档。归档后卡片从看板消失，可在"历史表单"页查看。

```
POST http://localhost:3000/api/admin/submissions?id=<SID>&action=archive
```

**验证：**
- 返回 `{ "ok": true, "status": "archived" }`
- 刷新 `/admin` 看板，该卡片消失
- 打开 `/admin/history` 页面，能看到刚归档的记录

---

## 完整状态流转图

```
new → sample_viewed → paid → detail_filling → detail_submitted
  → validating → validated → generating → done → delivered
    → using → archived

特殊分支：
  任意付费前状态 → cancelled
  paid → refunded
  delivered → refunded
```

---

## 后端生成管线状态机（trip_requests.status）

```
new
 └─ normalize_trip_profile worker 处理后 → profiled
     └─ POST /trips/{id}/generate 触发 → assembling
         ├─ city_circle_selector 选圈
         ├─ eligibility_gate 过滤
         ├─ major_activity_ranker 排序
         ├─ hotel_base_builder 酒店策略
         ├─ itinerary_builder 组装框架
         ├─ report_generator_v2 AI 文案（~60s）
         ├─ L3 page pipeline 渲染数据
         └─ LiveRiskMonitor 风险扫描
     → done（或 failed）
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|---|---|---|
| PATCH 返回 400 "无法从 X 转到 Y" | 状态必须按顺序推进，不能跳步 | 检查当前状态，按状态机顺序操作 |
| PATCH 返回 422 | 字段名或类型不匹配 | 检查本文档中的 ⚠️ 提示，核对字段名 |
| 生成超时（status 一直是 assembling）| AI API 调用失败或配额超限 | 检查 worker 日志，确认 `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` 有效 |
| city_circle 圈未匹配，走了旧链路 | destination 不在 city_circles 表中 | 用 `kansai` 或 `tokyo` 作为 destination |
| plan_metadata 里没有 pipeline_versions | city_circle 链路未走通 | 查看后端日志，搜索 `_try_city_circle_pipeline` |
| 前端 3000 端口无响应 | Next.js 进程挂了 | 重新启动前端服务 |
| `/plan/<SID>` 返回 404 | 攻略还没生成完 | 等待 status=done 再访问 |
| verify_api.py 11/11 但前端报错 | 前端 API proxy 路由缺失 | 检查 `web/app/api/` 对应路由文件 |

---

## 用于批量测试的不同用例参数

| # | destination | duration | party_type | styles | circle | 说明 |
|---|---|---|---|---|---|---|
| 1 | kansai | 5 | couple | food, photo | kansai_classic_circle | **关西情侣主推用例** |
| 2 | kansai | 7 | family | culture, kids | kansai_classic_circle | 亲子文化游 |
| 3 | tokyo | 5 | couple | food, photo | tokyo_v1 | 东京情侣 |
| 4 | tokyo | 7 | family | culture, kids | tokyo_v1 | 东京亲子 |
| 5 | tokyo | 3 | solo | food, budget | tokyo_v1 | 独旅省钱 |
| 6 | hokkaido | 5 | couple | nature, onsen | — | 北海道温泉（触发 fallback 旧链路） |
| 7 | kansai | 5 | parents | culture, easy | kansai_classic_circle | 带父母轻松游 |
| 8 | okinawa | 4 | couple | beach, diving | — | 冲绳海岛（fallback） |
| 9 | kansai | 9 | family | all | kansai_classic_circle | 关西深度全家游 |
| 10 | tokyo | 5 | solo | anime, shopping | tokyo_v1 | 宅文化秋叶原 |

> **用例 1、3 为优先跑通目标**（覆盖 City-Circle 主链路的两个主圈）。
> 用例 6、8 用于验证 fallback 旧链路是否正常降级（不应报错，只是不走 City-Circle）。
> 每个用例走完全部 13 步即为一个完整测试。

---

## 与自动化测试的关系

| 工具 | 用途 | 命令 |
|---|---|---|
| `scripts/verify_api.py` | 后端 11 个核心接口冒烟测试（当前唯一自动化 E2E 入口）| `python scripts/verify_api.py` |
| `tests/e2e/test_full_pipeline.py` | 后端管线单元级 E2E（34 个 mock 用例）| `python -m pytest tests/e2e/test_full_pipeline.py -v` |
| 本文档（手动） | 前后端联调全漏斗测试（13步业务流程）| 手动按步骤执行 |