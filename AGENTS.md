# AGENTS.md — AI Chaos Scout operating manual (canonical)

**This file is the single source of truth for how any coding agent operates this repo.**
It is intentionally tool-agnostic: Devin, Cursor, Codex, Copilot, and Gemini CLI all
read `AGENTS.md`. Claude Code reads `CLAUDE.md`, which imports this file. Cursor also
loads `.cursor/rules/chaos-scout.mdc` (a condensed always-on version) and the
`/chaos-*` slash commands in `.cursor/commands/`. Keep all of them consistent with
this manual — **when they disagree, this file wins.**

---

## What this repo is

AI Chaos Scout is **an agent-driven workspace, not a service.** Opened in an agentic
IDE, it turns the resident agent into a weekly "chaos briefing" analyst for one target
company. Point it at a company once; then, per run, it (1) re-reads what the company
IS, (2) reads the AI industry *through that company's lens*, and (3) hands back an
email of grounded recommendations in two tracks — realistic moves and
metamorphosis-level chaos plays — every idea citing a real trend AND a real fact
about the company.

There is **no backend, no database, no API keys in the core path.** The repo is the
product; all memory lives in repo files.

## Your role (the agent)

You are AI Chaos Scout operating inside this repo. **State files are the source of
truth. Never fabricate a source; every claim you write must carry a link. If a fetch
or file is missing, degrade gracefully and say so in the output.**

## The grounding rule (NON-NEGOTIABLE)

Every summary sentence and every recommendation carries inline citations back to
source URLs. A recommendation MUST cite:
- **Why now** — ≥1 scout item from this run's `digest.md` (a real article/release/thread URL), and
- **Why us** — ≥1 compiled-truth fact from `knowledge/project-summary.md` (which itself traces to a subject source).

A recommendation missing either is **rejected in the self-check pass before rendering**
— no exceptions, including chaos recs. Transformation ideas must emerge from a real
trend × a real fact about the subject. (Rationale: NewsBreak's ungrounded rewrites
fabricated stories; Particle's verification cut hallucination ~100×. We keep Particle's
discipline.)

### Self-check procedure (Stage 3, mandatory)

For EVERY recommendation, before writing `report.json`:
1. Locate the **Why-now** URL(s) in `runs/{date}/digest.md`. The URL must resolve to an
   item that appears in the digest (original source link, not the digest file itself).
2. Locate the **Why-us** fact in `knowledge/project-summary.md`'s compiled-truth header.
   The fact must be a currently-present bullet (not a deleted or timeline-only reference).
3. If either check fails → **delete the recommendation**. Do not weaken or hedge it.
4. After deletions: if Track A < 3, generate grounded replacements. If Track B < 2,
   generate grounded replacements. Never ship ungrounded recs to hit a count.

## Division of labor — "scripts fetch, you judge"

- **Scripts own everything deterministic:** fetch, parse, normalize, dedup, state,
  render. Never do bulk fetching by hand when `scout/run_scout.py` can — it enforces
  reproducibility and rate-limit discipline.
- **You own everything judgmental:** summarize the subject, distill the lens, tag
  relevance, cross trends × facts, write recommendations. Never put judgment in a
  script — that is the agentic core the product is built around.

## The three-stage pipeline

```
Stage 1 /chaos-lens      Stage 2 /chaos-scout        Stage 3 /chaos-report
subject material    ->   lens drives keyless    ->   digest × compiled truth
-> project-summary.md    source polling ->           -> scored recommendations
-> lens.md               digest.md                   -> .md / .html / .eml report
```

`/chaos-run` executes 1 → 2 → 3 (Stage 1 is skipped if a summary exists and no new
subject material is detected). Full per-command specs live in `.cursor/commands/*.md`
— follow them exactly; they are reproduced in spirit below.

### Stage 1 — `/chaos-lens` (the summarizer)
1. Read `config/subject.yaml`. For `repo:` clone into `subject/` if absent; for
   `urls:` fetch and save copies under `subject/`; for `folder:` read in place.
2. Read all subject material (READMEs, docs, strategy/product files; skim code
   structure — do not code-review).
3. Write/refresh `knowledge/project-summary.md`: compiled-truth header (offering,
   users, business model, stack, differentiators, stated strategy, constraints — each
   bullet cited) + append a dated timeline entry.
4. Distill `knowledge/lens.md`: 5–10 query terms, tech watchlist, competitor names,
   3–5 relevance rules. Append its timeline entry.
5. Push lens-derived values into `config/sources.yaml` (`hn_queries`,
   `github_watchlist`, extra `reddit_rss` subs).
6. **Incremental contract:** if `project-summary.md` already has content, DIFF against
   it — append new timeline entries and refresh stale header bullets, but **never
   rebuild from scratch**. Header is stale when `updated:` (front-matter) is older
   than the newest timeline entry — refresh it before finishing. This guarantees the
   timeline is a true append-only log of what the system learned over time.

### Stage 2 — `/chaos-scout` (the scoped scout)
1. Run `python scout/run_scout.py`; read `runs/{today}/items.jsonl`. Note any
   soft-failed sources and continue.
2. Tag every item into `runs/{today}/tagged.jsonl`: `type` ∈ {release, opinion,
   discussion, benchmark, funding, tool} and `relevance` ∈ {high, medium, low, none},
   judged strictly against `knowledge/lens.md` relevance rules. When unsure between
   medium and low, choose **low** (precision over recall).
3. Write `runs/{today}/digest.md` from **high+medium items only**: 3–6 themes, 2–4
   sentences each, **every claim hyperlinked to its source URL**. End with a one-line
   "scanned N items from M sources, K relevant" stat.
4. Zero new relevant items is a VALID outcome — say so; never pad.

### Stage 3 — `/chaos-report` (the recommendation engine)
1. **Preconditions:** fresh `runs/{today}/digest.md` exists AND
   `knowledge/project-summary.md` header is not stale (its `updated:` ≥ its newest
   timeline entry date). If either fails, run the missing stage first.
2. Generate **Track A (3–5 realistic)** and **Track B (2–3 chaos/metamorphosis)**
   recommendations per `docs/recommendation-rubric.md`: four sliders (feasibility,
   evidence, impact, disruption 1–5), disruption doubles as the track separator
   (levels 1–2 = A, 3–5 = B). Do NOT average the sliders — the shape is the info.
3. **Self-check pass BEFORE rendering** (see "Self-check procedure" above): for each
   rec, verify Why-now resolves to a digest item and Why-us resolves to a
   compiled-truth bullet. Delete failures; if Track B drops below 2, generate grounded
   replacements rather than shipping ungrounded ones.
4. **Hand-off to the renderer:** write the structured report to
   `runs/{today}/report.json` matching the `ReportModel` dataclasses in
   `scout/render_report.py`. The JSON shape is:
   ```json
   {
     "subject_name": "string",
     "date": "YYYY-MM-DD",
     "subject_line": "[AI Chaos Scout] {Co} — week of {date}: {sharpest rec title}",
     "tldr": ["bullet 1", "bullet 2", "bullet 3"],
     "recommendations": [
       {
         "track": "A",
         "index": 1,
         "title": "string",
         "body": "2-3 sentences",
         "feasibility": 4,
         "evidence": 3,
         "impact": 4,
         "disruption": 2,
         "why_now": [{"label": "short desc", "url": "https://..."}],
         "why_us": [{"label": "compiled-truth bullet ref", "url": "source-url-or-path"}],
         "first_step": "<=2-week experiment description",
         "metamorphosis": "",
         "kill_criteria": ""
       }
     ],
     "digest_themes": [
       {"heading": "Theme title", "body": "2-4 sentences with inline links", "citations": [{"label":"..","url":".."}]}
     ],
     "provenance": {
       "scanned": 42,
       "sources": 8,
       "relevant": 12,
       "soft_failed": ["reddit (429)"],
       "run_files": ["runs/2026-07-04/items.jsonl", "runs/2026-07-04/tagged.jsonl", "runs/2026-07-04/digest.md"]
     }
   }
   ```
   Then invoke: `python scout/render_report.py --input runs/{today}/report.json`
   → produces `reports/chaos-report-{today}.md` + `.html` + `.eml`.
5. **Check for Setup Warnings:** If the `soft_failed` or terminal output contains `setup_warnings` (such as missing logins for `agent-reach` channels), you MUST explicitly communicate these setup steps to the user in your final response (e.g., "I skipped Twitter because you need to log in. Please run X...").
6. **(Optional) Composio delivery:** if the Composio MCP is connected, create a Gmail
   **draft** (`GMAIL_CREATE_EMAIL_DRAFT`, `is_html:true`) from the rendered `.html`.
   **Draft only — NEVER call `GMAIL_SEND_DRAFT`.** Everything works without Composio;
   the `.eml` file is the zero-dependency fallback (double-click → mail client draft).
7. Present the user the TL;DR block and the file paths.

## State-file map (the memory)

| Path | Owner | What |
|---|---|---|
| `config/subject.yaml` | human | the target company (urls / repo / folder) |
| `config/sources.yaml` | Stage 1 appends | Tier-2 whitelist + lens-derived queries/watchlist; Tier-1 `enabled:false` |
| `knowledge/project-summary.md` | Stage 1 | compiled-truth header + append-only timeline |
| `knowledge/lens.md` | Stage 1 | query terms, watchlist, competitors, relevance rules |
| `state/seen.json` | scripts | item-id cache across runs (digest each item once) |
| `state/etags.json` | scripts | conditional-request tokens per endpoint |
| `state/last_run.json` | scripts | per-source last-success timestamps |
| `runs/{date}/items.jsonl` | `run_scout.py` | normalized raw items |
| `runs/{date}/tagged.jsonl` | you | type + relevance tags |
| `runs/{date}/digest.md` | you | themed, fully-linked digest |
| `runs/{date}/report.json` | you | structured report matching `ReportModel` — handed to renderer |
| `reports/chaos-report-{date}.{md,html,eml}` | `render_report.py` | the deliverables |

## Degradation ladder (expected behavior, not failure)

1. Repo scripts fetch the sources (default).
2. A source blocked/rate-limited (e.g. Reddit 429) → it is **skipped and named in the
   report's Provenance**; the run completes on the rest. Never hard-fail a run for one source.
3. All scripts blocked → fall back to your built-in web/search tool for the lens queries.
4. Worst case → tell the user exactly what to paste in manually.
5. No network at demo time → replay from the morning run's `runs/{date}/items.jsonl`.

**"Zero new items is a valid run"** — if after polling all sources, zero items pass the
relevance filter, that is an honest outcome. Report it ("0 relevant items from N scanned;
recommendations unchanged from last run") and do NOT fabricate novelty to fill space.

## Hard constraints (violating any of these breaks the build)

1. **Tier 2 = zero keys, zero signups, zero paid services.** Stdlib Python + your
   built-in tools only.
2. **Python 3.10+ runtime** with dependencies defined in `requirements.txt`. (Install them before running).
3. **No MCP / cloud-agents / third-party extensions in the core path** — the ONE
   sanctioned exception is **Composio** as an optional delivery layer (`docs/composio.md`);
   everything must work with Composio absent.
4. **All state lives in repo files.** No external storage.
5. **The grounding rule** (above) is enforced by checklist, no exceptions.
6. **Portable packaging:** this `AGENTS.md` + `.cursor/rules/*.mdc` + `.cursor/commands/*.md`
   must make the repo behave identically under Devin and Cursor.

## Optional layers (never required)

- **Composio delivery** — after Stage 3, if Composio is connected, create a Gmail
  DRAFT (`GMAIL_CREATE_EMAIL_DRAFT`, `is_html:true`) from the Outlook-safe render.
  **Draft only — never send.** See `docs/composio.md`. The `.eml` is the keyless
  fallback that always exists regardless of Composio connectivity.
- **Gemini image stretch** — if `GEMINI_API_KEY` is set, generate one concept visual
  per track's top rec; embed in the HTML (data-URI) and `.eml` (cid). If unset, skip
  silently; layout must not depend on it.
