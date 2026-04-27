#!/usr/bin/env bash
# =============================================================
# Synapse entrypoint — renders config from template, ensures
# signing key exists, then exec's the upstream image entrypoint.
# =============================================================
set -euo pipefail

DATA_DIR=/data
TMPL=/etc/matrix-synapse/homeserver.yaml.tmpl
CFG="${DATA_DIR}/homeserver.yaml"
LOGCFG="${DATA_DIR}/log.config"

mkdir -p "${DATA_DIR}/media_store" "${DATA_DIR}/uploads"

# Copy log.config (read-only mount → writable copy)
cp -f /etc/matrix-synapse/log.config "${LOGCFG}"

# Render homeserver.yaml from template
echo "[entrypoint] rendering homeserver.yaml from template…"
envsubst < "${TMPL}" > "${CFG}"

# First-boot signing key
if [[ ! -f "${DATA_DIR}/signing.key" ]]; then
  echo "[entrypoint] generating signing key (first run)…"
  python -m synapse.app.homeserver \
    --config-path "${CFG}" \
    --generate-keys
fi

echo "[entrypoint] launching synapse…"
exec python -m synapse.app.homeserver --config-path "${CFG}"
