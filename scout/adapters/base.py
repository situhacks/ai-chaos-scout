"""Tier-1 adapter interface — the seam that lets the keyless v1 grow into the
keyed/paid enterprise version WITHOUT a rebuild.

Every Tier-1 adapter (x_api, reddit_oauth, greptile, msgraph_sharepoint) subclasses
`SourceAdapter`, reads its credentials from environment variables, and raises
`AdapterNotConfigured` when they are absent. Adapters are UNTESTED SCAFFOLDS:
they conform to this interface and are documented honestly, but are
`enabled: false` in config and never exercised in the core path.

Stdlib-only. Do NOT add third-party imports to Tier-1 scaffolds either — keep the
import surface clean so `import scout.adapters.*` never fails on a fresh clone.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from datetime import datetime

from scout.models import Item


class AdapterNotConfigured(RuntimeError):
    """Raised when a Tier-1 adapter is invoked without its required credentials.

    The orchestrator catches this and soft-fails the source (logs + continues),
    exactly like a network error on a Tier-2 source.
    """

    def __init__(self, adapter: str, missing: list[str]):
        self.adapter = adapter
        self.missing = missing
        super().__init__(
            f"{adapter} is an UNTESTED Tier-1 scaffold and is not configured. "
            f"Missing environment variable(s): {', '.join(missing)}. "
            f"This adapter is enabled: false by default and has never been exercised."
        )


class SourceAdapter(ABC):
    """Common interface for all sources. Tier-2 sources may also adopt it, but the
    Tier-1 scaffolds MUST.

    Subclass contract:
        - class attr `key`: short source key written into Item.source
        - class attr `required_env`: list of env var names the adapter needs
        - `fetch(since)` returns a list[Item]; raises AdapterNotConfigured if creds absent
    """

    key: str = "base"
    required_env: list[str] = []
    #: Untested scaffold banner surfaced in the README and logs.
    UNTESTED: bool = True

    def missing_env(self) -> list[str]:
        return [name for name in self.required_env if not os.environ.get(name)]

    def ensure_configured(self) -> None:
        missing = self.missing_env()
        if missing:
            raise AdapterNotConfigured(self.__class__.__name__, missing)

    @abstractmethod
    def fetch(self, since: datetime | None = None) -> list[Item]:
        """Return normalized items published since `since` (or a sane default window).

        Must raise `AdapterNotConfigured` before any network call if credentials
        are missing.
        """
        raise NotImplementedError
