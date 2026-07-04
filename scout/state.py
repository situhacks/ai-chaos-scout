"""Repo-local state: seen-item cache, ETags, and per-source last-run timestamps.

Stdlib-only. All state lives in `state/*.json` so runs are idempotent and
inspectable/versionable. No external storage (hard constraint).

Files owned here:
    state/seen.json      -> {item_id: first_seen_iso}
    state/etags.json     -> {endpoint_url: {"etag": str, "last_modified": str}}
    state/last_run.json  -> {source_key: last_success_iso, "_run": last_run_iso}
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

_STATE_DIR_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "state"
)


def now_iso() -> str:
    """Current UTC time as ISO-8601 with a trailing Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today() -> str:
    """UTC date as YYYY-MM-DD — the runs/{date} folder key."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _load(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh) or {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)


class State:
    """Read/write wrapper over the three state files. Load once, mutate, `save()`."""

    def __init__(self, state_dir: str | None = None) -> None:
        self.dir = state_dir or _STATE_DIR_DEFAULT
        self.seen: dict[str, str] = _load(os.path.join(self.dir, "seen.json"))
        self.etags: dict[str, dict] = _load(os.path.join(self.dir, "etags.json"))
        self.last_run: dict[str, str] = _load(os.path.join(self.dir, "last_run.json"))

    # --- seen cache ---------------------------------------------------------
    def is_seen(self, item_id: str) -> bool:
        return item_id in self.seen

    def mark_seen(self, item_id: str) -> None:
        self.seen.setdefault(item_id, now_iso())

    # --- etags --------------------------------------------------------------
    def get_conditional_headers(self, url: str) -> dict[str, str]:
        """Headers to send for a conditional GET (If-None-Match / If-Modified-Since)."""
        rec = self.etags.get(url) or {}
        headers: dict[str, str] = {}
        if rec.get("etag"):
            headers["If-None-Match"] = rec["etag"]
        if rec.get("last_modified"):
            headers["If-Modified-Since"] = rec["last_modified"]
        return headers

    def update_etag(self, url: str, etag: str | None, last_modified: str | None) -> None:
        if not etag and not last_modified:
            return
        rec = self.etags.setdefault(url, {})
        if etag:
            rec["etag"] = etag
        if last_modified:
            rec["last_modified"] = last_modified

    # --- last run -----------------------------------------------------------
    def mark_source_success(self, source_key: str) -> None:
        self.last_run[source_key] = now_iso()

    def last_success(self, source_key: str) -> str | None:
        return self.last_run.get(source_key)

    def save(self) -> None:
        self.last_run["_run"] = now_iso()
        _save(os.path.join(self.dir, "seen.json"), self.seen)
        _save(os.path.join(self.dir, "etags.json"), self.etags)
        _save(os.path.join(self.dir, "last_run.json"), self.last_run)
