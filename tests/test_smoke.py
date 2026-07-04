"""Smoke tests for the shared contracts. Stdlib unittest — no pytest required to run:

    python -m unittest discover -s tests

These lock the interfaces the parallel workstreams build against: Item shape,
canonical-url dedup id, the stdlib YAML reader on the real config files, and dedup.
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scout.config import load_sources, load_subject, parse_yaml  # noqa: E402
from scout.dedup import dedup  # noqa: E402
from scout.models import Item, canonicalize_url, item_id  # noqa: E402


class TestModels(unittest.TestCase):
    def test_item_id_is_stable_and_canonical(self):
        a = "https://Example.com/Post/?utm_source=x&b=2&a=1#frag"
        b = "https://www.example.com/Post?a=1&b=2"
        self.assertEqual(canonicalize_url(a), canonicalize_url(b))
        self.assertEqual(item_id(a), item_id(b))

    def test_item_autoderives_id_and_trims_excerpt(self):
        it = Item.create("hn", "https://example.com/x", "T", excerpt="y" * 900)
        self.assertTrue(it.id)
        self.assertEqual(len(it.excerpt), 500)

    def test_item_roundtrips_json(self):
        it = Item.create("hn", "https://example.com/x", "Title", published_at="2026-07-04T00:00:00Z")
        again = Item.from_dict(__import__("json").loads(it.to_json()))
        self.assertEqual(again.id, it.id)
        self.assertEqual(again.source, "hn")


class TestConfigYaml(unittest.TestCase):
    def test_sources_yaml_parses(self):
        s = load_sources()
        self.assertIn("tier2", s)
        rss = s["tier2"]["rss"]
        self.assertTrue(any(f["id"] == "openai" for f in rss))
        # Tier-1 adapters must be disabled by default (hard constraint).
        for name, cfg in s["tier1"].items():
            self.assertFalse(cfg["enabled"], f"{name} must be enabled: false")

    def test_subject_yaml_parses(self):
        self.assertIn("subject", load_subject())

    def test_inline_flow_and_nesting(self):
        parsed = parse_yaml("a:\n  - {id: x, url: y}\n  - z\nb: [1, 2, 3]\nc: true\n")
        self.assertEqual(parsed["a"][0], {"id": "x", "url": "y"})
        self.assertEqual(parsed["a"][1], "z")
        self.assertEqual(parsed["b"], [1, 2, 3])
        self.assertIs(parsed["c"], True)


class TestDedup(unittest.TestCase):
    def test_exact_url_dedup(self):
        items = [
            Item.create("hn", "https://a.com/x?utm_source=1", "One"),
            Item.create("rss", "https://a.com/x", "One (dupe)"),
            Item.create("hn", "https://b.com/y", "Two"),
        ]
        out = dedup(items)
        self.assertEqual(len(out), 2)

    def test_fuzzy_title_dedup(self):
        items = [
            Item.create("hn", "https://a.com/1", "OpenAI ships a new model today"),
            Item.create("rss", "https://b.com/2", "OpenAI ships a new model  today"),
        ]
        self.assertEqual(len(dedup(items)), 1)


if __name__ == "__main__":
    unittest.main()
