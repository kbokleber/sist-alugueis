#!/bin/sh
# Smoke test for production (run on the server).
# Usage: ./scripts/prod-check.sh [domain] [frontend_port]
set -eu

DOMAIN="${1:-alugueis.kbosolucoes.com.br}"
FRONTEND_PORT="${2:-3001}"

echo "== Docker: app containers =="
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'frontend-|backend-|coolify-proxy' || true

echo ""
echo "== Duplicate releases (should be only ONE frontend/backend pair) =="
COUNT="$(docker ps --format '{{.Names}}' | grep -c '^frontend-' || true)"
if [ "$COUNT" -gt 1 ]; then
  echo "WARN: more than one frontend container running ($COUNT)"
fi

echo ""
echo "== Frontend local :$FRONTEND_PORT =="
curl -fsSI "http://127.0.0.1:${FRONTEND_PORT}/" | head -n 1 || echo "FAIL"

echo ""
echo "== Public HTTPS =="
curl -fsSI "https://${DOMAIN}/" | head -n 1 || echo "FAIL"

echo ""
echo "== Backend readiness (first backend container) =="
BACKEND="$(docker ps --format '{{.Names}}' | grep '^backend-' | head -n 1 || true)"
if [ -n "$BACKEND" ]; then
  docker exec "$BACKEND" curl -fsS "http://127.0.0.1:8000/health/ready" && echo "" || echo "FAIL"
else
  echo "No backend container found"
fi

echo ""
echo "Done."
