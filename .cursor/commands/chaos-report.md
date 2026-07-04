# /chaos-report — Stage 3: the recommendation engine

> You are AI Chaos Scout operating inside this repo. State files are the source of
> truth. Never fabricate a source; every claim you write must carry a link. If a fetch
> or file is missing, degrade gracefully and say so in the output.

Cross this run's digest × the compiled truth into grounded, two-track recommendations.

## Steps

1. **Preconditions:** a fresh `runs/{today}/digest.md` exists AND
   `knowledge/project-summary.md`'s `updated:` ≥ its newest timeline entry date (header
   not stale). If either fails, run the missing stage first (`/chaos-scout` or
   `/chaos-lens`).

2. **Generate recommendations** per `docs/recommendation-rubric.md`:
   - **Track A — Realistic (3–5):** low-lift, testable-this-quarter moves that follow
     from a current trend and the subject's current shape.
   - **Track B — Chaos / Metamorphosis (2–3):** transformational plays responding to a
     named market disruption. Chaos with purpose, never randomness.
   - Score **four sliders 1–5** each with a one-line justification: Feasibility,
     Evidence strength, Business impact, Disruption level. Do NOT average them.
   - Disruption doubles as the track separator: levels 1–2 → Track A, 3–5 → Track B.
   - Track A recs include a **First testable step** (≤2-week experiment). Track B recs
     include a **Metamorphosis narrative + kill criteria** (what observable result
     would falsify the idea).

3. **Self-check pass BEFORE rendering** (the grounding gate): for every rec, confirm:
   - **Why now** resolves to ≥1 real item in `runs/{today}/digest.md` (link to the
     original source URL, not the digest file path), and
   - **Why us** resolves to ≥1 compiled-truth bullet in `knowledge/project-summary.md`
     (the bullet must currently exist in the header, not only in a timeline entry).
   Delete any rec that fails either. If Track A falls below 3 or Track B falls below 2,
   generate grounded replacements — never ship an ungrounded rec to hit a count.

4. **Render:** write the structured report to `runs/{today}/report.json` matching the
   `ReportModel` dataclasses in `scout/render_report.py`:
   ```
   {subject_name, date, subject_line, tldr[3], recommendations[], digest_themes[], provenance}
   ```
   Each recommendation includes: `track`, `index`, `title`, `body`, `feasibility`,
   `evidence`, `impact`, `disruption`, `why_now[]` (Citation objects: `{label, url}`),
   `why_us[]` (Citation objects), `first_step` (Track A) or `metamorphosis` +
   `kill_criteria` (Track B). See `AGENTS.md` § Stage 3 for the full JSON shape.

   Then run: `python scout/render_report.py --input runs/{today}/report.json`
   → produces `reports/chaos-report-{today}.md` + `.html` + `.eml`.

5. **(Optional) Composio delivery:** if Composio MCP is connected, create a Gmail
   **draft** from the Outlook-safe email HTML:
   - Action: `GMAIL_CREATE_EMAIL_DRAFT`
   - Params: `is_html: true`, `subject`: the `subject_line` from report.json,
     `body`: contents of `reports/chaos-report-{today}.html`
   - **Draft only — NEVER call `GMAIL_SEND_DRAFT`.** The human reviews and sends.
   - If Composio is not connected, skip silently. The `.eml` is the keyless fallback
     (double-click → opens as a draft in any mail client).

6. **Present the operator** the TL;DR block and the three report file paths.

## The report contains (all formats)
TL;DR (≤3 bullets: the week's defining trend for THIS company, top realistic move, top
chaos play) · Scoreboard (one row per rec, 4 slider values) · Track A blocks · Track B
blocks (incl. kill criteria) · Deep dive (digest themes, every claim linked) ·
Provenance (N items / M sources / K relevant, what soft-failed, run-file links).
