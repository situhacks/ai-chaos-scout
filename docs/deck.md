# Deck deliverable — one report.json, email OR PPT

The strategic output of AI Chaos Scout is **flexible enough to format into an email OR
a PowerPoint deck** from the same `report.json`. The core pipeline (Stage 3 /
`/chaos-report`) always produces the keyless trio: `.md`, `.html`, `.eml`. The deck
path is an **optional add-on** that converts the same structured data into a branded
presentation.

## Architecture

```
                         ┌─── render_report.py ───▶ .md / .html / .eml  (keyless, always)
report.json ─────────────┤
                         └─── /chaos-deck ────────▶ .pptx               (optional, needs ppt-master)
                               │
                               ├─ storyboard.md (intermediate)
                               └─ assets/deck-templates/instar-chaos-scout/ (brand identity)
```

Both paths consume the **identical** `ReportModel` dataclass from
`scout/render_report.py`. No data is duplicated or reformulated — the deck slides and
the email sections carry the same content, citations, and slider values.

## The Instar deck-template package

Located at `assets/deck-templates/instar-chaos-scout/`, this is a ppt-master-compatible
brand template that encodes our "Instar" design language:

- **Warm-paper ground** (`#f4efe4`) — the naturalist's field-notebook page
- **Specimen-blue ink** (`#1f3a5f`) — text, rules, Track A lineart
- **Madder-red accent** (`#8c3b2e`) — Track B accents, margin warnings
- **Faint graph-paper grid** — 20px pitch, ink at 6% opacity
- **Hairline-ruled specimen-plate cards** — recommendations as catalog plates
- **Metamorphosis-stage glyphs** — egg→larva→chrysalis→emergence→imago for
  disruption levels 1–5, rendered as geometric lineart
- **PPT-safe typography** — Georgia (titles), Arial (body), Consolas (codes);
  every stack ends in a cross-platform pre-installed font

### Package contents

| File | Purpose |
|---|---|
| `design_spec.md` | Brand identity spec (`kind: brand`, sections I–VII) |
| `spec_lock.md` | Machine-readable execution contract (colors, typography, canvas) |
| `cover.svg` | Cover slide template (1280×720) |
| `disruption-ladder.svg` | Metamorphosis strip mapping levels 1–5 |
| `track-a-card.svg` | Track A specimen plate with sliders + citations |
| `track-b-card.svg` | Track B metamorphosis card with kill-criteria |
| `scoreboard.svg` | Recs × sliders matrix |
| `provenance.svg` | Source inventory + grounding note |
| `README.md` | Package documentation |

## Report → slide mapping

| Slide | report.json field(s) |
|---|---|
| Cover | `subject_name`, `date`, `subject_line` |
| TL;DR | `tldr[]` |
| Scoreboard | `recommendations[]` × 4 sliders |
| Disruption Ladder | Disruption levels 1–5 from `recommendations[]` |
| Track A cards (1 per rec) | `recommendations[track="A"]`: title, body, sliders, why_now, why_us, first_step |
| Track B cards (1 per rec) | `recommendations[track="B"]`: title, body, sliders, why_now, why_us, metamorphosis, kill_criteria |
| Digest Themes | `digest_themes[]`: heading, body, citations |
| Provenance | `provenance`: scanned, sources, relevant, soft_failed, run_files |

A typical deck is **10–14 slides**: 1 cover + 1 TL;DR + 1 scoreboard + 1 disruption
ladder + 3–5 Track A cards + 2–3 Track B cards + 1 digest themes + 1 provenance.

## The ppt-master dependency

The deck path requires the **external ppt-master skill**, which is not bundled with
AI Chaos Scout. It is a vendored deck-generation pipeline from the AgentFrame system.

### How to obtain and install

1. Clone the reference system:
   ```
   git clone https://github.com/situhacks/agentframe.git
   ```

2. The ppt-master skill lives at `system/skills/ppt-master/`. Its entry point is
   `SKILL.md` (the full pipeline specification).

3. Point the `/chaos-deck` workflow at the skill by ensuring the agent can resolve
   `${SKILL_DIR}` to the ppt-master directory. In Cursor, this is typically handled
   by loading the skill into the workspace. In Devin, clone agentframe alongside
   ai-chaos-scout.

4. Key scripts used by the deck workflow:
   - `scripts/project_manager.py` — project initialization and source import
   - `scripts/svg_to_pptx.py` — SVG-to-PPTX export (pass `--no-notes`)

### pip dependencies (ppt-master only)

The ppt-master skill requires `python-pptx` and other pip packages listed in its
`requirements.txt`. These are needed **only for the deck path** — the core AI Chaos
Scout pipeline remains stdlib-only Python 3.10+ with zero pip installs.

## Optional: AI cover imagery

If `GEMINI_API_KEY` is set in the environment, ppt-master's `image_gen.py` can generate
an AI cover background image. This is **off by default** — the layout does not depend on
it, and the cover works as a typographic treatment without any generated imagery. Set the
key only if you want the visual stretch; it is not required for a complete deck.

## Graceful degradation

The deck path is optional — the same way Composio is optional for email delivery. The
degradation ladder:

1. **ppt-master installed + `python-pptx` available** → native `.pptx` output
2. **ppt-master installed, `python-pptx` missing** → SVG pages generated but no PPTX export;
   the SVGs can be opened individually or assembled manually
3. **ppt-master absent** → `/chaos-deck` emits the storyboard markdown + a standalone
   HTML deck (browser-presentable, printable) so the run still yields a deck deliverable
4. **Neither `/chaos-deck` nor ppt-master** → the core pipeline still produces
   `.md` / `.html` / `.eml` via `/chaos-report` — the deck path is never a dependency

The keyless core is never compromised. The deck is garnish on top of the report.
