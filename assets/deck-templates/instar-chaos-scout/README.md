# Instar Chaos Scout — Deck Template Package

A ppt-master-compatible deck-template package that encodes the AI Chaos Scout "Instar"
design language for PowerPoint deck generation from `report.json`.

## What this is

A **brand-kind** template package (identity + signature layout SVGs, no fixed page
roster) that the external ppt-master skill consumes to produce branded decks. The
package encodes: warm-paper ground, specimen-blue ink, faint graph-paper grid,
hairline-ruled specimen-plate cards, Track A/B color separation, monospace citations,
and metamorphosis-stage glyphs for disruption levels 1–5.

## Package contents

```
assets/deck-templates/instar-chaos-scout/
├── design_spec.md          # Brand identity spec (kind: brand, §I–VII)
├── spec_lock.md            # Machine-readable execution contract
├── cover.svg               # Cover slide layout (1280×720)
├── disruption-ladder.svg   # Metamorphosis strip: egg→larva→chrysalis→emergence→imago
├── track-a-card.svg        # Track A specimen plate with sliders + citations
├── track-b-card.svg        # Track B metamorphosis card with kill-criteria
├── scoreboard.svg          # Recs × sliders matrix
├── provenance.svg          # Source inventory + grounding note
└── README.md               # This file
```

## How ppt-master consumes this

1. At **Step 3** of the ppt-master pipeline, hand the Strategist this directory path:
   `assets/deck-templates/instar-chaos-scout/`
2. The Strategist reads `design_spec.md` (frontmatter `kind: brand`) and locks the
   identity segment (colors, typography, voice, icon style).
3. At **Step 4** (Eight Confirmations), the locked color/type tokens from `spec_lock.md`
   pre-answer the palette and typography confirmations.
4. The **Executor** inherits the signature SVG layouts (cover, disruption-ladder,
   track-a-card, track-b-card, scoreboard, provenance) as starting templates for the
   corresponding slides, adapting content from `report.json`.

## Section → slide mapping

| Slide | SVG template | report.json source |
|---|---|---|
| Cover | `cover.svg` | `subject_name`, `date`, `subject_line` |
| TL;DR | (free layout) | `tldr[]` |
| Scoreboard | `scoreboard.svg` | All `recommendations[]` × 4 sliders |
| Disruption Ladder | `disruption-ladder.svg` | Disruption levels 1–5 |
| Track A cards (1 per rec) | `track-a-card.svg` | `recommendations[track=A]` |
| Track B cards (1 per rec) | `track-b-card.svg` | `recommendations[track=B]` |
| Digest themes | (free layout) | `digest_themes[]` |
| Provenance | `provenance.svg` | `provenance` |

## Design tokens (locked in spec_lock.md)

### Colors
| Token | HEX | Use |
|---|---|---|
| bg | `#f4efe4` | Warm paper ground |
| secondary_bg | `#ebe5d8` | Card backgrounds |
| primary | `#1f3a5f` | Specimen blue (titles, rules, Track A) |
| accent | `#8c3b2e` | Madder red (Track B, warnings) |
| text | `#2b2b2b` | Body text |
| grid | `#d3cfc6` | Graph-paper grid lines |

### Typography (PPT-safe)
| Role | Stack |
|---|---|
| Title | `Georgia, "Times New Roman", serif` |
| Body | `Arial, Helvetica, sans-serif` |
| Code | `Consolas, "Courier New", monospace` |

All SVGs use 1280×720 viewBox (PPT 16:9). All fonts end in cross-platform pre-installed
fallbacks — no Google Fonts or brand-only typefaces.
