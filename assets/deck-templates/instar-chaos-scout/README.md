# Chaos Scout — Deck Template Package ("Riso Field-Study")

A ppt-master-compatible deck-template package that encodes the AI Chaos Scout locked
"Riso Field-Study" design language for PowerPoint deck generation from `report.json`.
(The folder id `instar-chaos-scout` is retained for path stability; the earlier vintage
"Instar" look was rejected as dated and has been replaced.)

## What this is

A **brand-kind** template package (identity + signature layout SVGs, no fixed page
roster) that the external ppt-master skill consumes to produce branded decks. The
package encodes: soft off-white paper ground, a two-ink riso system (cobalt blue +
coral), a faint drafting grid, hairline-ruled plate cards, heavy grotesque-sans
headlines with layered/overlapping display type, monospace eyebrows/citations, Track
A/B color separation, and simplified metamorphosis-stage glyphs for disruption levels
1–5 (blue at levels 1–2 shifting to coral at 3–5).

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
| bg | `#F9F7F2` | Soft off-white paper ground |
| secondary_bg | `#FFFFFF` | Card backgrounds (plates) |
| primary | `#2438E0` | Riso cobalt (headlines, rules, structure, Track A) |
| accent | `#EE5340` | Riso coral (Track B, warnings) |
| text | `#1B1F2A` | Body text |
| grid | `#1B1F2A` @ 6% | Drafting-grid lines |

### Typography (PPT-safe)
| Role | Stack |
|---|---|
| Title | `"Arial Black", "Helvetica Neue", Arial, sans-serif` |
| Body | `Arial, Helvetica, sans-serif` |
| Code | `Consolas, "Courier New", monospace` |

All SVGs use 1280×720 viewBox (PPT 16:9). All fonts end in cross-platform pre-installed
fallbacks — no Google Fonts or brand-only typefaces.
