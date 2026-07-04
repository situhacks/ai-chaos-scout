"""OSSInsight trending-repos API — the grassroots "what's rising" signal.

Endpoint: https://api.ossinsight.io/v1/trends/repos/?period=past_week&language={lang}
Budget:   600 req/hr per IP, keyless. BETA API — endpoints may churn; on any
          non-200 or shape change, soft-fail (return []).
Signal:   stars + 28-day growth velocity; keep growth numbers in Item.meta.

STATUS: SCAFFOLD — implement me (sub-agent A).
"""

from __future__ import annotations

from scout.models import Item
from scout.state import State


def fetch(languages: list[str] | None, state: State) -> list[Item]:
    # TODO(sub-agent A): query per language (default a small set); map rows->Item with growth meta.
    return []
