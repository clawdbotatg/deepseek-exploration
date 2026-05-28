#!/usr/bin/env python3
"""
agent.py — let local DeepSeek decide when to make web requests.

This is the agentic "Level 2" web access. It talks to llama-server's
OpenAI-compatible API, advertises a `fetch_url` tool, and runs the tool-call
loop: the *model* chooses to fetch, we run the request, feed the result back,
and repeat until it produces a final answer.

Prereq — start the server first (separate terminal; loads the model, ~1 min):
    ./server.sh

Usage:
    ./agent.py "Fetch https://example.com and tell me what it's for."
    ./agent.py "Summarize the transcript at <url>, then list the key moments."

Env:
    SERVER_URL   default http://127.0.0.1:8080
    MAX_STEPS    max tool-call rounds before giving up (default 6)

Trace (the model's thinking + each tool call) goes to stderr; the final
answer goes to stdout. Stdlib only.
"""

import json
import os
import sys
import urllib.error
import urllib.request

from fetch import fetch  # reuse the exact cleaning logic the CLI scripts use

SERVER_URL = os.environ.get("SERVER_URL", "http://127.0.0.1:8080").rstrip("/")
MAX_STEPS = int(os.environ.get("MAX_STEPS", "6"))

# The tool we hand the model. Its `parameters` is a JSON Schema.
TOOLS = [{
    "type": "function",
    "function": {
        "name": "fetch_url",
        "description": (
            "Fetch a URL over HTTP(S) and return its readable text content "
            "(HTML stripped, JSON/NDJSON cleaned up). Call this whenever you "
            "need the contents of a web page or document."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to fetch."},
                "max_chars": {
                    "type": "integer",
                    "description": "Optional cap on characters returned (default 40000).",
                },
            },
            "required": ["url"],
        },
    },
}]


def run_tool(name: str, args: dict) -> str:
    """Dispatch a tool call to its implementation."""
    if name == "fetch_url":
        url = args.get("url", "")
        if not url:
            return "ERROR: fetch_url called without a url."
        try:
            return fetch(url, int(args.get("max_chars", 40000)))
        except Exception as e:  # noqa: BLE001 — report failures back to the model
            return f"ERROR fetching {url}: {e}"
    return f"ERROR: unknown tool {name!r}"


def chat(messages: list) -> dict:
    """One round-trip to the server's /v1/chat/completions endpoint."""
    payload = json.dumps({
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
        "temperature": 0.3,
        "max_tokens": 1024,
    }).encode()
    req = urllib.request.Request(
        f"{SERVER_URL}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=1800) as resp:
            return json.load(resp)
    except urllib.error.URLError as e:
        sys.exit(
            f"error: can't reach llama-server at {SERVER_URL} ({e}).\n"
            f"       start it first with ./server.sh"
        )


def main():
    if len(sys.argv) < 2:
        sys.exit('usage: ./agent.py "your task (mention a URL to fetch)"')

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant with a fetch_url tool. When the "
                "user references a URL or asks about a web page or document, "
                "call fetch_url to read it before answering. Base your answer "
                "on the fetched content."
            ),
        },
        {"role": "user", "content": " ".join(sys.argv[1:])},
    ]

    for _ in range(MAX_STEPS):
        msg = chat(messages)["choices"][0]["message"]

        reasoning = msg.get("reasoning_content")
        if reasoning:
            print(f"\n[think] {reasoning.strip()}\n", file=sys.stderr)

        messages.append(msg)
        calls = msg.get("tool_calls") or []
        if not calls:
            print((msg.get("content") or "").strip())
            return

        for tc in calls:
            fn = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            print(f"[tool] -> {fn}({json.dumps(args)})", file=sys.stderr)
            result = run_tool(fn, args)
            print(f"[tool] <- {len(result)} chars", file=sys.stderr)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": result,
            })

    print("[agent] hit MAX_STEPS without a final answer.", file=sys.stderr)


if __name__ == "__main__":
    main()
