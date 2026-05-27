# deepseek-exploration

Poking at a **local DeepSeek-V4-Flash** running on [llama.cpp](https://github.com/ggml-org/llama.cpp) to see how well it handles real tasks — no API, no cloud, just the GGUF on this machine.

## What's running

- **Model:** `DeepSeek-V4-Flash-IQ2XXS-w2Q2K-AProjQ8-SExpQ8-OutQ8-chat-v2.gguf` (~81 GB quantized)
- **Runtime:** `llama-cli` (llama.cpp, build b8927)
- **Hardware:** Apple M3 Max, Metal backend (~83 GB resident, ~20 tok/s generation)

This is a `-chat` build, so it applies a chat template and emits an explicit reasoning trace (`[Start thinking] … [End thinking]`) before its answer.

## Setup

The scripts assume these paths (override with env vars — see [`config.sh`](./config.sh)):

| Var         | Default                                                                 |
|-------------|-------------------------------------------------------------------------|
| `LLAMA_BIN` | `~/tools/llama-dsv4/build/bin/llama-cli`                                 |
| `MODEL`     | `~/models/deepseek-v4-flash/DeepSeek-V4-Flash-...-chat-v2.gguf`          |
| `CTX_SIZE`  | `4096`                                                                   |

The model weights are **not** in this repo (they're 81 GB — see `.gitignore`).

## Usage

### One-shot prompt — `ask.sh`

Single turn, then exits. Good for scripting and piping.

```bash
./ask.sh "what is the capital of France?"

# pipe from stdin
echo "summarize this: ..." | ./ask.sh

# cap the number of tokens generated
./ask.sh -n 1024 "write a bubble sort in rust"

# add a system prompt
SYS_PROMPT="you are a terse rust expert" ./ask.sh "explain lifetimes"
```

Example (trimmed):

```
> Reply with exactly one short sentence: what model are you?

[Start thinking]
... the user wants a single short sentence ...
[End thinking]

I am DeepSeek

[ Prompt: 38.7 t/s | Generation: 20.2 t/s ]
```

> Note: in single-turn mode llama.cpp prints its startup banner and the model's
> thinking trace to stdout alongside the answer. That's intentional here — the
> whole point is to watch *how* the model reasons.

### Interactive chat — `chat.sh`

The plain conversation loop. Type messages, get replies, `Ctrl-C` or `/exit` to quit.

```bash
./chat.sh
./chat.sh -sys "you are a helpful pair programmer"   # extra flags pass through
```

## Files

- `config.sh` — shared paths/settings, sourced by the scripts (env-overridable).
- `ask.sh` — non-interactive single prompt → reply.
- `chat.sh` — interactive conversation mode.
