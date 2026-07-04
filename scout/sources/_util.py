"""Shared, stdlib-only helpers for the Tier-2 source fetchers.

Kept deliberately small and dependency-free (html.parser, datetime, email.utils
only). These are internal to scout.sources; the public contract is each source's
`fetch(...)` returning list[scout.models.Item].
"""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    """Collect text nodes, dropping tags. Skips <script>/<style> content."""

    _SKIP = {"script", "style"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in self._SKIP:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0 and data:
            self._chunks.append(data)

    def text(self) -> str:
        return " ".join(" ".join(self._chunks).split())


def strip_html(raw: str | None) -> str:
    """Return plain text from an HTML/entity-laden string. Never raises."""
    if not raw:
        return ""
    try:
        p = _TextExtractor()
        p.feed(raw)
        p.close()
        return p.text()
    except Exception:
        # Absolute fallback: crude tag strip so we never sink a source on bad markup.
        import re

        return " ".join(re.sub(r"<[^>]+>", " ", raw).split())


def excerpt(raw: str | None, limit: int = 500) -> str:
    """Plain-text excerpt, HTML stripped and clipped to `limit` chars."""
    text = strip_html(raw)
    if len(text) > limit:
        text = text[:limit].rstrip()
    return text


def to_iso_utc(value: str | None) -> str:
    """Normalize a date string to ISO-8601 UTC ('YYYY-MM-DDTHH:MM:SSZ').

    Handles RFC-822 (RSS pubDate) and ISO-8601 (Atom/JSON, incl. trailing 'Z',
    fractional seconds, and numeric offsets). Returns '' if unparseable.
    """
    if not value:
        return ""
    s = value.strip()
    dt: datetime | None = None

    # ISO-8601 first (Atom, GitHub, HN, arXiv date elements).
    iso = s.replace("Z", "+00:00") if s.endswith("Z") else s
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError:
        dt = None

    # RFC-822 (RSS <pubDate>: "Wed, 02 Oct 2002 13:00:00 GMT").
    if dt is None:
        try:
            dt = parsedate_to_datetime(s)
        except (TypeError, ValueError, IndexError):
            dt = None

    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
