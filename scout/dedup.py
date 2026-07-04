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

    # Pass 2: fuzzy title. O(n^2) worst case, but gated by two cheap upper bounds
    # (SequenceMatcher.real_quick_ratio / quick_ratio) and a length-block index so the
    # expensive .ratio() runs only for plausibly-similar pairs. On a few-thousand-item
    # run this is the difference between seconds and minutes.
    kept: list[Item] = []
    # kept titles bucketed by rounded length; a title of length L can only reach
    # ratio >= threshold against titles whose length is within a bounded window,
    # since ratio <= 2*min(la,lb)/(la+lb). Only scan buckets in that window.
    kept_by_len: dict[int, list[str]] = {}
    sm = SequenceMatcher(autojunk=False)
    for it in survivors:
        nt = _norm_title(it.title)
        if not nt:
            kept.append(it)
            continue
        la = len(nt)
        # ratio >= t  =>  min/max >= t/(2-t)  =>  candidate length within [la*r, la/r].
        r = title_threshold / (2.0 - title_threshold)
        lo, hi = int(la * r), int(la / r) + 1
        sm.set_seq2(nt)
        is_dupe = False
        for blen in range(lo, hi + 1):
            for prev in kept_by_len.get(blen, ()):
                sm.set_seq1(prev)
                if (
                    sm.real_quick_ratio() >= title_threshold
                    and sm.quick_ratio() >= title_threshold
                    and sm.ratio() >= title_threshold
                ):
                    is_dupe = True
                    break
            if is_dupe:
                break
        if not is_dupe:
            kept.append(it)
            kept_by_len.setdefault(la, []).append(nt)
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
