"""Stage-3 renderer: structured report data -> 3 artifacts (.md, .html, .eml).

Deterministic templating only. The AGENT produces the report CONTENT (recommendations,
sliders, digest themes) as structured data and hands it here; this module never makes
judgments, it only renders. Keep templates cleanly separated from the content model so
new skins (PPT, alternate HTML) can be added without touching the pipeline.

Three targets from ONE content model:
  1. reports/chaos-report-{date}.md   -- plain-markdown email body, paste anywhere.
  2. reports/chaos-report-{date}.html -- standalone "Instar" field-guide render:
        warm paper ground, drawing-ink text, faint graph-paper grid, inline SVG
        slider strips + metamorphosis stage glyphs (egg->larva->chrysalis->
        emergence->imago), specimen-plate rec cards, Track A blue / Track B madder-red.
  3. reports/chaos-report-{date}.eml  -- Outlook-safe (Word engine): built with stdlib
        email.mime; table layout, 600px, inline styles, NO SVG (table-cell sliders,
        text stage glyphs), system font stack. Double-click -> Outlook draft. No SMTP.

Email template base: vendored MIT Cerberus hybrid (scout/templates/email/).
"""

from __future__ import annotations

import argparse
import base64
import html as html_mod
import json
import os
import re
import sys
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Allow `python scout/render_report.py` (script mode) as well as module import.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Disruption levels -> metamorphosis stage names.
STAGE_NAMES = {1: "egg", 2: "larva", 3: "chrysalis", 4: "emergence", 5: "imago"}
LEVEL_NAMES = {
    1: "Incremental", 2: "Adjacent", 3: "New line", 4: "Model shift", 5: "Metamorphosis",
}

# ── Design tokens (Instar field-guide language) ────────────────────────────────
PAPER = "#f4efe4"
INK = "#1f3a5f"
MADDER = "#8c3b2e"
GRID_RGBA = "rgba(31,58,95,0.06)"
FONT_SANS = "Inter, system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
FONT_MONO = "ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, monospace"
EMAIL_FONT = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"

# Unicode stage glyphs for email (Outlook-safe, no SVG).
EMAIL_STAGE_GLYPHS = {
    1: "\u25cb",  # egg
    2: "\u25d4",  # larva
    3: "\u25d1",  # chrysalis
    4: "\u25d5",  # emergence
    5: "\u25cf",  # imago
}

# ═══════════════════════════════════════════════════════════════════════════════
# CONTENT MODEL — stable contract, other workstreams depend on these fields.
# You may add optional fields with defaults; do NOT rename/remove existing ones.
# ═══════════════════════════════════════════════════════════════════════════════


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
    subject_line: str                # "[AI Chaos Scout] {Co} -- week of {date}: ..."
    tldr: list[str]                  # <=3 bullets
    recommendations: list[Recommendation]
    digest_themes: list[DigestTheme]
    provenance: Provenance


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _esc(text: str) -> str:
    return html_mod.escape(str(text))


def _track_color(rec: Recommendation) -> str:
    return MADDER if rec.track == "B" else INK


def _citations_md(citations: list[Citation]) -> str:
    return ", ".join(f"[{c.label}]({c.url})" for c in citations)


def _citations_html(citations: list[Citation], color: str = INK) -> str:
    parts = []
    for c in citations:
        parts.append(
            f'<a href="{_esc(c.url)}" style="color:{color};text-decoration:underline">'
            f'{_esc(c.label)}</a>'
        )
    return ", ".join(parts)


def _md_links_to_html(text: str, color: str = INK) -> str:
    """Convert [label](url) markdown links to HTML <a> tags."""
    def _repl(m: re.Match[str]) -> str:
        label = _esc(m.group(1))
        url = html_mod.escape(m.group(2), quote=True)
        return f'<a href="{url}" style="color:{color};text-decoration:underline">{label}</a>'
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', _repl, text)


# ═══════════════════════════════════════════════════════════════════════════════
# INLINE SVG — stage glyphs and slider strips (validated XML, self-contained)
# ═══════════════════════════════════════════════════════════════════════════════

_SVG_NS = 'xmlns="http://www.w3.org/2000/svg"'


def _svg_stage_glyph(level: int, color: str = INK) -> str:
    """Return inline SVG for one of the 5 metamorphosis stage glyphs."""
    c = color
    if level == 1:  # egg
        return (
            f'<svg {_SVG_NS} viewBox="0 0 24 32" width="24" height="32"'
            ' style="vertical-align:middle">'
            f'<ellipse cx="12" cy="18" rx="8" ry="11" fill="none" stroke="{c}"'
            ' stroke-width="1.5"/>'
            f'<ellipse cx="12" cy="18" rx="5" ry="7" fill="none" stroke="{c}"'
            ' stroke-width="0.5" opacity="0.3"/>'
            '</svg>'
        )
    if level == 2:  # larva
        return (
            f'<svg {_SVG_NS} viewBox="0 0 48 24" width="48" height="24"'
            ' style="vertical-align:middle">'
            f'<circle cx="8" cy="12" r="6" fill="none" stroke="{c}" stroke-width="1.2"/>'
            f'<circle cx="19" cy="12" r="5.5" fill="none" stroke="{c}" stroke-width="1.2"/>'
            f'<circle cx="29" cy="12" r="5" fill="none" stroke="{c}" stroke-width="1.2"/>'
            f'<circle cx="38" cy="13" r="4" fill="none" stroke="{c}" stroke-width="1.2"/>'
            f'<circle cx="6" cy="8" r="1" fill="{c}"/>'
            '</svg>'
        )
    if level == 3:  # chrysalis
        return (
            f'<svg {_SVG_NS} viewBox="0 0 24 36" width="24" height="36"'
            ' style="vertical-align:middle">'
            f'<line x1="12" y1="0" x2="12" y2="8" stroke="{c}" stroke-width="1"/>'
            f'<path d="M12,8 Q5,16 7,28 Q12,34 17,28 Q19,16 12,8Z" fill="none"'
            f' stroke="{c}" stroke-width="1.5"/>'
            f'<path d="M9,18 Q12,16 15,18" fill="none" stroke="{c}"'
            ' stroke-width="0.6" opacity="0.5"/>'
            f'<path d="M8,23 Q12,21 16,23" fill="none" stroke="{c}"'
            ' stroke-width="0.6" opacity="0.5"/>'
            '</svg>'
        )
    if level == 4:  # emergence
        return (
            f'<svg {_SVG_NS} viewBox="0 0 36 36" width="36" height="36"'
            ' style="vertical-align:middle">'
            f'<path d="M18,6 Q13,14 15,26 Q18,30 21,26 Q23,14 18,6Z" fill="none"'
            f' stroke="{c}" stroke-width="1" stroke-dasharray="3,2"/>'
            f'<path d="M15,14 Q6,8 3,16 Q5,24 15,22" fill="none" stroke="{c}"'
            ' stroke-width="1.5"/>'
            f'<path d="M21,14 Q30,8 33,16 Q31,24 21,22" fill="none" stroke="{c}"'
            ' stroke-width="1.5"/>'
            '</svg>'
        )
    if level == 5:  # imago
        return (
            f'<svg {_SVG_NS} viewBox="0 0 40 36" width="40" height="36"'
            ' style="vertical-align:middle">'
            f'<ellipse cx="20" cy="20" rx="2" ry="10" fill="none" stroke="{c}"'
            ' stroke-width="1.2"/>'
            f'<path d="M18,14 Q6,4 2,14 Q4,24 18,22" fill="none" stroke="{c}"'
            ' stroke-width="1.5"/>'
            f'<path d="M22,14 Q34,4 38,14 Q36,24 22,22" fill="none" stroke="{c}"'
            ' stroke-width="1.5"/>'
            f'<path d="M18,22 Q10,28 8,32 Q14,30 18,26" fill="none" stroke="{c}"'
            ' stroke-width="1.2"/>'
            f'<path d="M22,22 Q30,28 32,32 Q26,30 22,26" fill="none" stroke="{c}"'
            ' stroke-width="1.2"/>'
            f'<line x1="17" y1="10" x2="14" y2="4" stroke="{c}" stroke-width="1"/>'
            f'<line x1="23" y1="10" x2="26" y2="4" stroke="{c}" stroke-width="1"/>'
            f'<circle cx="13" cy="3" r="1" fill="{c}"/>'
            f'<circle cx="27" cy="3" r="1" fill="{c}"/>'
            '</svg>'
        )
    return ""


def _svg_slider(value: int, color: str = INK) -> str:
    """Inline SVG 5-cell slider strip. Cells up to *value* are filled."""
    cells = []
    for i in range(5):
        fill = color if i < value else "none"
        opacity = "" if i < value else ' opacity="0.25"'
        cells.append(
            f'<rect x="{i * 22}" y="1" width="20" height="12"'
            f' fill="{fill}" stroke="{color}" stroke-width="1" rx="1"{opacity}/>'
        )
    return (
        f'<svg {_SVG_NS} viewBox="0 0 110 14" width="110" height="14"'
        ' style="vertical-align:middle">'
        + "".join(cells) + '</svg>'
    )


# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL HELPERS (Outlook-safe, no SVG)
# ═══════════════════════════════════════════════════════════════════════════════

def _email_slider_cells(value: int, color: str = INK) -> str:
    """Table-cell slider for the email render (no SVG)."""
    cells = []
    for i in range(5):
        if i < value:
            style = f"width:14px;height:10px;background-color:{color};font-size:1px;"
        else:
            style = (
                f"width:14px;height:10px;border:1px solid {color};"
                "background-color:transparent;font-size:1px;"
            )
        cells.append(f'<td style="{style}">&nbsp;</td>')
    return (
        '<table cellpadding="0" cellspacing="1" border="0"'
        ' style="display:inline-table;border-collapse:separate;">'
        '<tr>' + "".join(cells) + '</tr></table>'
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MARKDOWN RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def render_markdown(model: ReportModel) -> str:
    """Render the plain-markdown email body."""
    lines: list[str] = []

    # Subject
    lines.append(f"# {model.subject_line}")
    lines.append("")

    # TL;DR
    lines.append("## TL;DR")
    lines.append("")
    for bullet in model.tldr:
        lines.append(f"- {bullet}")
    lines.append("")

    # Scoreboard
    lines.append("## Scoreboard")
    lines.append("")
    lines.append("| Code | Title | Feasibility | Evidence | Impact | Disruption | Stage |")
    lines.append("|------|-------|-------------|----------|--------|------------|-------|")
    for rec in model.recommendations:
        lines.append(
            f"| {rec.code} | {rec.title} | {rec.feasibility}/5 | {rec.evidence}/5 "
            f"| {rec.impact}/5 | {rec.disruption}/5 | {rec.stage} |"
        )
    lines.append("")

    # Track A
    track_a = [r for r in model.recommendations if r.track == "A"]
    if track_a:
        lines.append("## Track A \u2014 Realistic Moves")
        lines.append("")
        for rec in track_a:
            level_name = LEVEL_NAMES.get(rec.disruption, "")
            lines.append(f"### {rec.code} {rec.title}")
            lines.append(
                f"**Level {rec.disruption} \u2014 {level_name}** \u00b7 "
                f"Feasibility {rec.feasibility}/5 \u00b7 Evidence {rec.evidence}/5 \u00b7 "
                f"Impact {rec.impact}/5 \u00b7 Disruption {rec.disruption}/5"
            )
            lines.append("")
            lines.append(rec.body)
            lines.append("")
            if rec.why_now:
                lines.append(f"**Why now:** {_citations_md(rec.why_now)}")
            if rec.why_us:
                lines.append(f"**Why us:** {_citations_md(rec.why_us)}")
            if rec.first_step:
                lines.append(f"**First testable step:** {rec.first_step}")
            lines.append("")

    # Track B
    track_b = [r for r in model.recommendations if r.track == "B"]
    if track_b:
        lines.append("## Track B \u2014 Chaos / Metamorphosis")
        lines.append("")
        for rec in track_b:
            level_name = LEVEL_NAMES.get(rec.disruption, "")
            lines.append(f"### {rec.code} {rec.title}")
            lines.append(
                f"**Level {rec.disruption} \u2014 {level_name}** \u00b7 "
                f"Feasibility {rec.feasibility}/5 \u00b7 Evidence {rec.evidence}/5 \u00b7 "
                f"Impact {rec.impact}/5 \u00b7 Disruption {rec.disruption}/5"
            )
            lines.append("")
            lines.append(rec.body)
            lines.append("")
            if rec.why_now:
                lines.append(f"**Why now:** {_citations_md(rec.why_now)}")
            if rec.why_us:
                lines.append(f"**Why us:** {_citations_md(rec.why_us)}")
            if rec.metamorphosis:
                lines.append(f"**Metamorphosis narrative:** {rec.metamorphosis}")
            if rec.kill_criteria:
                lines.append(f"**Kill criteria:** {rec.kill_criteria}")
            lines.append("")

    # Deep Dive
    if model.digest_themes:
        lines.append("## Deep Dive \u2014 Digest Themes")
        lines.append("")
        for theme in model.digest_themes:
            lines.append(f"### {theme.heading}")
            lines.append("")
            lines.append(theme.body)
            lines.append("")
            if theme.citations:
                lines.append(f"Sources: {_citations_md(theme.citations)}")
            lines.append("")

    # Provenance
    prov = model.provenance
    lines.append("## Provenance")
    lines.append("")
    lines.append(
        f"Scanned **{prov.scanned}** items from **{prov.sources}** sources, "
        f"**{prov.relevant}** relevant."
    )
    if prov.soft_failed:
        lines.append(f"Soft-failed sources: {', '.join(prov.soft_failed)}")
    if prov.run_files:
        lines.append("Run files: " + ", ".join(f"`{f}`" for f in prov.run_files))
    lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# HTML RENDERER (standalone Instar field-guide)
# ═══════════════════════════════════════════════════════════════════════════════

_HTML_CSS = f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  background-color: {PAPER};
  color: {INK};
  font-family: {FONT_SANS};
  font-weight: 300;
  line-height: 1.65;
  background-image:
    linear-gradient({GRID_RGBA} 1px, transparent 1px),
    linear-gradient(90deg, {GRID_RGBA} 1px, transparent 1px);
  background-size: 20px 20px;
  padding: 48px 24px;
}}
.page {{ max-width: 740px; margin: 0 auto; }}
h1 {{
  font-weight: 300; font-size: 1.6rem; letter-spacing: 0.02em;
  border-bottom: 1px solid rgba(31,58,95,0.2); padding-bottom: 12px; margin-bottom: 20px;
}}
.section-label {{
  font-weight: 400; font-size: 0.78rem; letter-spacing: 0.14em;
  text-transform: uppercase; color: {INK}; margin: 36px 0 14px; display: block;
}}
.section-label.madder {{ color: {MADDER}; }}
.tldr {{ margin-bottom: 28px; }}
.tldr ul {{ list-style: none; padding: 0; }}
.tldr li {{ padding: 3px 0 3px 18px; position: relative; font-size: 0.95rem; }}
.tldr li::before {{ content: "\u2014"; position: absolute; left: 0; }}
table.scoreboard {{
  width: 100%; border-collapse: collapse; font-size: 0.82rem; margin-bottom: 8px;
}}
table.scoreboard th {{
  text-align: left; font-weight: 400; letter-spacing: 0.1em; text-transform: uppercase;
  font-size: 0.68rem; padding: 7px 10px; border-bottom: 2px solid rgba(31,58,95,0.2);
}}
table.scoreboard td {{
  padding: 7px 10px; border-bottom: 1px solid rgba(31,58,95,0.08);
  font-family: {FONT_MONO}; font-size: 0.8rem;
}}
table.scoreboard td.title-cell {{
  font-family: {FONT_SANS}; font-weight: 400; font-size: 0.82rem;
}}
.rec-card {{
  border: 1px solid rgba(31,58,95,0.18); padding: 22px 24px;
  margin: 14px 0; background: rgba(255,255,255,0.35);
}}
.rec-card.track-b {{ border-color: rgba(140,59,46,0.25); }}
.rec-card-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }}
.rec-code {{
  font-family: {FONT_MONO}; font-size: 0.82rem; font-weight: 600;
}}
.rec-level {{ font-size: 0.78rem; opacity: 0.7; }}
.rec-title {{ font-weight: 400; font-size: 1.15rem; margin: 8px 0 6px; }}
.rec-body {{ font-size: 0.92rem; margin-bottom: 12px; }}
.slider-row {{ display: flex; gap: 14px; flex-wrap: wrap; margin: 10px 0; }}
.slider-item {{ display: flex; align-items: center; gap: 5px; }}
.slider-label {{
  font-size: 0.68rem; letter-spacing: 0.05em; text-transform: uppercase; font-weight: 400;
}}
.rec-detail {{ font-size: 0.88rem; margin: 4px 0; }}
.rec-detail strong {{ font-weight: 500; }}
.fig-caption {{
  font-size: 0.72rem; font-style: italic; color: rgba(31,58,95,0.55); margin-top: 10px;
}}
.theme-block {{ margin: 14px 0; padding: 14px 0; border-bottom: 1px solid rgba(31,58,95,0.08); }}
.theme-heading {{ font-weight: 400; font-size: 1.05rem; margin-bottom: 6px; }}
.theme-body {{ font-size: 0.9rem; }}
.provenance {{
  margin-top: 36px; padding-top: 14px; border-top: 1px solid rgba(31,58,95,0.2);
  font-size: 0.82rem; color: rgba(31,58,95,0.65);
}}
.provenance strong {{ font-weight: 500; }}
.mono {{ font-family: {FONT_MONO}; }}
a {{ color: {INK}; text-decoration-color: rgba(31,58,95,0.35); }}
a.madder {{ color: {MADDER}; text-decoration-color: rgba(140,59,46,0.35); }}
.gemini-visual {{ max-width: 100%; margin: 12px 0; border: 1px solid rgba(31,58,95,0.1); }}
"""


def _render_html_impl(
    model: ReportModel,
    gemini_visuals: dict[str, bytes] | None = None,
) -> str:
    """Build the full standalone Instar HTML report."""
    gemini_visuals = gemini_visuals or {}
    parts: list[str] = []

    parts.append(
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>{_esc(model.subject_line)}</title>\n'
        f'<style>{_HTML_CSS}</style>\n'
        '</head>\n<body>\n<div class="page">\n'
    )

    # Header
    parts.append(f'<h1>{_esc(model.subject_line)}</h1>\n')

    # TL;DR
    parts.append('<div class="tldr">\n<span class="section-label">TL;DR</span>\n<ul>\n')
    for bullet in model.tldr:
        parts.append(f'<li>{_esc(bullet)}</li>\n')
    parts.append('</ul>\n</div>\n')

    # Scoreboard
    parts.append('<span class="section-label">Scoreboard</span>\n')
    parts.append('<table class="scoreboard">\n<thead><tr>')
    for hdr in ("Code", "Title", "F", "E", "I", "D", "Stage"):
        parts.append(f'<th>{hdr}</th>')
    parts.append('</tr></thead>\n<tbody>\n')
    for rec in model.recommendations:
        tc = _track_color(rec)
        parts.append('<tr>')
        parts.append(f'<td style="color:{tc}">{_esc(rec.code)}</td>')
        parts.append(f'<td class="title-cell">{_esc(rec.title)}</td>')
        for val in (rec.feasibility, rec.evidence, rec.impact, rec.disruption):
            parts.append(f'<td>{val}</td>')
        parts.append(f'<td style="font-size:1.1rem">{_svg_stage_glyph(rec.disruption, tc)}</td>')
        parts.append('</tr>\n')
    parts.append('</tbody>\n</table>\n')

    # Track A
    track_a = [r for r in model.recommendations if r.track == "A"]
    fig_num = 0
    if track_a:
        parts.append('<span class="section-label">Track A \u2014 Realistic Moves</span>\n')
        for rec in track_a:
            fig_num += 1
            parts.append(_html_rec_card(rec, fig_num, gemini_visuals))

    # Track B
    track_b = [r for r in model.recommendations if r.track == "B"]
    if track_b:
        parts.append(
            '<span class="section-label madder">Track B \u2014 Chaos / Metamorphosis</span>\n'
        )
        for rec in track_b:
            fig_num += 1
            parts.append(_html_rec_card(rec, fig_num, gemini_visuals))

    # Deep Dive
    if model.digest_themes:
        parts.append('<span class="section-label">Deep Dive \u2014 Digest Themes</span>\n')
        for theme in model.digest_themes:
            body_html = _md_links_to_html(_esc(theme.body), INK)
            parts.append(
                '<div class="theme-block">\n'
                f'<div class="theme-heading">{_esc(theme.heading)}</div>\n'
                f'<div class="theme-body">{body_html}</div>\n'
            )
            if theme.citations:
                parts.append(
                    '<div style="font-size:0.82rem;margin-top:4px">'
                    f'Sources: {_citations_html(theme.citations)}</div>\n'
                )
            parts.append('</div>\n')

    # Provenance
    prov = model.provenance
    parts.append('<div class="provenance">\n')
    parts.append(
        f'Scanned <strong>{prov.scanned}</strong> items from '
        f'<strong>{prov.sources}</strong> sources, '
        f'<strong>{prov.relevant}</strong> relevant.'
    )
    if prov.soft_failed:
        parts.append(f'<br>Soft-failed: {_esc(", ".join(prov.soft_failed))}')
    if prov.run_files:
        rf = ", ".join(f'<code class="mono">{_esc(f)}</code>' for f in prov.run_files)
        parts.append(f'<br>Run files: {rf}')
    parts.append('\n</div>\n')

    parts.append('</div>\n</body>\n</html>\n')
    return "".join(parts)


def _html_rec_card(
    rec: Recommendation,
    fig_num: int,
    gemini_visuals: dict[str, bytes],
) -> str:
    """Render a single recommendation as an Instar specimen-plate card."""
    tc = _track_color(rec)
    cls = "rec-card track-b" if rec.track == "B" else "rec-card"
    level_name = LEVEL_NAMES.get(rec.disruption, "")
    s = f'<article class="{cls}">\n'

    # Header: glyph + code + level
    s += '<div class="rec-card-header">\n'
    s += f'<span>{_svg_stage_glyph(rec.disruption, tc)}</span>\n'
    s += f'<span class="rec-code" style="color:{tc}">{_esc(rec.code)}</span>\n'
    s += f'<span class="rec-level">Level {rec.disruption} \u2014 {_esc(level_name)}</span>\n'
    s += '</div>\n'

    # Title + body
    s += f'<div class="rec-title" style="color:{tc}">{_esc(rec.title)}</div>\n'
    s += f'<div class="rec-body">{_esc(rec.body)}</div>\n'

    # Optional Gemini visual
    vis_key = f"{rec.track}{rec.index}"
    if vis_key in gemini_visuals:
        b64 = base64.b64encode(gemini_visuals[vis_key]).decode("ascii")
        s += f'<img class="gemini-visual" src="data:image/png;base64,{b64}" alt="Concept visual for {_esc(rec.title)}">\n'

    # Sliders
    s += '<div class="slider-row">\n'
    for label, val in [
        ("Feasibility", rec.feasibility), ("Evidence", rec.evidence),
        ("Impact", rec.impact), ("Disruption", rec.disruption),
    ]:
        s += (
            f'<div class="slider-item"><span class="slider-label">{label}</span>'
            f'{_svg_slider(val, tc)}</div>\n'
        )
    s += '</div>\n'

    # Why now / Why us
    if rec.why_now:
        s += (
            f'<div class="rec-detail"><strong>Why now:</strong> '
            f'{_citations_html(rec.why_now, tc)}</div>\n'
        )
    if rec.why_us:
        s += (
            f'<div class="rec-detail"><strong>Why us:</strong> '
            f'{_citations_html(rec.why_us, tc)}</div>\n'
        )

    # Track-specific
    if rec.track == "A" and rec.first_step:
        s += (
            f'<div class="rec-detail"><strong>First testable step:</strong> '
            f'{_esc(rec.first_step)}</div>\n'
        )
    if rec.track == "B":
        if rec.metamorphosis:
            s += (
                f'<div class="rec-detail"><strong>Metamorphosis narrative:</strong> '
                f'{_esc(rec.metamorphosis)}</div>\n'
            )
        if rec.kill_criteria:
            s += (
                f'<div class="rec-detail" style="color:{MADDER}">'
                f'<strong>Kill criteria:</strong> {_esc(rec.kill_criteria)}</div>\n'
            )

    s += f'<div class="fig-caption">Fig. {fig_num} \u2014 {_esc(rec.stage)}</div>\n'
    s += '</article>\n'
    return s


def render_html(model: ReportModel) -> str:
    return _render_html_impl(model)


# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL HTML BUILDER (Outlook-safe, Cerberus-based skeleton)
#
# Structure adapted from the vendored Cerberus hybrid template
# (scout/templates/email/cerberus-hybrid.html, MIT license).
# Restyled to the Instar design tokens. Key Cerberus patterns used:
# - MSO namespace declarations and conditional comments
# - CSS reset for cross-client consistency
# - Hybrid width technique (max-width + MSO conditional tables)
# - Table-based single-column layout
# ═══════════════════════════════════════════════════════════════════════════════

_EMAIL_WIDTH = 600

# Cerberus-derived CSS reset (adapted for Instar tokens)
_EMAIL_CSS_RESET = f"""
:root {{ color-scheme: light; }}
html, body {{ margin: 0 auto !important; padding: 0 !important; height: 100% !important; width: 100% !important; }}
* {{ -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%; }}
div[style*="margin: 16px 0"] {{ margin: 0 !important; }}
#MessageViewBody, #MessageWebViewDiv {{ width: 100% !important; }}
table, td {{ mso-table-lspace: 0pt !important; mso-table-rspace: 0pt !important; }}
table {{ border-spacing: 0 !important; border-collapse: collapse !important; table-layout: fixed !important; margin: 0 auto !important; }}
img {{ -ms-interpolation-mode: bicubic; }}
a {{ text-decoration: none; color: {INK}; }}
"""


def _render_email_html(
    model: ReportModel,
    gemini_visuals: dict[str, bytes] | None = None,
) -> str:
    """Build Outlook-safe HTML for the .eml (NO SVG, all inline styles)."""
    gemini_visuals = gemini_visuals or {}
    W = _EMAIL_WIDTH
    p: list[str] = []

    # Head (Cerberus-pattern DOCTYPE + MSO setup)
    p.append(
        '<!DOCTYPE html>\n'
        '<html lang="en" xmlns="http://www.w3.org/1999/xhtml"'
        ' xmlns:v="urn:schemas-microsoft-com:vml"'
        ' xmlns:o="urn:schemas-microsoft-com:office:office">\n'
        '<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width">\n'
        '<meta http-equiv="X-UA-Compatible" content="IE=edge">\n'
        '<meta name="x-apple-disable-message-reformatting">\n'
        '<meta name="format-detection" content="telephone=no,address=no,email=no,date=no,url=no">\n'
        f'<title>{_esc(model.subject_line)}</title>\n'
        '<!--[if gte mso 9]><xml><o:OfficeDocumentSettings>'
        '<o:PixelsPerInch>96</o:PixelsPerInch>'
        '</o:OfficeDocumentSettings></xml><![endif]-->\n'
        '<!--[if mso]><style>* { font-family: sans-serif !important; }</style><![endif]-->\n'
        f'<style>{_EMAIL_CSS_RESET}</style>\n'
        '</head>\n'
    )

    # Body start (Cerberus pattern: body > center > MSO table > container div > MSO inner table)
    p.append(
        f'<body width="100%" style="margin:0;padding:0 !important;'
        f'mso-line-height-rule:exactly;background-color:{PAPER};">\n'
        f'<center role="article" aria-roledescription="email" lang="en"'
        f' style="width:100%;background-color:{PAPER};">\n'
        f'<!--[if mso | IE]><table role="presentation" border="0" cellpadding="0"'
        f' cellspacing="0" width="100%" style="background-color:{PAPER};">'
        '<tr><td><![endif]-->\n'
        f'<div style="max-width:{W}px;margin:0 auto;">\n'
        f'<!--[if mso]><table align="center" role="presentation" cellspacing="0"'
        f' cellpadding="0" border="0" width="{W}"><tr><td><![endif]-->\n'
        '<table role="presentation" cellspacing="0" cellpadding="0" border="0"'
        ' width="100%" style="margin:auto;">\n'
    )

    ef = EMAIL_FONT  # shorthand for inline styles

    # Preheader
    tldr_preview = " | ".join(model.tldr[:3])
    p.append(
        '<tr><td style="font-size:0;line-height:0;max-height:0;overflow:hidden;'
        f'mso-hide:all;" aria-hidden="true">{_esc(tldr_preview)}</td></tr>\n'
    )

    # Subject/header row
    p.append(
        f'<tr><td style="padding:24px 24px 8px;background-color:{PAPER};">'
        f'<h1 style="margin:0;font-family:{ef};font-size:20px;font-weight:300;'
        f'line-height:28px;color:{INK};">{_esc(model.subject_line)}</h1>'
        '</td></tr>\n'
    )

    # TL;DR
    p.append(
        f'<tr><td style="padding:8px 24px 16px;background-color:{PAPER};">'
        f'<p style="margin:0 0 4px;font-family:{ef};font-size:11px;font-weight:600;'
        f'letter-spacing:1.5px;text-transform:uppercase;color:{INK};">TL;DR</p>'
    )
    for bullet in model.tldr:
        p.append(
            f'<p style="margin:0 0 4px;font-family:{ef};font-size:14px;'
            f'line-height:20px;color:{INK};">\u2014 {_esc(bullet)}</p>'
        )
    p.append('</td></tr>\n')

    # Scoreboard
    p.append(
        f'<tr><td style="padding:8px 24px;background-color:{PAPER};">'
        f'<p style="margin:0 0 6px;font-family:{ef};font-size:11px;font-weight:600;'
        f'letter-spacing:1.5px;text-transform:uppercase;color:{INK};">SCOREBOARD</p>'
        '<table role="presentation" cellspacing="0" cellpadding="0" border="0"'
        ' width="100%">\n'
    )
    # Header row
    p.append('<tr>')
    for hdr in ("Code", "Title", "F", "E", "I", "D"):
        p.append(
            f'<td style="padding:4px 6px;font-family:{ef};font-size:10px;'
            f'font-weight:600;letter-spacing:1px;text-transform:uppercase;'
            f'color:{INK};border-bottom:2px solid rgba(31,58,95,0.2);">{hdr}</td>'
        )
    p.append('</tr>\n')
    # Data rows
    for rec in model.recommendations:
        tc = _track_color(rec)
        glyph = EMAIL_STAGE_GLYPHS.get(rec.disruption, "")
        p.append('<tr>')
        p.append(
            f'<td style="padding:5px 6px;font-family:Consolas,monospace;font-size:12px;'
            f'color:{tc};border-bottom:1px solid rgba(31,58,95,0.08);">'
            f'{glyph} {_esc(rec.code)}</td>'
        )
        p.append(
            f'<td style="padding:5px 6px;font-family:{ef};font-size:13px;'
            f'color:{INK};border-bottom:1px solid rgba(31,58,95,0.08);">'
            f'{_esc(rec.title)}</td>'
        )
        for val in (rec.feasibility, rec.evidence, rec.impact, rec.disruption):
            p.append(
                f'<td style="padding:5px 6px;font-family:Consolas,monospace;font-size:12px;'
                f'text-align:center;color:{tc};'
                f'border-bottom:1px solid rgba(31,58,95,0.08);">{val}</td>'
            )
        p.append('</tr>\n')
    p.append('</table></td></tr>\n')

    # Rec cards
    track_a_recs, track_b_recs = (
        [r for r in model.recommendations if r.track == "A"],
        [r for r in model.recommendations if r.track == "B"],
    )
    fig_num = 0
    for track_label, recs, heading_color in [
        ("Track A \u2014 Realistic Moves", track_a_recs, INK),
        ("Track B \u2014 Chaos / Metamorphosis", track_b_recs, MADDER),
    ]:
        if not recs:
            continue
        p.append(
            f'<tr><td style="padding:16px 24px 4px;background-color:{PAPER};">'
            f'<p style="margin:0;font-family:{ef};font-size:11px;font-weight:600;'
            f'letter-spacing:1.5px;text-transform:uppercase;'
            f'color:{heading_color};">{_esc(track_label)}</p>'
            '</td></tr>\n'
        )
        for rec in recs:
            fig_num += 1
            p.append(_email_rec_card(rec, fig_num, ef, gemini_visuals))

    # Deep Dive
    if model.digest_themes:
        p.append(
            f'<tr><td style="padding:16px 24px 4px;background-color:{PAPER};">'
            f'<p style="margin:0;font-family:{ef};font-size:11px;font-weight:600;'
            f'letter-spacing:1.5px;text-transform:uppercase;'
            f'color:{INK};">DEEP DIVE \u2014 DIGEST THEMES</p>'
            '</td></tr>\n'
        )
        for theme in model.digest_themes:
            body_html = _md_links_to_html(_esc(theme.body), INK)
            p.append(
                f'<tr><td style="padding:8px 24px;background-color:{PAPER};'
                f'border-bottom:1px solid rgba(31,58,95,0.08);">'
                f'<p style="margin:0 0 4px;font-family:{ef};font-size:15px;'
                f'font-weight:400;color:{INK};">{_esc(theme.heading)}</p>'
                f'<p style="margin:0;font-family:{ef};font-size:13px;'
                f'line-height:19px;color:{INK};">{body_html}</p>'
            )
            if theme.citations:
                cite_html = _citations_html(theme.citations, INK)
                p.append(
                    f'<p style="margin:4px 0 0;font-family:{ef};font-size:12px;'
                    f'color:rgba(31,58,95,0.6);">Sources: {cite_html}</p>'
                )
            p.append('</td></tr>\n')

    # Provenance
    prov = model.provenance
    prov_text = (
        f'Scanned {prov.scanned} items from {prov.sources} sources, '
        f'{prov.relevant} relevant.'
    )
    if prov.soft_failed:
        prov_text += f' Soft-failed: {", ".join(prov.soft_failed)}.'
    p.append(
        f'<tr><td style="padding:16px 24px;background-color:{PAPER};'
        f'border-top:1px solid rgba(31,58,95,0.2);">'
        f'<p style="margin:0;font-family:{ef};font-size:11px;'
        f'line-height:16px;color:rgba(31,58,95,0.55);">'
        f'{_esc(prov_text)}</p>'
        '</td></tr>\n'
    )

    # Close all wrappers (Cerberus pattern)
    p.append(
        '</table>\n'
        '<!--[if mso]></td></tr></table><![endif]-->\n'
        '</div>\n'
        '<!--[if mso | IE]></td></tr></table><![endif]-->\n'
        '</center>\n</body>\n</html>\n'
    )

    return "".join(p)


def _email_rec_card(
    rec: Recommendation,
    fig_num: int,
    ef: str,
    gemini_visuals: dict[str, bytes],
) -> str:
    """Render a single rec as an Outlook-safe table card (no SVG)."""
    tc = _track_color(rec)
    border_color = "rgba(140,59,46,0.25)" if rec.track == "B" else "rgba(31,58,95,0.18)"
    level_name = LEVEL_NAMES.get(rec.disruption, "")
    glyph = EMAIL_STAGE_GLYPHS.get(rec.disruption, "")

    s = (
        f'<tr><td style="padding:8px 24px;background-color:{PAPER};">'
        '<table role="presentation" cellspacing="0" cellpadding="0" border="0"'
        f' width="100%" style="border:1px solid {border_color};">\n'
    )

    # Header: glyph + code + level
    s += (
        f'<tr><td style="padding:14px 16px 4px;font-family:{ef};font-size:13px;'
        f'color:{tc};">'
        f'<span style="font-size:18px;vertical-align:middle;">{glyph}</span> '
        f'<strong style="font-family:Consolas,monospace;">{_esc(rec.code)}</strong> '
        f'<span style="font-size:12px;opacity:0.7;">'
        f'Level {rec.disruption} \u2014 {_esc(level_name)}</span>'
        '</td></tr>\n'
    )

    # Title
    s += (
        f'<tr><td style="padding:4px 16px 6px;font-family:{ef};font-size:16px;'
        f'font-weight:400;color:{tc};">{_esc(rec.title)}</td></tr>\n'
    )

    # Body
    s += (
        f'<tr><td style="padding:2px 16px 8px;font-family:{ef};font-size:13px;'
        f'line-height:19px;color:{INK};">{_esc(rec.body)}</td></tr>\n'
    )

    # Optional Gemini CID image
    vis_key = f"{rec.track}{rec.index}"
    if vis_key in gemini_visuals:
        s += (
            f'<tr><td style="padding:4px 16px;">'
            f'<img src="cid:gemini-{vis_key}" width="560" style="width:100%;max-width:560px;'
            f'height:auto;border:1px solid rgba(31,58,95,0.1);" alt="Concept visual">'
            '</td></tr>\n'
        )

    # Sliders (table cells, no SVG)
    s += f'<tr><td style="padding:6px 16px;font-family:{ef};font-size:12px;color:{tc};">'
    for label, val in [
        ("F", rec.feasibility), ("E", rec.evidence),
        ("I", rec.impact), ("D", rec.disruption),
    ]:
        s += (
            f'<span style="margin-right:12px;white-space:nowrap;">'
            f'{label}: {_email_slider_cells(val, tc)}</span>'
        )
    s += '</td></tr>\n'

    # Why now / Why us
    if rec.why_now:
        cite = _citations_html(rec.why_now, tc)
        s += (
            f'<tr><td style="padding:3px 16px;font-family:{ef};font-size:12px;'
            f'color:{INK};"><strong>Why now:</strong> {cite}</td></tr>\n'
        )
    if rec.why_us:
        cite = _citations_html(rec.why_us, tc)
        s += (
            f'<tr><td style="padding:3px 16px;font-family:{ef};font-size:12px;'
            f'color:{INK};"><strong>Why us:</strong> {cite}</td></tr>\n'
        )

    # Track-specific
    if rec.track == "A" and rec.first_step:
        s += (
            f'<tr><td style="padding:3px 16px;font-family:{ef};font-size:12px;'
            f'color:{INK};"><strong>First testable step:</strong> '
            f'{_esc(rec.first_step)}</td></tr>\n'
        )
    if rec.track == "B":
        if rec.metamorphosis:
            s += (
                f'<tr><td style="padding:3px 16px;font-family:{ef};font-size:12px;'
                f'color:{INK};"><strong>Metamorphosis:</strong> '
                f'{_esc(rec.metamorphosis)}</td></tr>\n'
            )
        if rec.kill_criteria:
            s += (
                f'<tr><td style="padding:3px 16px;font-family:{ef};font-size:12px;'
                f'color:{MADDER};"><strong>Kill criteria:</strong> '
                f'{_esc(rec.kill_criteria)}</td></tr>\n'
            )

    # Fig caption
    s += (
        f'<tr><td style="padding:6px 16px 12px;font-family:{ef};font-size:11px;'
        f'font-style:italic;color:rgba(31,58,95,0.5);">'
        f'Fig. {fig_num} \u2014 {_esc(rec.stage)}</td></tr>\n'
    )

    s += '</table></td></tr>\n'
    return s


# ═══════════════════════════════════════════════════════════════════════════════
# EML BUILDER (stdlib email.mime)
# ═══════════════════════════════════════════════════════════════════════════════

def _render_eml_impl(
    model: ReportModel,
    gemini_visuals: dict[str, bytes] | None = None,
) -> bytes:
    """Build a valid .eml file. Double-click -> Outlook opens it as a ready-to-send draft."""
    gemini_visuals = gemini_visuals or {}

    email_html = _render_email_html(model, gemini_visuals)
    plain_text = render_markdown(model)

    if gemini_visuals:
        # multipart/related wraps multipart/alternative + CID images
        from email.mime.image import MIMEImage
        outer = MIMEMultipart("related")
        outer["Subject"] = model.subject_line
        outer["From"] = f"AI Chaos Scout <scout@{model.subject_name.lower().replace(' ', '')}.com>"
        outer["To"] = ""
        outer["X-Unsent"] = "1"

        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(plain_text, "plain", "utf-8"))
        alt.attach(MIMEText(email_html, "html", "utf-8"))
        outer.attach(alt)

        for vis_key, img_data in gemini_visuals.items():
            img_part = MIMEImage(img_data, "png")
            img_part.add_header("Content-ID", f"<gemini-{vis_key}>")
            img_part.add_header("Content-Disposition", "inline", filename=f"gemini-{vis_key}.png")
            outer.attach(img_part)

        return outer.as_bytes()

    # Simple multipart/alternative (no images)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = model.subject_line
    msg["From"] = f"AI Chaos Scout <scout@{model.subject_name.lower().replace(' ', '')}.com>"
    msg["To"] = ""
    msg["X-Unsent"] = "1"
    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(email_html, "html", "utf-8"))
    return msg.as_bytes()


def render_eml(model: ReportModel) -> bytes:
    return _render_eml_impl(model)


# ═══════════════════════════════════════════════════════════════════════════════
# OPTIONAL GEMINI INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def _try_gemini_visuals(model: ReportModel) -> dict[str, bytes]:
    """Generate concept visuals via Gemini if GEMINI_API_KEY is set. Returns {} otherwise."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return {}
    try:
        from scout.gemini import generate_concept_visual
    except Exception:
        return {}

    visuals: dict[str, bytes] = {}
    # Top rec per track
    for track in ("A", "B"):
        track_recs = [r for r in model.recommendations if r.track == track]
        if not track_recs:
            continue
        top = track_recs[0]
        prompt = (
            f"Create a concept illustration in the style of a naturalist's field-guide plate: "
            f"warm paper background, dark blue ink line art, geometric and taxonomic. "
            f"The subject is: {top.title}. Description: {top.body}. "
            f"Style: elegant scientific illustration, no text, no labels."
        )
        try:
            img = generate_concept_visual(prompt, api_key)
            if img:
                visuals[f"{top.track}{top.index}"] = img
        except Exception:
            pass

    return visuals


# ═══════════════════════════════════════════════════════════════════════════════
# RENDER ALL + JSON LOADER
# ═══════════════════════════════════════════════════════════════════════════════

def render_all(model: ReportModel, out_dir: str | None = None) -> dict[str, str]:
    """Write all three artifacts; return {'md': path, 'html': path, 'eml': path}."""
    out_dir = out_dir or os.path.join(REPO_ROOT, "reports")
    os.makedirs(out_dir, exist_ok=True)

    gemini_visuals = _try_gemini_visuals(model)

    md_content = render_markdown(model)
    html_content = _render_html_impl(model, gemini_visuals)
    eml_content = _render_eml_impl(model, gemini_visuals)

    date = model.date
    paths: dict[str, str] = {}

    md_path = os.path.join(out_dir, f"chaos-report-{date}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    paths["md"] = md_path

    html_path = os.path.join(out_dir, f"chaos-report-{date}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    paths["html"] = html_path

    eml_path = os.path.join(out_dir, f"chaos-report-{date}.eml")
    with open(eml_path, "wb") as f:
        f.write(eml_content)
    paths["eml"] = eml_path

    return paths


def load_model_from_json(path: str) -> ReportModel:
    """Hydrate a ReportModel from the agent's report.json."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    recs: list[Recommendation] = []
    for r in data.get("recommendations", []):
        recs.append(Recommendation(
            track=r["track"],
            index=r["index"],
            title=r["title"],
            body=r["body"],
            feasibility=r["feasibility"],
            evidence=r["evidence"],
            impact=r["impact"],
            disruption=r["disruption"],
            why_now=[Citation(**c) for c in r.get("why_now", [])],
            why_us=[Citation(**c) for c in r.get("why_us", [])],
            first_step=r.get("first_step", ""),
            metamorphosis=r.get("metamorphosis", ""),
            kill_criteria=r.get("kill_criteria", ""),
        ))

    themes: list[DigestTheme] = []
    for t in data.get("digest_themes", []):
        themes.append(DigestTheme(
            heading=t["heading"],
            body=t["body"],
            citations=[Citation(**c) for c in t.get("citations", [])],
        ))

    prov_data = data.get("provenance", {})
    provenance = Provenance(
        scanned=prov_data.get("scanned", 0),
        sources=prov_data.get("sources", 0),
        relevant=prov_data.get("relevant", 0),
        soft_failed=prov_data.get("soft_failed", []),
        run_files=prov_data.get("run_files", []),
    )

    return ReportModel(
        subject_name=data["subject_name"],
        date=data["date"],
        subject_line=data["subject_line"],
        tldr=data.get("tldr", []),
        recommendations=recs,
        digest_themes=themes,
        provenance=provenance,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> int:
    ap = argparse.ArgumentParser(description="AI Chaos Scout \u2014 Stage 3 render")
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
