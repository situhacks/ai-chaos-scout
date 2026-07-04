"""greptile.py — Tier-1 adapter scaffold for Greptile repo-understanding at scale.

    ┌─────────────────────────────────────────────────────────────────────┐
    │ UNTESTED SCAFFOLD. enabled: false. Never exercised in the core path. │
    │ Request-construction is unit-tested OFFLINE only — ZERO live calls.  │
    └─────────────────────────────────────────────────────────────────────┘

Context: in the keyless v1, Stage-1 repo understanding is done by the IDE agent
reading the cloned repo directly (no Greptile). This scaffold is the "at scale"
replacement: Greptile indexes a repo and answers structured questions about it.
Requires a Greptile key AND a GitHub token; paid.

IMPORTANT: Greptile feeds STAGE 1 (repo understanding for the lens), NOT the
Stage-2 `Item` stream. The real entrypoint here is `summarize_repo(repo_url,
question)`; `fetch()` deliberately raises NotImplementedError because there is
no Item stream to produce. It shares the "configured-by-env, raises-when-absent"
discipline with the other adapters. Built to the documented shape but NEVER run.

Required env: GREPTILE_API_KEY, GITHUB_TOKEN
API shape:    POST https://api.greptile.com/v2/repositories  (index a repo)
              POST https://api.greptile.com/v2/query         (ask about repos)
              Authorization: Bearer {greptile_key}
              X-GitHub-Token: {github_token}

STATUS: SCAFFOLD — index/query shapes implemented and unit-tested offline.
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from scout.adapters.base import SourceAdapter
from scout.models import Item

API_BASE = "https://api.greptile.com/v2"
DEFAULT_REMOTE = "github"
DEFAULT_BRANCH = "main"


@dataclass
class PreparedRequest:
    """A fully-described HTTP request, built WITHOUT performing any I/O."""

    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes | None = None


def _auth_headers(greptile_key: str, github_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {greptile_key}",
        "X-GitHub-Token": github_token,
        "Content-Type": "application/json",
    }


def parse_repo_identifier(repo_url: str) -> str:
    """Reduce a repo URL (or 'owner/repo') to Greptile's 'owner/repo' identifier."""
    ref = repo_url.strip().rstrip("/")
    if ref.startswith("http://") or ref.startswith("https://"):
        # https://github.com/owner/repo(.git) -> owner/repo
        parts = [p for p in ref.split("/") if p]
        ref = "/".join(parts[-2:]) if len(parts) >= 2 else parts[-1]
    if ref.endswith(".git"):
        ref = ref[: -len(".git")]
    return ref


def repo_ref(repo_url: str, remote: str = DEFAULT_REMOTE,
             branch: str = DEFAULT_BRANCH) -> dict[str, str]:
    """The repository reference object Greptile expects in both endpoints."""
    return {"remote": remote, "repository": parse_repo_identifier(repo_url), "branch": branch}


def build_index_request(repo_url: str, greptile_key: str, github_token: str,
                        remote: str = DEFAULT_REMOTE,
                        branch: str = DEFAULT_BRANCH) -> PreparedRequest:
    """Build the POST /repositories index request. Pure — no network."""
    ref = repo_ref(repo_url, remote=remote, branch=branch)
    body = json.dumps(ref).encode("utf-8")
    return PreparedRequest(
        "POST", f"{API_BASE}/repositories", _auth_headers(greptile_key, github_token), body
    )


def build_query_request(question: str, repo_url: str, greptile_key: str,
                        github_token: str, remote: str = DEFAULT_REMOTE,
                        branch: str = DEFAULT_BRANCH) -> PreparedRequest:
    """Build the POST /query ask request. Pure — no network."""
    payload: dict[str, Any] = {
        "messages": [{"role": "user", "content": question}],
        "repositories": [repo_ref(repo_url, remote=remote, branch=branch)],
    }
    body = json.dumps(payload).encode("utf-8")
    return PreparedRequest(
        "POST", f"{API_BASE}/query", _auth_headers(greptile_key, github_token), body
    )


def parse_query_response(body: str) -> str:
    """Extract the assistant answer from a /query JSON body. Pure (no network)."""
    payload = json.loads(body) if body else {}
    # Greptile returns {"message": "..."} (and a sources list we ignore here).
    return payload.get("message", "") or ""


class GreptileAdapter(SourceAdapter):
    key = "greptile"
    required_env = ["GREPTILE_API_KEY", "GITHUB_TOKEN"]
    UNTESTED = True

    def _creds(self) -> tuple[str, str]:
        import os

        return os.environ["GREPTILE_API_KEY"], os.environ["GITHUB_TOKEN"]

    def summarize_repo(self, repo_url: str, question: str) -> str:
        """The real Stage-1 use: index `repo_url`, then ask `question`.

        Network method — raises AdapterNotConfigured when creds are absent.
        """
        self.ensure_configured()
        greptile_key, github_token = self._creds()
        # Kick off indexing (indexing is asynchronous server-side; a production
        # client would poll GET /repositories/{id} until "COMPLETED" before asking).
        _perform(build_index_request(repo_url, greptile_key, github_token))
        status, body = _perform(
            build_query_request(question, repo_url, greptile_key, github_token)
        )
        return parse_query_response(body) if status == 200 else ""

    def fetch(self, since: datetime | None = None) -> list[Item]:
        # Greptile is a Stage-1 repo-understanding tool, not a Stage-2 signal source.
        self.ensure_configured()  # raises AdapterNotConfigured when unset
        raise NotImplementedError(
            "greptile is a Stage-1 repo-understanding tool (feeds the lens), not a "
            "Stage-2 scout source. It produces no Item stream — use summarize_repo()."
        )


def _perform(prepared: PreparedRequest) -> tuple[int, str]:
    """Execute a PreparedRequest. Only reached with real creds — never in tests."""
    req = urllib.request.Request(
        prepared.url, data=prepared.body, headers=prepared.headers,
        method=prepared.method,
    )
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (https only)
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.status, resp.read().decode(charset, errors="replace")
