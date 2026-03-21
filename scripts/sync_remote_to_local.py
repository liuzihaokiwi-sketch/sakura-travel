"""从 Supabase 远端同步全量数据到本地 PostgreSQL

用法: python scripts/sync_remote_to_local.py
"""
import asyncio
import json
import os
import ssl
import traceback
import uuid
from datetime import date, datetime
from decimal import Decimal
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, inspect

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
PROJECT_ID = SUPABASE_URL.replace("https://", "").split(".")[0]
SUPA_PW = os.getenv("SUPABASE_DB_PASSWORD", "")
LOCAL_URL = os.getenv("DATABASE_URL", "")
REMOTE_URL = f"postgresql+asyncpg://postgres.{PROJECT_ID}:{SUPA_PW}@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE


async def get_remote_tables(engine) -> list[str]:
    """动态获取远端所有 public schema 的表名"""
    async with engine.begin() as conn:
        r = await conn.execute(text(
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname = 'public' "
            "ORDER BY tablename"
        ))
        return [row[0] for row in r.fetchall()]


async def get_local_tables(engine) -> set[str]:
    """获取本地已有的表名"""
    async with engine.begin() as conn:
        r = await conn.execute(text(
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname = 'public'"
        ))
        return {row[0] for row in r.fetchall()}


# 按外键依赖排序：父表在前，子表在后
# 删除时反过来：子表先删
TABLE_ORDER = [
    # 基础表
    "entity_base",
    # CTI 子表
    "pois",
    "hotels",
    "restaurants",
    # 关联表
    "entity_tags",
    "entity_scores",
    "entity_media",
    "entity_editor_notes",
    "hotel_area_guide",
    # 衍生/模板
    "route_templates",
    "render_templates",
    "ranked_lists",
    "entity_score_log",
    # 业务表
    "questionnaire_submissions",
    "trip_plans",
    "trip_plan_days",
    "trip_plan_items",
    # 快照
    "hotel_offers",
    "flight_offers",
    "poi_openings",
    "weather_daily",
    "sakura_forecast",
    # 其他
    "alembic_version",
]


def _sanitize_value(val, udt: str = ""):
    """处理跨数据库类型不匹配的值"""
    if val is None:
        return None
    if isinstance(val, uuid.UUID):
        return str(val)
    if isinstance(val, Decimal):
        return float(val)
    # JSONB/JSON 列：确保是 JSON 字符串
    if udt in ("jsonb", "json"):
        if isinstance(val, str):
            try:
                json.loads(val)
                return val
            except (json.JSONDecodeError, TypeError):
                return json.dumps(val, ensure_ascii=False)
        if isinstance(val, (dict, list)):
            return json.dumps(val, ensure_ascii=False, default=str)
        return json.dumps(val, ensure_ascii=False, default=str)
    if isinstance(val, (dict, list)):
        return json.dumps(val, ensure_ascii=False, default=str)
    # timestamptz 列：如果值是字符串（Supabase pooler 返回 ISO 字符串），解析回 datetime
    if udt in ("timestamptz", "timestamp") and isinstance(val, str):
        try:
            return datetime.fromisoformat(val)
        except (ValueError, TypeError):
            return val
    # date 列
    if udt == "date" and isinstance(val, str):
        try:
            return date.fromisoformat(val)
        except (ValueError, TypeError):
            return val
    return val


async def sync_table(remote_engine, local_engine, table_name: str) -> tuple[str, int, str]:
    """同步单张表，返回 (表名, 行数, 状态)"""
    try:
        # 1. 从远端读全量
        async with remote_engine.begin() as rconn:
            cnt_r = await rconn.execute(text(f'SELECT count(*) FROM "{table_name}"'))
            remote_count = cnt_r.scalar()
            if remote_count == 0:
                return (table_name, 0, "远端为空")

            data_r = await rconn.execute(text(f'SELECT * FROM "{table_name}"'))
            columns = list(data_r.keys())
            rows = data_r.fetchall()

        # 2. 获取本地表的列类型信息，用于 CAST
        async with local_engine.begin() as lconn:
            col_types_r = await lconn.execute(text(
                f"SELECT column_name, data_type, udt_name "
                f"FROM information_schema.columns "
                f"WHERE table_name = :tbl AND table_schema = 'public'"
            ), {"tbl": table_name})
            local_col_types = {r[0]: (r[1], r[2]) for r in col_types_r.fetchall()}

        # 3. 写入本地
        async with local_engine.begin() as lconn:
            await lconn.execute(text("SET session_replication_role = 'replica'"))
            await lconn.execute(text(f'DELETE FROM "{table_name}"'))

            if rows:
                # 构建 INSERT 语句，对 UUID/JSONB/Vector 列加 CAST
                cast_parts = []
                for c in columns:
                    dtype, udt = local_col_types.get(c, ("", ""))
                    if udt == "uuid":
                        cast_parts.append(f"CAST(:{c} AS uuid)")
                    elif udt == "jsonb":
                        cast_parts.append(f"CAST(:{c} AS jsonb)")
                    elif udt == "json":
                        cast_parts.append(f"CAST(:{c} AS json)")
                    elif udt == "vector":
                        cast_parts.append(f"CAST(:{c} AS vector)")
                    elif udt == "numeric":
                        cast_parts.append(f"CAST(:{c} AS numeric)")
                    else:
                        cast_parts.append(f":{c}")

                col_str = ", ".join(f'"{c}"' for c in columns)
                param_str = ", ".join(cast_parts)
                insert_sql = f'INSERT INTO "{table_name}" ({col_str}) VALUES ({param_str})'

                batch_size = 100
                for i in range(0, len(rows), batch_size):
                    batch = rows[i:i + batch_size]
                    params = []
                    for row in batch:
                        d = {}
                        for col, val in zip(columns, row):
                            _, udt = local_col_types.get(col, ("", ""))
                            d[col] = _sanitize_value(val, udt=udt)
                        params.append(d)
                    await lconn.execute(text(insert_sql), params)

            await lconn.execute(text("SET session_replication_role = 'origin'"))

        return (table_name, len(rows), "✅")

    except Exception as e:
        err = str(e)
        if "does not exist" in err:
            return (table_name, 0, "表不存在(跳过)")
        # 打印完整错误以便调试
        short_err = err[:200].replace('\n', ' ')
        return (table_name, 0, f"❌ {short_err}")


async def main():
    print(f"\n{'='*60}")
    print(f"🔄 Supabase → 本地 全量数据同步")
    print(f"   远端: aws-1-ap-northeast-1.pooler.supabase.com")
    print(f"   本地: {LOCAL_URL.split('@')[1] if '@' in LOCAL_URL else 'localhost'}")
    print(f"{'='*60}\n")

    remote_engine = create_async_engine(
        REMOTE_URL, connect_args={"ssl": ssl_ctx},
        pool_size=3, max_overflow=0, pool_timeout=30,
    )
    local_engine = create_async_engine(LOCAL_URL, pool_size=3, max_overflow=0)

    # 获取远端实际存在的表
    remote_tables = await get_remote_tables(remote_engine)
    local_tables = await get_local_tables(local_engine)
    print(f"📊 远端表: {len(remote_tables)} 个, 本地表: {len(local_tables)} 个\n")

    # 过滤：只同步远端有且本地也有的表（按依赖顺序）
    ordered = [t for t in TABLE_ORDER if t in remote_tables and t in local_tables]
    # 加上不在 TABLE_ORDER 里但远端和本地都有的表
    extra = [t for t in remote_tables if t in local_tables and t not in ordered]
    sync_list = ordered + extra

    print(f"📋 计划同步 {len(sync_list)} 张表:\n")

    total_rows = 0
    results = []
    for table in sync_list:
        name, count, status = await sync_table(remote_engine, local_engine, table)
        results.append((name, count, status))
        total_rows += count
        icon = "✅" if status == "✅" else ("⏭️" if "跳过" in status or "为空" in status else "❌")
        print(f"  {icon} {name:30s} {count:>6d} 条  {status}")

    await remote_engine.dispose()
    await local_engine.dispose()

    # 汇总
    success = sum(1 for _, _, s in results if s == "✅")
    skipped = sum(1 for _, _, s in results if "跳过" in s or "为空" in s)
    failed = sum(1 for _, _, s in results if "❌" in s)

    print(f"\n{'='*60}")
    print(f"📊 同步结果: ✅{success} ⏭️{skipped} ❌{failed}  共 {total_rows:,} 条")
    print(f"{'='*60}\n")

    if failed > 0:
        print("❌ 失败项:")
        for name, _, status in results:
            if "❌" in status:
                print(f"   - {name}: {status}")


asyncio.run(main())