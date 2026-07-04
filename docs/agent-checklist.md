# Agent operating checklist — full `/chaos-run` from scratch

Follow this top-to-bottom for a complete run. Each step has a verification gate;
do not skip a gate even if the step "seemed to work."

---

## Pre-flight

- [ ] `config/subject.yaml` has a non-empty `name` + at least one of `urls`, `repo`, or `folder`.
- [ ] Python 3.10+ available: `python --version` (no pip needed).
- [ ] Outbound HTTPS on port 443 (or accept the offline-fallback path).

---

## Stage 1 — `/chaos-lens`

| # | Action | Gate |
|---|---|---|
| 1 | Read `config/subject.yaml`; ingest subject material into `subject/` | `subject/` is non-empty |
| 2 | Read all subject material (READMEs, docs, strategy) | You can articulate what the company IS |
| 3 | Write/refresh `knowledge/project-summary.md` (compiled-truth header + timeline) | Every bullet has a `[source](url)` citation; `updated:` = today |
| 4 | Distill `knowledge/lens.md` (queries, watchlist, relevance rules) | 5–10 query terms present; `updated:` = today |
| 5 | Push lens values into `config/sources.yaml` (`hn_queries`, `github_watchlist`, `reddit_rss`) | At least `hn_queries` is non-empty |
| 6 | Report to operator | Explain first-ingest or what changed |

**Incremental rule:** if `project-summary.md` already has content, DIFF + append.
Never rebuild. Timeline is append-only.

**Skip condition (`/chaos-run` only):** if compiled-truth header exists AND `updated:`
≥ last subject-material change date → skip Stage 1 entirely.

---

## Stage 2 — `/chaos-scout`

| # | Action | Gate |
|---|---|---|
| 1 | `python scout/run_scout.py` | `runs/{today}/items.jsonl` exists (even if 0 items) |
| 2 | Tag every item → `runs/{today}/tagged.jsonl` | Each item has `type` + `relevance` fields |
| 3 | Write `runs/{today}/digest.md` from high+medium items | Every claim is hyperlinked; ends with stat line |

**Zero items is valid.** Write the stat line (`scanned 0 items from 0 sources, 0 relevant`)
and move on. Do NOT pad.

**Degradation:** if `run_scout.py` fails → use built-in web tool for `hn_queries`.
If that also fails → tell operator what to paste.

---

## Stage 3 — `/chaos-report`

| # | Action | Gate |
|---|---|---|
| 1 | Verify preconditions: `digest.md` exists for today; `project-summary.md` not stale | Both checks pass |
| 2 | Generate Track A (3–5) + Track B (2–3) recs per `docs/recommendation-rubric.md` | Each rec has 4 sliders + the required narrative fields |
| 3 | **Self-check pass** (THE GROUNDING GATE) | See below |
| 4 | Write `runs/{today}/report.json` matching `ReportModel` | Valid JSON; all required fields present |
| 5 | `python scout/render_report.py --input runs/{today}/report.json` | Three files appear in `reports/` |
| 6 | (Optional) Composio Gmail draft | Only if MCP connected; draft only, never send |
| 7 | Present TL;DR + file paths to operator | Done |

### Self-check gate (step 3) — DO NOT SKIP

For EACH recommendation:
1. Find its **Why-now** URL in `runs/{today}/digest.md` → must exist as a hyperlink in
   the digest pointing to a real source.
2. Find its **Why-us** reference in `knowledge/project-summary.md` → must be a
   currently-present compiled-truth bullet.
3. **If either fails → delete the rec.** No hedging, no weakening.
4. After deletions: Track A < 3 → generate grounded replacements. Track B < 2 →
   generate grounded replacements. Never ship ungrounded.

---

## Post-run

- [ ] Verify all three report files exist: `reports/chaos-report-{today}.{md,html,eml}`
- [ ] Spot-check: open the `.md` and confirm every rec has Why-now + Why-us links.
- [ ] (If Composio connected) Confirm the Gmail draft was created (draft only!).
- [ ] Report to operator: TL;DR block + file paths.

---

## The degradation ladder (memorize this)

1. **Scripts fetch** (default happy path)
2. **Source blocked** → skipped + named in Provenance; run continues
3. **All scripts blocked** → fall back to agent's built-in web/search tool
4. **Web tool also blocked** → tell operator exactly what to paste in
5. **No network (demo)** → replay from cached `runs/{date}/items.jsonl`

---

## Key rules to internalize

- **Zero new items is a valid run.** Say so; never pad.
- **Never fabricate a source.** Every link must be real and fetchable.
- **Never rebuild the timeline.** It is append-only memory.
- **Never send email.** Drafts only, always.
- **Never average the four sliders.** The shape IS the information.
- **Composio is optional.** Everything works without it.
- **Disruption level = track assignment.** 1–2 = Track A, 3–5 = Track B.
