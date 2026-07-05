# CLAUDE.md

Claude Code reads `CLAUDE.md`, not `AGENTS.md`. This repo keeps **`AGENTS.md` as the
canonical, tool-agnostic operating manual** — so import it here rather than
duplicating instructions:

@AGENTS.md

Everything above (role, the non-negotiable grounding rule, the self-check procedure,
the scripts-fetch/you-judge division of labor, the three-stage `/chaos-*` pipeline,
the state-file map, the degradation ladder, and the hard constraints) applies verbatim
to Claude Code.

## Claude Code specifics

- The `/chaos-lens`, `/chaos-scout`, `/chaos-report`, `/chaos-run` flows are defined in
  `.cursor/commands/*.md`. They are plain-markdown procedures — follow them step by
  step even though Claude Code will not surface them as native slash commands. To run
  a stage, read the matching command file and execute it.
- Runtime is **Python 3.10+**. Ensure dependencies in `requirements.txt` are installed before running. Run `python scout/run_scout.py` and `python scout/render_report.py` directly.
- Do not edit files under `.cursor/` unless explicitly asked; in enterprise setups that
  directory is human-committed and may be read-only to the agent.
- The `report.json` you produce in Stage 3 must match the `ReportModel` dataclasses in
  `scout/render_report.py` exactly — see `AGENTS.md` § Stage 3 for the full JSON shape.
- **Composio is optional.** If Composio MCP is unavailable, the pipeline still
  produces all three report artifacts (`.md`, `.html`, `.eml`). The `.eml` is the
  zero-dependency delivery fallback.
