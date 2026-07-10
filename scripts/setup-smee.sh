#!/usr/bin/env bash
#
# setup-smee.sh — create (or reuse) a smee.io channel and record it as SMEE_URL
# in .env so the local github-app can receive GitHub webhooks without a public
# ingress. See docs/github-app-permissions.md for how the webhook is used.
#
# Idempotent: if .env already has a usable SMEE_URL we keep it unless --force is
# given. Otherwise we allocate a fresh channel from https://smee.io/new.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
FORCE=0
[[ "${1:-}" == "--force" ]] && FORCE=1

if [[ ! -f "${ENV_FILE}" ]]; then
  cp "${ROOT_DIR}/.env.example" "${ENV_FILE}"
fi

current_url() {
  # Print the active SMEE_URL value (empty if unset/commented/blank).
  sed -nE 's|^[[:space:]]*SMEE_URL=([^[:space:]#]+).*|\1|p' "${ENV_FILE}" | head -n1
}

EXISTING="$(current_url || true)"
if [[ -n "${EXISTING}" && "${FORCE}" -eq 0 ]]; then
  echo "==> SMEE_URL already set: ${EXISTING} (use --force to replace)"
  exit 0
fi

echo "==> Allocating a new smee.io channel..."
# smee.io/new issues a 302 to the freshly-minted channel URL. We read the
# Location header rather than the body so no HTML parsing is needed.
NEW_URL="$(curl -fsS -o /dev/null -w '%{redirect_url}' https://smee.io/new || true)"

if [[ -z "${NEW_URL}" ]]; then
  echo "!! Could not reach smee.io. Set SMEE_URL manually in .env." >&2
  exit 1
fi

# Idempotent write: replace an existing (possibly commented) SMEE_URL line, else append.
if grep -qE '^#?[[:space:]]*SMEE_URL=' "${ENV_FILE}"; then
  tmp="$(mktemp)"
  sed -E "s|^#?[[:space:]]*SMEE_URL=.*|SMEE_URL=${NEW_URL}|" "${ENV_FILE}" >"${tmp}"
  mv "${tmp}" "${ENV_FILE}"
else
  printf 'SMEE_URL=%s\n' "${NEW_URL}" >>"${ENV_FILE}"
fi

echo "==> SMEE_URL=${NEW_URL}"
echo "==> Set this as the GitHub App webhook URL, then run scripts/run-local-webhook.ts"
