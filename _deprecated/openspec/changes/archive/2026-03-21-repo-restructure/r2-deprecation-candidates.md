# R2. 废弃代码与文档识别报告

> 方法：基于 R1 体检结果，对所有疑似废弃文件做引用扫描（import/require/配置/路由/文档互链）
> 原则：确认无引用 → delete_candidate；有不确定性 → archive；有引用 → keep

---

## 表 1：删除候选清单（确认无引用，可安全删除）

| # | 路径 | 类型 | 引用扫描结果 | 删除理由 |
|---|---|---|---|---|
| 1 | `data/gf_after_click1.png` | 截图 | 无引用 | Google Flights 调试截图 |
| 2 | `data/gf_after_click2.png` | 截图 | 无引用 | 同上 |
| 3 | `data/gf_after_done.png` | 截图 | 无引用 | 同上 |
| 4 | `data/gf_before_select.png` | 截图 | 无引用 | 同上 |
| 5 | `data/gf_cal_after_nav.png` | 截图 | 无引用 | 同上 |
| 6 | `data/gf_cal_july.png` | 截图 | 无引用 | 同上 |
| 7 | `data/gf_calendar.png` | 截图 | 无引用 | 同上 |
| 8 | `data/gf_dates_selected.png` | 截图 | 无引用 | 同上 |
| 9 | `data/gf_dep_selected.png` | 截图 | 无引用 | 同上 |
| 10 | `data/gf_final_results.png` | 截图 | 无引用 | 同上 |
| 11 | `data/gf_jul_selected.png` | 截图 | 无引用 | 同上 |
| 12 | `data/gf_july.png` | 截图 | 无引用 | 同上 |
| 13 | `data/gf_results.png` | 截图 | 无引用 | 同上 |
| 14 | `data/gf_step1.png` | 截图 | 无引用 | 同上 |
| 15 | `data/gf_step2_origin_clicked.png` | 截图 | 无引用 | 同上 |
| 16 | `data/gf_step3_typed.png` | 截图 | 无引用 | 同上 |
| 17 | `data/flights_raw/gf_error.png` | 截图 | `google_flights.py` 中有文件名但仅为注释 | 调试截图 |
| 18 | `data/sakura/screenshots/` | 目录 | 无引用 | 爬虫调试截图目录 |
| 19 | `exports/*.html` `exports/*.pdf` | 构建产物 | 无代码引用，运行时生成 | 每次可重新生成 |
| 20 | `logs/tags_tokyo.log` | 日志 | 无引用 | 运行日志 |

**总计 20 项，均为调试截图/构建产物/日志，删除无风险。**

---

## 表 2：归档候选清单（疑似废弃但有不确定性，先移入 archive/）

| # | 路径 | 类型 | 引用扫描结果 | 归档理由 |
|---|---|---|---|---|
| 1 | `web/app/generating/[id]/` | 前端页面 | **无被其他页面引用**（路由是独立的） | 流程改为微信交付，不再需要即时生成等待页 |
| 2 | `web/app/preview/[id]/` | 前端页面 | **无被其他页面引用** | 流程改为微信交付免费预览 |
| 3 | `web/app/checkout/[id]/` | 前端页面 | **无被其他页面引用** | 流程改为微信转账 |
| 4 | `web/app/questionnaire/[id]/` | 前端页面 | **无被其他页面引用** | 流程改为微信追问 |
| 5 | `web/app/rush/` | 前端页面 | **自引用**（rush/page.tsx 引用 rush 组件） | 早期樱花追踪功能，已不是核心产品 |
| 6 | `web/components/rush/` | 前端组件 | 只被 `web/app/rush/page.tsx` 引用 | 跟随 rush 页面一起归档 |
| 7 | `web/app/city/` | 前端页面 | 被 `generating/` 和 `rush/` 引用，**但这两个也要归档** | 早期城市展示页 |
| 8 | `web/app/custom/` | 前端页面 | 只有 `custom/page.tsx` 自己 + `HeroSection` 中有 "custom" 字符串 | 需确认：是否是当前定制入口？ |
| 9 | `web/components/custom/` | 前端组件 | 只被 `web/app/custom/page.tsx` 引用 | 跟随 custom 页面 |
| 10 | `sakura-rush-2026/*.html`（全目录） | 静态HTML | **无代码引用** | 早期樱花攻略成品，已被 templates/magazine/ 替代 |
| 11 | `data/sakura/custom_onepage.html` | 静态HTML | 无代码引用 | 早期单页展示 |
| 12 | `data/sakura/custom_tailwind.html` | 静态HTML | 无代码引用 | 早期 Tailwind 版展示 |
| 13 | `data/sakura/index.html` | 静态HTML | 无代码引用 | 早期首页 |
| 14 | `data/sakura/sakura_rush.html` | 静态HTML | 无代码引用 | 早期樱花展示 |
| 15 | `data/sakura/xiaohongshu*.html`（3个） | 静态HTML | `xiaohongshu.py` 爬虫可能输出到此 | 早期小红书展示页 |
| 16 | `docs/custom_tailwind.html` | 静态HTML | 无引用 | docs里不该有HTML |
| 17 | `docs/index.html` | 静态HTML | 无引用 | 同上 |
| 18 | `docs/sakura_rush.html` | 静态HTML | 无引用 | 同上 |
| 19 | `docs/xiaohongshu*.html`（3个） | 静态HTML | 无引用 | 同上 |
| 20 | `docs/DELIVERY_PAGE_DESIGN.md` | 文档 | 无被其他文档引用 | 已被 openspec delivery-page spec 替代 |
| 21 | `docs/PRICING_AND_FEATURES.md` | 文档 | 无被其他文档引用 | 已被 openspec master-product-strategy 替代 |
| 22 | `docs/PRICING.md` | 文档 | 无被其他文档引用 | 与上面重复 |
| 23 | `docs/PRODUCT_TIERS_V2.md` | 文档 | 被 `seed_product_skus.py` 引用（注释） | 已被 openspec 替代，但脚本注释提到 |
| 24 | `docs/PROJECT_PLAN.md` | 文档 | 被 `README.md` 引用 | 旧版项目计划 |
| 25 | `docs/SAKURA_DISPLAY_PLAN.md` | 文档 | 无引用 | 旧版 |
| 26 | `docs/SAKURA_SYSTEM_PLAN.md` | 文档 | 无引用 | 旧版 |
| 27 | `docs/TASK_SPLIT_V4.md` | 文档 | 自引用链 | 旧版任务拆分 |
| 28 | `docs/A19-A27_DELIVERY_PREVIEW_QUESTIONNAIRE.md` | 文档 | 无引用 | 已被 openspec 替代 |
| 29 | `scripts/crawlers/AI_TASK_SPLIT.md` | 文档 | 无引用 | V1历史版本 |
| 30 | `scripts/crawlers/AI_TASK_SPLIT_V2.md` | 文档 | 自引用 | V2历史版本 |
| 31 | `scripts/crawlers/AI_TASK_SPLIT_V3.md` | 文档 | 自引用 | V3历史版本 |

**总计 31 项。建议统一移入 `archive/` 目录，保留 60 天后再评估删除。**

---

## 表 3：高风险不可动清单（核心文件，unsafe_to_touch）

| # | 路径 | 原因 |
|---|---|---|
| 1 | `app/` 整个目录 | 后端核心，所有模块有复杂引用链 |
| 2 | `app/core/config.py` | 全局配置入口，几乎所有模块依赖 |
| 3 | `app/db/models/` | 数据模型，Alembic迁移依赖 |
| 4 | `app/db/migrations/` | 数据库迁移历史，删除会导致迁移断链 |
| 5 | `app/domains/` 所有子目录 | 业务核心，互相引用 |
| 6 | `templates/magazine/` | Jinja2模板，被渲染引擎引用 |
| 7 | `data/route_templates/` | 路线模板，被规划引擎引用 |
| 8 | `data/*.json`（根级配置） | 评分/路由/权重配置，被多个模块引用 |
| 9 | `web/app/plan/` | 交付页核心，微信发的H5链接指向此 |
| 10 | `web/app/quiz/` | 轻问卷，当前漏斗入口 |
| 11 | `web/app/submitted/` | 提交成功页，新建的核心页面 |
| 12 | `web/app/pricing/` | 价格页，引流页面 |
| 13 | `web/components/ui/` | 基础UI组件，被所有页面引用 |
| 14 | `web/components/shared/` | 共享组件（FloatingCTA等） |
| 15 | `web/lib/` | 工具函数/常量/动画，全局依赖 |
| 16 | `openspec/` | 项目核心spec文档 |
| 17 | `scripts/crawlers/*.py` | 爬虫代码，活跃使用 |
| 18 | `.env.example` | 环境变量模板 |
| 19 | `docker-compose.yml` / `Dockerfile` | 部署配置 |
| 20 | `pyproject.toml` / `alembic.ini` | 项目配置 |

---

## 表 4：重复内容合并建议

| # | 重复项 | 建议 |
|---|---|---|
| 1 | `docs/PRICING.md` + `docs/PRICING_AND_FEATURES.md` + `docs/PRODUCT_TIERS_V2.md` | 三个都讲定价，全部归档，以 `openspec/.../master-product-strategy.md` 为准 |
| 2 | `data/sakura/*.html` + `docs/*.html` + `sakura-rush-2026/*.html` | 三处存放早期HTML展示页，合并归档到 `archive/legacy-html/` |
| 3 | `scripts/crawlers/AI_TASK_SPLIT.md` + `V2.md` + `V3.md` + `docs/TASK_SPLIT_V4.md` | 4 个版本的任务拆分，保留最新版归档，其余删除 |
| 4 | `data/sakura/weathernews_all_spots.json` + `docs/weathernews_all_spots.json` | 同一数据文件在两处，保留 `data/` 的，删 `docs/` 的 |
| 5 | `web/components/social/` | 需确认是否与小红书内容引擎（S6/S7）有关；如已废弃则归档 |

---

## 执行建议

### 第一步：直接删除（表1，无风险）
```
rm data/gf_*.png
rm data/flights_raw/gf_error.png
rm -rf data/sakura/screenshots/
rm -rf exports/
rm logs/tags_tokyo.log
```

### 第二步：归档（表2）
```
mkdir -p archive/legacy-html
mkdir -p archive/legacy-docs
mkdir -p archive/legacy-web-pages

# 早期HTML
mv sakura-rush-2026/ archive/legacy-html/
mv data/sakura/*.html archive/legacy-html/
mv docs/*.html archive/legacy-html/

# 废弃前端页面
mv web/app/generating/ archive/legacy-web-pages/
mv web/app/preview/ archive/legacy-web-pages/
mv web/app/checkout/ archive/legacy-web-pages/
mv web/app/questionnaire/ archive/legacy-web-pages/
mv web/app/rush/ archive/legacy-web-pages/
mv web/app/city/ archive/legacy-web-pages/
mv web/components/rush/ archive/legacy-web-pages/components-rush/

# 废弃文档
mv docs/DELIVERY_PAGE_DESIGN.md archive/legacy-docs/
mv docs/PRICING_AND_FEATURES.md archive/legacy-docs/
mv docs/PRICING.md archive/legacy-docs/
mv docs/PRODUCT_TIERS_V2.md archive/legacy-docs/
mv docs/PROJECT_PLAN.md archive/legacy-docs/
mv docs/SAKURA_DISPLAY_PLAN.md archive/legacy-docs/
mv docs/SAKURA_SYSTEM_PLAN.md archive/legacy-docs/
mv docs/TASK_SPLIT_V4.md archive/legacy-docs/
mv docs/A19-A27_DELIVERY_PREVIEW_QUESTIONNAIRE.md archive/legacy-docs/
mv scripts/crawlers/AI_TASK_SPLIT*.md archive/legacy-docs/
```

### 第三步：需要你确认的项
1. `web/app/custom/` — 是当前定制入口还是已废弃？
2. `web/components/social/` — 是否与小红书引擎相关？
3. `docs/weathernews_all_spots.json` — 直接移到 `data/sakura/` 还是删除？