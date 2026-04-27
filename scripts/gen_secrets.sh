#!/usr/bin/env bash
# =============================================================
# gen_secrets.sh — fills in the __GENERATE_ME__ placeholders
# in .env with cryptographically random values.
#
# Usage:
#   cp .env.example .env
#   ./scripts/gen_secrets.sh         # in-place edit of ./.env
#   ./scripts/gen_secrets.sh path/to/.env
#
# Idempotent: only replaces lines whose value is __GENERATE_ME__.
# =============================================================
set -euo pipefail

ENV_FILE="${1:-.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "error: $ENV_FILE not found. Copy .env.example first." >&2
  exit 1
fi

gen() {
  # 48 bytes → 64 base64 chars; URL-safe so no escaping needed in YAML
  openssl rand -base64 48 | tr -d '\n' | tr '/+' '_-'
}

# Use a tmp file because in-place sed differs between BSD/GNU
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

while IFS= read -r line; do
  if [[ "$line" =~ ^([A-Z0-9_]+)=__GENERATE_ME__$ ]]; then
    key="${BASH_REMATCH[1]}"
    value="$(gen)"
    echo "$key=$value" >> "$TMP"
    echo "  ✓ generated  $key"
  else
    echo "$line" >> "$TMP"
  fi
done < "$ENV_FILE"

mv "$TMP" "$ENV_FILE"
chmod 600 "$ENV_FILE"
echo
echo "✅ $ENV_FILE updated (chmod 600)."
echo "   Remaining manual values still marked with __FROM_*__ or __FILL_*__ — fill before deploy."
