# CLAUDE.md

Claude Code reads `CLAUDE.md`, not `AGENTS.md`. This repo keeps **`AGENTS.md` as the
canonical, tool-agnostic operating manual** — so import it here rather than
duplicating instructions:

@AGENTS.md

Everything above (role, the non-negotiable grounding rule, the scripts-fetch/you-judge
division of labor, the three-stage `/chaos-*` pipeline, the state-file map, the
degradation ladder, and the hard constraints) applies verbatim to Claude Code.

## Claude Code specifics

- The `/chaos-lens`, `/chaos-scout`, `/chaos-report`, `/chaos-run` flows are defined in
  `.cursor/commands/*.md`. They are plain-markdown procedures — follow them step by
  step even though Claude Code will not surface them as native slash commands. To run
  a stage, read the matching command file and execute it.
- Runtime is **stdlib-only Python 3.10+** — do not `pip install` anything in the core
  path. Run `python scout/run_scout.py` and `python scout/render_report.py` directly.
- Do not edit files under `.cursor/` unless explicitly asked; in enterprise setups that
  directory is human-committed and may be read-only to the agent.
