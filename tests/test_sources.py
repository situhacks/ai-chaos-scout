"""Offline unit tests for the Tier-2 source fetchers.

Stdlib `unittest` only. All parsing is tested against small embedded
RSS/Atom/JSON/HTML strings — no network. Network-facing `fetch()` wrappers are
exercised with a patched `scout.http.get` to prove soft-fail discipline.

    python -m unittest discover -s tests
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scout.http import Response  # noqa: E402
from scout.sources import (  # noqa: E402
    github_api,
    github_trending,
    hn_algolia,
    ossinsight,
    rss,
)
from scout.sources._util import excerpt, strip_html, to_iso_utc  # noqa: E402
from scout.state import State  # noqa: E402


def _state() -> State:
    # A State pointed at a throwaway dir so tests never touch real state files.
    return State(state_dir=os.path.join(os.path.dirname(__file__), "_tmp_state"))


RSS_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>Example Blog</title>
    <item>
      <title>First Post</title>
      <link>https://example.com/first</link>
      <description>&lt;p&gt;Hello &lt;b&gt;world&lt;/b&gt;&lt;/p&gt;</description>
      <pubDate>Wed, 02 Oct 2002 13:00:00 GMT</pubDate>
      <dc:creator>Ada</dc:creator>
    </item>
    <item>
      <title>Second Post</title>
      <link>https://example.com/second</link>
      <content:encoded>Body text here</content:encoded>
      <dc:date>2026-07-01T09:30:00Z</dc:date>
    </item>
  </channel>
</rss>"""

ATOM_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Chan</title>
  <entry>
    <title>Video Title</title>
    <link rel="alternate" href="https://youtube.com/watch?v=abc"/>
    <published>2026-07-02T12:00:00+00:00</published>
    <summary>A summary of the video</summary>
    <author><name>Creator</name></author>
  </entry>
</feed>"""


class TestUtil(unittest.TestCase):
    def test_strip_html(self):
        self.assertEqual(strip_html("<p>Hi <b>there</b></p>"), "Hi there")
        self.assertEqual(strip_html(None), "")

    def test_excerpt_clips(self):
        self.assertEqual(len(excerpt("x" * 900)), 500)

    def test_to_iso_utc_rfc822(self):
        self.assertEqual(to_iso_utc("Wed, 02 Oct 2002 13:00:00 GMT"), "2002-10-02T13:00:00Z")

    def test_to_iso_utc_iso_and_offset(self):
        self.assertEqual(to_iso_utc("2026-07-02T12:00:00+00:00"), "2026-07-02T12:00:00Z")
        self.assertEqual(to_iso_utc("2026-07-01T09:30:00.500Z"), "2026-07-01T09:30:00Z")

    def test_to_iso_utc_garbage(self):
        self.assertEqual(to_iso_utc("not a date"), "")
        self.assertEqual(to_iso_utc(""), "")


class TestRss(unittest.TestCase):
    def test_parse_rss(self):
        items = rss.parse_feed(RSS_SAMPLE, "openai")
        self.assertEqual(len(items), 2)
        first = items[0]
        self.assertEqual(first.source, "openai")
        self.assertEqual(first.url, "https://example.com/first")
        self.assertEqual(first.title, "First Post")
        self.assertEqual(first.published_at, "2002-10-02T13:00:00Z")
        self.assertEqual(first.excerpt, "Hello world")
        self.assertEqual(first.meta.get("author"), "Ada")
        self.assertEqual(items[1].published_at, "2026-07-01T09:30:00Z")

    def test_parse_atom(self):
        items = rss.parse_feed(ATOM_SAMPLE, "youtube_abc")
        self.assertEqual(len(items), 1)
        it = items[0]
        self.assertEqual(it.url, "https://youtube.com/watch?v=abc")
        self.assertEqual(it.published_at, "2026-07-02T12:00:00Z")
        self.assertEqual(it.excerpt, "A summary of the video")
        self.assertEqual(it.meta.get("author"), "Creator")

    def test_empty_feed_is_normal(self):
        empty = '<?xml version="1.0"?><rss><channel><title>x</title></channel></rss>'
        self.assertEqual(rss.parse_feed(empty, "arxiv_csai"), [])
        self.assertEqual(rss.parse_feed("", "arxiv_csai"), [])

    def test_malformed_softfails(self):
        self.assertEqual(rss.parse_feed("<rss><broken", "x"), [])

    def test_fetch_softfails_on_http_error(self):
        with mock.patch.object(rss, "get", return_value=Response(status=503, error="boom")):
            out = rss.fetch([{"id": "openai", "url": "https://x/y"}], _state())
        self.assertEqual(out, [])

    def test_fetch_parses_and_persists_etag(self):
        resp = Response(status=200, body=RSS_SAMPLE, etag='"abc"')
        st = _state()
        with mock.patch.object(rss, "get", return_value=resp):
            out = rss.fetch([{"id": "openai", "url": "https://x/y"}], st)
        self.assertEqual(len(out), 2)
        self.assertEqual(st.etags["https://x/y"]["etag"], '"abc"')


class TestGithubApi(unittest.TestCase):
    RELEASES = json.dumps([
        {
            "html_url": "https://github.com/openai/openai-python/releases/tag/v1.2.3",
            "name": "v1.2.3", "tag_name": "v1.2.3",
            "published_at": "2026-07-01T10:00:00Z",
            "body": "Bug fixes", "prerelease": False,
            "author": {"login": "octocat"},
        }
    ])

    def test_map_release(self):
        it = github_api._release_to_item(json.loads(self.RELEASES)[0], "openai/openai-python")
        self.assertEqual(it.title, "v1.2.3")
        self.assertEqual(it.meta["tag_name"], "v1.2.3")
        self.assertEqual(it.meta["repo"], "openai/openai-python")
        self.assertEqual(it.source, "github_openai/openai-python")
        self.assertEqual(it.published_at, "2026-07-01T10:00:00Z")

    def test_fetch_ok(self):
        resp = Response(status=200, body=self.RELEASES, etag='"e"')
        with mock.patch.object(github_api, "get", return_value=resp):
            out = github_api.fetch(["openai/openai-python"], _state())
        self.assertEqual(len(out), 1)

    def test_fetch_ratelimit_softfails(self):
        with mock.patch.object(github_api, "get", return_value=Response(status=403, error="rate")):
            out = github_api.fetch(["openai/openai-python"], _state())
        self.assertEqual(out, [])

    def test_bad_entries_skipped(self):
        self.assertIsNone(github_api._release_to_item({"name": "no url"}, "a/b"))


class TestHnAlgolia(unittest.TestCase):
    def _payload(self, url=None):
        return json.dumps({"hits": [{
            "objectID": "42", "title": "Story", "url": url,
            "points": 100, "num_comments": 5, "author": "pg",
            "created_at": "2026-07-03T08:00:00.000Z",
        }]})

    def test_map_hit_external_url(self):
        it = hn_algolia._hit_to_item(json.loads(self._payload("https://ext.com/a"))["hits"][0], "gpt")
        self.assertEqual(it.url, "https://ext.com/a")
        self.assertEqual(it.meta["points"], 100)
        self.assertEqual(it.meta["query"], "gpt")
        self.assertEqual(it.published_at, "2026-07-03T08:00:00Z")

    def test_map_hit_permalink_fallback(self):
        it = hn_algolia._hit_to_item(json.loads(self._payload(None))["hits"][0], "llm")
        self.assertEqual(it.url, "https://news.ycombinator.com/item?id=42")

    def test_fetch_ok(self):
        with mock.patch.object(hn_algolia, "get", return_value=Response(status=200, body=self._payload("https://e/x"))):
            out = hn_algolia.fetch(["gpt"], _state())
        self.assertEqual(len(out), 1)

    def test_fetch_bad_json_softfails(self):
        with mock.patch.object(hn_algolia, "get", return_value=Response(status=200, body="not json")):
            out = hn_algolia.fetch(["gpt"], _state())
        self.assertEqual(out, [])


class TestOssinsight(unittest.TestCase):
    PAYLOAD = json.dumps({"data": {"rows": [
        {"repo_name": "foo/bar", "stars": "123", "forks": "5",
         "description": "A tool", "total_score": "9.9"},
    ]}})

    def test_map_row(self):
        it = ossinsight._row_to_item(json.loads(self.PAYLOAD)["data"]["rows"][0], "Python")
        self.assertEqual(it.url, "https://github.com/foo/bar")
        self.assertEqual(it.title, "foo/bar")
        self.assertEqual(it.meta["stars"], "123")
        self.assertEqual(it.meta["language"], "Python")

    def test_fetch_ok(self):
        with mock.patch.object(ossinsight, "get", return_value=Response(status=200, body=self.PAYLOAD)):
            out = ossinsight.fetch(["Python"], _state())
        self.assertEqual(len(out), 1)

    def test_fetch_shape_change_softfails(self):
        with mock.patch.object(ossinsight, "get", return_value=Response(status=200, body='{"unexpected": true}')):
            out = ossinsight.fetch(["Python"], _state())
        self.assertEqual(out, [])

    def test_non200_softfails(self):
        with mock.patch.object(ossinsight, "get", return_value=Response(status=500, error="beta down")):
            out = ossinsight.fetch(["Python"], _state())
        self.assertEqual(out, [])


TRENDING_HTML = """
<div>
  <article class="Box-row">
    <h2 class="h3 lh-condensed"><a href="/owner/repo1">owner / repo1</a></h2>
    <p class="col-9 color-fg-muted my-1 pr-4">First trending repo</p>
  </article>
  <article class="Box-row">
    <h2 class="h3 lh-condensed"><a href="/acme/tool?tab=readme">acme / tool</a></h2>
    <p>Second trending repo</p>
  </article>
</div>"""


class TestGithubTrending(unittest.TestCase):
    def test_parse(self):
        items = github_trending.parse_trending(TRENDING_HTML, "python")
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].url, "https://github.com/owner/repo1")
        self.assertEqual(items[0].title, "owner/repo1")
        self.assertEqual(items[0].excerpt, "First trending repo")
        self.assertEqual(items[0].meta["language"], "python")
        self.assertEqual(items[1].meta["repo"], "acme/tool")

    def test_parse_broken_markup_returns_empty(self):
        self.assertEqual(github_trending.parse_trending("<html>nothing here</html>"), [])
        self.assertEqual(github_trending.parse_trending(""), [])

    def test_fetch_network_error_returns_empty(self):
        with mock.patch.object(github_trending, "get", return_value=Response(status=0, error="dns")):
            out = github_trending.fetch(["python"], _state())
        self.assertEqual(out, [])


if __name__ == "__main__":
    unittest.main()
