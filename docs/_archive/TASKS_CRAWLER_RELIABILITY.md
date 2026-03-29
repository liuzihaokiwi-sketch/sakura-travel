# 爬虫/数据采集脚本：生产级可靠性改造

> 当前状态：脚本能跑但不可靠——JSON 解析失败、并发封 IP、无断点续传、无监控。
> 目标：改造成可以无人值守跑完 8 个城市圈 41+ 城市的生产级数据管线。

---

## 一、当前问题清单

### 1. 并发过高导致 IP 被封
- 之前每个类别单独调 API（一个城市 20 次调用），间隔只有 0.3 秒
- 已改为批量模式（一个城市 3 次调用），但间隔控制不够稳健
- 没有全局速率限制器，多个城市串行但单城市内的 3 次调用间隔不够

### 2. JSON 解析不稳定
- AI 返回的 JSON 经常不规范（包含 control character、截断、多余文字）
- `_extract_json_array()` 的容错太简单，碰到脏数据直接 crash
- 没有重试机制——解析失败就丢弃整批数据

### 3. 无断点续传
- 脚本从头跑，如果在第 20 个城市失败，前 19 个的进度没问题（已 commit），但需要手动跳过已完成的城市重新跑
- 没有持久化的进度文件记录"哪些城市已完成"

### 4. 无监控
- 日志混在 sqlalchemy 的大量 SQL 日志里，看不到关键信息
- 没有进度输出（"正在处理第 15/41 个城市，已生成 2300 实体"）
- 没有错误汇总（"3 个城市失败，原因：..."）
- 没有运行时间预估

### 5. 数据质量无校验
- AI 生成的数据直接入库，没有检查：坐标是否在合理范围、名字是否为空、评分是否在 1-5 之间
- 重复实体可能被重复写入（name_zh + city_code 相同但 entity_id 不同）

---

## 二、改造目标

```
python scripts/seed_all_production.py --force-ai --resume
```

这一条命令应该能：
1. 自动跳过已完成的城市（断点续传）
2. 全局限速（每次 API 调用间隔 ≥ 10 秒）
3. AI 返回的 JSON 自动清洗 + 重试（最多 3 次）
4. 实时输出进度（每个城市完成时打印一行摘要）
5. 错误不中断（单个城市失败不影响后续城市）
6. 运行结束输出完整报告
7. 进度持久化到 `data/seed_progress.json`

---

## 三、具体改造任务

### Task 1：全局速率限制器

在 `app/core/rate_limiter.py`（已存在）或新建一个模块：

```python
class GlobalRateLimiter:
    """全局 API 调用限速器，确保任意两次调用间隔 >= min_interval_seconds"""

    def __init__(self, min_interval_seconds: float = 10.0):
        self._last_call_time = 0
        self._lock = asyncio.Lock()

    async def wait(self):
        async with self._lock:
            elapsed = time.time() - self._last_call_time
            if elapsed < self.min_interval_seconds:
                await asyncio.sleep(self.min_interval_seconds - elapsed)
            self._last_call_time = time.time()
```

在 `ai_cache.py` 的 `cached_ai_call` 里，调 AI 前先 `await rate_limiter.wait()`。

### Task 2：JSON 清洗 + 重试

改造 `_extract_json_array()`：

```python
def _extract_json_array(text: str) -> str:
    """从 AI 响应中提取 JSON 数组，带容错处理"""
    text = text.strip()

    # 1. 去掉 markdown code block
    # 2. 去掉 JSON 前后的解释文字
    # 3. 修复常见问题：
    #    - 尾部多余逗号 (trailing comma)
    #    - control characters (替换为空格)
    #    - 单引号 → 双引号
    #    - 截断的 JSON（尝试闭合未闭合的括号）
    # 4. 尝试 json.loads，失败则 return "[]"
```

在 `pipeline.py` 的批量生成里加重试：

```python
for attempt in range(3):
    raw = await cached_ai_call(...)
    try:
        data = json.loads(_extract_json_array(raw))
        if data:  # 非空才算成功
            break
    except json.JSONDecodeError:
        logger.warning(f"[{city_code}] JSON parse failed, attempt {attempt+1}/3")
        await asyncio.sleep(5)
else:
    stats["errors"].append(f"JSON parse failed after 3 attempts")
```

### Task 3：断点续传

`seed_all_production.py` 加进度文件：

```python
PROGRESS_FILE = Path("data/seed_progress.json")

# 格式：
{
    "kansai": {
        "kyoto": {"status": "done", "pois": 96, "restaurants": 80, "hotels": 60, "finished_at": "..."},
        "osaka": {"status": "done", ...},
        "nara": {"status": "error", "error": "timeout", ...},
    },
    ...
}
```

启动时读取进度文件，跳过 `status == "done"` 的城市。

### Task 4：进度输出 + 日志分离

```python
# 关闭 sqlalchemy 的 SQL 日志
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# 每个城市完成时输出一行
# [15/41] fukuoka: POI=24 REST=32 HOTEL=16 (12.3s) ✅
# [16/41] nagasaki: ERROR: JSON parse failed ❌
```

运行结束输出完整报告：
```
=== 采集完成 ===
总耗时: 45 分钟
成功: 38/41 城市
失败: 3 城市 (nagoya, biei, hemu)
总实体: POI=1200 REST=1600 HOTEL=800
```

### Task 5：数据质量校验

在 `_write_poi` / `_write_restaurant` / `_write_hotel` 前加校验：

```python
def _validate_entity(data: dict) -> list[str]:
    errors = []
    if not data.get("name_zh"):
        errors.append("name_zh is empty")
    lat, lng = data.get("lat"), data.get("lng")
    if lat and (lat < -90 or lat > 90):
        errors.append(f"lat {lat} out of range")
    if lng and (lng < -180 or lng > 180):
        errors.append(f"lng {lng} out of range")
    rating = data.get("google_rating")
    if rating and (rating < 1 or rating > 5):
        errors.append(f"google_rating {rating} out of range")
    return errors
```

### Task 6：去重

在 upsert 前检查 name_zh + city_code 是否已存在：

```python
existing = await session.execute(
    select(EntityBase).where(
        EntityBase.name_zh == data["name_zh"],
        EntityBase.city_code == data["city_code"],
    )
)
if existing.scalar_one_or_none():
    stats["skipped"] += 1
    continue
```

---

## 四、涉及文件

| 文件 | 改动 |
|------|------|
| `app/core/rate_limiter.py` | 新增或改造全局限速器 |
| `app/core/ai_cache.py` | 接入限速器 |
| `app/domains/catalog/ai_generator.py` | 改造 `_extract_json_array` 容错 |
| `app/domains/catalog/pipeline.py` | 批量生成加重试 + 校验 + 去重 |
| `scripts/seed_all_production.py` | 断点续传 + 进度输出 + 日志分离 |

---

## 五、验收标准

1. `python scripts/seed_all_production.py --force-ai` 能无人值守跑完 41 个城市
2. 中途 Ctrl+C 后重新跑，自动跳过已完成的城市
3. 单个城市失败不影响后续城市
4. JSON 解析失败自动重试（最多 3 次）
5. 不会因并发过高被 API 封 IP
6. 运行结束输出完整的成功/失败/数据量报告
7. `data/seed_progress.json` 实时记录进度
8. 不会写入 name_zh 为空或坐标明显错误的实体
9. 相同 name_zh + city_code 的实体不会重复写入
