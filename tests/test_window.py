"""Tests for recency windowing (scout/window.py)."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from scout import window
from scout.models import Item


class _State:
    def __init__(self, last_run: dict | None = None):
        self.last_run = last_run or {}


class TestWindow(unittest.TestCase):
    def test_first_run_detection(self):
        self.assertTrue(window.is_first_run(_State()))
        self.assertFalse(window.is_first_run(_State({"_run": "2026-07-01T00:00:00Z"})))

    def test_lookback_days_first_vs_incremental(self):
        cfg = {"research": {"first_run_lookback_days": 365, "future_run_days": 14}}
        self.assertEqual(window.lookback_days(cfg, _State()), 365)
        self.assertEqual(window.lookback_days(cfg, _State({"_run": "x"})), 14)

    def test_lookback_days_override_and_force(self):
        cfg = {"research": {"first_run_lookback_days": 365, "future_run_days": 14}}
        self.assertEqual(window.lookback_days(cfg, _State({"_run": "x"}), override_days=30), 30)
        self.assertEqual(window.lookback_days(cfg, _State({"_run": "x"}), force_first=True), 365)

    def test_defaults_when_config_missing(self):
        self.assertEqual(window.lookback_days({}, _State()), window.DEFAULT_FIRST_RUN_DAYS)
        self.assertEqual(window.lookback_days({}, _State({"_run": "x"})), window.DEFAULT_FUTURE_RUN_DAYS)

    def test_within_window(self):
        cut = window.cutoff(14, now=datetime(2026, 7, 4, tzinfo=timezone.utc))
        self.assertTrue(window.within_window("2026-07-01T00:00:00Z", cut))
        self.assertFalse(window.within_window("2025-01-01T00:00:00Z", cut))
        self.assertTrue(window.within_window(None, cut))  # undated kept
        self.assertTrue(window.within_window("garbage", cut))  # unparseable kept

    def test_filter_recent_drops_old_keeps_undated(self):
        cut = window.cutoff(14, now=datetime(2026, 7, 4, tzinfo=timezone.utc))
        items = [
            Item.create(source="hn", url="https://a.test/1", title="recent",
                        published_at="2026-07-02T00:00:00Z"),
            Item.create(source="hn", url="https://a.test/2", title="old",
                        published_at="2020-01-01T00:00:00Z"),
            Item.create(source="hn", url="https://a.test/3", title="undated",
                        published_at=""),
        ]
        kept = window.filter_recent(items, cut)
        titles = {it.title for it in kept}
        self.assertEqual(titles, {"recent", "undated"})


if __name__ == "__main__":
    unittest.main()
