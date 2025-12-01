import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from alembic.config import Config
from alembic import command

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://visit:visit@db:5432/visit"
)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)
Base = declarative_base()


async def init_db():
    # Run Alembic upgrade to head
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


async def get_session() -> AsyncSession:
    # Для тестов на sqlite без миграций — создаём таблицы лениво
    if DATABASE_URL.startswith("sqlite") and os.getenv("DISABLE_DB_INIT") == "1":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        yield session
