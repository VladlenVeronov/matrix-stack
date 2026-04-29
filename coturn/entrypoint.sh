#!/bin/sh
# =============================================================
# coturn entrypoint — render config from template, then exec.
# =============================================================
set -eu

TMPL=/etc/coturn/turnserver.conf.tmpl
CFG=/etc/coturn/turnserver.conf

: "${COTURN_REALM:?COTURN_REALM is required}"
: "${COTURN_EXTERNAL_IP:?COTURN_EXTERNAL_IP is required}"
: "${COTURN_STATIC_AUTH_SECRET:?COTURN_STATIC_AUTH_SECRET is required}"

echo "[coturn] rendering turnserver.conf from template…"
envsubst < "$TMPL" > "$CFG"

echo "[coturn] launching turnserver on port 3478 (relay 49152-49200)…"
exec turnserver -c "$CFG"
