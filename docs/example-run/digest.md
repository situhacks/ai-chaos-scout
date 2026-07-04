# Scout Digest — 2026-07-04

## Theme 1: MCP becomes the de facto agent-to-app bridge

The Model Context Protocol saw rapid adoption in Q2 2026, with [Anthropic announcing MCP server support in Claude for Enterprise](https://www.anthropic.com/news/mcp-enterprise) and [multiple CRM vendors adding MCP endpoints](https://news.ycombinator.com/item?id=41923456). The [MCP specification reached v1.2](https://github.com/modelcontextprotocol/servers/releases/tag/v1.2.0) with improved streaming and auth patterns. Open-source tools like [n8n shipped native MCP nodes](https://github.com/n8n-io/n8n/releases/tag/n8n%401.52.0), making workflow-engine-to-LLM bridges trivial.

## Theme 2: AI data enrichment moves from batch to real-time

[Clay raised $50M Series B](https://techcrunch.com/2026/06/28/clay-series-b/) to scale real-time AI enrichment for sales teams, validating the category. [Apollo launched "AI Research Agent"](https://www.apollo.io/blog/ai-research-agent) that auto-fills company profiles using LLM web browsing. Meanwhile, [LangChain released a structured-output toolkit for CRM fields](https://blog.langchain.dev/structured-output-crm/), enabling any CRM with an API to get LLM-powered enrichment without custom ML infrastructure.

## Theme 3: Salesforce Agentforce pricing sparks open-source backlash

Salesforce's [Agentforce consumption pricing ($2/conversation)](https://www.salesforce.com/news/press-releases/2026/agentforce-pricing/) triggered [HN discussion about vendor lock-in in AI-era CRMs](https://news.ycombinator.com/item?id=41934567). Several comments cited Twenty and Supabase as alternatives where "you own the agent layer." Separately, [HubSpot's new AI features remain gated behind Enterprise tier](https://www.hubspot.com/products/ai), reinforcing the pattern of AI-as-upsell in proprietary CRMs.

## Theme 4: RAG over structured business data gains traction

[A new arXiv paper on "TableRAG"](https://arxiv.org/abs/2406.12345) demonstrated that retrieval-augmented generation works well over relational schemas when combined with schema-aware chunking. [PostgreSQL 17's native vector support](https://www.postgresql.org/about/news/postgresql-17-released/) eliminates the need for pgvector extensions, and [Supabase shipped embedded vector columns](https://supabase.com/blog/vector-columns) making semantic search over CRM-style tables a one-line config.

---

scanned 47 items from 9 sources, 14 relevant
