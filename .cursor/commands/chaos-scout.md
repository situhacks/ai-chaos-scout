# /chaos-scout — Stage 2: scoped scout

> You are AI Chaos Scout operating inside this repo. State files are the source of
> truth. Never fabricate a source; every claim you write must carry a link. If a fetch
> or file is missing, degrade gracefully and say so in the output.

Poll the keyless sources THROUGH the lens, then judge what matters.

## Steps

1. **Fetch:** run `python scout/run_scout.py` in the terminal. It reads
   `config/sources.yaml` + the lens-seeded queries/watchlist, fetches all enabled
   Tier-2 sources, dedups against `state/seen.json`, and writes
   `runs/{today}/items.jsonl`. Read that file. If some sources soft-failed, note which
   (the script prints them) and continue — a blocked source is skipped, not fatal.
   - If the script itself is blocked, fall back to your built-in web tool for the lens
     `hn_queries`; worst case, tell the operator exactly what to paste in.

2. **Tag** every item into `runs/{today}/tagged.jsonl` (same fields as the item plus):
   - `type` ∈ {release, opinion, discussion, benchmark, funding, tool}
   - `relevance` ∈ {high, medium, low, none}, judged **strictly against
     `knowledge/lens.md` relevance rules**. When unsure between medium and low, choose
     **low** (precision over recall — the digest must stay readable).

3. **Write `runs/{today}/digest.md`** from **high + medium items only**:
   - 3–6 themes, each 2–4 sentences, **every claim hyperlinked to its item URL**
     (link to the original article/release/thread, not to the digest file itself).
   - End with one line: `scanned N items from M sources, K relevant`.
   - The digest is what Stage 3 reads for "Why now" citations — every URL here must be
     a real, fetchable source URL. Do not link to `runs/` paths or internal files.

4. **Zero new relevant items is a valid outcome** — say so plainly; do not pad or
   fabricate novelty. Write the digest with the stat line and 0 themes.

## Output to operator
The `scanned N / K relevant` stat, the theme headings, and the path to `digest.md`.

## Guardrails
- Tag against the lens relevance rules, not general interestingness.
- Do not promote low→medium to fill space. Precision over recall.
- Every claim in the digest must hyperlink to the original source — these become the
  Why-now citations in Stage 3. Broken or missing links will cause recs to fail the
  self-check gate.
