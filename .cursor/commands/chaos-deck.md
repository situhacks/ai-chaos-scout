# /chaos-deck — Stage 3+: PowerPoint deck from report.json

> You are AI Chaos Scout operating inside this repo. State files are the source of
> truth. Never fabricate a source; every claim you write must carry a link. If a fetch
> or file is missing, degrade gracefully and say so in the output.

Transform a completed `report.json` into a branded PowerPoint deck using the Instar
deck-template package and the external ppt-master skill. This is an **optional add-on**
to the core pipeline — the keyless md/html/eml deliverables are always produced first
by `/chaos-report`. The deck path requires the external ppt-master skill.

## Prerequisites

- A completed `runs/{date}/report.json` from a `/chaos-report` run.
- The external **ppt-master** skill installed (from `situhacks/agentframe` at
  `system/skills/ppt-master/`, or upstream). If absent, this command degrades to
  emitting the storyboard markdown + a standalone HTML deck.

## Steps

### 1. Locate and validate report.json

Find the most recent `runs/{date}/report.json`. Validate it contains the full
`ReportModel` shape: `subject_name`, `date`, `subject_line`, `tldr[]`,
`recommendations[]` (each with `track`, `index`, `title`, `body`, four sliders,
`why_now[]`, `why_us[]`, and track-specific fields), `digest_themes[]`, `provenance`.

If no `report.json` exists, tell the user to run `/chaos-report` first and stop.

### 2. Build the ppt-master storyboard markdown

Transform `report.json` into a ppt-master source/storyboard markdown document
(`runs/{date}/deck-storyboard.md`). Map the ReportModel to slides:

| Slide | Source | Content |
|---|---|---|
| **Cover** | `subject_name`, `date`, `subject_line` | Typographic title on warm paper, metamorphosis strip |
| **TL;DR** | `tldr[]` | Three-bullet summary: defining trend, top realistic, top chaos |
| **Scoreboard** | `recommendations[]` × sliders | Matrix: all recs as rows, 4 slider strips as columns |
| **Disruption Ladder** | Disruption levels from recs | Metamorphosis stages egg→larva→chrysalis→emergence→imago |
| **Track A cards** (one per rec) | `recommendations[track="A"]` | Specimen plate: title, body, why_now/why_us citations, first_step, slider strip |
| **Track B cards** (one per rec) | `recommendations[track="B"]` | Metamorphosis plate: title, body, why_now/why_us citations, metamorphosis narrative, kill_criteria callout |
| **Digest themes** | `digest_themes[]` | One section per theme, linked citations preserved |
| **Provenance** | `provenance` | Source inventory (scanned/sources/relevant), soft-failed list, run-file paths, grounding note |

**Grounding rule carries into the deck:** every recommendation slide MUST display its
Why-now and Why-us citations inline. A recommendation missing either is rejected — the
same self-check pass applies to the deck as to the email.

### 3. Run the ppt-master pipeline (if available)

Check if the ppt-master skill is available (look for its `SKILL.md`). If found:

a. **Initialize a project** in a working directory:
   ```
   python3 ${SKILL_DIR}/scripts/project_manager.py init chaos-deck-{date} --format ppt169
   ```

b. **Import the storyboard** as source content:
   ```
   python3 ${SKILL_DIR}/scripts/project_manager.py import-sources <project_path> runs/{date}/deck-storyboard.md --move
   ```
   (Copy the storyboard first — the original stays in `runs/` as source of truth.)

c. **Hand the deck-template package** at Step 3:
   Pass `assets/deck-templates/instar-chaos-scout/` as the brand template path.
   The Strategist locks our identity segment (colors, typography, voice).

d. **Pre-answer Step 4 confirmations** from our locked tokens:
   - Canvas: PPT 16:9 (1280×720)
   - Mode: `briefing`
   - Visual style: `custom` (Instar field-guide aesthetic per `spec_lock.md`)
   - Colors: from `spec_lock.md` — bg `#f4efe4`, primary `#1f3a5f`, accent `#8c3b2e`
   - Typography: Georgia serif titles, Arial sans body, Consolas monospace codes
   - Delivery purpose: `balanced` (body baseline 24px)
   - Content strategy: stay close to report.json structure

e. **Execute SVG generation** per ppt-master's pipeline (Steps 5–7).
   The signature SVGs in the template package serve as layout references.

f. **Export to PPTX:**
   ```
   python3 ${SKILL_DIR}/scripts/svg_to_pptx.py --no-notes <project_path>
   ```
   Copy the output to `reports/chaos-report-{date}.pptx`.

### 4. Degrade gracefully if ppt-master is absent

If the ppt-master skill is not installed:

a. **Emit the storyboard markdown** to `reports/chaos-report-{date}-deck.md`.
   This is a complete slide-by-slide narrative that can be manually pasted into
   any presentation tool.

b. **Generate a standalone HTML deck** to `reports/chaos-report-{date}-deck.html`.
   A single self-contained HTML file using the Instar design language (warm paper,
   graph-paper grid, specimen plates, metamorphosis glyphs). This is a functional
   deck that can be presented in a browser or printed.

c. Tell the user:
   > ppt-master is not installed. The storyboard markdown and standalone HTML deck
   > have been saved. To generate a native .pptx, install the ppt-master skill from
   > `situhacks/agentframe` (see `system/skills/ppt-master/SKILL.md`) and re-run
   > `/chaos-deck`.

### 5. Present the operator

Show the output file paths and a summary:
- The deck file (`.pptx` if ppt-master ran, otherwise `.html` + `.md`)
- Number of slides generated
- The report→slide mapping used

## Notes

- **ppt-master is EXTERNAL.** It is not bundled with AI Chaos Scout. Install it from
  `situhacks/agentframe` (`system/skills/ppt-master/`) or the upstream repo. The deck
  path is an optional layer — like Composio, it adds capability without changing the
  core.
- **Optional AI cover imagery:** if `GEMINI_API_KEY` is set, ppt-master's
  `image_gen.py` can generate a cover background. Off by default; layout does not
  depend on it.
- **The grounding rule applies to every slide.** Citation codes (`[A1]`, `[B2]`) and
  source URLs must survive the report→deck transformation intact.
- **Subject-agnostic.** The template is parameterized by `report.json` — it works for
  any target company, not just the demo subject.
