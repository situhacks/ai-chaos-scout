#!/usr/bin/env python3
"""Create a Gmail draft through the Composio MCP (streamable HTTP, stdlib-only).

Usage:
    source ~/.composio_env
    python3 composio_draft.py --html reports/chaos-report-2026-07-04.html \
        --subject "..." --to someone@example.com [--list]

Draft-only: never sends. Reads COMPOSIO_MCP_URL / COMPOSIO_MCP_KEY from env.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

URL = os.environ["COMPOSIO_MCP_URL"]
KEY = os.environ["COMPOSIO_MCP_KEY"]
_SESSION = {"id": None}


def _post(payload: dict) -> dict | None:
    headers = {
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if _SESSION["id"]:
        headers["mcp-session-id"] = _SESSION["id"]
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        sid = resp.headers.get("mcp-session-id")
        if sid:
            _SESSION["id"] = sid
        body = resp.read().decode("utf-8", "replace")
    # Parse SSE: lines beginning with "data: "; return the last JSON payload.
    result = None
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            chunk = line[len("data:"):].strip()
            try:
                result = json.loads(chunk)
            except json.JSONDecodeError:
                continue
    if result is None and body.strip():
        try:
            result = json.loads(body)
        except json.JSONDecodeError:
            pass
    return result


def _notify(method: str) -> None:
    headers = {
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "mcp-session-id": _SESSION["id"] or "",
    }
    req = urllib.request.Request(
        URL, data=json.dumps({"jsonrpc": "2.0", "method": method}).encode(),
        headers=headers, method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=30).read()
    except Exception:
        pass


def handshake() -> None:
    _post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
           "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                      "clientInfo": {"name": "chaos-scout", "version": "1.0"}}})
    _notify("notifications/initialized")


def list_tools() -> list[str]:
    r = _post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    tools = (((r or {}).get("result") or {}).get("tools")) or []
    return [t.get("name", "") for t in tools]


def call(name: str, arguments: dict) -> dict | None:
    return _post({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                  "params": {"name": name, "arguments": arguments}})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--html")
    ap.add_argument("--subject")
    ap.add_argument("--to")
    ap.add_argument("--tool", default=None, help="Override tool name")
    ap.add_argument("--list", action="store_true", help="List available tools and exit")
    args = ap.parse_args()

    handshake()
    names = list_tools()
    if args.list:
        print("\n".join(names))
        return 0

    tool = args.tool or "GMAIL_CREATE_EMAIL_DRAFT"
    body = open(args.html, encoding="utf-8").read()
    # This MCP exposes Composio meta-tools; toolkit tools run via multi-execute.
    res = call("COMPOSIO_MULTI_EXECUTE_TOOL", {"tools": [{
        "tool_slug": tool,
        "arguments": {
            "recipient_email": args.to,
            "subject": args.subject,
            "body": body,
            "is_html": True,
        },
    }]})
    content = (((res or {}).get("result") or {}).get("content")) or []
    text = "\n".join(x.get("text", "") for x in content if x.get("type") == "text")
    print(text[:4000] if text else json.dumps(res, indent=2)[:4000])
    ok = '"successful":true' in text or '"successful": true' in text
    err = (res or {}).get("error") or (((res or {}).get("result") or {}).get("isError"))
    return 0 if (ok and not err) else 1


if __name__ == "__main__":
    sys.exit(main())
