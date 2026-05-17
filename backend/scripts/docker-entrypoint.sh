#!/bin/sh
set -eu

# Allow docker-compose dev override: entrypoint.sh uvicorn ...
if [ "$#" -gt 0 ]; then
  exec "$@"
fi

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
