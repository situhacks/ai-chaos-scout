"""msgraph_sharepoint.py — Tier-1 adapter scaffold for Microsoft Graph / SharePoint.

    ┌─────────────────────────────────────────────────────────────────────┐
    │ UNTESTED SCAFFOLD. enabled: false. Never exercised in the core path. │
    │ Request-construction is unit-tested OFFLINE only — ZERO live calls.  │
    └─────────────────────────────────────────────────────────────────────┘

Context: the operator's real future input path. In v1, subject material arrives
via the local `folder:` drop-zone; this adapter is how that folder becomes a live
SharePoint document library later. Real access needs tenant admin consent
(app-only Graph perms) — infeasible to test in-window, hence scaffold-only.

CRITICAL DESIGN RULE: this emits STAGE-1 SUBJECT MATERIAL (the same role as the
local `folder:` drop-zone), NOT Stage-2 scout signals. Its `Item` shape MATCHES
folder ingestion — one Item per document (title=file name, url=webUrl,
excerpt=file text, meta carries drive/item ids + size + mimeType) — so swapping
local folder → SharePoint is CONFIG-ONLY, not a rewrite.

Required env: MSGRAPH_TENANT_ID, MSGRAPH_CLIENT_ID, MSGRAPH_CLIENT_SECRET, MSGRAPH_DRIVE_ID
API shape:    POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
                   (client_credentials, scope=https://graph.microsoft.com/.default)
              GET  https://graph.microsoft.com/v1.0/drives/{drive}/root/children
              GET  https://graph.microsoft.com/v1.0/drives/{drive}/items/{id}/content

STATUS: SCAFFOLD — token/listing/content shapes implemented and unit-tested offline.
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

from scout.adapters.base import SourceAdapter
from scout.models import Item

LOGIN_BASE = "https://login.microsoftonline.com"
GRAPH_BASE = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"
USER_AGENT = "ai-chaos-scout/0.1 (+https://github.com/situhacks/ai-chaos-scout)"


@dataclass
class PreparedRequest:
    """A fully-described HTTP request, built WITHOUT performing any I/O."""

    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes | None = None


def build_token_request(tenant_id: str, client_id: str,
                        client_secret: str) -> PreparedRequest:
    """Build the app-only (client-credentials) token request. Pure — no network."""
    url = f"{LOGIN_BASE}/{tenant_id}/oauth2/v2.0/token"
    body = urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": GRAPH_SCOPE,
    }).encode("utf-8")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": USER_AGENT,
    }
    return PreparedRequest("POST", url, headers, body)


def build_children_request(drive_id: str, token: str) -> PreparedRequest:
    """Build the GET drive root children listing request. Pure — no network."""
    url = f"{GRAPH_BASE}/drives/{drive_id}/root/children"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    return PreparedRequest("GET", url, headers)


def build_content_request(drive_id: str, item_id: str, token: str) -> PreparedRequest:
    """Build the GET item content (raw file bytes) request. Pure — no network."""
    url = f"{GRAPH_BASE}/drives/{drive_id}/items/{item_id}/content"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": USER_AGENT,
    }
    return PreparedRequest("GET", url, headers)


def parse_token_response(body: str) -> str:
    """Extract the access token from the token-endpoint JSON body. Pure."""
    return json.loads(body).get("access_token", "") if body else ""


def drive_item_to_item(child: dict[str, Any], drive_id: str,
                       excerpt: str = "") -> Item:
    """Map one Graph driveItem -> the shared `Item` shape (subject material).

    Mirrors local `folder:` ingestion: one Item per document. `excerpt` is the
    (optionally later-fetched) file text; left empty here since content is a
    second request.
    """
    item_id = child.get("id", "")
    url = child.get("webUrl", "")
    file_facet = child.get("file", {}) or {}
    return Item.create(
        source="msgraph",
        url=url,
        title=child.get("name", "") or "",
        published_at=child.get("lastModifiedDateTime", "") or "",
        excerpt=excerpt,
        meta={
            "drive_id": drive_id,
            "item_id": item_id,
            "size": child.get("size"),
            "mimeType": file_facet.get("mimeType", ""),
            "created": child.get("createdDateTime", ""),
        },
    )


def parse_children_response(body: str, drive_id: str) -> list[Item]:
    """Map a drive children JSON body -> list[Item], files only. Pure (no network)."""
    payload = json.loads(body) if body else {}
    items: list[Item] = []
    for child in payload.get("value", []):
        # Skip sub-folders; folder ingestion emits one Item per FILE.
        if "folder" in child:
            continue
        items.append(drive_item_to_item(child, drive_id))
    return items


class MSGraphSharePointAdapter(SourceAdapter):
    key = "msgraph"
    required_env = [
        "MSGRAPH_TENANT_ID",
        "MSGRAPH_CLIENT_ID",
        "MSGRAPH_CLIENT_SECRET",
        "MSGRAPH_DRIVE_ID",
    ]
    UNTESTED = True

    def build_token_request(self) -> PreparedRequest:
        """Build the token request from env creds. Requires configuration."""
        self.ensure_configured()
        import os

        return build_token_request(
            os.environ["MSGRAPH_TENANT_ID"],
            os.environ["MSGRAPH_CLIENT_ID"],
            os.environ["MSGRAPH_CLIENT_SECRET"],
        )

    def _get_token(self) -> str:
        status, body = _perform(self.build_token_request())
        return parse_token_response(body) if status == 200 else ""

    def fetch(self, since: datetime | None = None) -> list[Item]:
        self.ensure_configured()  # raises AdapterNotConfigured when unset
        import os

        drive_id = os.environ["MSGRAPH_DRIVE_ID"]
        token = self._get_token()
        status, body = _perform(build_children_request(drive_id, token))
        return parse_children_response(body, drive_id) if status == 200 else []


def _perform(prepared: PreparedRequest) -> tuple[int, str]:
    """Execute a PreparedRequest. Only reached with real creds — never in tests."""
    req = urllib.request.Request(
        prepared.url, data=prepared.body, headers=prepared.headers,
        method=prepared.method,
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (https only)
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.status, resp.read().decode(charset, errors="replace")
