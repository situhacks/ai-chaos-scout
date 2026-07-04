"""x_api.py — Tier-1 adapter scaffold for the X (Twitter) API v2.

    ┌─────────────────────────────────────────────────────────────────────┐
    │ UNTESTED SCAFFOLD. enabled: false. Never exercised in the core path. │
    │ Request-construction is unit-tested OFFLINE only — ZERO live calls.  │
    └─────────────────────────────────────────────────────────────────────┘

Context: X killed its free read tier in Feb 2026. Reads are now pay-per-use
(~$0.005/read; a 50-account whitelist at realistic volume ≈ $1,500/mo). This is
exactly why X is NOT a Tier-2 source. This scaffold proves the architecture
extends to a keyed X feed with config only — it is built to the documented v2
recent-search shape but has NEVER been run against the live API.

Required env: X_BEARER_TOKEN
API shape:    GET https://api.twitter.com/2/tweets/search/recent
                  ?query=...&tweet.fields=created_at,public_metrics
              Authorization: Bearer {token}
Item mapping: url = https://twitter.com/i/web/status/{id}

STATUS: SCAFFOLD — the request/response shape is implemented and unit-tested
offline; do NOT test against live X (every read is billed).
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

from scout.adapters.base import SourceAdapter
from scout.models import Item

#: X v2 recent-search endpoint (last ~7 days of public tweets).
SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"
#: Fields we ask for on every tweet so the mapping below is populated.
DEFAULT_TWEET_FIELDS = "created_at,public_metrics"
#: v2 recent-search allows 10..100 results per page.
DEFAULT_MAX_RESULTS = 25
USER_AGENT = "ai-chaos-scout/0.1 (+https://github.com/situhacks/ai-chaos-scout)"


@dataclass
class PreparedRequest:
    """A fully-described HTTP request, built WITHOUT performing any I/O.

    Extracting construction into this pure value is what makes the adapter
    testable offline: tests assert on `url`/`headers`/`body` without a network.
    """

    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes | None = None


def build_search_request(
    query: str,
    token: str,
    since: datetime | None = None,
    max_results: int = DEFAULT_MAX_RESULTS,
    tweet_fields: str = DEFAULT_TWEET_FIELDS,
) -> PreparedRequest:
    """Build the v2 recent-search request. Pure — no network, no env reads."""
    params: dict[str, str] = {
        "query": query,
        "tweet.fields": tweet_fields,
        "max_results": str(max_results),
    }
    if since is not None:
        start = since.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        params["start_time"] = start
    url = f"{SEARCH_URL}?{urlencode(params)}"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    return PreparedRequest("GET", url, headers)


def tweet_to_item(tweet: dict[str, Any]) -> Item:
    """Map one v2 tweet object -> the shared `Item` shape. Pure."""
    tweet_id = str(tweet.get("id", ""))
    text = (tweet.get("text") or "").strip()
    url = f"https://twitter.com/i/web/status/{tweet_id}"
    meta: dict[str, Any] = {"tweet_id": tweet_id}
    if "public_metrics" in tweet:
        meta["public_metrics"] = tweet["public_metrics"]
    if "author_id" in tweet:
        meta["author_id"] = tweet["author_id"]
    return Item.create(
        source="x",
        url=url,
        title=text or f"tweet {tweet_id}",
        published_at=tweet.get("created_at", "") or "",
        excerpt=text,
        meta=meta,
    )


def parse_search_response(body: str) -> list[Item]:
    """Map a v2 recent-search JSON body -> list[Item]. Pure (no network)."""
    payload = json.loads(body) if body else {}
    return [tweet_to_item(t) for t in payload.get("data", [])]


class XApiAdapter(SourceAdapter):
    key = "x"
    required_env = ["X_BEARER_TOKEN"]
    UNTESTED = True

    def __init__(self, queries: list[str] | None = None,
                 max_results: int = DEFAULT_MAX_RESULTS) -> None:
        self.queries = queries or []
        self.max_results = max_results

    def _token(self) -> str:
        import os

        return os.environ["X_BEARER_TOKEN"]

    def build_requests(self, since: datetime | None = None) -> list[PreparedRequest]:
        """Build one recent-search request per configured query. Requires creds."""
        self.ensure_configured()
        token = self._token()
        return [
            build_search_request(q, token, since=since, max_results=self.max_results)
            for q in self.queries
        ]

    def fetch(self, since: datetime | None = None) -> list[Item]:
        self.ensure_configured()  # raises AdapterNotConfigured when unset
        items: list[Item] = []
        for req in self.build_requests(since=since):
            status, body = _perform(req)
            if status == 200:
                items.extend(parse_search_response(body))
        return items


def _perform(prepared: PreparedRequest) -> tuple[int, str]:
    """Execute a PreparedRequest. Only reached with real creds — never in tests."""
    req = urllib.request.Request(
        prepared.url, data=prepared.body, headers=prepared.headers,
        method=prepared.method,
    )
    with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310 (https only)
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.status, resp.read().decode(charset, errors="replace")
