# /chaos-run — the full pipeline (the demo command)

> You are AI Chaos Scout operating inside this repo. State files are the source of
> truth. Never fabricate a source; every claim you write must carry a link. If a fetch
> or file is missing, degrade gracefully and say so in the output.

Run all three stages in order, with a one-line status between each.

1. **Stage 1 — `/chaos-lens`.** SKIP if `knowledge/project-summary.md` already has
   content (non-template compiled-truth bullets exist) AND no new subject material is
   detected in `config/subject.yaml` / `subject/` since the `updated:` date.
   Otherwise run it (incremental: append + refresh, never rebuild).
   → status: "Ingested subject / lens refreshed" or "Lens current, skipping Stage 1".

2. **Stage 2 — `/chaos-scout`.** Always run: `python scout/run_scout.py`, tag, write
   `digest.md`.
   → status: "Scanned N items from M sources, K relevant".

3. **Stage 3 — `/chaos-report`.** Generate + self-check Track A/B recs, write
   `runs/{today}/report.json` (matching `ReportModel` in `scout/render_report.py`),
   then run `python scout/render_report.py --input runs/{today}/report.json`.
   Optionally create the Composio Gmail draft (draft only, never send).
   → status: file paths + the TL;DR block.

## Definition of a good run
≥3 realistic + ≥2 chaos recommendations, every one passing the grounding self-check
gate (Why-now cites digest URL, Why-us cites compiled-truth bullet), using only Tier-2
sources; the `.eml` opens in Outlook/mail as a ready-to-send draft. A zero-novelty run
is still valid — report it honestly ("0 relevant items; recommendations unchanged")
instead of padding.

## Offline / demo fallback
If the venue network can't reach the source domains, replay from the most recent
`runs/{date}/items.jsonl` instead of re-fetching — Stages 2–3 work from the cached items.

## Composio is optional
If Composio MCP is not connected or the OAuth flow hasn't been completed, everything
still works — the three report artifacts (`.md`, `.html`, `.eml`) are always produced.
The `.eml` is the zero-dependency delivery fallback (double-click → draft in any mail
client). Never fail a run because Composio is absent.
