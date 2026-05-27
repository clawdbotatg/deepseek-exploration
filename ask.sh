#!/usr/bin/env bash
#
# ask.sh — send a single prompt to local DeepSeek-V4-Flash and print the reply.
#
# Non-interactive: runs one turn and exits, so it's easy to script / pipe.
#
# Usage:
#   ./ask.sh "what is the capital of France?"
#   echo "summarize this: ..." | ./ask.sh
#   ./ask.sh -n 1024 "write a haiku about gpus"     # -n caps tokens generated
#
# Env overrides (see config.sh): LLAMA_BIN, MODEL, CTX_SIZE, plus:
#   N_PREDICT   max tokens to generate (default 512; -1 = unlimited)
#   SYS_PROMPT  optional system prompt

set -euo pipefail
cd "$(dirname "$0")"
source ./config.sh

N_PREDICT="${N_PREDICT:-512}"

# Allow an inline -n / --n-predict flag before the prompt.
if [ "${1:-}" = "-n" ] || [ "${1:-}" = "--n-predict" ]; then
  N_PREDICT="$2"
  shift 2
fi

# Prompt comes from args, or from stdin if no args were given.
if [ "$#" -gt 0 ]; then
  PROMPT="$*"
else
  PROMPT="$(cat)"
fi

if [ -z "${PROMPT//[[:space:]]/}" ]; then
  echo "error: empty prompt. pass it as an argument or pipe it on stdin." >&2
  exit 1
fi

SYS_ARGS=()
if [ -n "${SYS_PROMPT:-}" ]; then
  SYS_ARGS=(-sys "$SYS_PROMPT")
fi

# -st        : single turn, then exit (non-interactive because -p is set)
# --simple-io: cleaner output for subprocess/pipe use
# Metal/loader logs go to stderr; the model's reply goes to stdout.
exec "$LLAMA_BIN" \
  -m "$MODEL" \
  -c "$CTX_SIZE" \
  -n "$N_PREDICT" \
  -st \
  --simple-io \
  "${SYS_ARGS[@]}" \
  -p "$PROMPT"
