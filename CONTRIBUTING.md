# Contributing to Travel AI

## Git 宸ヤ綔娴?
### 鍒嗘敮鍛藉悕

| 绫诲瀷 | 鍛藉悕瑙勮寖 | 绀轰緥 |
|------|----------|------|
| 鍔熻兘寮€鍙?| `feature/<name>` | `feature/admin-dashboard` |
| Bug 淇 | `fix/<name>` | `fix/quiz-validation` |
| 閲嶆瀯 | `refactor/<name>` | `refactor/repo-cleanup` |
| 鏂囨。 | `docs/<name>` | `docs/api-guide` |
| 绱ф€ヤ慨澶?| `hotfix/<name>` | `hotfix/payment-error` |

### Commit 瑙勮寖

浣跨敤 [Conventional Commits](https://www.conventionalcommits.org/)锛?
```
<type>(<scope>): <description>

[optional body]
```

**Type**:
- `feat` 鈥?鏂板姛鑳?- `fix` 鈥?Bug 淇
- `chore` 鈥?鏋勫缓/宸ュ叿/渚濊禆
- `docs` 鈥?鏂囨。
- `refactor` 鈥?閲嶆瀯
- `test` 鈥?娴嬭瘯
- `style` 鈥?鏍煎紡璋冩暣

**Scope**: `admin` / `api` / `web` / `scripts` / `db` / `docs`

**绀轰緥**:
```
feat(admin): add order kanban dashboard
fix(api): prevent duplicate quiz submissions
docs: update README with new API endpoints
chore: archive legacy HTML pages
```

### PR 娴佺▼

1. 浠?`main` 鎷夊垎鏀?2. 寮€鍙?+ 鏈湴娴嬭瘯
3. 纭繚 `ruff check` 鍜?`pnpm lint` 閫氳繃
4. 鎻愪氦 PR锛屾弿杩版竻妤氭敼浜嗕粈涔堝拰涓轰粈涔?5. Code review 鍚庡悎骞跺埌 `main`

## 馃帹 浠ｇ爜椋庢牸

### Python锛堝悗绔級

- **Formatter**: [Ruff](https://docs.astral.sh/ruff/) (`ruff format app/ scripts/`)
- **Linter**: [Ruff](https://docs.astral.sh/ruff/) (`ruff check app/ scripts/`)
- 绫诲瀷鏍囨敞: 鎵€鏈夊叕鍏卞嚱鏁板繀椤绘湁绫诲瀷鏍囨敞
- Docstring: 浣跨敤 Google style

```bash
# 涓€閿鏌?+ 淇
ruff check --fix app/ scripts/
ruff format app/ scripts/
```

### TypeScript / React锛堝墠绔級

- **Linter**: ESLint (Next.js 榛樿閰嶇疆)
- **鏍煎紡鍖?*: Prettier锛堝鏈夐厤缃級
- **缁勪欢**: 鍑芥暟缁勪欢 + hooks锛屼笉浣跨敤 class 缁勪欢
- **鏍峰紡**: Tailwind CSS utility classes锛屼笉鍐欒嚜瀹氫箟 CSS

```bash
cd web
pnpm lint        # ESLint 妫€鏌?pnpm lint --fix  # 鑷姩淇
```

### SQL / 鏁版嵁搴?
- **琛ㄥ悕**: snake_case 澶嶆暟锛坄entity_base`, `pois`, `hotels`锛?- **鍒楀悕**: snake_case锛坄city_code`, `entity_type`锛?- **杩佺Щ**: 浣跨敤 Alembic `autogenerate`锛屾瘡娆¤縼绉诲繀椤诲甫鎻忚堪鎬?message

```bash
alembic revision --autogenerate -m "add_name_local_column"
alembic upgrade head
```

## 馃И 娴嬭瘯

- 鏂板姛鑳藉繀椤婚檮甯︽祴璇?- 娴嬭瘯妗嗘灦锛歚pytest` + `pytest-asyncio`
- 鍗曞厓娴嬭瘯浣跨敤 SQLite in-memory锛岄泦鎴愭祴璇曚娇鐢?PostgreSQL

```bash
# 杩愯鍏ㄩ儴娴嬭瘯
pytest -v

# 杩愯鐗瑰畾娴嬭瘯
pytest tests/test_scoring.py -v -k "test_context_score"

# 瑕嗙洊鐜囨姤鍛?pytest --cov=app --cov-report=html
```

## 馃搧 鏂囦欢缁勭粐

- 鍚庣鏂版ā鍧楁斁 `app/domains/<domain>/`
- API 璺敱鏀?`app/api/`
- 鍓嶇椤甸潰鏀?`web/app/<route>/`
- 鍏变韩缁勪欢鏀?`web/components/`
- 鑴氭湰鏀?`scripts/`
- 绉嶅瓙鏁版嵁鏀?`data/seed/`

## 鈿狅笍 娉ㄦ剰浜嬮」

1. **姘歌繙涓嶈鎻愪氦 `.env` 鏂囦欢** 鈥?宸叉湁 pre-commit hook 闃叉姢
2. **鏂板鐜鍙橀噺** 鈫?鍚屾鏇存柊 `.env.example` + `app/core/config.py`
3. **淇敼鏁版嵁搴撴ā鍨?* 鈫?鐢熸垚 Alembic 杩佺Щ鑴氭湰
4. **淇敼楂橀闄╂枃浠?*锛堣瘎鍒嗗紩鎿?/ 琛岀▼瑁呴厤鍣級鈫?蹇呴』鏈夋祴璇曡鐩?

## Dual-Track Test Entry (Team Default)

Primary acceptance vs legacy baseline is now standardized:

- Primary acceptance (blocking): `phase2_acceptance`
- Legacy baseline (non-blocking by default): `legacy_compatibility`

Recommended commands:

```bash
# default team flow: phase2 (blocking) + legacy (non-blocking)
python scripts/ci/run_dual_track_tests.py -q

# primary acceptance only
python scripts/ci/run_dual_track_tests.py --phase2-only -q

# legacy compatibility baseline only
python scripts/ci/run_dual_track_tests.py --legacy-only -q
```

