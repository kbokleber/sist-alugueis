#!/bin/sh
# Smoke test for production (run on the server).
# Usage: ./scripts/prod-check.sh [frontend_domain] [api_domain] [frontend_port]
set -eu

FRONTEND_DOMAIN="${1:-alugueis.kbosolucoes.com.br}"
API_DOMAIN="${2:-alugueis-api.kbosolucoes.com.br}"
FRONTEND_PORT="${3:-3001}"

fail=0
warn() { echo "WARN: $*"; }
ok() { echo "OK: $*"; }
bad() { echo "FAIL: $*"; fail=1; }

echo "== Coolify / Traefik proxy =="
if docker ps --format '{{.Names}}' | grep -q '^coolify-proxy$'; then
  MISSING="$(docker logs --since 5m coolify-proxy 2>&1 | grep -c 'port is missing' || true)"
  if [ "$MISSING" -gt 0 ]; then
    bad "coolify-proxy: $MISSING erro(s) 'port is missing' nos últimos 5 min (Traefik instável)"
    docker logs --since 5m coolify-proxy 2>&1 | grep 'port is missing' | tail -n 5
  else
    ok "coolify-proxy sem 'port is missing' nos últimos 5 min"
  fi
else
  warn "container coolify-proxy não encontrado"
fi

echo ""
echo "== Docker: releases do aluguel =="
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'frontend-|backend-|sist_alugueis' || true

FRONTEND_COUNT="$(docker ps --format '{{.Names}}' | grep -c '^frontend-' || true)"
BACKEND_COUNT="$(docker ps --format '{{.Names}}' | grep -c '^backend-' || true)"
if [ "$FRONTEND_COUNT" -gt 1 ] || [ "$BACKEND_COUNT" -gt 1 ]; then
  bad "releases duplicadas (frontend=$FRONTEND_COUNT backend=$BACKEND_COUNT) — causa 504 intermitente"
else
  ok "uma release ativa (frontend=$FRONTEND_COUNT backend=$BACKEND_COUNT)"
fi

echo ""
echo "== Frontend local :$FRONTEND_PORT =="
if curl -fsSI --max-time 10 "http://127.0.0.1:${FRONTEND_PORT}/" | head -n 1 | grep -qE '200|301|302'; then
  ok "SPA http://127.0.0.1:${FRONTEND_PORT}/"
else
  bad "SPA http://127.0.0.1:${FRONTEND_PORT}/"
fi

if curl -fsS --max-time 10 "http://127.0.0.1:${FRONTEND_PORT}/health/api" >/dev/null 2>&1; then
  ok "API via nginx proxy /health/api"
else
  bad "API via nginx proxy /health/api (frontend up mas backend inacessível)"
fi

echo ""
echo "== Backend readiness (primeiro container backend-*) =="
BACKEND="$(docker ps --format '{{.Names}}' | grep '^backend-' | head -n 1 || true)"
if [ -n "$BACKEND" ]; then
  if docker exec "$BACKEND" curl -fsS --max-time 10 "http://127.0.0.1:8000/health/ready" >/dev/null 2>&1; then
    ok "backend $BACKEND /health/ready"
  else
    bad "backend $BACKEND /health/ready"
  fi
else
  bad "nenhum container backend-* encontrado"
fi

echo ""
echo "== Domínios públicos HTTPS =="
if curl -fsSI --max-time 15 "https://${FRONTEND_DOMAIN}/" | head -n 1 | grep -qE '200|301|302'; then
  ok "https://${FRONTEND_DOMAIN}/"
else
  bad "https://${FRONTEND_DOMAIN}/"
fi

if curl -fsS --max-time 15 "https://${FRONTEND_DOMAIN}/health/api" >/dev/null 2>&1; then
  ok "https://${FRONTEND_DOMAIN}/health/api (same-origin API)"
else
  bad "https://${FRONTEND_DOMAIN}/health/api"
fi

echo ""
echo "== Diagnóstico Coolify verde x site fora =="
LOCAL_API=0
PUBLIC_SITE=0
PUBLIC_API=0
curl -fsS --max-time 10 "http://127.0.0.1:${FRONTEND_PORT}/health/api" >/dev/null 2>&1 && LOCAL_API=1
curl -fsSI --max-time 15 "https://${FRONTEND_DOMAIN}/" | head -n 1 | grep -qE '200|301|302' && PUBLIC_SITE=1
curl -fsS --max-time 15 "https://${FRONTEND_DOMAIN}/health/api" >/dev/null 2>&1 && PUBLIC_API=1

if [ "$LOCAL_API" -eq 1 ] && [ "$PUBLIC_SITE" -eq 0 ]; then
  bad "LOCAL=OK PUBLIC=FAIL → proxy Traefik quebrado (Coolify pode continuar verde)"
  echo "      Ação: docker restart coolify-proxy + corrigir Hermes port is missing"
elif [ "$LOCAL_API" -eq 0 ]; then
  bad "LOCAL=FAIL → container/app (Coolify deveria marcar unhealthy com /health/api)"
elif [ "$PUBLIC_SITE" -eq 1 ] && [ "$PUBLIC_API" -eq 0 ]; then
  bad "site abre mas API pública falha → nginx→backend ou CORS"
else
  ok "LOCAL e PUBLIC consistentes"
fi

echo ""
if curl -fsSI --max-time 15 "https://${API_DOMAIN}/health/ready" | head -n 1 | grep -qE '200|301|302'; then
  ok "https://${API_DOMAIN}/health/ready (API externa / Hermes)"
else
  warn "https://${API_DOMAIN}/health/ready indisponível (ok se domínio API não estiver publicado)"
fi

echo ""
if [ "$fail" -eq 0 ]; then
  echo "Resultado: PASS"
else
  echo "Resultado: FAIL — veja docs/passo-a-passo-corrigir-504-coolify.md"
  exit 1
fi
