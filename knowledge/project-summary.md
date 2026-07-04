---
subject: ""            # set to config subject.name after first ingest
updated: ""            # ISO date the compiled-truth header was last refreshed
---

# Project Summary — {subject}

> **This is a TEMPLATE.** Stage 1 (`/chaos-lens`) fills it on first run and only
> ever APPENDS to the timeline / REFRESHES the header afterward — never rebuilds.
> Every bullet in the compiled-truth header MUST cite its source (file path or URL).
> Staleness rule: if `updated:` (front-matter) is older than the newest timeline
> entry below, this file is STALE — Stage 1 must refresh the header before Stage 3
> may write recommendations.

## Compiled truth — what is true NOW

*(What the company IS today. Each bullet cites a source: a `subject/…` file path or a URL.)*

- **Offering:** _(what they sell / build)_ — [source](…)
- **Users / customers:** _()_ — [source](…)
- **Business model:** _()_ — [source](…)
- **Tech stack:** _()_ — [source](…)
- **Differentiators:** _()_ — [source](…)
- **Stated strategy:** _()_ — [source](…)
- **Constraints:** _(team size, regulatory, platform dependencies)_ — [source](…)

## Timeline — append-only ingest log

*(Dated entries: what material was read this run, and what changed vs. last run.
 Never rewrite past entries. This IS the system's memory.)*

<!-- Example:
### 2026-07-04 — first ingest
Read subject/acme/README.md, subject/acme/docs/strategy.md, and https://acme.ai.
Established: offering, ICP, stack (Python/FastAPI + pgvector), and stated 2026
"agents everywhere" strategy. First compiled-truth header written.
-->
