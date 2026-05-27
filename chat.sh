#!/usr/bin/env bash
#
# chat.sh — open an interactive conversation with local DeepSeek-V4-Flash.
#
# This is the plain `-cnv` (conversation) mode: type messages, get replies,
# Ctrl-C to quit.
#
# Usage:
#   ./chat.sh
#   ./chat.sh -sys "you are a terse rust expert"   # extra flags pass through
#
# Env overrides: see config.sh (LLAMA_BIN, MODEL, CTX_SIZE).

set -euo pipefail
cd "$(dirname "$0")"
source ./config.sh

exec "$LLAMA_BIN" \
  -m "$MODEL" \
  -c "$CTX_SIZE" \
  -cnv \
  "$@"
