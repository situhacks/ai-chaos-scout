"""Deduplication: URL-canonical (exact) + title-similarity (fuzzy).

Stdlib-only (uses difflib). Two-pass:
  1. collapse items whose canonical URL id matches (exact dupes across sources);
  2. within the survivors, drop near-identical titles (same story, different outlet).
"""

from __future__ import annotations

from difflib import SequenceMatcher

from scout.models import Item

_TITLE_SIMILARITY_THRESHOLD = 0.90


def _norm_title(t: str) -> str:
    return " ".join(t.lower().split())


def dedup(items: list[Item], title_threshold: float = _TITLE_SIMILARITY_THRESHOLD) -> list[Item]:
    """Return items with exact-URL and near-duplicate-title collisions removed.

    Order is preserved; the first occurrence of each cluster wins.
    """
    # Pass 1: exact canonical-url id.
    by_id: dict[str, Item] = {}
    for it in items:
        by_id.setdefault(it.id, it)
    survivors = list(by_id.values())

    # Pass 2: fuzzy title.
    kept: list[Item] = []
    kept_titles: list[str] = []
    for it in survivors:
        nt = _norm_title(it.title)
        if not nt:
            kept.append(it)
            continue
        is_dupe = any(
            SequenceMatcher(None, nt, prev).ratio() >= title_threshold
            for prev in kept_titles
        )
        if not is_dupe:
            kept.append(it)
            kept_titles.append(nt)
    return kept


def filter_unseen(items: list[Item], state) -> list[Item]:
    """Drop items already in the seen-cache; mark the rest as seen. Returns new items."""
    fresh: list[Item] = []
    for it in items:
        if state.is_seen(it.id):
            continue
        state.mark_seen(it.id)
        fresh.append(it)
    return fresh
