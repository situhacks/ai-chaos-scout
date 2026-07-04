"""Stage-2 orchestrator: read config + lens, fetch all enabled Tier-2 sources,
dedup against state, write runs/{date}/items.jsonl.

Deterministic mechanics only — NO judgment here (that's the agent's job in the
slash command). Soft-fail per source: log to stderr and continue; never hard-fail
the run just because one source is blocked.

Run:  python scout/run_scout.py            # today's run
      python scout/run_scout.py --date 2026-07-04

STATUS: PARTIALLY SCAFFOLDED. The wiring/soft-fail/state/output is here; the
per-source fetchers it calls are in scout/sources/* (sub-agent A implements those).
"""

from __future__ import annotations

import argparse
import os
import sys

# Allow `python scout/run_scout.py` (script mode) as well as `python -m scout.run_scout`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# In script mode Python also puts this file's dir (scout/) on sys.path, where
# scout/http.py would shadow the stdlib `http` package and break `import http.client`
# (used by urllib.request inside the sources). Drop it so the stdlib wins.
try:
    sys.path.remove(os.path.dirname(os.path.abspath(__file__)))
except ValueError:
    pass

from datetime import datetime, timezone

from scout import dedup, window
from scout.config import load_sources
from scout.models import Item, write_items_jsonl
from scout.state import State, today

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _log(msg: str) -> None:
    print(f"[scout] {msg}", file=sys.stderr)


def run(
    date: str | None = None,
    window_days: int | None = None,
    first_run: bool = False,
) -> dict:
    date = date or today()
    state = State()
    cfg = load_sources()
    # Recency window: first run looks back ~1yr, later runs a tight 14d chunk.
    days = window.lookback_days(cfg, state, override_days=window_days, force_first=first_run)
    now = datetime.now(timezone.utc)
    cutoff_dt = window.cutoff(days, now=now)
    cutoff_epoch = int(cutoff_dt.timestamp())
    is_first = first_run or window.is_first_run(state)
    _log(f"window: {'first-run' if is_first else 'incremental'}, looking back {days}d (since {cutoff_dt.date()})")
    # Stage 1 pushes lens-derived query terms / watchlist into config/sources.yaml,
    # so the scout just reads them here (source of truth = sources.yaml).
    tier2 = cfg.get("tier2", {}) or {}
    all_items: list[Item] = []
    soft_failed: list[str] = []

    # Each source is wrapped so one failure never sinks the run.
    def _safe(source_key: str, fn) -> None:
        try:
            got = fn() or []
            _log(f"{source_key}: {len(got)} items")
            all_items.extend(got)
            state.mark_source_success(source_key)
        except Exception as e:  # noqa: BLE001 - deliberate: soft-fail any source
            _log(f"{source_key}: SOFT-FAIL {e}")
            soft_failed.append(source_key)

    # Import lazily so a broken/unimplemented source can't stop the others at import time.
    from scout.sources import github_api, github_trending, hn_algolia, ossinsight, rss

    hn_queries = tier2.get("hn_queries") or []
    watchlist = tier2.get("github_watchlist") or []

    _safe("rss", lambda: rss.fetch(
        tier2.get("rss", []), state,
        reddit_subs=tier2.get("reddit_rss", []),
        youtube_channels=tier2.get("youtube_channels", []),
    ))
    _safe("github", lambda: github_api.fetch(watchlist, state))
    _safe("github_trending", lambda: github_trending.fetch(tier2.get("trending_languages"), state))
    _safe("hn", lambda: hn_algolia.fetch(hn_queries, state, since_epoch=cutoff_epoch))
    _safe("ossinsight", lambda: ossinsight.fetch(tier2.get("ossinsight_languages"), state))

    # Recency filter: drop items older than the window (undated items kept;
    # seen-state still dedups them across runs).
    scanned_total = len(all_items)
    windowed = window.filter_recent(all_items, cutoff_dt)
    # Dedup within-run, then drop already-seen items and mark the fresh ones.
    deduped = dedup.dedup(windowed)
    fresh = dedup.filter_unseen(deduped, state)

    out_dir = os.path.join(REPO_ROOT, "runs", date)
    out_path = os.path.join(out_dir, "items.jsonl")
    write_items_jsonl(out_path, fresh)
    state.save()

    summary = {
        "date": date,
        "scanned": scanned_total,
        "in_window": len(windowed),
        "unique": len(deduped),
        "new": len(fresh),
        "first_run": is_first,
        "lookback_days": days,
        "cutoff": cutoff_dt.strftime("%Y-%m-%d"),
        "soft_failed": soft_failed,
        "items_path": os.path.relpath(out_path, REPO_ROOT),
    }
    _log(
        f"done: scanned {summary['scanned']} -> {summary['unique']} unique -> "
        f"{summary['new']} new. soft-failed: {soft_failed or 'none'}"
    )
    print(
        f"scanned {summary['scanned']} items, {summary['new']} new "
        f"({summary['unique']} unique this run) -> {summary['items_path']}"
    )
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description="AI Chaos Scout — Stage 2 fetch")
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: today, UTC)")
    ap.add_argument("--window-days", type=int, default=None,
                    help="Override lookback window in days (default: config-driven)")
    ap.add_argument("--first-run", action="store_true",
                    help="Force first-run broad lookback even if prior state exists")
    args = ap.parse_args()
    run(args.date, window_days=args.window_days, first_run=args.first_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
