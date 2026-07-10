#!/usr/bin/env bash
#
# setup-ollama.sh — ensure a local Ollama server is running and the coding model
# the worker uses (qwen2.5-coder) is pulled. Ollama is the zero-cost local
# fallback in the provider chain; see docs/llm-provider-strategy.md.
set -euo pipefail

MODEL="${OLLAMA_MODEL:-qwen2.5-coder}"
OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"

if ! command -v ollama >/dev/null 2>&1; then
  cat >&2 <<'EOF'
!! ollama is not installed.
   macOS:  brew install ollama
   Linux:  curl -fsSL https://ollama.com/install.sh | sh
   Then re-run this script.
EOF
  exit 1
fi

# Start the server in the background if it isn't already responding.
if ! curl -fsS "${OLLAMA_HOST}/api/tags" >/dev/null 2>&1; then
  echo "==> Starting ollama server..."
  ollama serve >/tmp/ollama-serve.log 2>&1 &
  # Wait for the API to come up (up to ~30s).
  for _ in $(seq 1 30); do
    if curl -fsS "${OLLAMA_HOST}/api/tags" >/dev/null 2>&1; then break; fi
    sleep 1
  done
fi

echo "==> Pulling model: ${MODEL}"
ollama pull "${MODEL}"

echo "==> Available models:"
ollama list

echo "==> Done. Set OLLAMA_HOST=${OLLAMA_HOST} in .env if it differs from the default."
