#!/usr/bin/env bash
# Sygnal entrypoint — renders config from envsubst template.
# Sygnal reads its config path from the SYGNAL_CONF env var.
set -euo pipefail

CFG=/tmp/sygnal.yaml
TMPL=/etc/sygnal/sygnal.yaml.tmpl

echo "[sygnal-entrypoint] rendering ${CFG}…"
envsubst < "${TMPL}" > "${CFG}"

export SYGNAL_CONF="${CFG}"
exec python -m sygnal.sygnal
