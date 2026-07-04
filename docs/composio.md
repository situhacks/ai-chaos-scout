# Composio — the one sanctioned connector layer

Composio is the single approved MCP/connector surface for this repo. It is a **delivery
layer, not a pipeline dependency**: every stage and all three report artifacts must work
with Composio absent (the `.eml` is the keyless fallback).

## Setup

1. `.cursor/mcp.json` already ships the URL-based MCP server (no API key for this path):
   ```json
   {"mcpServers": {"composio": {"type": "http", "url": "https://connect.composio.dev/mcp"}}}
   ```
2. First use triggers browser OAuth: a Composio account, then per-toolkit connected-app
   consent (Gmail, GitHub, …) as each tool is first called.
3. Free tier: 20,000 tool calls/month, no card — hackathon volume is a rounding error.

## Committed v1 action

After `/chaos-report` renders, **if Composio is connected**, create a Gmail draft:
- `GMAIL_CREATE_EMAIL_DRAFT` with `is_html: true`, body = the Outlook-safe email render.
- **Draft only — never call `GMAIL_SEND_DRAFT`.** The human reviews and sends. That is both
  the safety posture and the enterprise story: the agent proposes, the person sends.

## Demo extras (build at most the first)

| Action | Beat |
|---|---|
| `GITHUB_CREATE_ISSUE` | the top Track A rec's "first testable step" becomes a real issue in the subject repo, live on stage — recommendation → backlog in one breath |
| `SLACK_SEND_MESSAGE` | TL;DR posted to a channel (parked) |
| `GOOGLECALENDAR_CREATE_EVENT` | agent books next week's "chaos briefing" (parked) |

Scope guard: each extra is a single post-report call. If any threatens report quality
time, cut it — the report is the product; delivery is garnish.

## Enterprise follow-up (document, don't build)

- **Outlook is drop-in:** `OUTLOOK_CREATE_DRAFT` mirrors the Gmail action. Known friction:
  M365 tenants typically need one-time **admin consent** for Composio's OAuth app — put it
  in the rollout plan, not the demo.
- **Security posture, stated honestly:** Composio disclosed a **May 2026 breach** (a
  compromised internal agentic monitoring tool executed code in the tool-execution sandbox;
  5,000+ GitHub connections affected; pre-May-22 API keys deleted, GitHub tokens revoked —
  see their incident post). Our stance: grants are **draft-only / least-scope**; enterprise
  deployment should use Composio's SOC-2 tier with a custom OAuth app + VPC/on-prem options.
  An enterprise reviewer *will* raise this — so we cite it and the remediation rather than
  hoping nobody asks.
