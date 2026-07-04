"""OSSInsight trending-repos API — the grassroots "what's rising" signal.

Endpoint: https://api.ossinsight.io/v1/trends/repos/?period=past_week&language={lang}
Budget:   600 req/hr per IP, keyless. BETA API — endpoints may churn; on any
          non-200 or shape change, soft-fail (return []).
Signal:   stars + 28-day growth velocity; keep growth numbers in Item.meta.
"""

from __future__ import annotations

import json
from urllib.parse import quote

from scout.http import get
from scout.models import Item
from scout.sources._util import excerpt
from scout.state import State

# Fields (if present) worth carrying into meta as the growth/velocity signal.
_META_FIELDS = (
    "stars", "forks", "pushes", "pull_requests", "total_score",
    "contributor_logins", "collection_names", "language", "repo_id",
)


def _row_to_item(row: dict, language: str) -> Item | None:
    if not isinstance(row, dict):
        return None
    repo_name = row.get("repo_name") or row.get("full_name") or row.get("name")
    if not repo_name:
        return None
    meta: dict = {"language": language}
    for key in _META_FIELDS:
        if key in row and row[key] not in (None, ""):
            meta[key] = row[key]
    return Item.create(
        source="ossinsight",
        url=f"https://github.com/{repo_name}",
        title=repo_name,
        published_at="",
        excerpt=excerpt(row.get("description")),
        meta=meta,
    )


def _extract_rows(payload: object) -> list:
    """Tolerate a couple of documented/observed response shapes; else []."""
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, dict) and isinstance(data.get("rows"), list):
            return data["rows"]
        if isinstance(data, list):
            return data
        if isinstance(payload.get("rows"), list):
            return payload["rows"]
    return []


def _fetch_language(language: str, state: State) -> list[Item]:
    url = (
        "https://api.ossinsight.io/v1/trends/repos/"
        f"?period=past_week&language={quote(language)}"
    )
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
    out: list[Item] = []
    for row in _extract_rows(payload):
        it = _row_to_item(row, language)
        if it is not None:
            out.append(it)
    return out


def fetch(languages: list[str] | None, state: State) -> list[Item]:
    items: list[Item] = []
    for language in languages or []:
        if not language or not str(language).strip():
            continue
        try:
            items.extend(_fetch_language(str(language).strip(), state))
        except Exception:
            continue
    return items
