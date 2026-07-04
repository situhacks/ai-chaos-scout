"""GitHub releases/tags fetcher — unauthenticated, with strict ETag discipline.

Endpoint: https://api.github.com/repos/{owner}/{repo}/releases
Budget:   60 req/hr per IP, UNAUTHENTICATED, shared across a corporate NAT.
          A 304 (via ETag) does NOT count against the budget — always send
          conditional headers (see scout.state.get_conditional_headers).
          Cap at ~25 repos/run.

Watchlist comes from config `tier2.github_watchlist` (seeded by Stage 1 from the
lens tech watchlist), each entry "owner/repo".

Contract: return list[scout.models.Item] with meta including tag_name / published_at.
"""

from __future__ import annotations

import json

from scout.http import get
from scout.models import Item
from scout.sources._util import excerpt, to_iso_utc
from scout.state import State

MAX_REPOS_PER_RUN = 25

_GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def _release_to_item(rel: dict, repo: str) -> Item | None:
    if not isinstance(rel, dict):
        return None
    url = rel.get("html_url")
    if not url:
        return None
    tag = rel.get("tag_name") or ""
    name = rel.get("name") or tag or url
    meta = {
        "repo": repo,
        "tag_name": tag,
        "prerelease": bool(rel.get("prerelease")),
        "draft": bool(rel.get("draft")),
        "author": (rel.get("author") or {}).get("login", ""),
    }
    return Item.create(
        source=f"github_{repo}",
        url=url,
        title=name,
        published_at=to_iso_utc(rel.get("published_at") or rel.get("created_at")),
        excerpt=excerpt(rel.get("body")),
        meta=meta,
    )


def _fetch_repo(repo: str, state: State) -> list[Item]:
    url = f"https://api.github.com/repos/{repo}/releases"
    resp = get(
        url,
        conditional_headers=state.get_conditional_headers(url),
        extra_headers=_GITHUB_HEADERS,
    )
    if resp.not_modified:
        return []
    if resp.error or resp.status != 200:
        # 403/rate-limit or any other soft error -> skip this repo.
        return []
    state.update_etag(url, resp.etag, resp.last_modified)
    try:
        payload = json.loads(resp.body)
    except (json.JSONDecodeError, ValueError):
        return []
    if not isinstance(payload, list):
        return []
    out: list[Item] = []
    for rel in payload:
        it = _release_to_item(rel, repo)
        if it is not None:
            out.append(it)
    return out


def fetch(watchlist: list[str], state: State) -> list[Item]:
    items: list[Item] = []
    for repo in (watchlist or [])[:MAX_REPOS_PER_RUN]:
        if not repo or "/" not in str(repo):
            continue
        try:
            items.extend(_fetch_repo(str(repo).strip(), state))
        except Exception:
            continue
    return items
