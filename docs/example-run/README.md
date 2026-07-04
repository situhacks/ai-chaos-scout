# Example run — Twenty (open-source CRM)

These files are **illustrative fixtures** showing what each pipeline stage produces
when pointed at a real subject. They demonstrate the artifact shapes, the grounding
discipline (every bullet cited), and how the stages connect.

**Subject:** [Twenty](https://twenty.com) — the #1 open-source CRM. Build-in-public,
self-hostable, TypeScript/React/PostgreSQL, GraphQL + REST API, data-model
customization, workflow engine, MCP-native. Non-AI-native today but AI-adjacent
(agents, AI chat, agentic IDE integration as of v2.0).

---

## How these map to the pipeline stages

| File | Pipeline stage | What it shows |
|---|---|---|
| `project-summary.md` | Stage 1 `/chaos-lens` output | Compiled-truth header (each bullet cited to a real Twenty page) + one timeline entry |
| `lens.md` | Stage 1 `/chaos-lens` output | Query terms, tech watchlist, competitors, relevance rules scoped to Twenty |
| `digest.md` | Stage 2 `/chaos-scout` output | 4 themes from a realistic scout run, every claim hyperlinked |
| `report.json` | Stage 3 `/chaos-report` output | Valid `ReportModel` JSON: 3 Track A + 2 Track B recs, all grounded |

---

## Using these as a reference

- **Pattern-match structure:** when writing your own artifacts, mirror the heading
  hierarchy, citation format, and field names shown here.
- **Grounding discipline:** notice that every Why-now URL in `report.json` points to a
  source that appears in `digest.md`, and every Why-us reference points to a bullet in
  `project-summary.md`. The self-check gate enforces this mechanically.
- **Do NOT copy these into the real `knowledge/` or `runs/` directories.** They live
  under `docs/example-run/` only. The real pipeline writes to `knowledge/`, `runs/`,
  and `reports/` at runtime.

---

## Freshness note

These fixtures reflect Twenty's public state as of early July 2026 (v2.0 release,
pricing, docs). They will drift as Twenty ships new features — that's fine; they exist
to show the *shape* of the artifacts, not to stay current.
