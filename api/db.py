import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

_db_host = os.getenv("DB_HOST")
if _db_host:
    _user = os.getenv("PG_USER", "postgres")
    _password = os.getenv("PG_PASSWORD", "1234")
    _name = os.getenv("PG_NAME", "lingwo")
    _port = os.getenv("PG_PORT", "5432")
    DATABASE_URL = f"postgresql+asyncpg://{_user}:{_password}@{_db_host}:{_port}/{_name}"
else:
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:1234@localhost:5432/lingwo",
    )

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Миграция: добавить колонки для оценки сочинения, если их ещё нет
        await conn.execute(text("ALTER TABLE essays ADD COLUMN IF NOT EXISTS max_score DOUBLE PRECISION"))
        await conn.execute(text("ALTER TABLE essays ADD COLUMN IF NOT EXISTS common_mistakes JSONB DEFAULT '[]'::jsonb"))
        await conn.execute(text("ALTER TABLE essays ADD COLUMN IF NOT EXISTS total_score_per DOUBLE PRECISION"))
    # user_settings создаётся через create_all из модели UserSettings