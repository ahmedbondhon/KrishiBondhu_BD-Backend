# ============================================================================
# KrishiBondhu Bangladesh — Alembic env.py
# Async migration environment for PostgreSQL
# ============================================================================

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import get_settings
from app.db.session import Base

# Import all models so Alembic can detect them
from app.models.auth import (  # noqa: F401
    AdminAction,
    ConsentType,
    LoginAttempt,
    OtpLog,
    RefreshToken,
    Role,
    User,
    UserConsent,
)
from app.models.geo import District, Division, Union, Upazila  # noqa: F401

# Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url from settings
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

# Target metadata for autogenerate
target_metadata = Base.metadata


def include_name(name, type_, parent_names):
    """Include auth, geo, and audit schema objects in migrations."""
    if type_ == "schema":
        return name in ("auth", "geo", "audit")
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_name=include_name,
        version_table_schema="auth",
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        include_name=include_name,
        version_table_schema="auth",
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Ensure auth schema exists
        await connection.execute(text("CREATE SCHEMA IF NOT EXISTS auth"))
        await connection.commit()
        await connection.run_sync(do_run_migrations)
        await connection.commit()

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
