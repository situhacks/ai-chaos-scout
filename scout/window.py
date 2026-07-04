"""Recency windowing — decide how far back a scout run looks.

First run (no prior `_run` marker in state) looks broadly (default 365 days) so
the very first report has a full year of context, biased toward recent items.
Every later run is tight (default 14 days) and, combined with the seen-cache in
`dedup.filter_unseen`, never re-surfaces findings from a previous scout.

The date window is a *secondary* guard: seen-state already prevents overlap; the
window keeps incremental runs scoped to fresh signal. Items whose `published_at`
cannot be parsed are kept (the source couldn't date them; seen-state still dedups
them across runs).

Config (config/sources.yaml, optional):

    research:
      first_run_lookback_days: 365
      future_run_days: 14
      focus_days: 7          # items newer than this are "recent" (for weighting)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

DEFAULT_FIRST_RUN_DAYS = 365
DEFAULT_FUTURE_RUN_DAYS = 14
DEFAULT_FOCUS_DAYS = 7

_ISO_FORMATS = (
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%d",
)


def parse_iso(value: str | None) -> datetime | None:
    """Parse an ISO-8601 timestamp into an aware UTC datetime, or None."""
    if not value or not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    for fmt in _ISO_FORMATS:
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def is_first_run(state) -> bool:
    """A run is the first if no prior run marker exists in last_run.json."""
    return not (getattr(state, "last_run", {}) or {}).get("_run")


def lookback_days(cfg: dict, state, override_days: int | None = None, force_first: bool = False) -> int:
    """Resolve how many days back this run should look."""
    if override_days is not None:
        return int(override_days)
    research = (cfg.get("research") or {}) if isinstance(cfg, dict) else {}
    if force_first or is_first_run(state):
        return int(research.get("first_run_lookback_days", DEFAULT_FIRST_RUN_DAYS))
    return int(research.get("future_run_days", DEFAULT_FUTURE_RUN_DAYS))


def focus_days(cfg: dict) -> int:
    research = (cfg.get("research") or {}) if isinstance(cfg, dict) else {}
    return int(research.get("focus_days", DEFAULT_FOCUS_DAYS))


def cutoff(days: int, now: datetime | None = None) -> datetime:
    now = now or datetime.now(timezone.utc)
    return now - timedelta(days=days)


def within_window(published_at: str | None, cutoff_dt: datetime) -> bool:
    """True if the item is new enough (or undated — kept, seen-state dedups it)."""
    dt = parse_iso(published_at)
    if dt is None:
        return True
    return dt >= cutoff_dt


def filter_recent(items: list, cutoff_dt: datetime) -> list:
    """Drop items older than the cutoff; keep undated ones."""
    return [it for it in items if within_window(getattr(it, "published_at", None), cutoff_dt)]
