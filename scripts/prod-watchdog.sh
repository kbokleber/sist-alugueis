#!/bin/sh
# Monitor externo: detecta "Coolify verde mas site fora".
# Rode no SERVIDOR via cron (a cada 2–5 min). Não substitui corrigir Hermes/proxy.
#
# Usage:
#   ./scripts/prod-watchdog.sh [frontend_domain] [frontend_port] [log_file]
#
# Cron example (root):
#   */3 * * * * /path/to/sist-alugueis/scripts/prod-watchdog.sh >> /var/log/sist-alugueis-watchdog.log 2>&1
set -eu

FRONTEND_DOMAIN="${1:-alugueis.kbosolucoes.com.br}"
FRONTEND_PORT="${2:-3001}"
LOG_FILE="${3:-/var/log/sist-alugueis-watchdog.log}"

ts() { date -Iseconds 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S%z'; }
log() { echo "$(ts) $*"; }

check() {
  curl -fsS --max-time 12 "$1" >/dev/null 2>&1
}

LOCAL_URL="http://127.0.0.1:${FRONTEND_PORT}/health/api"
PUBLIC_URL="https://${FRONTEND_DOMAIN}/health/api"

local_ok=0
public_ok=0
check "$LOCAL_URL" && local_ok=1
check "$PUBLIC_URL" && public_ok=1

if [ "$local_ok" -eq 1 ] && [ "$public_ok" -eq 1 ]; then
  log "OK local+public"
  exit 0
fi

# Diagnóstico: local OK + público FAIL = Traefik/proxy (Coolify continua verde)
if [ "$local_ok" -eq 1 ] && [ "$public_ok" -eq 0 ]; then
  missing=0
  if docker ps --format '{{.Names}}' | grep -q '^coolify-proxy$'; then
    missing="$(docker logs --since 3m coolify-proxy 2>&1 | grep -c 'port is missing' || true)"
  fi
  log "FAIL public_only local=${LOCAL_URL} public=${PUBLIC_URL} proxy_port_missing=${missing} action=restart_coolify-proxy"
  docker restart coolify-proxy >/dev/null 2>&1 || true
  sleep 15
  if check "$PUBLIC_URL"; then
    log "RECOVERED after proxy restart"
    exit 0
  fi
  log "STILL_DOWN after proxy restart — fix Hermes gateway/dashboard domains (port is missing)"
  exit 1
fi

# local FAIL: app/container (Coolify deveria marcar unhealthy após deploy novo com /health/api)
log "FAIL local_and_or_public local=${LOCAL_URL} public=${PUBLIC_URL} action=restart_frontend_backend"

FRONTEND="$(docker ps --format '{{.Names}}' | grep '^frontend-' | head -n 1 || true)"
BACKEND="$(docker ps --format '{{.Names}}' | grep '^backend-' | head -n 1 || true)"

if [ -n "$FRONTEND" ]; then
  log "restarting ${FRONTEND}"
  docker restart "$FRONTEND" >/dev/null 2>&1 || true
fi
if [ -n "$BACKEND" ] && [ "$local_ok" -eq 0 ]; then
  log "restarting ${BACKEND}"
  docker restart "$BACKEND" >/dev/null 2>&1 || true
fi

exit 1
