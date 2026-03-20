import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# ── Alembic Config object ─────────────────────────────────────────────────────
config = context.config

# ── Python logging from alembic.ini ─────────────────────────────────────────
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Import all models for autogenerate ────────────────────────────────────────
from app.db.session import Base  # noqa: E402
import app.db.models  # noqa: E402, F401

target_metadata = Base.metadata

# ── DB URL: 直接从 settings 取，绕过 configparser 的 % 转义问题 ─────────────────
from app.core.config import settings  # noqa: E402

DATABASE_URL = settings.database_url  # asyncpg URL，可能含 %21 等编码字符


def run_migrations_offline() -> None:
    """offline 模式：生成 SQL 脚本，不连接真实 DB。"""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """直接用 create_async_engine 构造引擎，避免 configparser 解析 URL。"""
    connectable = create_async_engine(DATABASE_URL, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
