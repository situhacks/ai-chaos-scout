"""Offline tests for the Tier-1 adapter SCAFFOLDS.

    python -m unittest discover -s tests

These tests NEVER touch the network. They prove two things for every Tier-1
adapter (x_api, reddit_oauth, greptile, msgraph_sharepoint):

  1. Contract: it imports cleanly, subclasses SourceAdapter, sets `UNTESTED = True`,
     declares its `required_env`, and — with NO env vars set — raises
     `AdapterNotConfigured` from its network method(s).
  2. Request construction: with dummy creds, the pure `build_*` helpers produce the
     documented URL / method / headers / params / body. Response-mapping helpers are
     exercised on canned JSON so no live Tier-1 service is ever called.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scout.adapters import greptile, msgraph_sharepoint, reddit_oauth, x_api  # noqa: E402
from scout.adapters.base import AdapterNotConfigured, SourceAdapter  # noqa: E402
from scout.models import Item  # noqa: E402

ALL_ADAPTERS = [
    x_api.XApiAdapter,
    reddit_oauth.RedditOAuthAdapter,
    greptile.GreptileAdapter,
    msgraph_sharepoint.MSGraphSharePointAdapter,
]


def _no_env():
    """Context manager: an environment with NONE of the Tier-1 vars set."""
    return mock.patch.dict(os.environ, {}, clear=True)


class TestAdapterContract(unittest.TestCase):
    def test_all_subclass_source_adapter_and_untested(self):
        for cls in ALL_ADAPTERS:
            self.assertTrue(issubclass(cls, SourceAdapter), cls.__name__)
            self.assertIs(cls.UNTESTED, True, f"{cls.__name__}.UNTESTED must be True")

    def test_all_declare_required_env(self):
        expected = {
            x_api.XApiAdapter: ["X_BEARER_TOKEN"],
            reddit_oauth.RedditOAuthAdapter: ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"],
            greptile.GreptileAdapter: ["GREPTILE_API_KEY", "GITHUB_TOKEN"],
            msgraph_sharepoint.MSGraphSharePointAdapter: [
                "MSGRAPH_TENANT_ID", "MSGRAPH_CLIENT_ID",
                "MSGRAPH_CLIENT_SECRET", "MSGRAPH_DRIVE_ID",
            ],
        }
        for cls, req in expected.items():
            self.assertEqual(cls.required_env, req, cls.__name__)
            self.assertTrue(cls.required_env, f"{cls.__name__} must declare required_env")

    def test_fetch_raises_when_unconfigured(self):
        with _no_env():
            for cls in ALL_ADAPTERS:
                with self.assertRaises(AdapterNotConfigured, msg=cls.__name__):
                    cls().fetch()

    def test_greptile_summarize_repo_raises_when_unconfigured(self):
        with _no_env():
            with self.assertRaises(AdapterNotConfigured):
                greptile.GreptileAdapter().summarize_repo("owner/repo", "what is this?")

    def test_reddit_and_msgraph_token_helpers_raise_when_unconfigured(self):
        with _no_env():
            with self.assertRaises(AdapterNotConfigured):
                reddit_oauth.RedditOAuthAdapter().build_token_request()
            with self.assertRaises(AdapterNotConfigured):
                msgraph_sharepoint.MSGraphSharePointAdapter().build_token_request()

    def test_missing_env_reports_all_missing_names(self):
        with _no_env():
            try:
                msgraph_sharepoint.MSGraphSharePointAdapter().fetch()
            except AdapterNotConfigured as exc:
                self.assertEqual(
                    exc.missing,
                    ["MSGRAPH_TENANT_ID", "MSGRAPH_CLIENT_ID",
                     "MSGRAPH_CLIENT_SECRET", "MSGRAPH_DRIVE_ID"],
                )
            else:
                self.fail("expected AdapterNotConfigured")


class TestXApiConstruction(unittest.TestCase):
    def test_build_search_request_shape(self):
        req = x_api.build_search_request("chaos AI", token="TOK", max_results=50)
        self.assertEqual(req.method, "GET")
        self.assertTrue(req.url.startswith(x_api.SEARCH_URL + "?"))
        self.assertIn("query=chaos+AI", req.url)
        self.assertIn("tweet.fields=created_at%2Cpublic_metrics", req.url)
        self.assertIn("max_results=50", req.url)
        self.assertEqual(req.headers["Authorization"], "Bearer TOK")
        self.assertIsNone(req.body)

    def test_build_requests_uses_env_token(self):
        adapter = x_api.XApiAdapter(queries=["a", "b"])
        with mock.patch.dict(os.environ, {"X_BEARER_TOKEN": "SEKRET"}, clear=True):
            reqs = adapter.build_requests()
        self.assertEqual(len(reqs), 2)
        self.assertTrue(all(r.headers["Authorization"] == "Bearer SEKRET" for r in reqs))

    def test_tweet_to_item_mapping(self):
        item = x_api.tweet_to_item({
            "id": "1789",
            "text": "hello world",
            "created_at": "2026-07-01T09:00:00.000Z",
            "public_metrics": {"like_count": 3},
            "author_id": "42",
        })
        self.assertIsInstance(item, Item)
        self.assertEqual(item.source, "x")
        self.assertEqual(item.url, "https://twitter.com/i/web/status/1789")
        self.assertEqual(item.meta["public_metrics"], {"like_count": 3})
        self.assertEqual(item.meta["author_id"], "42")

    def test_parse_search_response(self):
        body = json.dumps({"data": [{"id": "1", "text": "t"}, {"id": "2", "text": "u"}]})
        items = x_api.parse_search_response(body)
        self.assertEqual([i.url for i in items], [
            "https://twitter.com/i/web/status/1",
            "https://twitter.com/i/web/status/2",
        ])
        self.assertEqual(x_api.parse_search_response(""), [])


class TestRedditConstruction(unittest.TestCase):
    def test_build_token_request_shape(self):
        req = reddit_oauth.build_token_request("CID", "CSECRET")
        self.assertEqual(req.method, "POST")
        self.assertEqual(req.url, reddit_oauth.TOKEN_URL)
        expected_basic = base64.b64encode(b"CID:CSECRET").decode()
        self.assertEqual(req.headers["Authorization"], f"Basic {expected_basic}")
        self.assertIn("User-Agent", req.headers)
        self.assertEqual(req.body, b"grant_type=client_credentials")

    def test_build_listing_request_shape(self):
        req = reddit_oauth.build_listing_request("LocalLLaMA", "TOKEN123", limit=10)
        self.assertEqual(req.method, "GET")
        self.assertTrue(req.url.startswith("https://oauth.reddit.com/r/LocalLLaMA/new?"))
        self.assertIn("limit=10", req.url)
        self.assertEqual(req.headers["Authorization"], "bearer TOKEN123")
        self.assertIn("ai-chaos-scout", req.headers["User-Agent"])

    def test_post_to_item_mapping(self):
        item = reddit_oauth.post_to_item({
            "id": "abc",
            "title": "New model dropped",
            "permalink": "/r/LocalLLaMA/comments/abc/new_model/",
            "created_utc": 1751362800,
            "selftext": "body text",
            "subreddit": "LocalLLaMA",
            "author": "someone",
            "ups": 12,
            "num_comments": 3,
        })
        self.assertEqual(item.source, "reddit_oauth")
        self.assertEqual(
            item.url, "https://www.reddit.com/r/LocalLLaMA/comments/abc/new_model/"
        )
        self.assertTrue(item.published_at.endswith("Z"))
        self.assertEqual(item.meta["subreddit"], "LocalLLaMA")

    def test_parse_listing_and_token_responses(self):
        body = json.dumps({"data": {"children": [
            {"data": {"id": "1", "title": "A", "permalink": "/r/x/1/"}},
            {"data": {"id": "2", "title": "B", "permalink": "/r/x/2/"}},
        ]}})
        self.assertEqual(len(reddit_oauth.parse_listing_response(body)), 2)
        self.assertEqual(
            reddit_oauth.parse_token_response(json.dumps({"access_token": "T"})), "T"
        )


class TestGreptileConstruction(unittest.TestCase):
    def test_parse_repo_identifier(self):
        self.assertEqual(greptile.parse_repo_identifier("owner/repo"), "owner/repo")
        self.assertEqual(
            greptile.parse_repo_identifier("https://github.com/owner/repo"), "owner/repo"
        )
        self.assertEqual(
            greptile.parse_repo_identifier("https://github.com/owner/repo.git"),
            "owner/repo",
        )

    def test_build_index_request_shape(self):
        req = greptile.build_index_request("owner/repo", "GKEY", "GHTOK")
        self.assertEqual(req.method, "POST")
        self.assertTrue(req.url.endswith("/v2/repositories"))
        self.assertEqual(req.headers["Authorization"], "Bearer GKEY")
        self.assertEqual(req.headers["X-GitHub-Token"], "GHTOK")
        self.assertEqual(req.headers["Content-Type"], "application/json")
        payload = json.loads(req.body)
        self.assertEqual(payload["repository"], "owner/repo")
        self.assertEqual(payload["remote"], "github")

    def test_build_query_request_shape(self):
        req = greptile.build_query_request("what is X?", "owner/repo", "GKEY", "GHTOK")
        self.assertEqual(req.method, "POST")
        self.assertTrue(req.url.endswith("/v2/query"))
        payload = json.loads(req.body)
        self.assertEqual(payload["messages"][0]["content"], "what is X?")
        self.assertEqual(payload["repositories"][0]["repository"], "owner/repo")

    def test_parse_query_response(self):
        self.assertEqual(
            greptile.parse_query_response(json.dumps({"message": "the answer"})),
            "the answer",
        )

    def test_fetch_raises_not_implemented_when_configured(self):
        env = {"GREPTILE_API_KEY": "k", "GITHUB_TOKEN": "t"}
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(NotImplementedError):
                greptile.GreptileAdapter().fetch()


class TestMSGraphConstruction(unittest.TestCase):
    def test_build_token_request_shape(self):
        req = msgraph_sharepoint.build_token_request("TENANT", "CID", "CSECRET")
        self.assertEqual(req.method, "POST")
        self.assertEqual(
            req.url, "https://login.microsoftonline.com/TENANT/oauth2/v2.0/token"
        )
        body = req.body.decode()
        self.assertIn("grant_type=client_credentials", body)
        self.assertIn("scope=https%3A%2F%2Fgraph.microsoft.com%2F.default", body)
        self.assertIn("client_id=CID", body)

    def test_build_children_request_shape(self):
        req = msgraph_sharepoint.build_children_request("DRIVE", "TOKEN")
        self.assertEqual(req.method, "GET")
        self.assertEqual(
            req.url, "https://graph.microsoft.com/v1.0/drives/DRIVE/root/children"
        )
        self.assertEqual(req.headers["Authorization"], "Bearer TOKEN")

    def test_build_content_request_shape(self):
        req = msgraph_sharepoint.build_content_request("DRIVE", "ITEM", "TOKEN")
        self.assertEqual(
            req.url, "https://graph.microsoft.com/v1.0/drives/DRIVE/items/ITEM/content"
        )
        self.assertEqual(req.headers["Authorization"], "Bearer TOKEN")

    def test_drive_item_to_item_matches_subject_material_shape(self):
        item = msgraph_sharepoint.drive_item_to_item(
            {
                "id": "01ABC",
                "name": "strategy.docx",
                "webUrl": "https://contoso.sharepoint.com/strategy.docx",
                "lastModifiedDateTime": "2026-07-01T09:00:00Z",
                "size": 2048,
                "file": {"mimeType": "application/vnd.ms-word"},
            },
            drive_id="DRIVE",
        )
        self.assertEqual(item.source, "msgraph")
        self.assertEqual(item.title, "strategy.docx")
        self.assertEqual(item.url, "https://contoso.sharepoint.com/strategy.docx")
        self.assertEqual(item.meta["drive_id"], "DRIVE")
        self.assertEqual(item.meta["item_id"], "01ABC")
        self.assertEqual(item.meta["mimeType"], "application/vnd.ms-word")

    def test_parse_children_response_skips_folders(self):
        body = json.dumps({"value": [
            {"id": "1", "name": "doc.md", "webUrl": "u1", "file": {"mimeType": "text/markdown"}},
            {"id": "2", "name": "subdir", "folder": {"childCount": 3}},
        ]})
        items = msgraph_sharepoint.parse_children_response(body, "DRIVE")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "doc.md")


if __name__ == "__main__":
    unittest.main()
