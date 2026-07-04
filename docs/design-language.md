# Design language — "Instar" (binding for both HTML renders)

Operator-set direction, interpreted by the implementer (exact hex/type values are the
renderer's call within this treatment). "Instar" = a developmental stage between insect
molts — the metamorphosis motif is the whole point.

> An insect field-guide study of metamorphosis — the visual register of a naturalist's
> plate, not a SaaS dashboard. Warm paper ground; dark blue drawing ink for text, rules,
> and lineart; a faint architectural/graph-paper grid behind content; shading as
> hatching/stipple, never soft drop-shadows. Thin, modern sans-serif (light weights,
> generous letterspacing on uppercase labels); monospace only for specimen codes and
> citations. Recommendations are specimen plates: hairline-ruled cards with catalog codes
> ([A2], [B1]) and "Fig. N" captions. Track A is annotated in the base specimen-blue ink;
> Track B in a second madder-red ink, like a researcher's margin warnings. **Disruption
> levels 1–5 draw as metamorphosis stages: egg → larva → chrysalis → emergence → imago.**
> Stylized geometric lineart throughout — elegant, taxonomic, never photoreal or gross.
> Anti-patterns: neon/gradient tech aesthetics, dark-mode-first, rounded bubbly cards,
> emoji in the report body.

## Suggested tokens (renderer may refine)

| Token | Value (starting point) | Use |
|---|---|---|
| paper | `#f4efe4` | page ground |
| ink | `#1f3a5f` (specimen blue) | text, rules, Track A lineart |
| madder | `#8c3b2e` (madder red) | Track B accents / margin warnings |
| grid | `#1f3a5f` @ ~6% opacity | graph-paper background |
| sans | `Inter`/system light | body + labels (letterspaced uppercase) |
| mono | `ui-monospace, Menlo` | specimen codes `[A2]`, citations |

## Two renders, one identity

- **Standalone HTML (`.html`):** full treatment — graph-paper background, inline **SVG**
  metamorphosis stage glyphs + slider strips, figure-numbered specimen cards. Self-contained
  single file.
- **Email (`.eml`):** the SAME identity within Outlook's Word-engine limits — paper
  background color, ink text, **table-cell** sliders in track colors (NO SVG), stage glyphs
  as text glyphs or small `cid:`-embedded PNGs. System font stack only
  (`Segoe UI, Helvetica Neue, Arial`). Must degrade gracefully with images off — all
  information survives as text/table color.

## Building the SVG lineart

Prefer generating clean, standalone SVG (hand-authored or via an open SVG skill such as
`jawwadfirdousi/agent-skills/svg-creator`, or editorial-illustration skills like
`caezium/nib`) over pulling a heavy dependency. The five stage glyphs (egg → larva →
chrysalis → emergence → imago) and the 5-cell slider strip are the only required motifs;
keep them geometric and taxonomic, validate the XML, and inline them (no runtime deps).
