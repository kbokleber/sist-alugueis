from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


engine_kwargs = {
    "echo": settings.debug,
    "pool_pre_ping": True,
}

# SQLite (dev) doesn't support pool tuning params used in asyncpg/postgres.
if "sqlite" not in settings.database_url:
    engine_kwargs.update(
        {
            "pool_size": settings.database_pool_size,
            "max_overflow": settings.database_max_overflow,
            "pool_timeout": settings.database_pool_timeout,
            "pool_recycle": settings.database_pool_recycle,
        }
    )

engine = create_async_engine(settings.database_url, **engine_kwargs)

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


async def ensure_property_financial_columns():
    async with engine.begin() as conn:
        if "sqlite" in settings.database_url:
            result = await conn.exec_driver_sql("PRAGMA table_info(properties)")
            columns = {row[1] for row in result.fetchall()}
            if "default_cleaning_fee" not in columns:
                await conn.exec_driver_sql(
                    "ALTER TABLE properties ADD COLUMN default_cleaning_fee NUMERIC(15, 2) NOT NULL DEFAULT 170.00"
                )
            if "platform_fee_percent" not in columns:
                await conn.exec_driver_sql(
                    "ALTER TABLE properties ADD COLUMN platform_fee_percent NUMERIC(5, 2) NOT NULL DEFAULT 15.00"
                )
            if "default_platform_fee" in columns:
                await conn.exec_driver_sql("ALTER TABLE properties DROP COLUMN default_platform_fee")
            return

        if "postgresql" in settings.database_url or "postgres" in settings.database_url:
            result = await conn.exec_driver_sql(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'properties'
                  AND column_name IN (
                    'default_cleaning_fee',
                    'platform_fee_percent',
                    'default_platform_fee'
                  )
                """
            )
            columns = {row[0] for row in result.fetchall()}
            if "default_cleaning_fee" not in columns:
                await conn.exec_driver_sql(
                    "ALTER TABLE properties ADD COLUMN default_cleaning_fee NUMERIC(15, 2) NOT NULL DEFAULT 170.00"
                )
            if "platform_fee_percent" not in columns:
                await conn.exec_driver_sql(
                    "ALTER TABLE properties ADD COLUMN platform_fee_percent NUMERIC(5, 2) NOT NULL DEFAULT 15.00"
                )
            if "default_platform_fee" in columns:
                await conn.exec_driver_sql(
                    "ALTER TABLE properties DROP COLUMN default_platform_fee"
                )


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


async def ensure_user_app_profile_column():
    async with engine.begin() as conn:
        if "sqlite" in settings.database_url:
            result = await conn.exec_driver_sql("PRAGMA table_info(users)")
            columns = [row[1] for row in result.fetchall()]
            if "app_profile" not in columns:
                await conn.exec_driver_sql(
                    "ALTER TABLE users ADD COLUMN app_profile VARCHAR(20) NOT NULL DEFAULT 'full'"
                )
            return

        if "postgresql" in settings.database_url or "postgres" in settings.database_url:
            result = await conn.exec_driver_sql(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'app_profile'
                """
            )
            if result.first() is None:
                await conn.exec_driver_sql(
                    "ALTER TABLE users ADD COLUMN app_profile VARCHAR(20) NOT NULL DEFAULT 'full'"
                )


_INVENTORY_ITEM_DETAIL_COLUMNS = {
    "color": "ALTER TABLE property_inventory_items ADD COLUMN color VARCHAR(100)",
    "serial_number": "ALTER TABLE property_inventory_items ADD COLUMN serial_number VARCHAR(150)",
    "brand": "ALTER TABLE property_inventory_items ADD COLUMN brand VARCHAR(100)",
    "model": "ALTER TABLE property_inventory_items ADD COLUMN model VARCHAR(150)",
    "image_url": "ALTER TABLE property_inventory_items ADD COLUMN image_url TEXT",
}


async def ensure_inventory_item_detail_columns():
    async with engine.begin() as conn:
        if "sqlite" in settings.database_url:
            result = await conn.exec_driver_sql("PRAGMA table_info(property_inventory_items)")
            columns = {row[1] for row in result.fetchall()}
            if not columns:
                return
            for column, ddl in _INVENTORY_ITEM_DETAIL_COLUMNS.items():
                if column not in columns:
                    await conn.exec_driver_sql(ddl)
            return

        if "postgresql" in settings.database_url or "postgres" in settings.database_url:
            result = await conn.exec_driver_sql(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'property_inventory_items'
                """
            )
            columns = {row[0] for row in result.fetchall()}
            if not columns:
                return
            for column, ddl in _INVENTORY_ITEM_DETAIL_COLUMNS.items():
                if column not in columns:
                    await conn.exec_driver_sql(ddl)


async def ensure_checklist_incident_image_column():
    async with engine.begin() as conn:
        if "sqlite" in settings.database_url:
            result = await conn.exec_driver_sql("PRAGMA table_info(stay_checklist_items)")
            columns = {row[1] for row in result.fetchall()}
            if columns and "incident_image_url" not in columns:
                await conn.exec_driver_sql(
                    "ALTER TABLE stay_checklist_items ADD COLUMN incident_image_url TEXT"
                )
            return

        if "postgresql" in settings.database_url or "postgres" in settings.database_url:
            result = await conn.exec_driver_sql(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'stay_checklist_items'
                  AND column_name = 'incident_image_url'
                """
            )
            if result.first() is None:
                await conn.exec_driver_sql(
                    "ALTER TABLE stay_checklist_items ADD COLUMN incident_image_url TEXT"
                )


async def ensure_consumable_columns():
    sqlite_targets = (
        (
            "property_inventory_items",
            "ALTER TABLE property_inventory_items ADD COLUMN is_consumable BOOLEAN NOT NULL DEFAULT 0",
        ),
        (
            "stay_checklist_items",
            "ALTER TABLE stay_checklist_items ADD COLUMN is_consumable BOOLEAN NOT NULL DEFAULT 0",
        ),
    )
    pg_targets = (
        (
            "property_inventory_items",
            "ALTER TABLE property_inventory_items ADD COLUMN is_consumable BOOLEAN NOT NULL DEFAULT false",
        ),
        (
            "stay_checklist_items",
            "ALTER TABLE stay_checklist_items ADD COLUMN is_consumable BOOLEAN NOT NULL DEFAULT false",
        ),
    )
    async with engine.begin() as conn:
        if "sqlite" in settings.database_url:
            for table, ddl in sqlite_targets:
                result = await conn.exec_driver_sql(f"PRAGMA table_info({table})")
                columns = {row[1] for row in result.fetchall()}
                if columns and "is_consumable" not in columns:
                    await conn.exec_driver_sql(ddl)
            return

        if "postgresql" in settings.database_url or "postgres" in settings.database_url:
            for table, ddl in pg_targets:
                result = await conn.exec_driver_sql(
                    f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = '{table}' AND column_name = 'is_consumable'
                    """
                )
                if result.first() is None:
                    await conn.exec_driver_sql(ddl)


async def ensure_inventory_categories_property_scope():
    """Garante categorias de inventário por imóvel (não por usuário)."""
    import uuid as uuid_mod

    from sqlalchemy import text

    defaults_shared = [("Sala", 1), ("Banheiro", 2), ("Cozinha", 3)]
    andorinhas_extra = [("Quarto casal", 4), ("Quarto solteiro", 5)]
    on_domingos_extra = [("Quarto", 4)]

    def _wanted_for(prop_name: str) -> list[tuple[str, int]]:
        lower = (prop_name or "").lower()
        if "andorinhas" in lower:
            return [*defaults_shared, *andorinhas_extra]
        if "domingos" in lower:
            return [*defaults_shared, *on_domingos_extra]
        return []

    async with engine.begin() as conn:
        if "sqlite" not in settings.database_url:
            return

        result = await conn.exec_driver_sql("PRAGMA table_info(inventory_categories)")
        columns = {row[1] for row in result.fetchall()}
        if not columns:
            return

        already_ok = "property_id" in columns and "user_id" not in columns

        async def seed_named_properties() -> None:
            props = (
                await conn.execute(text("SELECT id, name FROM properties WHERE is_active = 1"))
            ).fetchall()
            for prop_id, prop_name in props:
                wanted = _wanted_for(prop_name or "")
                if not wanted:
                    continue
                pid = str(prop_id).replace("-", "").lower()
                existing_rows = (
                    await conn.execute(
                        text(
                            "SELECT lower(name) FROM inventory_categories WHERE property_id = :pid"
                        ),
                        {"pid": pid},
                    )
                ).fetchall()
                existing = {row[0] for row in existing_rows}
                for name, order in wanted:
                    if name.lower() in existing:
                        continue
                    await conn.execute(
                        text(
                            "INSERT INTO inventory_categories "
                            "(id, property_id, name, sort_order, is_active, created_at, updated_at) "
                            "VALUES (:id, :property_id, :name, :sort_order, 1, CURRENT_TIMESTAMP, NULL)"
                        ),
                        {
                            "id": uuid_mod.uuid4().hex,
                            "property_id": pid,
                            "name": name,
                            "sort_order": order,
                        },
                    )

        if already_ok:
            await seed_named_properties()
            return

        old_cats = (
            await conn.execute(
                text("SELECT id, name, sort_order, is_active FROM inventory_categories")
            )
        ).fetchall()
        cat_meta = {
            str(r[0]).replace("-", "").lower(): {
                "name": r[1],
                "sort_order": r[2] or 0,
                "is_active": 1 if r[3] else 0,
            }
            for r in old_cats
        }
        items = (
            await conn.execute(
                text("SELECT id, property_id, category_id FROM property_inventory_items")
            )
        ).fetchall()
        props = (await conn.execute(text("SELECT id, name FROM properties"))).fetchall()

        await conn.exec_driver_sql(
            "ALTER TABLE inventory_categories RENAME TO inventory_categories_old"
        )
        await conn.exec_driver_sql(
            """
            CREATE TABLE inventory_categories (
                id CHAR(32) NOT NULL PRIMARY KEY,
                property_id CHAR(32) NOT NULL,
                name VARCHAR(100) NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL,
                updated_at DATETIME,
                CONSTRAINT uq_inventory_categories_property_name UNIQUE (property_id, name),
                FOREIGN KEY(property_id) REFERENCES properties (id)
            )
            """
        )
        await conn.exec_driver_sql(
            "CREATE INDEX ix_inventory_categories_property_id ON inventory_categories (property_id)"
        )

        pending_inserts: list[tuple] = []
        property_cats: dict[str, dict[str, str]] = {}

        def ensure_cat(pid: str, name: str, sort_order: int, is_active: int = 1) -> str:
            key = name.strip().lower()
            bucket = property_cats.setdefault(pid, {})
            if key in bucket:
                return bucket[key]
            new_id = uuid_mod.uuid4().hex
            bucket[key] = new_id
            pending_inserts.append((new_id, pid, name.strip(), sort_order, is_active))
            return new_id

        for item_id, property_id, category_id in items:
            pid = str(property_id).replace("-", "").lower()
            cid = str(category_id).replace("-", "").lower()
            meta = cat_meta.get(cid)
            if not meta:
                continue
            new_cid = ensure_cat(pid, meta["name"], meta["sort_order"], meta["is_active"])
            await conn.execute(
                text(
                    "UPDATE property_inventory_items SET category_id = :cid WHERE id = :id"
                ),
                {"cid": new_cid, "id": str(item_id).replace("-", "").lower()},
            )

        for prop_id, prop_name in props:
            pid = str(prop_id).replace("-", "").lower()
            for name, order in _wanted_for(prop_name or ""):
                ensure_cat(pid, name, order)

        for row in pending_inserts:
            await conn.execute(
                text(
                    "INSERT INTO inventory_categories "
                    "(id, property_id, name, sort_order, is_active, created_at, updated_at) "
                    "VALUES (:id, :property_id, :name, :sort_order, :is_active, CURRENT_TIMESTAMP, NULL)"
                ),
                {
                    "id": row[0],
                    "property_id": row[1],
                    "name": row[2],
                    "sort_order": row[3],
                    "is_active": row[4],
                },
            )

        await conn.exec_driver_sql("DROP TABLE inventory_categories_old")
