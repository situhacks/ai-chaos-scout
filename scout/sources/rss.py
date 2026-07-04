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

STATUS: SCAFFOLD — implement me (sub-agent A).
"""

from __future__ import annotations

from scout.models import Item
from scout.state import State


def fetch(feeds: list[dict], state: State, reddit_subs: list[str] | None = None,
          youtube_channels: list[str] | None = None) -> list[Item]:
    """Fetch all configured feeds -> normalized Items.

    Args:
        feeds: list of {"id": str, "url": str} from config `tier2.rss`.
        state: shared State (for ETags + seen).
        reddit_subs: subreddit names for reddit_rss (default + lens-derived).
        youtube_channels: channel_ids for YouTube Atom feeds.
    """
    # TODO(sub-agent A): implement feedparser-free RSS/Atom parsing with xml.etree,
    # conditional requests, per-source soft-fail, and Reddit spacing/UA discipline.
    return []
