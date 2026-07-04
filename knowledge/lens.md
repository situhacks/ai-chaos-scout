---
subject: "Twenty"
updated: "2026-07-04"
---

# Research Lens — Twenty

> Distilled FROM `project-summary.md`. Scopes Stage 2 so research is done *as Twenty*,
> not generically. Machine-readable values below are pushed into `config/sources.yaml`
> (`hn_queries`, `github_watchlist`, extra `reddit_rss`).

## Compiled lens — how we look at the industry FOR this subject

- **Query terms (drive HN Algolia + web-search fallback):**
  - `open source CRM`
  - `AI CRM`
  - `CRM agents`
  - `AI sales automation`
  - `AI data enrichment`
  - `LLM workflow automation`
  - `text to SQL`
  - `Salesforce alternative`
  - `AI agent tools`
  - `model context protocol`
- **Tech watchlist (GitHub release polling, `owner/repo`, cap ~25):**
  - `twentyhq/twenty`
  - `nestjs/nest`
  - `typeorm/typeorm`
  - `graphql/graphql-js`
  - `facebook/react`
  - `pmndrs/jotai`
  - `lingui/js-lingui`
  - `redis/redis`
  - `vercel/next.js`
  - `vercel/ai`
  - `langchain-ai/langchainjs`
  - `run-llama/llama_index`
  - `modelcontextprotocol/servers`
  - `n8n-io/n8n`
  - `calcom/cal.com`
  - `documenso/documenso`
  - `supabase/supabase`
  - `pgvector/pgvector`
  - `ollama/ollama`
  - `browser-use/browser-use`
- **Competitor / adjacent names:** Salesforce (Agentforce), HubSpot, Attio, Pipedrive, Folk, Airtable, Notion, Supabase, n8n, Clay (AI enrichment).
- **Relevance rules (applied when tagging in Stage 2):**
  1. Relevant if it changes how a CRM embeds AI/agents (data entry, enrichment, outreach, summarization, natural-language querying).
  2. Relevant if it touches Twenty's stack or ecosystem: TypeScript/Node AI tooling, GraphQL, PostgreSQL/pgvector, Redis, workflow automation, MCP.
  3. Relevant if it bears on open-source monetization, self-hosting, or dev-extensible platform strategy.
  4. Ignore generic AI hype with no bearing on CRM, customer data, agents, or Twenty's stack.
  5. When unsure between medium and low relevance, choose low (precision over recall).

## Timeline — append-only

### 2026-07-04 — first lens
Distilled from the first project-summary. Seeded 10 HN queries, 20-repo tech watchlist
(anchored on Twenty's TS/NestJS/GraphQL/Postgres stack + the JS AI-agent ecosystem:
vercel/ai, langchainjs, llama_index, MCP servers, n8n, ollama, pgvector), and added
CRM/AI-adjacent competitors. Added r/CRM and r/SaaS to reddit_rss. Relevance rules
tuned to CRM×AI so generic model-release hype scores low unless it touches agents,
data, or Twenty's stack.
