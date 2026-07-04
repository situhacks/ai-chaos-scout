---
subject: "Twenty"
updated: "2026-07-04"
---

# Project Summary — Twenty

> Compiled-truth header + append-only ingest timeline. Stage 1 (`/chaos-lens`)
> refreshes the header and appends to the timeline; it never rebuilds. Every
> compiled-truth bullet cites a source (a `subject/…` path or a URL).

## Compiled truth — what is true NOW

*(What the company IS today. Each bullet cites a source.)*

- **Offering:** Open-source CRM positioned as "the open alternative to Salesforce, designed for AI" — a set of building blocks (objects, views, workflows, and **agents**) that technical teams extend as code, available as managed Cloud or self-hosted — [repo description + README](https://github.com/twentyhq/twenty), [twenty.com/product](https://twenty.com/product)
- **Users / customers:** Technical teams / developers who want a custom CRM they "build, ship, and version like the rest of [their] stack," plus non-technical CRM end-users on the hosted product — [README "Why Twenty"](https://github.com/twentyhq/twenty), [twenty.com/why-twenty](https://twenty.com/why-twenty)
- **Business model:** Open-source core (public monorepo, community contributions) + managed **Cloud** signup at twenty.com (spin up a workspace in <1 min) as the commercial/hosted path; self-hosting via Docker Compose is free — [README "Installation → Cloud / Self-hosting"](https://github.com/twentyhq/twenty), [twenty.com/pricing](https://twenty.com/pricing)
- **Tech stack:** TypeScript monorepo on Nx; backend NestJS + BullMQ + PostgreSQL + Redis; frontend React + Jotai + Linaria + Lingui; GraphQL API — [README "Stack"](https://github.com/twentyhq/twenty), [repo topics](https://github.com/twentyhq/twenty)
- **Differentiators:** CRM-as-code — define objects/fields/views in TypeScript (`twenty-sdk/define`), scaffold with `npx create-twenty-app`, publish apps to a workspace, version control the CRM like software; very large OSS community (~52k+ GitHub stars) — [README "Build an app" / apps guide](https://github.com/twentyhq/twenty)
- **Stated strategy:** "Designed for AI" — AI/agents treated as a first-class CRM primitive alongside objects/views/workflows; developer-extensible platform play against incumbent SaaS CRMs — [repo description (2026)](https://github.com/twentyhq/twenty), [developer docs](https://docs.twenty.com/developers/introduction)
- **Constraints:** Community/OSS-driven cadence (Hacktoberfest, good-first-issue) → contributor bandwidth dependency; hard runtime deps on PostgreSQL + Redis for self-host; competes directly with well-funded incumbents (Salesforce, HubSpot) and newer AI-CRM entrants; license is non-standard (`NOASSERTION` per GitHub) which can affect commercial redistribution — [repo topics/license](https://github.com/twentyhq/twenty), [self-host docs](https://docs.twenty.com/developers/introduction)

## Timeline — append-only ingest log

### 2026-07-04 — first ingest
Read the live GitHub repo (`twentyhq/twenty`: description, README, topics, Stack, latest release `twenty/v2.18.0` published 2026-07-02, ~52,166 stars, created 2022-12-01) via the GitHub API, plus saved copies of twenty.com, /product, /why-twenty, /releases, /pricing and docs.twenty.com getting-started + developers intro under `subject/twenty-web/`. Established the first compiled-truth header: offering (AI-designed open-source CRM), ICP (technical teams building CRM-as-code), model (OSS core + managed Cloud + free self-host), stack (TS/Nx/NestJS/Postgres/Redis/React), differentiators (CRM-as-code, apps SDK/CLI, agents as a primitive, 52k+ stars), stated "designed for AI" strategy, and constraints (OSS cadence, infra deps, incumbent competition, NOASSERTION license). Key signal vs. a naive prior: Twenty ALREADY ships "agents" and brands itself "designed for AI" — recommendations must build beyond table-stakes AI, not propose it from zero.
