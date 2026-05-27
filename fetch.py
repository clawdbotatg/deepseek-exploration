#!/usr/bin/env python3
"""
fetch.py — fetch a URL and emit clean, model-friendly text on stdout.

This is the "web request" primitive: it does the HTTP GET and turns whatever
comes back into something compact enough to drop into a prompt. Content-type
aware so the model doesn't waste tokens on markup / JSON syntax:

  - text/html        -> tags stripped, whitespace collapsed
  - *ndjson*         -> one object per line; chat-shaped objects ({text,handle})
                        render as "handle: text", otherwise compact JSON
  - application/json -> pretty-printed
  - everything else  -> raw text

Usage:
  ./fetch.py <url> [--max-chars N]

Diagnostics (URL, content-type, byte counts, truncation) go to stderr so
stdout stays clean for piping into the model.

No third-party deps — standard library only.
"""

import argparse
import json
import sys
from html.parser import HTMLParser
from urllib.request import Request, urlopen

# Tags whose text content is noise, not prose.
_SKIP_TAGS = {"script", "style", "head", "noscript", "template", "svg"}


class _TextExtractor(HTMLParser):
    """Collect human-readable text from HTML, skipping script/style/etc."""

    def __init__(self):
        super().__init__()
        self._chunks = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth == 0 and data.strip():
            self._chunks.append(data.strip())

    def text(self):
        return "\n".join(self._chunks)


def _render_ndjson(body: str) -> str:
    """Render newline-delimited JSON. Chat-shaped rows -> 'handle: text'."""
    out = []
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            out.append(line)  # not JSON after all; keep verbatim
            continue
        if isinstance(obj, dict) and "text" in obj:
            who = obj.get("handle") or obj.get("anonId") or obj.get("address") or "?"
            out.append(f"{who}: {obj['text']}")
        else:
            out.append(json.dumps(obj, separators=(",", ":")))
    return "\n".join(out)


def _looks_like_ndjson(body: str) -> bool:
    lines = [ln for ln in body.splitlines() if ln.strip()]
    if len(lines) < 2:
        return False
    try:
        json.loads(lines[0])
        json.loads(lines[1])
        return True
    except json.JSONDecodeError:
        return False


def fetch(url: str, max_chars: int) -> str:
    req = Request(url, headers={"User-Agent": "deepseek-exploration/fetch.py"})
    with urlopen(req, timeout=30) as resp:
        ctype = resp.headers.get("Content-Type", "").lower()
        raw = resp.read()
    body = raw.decode("utf-8", errors="replace")
    print(f"[fetch] {url}", file=sys.stderr)
    print(f"[fetch] content-type: {ctype or '(none)'}  bytes: {len(raw)}", file=sys.stderr)

    if "html" in ctype:
        parser = _TextExtractor()
        parser.feed(body)
        text = parser.text()
    elif "ndjson" in ctype or url.endswith(".ndjson") or _looks_like_ndjson(body):
        text = _render_ndjson(body)
    elif "json" in ctype:
        try:
            text = json.dumps(json.loads(body), indent=2)
        except json.JSONDecodeError:
            text = body
    else:
        text = body

    if len(text) > max_chars:
        print(f"[fetch] truncating {len(text)} -> {max_chars} chars", file=sys.stderr)
        text = text[:max_chars] + "\n\n[... truncated ...]"
    print(f"[fetch] emitting {len(text)} chars (~{len(text)//4} tokens)", file=sys.stderr)
    return text


def main():
    ap = argparse.ArgumentParser(description="Fetch a URL as clean text.")
    ap.add_argument("url")
    ap.add_argument("--max-chars", type=int, default=120_000,
                    help="cap output length (default 120000, ~30k tokens)")
    args = ap.parse_args()
    try:
        sys.stdout.write(fetch(args.url, args.max_chars))
    except Exception as e:  # noqa: BLE001 — surface any fetch error cleanly
        print(f"[fetch] error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
