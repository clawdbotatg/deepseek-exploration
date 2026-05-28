#!/usr/bin/env bash
#
# server.sh — run llama-server with tool-calling enabled, for the agent.
#
# Loads the 81 GB model and serves an OpenAI-compatible API at
# http://127.0.0.1:8080. `--jinja` turns on the chat template's tool-calling
# support so agent.py can advertise tools the model can invoke.
#
# Run this in its own terminal (it blocks); then run ./agent.py in another.
#
#   ./server.sh
#   PORT=9090 SRV_CTX=16384 ./server.sh    # override port / context
#
# Env: HOST (127.0.0.1), PORT (8080), SRV_CTX (32768 — big, to hold fetched
#      pages as tool results), LLAMA_SERVER (path), plus MODEL from config.sh.

set -euo pipefail
cd "$(dirname "$0")"
source ./config.sh

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8080}"
SRV_CTX="${SRV_CTX:-32768}"
LLAMA_SERVER="${LLAMA_SERVER:-$(dirname "$LLAMA_BIN")/llama-server}"

if [ ! -x "$LLAMA_SERVER" ]; then
  echo "error: llama-server not found at: $LLAMA_SERVER" >&2
  echo "       set LLAMA_SERVER to override." >&2
  exit 1
fi

echo "starting llama-server on http://$HOST:$PORT (ctx=$SRV_CTX, --jinja) ..." >&2
exec "$LLAMA_SERVER" \
  -m "$MODEL" \
  -c "$SRV_CTX" \
  --jinja \
  --host "$HOST" \
  --port "$PORT" \
  "$@"
