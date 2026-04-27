#!/usr/bin/env sh
# LiveKit entrypoint — render config from envsubst, then exec server.
set -eu

CFG=/etc/livekit/livekit.yaml
TMPL=/etc/livekit/livekit.yaml.tmpl

mkdir -p /etc/livekit
echo "[livekit-entrypoint] rendering ${CFG}…"
envsubst < "${TMPL}" > "${CFG}"

exec /livekit-server --config "${CFG}"
