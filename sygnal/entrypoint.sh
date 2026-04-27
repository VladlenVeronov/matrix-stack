#!/usr/bin/env bash
# Sygnal entrypoint — renders config from envsubst template.
set -euo pipefail

CFG=/tmp/sygnal.yaml
TMPL=/etc/sygnal/sygnal.yaml.tmpl

echo "[sygnal-entrypoint] rendering ${CFG}…"
envsubst < "${TMPL}" > "${CFG}"

exec python -m sygnal.sygnal --config-path "${CFG}"
