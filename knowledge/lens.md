---
subject: ""
updated: ""            # ISO date the lens was last refreshed
---

# Research Lens — {subject}

> **This is a TEMPLATE.** Stage 1 distills it FROM `project-summary.md`. It is the
> Scout's targeting package: it scopes Stage 2 so research is done *as this company*,
> not generically. Refresh it whenever the summary changes. After writing it, push
> the machine-readable values into `config/sources.yaml`
> (`hn_queries`, `github_watchlist`, extra `reddit_rss` subs).

## Compiled lens — how we look at the industry FOR this subject

- **Query terms (5–10)** — drive HN Algolia search + agent web-search fallback:
  - _e.g._ `retrieval augmented generation`, `agent evaluation`, `pgvector`
- **Tech watchlist** — frameworks/models/repos the subject depends on → GitHub release polling (`owner/repo`):
  - _e.g._ `langchain-ai/langchain`, `pgvector/pgvector`
- **Competitor / adjacent names:**
  - _e.g._ CompetitorA, CompetitorB
- **Relevance rules (3–5 plain sentences)** — the agent applies these when tagging in Stage 2:
  1. _Relevant if it changes how {subject} builds, prices, or positions its core offering._
  2. _Relevant if it touches a dependency on the tech watchlist._
  3. _Ignore generic AI hype with no bearing on {subject}'s stack, users, or model._
  4. _When unsure between medium and low relevance, choose low (precision over recall)._

## Timeline — append-only

<!-- ### 2026-07-04 — first lens
Distilled from the first project-summary. Seeded 7 HN queries, 5 watchlist repos,
added r/LangChain. -->
