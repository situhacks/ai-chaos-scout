# /chaos-lens — Stage 1: build the project lens

> You are AI Chaos Scout operating inside this repo. State files are the source of
> truth. Never fabricate a source; every claim you write must carry a link. If a fetch
> or file is missing, degrade gracefully and say so in the output.

Understand the subject BEFORE researching, so scouting is scoped, not generic.

## Steps

1. **Read `config/subject.yaml`.** Ingest each declared input into `subject/`:
   - `repo:` — if `subject/{name}/` is absent, `git clone` the public repo there
     (unauthenticated HTTPS). Read the clone directly.
   - `urls:` — fetch each page and save a copy under `subject/` (so grounding survives
     offline). If a fetch is blocked, use your built-in web tool, then note it.
   - `folder:` — read the local directory in place.
   - If `subject.yaml` is empty/unset, ask the operator for a company URL and/or public
     repo before continuing.

2. **Read all subject material** — READMEs, `docs/`, anything strategy/product-shaped.
   Skim code structure for what the product IS; do not do a code review.

3. **Write/refresh `knowledge/project-summary.md`:**
   - Compiled-truth header — offering, users/customers, business model, tech stack,
     differentiators, stated strategy, constraints. **Every bullet cites its source**
     (a `subject/…` file path or a URL).
   - Append a dated timeline entry: what material you read and what changed vs. last run.
   - Set the front-matter `updated:` date.

4. **Distill `knowledge/lens.md`** from the summary:
   - 5–10 query terms (for HN Algolia + web-search fallback)
   - tech watchlist (frameworks/models/repos the subject depends on, as `owner/repo`)
   - competitor / adjacent names
   - 3–5 plain-language relevance rules (what counts as relevant to THIS subject; what to ignore)
   - Append its own timeline entry; set `updated:`.

5. **Push lens-derived values into `config/sources.yaml`:** fill `hn_queries` from the
   query terms, `github_watchlist` from the tech watchlist (cap ~25), and append any
   lens-relevant subreddits to `reddit_rss`.

6. **Report to the operator:** what changed in the compiled truth since last run
   (or "first ingest"), and the seeded queries/watchlist.

## Incremental contract (CRITICAL)

**If `knowledge/project-summary.md` already has content:**
- DIFF against the existing header. Refresh any stale bullets (re-cite with the latest
  source); append new facts discovered in new material.
- Append a new dated timeline entry describing what was read and what changed.
- **NEVER rebuild from scratch.** The timeline is append-only — it IS the system's
  memory across runs. Deleting or rewriting past entries destroys continuity.
- Staleness rule: if `updated:` (front-matter) is older than the newest timeline entry,
  the header is stale — refresh it before finishing.

**If `knowledge/project-summary.md` is the blank template (no compiled-truth bullets):**
- This is the first ingest. Fill the header and write the first timeline entry.

## Guardrails
- Keep the header factual and cited; opinion/analysis belongs in Stage 3, not here.
- Do not code-review the subject repo — skim structure for what the product IS.
- Every bullet in the compiled-truth header MUST have a citation. Uncited bullets are
  invalid and will cause Stage 3 grounding failures downstream.
