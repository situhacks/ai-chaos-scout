"""reddit_oauth.py — Tier-1 adapter scaffold for the official Reddit OAuth API.

    ┌─────────────────────────────────────────────────────────────────────┐
    │ UNTESTED SCAFFOLD. enabled: false. Never exercised in the core path. │
    └─────────────────────────────────────────────────────────────────────┘

Context: the Tier-2 path uses Reddit RSS (keyless, rate-limited). This is the
upgrade path once an app registration is approved: client-credentials OAuth,
100 QPM, reliable — replaces the flaky RSS source without changing Item shape.

Required env: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET
API shape:    POST https://www.reddit.com/api/v1/access_token (client_credentials)
              GET  https://oauth.reddit.com/r/{sub}/new

STATUS: SCAFFOLD — implement the shape (sub-agent C).
"""

from __future__ import annotations

from datetime import datetime

from scout.adapters.base import SourceAdapter
from scout.models import Item


class RedditOAuthAdapter(SourceAdapter):
    key = "reddit_oauth"
    required_env = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"]
    UNTESTED = True

    def fetch(self, since: datetime | None = None) -> list[Item]:
        self.ensure_configured()
        # TODO(sub-agent C): token exchange + per-sub listing fetch; map -> Item.
        raise NotImplementedError("reddit_oauth is an untested Tier-1 scaffold")
