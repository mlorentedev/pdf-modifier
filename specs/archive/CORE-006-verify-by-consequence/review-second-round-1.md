---
spec: "CORE-006-verify-by-consequence"
verdict: "FAIL"
reviewed_sha: "e6a418c13a331afa76b88c31a8cdad89be11a32a"
reviewer: "anthropic-review/claude-sonnet-5-5"
date: "2026-10-13"
---

## Adversarial review

**Scope**: `CORE-006-verify-by-consequence`, whole range `git diff 01624dee3bc417bd0688b183778781674b4c8a9f...HEAD` (28 files; `core/modifier.py` +401, one test file +713).
**Sources**: `proposal.md`, `tasks.md`, `features.json`, `verification.md`, the full `modifier.py` diff, `docs/adr/adr-015-refuse-rather-than-lose.md`. I did not read `review.md` or its transcript. The earlier `review-round-*.md` files in the spec folder were not read either.

Run in this session (all against `e6a418c`, tree clean apart from this file):
- `uv run pytest -q`: 424 passed, 19 skipped. `ruff check` and `mypy --strict src`: clean.
- The target test file: 43 passed.
- Mutation M1 (`_check_no_other_object_lost_characters` returns immediately): 7 red, matching `verification.md`. Reverted.
- Four throw-away probes in `/tmp/rv/`, not committed. A random-page fuzz ran about 2000 pages over varied fonts, columns and leading, against both this code and the base-commit `modifier.py`. There were also a two-replacement geometry probe, a rotated-text probe and a base-vs-new single-column sweep.

### Spec and task alignment
- The core claim holds under the fuzz. No page converted with an unreported loss of non-target glyphs (0 silent losses in about 2000 pages, read from the written file). No refusal came from coordinate noise: every check-refusal I replayed with the check neutralised showed real loss in the output.
- AC3 (planted loss fires), AC4 (page named, no output) and AC6 (cost) are backed by named tests and my re-runs. M1 confirms the check is load-bearing.
- AC5 is satisfied only in the narrowest sense. The CORE-006 commit itself is small, but the range carries CORE-001's trim rewrite, `scripts/check-dependabot-alerts.py`, `probe_fitter_reachability.py` and CI-001's `tasks.md`. `verification.md` declares this honestly under "Provenance".
- The proposal's boundary for what may be accepted is "an object whose ink the replacement's rectangle cannot avoid covering". The code does not implement that boundary reliably (Finding 1), and the "no third outcome" sentence in "What" is not true for multi-replacement pages.
- `tasks.md`'s last two boxes (CORE-001 f9, archive) are unticked, which is accurate.
- No `[AGENT-DRAFT]` or `[AGENT-SUGGESTION]` tags found in the spec files.

### Findings

| Severity | Reality | Area | Finding | Evidence | Test (named, or UNTESTED) | Fix location |
|----------|---------|------|---------|----------|---------------------------|--------------|
| **Major** | **REAL** | `_dispose_of_lost_characters` / `_apply_replacements_to_page` | **A loss caused by one replacement is downgraded from refusal to warning because a *different* replacement on the same page shares a line with the lost object.** `co_located` is computed as `any(_same_line(target, box) for _, target in redactions)`: any target on the page, not the redaction whose rectangle reached the glyph. Repro: 12 pt Helvetica at 0.6 em leading, lines `VALTHREE` (x=72), `KEEPKEEP` (x=72, next line) and `VALFOUR` (x=250, same line as `KEEPKEEP`). Replace `{VALTHREE: X}` alone and the page is **refused** (`would lose 8 character(s) ... (72.0, 94.3, 136.0, 110.8)`). Replace `{VALTHREE: X, VALFOUR: Y}` and the page **converts**; the output text is `X\nY\n`. `KEEPKEEP` is gone and the only trace is a warning saying it was removed "because its ink is drawn in the same place". That is false: `KEEPKEEP` is a different line from `VALTHREE`, the rectangle that took it, and it shares ink with nothing. The same geometry gives opposite outcomes depending on an unrelated second replacement, so this is not a boundary-of-the-proxy question (the CORE-007 / `#209` gap) but a misattribution. `proposal.md` says the allow-list is "the replacement itself, and any object whose ink the replacement's rectangle cannot avoid covering"; everything else refuses. Multi-replacement pages are the normal case: `process()` takes a dict of replacements and batches per page. Tight leading is the geometry this spec exists for. | `/tmp/rv/g.py` output at 0.6 em: `False refused ... would lose 8 character(s)` vs `True converted False ['page 1: 8 character(s) of a text object at (72.0, 94.3, 136.0, 110.8) were removed with the replacement, because its ink is drawn in the same place'] 'X\nY\n'`. Code: `modifier.py` `_dispose_of_lost_characters`, the `co_located = any(...)` over all `redactions`. | **UNTESTED.** Every `process(...)` call in `test_replacement_preserves_following_lines.py` passes exactly one key (`replacements={TARGET: ...}`). The one-page, one-replacement fixtures cannot see this. | code + tests. Attribute per redaction: a lost glyph is accepted only if the fitted rect of a redaction **that reaches that glyph** also belongs to a target on the lost object's line. Add a two-replacement row (the repro above) that asserts refuse-or-preserve. |
| Minor | REAL | Spec/ADR claim vs code | ADR-015 says `ModificationResult.warnings` "reaches every interface (CLI, MCP, HTTP, batch)". Checked: single-file CLI prints it, and the MCP and HTTP routes return it in the JSON payload. But `frontend/src` never reads `warnings` (only the TS type and one test fixture mention it), and the CLI batch table (`cli.py` ~L262-290) prints only `replacements_made` with status `OK`, so the accepted-and-reported loss is invisible in the web UI and in batch mode. "Accepted is not the same as silent" holds only where a consumer reads the list. The AC as worded ("adds a `warnings` entry") is met literally. | `grep -rn warnings frontend/src backend/src` (only the TS type, a test fixture, `models.py`, `cli.py:171`, and the MCP docstring); `cli.py` batch loop | UNTESTED | ticket (frontend + batch table); correct the ADR sentence (ADR is outside the contract set) |
| Minor | REAL | AC2 / refusal cost | Documents that base converted correctly now refuse at 0.7 em in ordinary fonts, via the CORE-001 fitter guards (predictive refusals), not the new check. Single-column block, 8 lines, 12 pt, 0.7 em leading: Helvetica and Times-Roman convert correctly at base (all lines kept, target gone) and are refused now. Courier-Bold at 0.7 em: base loses a line, now refused (correct). In a 400-page random fuzz, 19 of 30 fitter refusals were pages base converted cleanly. This is in-spirit with ADR-015's "refuse rather than lose", but the proposal says the trim "reduces how often the consequence check has to refuse", and here the predictive guards (`_refuse_trim_that_drops_another_line`, `_refuse_collapsed_fit`) refuse where the consequence would have been clean. They also duplicate what the check now decides. AC1's own sweep lists `helv 11/7.7 (0.70 em): REFUSED (the fitter's own guard)` without noting that base was fine there. | `/tmp/rv/h.py`: `helv 0.7 [('base','ok'),('new','refused')]`, `tiro 0.7 [('base','ok'),('new','refused')]` | UNTESTED. No row pins helv/tiro at 0.7 em. | ticket (CORE-007 neighbourhood): consider letting the consequence check, not the predictive guards, decide |
| Minor | SPECULATIVE | `_glyph_index` | The glyph key `(char, round(x0,1), round(y0,1))` stores one owner per key. With exact overprints (same character, same position, two spans) the earlier span's ownership is overwritten by the later one. If the later span is the target, a co-located object that shares those glyphs is exempted from both refusal and warning. I did not construct a case where this loses a character unreported. | code read only | UNTESTED | tests (add an exact-overprint row), or key by `(owner, char, pos)` |
| Question | n/a | Scope | `scripts/check-dependabot-alerts.py`, `backend/scripts/probe_fitter_reachability.py` and CI-001's `tasks.md`/`verification.md` ride in this range. AC5 wants "nothing opportunistic in the diff". The provenance section justifies them (stacked, unblocking). Confirm the PR description lists them, since the review diff is the union. | `git diff --stat` | n/a | PR body |

Strengths that directly mitigate a risk (not praise): the glyph-position comparison read from the written file is robust to span re-splitting. I found no false refusals from position rounding in about 2000 fuzzed pages.

### Evaluator rubric

| Dimension | Grade (A-D) | Rationale (one line) |
|-----------|-------------|----------------------|
| Correctness        | C | Single-replacement behaviour is sound (0 silent losses in the fuzz), but a REAL attribution defect downgrades a refusal to a false warning on multi-replacement pages. |
| Verification       | C | Strong for the single-replacement geometry (M1 and the planted loss reproduce); no row has more than one replacement key, so the Major is invisible to the whole suite. |
| Scope              | B | Check and rows match the proposal; stacked CORE-001/#204/#207 content is declared and attributable. |
| Reliability        | B | Refusal writes nothing and names page and object; the accepted-loss reporting reaches only some consumers (Minor). |
| Maintainability    | B | New helpers are small (CC 2-3, functions under 30 body lines), ruff and mypy --strict clean; per-redaction attribution is the missing structure. |
| Handoff-readiness  | B | ADR-015, lessons and `verification.md` are present and candid; one ADR sentence overstates interface coverage. |

### Verdict
**FAIL**: one REAL Major (misattributed co-location turns a refusal into a false-reason warning), UNTESTED. The Major is in code and tests, so it is outside the contract set; the fix needs a re-review but no edit to `proposal.md`, `tasks.md` or `features.json`.

`dotf spec archive` is **not advisable** at this revision.

### Recommended next steps
1. Code + tests (outside the contract set). In `_dispose_of_lost_characters` / `_apply_replacements_to_page`, record per redaction which glyphs its fitted rect reaches and which target it belongs to. Accept (warn) a lost glyph only when a redaction that reaches it has a target on that object's line; otherwise refuse. Add a named regression row with two replacement keys (the `VALTHREE` / `KEEPKEEP` / `VALFOUR` fixture at 0.6 em) that fails today (converted, `KEEPKEEP` lost) and passes after (refused or preserved). Re-run M1 to confirm the new row goes red under it.
2. For `verification.md` (outside the contract set), disposition each of these as applied, ticketed, or declined with a reason:
   - Warnings not surfaced by the frontend or the batch table: ticket it and correct ADR-015's "every interface" sentence.
   - Predictive CORE-001 guards refusing helv/tiro at 0.7 em where base was clean: ticket it next to CORE-007 (`#209`).
   - The exact-overprint ownership overwrite: ticket it, or add a row showing it is harmless.
3. Re-review after the fix, at the new head. The first signer's contract-digest freshness still holds, because no contract-set file changes.
