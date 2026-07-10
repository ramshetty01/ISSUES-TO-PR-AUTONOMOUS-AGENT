#!/usr/bin/env bash
#
# setup-github-app.sh — guide creation of the GitHub App used by the agent and
# scaffold the local .env secrets it needs.
#
# This is intentionally interactive: creating a GitHub App requires a browser
# and a human to click "Create". We can't mint the App ID / private key from a
# shell, so this script (a) opens the App-manifest flow, (b) prints the exact
# permissions to grant (see docs/github-app-permissions.md), and (c) helps you
# paste the resulting secrets into .env.
#
# Re-running is safe: it never overwrites a non-empty secret without asking.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
MANIFEST="${ROOT_DIR}/examples/github-app-manifest.example.json"

echo "==> issue-to-pr-agent :: GitHub App setup"
echo

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "==> No .env found; creating one from .env.example"
  cp "${ROOT_DIR}/.env.example" "${ENV_FILE}"
fi

cat <<'EOF'
1. Create the App from the manifest (recommended):
   https://github.com/settings/apps/new?state=itpr

   Or create it manually with these permissions (Repository level):
     - Contents:       Read & write   (clone repo, push branches)
     - Issues:         Read & write   (read issue, post ack/result comments)
     - Pull requests:  Read & write   (open the fix PR)
     - Metadata:       Read-only      (mandatory)
     - Administration: Read-only      (verify branch protection)
   Subscribe to events: Issues, Issue comment, Pull request.
   Webhook URL: your SMEE_URL (run scripts/setup-smee.sh first).

2. After creating the App:
     - copy the numeric "App ID"
     - generate a private key (.pem) and download it
     - set a webhook secret

See docs/github-app-permissions.md for the full rationale.
EOF

echo
echo "==> Reference manifest: ${MANIFEST}"
echo "==> Now paste the values (leave blank to keep the current .env value)."
echo

# Idempotent .env key setter: updates in place or appends; skips empty inputs.
set_env() {
  local key="$1" value="$2"
  [[ -z "${value}" ]] && return 0
  if grep -qE "^#?[[:space:]]*${key}=" "${ENV_FILE}"; then
    # Replace the (possibly commented) line with an active assignment.
    local tmp
    tmp="$(mktemp)"
    sed -E "s|^#?[[:space:]]*${key}=.*|${key}=${value}|" "${ENV_FILE}" >"${tmp}"
    mv "${tmp}" "${ENV_FILE}"
  else
    printf '%s=%s\n' "${key}" "${value}" >>"${ENV_FILE}"
  fi
  echo "    set ${key}"
}

read -r -p "GITHUB_APP_ID: " APP_ID || true
read -r -p "GITHUB_WEBHOOK_SECRET: " WEBHOOK_SECRET || true
read -r -p "Path to private key .pem (contents are inlined): " PEM_PATH || true

set_env "GITHUB_APP_ID" "${APP_ID:-}"
set_env "GITHUB_WEBHOOK_SECRET" "${WEBHOOK_SECRET:-}"

if [[ -n "${PEM_PATH:-}" && -f "${PEM_PATH}" ]]; then
  # Store the PEM as a single-line value with escaped newlines (config reverses this).
  PEM_ONE_LINE="$(awk 'BEGIN{ORS="\\n"} {print}' "${PEM_PATH}")"
  set_env "GITHUB_APP_PRIVATE_KEY" "\"${PEM_ONE_LINE}\""
fi

echo
echo "==> Done. Verify with: pnpm --filter @itpr/github-app dev"
