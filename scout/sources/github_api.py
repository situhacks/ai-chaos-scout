"""GitHub releases/tags fetcher — unauthenticated, with strict ETag discipline.

Endpoint: https://api.github.com/repos/{owner}/{repo}/releases
Budget:   60 req/hr per IP, UNAUTHENTICATED, shared across a corporate NAT.
          A 304 (via ETag) does NOT count against the budget — always send
          conditional headers (see scout.state.get_conditional_headers).
          Cap at ~25 repos/run.

Watchlist comes from config `tier2.github_watchlist` (seeded by Stage 1 from the
lens tech watchlist), each entry "owner/repo".

Contract: return list[scout.models.Item] with meta including tag_name / published_at.

STATUS: SCAFFOLD — implement me (sub-agent A).
"""

from __future__ import annotations

from scout.models import Item
from scout.state import State

MAX_REPOS_PER_RUN = 25


def fetch(watchlist: list[str], state: State) -> list[Item]:
    # TODO(sub-agent A): GET releases per repo with If-None-Match; persist ETag;
    # soft-fail on 403/rate-limit; cap at MAX_REPOS_PER_RUN.
    return []
