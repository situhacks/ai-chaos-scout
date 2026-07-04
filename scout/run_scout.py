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

from scout import dedup
from scout.config import load_sources
from scout.models import Item, write_items_jsonl
from scout.state import State, today

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _log(msg: str) -> None:
    print(f"[scout] {msg}", file=sys.stderr)


def run(date: str | None = None) -> dict:
    date = date or today()
    state = State()
    cfg = load_sources()
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
    _safe("hn", lambda: hn_algolia.fetch(hn_queries, state))
    _safe("ossinsight", lambda: ossinsight.fetch(tier2.get("ossinsight_languages"), state))

    # Dedup within-run, then drop already-seen items and mark the fresh ones.
    deduped = dedup.dedup(all_items)
    fresh = dedup.filter_unseen(deduped, state)

    out_dir = os.path.join(REPO_ROOT, "runs", date)
    out_path = os.path.join(out_dir, "items.jsonl")
    write_items_jsonl(out_path, fresh)
    state.save()

    summary = {
        "date": date,
        "scanned": len(all_items),
        "unique": len(deduped),
        "new": len(fresh),
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
    args = ap.parse_args()
    run(args.date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
