"""Stdlib-only HTTP helper with conditional-request + soft-fail discipline.

Every Tier-2 fetcher should go through `get()` so the ETag / rate-limit / timeout
rules from kit/02-sourcing.md are enforced in one place. No `requests`, no pip.
"""

from __future__ import annotations

import gzip
import io
import urllib.error
import urllib.request
from dataclasses import dataclass

# A browser-ish UA — Reddit RSS and a few CDNs reject obviously-scripted agents.
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0 Safari/537.36 ai-chaos-scout/0.1 (+https://github.com/situhacks/ai-chaos-scout)"
)

DEFAULT_TIMEOUT = 20


@dataclass
class Response:
    """Result of a conditional GET.

    status:        HTTP status (304 = not modified, use your cache)
    body:          decoded text ("" on 304 or error)
    etag:          response ETag, persist via State.update_etag
    last_modified: response Last-Modified, persist via State.update_etag
    not_modified:  True when the server returned 304
    error:         populated on a soft-failed request (caller logs + skips source)
    """

    status: int
    body: str = ""
    etag: str | None = None
    last_modified: str | None = None
    not_modified: bool = False
    error: str | None = None


def get(
    url: str,
    conditional_headers: dict[str, str] | None = None,
    extra_headers: dict[str, str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Response:
    """GET a URL, honoring conditional headers. Never raises — soft-fails into Response.error."""
    headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"}
    if conditional_headers:
        headers.update(conditional_headers)
    if extra_headers:
        headers.update(extra_headers)

    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
            charset = resp.headers.get_content_charset() or "utf-8"
            return Response(
                status=resp.status,
                body=raw.decode(charset, errors="replace"),
                etag=resp.headers.get("ETag"),
                last_modified=resp.headers.get("Last-Modified"),
            )
    except urllib.error.HTTPError as e:
        if e.code == 304:
            return Response(status=304, not_modified=True)
        return Response(status=e.code, error=f"HTTP {e.code}: {e.reason}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return Response(status=0, error=f"network error: {e}")
