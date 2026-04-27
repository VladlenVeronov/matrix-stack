#!/usr/bin/env bash
# =============================================================
# init_admin_user.sh — create the first Synapse admin user.
# Run ONCE after the synapse container is healthy.
#
# Usage (locally):
#   ./scripts/init_admin_user.sh <username> <password>
#
# Usage (on the production server, against the running container):
#   ssh server 'docker exec -it synapse register_new_matrix_user \
#     -c /data/homeserver.yaml -u admin -p <strong> -a \
#     http://localhost:8008'
# =============================================================
set -euo pipefail

USERNAME="${1:?usage: $0 <username> <password>}"
PASSWORD="${2:?usage: $0 <username> <password>}"

docker exec -i synapse register_new_matrix_user \
  -c /data/homeserver.yaml \
  -u "$USERNAME" \
  -p "$PASSWORD" \
  -a \
  http://localhost:8008

echo
echo "✅ Admin user @${USERNAME}:vir.group created."
echo "   Next: log in at https://admin.matrix.vir.group"
echo "   then create an Admin API token (User → Generate access token)"
echo "   and set it as BRIDGE_SYNAPSE_ADMIN_TOKEN in Coolify."
