#!/bin/sh
set -eu

# Allow docker-compose dev override: entrypoint.sh uvicorn ...
if [ "$#" -gt 0 ]; then
  exec "$@"
fi

echo "[entrypoint] waiting for database..."
python - <<'PY'
import asyncio
import os
import sys
import time

import asyncpg

url = os.environ.get("DATABASE_URL", "")
if not url:
    sys.exit("DATABASE_URL is not set")

dsn = url.replace("postgresql+asyncpg://", "postgresql://")

async def wait_db() -> None:
    deadline = time.time() + 90
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            conn = await asyncpg.connect(dsn, timeout=5)
            await conn.execute("SELECT 1")
            await conn.close()
            print("[entrypoint] database is reachable")
            return
        except Exception as exc:
            last_err = exc
            await asyncio.sleep(2)
    raise RuntimeError(f"database not reachable after 90s: {last_err}")

asyncio.run(wait_db())
PY

echo "[entrypoint] alembic upgrade head"
alembic upgrade head

if [ "${RUN_SEED:-false}" = "true" ]; then
  echo "[entrypoint] RUN_SEED=true — running seed_data.py"
  python scripts/seed_data.py
else
  echo "[entrypoint] skipping seed (set RUN_SEED=true only on first deploy)"
fi

echo "[entrypoint] starting gunicorn"
exec gunicorn -c gunicorn.conf.py app.main:app
