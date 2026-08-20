from collections.abc import AsyncIterator
from ssl import CERT_NONE, create_default_context
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import certifi
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import Settings
from app.infrastructure import models as persistence_models  # noqa: F401


def _async_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url.removeprefix("postgresql://")
    elif url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url.removeprefix("postgres://")
    if url.startswith("sqlite"):
        return url
    parts = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parts.query) if key.lower() != "ssl"]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def build_engine(settings: Settings) -> AsyncEngine:
    url = _async_database_url(settings.database_url)
    connect_args: dict = {}
    engine_kwargs: dict = {"connect_args": connect_args, "future": True, "pool_pre_ping": True}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    elif "+asyncpg" in url:
        ssl_context = create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = False
        ssl_context.verify_mode = CERT_NONE
        connect_args["ssl"] = ssl_context
        connect_args["statement_cache_size"] = 0
        engine_kwargs["pool_size"] = 5
        engine_kwargs["max_overflow"] = 5
    return create_async_engine(url, **engine_kwargs)


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)
    await ensure_pgvector(engine)
    await ensure_postgres_enums(engine)


async def ensure_pgvector(engine: AsyncEngine) -> None:
    if engine.dialect.name != "postgresql":
        return
    statements = (
        "CREATE EXTENSION IF NOT EXISTS vector",
        "ALTER TABLE brand_chunks ADD COLUMN IF NOT EXISTS embedding vector(1536)",
        "ALTER TABLE brands ADD COLUMN IF NOT EXISTS activated_at TIMESTAMPTZ",
    )
    try:
        async with engine.begin() as connection:
            for statement in statements:
                await connection.execute(text(statement))
    except Exception:
        return


async def ensure_postgres_enums(engine: AsyncEngine) -> None:
    """create_all no altera enums existentes: IMAGE_PROMPT se añadió después."""
    if engine.dialect.name != "postgresql":
        return
    try:
        async with engine.connect() as connection:
            autocommit = await connection.execution_options(isolation_level="AUTOCOMMIT")
            await autocommit.execute(
                text("ALTER TYPE assetkind ADD VALUE IF NOT EXISTS 'IMAGE_PROMPT'")
            )
    except Exception:
        return


async def session_scope(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with factory() as session:
        yield session
