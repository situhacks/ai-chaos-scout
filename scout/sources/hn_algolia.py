"""Hacker News via the Algolia Search API — the most generous keyless source.

Endpoint: https://hn.algolia.com/api/v1/search_by_date?query={q}&tags=story
Budget:   ~10,000 req/hr per IP — no meaningful limit for our volume.

THIS IS WHERE LENS-FIRST SCOPING IS VISIBLE: queries come from
`knowledge/lens.md` query terms (config `tier2.hn_queries`, seeded by Stage 1).
Run one search per query term; normalize the JSON `hits` into Items
(url falls back to the HN item permalink when a story has no external url).

STATUS: SCAFFOLD — implement me (sub-agent A).
"""

from __future__ import annotations

from scout.models import Item
from scout.state import State


def fetch(queries: list[str], state: State) -> list[Item]:
    # TODO(sub-agent A): one search_by_date call per query; dedup within run; map hits->Item.
    return []
