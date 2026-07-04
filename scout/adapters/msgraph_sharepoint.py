"""msgraph_sharepoint.py — Tier-1 adapter scaffold for Microsoft Graph / SharePoint.

    ┌─────────────────────────────────────────────────────────────────────┐
    │ UNTESTED SCAFFOLD. enabled: false. Never exercised in the core path. │
    └─────────────────────────────────────────────────────────────────────┘

Context: the operator's real future input path. In v1, subject material arrives
via the local `folder:` drop-zone; this adapter is how that folder becomes a live
SharePoint document library later. CRITICAL DESIGN RULE: keep the output Item
shape IDENTICAL to `folder:` ingestion so swapping is config-only, not a rewrite.
Real access needs tenant admin consent (app-only Graph perms) — infeasible to
test in-window, hence scaffold-only.

Required env: MSGRAPH_TENANT_ID, MSGRAPH_CLIENT_ID, MSGRAPH_CLIENT_SECRET, MSGRAPH_DRIVE_ID
API shape:    GET https://graph.microsoft.com/v1.0/drives/{id}/root/children
              GET https://graph.microsoft.com/v1.0/drives/{id}/items/{item}/content

STATUS: SCAFFOLD — implement the shape (sub-agent C).
"""

from __future__ import annotations

from datetime import datetime

from scout.adapters.base import SourceAdapter
from scout.models import Item


class MSGraphSharePointAdapter(SourceAdapter):
    key = "msgraph"
    required_env = [
        "MSGRAPH_TENANT_ID",
        "MSGRAPH_CLIENT_ID",
        "MSGRAPH_CLIENT_SECRET",
        "MSGRAPH_DRIVE_ID",
    ]
    UNTESTED = True

    def fetch(self, since: datetime | None = None) -> list[Item]:
        self.ensure_configured()
        # TODO(sub-agent C): client-credentials token + drive children listing.
        # Emit Items whose shape matches folder: ingestion (subject material, not scout signals).
        raise NotImplementedError("msgraph_sharepoint is an untested Tier-1 scaffold")
