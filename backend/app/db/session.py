"""
db/session.py
=============
Async SQLAlchemy database engine and session factory setup.

Architecture:
  - Uses SQLAlchemy 2.0 async engine with asyncpg driver for non-blocking I/O.
  - `async_session_factory` is an AsyncSession factory bound to the engine.
  - `get_engine()` creates the engine lazily (called once at startup).
  - All database models use `DeclarativeBase` from `db/base.py`.

Why async?
  FastAPI is built on async Python (asyncio). Using an async DB engine ensures
  that database I/O does NOT block the event loop, keeping the API highly
  concurrent without needing multiple threads.
"""

import ssl
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


def _build_engine():
    """
    Build async engine with SSL support for cloud databases (Neon, Supabase, etc.).
    asyncpg does not accept `sslmode` or `channel_binding` as URL query params.
    We strip them and pass SSL context via connect_args instead.
    """
    db_url = settings.database_url

    # Strip asyncpg-incompatible SSL query params
    parsed = urlparse(db_url)
    params = parse_qs(parsed.query)
    needs_ssl = params.pop("sslmode", ["disable"])[0] in ("require", "verify-ca", "verify-full")
    params.pop("channel_binding", None)  # asyncpg doesn't support this param
    clean_query = urlencode({k: v[0] for k, v in params.items()})
    clean_url = urlunparse(parsed._replace(query=clean_query))

    connect_args = {}
    if needs_ssl:
        ssl_ctx = ssl.create_default_context()
        if settings.environment.lower() == "production":
            ssl_ctx.check_hostname = True
            ssl_ctx.verify_mode = ssl.CERT_REQUIRED
        else:
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_ctx

    return create_async_engine(
        clean_url,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        connect_args=connect_args,
    )


engine = _build_engine()


# Session factory: each call produces a new AsyncSession.
# expire_on_commit=False: keeps model attributes accessible after commit
# without issuing additional SELECT queries.
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
