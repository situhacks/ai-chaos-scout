# Design language — "Riso Field-Study" (binding for both HTML renders)

Locked direction (Twenty demo, 2026-07-04). Modern design-portfolio treatment, NOT the
earlier vintage/antique field-guide (that was rejected as dated). Keeps the metamorphosis
concept; re-casts the execution as riso-print editorial on warm digital paper.

> A modern riso/editorial study of metamorphosis — the register of a design-school plate,
> not a SaaS dashboard and not an old naturalist's book. Warm **digital** paper ground (not
> yellowed, not stark white) with a faint architectural drafting grid peering through.
> Two riso spot inks: electric cobalt blue and coral. Bold, confident sans-serif headlines
> with **layered / overlapping typography** as a hero motif; monospace only for eyebrows,
> specimen codes, and citations. Recommendations are specimen plates: hairline-ruled cards
> with catalog codes ([A2], [B1]) and "Fig. N" captions. Track A is drawn in cobalt blue;
> Track B in coral. Metamorphosis glyphs are **simplified, "digified" line-art** (less
> detailed than a scientific drawing, more like a clean vector diagram).
> **Disruption levels 1–5 draw as metamorphosis stages: egg → larva → chrysalis →
> emergence → imago.**
> Anti-patterns: **glitch / channel-split / scanline / cyberpunk effects (explicitly cut)**,
> yellowed vintage paper, photoreal/gross bug art, neon gradients, dark-mode-first, rounded
> bubbly cards, emoji in the report body.

Provenance of the lock: Image 3 (the process layout + paper texture, for readability) +
Image 1 (the bold metamorphosis type) + Image 2 (the layered/overlapping text) — with
Image 2's glitch effect removed.

## Tokens (locked)

| Token | Value | Use |
|---|---|---|
| paper | `#F9F7F2` | soft off-white paper ground (~50% between warm paper and white) |
| ink | `#1B1F2A` | near-black body text |
| blue | `#2438E0` (riso cobalt) | Track A, links, structure, headlines |
| coral | `#EE5340` (riso coral) | Track B accents / chaos plays |
| grid | `rgba(27,31,42,0.06)` | drafting-grid background |
| sans | `Inter`/system | headlines (bold 600–700) + body |
| mono | `ui-monospace, Menlo` | eyebrows, specimen codes `[A2]`, citations |

(Renderer constants live in `scout/render_report.py`: `PAPER`, `INK`, `BLUE`, `MADDER`
[coral], `GRID_RGBA`.)

## Two renders, one identity

- **Standalone HTML (`.html`):** full treatment — drafting-grid background, inline **SVG**
  metamorphosis stage glyphs + slider strips, figure-numbered specimen cards. Self-contained
  single file.
- **Email (`.eml`):** the SAME identity within Outlook's Word-engine limits — paper
  background color, ink text, **table-cell** sliders in track colors (NO SVG), stage glyphs
  as text glyphs or small `cid:`-embedded PNGs. System font stack only. Table-based, fixed
  column widths, legend under the scoreboard, real bulleted TL;DR, monospace eyebrow header.
  Must degrade gracefully with images off — all information survives as text/table color.

## Track B realism ladder (see docs/recommendation-rubric.md)

Chaos plays carry a **scope-of-the-bet** label next to the level, so the reader sees how
much of the company each play risks: L3 = product/feature bet (reversible), L4 =
line-of-business / model bet, L5 = bet-the-company. Order Track B ascending (3 → 4 → 5).

## Building the SVG lineart

Prefer generating clean, standalone SVG (hand-authored or via an open SVG skill such as
`jawwadfirdousi/agent-skills/svg-creator`, or editorial-illustration skills like
`caezium/nib`) over pulling a heavy dependency. The five stage glyphs (egg → larva →
chrysalis → emergence → imago) and the 5-cell slider strip are the only required motifs;
keep them simplified/geometric ("digified", not photoreal), validate the XML, and inline
them (no runtime deps). Draw Track A glyphs in cobalt, Track B glyphs in coral.
