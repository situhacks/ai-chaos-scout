"""RSS / Atom fetcher — the backbone Tier-2 source.

Covers: OpenAI, Hugging Face, Google AI, arXiv cs.AI, MarkTechPost blogs, plus
Reddit RSS (`reddit.com/r/{sub}/new/.rss`) and YouTube channel feeds
(`youtube.com/feeds/videos.xml?channel_id={ID}`). Parse with `xml.etree` only.

Rules from kit/02-sourcing.md (enforce these):
  - Use conditional requests (ETag / If-Modified-Since) via scout.http + scout.state.
  - arXiv cs.AI is EMPTY on weekends/US holidays — that is normal, not an error.
  - Reddit RSS: 1 request per subreddit per run, >=2s spacing, browser-ish UA,
    tolerate 429 as a SOFT-FAIL skip (never hard-fail the run).
  - YouTube feeds return ~15 newest videos; resolve channel_ids at config time.

Contract: return a list[scout.models.Item] (id auto-derived from url).
"""

from __future__ import annotations

import time
from xml.etree import ElementTree as ET

from scout.http import get
from scout.models import Item
from scout.sources._util import excerpt, to_iso_utc
from scout.state import State

# >=2s between Reddit requests (rule): be a good citizen, avoid 429s.
_REDDIT_SPACING_SECONDS = 2.0


def _local(tag: str) -> str:
    """Local tag name without the ``{namespace}`` prefix."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _find_child_text(elem: ET.Element, names: tuple[str, ...]) -> str:
    for child in elem:
        if _local(child.tag) in names:
            if child.text and child.text.strip():
                return child.text.strip()
    return ""


def _extract_link(entry: ET.Element) -> str:
    """Pull the item/entry link, handling RSS text links and Atom href attrs."""
    fallback = ""
    for child in entry:
        if _local(child.tag) != "link":
            continue
        href = child.attrib.get("href")
        if href:
            rel = child.attrib.get("rel", "alternate")
            if rel == "alternate":
                return href.strip()
            fallback = fallback or href.strip()
        elif child.text and child.text.strip():
            # RSS-style <link>https://...</link>
            return child.text.strip()
    if fallback:
        return fallback
    # Atom entries sometimes only carry an id that is a URL.
    guid = _find_child_text(entry, ("guid", "id"))
    if guid.startswith("http"):
        return guid
    return ""


def _entry_to_item(entry: ET.Element, source: str) -> Item | None:
    title = _find_child_text(entry, ("title",))
    url = _extract_link(entry)
    if not url:
        return None
    published = to_iso_utc(
        _find_child_text(entry, ("published", "pubDate", "date", "updated"))
    )
    summary = _find_child_text(entry, ("description", "summary", "content", "encoded"))
    meta: dict = {}
    author = _find_child_text(entry, ("creator", "author"))
    if not author:
        # Atom <author><name>..</name></author>
        for child in entry:
            if _local(child.tag) == "author":
                author = _find_child_text(child, ("name",))
                break
    if author:
        meta["author"] = author
    return Item.create(
        source=source,
        url=url,
        title=title or url,
        published_at=published,
        excerpt=excerpt(summary),
        meta=meta,
    )


def parse_feed(xml_text: str, source: str) -> list[Item]:
    """Parse an RSS or Atom document into Items. Never raises — returns [] on error."""
    if not xml_text or not xml_text.strip():
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    items: list[Item] = []
    for elem in root.iter():
        if _local(elem.tag) in ("item", "entry"):
            try:
                it = _entry_to_item(elem, source)
            except Exception:
                it = None
            if it is not None:
                items.append(it)
    return items


def _fetch_one(url: str, source: str, state: State,
               tolerate_forbidden: bool = False) -> list[Item]:
    resp = get(url, conditional_headers=state.get_conditional_headers(url))
    if resp.not_modified:
        return []
    if resp.error or resp.status != 200:
        # 429/403 on Reddit (and any soft error) -> skip, don't raise.
        return []
    state.update_etag(url, resp.etag, resp.last_modified)
    return parse_feed(resp.body, source)


def fetch(feeds: list[dict], state: State, reddit_subs: list[str] | None = None,
          youtube_channels: list[str] | None = None) -> list[Item]:
    """Fetch all configured feeds -> normalized Items.

    Args:
        feeds: list of {"id": str, "url": str} from config `tier2.rss`.
        state: shared State (for ETags + seen).
        reddit_subs: subreddit names for reddit_rss (default + lens-derived).
        youtube_channels: channel_ids for YouTube Atom feeds.
    """
    items: list[Item] = []

    for feed in feeds or []:
        if not isinstance(feed, dict):
            continue
        url = feed.get("url")
        fid = feed.get("id") or url
        if not url:
            continue
        try:
            items.extend(_fetch_one(url, str(fid), state))
        except Exception:
            continue

    # YouTube Atom feeds.
    for channel_id in youtube_channels or []:
        if not channel_id:
            continue
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        try:
            items.extend(_fetch_one(url, f"youtube_{channel_id}", state))
        except Exception:
            continue

    # Reddit RSS last: least reliable, rate-spaced, 429/403 tolerant.
    reddit = reddit_subs or []
    for idx, sub in enumerate(reddit):
        if not sub:
            continue
        if idx > 0:
            time.sleep(_REDDIT_SPACING_SECONDS)
        url = f"https://www.reddit.com/r/{sub}/new/.rss"
        try:
            items.extend(_fetch_one(url, f"reddit_{sub}", state, tolerate_forbidden=True))
        except Exception:
            continue

    return items
