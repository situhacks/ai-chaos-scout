"""x_api.py — Tier-1 adapter scaffold for the X (Twitter) API v2.

    ┌─────────────────────────────────────────────────────────────────────┐
    │ UNTESTED SCAFFOLD. enabled: false. Never exercised in the core path. │
    └─────────────────────────────────────────────────────────────────────┘

Context: X killed its free read tier in Feb 2026. Reads are now pay-per-use
(~$0.005/read; a 50-account whitelist at realistic volume ≈ $1,500/mo). This is
exactly why X is NOT a Tier-2 source. This scaffold proves the architecture
extends to a keyed X feed with config only — it is not run.

Required env: X_BEARER_TOKEN
API shape:    GET https://api.twitter.com/2/tweets/search/recent?query=...
              Authorization: Bearer {token}

STATUS: SCAFFOLD — implement the shape (sub-agent C). Do NOT test against live X.
"""

from __future__ import annotations

from datetime import datetime

from scout.adapters.base import SourceAdapter
from scout.models import Item


class XApiAdapter(SourceAdapter):
    key = "x"
    required_env = ["X_BEARER_TOKEN"]
    UNTESTED = True

    def fetch(self, since: datetime | None = None) -> list[Item]:
        self.ensure_configured()  # raises AdapterNotConfigured when unset
        # TODO(sub-agent C): build the v2 recent-search request shape; map -> Item.
        raise NotImplementedError("x_api is an untested Tier-1 scaffold")
