"""reddit_oauth.py — Tier-1 adapter scaffold for the official Reddit OAuth API.

    ┌─────────────────────────────────────────────────────────────────────┐
    │ UNTESTED SCAFFOLD. enabled: false. Never exercised in the core path. │
    │ Request-construction is unit-tested OFFLINE only — ZERO live calls.  │
    └─────────────────────────────────────────────────────────────────────┘

Context: the Tier-2 path uses Reddit RSS (keyless, flaky, rate-limited). This is
the reliable upgrade path once an app registration is approved: client-credentials
OAuth, 100 QPM, stable — it replaces the flaky RSS source WITHOUT changing the
`Item` shape (swap is config, not a rewrite). Built to the documented shape but
NEVER run against live Reddit.

Required env: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET
API shape:    POST https://www.reddit.com/api/v1/access_token
                   (HTTP Basic auth, grant_type=client_credentials)
              GET  https://oauth.reddit.com/r/{sub}/new
                   (Authorization: bearer {token}, custom User-Agent)

STATUS: SCAFFOLD — token + listing shapes implemented and unit-tested offline.
"""

from __future__ import annotations

import base64
import json
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

from scout.adapters.base import SourceAdapter
from scout.models import Item

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
API_BASE = "https://oauth.reddit.com"
#: Reddit REQUIRES a unique, descriptive User-Agent or it 429s/blocks aggressively.
USER_AGENT = "ai-chaos-scout/0.1 (by /u/ai-chaos-scout; +https://github.com/situhacks/ai-chaos-scout)"
#: Reddit listing page size cap.
DEFAULT_LIMIT = 25


@dataclass
class PreparedRequest:
    """A fully-described HTTP request, built WITHOUT performing any I/O."""

    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes | None = None


def build_token_request(client_id: str, client_secret: str) -> PreparedRequest:
    """Build the client-credentials token exchange. Pure — no network."""
    raw = f"{client_id}:{client_secret}".encode()
    basic = base64.b64encode(raw).decode("ascii")
    body = urlencode({"grant_type": "client_credentials"}).encode("utf-8")
    headers = {
        "Authorization": f"Basic {basic}",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    return PreparedRequest("POST", TOKEN_URL, headers, body)


def build_listing_request(subreddit: str, token: str,
                          limit: int = DEFAULT_LIMIT) -> PreparedRequest:
    """Build a GET /r/{sub}/new request with the bearer token. Pure — no network."""
    url = f"{API_BASE}/r/{subreddit}/new?{urlencode({'limit': limit})}"
    headers = {
        "Authorization": f"bearer {token}",
        "User-Agent": USER_AGENT,
    }
    return PreparedRequest("GET", url, headers)


def post_to_item(post: dict[str, Any]) -> Item:
    """Map one Reddit `t3` post's `data` object -> the shared `Item` shape. Pure."""
    permalink = post.get("permalink", "")
    url = f"https://www.reddit.com{permalink}" if permalink else post.get("url", "")
    created = post.get("created_utc")
    published_at = ""
    if isinstance(created, (int, float)):
        published_at = datetime.fromtimestamp(created, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    return Item.create(
        source="reddit_oauth",
        url=url,
        title=post.get("title", "") or "",
        published_at=published_at,
        excerpt=post.get("selftext", "") or "",
        meta={
            "subreddit": post.get("subreddit", ""),
            "author": post.get("author", ""),
            "ups": post.get("ups"),
            "num_comments": post.get("num_comments"),
            "reddit_id": post.get("id", ""),
        },
    )


def parse_listing_response(body: str) -> list[Item]:
    """Map a Reddit listing JSON body -> list[Item]. Pure (no network)."""
    payload = json.loads(body) if body else {}
    children = payload.get("data", {}).get("children", [])
    return [post_to_item(c.get("data", {})) for c in children]


def parse_token_response(body: str) -> str:
    """Extract the bearer token from the token-endpoint JSON body. Pure."""
    return json.loads(body).get("access_token", "")


class RedditOAuthAdapter(SourceAdapter):
    key = "reddit_oauth"
    required_env = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"]
    UNTESTED = True

    def __init__(self, subreddits: list[str] | None = None,
                 limit: int = DEFAULT_LIMIT) -> None:
        self.subreddits = subreddits or []
        self.limit = limit

    def build_token_request(self) -> PreparedRequest:
        """Build the token request from env creds. Requires configuration."""
        self.ensure_configured()
        import os

        return build_token_request(
            os.environ["REDDIT_CLIENT_ID"], os.environ["REDDIT_CLIENT_SECRET"]
        )

    def _get_token(self) -> str:
        status, body = _perform(self.build_token_request())
        return parse_token_response(body) if status == 200 else ""

    def fetch(self, since: datetime | None = None) -> list[Item]:
        self.ensure_configured()  # raises AdapterNotConfigured when unset
        token = self._get_token()
        items: list[Item] = []
        for sub in self.subreddits:
            status, body = _perform(build_listing_request(sub, token, self.limit))
            if status == 200:
                items.extend(parse_listing_response(body))
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
