#!/usr/bin/env bash
#
# web-summarize.sh — fetch a URL and have local DeepSeek summarize it.
#
# Level-1 "web access": the script does the HTTP request (via fetch.py), then
# feeds the cleaned content to the model. The model reasons over the page; it
# doesn't decide to browse — that's what the agentic version (see README) adds.
#
# Usage:
#   ./web-summarize.sh <url>
#   ./web-summarize.sh <url> "list the key decisions, with timestamps"
#
# Args:
#   $1  url to fetch (required)
#   $2  instruction (optional; defaults to a general summary)
#
# Env overrides: CTX_SIZE (default 16384 here — transcripts are big),
#                N_PREDICT (default 800), plus LLAMA_BIN/MODEL from config.sh.

set -euo pipefail
cd "$(dirname "$0")"

URL="${1:-}"
if [ -z "$URL" ]; then
  echo "usage: ./web-summarize.sh <url> [instruction]" >&2
  exit 1
fi
INSTRUCTION="${2:-Summarize the following content. Give a concise overview, then the key points as bullets.}"

# Bigger context than the default — fetched pages don't fit in 4096 tokens.
export CTX_SIZE="${CTX_SIZE:-16384}"
export N_PREDICT="${N_PREDICT:-800}"

# Fetch first so a network error fails before we spend a minute loading the model.
CONTENT="$(python3 ./fetch.py "$URL")"

# Build the prompt and pipe it to the model on stdin (avoids argv size limits).
{
  printf '%s\n\n' "$INSTRUCTION"
  printf -- '--- BEGIN CONTENT (from %s) ---\n' "$URL"
  printf '%s\n' "$CONTENT"
  printf -- '--- END CONTENT ---\n'
} | ./ask.sh
