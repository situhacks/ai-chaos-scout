"""Hacker News via the Algolia Search API — the most generous keyless source.

Endpoint: https://hn.algolia.com/api/v1/search_by_date?query={q}&tags=story
Budget:   ~10,000 req/hr per IP — no meaningful limit for our volume.

THIS IS WHERE LENS-FIRST SCOPING IS VISIBLE: queries come from
`knowledge/lens.md` query terms (config `tier2.hn_queries`, seeded by Stage 1).
Run one search per query term; normalize the JSON `hits` into Items
(url falls back to the HN item permalink when a story has no external url).
"""

from __future__ import annotations

import json
from urllib.parse import quote

from scout.http import get
from scout.models import Item
from scout.sources._util import excerpt, to_iso_utc
from scout.state import State

_HITS_PER_PAGE = 30


def _hit_to_item(hit: dict, query: str) -> Item | None:
    if not isinstance(hit, dict):
        return None
    object_id = hit.get("objectID")
    permalink = f"https://news.ycombinator.com/item?id={object_id}" if object_id else ""
    url = hit.get("url") or hit.get("story_url") or permalink
    if not url:
        return None
    title = hit.get("title") or hit.get("story_title") or url
    body = hit.get("story_text") or hit.get("comment_text") or ""
    meta = {
        "query": query,
        "points": hit.get("points"),
        "num_comments": hit.get("num_comments"),
        "author": hit.get("author", ""),
        "object_id": object_id,
        "hn_url": permalink,
    }
    return Item.create(
        source="hn",
        url=url,
        title=title,
        published_at=to_iso_utc(hit.get("created_at")),
        excerpt=excerpt(body),
        meta=meta,
    )


def _fetch_query(query: str, state: State, since_epoch: int | None = None) -> list[Item]:
    url = (
        "https://hn.algolia.com/api/v1/search_by_date"
        f"?query={quote(query)}&tags=story&hitsPerPage={_HITS_PER_PAGE}"
    )
    if since_epoch is not None:
        # Source-side recency window: only stories created after the cutoff.
        url += f"&numericFilters={quote(f'created_at_i>{int(since_epoch)}')}"
    resp = get(url, conditional_headers=state.get_conditional_headers(url))
    if resp.not_modified:
        return []
    if resp.error or resp.status != 200:
        return []
    state.update_etag(url, resp.etag, resp.last_modified)
    try:
        payload = json.loads(resp.body)
    except (json.JSONDecodeError, ValueError):
        return []
    hits = payload.get("hits") if isinstance(payload, dict) else None
    if not isinstance(hits, list):
        return []
    out: list[Item] = []
    for hit in hits:
        it = _hit_to_item(hit, query)
        if it is not None:
            out.append(it)
    return out


def fetch(queries: list[str], state: State, since_epoch: int | None = None) -> list[Item]:
    items: list[Item] = []
    for query in queries or []:
        if not query or not str(query).strip():
            continue
        try:
            items.extend(_fetch_query(str(query).strip(), state, since_epoch=since_epoch))
        except Exception:
            continue
    return items
