---
brand_id: instar-chaos-scout
kind: brand
summary: AI Chaos Scout "Instar" field-guide aesthetic — weekly chaos briefings, two-track strategic recommendations, metamorphosis-themed disruption analysis
primary_color: "#1f3a5f"
---

# Instar Chaos Scout Brand Specification

> Identity-only preset. No fixed SVG page roster — pages are composed freely under these constraints. The deck-template encodes the "Instar" design language from AI Chaos Scout: a naturalist's field-guide study of corporate metamorphosis.

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | AI Chaos Scout — Instar |
| Use Cases | Weekly chaos briefings, strategic recommendation decks, two-track (realistic + metamorphosis) analysis presentations, board-level disruption reports |
| Tone | Analytical, taxonomic, field-guide authority — the register of a naturalist's plate, not a SaaS dashboard. Warm and deliberate, never flashy or corporate-generic |

## II. Color Scheme

> Derived from the Instar design language (`docs/design-language.md`). Warm-paper ground with specimen-blue ink and madder-red accent. Track A (realistic recs) uses the base specimen-blue; Track B (chaos/metamorphosis recs) uses madder-red.

| Role | HEX | Purpose |
|---|---|---|
| **Background** | `#f4efe4` | Warm paper ground — the naturalist's field-notebook page |
| **Secondary bg** | `#ebe5d8` | Card background — hairline-ruled specimen plates, slightly darker than page |
| **Primary** | `#1f3a5f` | Specimen blue — titles, rules, Track A lineart and text |
| **Accent** | `#8c3b2e` | Madder red — Track B accents, margin warnings, metamorphosis highlights |
| **Secondary accent** | `#5a7a3a` | Specimen green — success states, positive indicators, emergence glyphs |
| **Body text** | `#2b2b2b` | Near-black ink — main body text on warm paper |
| **Secondary text** | `#5c5c5c` | Faded ink — captions, annotations, slider labels |
| **Tertiary text** | `#8a8578` | Ghost ink — footnotes, page numbers, provenance metadata |
| **Border/divider** | `#1f3a5f` | Specimen blue at 25% opacity — hairline rules, card borders, graph-paper grid lines |
| **Success** | `#5a7a3a` | Specimen green — positive indicators, high-feasibility markers |
| **Warning** | `#8c3b2e` | Madder red — risk markers, low-feasibility, Track B disruption alerts |

### Design-language tokens (supplementary)

| Token | HEX | Use |
|---|---|---|
| paper | `#f4efe4` | Page ground |
| ink | `#1f3a5f` | Text, rules, Track A lineart |
| madder | `#8c3b2e` | Track B accents, margin warnings |
| grid | `#1f3a5f` @ 6% opacity | Graph-paper background lines |
| grid-line | `#d3cfc6` | Rendered grid stroke (ink at 6% on paper) |

## III. Typography

> PPT-safe stacks only. The Instar aesthetic calls for a serif title (taxonomic authority), clean sans body (legible field notes), and monospace for specimen codes and citations. No Google Fonts or brand-only typefaces.

| Role | Family | Weight |
|---|---|---|
| Title | `Georgia, "Times New Roman", serif` | 700 (Bold) |
| Body | `Arial, Helvetica, sans-serif` | 400 (Regular) |
| Emphasis | `Georgia, "Times New Roman", serif` | 600 (SemiBold) / Italic |
| Code | `Consolas, "Courier New", monospace` | 400 (Regular) |

**Per-role font stacks** (CSS `font-family` strings):

- Title: `Georgia, "Times New Roman", serif`
- Body: `Arial, Helvetica, sans-serif`
- Emphasis: `Georgia, "Times New Roman", serif`
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline (unitless px):** Body font size = 24 (balanced/business delivery purpose).

| Purpose | Ratio | Size @ body=24 | Weight |
|---|---|---|---|
| Cover title | 3x | 72 | Bold |
| Page title | 1.75x | 42 | Bold |
| Subtitle | 1.33x | 32 | SemiBold |
| **Body** | **1x** | **24** | Regular |
| Annotation/caption | 0.75x | 18 | Regular |
| Footnote/page number | 0.58x | 14 | Regular |
| Specimen code | 1x | 24 | Monospace Regular |

## IV. Logo

No logo lockup. AI Chaos Scout is a repo-as-product; brand identity is carried by the design language (warm paper, specimen-blue ink, metamorphosis glyphs) rather than a logo mark. Cover slides use a typographic title treatment in the specimen-blue ink with a hairline rule.

## V. Voice & Tone

- Formality: analytical-professional, field-guide register
- Person: third-person analytical ("the subject", "this company") in report body; second-person ("you") only in TL;DR / first-step directives
- Emoji: forbidden in report body (anti-pattern per design language)
- Abbreviations: spell-out-first-use
- Citations: every claim carries inline source links; specimen codes `[A1]`, `[B2]` for recommendations
- Disruption levels rendered as metamorphosis stages: egg, larva, chrysalis, emergence, imago

## VI. Icon Style

- Preference: geometric lineart (stroke)

> The Instar aesthetic uses stylized geometric lineart throughout — elegant, taxonomic, never photoreal. The five metamorphosis-stage glyphs (egg, larva, chrysalis, emergence, imago) are the primary iconographic system, rendered as clean SVG lineart in specimen-blue (Track A) or madder-red (Track B). Supplementary icons (if needed) should follow a thin-stroke style consistent with the field-guide register.

## VII. Slide Mapping (report.json to deck)

The deck is parameterized by `report.json` (the `ReportModel` from `scout/render_report.py`). The following mapping defines the section-to-slide roster:

| Slide | Source field(s) | Layout |
|---|---|---|
| Cover | `subject_name`, `date`, `subject_line` | Full-bleed warm paper, typographic title, hairline rules |
| TL;DR | `tldr[]` (3 bullets) | Three-line specimen plate |
| Scoreboard | `recommendations[]` (all recs x 4 sliders) | Matrix grid — recs as rows, slider strips as columns |
| Disruption Ladder | Disruption levels 1-5 from `recommendations[]` | Horizontal metamorphosis strip: egg-larva-chrysalis-emergence-imago |
| Track A Card (per rec) | `recommendations[track=A]`: title, body, sliders, why_now, why_us, first_step | Specimen plate with hairline-ruled card, slider strip, citation block |
| Track B Card (per rec) | `recommendations[track=B]`: title, body, sliders, why_now, why_us, metamorphosis, kill_criteria | Metamorphosis-play card with madder-red accent, kill-criteria callout |
| Digest Themes | `digest_themes[]` | One card per theme, linked citations |
| Provenance | `provenance`: scanned, sources, relevant, soft_failed, run_files | Metadata plate with source inventory and grounding note |
