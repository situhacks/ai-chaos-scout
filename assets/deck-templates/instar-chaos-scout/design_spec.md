---
brand_id: instar-chaos-scout
kind: brand
summary: AI Chaos Scout "Riso Field-Study" aesthetic — weekly chaos briefings, two-track strategic recommendations, metamorphosis-themed disruption analysis
primary_color: "#2438E0"
---

# Chaos Scout Brand Specification — "Riso Field-Study"

> Identity-only preset. No fixed SVG page roster — pages are composed freely under these constraints. The deck-template encodes the locked "Riso Field-Study" design language from AI Chaos Scout (`docs/design-language.md`): a modern, editorial riso-print study of corporate metamorphosis on soft off-white paper. This replaces the earlier vintage field-guide look (rejected as dated). The `instar-chaos-scout` folder id is kept for path stability.

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | AI Chaos Scout — Riso Field-Study |
| Use Cases | Weekly chaos briefings, strategic recommendation decks, two-track (realistic + metamorphosis) analysis presentations, board-level disruption reports |
| Tone | Analytical and editorial — a modern design-portfolio artifact, not a SaaS dashboard and not a vintage almanac. Confident, spacious, riso-print restraint; two inks doing the work |

## II. Color Scheme

> Locked to the "Riso Field-Study" design language (`docs/design-language.md`). Soft off-white paper ground; a two-ink riso system — cobalt blue and coral — on near-black text. Track A (realistic recs) uses riso cobalt; Track B (chaos/metamorphosis recs) uses riso coral.

| Role | HEX | Purpose |
|---|---|---|
| **Background** | `#F9F7F2` | Soft off-white paper ground (~50% between warm paper and white) |
| **Secondary bg** | `#FFFFFF` | Card background — hairline-ruled plates that lift off the paper |
| **Primary** | `#2438E0` | Riso cobalt — headlines, rules, structure, Track A lineart, links |
| **Accent** | `#EE5340` | Riso coral — Track B accents, margin stripe, metamorphosis highlights |
| **Secondary accent** | `#2438E0` | Riso cobalt (single accent system — no third hue) |
| **Body text** | `#1B1F2A` | Near-black ink — main body text |
| **Secondary text** | `#55596A` | Cool slate — captions, annotations, slider labels |
| **Tertiary text** | `#8A8A93` | Cool gray — footnotes, page numbers, provenance metadata |
| **Border/divider** | `#E3E1DC` | Hairline rules and card borders (neutral) |
| **Success** | `#2438E0` | Riso cobalt — positive indicators, high-feasibility markers |
| **Warning** | `#EE5340` | Riso coral — risk markers, low-feasibility, Track B disruption alerts |

### Design-language tokens (locked)

| Token | HEX | Use |
|---|---|---|
| paper | `#F9F7F2` | Page ground |
| ink | `#1B1F2A` | Body text |
| blue | `#2438E0` | Track A, links, structure, headlines |
| coral | `#EE5340` | Track B accents, margin stripe |
| grid | `#1B1F2A` @ 6% opacity | Drafting-grid background lines |
| grid-line | `#E3E1DC` | Rendered faint rule/connector stroke on paper |

## III. Typography

> PPT-safe stacks only. The Riso Field-Study aesthetic calls for a heavy grotesque-sans headline (bold, editorial), a clean sans body, and monospace for eyebrows, codes, and citations. No serif titles, no Google Fonts or brand-only typefaces.

| Role | Family | Weight |
|---|---|---|
| Title | `"Arial Black", "Helvetica Neue", Arial, sans-serif` | 800 (Heavy) |
| Body | `Arial, Helvetica, sans-serif` | 400 (Regular) |
| Emphasis | `"Arial Black", "Helvetica Neue", Arial, sans-serif` | 700 (Bold) |
| Code | `Consolas, "Courier New", monospace` | 400 (Regular) |

**Per-role font stacks** (CSS `font-family` strings):

- Title: `"Arial Black", "Helvetica Neue", Arial, sans-serif`
- Body: `Arial, Helvetica, sans-serif`
- Emphasis: `"Arial Black", "Helvetica Neue", Arial, sans-serif`
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

No logo lockup. AI Chaos Scout is a repo-as-product; brand identity is carried by the design language (soft paper, two riso inks, layered display type, metamorphosis glyphs) rather than a logo mark. Cover slides use a heavy typographic title treatment with a monospace eyebrow, a blue accent bar, and an oversized layered/overlapping display word set at low opacity behind the title.

## V. Voice & Tone

- Formality: analytical-professional, field-guide register
- Person: third-person analytical ("the subject", "this company") in report body; second-person ("you") only in TL;DR / first-step directives
- Emoji: forbidden in report body (anti-pattern per design language)
- Abbreviations: spell-out-first-use
- Citations: every claim carries inline source links; specimen codes `[A1]`, `[B2]` for recommendations
- Disruption levels rendered as metamorphosis stages: egg, larva, chrysalis, emergence, imago
- Track B carries a scope-of-the-bet realism label (product/feature bet → line-of-business/model bet → bet-the-company) beside its level

## VI. Icon Style

- Preference: geometric lineart (stroke)

> The Riso Field-Study aesthetic uses simplified, "digified" geometric lineart — clean and modern, never photoreal or ornate. The five metamorphosis-stage glyphs (egg, larva, chrysalis, emergence, imago) are the primary iconographic system, rendered as SVG lineart that shifts from riso cobalt (Track A, levels 1–2) to riso coral (Track B, levels 3–5). Supplementary icons (if needed) follow the same thin-stroke style. No glitch/scanline effects.

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
