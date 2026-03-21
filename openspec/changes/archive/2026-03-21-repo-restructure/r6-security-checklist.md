# R6. Git 上传前安全检查

> 扫描时间：2026-03-21
> 基于：R1 全项目体检报告中的安全风险标记
> 状态：✅ 完成

---

## 一、检查总结

| 类别 | 发现数 | P0 | P1 | P2 |
|---|---|---|---|---|
| 🔴 真实密钥泄露 | 1 | 1 | — | — |
| 🟡 .gitignore 缺失条目 | 7 | 2 | 3 | 2 |
| 🟢 API key 硬编码检查 | 6文件 | 0（全部安全） | — | — |
| 🟡 .env.example 不完整 | 6字段 | — | 1 | — |
| 🟡 大文件 | 1 | — | 1 | — |
| 🟡 构建产物/日志 | 4目录 | 2 | 2 | — |
| 🟡 config.py 默认值 | 2 | — | — | 2 |

---

## 二、🔴 P0 — 真实密钥（绝不可入库）

### 2.1 `.env` 文件（P0 🔴 CRITICAL）

**状态**：`.env` 已在 `.gitignore` 中 ✅ — 但 gitignore 极度简陋，仅4行

**发现的真实密钥**：

| 变量 | 类型 | 风险 |
|---|---|---|
| `DATABASE_URL` | PostgreSQL 连接串（含密码 `Pp360808973!`） | 🔴 数据库直接访问 |
| `POSTGRES_PASSWORD` | 数据库密码明文 | 🔴 |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase 匿名key（`sb_publishable_...`） | 🟡 公开key，低风险但应管控 |
| `OPENAI_API_KEY` | OpenAI/中转站 API key（`sk-da2P...`） | 🔴 可被盗刷 |
| `SERPAPI_KEY` | SerpAPI key（`c3c95e...`） | 🔴 按调用计费 |
| `AUTH_SECRET` / `NEXTAUTH_SECRET` | 认证密钥 | 🟡 开发值，但应管控 |
| 被注释的 Supabase 生产URL | 含生产密码 | 🔴 注释中也含敏感信息 |

**处置**：
- [x] `.env` 已在 `.gitignore` — 验证通过（`git check-ignore .env` → 确认被忽略）
- [ ] **操作项**：确认 `.env` 从未被 `git add` 过。如果 git history 中存在，必须用 `git filter-repo` 清除

```bash
# 检查 .env 是否在 git 历史中
git log --all --full-history -- .env
# 如果有记录，必须执行：
pip install git-filter-repo
git filter-repo --path .env --invert-paths
```

---

## 三、🟢 Python 文件 API Key 引用检查（6个文件）

### 逐文件检查结果

| # | 文件 | 取 key 方式 | 硬编码? | 结论 |
|---|---|---|---|---|
| 1 | `app/core/config.py` | `pydantic_settings.BaseSettings` 从 `.env` 加载 | ❌ 无 | ✅ **安全** — 所有字段默认值为空字符串，不含真实密钥 |
| 2 | `app/domains/flights/amadeus_client.py` | `settings.amadeus_client_id` / `settings.amadeus_client_secret` | ❌ 无 | ✅ **安全** — 通过 config 间接读取 |
| 3 | `app/domains/catalog/google_places.py` | 函数参数 `api_key: str`（调用方传入） | ❌ 无 | ✅ **安全** — key 从外部注入，未硬编码 |
| 4 | `app/domains/catalog/serp_sync.py` | `settings.serpapi_key` | ❌ 无 | ✅ **安全** — 通过 config 间接读取 |
| 5 | `scripts/crawlers/google_flights.py` | 无 API key（纯爬虫/Playwright） | N/A | ✅ **安全** — 不涉及 API key |
| 6 | `app/domains/planning/copywriter.py` | `AsyncOpenAI()`（从 `OPENAI_API_KEY` 环境变量自动读取） | ❌ 无 | ✅ **安全** — OpenAI SDK 默认行为 |

### 额外发现：3个隐含 OpenAI 调用点

| 文件 | 取 key 方式 | 结论 |
|---|---|---|
| `app/domains/catalog/tagger.py` | `AsyncOpenAI()`（环境变量） | ✅ 安全 |
| `app/domains/intake/intent_parser.py` | `AsyncOpenAI()`（环境变量） | ✅ 安全 |
| `app/domains/catalog/ai_generator.py` | `AsyncOpenAI()`（环境变量） | ✅ 安全 |

**结论：所有9个涉及 API key 的 Python 文件均无硬编码密钥。** 全部通过 `pydantic-settings` 或 SDK 默认环境变量机制读取。

---

## 四、🟡 .gitignore 缺失条目（P0/P1）

### 当前 `.gitignore`（仅4行，极度不足）

```
.DS_Store
__pycache__/
*.pyc
.env
```

### 必须立即补充的条目

| 条目 | 原因 | 优先级 |
|---|---|---|
| `exports/` | 构建产物（HTML/PDF），1.8MB+ | **P0** |
| `logs/` | 运行日志 | **P0** |
| `web/.next/` | Next.js 编译缓存，100MB+ | **P1** |
| `web/output/` | 导出产物 | **P1** |
| `web/node_modules/` | npm 依赖 | **P1** |
| `node_modules/` | 根级 npm 依赖（如有） | **P1** |
| `*.db` | SQLite 本地数据库 | **P1** |
| `japan_ai.db` | 默认 SQLite 文件 | **P1** |
| `data/*_raw/` | 爬虫原始数据（168KB+会持续增长） | **P2** |
| `data/sakura/screenshots/` | 调试截图 | **P2** |
| `data/gf_*.png` | 调试截图 | **P2** |
| `data/flights_raw/gf_error.png` | 错误截图 | **P2** |
| `.venv/` / `venv/` | Python虚拟环境 | **P1** |
| `*.egg-info/` | Python包构建产物 | **P2** |
| `dist/` / `build/` | 构建目录 | **P2** |
| `.pytest_cache/` | pytest 缓存 | **P2** |
| `.mypy_cache/` | mypy 缓存 | **P2** |
| `.ruff_cache/` | ruff 缓存 | **P2** |
| `*.log` | 日志文件 | **P1** |
| `*.env.local` / `.env.*.local` | 本地环境覆盖 | **P0** |

### 建议的完整 `.gitignore`

```gitignore
# ─── OS ────────────────────────────
.DS_Store
Thumbs.db

# ─── Python ────────────────────────
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
.venv/
venv/
*.db
japan_ai.db
.pytest_cache/
.mypy_cache/
.ruff_cache/

# ─── Node / Next.js ───────────────
node_modules/
web/.next/
web/output/
web/node_modules/

# ─── Secrets ───────────────────────
.env
.env.local
.env.*.local
*.env.local

# ─── Build artifacts ───────────────
exports/
logs/
*.log

# ─── Raw data (regeneratable) ──────
data/events_raw/
data/experiences_raw/
data/flights_raw/
data/hotels_raw/
data/tabelog_raw/
data/sakura/screenshots/
data/gf_*.png
```

---

## 五、🟡 大文件检查

### 超过 5MB 的文件

| 文件 | 大小 | 处置建议 |
|---|---|---|
| `web/public/fonts/NotoSansSC-Regular.ttf` | **17MB** | ⚠️ **P1** — 超出 GitHub 推荐的单文件上限。三选一：① Git LFS 追踪 ② CDN 托管+URL引用 ③ 用 woff2 压缩版（~5MB） |

### 其他目录大小

| 目录 | 大小 | 是否入库 |
|---|---|---|
| `exports/` | 1.8MB | ❌ 构建产物，.gitignore |
| `data/*_raw/`（全部） | ~168KB | ❌ 爬虫原始数据，.gitignore |
| `logs/` | 4KB | ❌ 日志，.gitignore |
| `web/.next/` | 100MB+ | ❌ 已通过 web/.gitignore 或需加入根 .gitignore |

### 建议操作

```bash
# 方案A: Git LFS（推荐）
git lfs install
git lfs track "*.ttf"
git lfs track "*.woff2"
git add .gitattributes

# 方案B: 压缩字体
# pip install fonttools brotli
# pyftsubset NotoSansSC-Regular.ttf --output-file=NotoSansSC-Regular.woff2 --flavor=woff2
```

---

## 六、🟡 构建产物 / 临时文件检查

| 路径 | 类型 | 当前状态 | 处置 |
|---|---|---|---|
| `exports/` | HTML/PDF 生成物 | 存在，未被 .gitignore | **P0** 加入 .gitignore |
| `logs/` | 运行日志 | 存在，未被 .gitignore | **P0** 加入 .gitignore |
| `web/.next/` | Next.js 编译缓存 | 存在，未被 .gitignore | **P1** 加入 .gitignore |
| `web/output/` | 导出产物 | 存在，未被 .gitignore | **P1** 加入 .gitignore |
| `data/sakura/screenshots/` | 调试截图 | 存在 | **P2** 删除 + .gitignore |
| `data/gf_*.png` | Google Flights 调试截图 | 存在 | **P2** 删除 + .gitignore |
| `data/flights_raw/gf_error.png` | 错误截图 | 存在 | **P2** 删除 |

---

## 七、🟡 `.env.example` 完整性检查

`.env.example` 缺少以下在 `.env` 中实际使用的变量：

| 缺失变量 | 在 `.env` 中 | 在 `config.py` 中 | 优先级 |
|---|---|---|---|
| `SERPAPI_KEY` | ✅ 有真实值 | ✅ `serpapi_key` | **P1** 必须补充 |
| `AI_BASE_URL` | ✅ 中转站地址 | ✅ `ai_base_url` | P2 |
| `AI_MODEL` | ✅ claude-opus-4-6 | ✅ `ai_model` | P2 |
| `AI_MODEL_STRONG` | ✅ claude-opus-4-6 | ✅ `ai_model_strong` | P2 |
| `NEXT_PUBLIC_SUPABASE_URL` | ✅ Supabase URL | ❌ 前端使用 | P2 |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | ✅ 匿名 key | ❌ 前端使用 | P2 |

**操作项**：更新 `.env.example` 补充缺失变量（使用占位值，不含真实密钥）

---

## 八、🟡 `config.py` 默认值审查

| 字段 | 默认值 | 风险 | 建议 |
|---|---|---|---|
| `secret_key` | `"change_me_in_production"` | 🟡 低 — 明确标注需更改 | ✅ 可接受 |
| `postgres_password` | `"japan_ai_dev"` | 🟡 低 — 仅本地开发 | ✅ 可接受，但建议改为空字符串 |
| `database_url` | `"sqlite+aiosqlite:///./japan_ai.db"` | 🟢 无风险 | ✅ 安全 |
| 所有 API key 字段 | `""` (空字符串) | 🟢 无风险 | ✅ 安全 |

---

## 九、✅ 上传前操作清单

### P0 — 上传前必须完成

- [ ] **1. 确认 `.env` 不在 git 历史中**
  ```bash
  git log --all --full-history -- .env
  ```
  如有记录 → `git filter-repo --path .env --invert-paths`

- [ ] **2. 补全 `.gitignore`**（见第四章完整建议）

- [ ] **3. 清理已暂存的构建产物**
  ```bash
  git rm -r --cached exports/ logs/ 2>/dev/null
  git rm -r --cached web/.next/ web/output/ 2>/dev/null
  ```

### P1 — 首次推送前完成

- [ ] **4. 处理大字体文件**（Git LFS 或压缩）
  ```bash
  git lfs track "web/public/fonts/*.ttf"
  ```

- [ ] **5. 更新 `.env.example`**（补充缺失的 `SERPAPI_KEY` 等6个变量）

- [ ] **6. 删除调试截图**
  ```bash
  rm -f data/gf_*.png data/flights_raw/gf_error.png
  rm -rf data/sakura/screenshots/
  ```

### P2 — 后续迭代

- [ ] **7. 考虑 pre-commit hook** 防止未来意外提交密钥
  ```yaml
  # .pre-commit-config.yaml
  repos:
    - repo: https://github.com/gitleaks/gitleaks
      rev: v8.18.0
      hooks:
        - id: gitleaks
  ```

- [ ] **8. 定期轮换已暴露的密钥**（如果 `.env` 曾被提交）

---

## 十、安全检查矩阵（速查）

| 检查项 | 结果 | 风险 |
|---|---|---|
| `.env` 在 .gitignore 中？ | ✅ 是 | — |
| `.env` 在 git 历史中？ | ⚠️ 需手动验证 | 如有则 P0 |
| Python 文件硬编码密钥？ | ✅ 无（9个文件全部安全） | — |
| 前端文件硬编码密钥？ | ✅ 无 | — |
| .gitignore 覆盖构建产物？ | ❌ 不足（仅4行） | P0 |
| 大文件（>10MB）？ | ⚠️ 1个（17MB字体） | P1 |
| 调试截图/临时文件？ | ⚠️ 若干 | P2 |
| `.env.example` 完整？ | ❌ 缺6个变量 | P1 |
