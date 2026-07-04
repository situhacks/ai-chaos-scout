# Composio — the one sanctioned connector layer

Composio is the single approved MCP/connector surface for this repo. It is a **delivery
layer, not a pipeline dependency**: every stage and all three report artifacts must work
with Composio absent (the `.eml` is the keyless fallback).

---

## Setup

1. `.cursor/mcp.json` already ships the URL-based MCP server (no API key for this path):
   ```json
   {"mcpServers": {"composio": {"type": "http", "url": "https://connect.composio.dev/mcp"}}}
   ```
2. **First-run OAuth flow:** on first use the IDE triggers a browser popup:
   - Sign in to Composio (GitHub SSO or email — free tier, no card).
   - The Gmail toolkit requests connected-app consent the first time its action is
     called. The agent says "connect your Gmail" → browser opens → standard Google
     OAuth consent → done. One-time per account.
3. Free tier: 20,000 tool calls/month, no card — hackathon volume is a rounding error.
4. **Verification:** after OAuth, the agent can call `COMPOSIO_CHECK_CONNECTED_ACCOUNT`
   (or just attempt the draft action — a clear error means not connected).

---

## Committed v1 action: `GMAIL_CREATE_EMAIL_DRAFT`

After `/chaos-report` renders the three artifacts, **if Composio is connected**, create
a Gmail draft. This is the ONLY action that runs as part of the standard pipeline.

### Exact payload shape

```json
{
  "action": "GMAIL_CREATE_EMAIL_DRAFT",
  "params": {
    "recipient_email": "{{operator's email from config or prompt}}",
    "subject": "[AI Chaos Scout] Nimbus Labs — week of 2026-07-04: Ship a retrieval-quality dashboard",
    "body": "{{contents of reports/chaos-report-2026-07-04.html}}",
    "is_html": true
  }
}
```

### Rules

- **Draft only — NEVER call `GMAIL_SEND_DRAFT` or `GMAIL_SEND_EMAIL`.** The human
  reviews, edits, and sends. That is both the safety posture and the enterprise story:
  the agent proposes, the person sends.
- `is_html: true` — the body is the Outlook-safe email HTML from the renderer (table
  layout, inline styles, system font stack). It is already designed for the Word
  rendering engine.
- `recipient_email` — prompt the operator for this on first run if not configured.
  Store it in `config/subject.yaml` under `delivery.recipient_email` for subsequent
  runs.
- `subject` — use the `subject_line` field from `report.json` verbatim.

### Fallback when Composio is absent

The `.eml` file (`reports/chaos-report-{date}.eml`) is always produced by the renderer
regardless of Composio status. Double-clicking it opens it as a ready-to-send draft in
Outlook, Apple Mail, or Thunderbird. **This is the zero-dependency delivery path.**

---

## Parked enterprise mirror (document only — do NOT require or implement)

| Action | Purpose | Notes |
|---|---|---|
| `OUTLOOK_CREATE_DRAFT` | Enterprise mirror of the Gmail draft for M365 orgs | Drop-in replacement for `GMAIL_CREATE_EMAIL_DRAFT`; known friction: M365 tenants need one-time **admin consent** for Composio's OAuth app — put in rollout plan, not demo |

---

## Security posture

### The May 2026 incident (stated honestly)

Composio disclosed a **May 2026 breach**: a compromised internal agentic monitoring
tool executed code in Composio's tool-execution sandbox. Impact: ~5,000 GitHub
connections affected; pre-May-22 API keys were deleted; GitHub tokens revoked. See
their [incident post](https://composio.dev/blog/security-incident-may-2026) for full
timeline and remediation.

### Our stance

- **Draft-only / least-scope grants.** We never send email, never write code, never
  push commits via Composio. The worst case for our integration is a leaked draft email
  (which contains only publicly-sourced information anyway).
- **Enterprise deployment** should use Composio's SOC-2 tier with:
  - A custom OAuth app (org-controlled client ID/secret, not Composio's shared app)
  - VPC / on-prem deployment option (Composio offers self-hosted)
  - Scoped tokens: Gmail `compose` scope only (no `read`)
- An enterprise security reviewer **will** raise the May 2026 incident — so we cite it
  proactively and describe the remediation + our minimal-scope posture rather than
  hoping nobody asks.

### Scope of each connected app

| App | OAuth scopes requested | Justification |
|---|---|---|
| Gmail | `https://www.googleapis.com/auth/gmail.compose` | Create drafts only; no read access to inbox |

---

## `.cursor/mcp.json` reference

The file ships in-repo and requires no modification:

```json
{
  "mcpServers": {
    "composio": {
      "type": "http",
      "url": "https://connect.composio.dev/mcp"
    }
  }
}
```

This URL-based MCP server requires no API key — authentication is handled per-user via
the browser OAuth flow described above. The MCP connection is established when the IDE
loads the project; tool calls are available immediately after OAuth consent.
