# Shared config for the DeepSeek-V4-Flash llama.cpp scripts.
# Sourced by the other scripts. Override any of these via environment variables, e.g.
#   LLAMA_BIN=/path/to/llama-cli MODEL=/path/to/model.gguf ./ask.sh "hi"

# Path to the llama.cpp `llama-cli` binary.
LLAMA_BIN="${LLAMA_BIN:-$HOME/tools/llama-dsv4/build/bin/llama-cli}"

# Path to the DeepSeek-V4-Flash GGUF model.
MODEL="${MODEL:-$HOME/models/deepseek-v4-flash/DeepSeek-V4-Flash-IQ2XXS-w2Q2K-AProjQ8-SExpQ8-OutQ8-chat-v2.gguf}"

# Context window size (tokens). The model supports more; keep modest for speed.
CTX_SIZE="${CTX_SIZE:-4096}"

# Fail early with a clear message if the binary or model is missing.
if [ ! -x "$LLAMA_BIN" ]; then
  echo "error: llama-cli not found or not executable at: $LLAMA_BIN" >&2
  echo "       set LLAMA_BIN to override." >&2
  exit 1
fi
if [ ! -f "$MODEL" ]; then
  echo "error: model file not found at: $MODEL" >&2
  echo "       set MODEL to override." >&2
  exit 1
fi
