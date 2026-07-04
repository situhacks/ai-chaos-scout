"""Shared data contracts for AI Chaos Scout.

Stdlib-only. This module defines the normalized `Item` shape that every source
and every Tier-1 adapter MUST emit, plus the canonical-id helper used for
deduplication. Do not add third-party imports here.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Query params that carry no identity, only tracking. Stripped when canonicalizing.
_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "ref_src", "ref_url", "fbclid", "gclid", "mc_cid", "mc_eid",
    "source", "cmpid", "spm",
}


def canonicalize_url(url: str) -> str:
    """Return a stable, comparable form of a URL.

    Lowercases scheme/host, drops the fragment, strips known tracking params,
    sorts remaining params, and removes a trailing slash on the path. Two URLs
    that point at the same resource should canonicalize to the same string.
    """
    if not url:
        return ""
    parts = urlsplit(url.strip())
    scheme = (parts.scheme or "https").lower()
    netloc = parts.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = re.sub(r"/+$", "", parts.path) or "/"
    query_pairs = [
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=False)
        if k.lower() not in _TRACKING_PARAMS
    ]
    query = urlencode(sorted(query_pairs))
    return urlunsplit((scheme, netloc, path, query, ""))


def item_id(url: str) -> str:
    """SHA1 of the canonical URL — the stable id used across runs and in seen.json."""
    return hashlib.sha1(canonicalize_url(url).encode("utf-8")).hexdigest()


@dataclass
class Item:
    """One normalized signal from any source. Serializes as a single JSONL line.

    Contract (see kit/01-architecture.md):
        {"id", "source", "url", "title", "published_at", "excerpt", "meta"}

    - id:           sha1 of the canonical url (use `Item.create` / `item_id`)
    - source:       short source key, e.g. "hn", "openai_rss", "github", "ossinsight"
    - url:          the ORIGINAL clickable url (not canonicalized) — reports link here
    - title:        item title
    - published_at: ISO-8601 UTC string ("2026-07-01T09:00:00Z") or "" if unknown
    - excerpt:      first ~500 chars of body/summary, plain text
    - meta:         source-specific extras (author, points, stars, growth, tags...)
    """

    source: str
    url: str
    title: str
    published_at: str = ""
    excerpt: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    id: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = item_id(self.url)
        if self.excerpt and len(self.excerpt) > 500:
            self.excerpt = self.excerpt[:500].rstrip()

    @classmethod
    def create(cls, source: str, url: str, title: str, **kwargs: Any) -> Item:
        return cls(source=source, url=url, title=title, **kwargs)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # stable key order matching the documented contract
        return {
            "id": d["id"],
            "source": d["source"],
            "url": d["url"],
            "title": d["title"],
            "published_at": d["published_at"],
            "excerpt": d["excerpt"],
            "meta": d["meta"],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Item:
        return cls(
            source=d.get("source", ""),
            url=d.get("url", ""),
            title=d.get("title", ""),
            published_at=d.get("published_at", ""),
            excerpt=d.get("excerpt", ""),
            meta=d.get("meta", {}) or {},
            id=d.get("id", ""),
        )


def write_items_jsonl(path: str, items: list[Item]) -> None:
    """Write items to a JSONL file, one JSON object per line, UTF-8."""
    import os

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for it in items:
            fh.write(it.to_json() + "\n")


def read_items_jsonl(path: str) -> list[Item]:
    """Read items from a JSONL file. Missing file -> empty list."""
    import os

    if not os.path.exists(path):
        return []
    out: list[Item] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            out.append(Item.from_dict(json.loads(line)))
    return out
