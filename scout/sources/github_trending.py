"""GitHub Trending — best-effort HTML scrape (no official API).

Endpoint: https://github.com/trending  (optionally ?since=daily|weekly, /{language})
Markup is unofficial and may change without notice: use a TOLERANT parser
(html.parser), and on any parse/network failure just return [] (best-effort skip).
OSSInsight is the more stable structured alternative — this is a supplement.

STATUS: SCAFFOLD — implement me (sub-agent A).
"""

from __future__ import annotations

from scout.models import Item
from scout.state import State


def fetch(languages: list[str] | None, state: State) -> list[Item]:
    # TODO(sub-agent A): tolerant html.parser scrape of the trending list; skip on any error.
    return []
