#!/bin/sh
set -eu

# Coolify renomeia serviços por release (ex.: backend-i2a5...). SERVICE_NAME_BACKEND
# é injetado automaticamente; aliases "backend" no compose cobrem deploy manual.
if [ -z "${BACKEND_UPSTREAM:-}" ]; then
  BACKEND_HOST="${SERVICE_NAME_BACKEND:-backend}"
  BACKEND_UPSTREAM="http://${BACKEND_HOST}:8000"
fi
export BACKEND_UPSTREAM

echo "[entrypoint] API proxy upstream=${BACKEND_UPSTREAM}"
envsubst '${BACKEND_UPSTREAM}' < /etc/nginx/templates/default.conf.template \
  > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
