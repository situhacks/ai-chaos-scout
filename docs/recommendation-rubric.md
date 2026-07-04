# Recommendation rubric — two tracks, four sliders, one grounding rule

Every `/chaos-report` run produces both tracks. They share the rubric; they differ on
the disruption slider and the narrative obligation.

## The two tracks

- **Track A — Realistic (3–5 recs):** corporate-friendly, low-lift, testable-this-quarter
  moves — features, integrations, process changes, positioning shifts that follow from a
  current trend and the subject's current shape.
- **Track B — Chaos / Metamorphosis (2–3 recs):** transformational plays — what if the
  subject drastically revamped a product, its approach, or itself because something in the
  market just made the old shape questionable. **Chaos is not randomness:** a chaos rec
  that can't name the disruption it responds to doesn't ship.

## Disruption levels (the chaos meter → metamorphosis stages)

The level is also a **realism ladder** — how much of the company each play actually
bets. Most chaos should be *product/feature-scoped and reversible*; only rarely is a
play worth betting the whole company on.

| Level | Meaning | Scope of the bet | Track | Stage glyph |
|---|---|---|---|---|
| 1 | Incremental — tune an existing feature/process | tweak an existing surface | A | egg |
| 2 | Adjacent — new feature/channel on the current product | feature-level bet | A | larva |
| 3 | New line — a distinct product/feature the current org could ship | product/feature bet — reversible | B | chrysalis |
| 4 | Model shift — changed business model, pricing, or GTM | line-of-business / model bet | B | emergence |
| 5 | Metamorphosis — identity-level pivot; a different animal emerges | bet-the-company | B | imago |

## Track B composition rule (levels of realism)

Chaos is not uniformly bet-the-company. Every Track B set must:

- **Span at least two scope tiers** — never three plays all at Level 5.
- **Include at least one product/feature-level (Level 3) play** — a bold-but-reversible
  bet the team could ship without a re-org, so the reader has a realistic-chaos option.
- **Cap bet-the-company (Level 5) plays at one**, and only when the grounding signal is
  strong enough to justify an identity-level pivot. If the signal isn't there, that play
  drops to Level 4 or is cut.

Order Track B by ascending scope (Level 3 → 4 → 5) so the realism ladder is legible.

## The four sliders (score every rec 1–5, one-line justification each)

1. **Feasibility / effort** — buildable with the subject's current team/stack/constraints
   (5 = a sprint; 1 = a re-org).
2. **Evidence strength** — how well-sourced the underlying trend is: number of independent
   scout signals, source quality, recency (5 = multiple independent Tier-2 signals; 1 = a
   single opinion post).
3. **Business impact** — expected upside if it works (5 = changes the company's trajectory;
   1 = nice-to-have).
4. **Disruption level** — the chaos meter above; doubles as the track separator.

**Do not average the four into one score** — the *shape* of the four values is the
information (a 5-impact / 1-feasibility rec is a strategy conversation, not a backlog item).

## The grounding rule (mechanical, enforced by checklist)

Every recommendation must contain, inline:
- **Why now** — citation(s) to ≥1 scout item from this run's `digest.md` (original source URL).
- **Why us** — citation(s) to ≥1 compiled-truth fact from `knowledge/project-summary.md`.

A rec missing either is rejected in the self-check pass before rendering — no exceptions,
including chaos recs.

## Per-recommendation shape

```markdown
### [A2] {Title}
**Level {n} — {level name}** · Feasibility {n}/5 · Evidence {n}/5 · Impact {n}/5 · Disruption {n}/5

{2–3 sentences: what it is.}

**Why now:** {trend claim} ([source](url), [source](url))
**Why us:** {subject fact} (project-summary: {header bullet ref})
**First testable step:** {one concrete ≤2-week experiment}          ← Track A only
**Metamorphosis narrative + kill criteria:** {before/after story,   ← Track B only
  and the observable result that would kill this idea}
```

Track B's kill-criteria line is what keeps chaos honest: intentional chaos includes
knowing what would falsify it.
