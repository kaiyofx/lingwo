import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# В Docker compose передаёт DATABASE_URL с хостом pg-lingwo (имя сервиса)
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