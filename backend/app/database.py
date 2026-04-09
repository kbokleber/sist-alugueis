from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create all tables (used for dev/SQLite)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def ensure_property_code_column():
    async with engine.begin() as conn:
        if "sqlite" in settings.database_url:
            result = await conn.exec_driver_sql("PRAGMA table_info(properties)")
            columns = [row[1] for row in result.fetchall()]
            if "code" not in columns:
                await conn.exec_driver_sql("ALTER TABLE properties ADD COLUMN code VARCHAR(50)")
            return

        if "postgresql" in settings.database_url or "postgres" in settings.database_url:
            result = await conn.exec_driver_sql(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'properties' AND column_name = 'code'
                """
            )
            if result.first() is None:
                await conn.exec_driver_sql("ALTER TABLE properties ADD COLUMN code VARCHAR(50)")


async def ensure_property_image_url_column():
    async with engine.begin() as conn:
        if "sqlite" in settings.database_url:
            result = await conn.exec_driver_sql("PRAGMA table_info(properties)")
            columns = [row[1] for row in result.fetchall()]
            if "image_url" not in columns:
                await conn.exec_driver_sql("ALTER TABLE properties ADD COLUMN image_url TEXT")
            return

        if "postgresql" in settings.database_url or "postgres" in settings.database_url:
            result = await conn.exec_driver_sql(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'properties' AND column_name = 'image_url'
                """
            )
            if result.first() is None:
                await conn.exec_driver_sql("ALTER TABLE properties ADD COLUMN image_url TEXT")


async def ensure_revenue_pending_amount_column():
    async with engine.begin() as conn:
        if "sqlite" in settings.database_url:
            result = await conn.exec_driver_sql("PRAGMA table_info(rental_revenues)")
            columns = [row[1] for row in result.fetchall()]
            if "pending_amount" not in columns:
                await conn.exec_driver_sql(
                    "ALTER TABLE rental_revenues ADD COLUMN pending_amount NUMERIC(15, 2)"
                )
            return

        if "postgresql" in settings.database_url or "postgres" in settings.database_url:
            result = await conn.exec_driver_sql(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'rental_revenues' AND column_name = 'pending_amount'
                """
            )
            if result.first() is None:
                await conn.exec_driver_sql(
                    "ALTER TABLE rental_revenues ADD COLUMN pending_amount NUMERIC(15, 2)"
                )
