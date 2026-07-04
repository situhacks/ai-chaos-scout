"""GitHub Trending — best-effort HTML scrape (no official API).

Endpoint: https://github.com/trending  (optionally ?since=daily|weekly, /{language})
Markup is unofficial and may change without notice: use a TOLERANT parser
(html.parser), and on any parse/network failure just return [] (best-effort skip).
OSSInsight is the more stable structured alternative — this is a supplement.
"""

from __future__ import annotations

from html.parser import HTMLParser

from scout.http import get
from scout.models import Item
from scout.sources._util import excerpt
from scout.state import State


class _TrendingParser(HTMLParser):
    """Pull (full_name, description) pairs out of the trending repo list.

    Each repo lives in ``<article class="Box-row">``; the repo path is the href
    of the ``<a>`` inside the row's ``<h2>``; the blurb is the row's ``<p>``.
    Deliberately forgiving — unknown/changed markup yields fewer rows, never a raise.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.repos: list[tuple[str, str]] = []
        self._in_article = False
        self._in_h2 = False
        self._in_p = False
        self._href: str = ""
        self._desc_parts: list[str] = []

    @staticmethod
    def _has_class(attrs: list[tuple[str, str | None]], needle: str) -> bool:
        for name, val in attrs:
            if name == "class" and val and needle in val:
                return True
        return False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "article" and self._has_class(attrs, "Box-row"):
            self._in_article = True
            self._href = ""
            self._desc_parts = []
        elif self._in_article and tag == "h2":
            self._in_h2 = True
        elif self._in_article and self._in_h2 and tag == "a" and not self._href:
            for name, val in attrs:
                if name == "href" and val:
                    self._href = val.strip()
                    break
        elif self._in_article and tag == "p":
            self._in_p = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "h2" and self._in_h2:
            self._in_h2 = False
        elif tag == "p" and self._in_p:
            self._in_p = False
        elif tag == "article" and self._in_article:
            full_name = self._href.strip("/").split("?")[0]
            if full_name.count("/") == 1:
                desc = " ".join(" ".join(self._desc_parts).split())
                self.repos.append((full_name, desc))
            self._in_article = False
            self._in_h2 = False
            self._in_p = False

    def handle_data(self, data: str) -> None:
        if self._in_article and self._in_p and data:
            self._desc_parts.append(data)


def parse_trending(html_text: str, language: str | None = None) -> list[Item]:
    """Parse a github.com/trending page into Items. Never raises."""
    if not html_text:
        return []
    try:
        parser = _TrendingParser()
        parser.feed(html_text)
        parser.close()
    except Exception:
        return []
    out: list[Item] = []
    for full_name, desc in parser.repos:
        meta: dict = {"repo": full_name}
        if language:
            meta["language"] = language
        out.append(
            Item.create(
                source="github_trending",
                url=f"https://github.com/{full_name}",
                title=full_name,
                published_at="",
                excerpt=excerpt(desc),
                meta=meta,
            )
        )
    return out


def _fetch_url(url: str, language: str | None, state: State) -> list[Item]:
    resp = get(url, conditional_headers=state.get_conditional_headers(url))
    if resp.not_modified:
        return []
    if resp.error or resp.status != 200:
        return []
    state.update_etag(url, resp.etag, resp.last_modified)
    return parse_trending(resp.body, language)


def fetch(languages: list[str] | None, state: State) -> list[Item]:
    items: list[Item] = []
    # Empty/None -> the language-agnostic trending page once.
    targets = languages if languages else [None]
    for language in targets:
        if language:
            url = f"https://github.com/trending/{str(language).strip()}"
        else:
            url = "https://github.com/trending"
        try:
            items.extend(_fetch_url(url, language, state))
        except Exception:
            continue
    return items
