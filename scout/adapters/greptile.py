"""greptile.py — Tier-1 adapter scaffold for Greptile repo-understanding at scale.

    ┌─────────────────────────────────────────────────────────────────────┐
    │ UNTESTED SCAFFOLD. enabled: false. Never exercised in the core path. │
    └─────────────────────────────────────────────────────────────────────┘

Context: in the keyless v1, Stage-1 repo understanding is done by the IDE agent
reading the cloned repo directly (no Greptile). This scaffold is the "at scale"
replacement: Greptile indexes a repo and answers structured queries about it.
Requires a Greptile key AND a GitHub token; paid. Not a drop-in for the Item
pipeline — it feeds Stage 1 (the lens), not Stage 2 (the scout) — but it shares
the "configured-by-env, raises-when-absent" discipline.

Required env: GREPTILE_API_KEY, GITHUB_TOKEN
API shape:    POST https://api.greptile.com/v2/repositories (index)
              POST https://api.greptile.com/v2/query        (ask)

STATUS: SCAFFOLD — implement the shape (sub-agent C).
"""

from __future__ import annotations

from datetime import datetime

from scout.adapters.base import SourceAdapter
from scout.models import Item


class GreptileAdapter(SourceAdapter):
    key = "greptile"
    required_env = ["GREPTILE_API_KEY", "GITHUB_TOKEN"]
    UNTESTED = True

    def fetch(self, since: datetime | None = None) -> list[Item]:
        self.ensure_configured()
        # TODO(sub-agent C): index + query shape. Feeds Stage 1, not the Item stream.
        raise NotImplementedError("greptile is an untested Tier-1 scaffold")

    def summarize_repo(self, repo_url: str, question: str) -> str:
        """The real Stage-1 use: index `repo_url`, then ask `question`."""
        self.ensure_configured()
        raise NotImplementedError("greptile is an untested Tier-1 scaffold")
