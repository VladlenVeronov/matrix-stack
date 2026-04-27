#!/usr/bin/env sh
# Sygnal entrypoint — renders config from envsubst template.
set -eu

CFG=/data/sygnal.yaml
TMPL=/etc/sygnal/sygnal.yaml.tmpl

mkdir -p /data
echo "[sygnal-entrypoint] rendering ${CFG}…"
envsubst < "${TMPL}" > "${CFG}"

exec python -m sygnal.sygnal --config-path "${CFG}"
