"""Stage-3 renderer: structured report data -> 3 artifacts (.md, .html, .eml).

Deterministic templating only. The AGENT produces the report CONTENT (recommendations,
sliders, digest themes) as structured data and hands it here; this module never makes
judgments, it only renders. Keep templates cleanly separated from the content model so
new skins (PPT, alternate HTML) can be added without touching the pipeline.

Three targets from ONE content model (see kit/05-output-spec.md):
  1. reports/chaos-report-{date}.md   — plain-markdown email body, paste anywhere.
  2. reports/chaos-report-{date}.html — standalone "Instar" field-guide render:
        warm paper ground, drawing-ink text, faint graph-paper grid, inline SVG
        slider strips + metamorphosis stage glyphs (egg->larva->chrysalis->
        emergence->imago), specimen-plate rec cards, Track A blue / Track B madder-red.
  3. reports/chaos-report-{date}.eml  — Outlook-safe (Word engine): built with stdlib
        email.mime; table layout, 600px, inline styles, NO SVG (table-cell sliders,
        text/cid-PNG glyphs), system font stack. Double-click -> Outlook draft. No SMTP.

Email template base: vendor MIT Cerberus hybrid into scout/templates/email/ and
restyle to the design tokens (do not hand-roll Outlook table skeletons).

STATUS: SCAFFOLD — implement me (sub-agent B). The content-model dataclasses below
are the contract the agent writes against; keep them stable.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field

# Allow `python scout/render_report.py` (script mode) as well as module import.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Disruption levels -> metamorphosis stage names (kit/03 + kit/05 design direction).
STAGE_NAMES = {1: "egg", 2: "larva", 3: "chrysalis", 4: "emergence", 5: "imago"}
LEVEL_NAMES = {
    1: "Incremental", 2: "Adjacent", 3: "New line", 4: "Model shift", 5: "Metamorphosis",
}


@dataclass
class Citation:
    """A single clickable source link (Why-now points to the original article/release)."""
    label: str
    url: str


@dataclass
class Recommendation:
    track: str                       # "A" (realistic) or "B" (chaos/metamorphosis)
    index: int                       # 1-based within track -> catalog code [A2], [B1]
    title: str
    body: str                        # 2-3 sentences: what it is
    feasibility: int                 # 1-5
    evidence: int                    # 1-5
    impact: int                      # 1-5
    disruption: int                  # 1-5 (the chaos meter; also the track separator)
    why_now: list[Citation] = field(default_factory=list)   # >=1 digest/scout item URL
    why_us: list[Citation] = field(default_factory=list)    # >=1 compiled-truth fact ref
    first_step: str = ""             # Track A only: <=2-week experiment
    metamorphosis: str = ""          # Track B only: before/after narrative
    kill_criteria: str = ""          # Track B only: observable result that falsifies it

    @property
    def code(self) -> str:
        return f"[{self.track}{self.index}]"

    @property
    def stage(self) -> str:
        return STAGE_NAMES.get(self.disruption, "")


@dataclass
class DigestTheme:
    heading: str
    body: str                        # 2-4 sentences, every claim hyperlinked inline (markdown)
    citations: list[Citation] = field(default_factory=list)


@dataclass
class Provenance:
    scanned: int = 0
    sources: int = 0
    relevant: int = 0
    soft_failed: list[str] = field(default_factory=list)
    run_files: list[str] = field(default_factory=list)


@dataclass
class ReportModel:
    subject_name: str
    date: str
    subject_line: str                # "[AI Chaos Scout] {Co} — week of {date}: {sharpest rec}"
    tldr: list[str]                  # <=3 bullets: defining trend, top realistic, top chaos
    recommendations: list[Recommendation]
    digest_themes: list[DigestTheme]
    provenance: Provenance


def render_markdown(model: ReportModel) -> str:
    raise NotImplementedError("sub-agent B: render the plain-markdown email body")


def render_html(model: ReportModel) -> str:
    raise NotImplementedError("sub-agent B: render the standalone Instar HTML (inline SVG)")


def render_eml(model: ReportModel) -> bytes:
    raise NotImplementedError("sub-agent B: build the Outlook-safe .eml via email.mime")


def render_all(model: ReportModel, out_dir: str | None = None) -> dict:
    """Write all three artifacts; return {'md':path,'html':path,'eml':path}."""
    raise NotImplementedError("sub-agent B: write .md/.html/.eml to reports/")


def load_model_from_json(path: str) -> ReportModel:
    """The agent writes the structured report to runs/{date}/report.json; load it here.

    This is the seam between the agentic Stage-3 (judgment) and deterministic rendering.
    """
    raise NotImplementedError("sub-agent B: hydrate ReportModel from the agent's report.json")


def main() -> int:
    ap = argparse.ArgumentParser(description="AI Chaos Scout — Stage 3 render")
    ap.add_argument("--input", required=True, help="path to the agent's report.json")
    ap.add_argument("--out", default=None, help="output dir (default: reports/)")
    args = ap.parse_args()
    model = load_model_from_json(args.input)
    paths = render_all(model, args.out)
    for kind, p in paths.items():
        print(f"{kind}: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
