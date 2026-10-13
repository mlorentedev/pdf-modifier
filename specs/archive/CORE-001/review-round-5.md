---
spec: "CORE-001"
verdict: "PASS"
reviewed_sha: "f7b1324eea56c0e59ab9acf112d4df25a7a525fd"
reviewer: "nan/deepseek-v4-flash"
date: "2026-10-13"
---

## Adversarial review

**Scope**: CORE-001 — a replacement must not drop the lines that follow it (`core/modifier.py` redaction-rect fitter), whole change at `f7b1324`, base `53a6974` (launcher-resolved; `main` not substituted).
**Sources**: `specs/CORE-001/{proposal,tasks,verification}.md` + `features.json`; `git diff 53a697441c2e7f5236ff0ec0d481808d89c62d7a...HEAD`; `git log 53a6974..HEAD`; `backend/tests/unit/core/test_replacement_preserves_following_lines.py`; `backend/scripts/probe_fitter_reachability.py`; `harness/reviewer-pool.json`.

### Spec and task alignment

- **Acceptance criteria.** AC2 (set inclusion, all three replacement sizes), AC3 (synthetic, tight fixture), AC4 (the two following lines present per row) and AC5 (existing suite unchanged) are each carried by a named test I re-ran: `test_no_untouched_line_is_lost`, `test_no_untouched_line_is_lost_when_the_target_line_has_two_spans`, `test_no_untouched_line_is_lost_when_a_neighbour_overlaps_the_target`, `test_no_character_of_the_value_survives_a_sub_character_overlap`, and — for the fail-loud side — `test_a_collapsing_fit_raises_instead_of_redacting_the_raw_rect` and `test_a_target_that_cannot_be_identified_is_refused_not_trimmed_unguarded`. AC1 (RED first) cannot be re-verified from history and the spec says so honestly: `ae28471` is a squash merge, `1c0ae90` is not an ancestor of HEAD. The RED is instead reproducible as a neutralisation, and I reproduced one: fitter neutralised → **25 failed / 3 passed**, the 3 being the single-object control (round 5 recorded 21/3 on the then-24-row file; the file is now 28 rows, consistent).
- **No test was deleted or weakened.** The diff adds one test file and touches no existing test — the retention bar has nothing to rule on.
- **Verified evidence (re-run fresh, this session):**
  - `uv run pytest -q --no-cov` → **409 passed, 19 skipped** (matches `features.json` f6).
  - the regression file alone → **28 passed** (matches f3).
  - probe, `PYTHONPATH=scripts uv run pytest tests/ -q --no-cov -p probe_fitter_reachability` → **`PROBE {'fits': 125, 'refused_trims': 15, 'unidentified': 1, 'collapsed': 1, 'identified_misses': 1}`** — an exact match to `verification.md`, and the only collapse/unidentified fits are the guard's own stub rows.
  - `M5` refusal neutralised → **2 failed / 26 passed**; `M6` floor back to `0.15` → **1 failed / 27 passed** — both exactly as recorded, so the newest layer is pinned by named tests in both directions.
  - `ruff check`, `ruff check --select C901 --config lint.mccabe.max-complexity=10`, `mypy --strict` on `modifier.py` → clean.
  - End-to-end through the real entry point: `uv run pdf-mod modify` on a 12 pt-on-9 pt block → **exit 1, a one-line `Error: Cannot fit the redaction rectangle … whose characters would be removed and not re-inserted.`, no traceback, no output file created**. The new fail-loud policy is real user-facing behaviour, and it degrades cleanly.
- **The fitter's central measurement re-checked independently.** The code's `GLYPH_COVERAGE_FLOOR = 0.12` rests on the claim that `apply_redactions` needs ~10.0% of the character box on **both** axes. I re-measured the predicate (`/tmp/probe_pred.py`): at 100% width, height fractions 0.15/0.12/0.10 remove the glyph and 0.07/0.05/0.01 do not; the same holds at 50% width. So the predicate really is an AND of both axes at ~0.10, and `_reaches_glyph` with 0.12 is **not lax** — no residue can survive behind it. This closes the question that mattered most: a laxer check here would have re-opened the round-3 Major.
- **Disclosed boundaries, not defects against this change.** The co-located/shared-ink case (a label drawn in the target's ink can lose the characters the rect covers, silently) is deliberate, pinned by `test_a_label_sharing_the_target_ink_loses_exactly_the_shared_characters`, and ticketed as CORE-003 (`#199`); the pre-spec behaviour for the same shape was equal or worse. Page re-parsing per rectangle is measured and ticketed as CORE-005 (`#202`). Both are out of scope per ADR-014 condition 3.
- **Scope.** The diff's `modifier.py` + one test file + spec + three `docs/lessons/` entries match the proposal. The range also contains release automation (`.release-please-manifest.json` / `pyproject.toml` / `server.json` / `CHANGELOG.md`, `a1b6056`) which is release-please's, not this spec's authoring; its declared versions agree at `1.9.2`, but it left `backend/uv.lock` behind (finding 5).
- **UNVERIFIED.** I did not re-run `make check` as one command, so the **84.88% coverage figure is the author's, not mine** (ruff/mypy/pytest parts were each run separately and pass). I did not run `mutmut`. Rotated text and a real (non-synthetic) receipt corpus remain untested here, as `verification.md` already states.
- No `[AGENT-DRAFT]` / `[AGENT-SUGGESTION]` tag remains in any contract file (the only grep hits are earlier reviews *reporting* their absence).

### Findings

| Severity | Reality | Area | Finding | Evidence | Test (named, or UNTESTED) | Fix location (code / tests / spec / vault) |
|----------|---------|------|---------|----------|---------------------------|---------------------------------------------|
| Minor | THEORETICAL | correctness / availability | The 0.12 floor is stricter than the redactor's measured 0.10 transition, so a candidate covering a glyph by 10–12% is refused although the redactor would act. Because a refusal can now raise, the margin can turn a document that would have converted into a hard failure. | My re-measurement of the predicate (0.10 removes, 0.07 survives, both axes); `verification.md`'s own sweep shows lowering the floor to 0.10 still loses 12/9, so the margin is not the cause of any *needed* refusal — but no fixture demonstrates a document where 0.10 converts safely and 0.12 refuses. | `test_a_slightly_tight_block_is_still_fitted_without_losing_anything[10pt-on8pt]` (I verified `M6` floor→0.15 turns it red) | no action required; if wished, a corpus measurement or a CORE-004 (`#201`) note — not code |
| Minor | THEORETICAL | reliability | `_refuse_trim_that_drops_another_line` raises on `other.intersects(trimmed)` without applying the redactor's own 10% rule, so a sub-threshold sliver of a neighbouring line's box raises a document-level failure although none of that line's characters would be removed. | Code read of `_refuse_trim_that_drops_another_line` + my measured 10% predicate; no fixture at that boundary (the tight-block rows use unambiguous overlaps). | UNTESTED | tests (a stub-page row at a 5%-overlap neighbour), then code if the boundary is judged worth narrowing |
| Minor | THEORETICAL | correctness | Target identification is `next(span for span in spans if bbox.contains(centre))`, so with two spans containing the centre the extraction order decides whose glyphs are protected. I could not weaponize it: a misidentified span that lies to the left has its own glyphs cut by the same x-trim, which refuses it, so I found no path to silently surviving text. | Code read; attempted construction (a same-band stamp spanning the centre) refuses rather than losing the value. Already recorded by round 4's first signer. | UNTESTED | code + tests — already ticketed as CORE-004 (`#201`), not a new finding |
| Minor | REAL | toolchain | `backend/uv.lock` still records the editable package at `1.9.1` while `pyproject.toml` declares `1.9.2`: the release bump updated the manifest, `pyproject.toml` and `server.json` but not the lock. Any `uv run`/`uv sync` silently rewrites the tracked lock (it rewrote mine during this review), and a lock-strict command fails. | `uv lock --check` → `error: The lockfile at 'uv.lock' needs to be updated`, exit 1; `grep -A2 'name = "pdf-modifier"' uv.lock` → `version = "1.9.1"`; I reproduced the rewrite by running `uv run pytest` (then reverted it). CI is unaffected because `.github/workflows/ci.yml` and the `Makefile` call plain `uv run`/`uv sync --all-extras`. | UNTESTED (no test guards lock/pyproject parity) | code (run `uv lock`, ideally from release automation) — outside the contract set |
| Minor | REAL | spec artifact | `proposal.md`'s acceptance-criteria checkboxes are all still `- [ ]` although `features.json` marks f1–f10 `verified` and every criterion has a passing named test. | Read of `proposal.md`; `features.json` states. | n/a (spec artifact) | spec — **declined here**: editing `proposal.md` after this verdict invalidates the verdict the archive depends on. Record the criteria-by-test mapping in `verification.md` instead. |

No Blocker and no REAL Major was found; the five findings above are tracked, not blocking. Two are REAL, and both are Minor: the stale lock and the unticked criteria are toolchain/spec-artifact drift, neither of which a user of the modifier can observe.

### Evaluator rubric

| Dimension | Grade (A-D) | Rationale (one line) |
|-----------|-------------|----------------------|
| Correctness        | B | Every acceptance criterion is met and the negative shapes (two-span line, overprint, sliver, collapse, tight leading) are covered; the two THEORETICAL boundaries above remain open. |
| Verification       | A | Every load-bearing number I re-ran reproduced exactly — 409-pass suite, 28-row file, `PROBE {125,15,1,1}`, `M5` 2/26, `M6` 1/27, fitter-off 25/3 — plus the predicate independently re-measured. |
| Scope              | B | `modifier.py` + one regression file + spec + lessons match the proposal; the range additionally carries release-please version bumps whose declared versions agree at `1.9.2` but left `uv.lock` stale (finding 5). |
| Reliability        | B | The new refusals are fail-loud, layer-caught (CLI/MCP/API/batch citations all check out) and leave no half-written file — I reproduced the CLI path; the theoretical over-refusal paths are the residual gap. |
| Maintainability    | A | Six ≤17-line helpers, CC ≤ 10 verified with `ruff C901` at `max-complexity=10`, `mypy --strict` clean, and docstrings that state why each invariant exists and which review round it came from. |
| Handoff-readiness  | A | Spec triad current, three `docs/lessons/` entries added, remaining work filed as CORE-003/004/005 + CI-004, and the historical RED's absence from master stated rather than papered over. |

### Verdict

PASS

### Recommended next steps

Everything below is **outside the contract set** (`proposal.md`, `tasks.md`, `features.json`); do not edit those three, or this verdict goes stale.

- **Do not tick `tasks.md`'s round-5 box (or `proposal.md`'s AC boxes) on the strength of this review without checking the gate first.** `dotf spec archive` measures staleness against the contract files; SDD-042's rule is to ignore checkbox ticks, but if this repo's gate compares raw file hashes, a tick invalidates the review it was meant to record. Confirm with a dry run, or accept the ticked-box drift and keep this verdict.
- **Relaunch the second signature against `f7b1324`**: `dotf spec review CORE-001 --second`. `proposal.md` declares `risk: high`, and the existing `review-second.md` was signed at `a479628` with different contract digests (`features.json` `e2ab91…`, `tasks.md` `e07ea3…` vs the current `700d71…` / `ded4b6…`), so it is stale and the archive gate will not accept it as the second signature. This review is the first signature, from another vendor (`deepseek`), so the Anthropic second signer is admissible.
- **Record in `verification.md`** (excluded from the staleness check): this round's verdict and that the contract set was untouched by it; plus the four findings with a disposition line each — applied, ticketed, or declined with a reason.
- **Regenerate `backend/uv.lock`** (finding 5): `cd backend && uv lock`. One line, outside the contract set; ideally fold it into release-please so the next bump cannot leave it behind, and consider a CI parity check (`uv lock --check`) — that is a follow-up ticket, not this spec.
- **Optionally** add the sub-threshold-refusal row (finding 2) to CORE-004 (`#201`) as a test-only follow-up; and note that the fitter's over-refusal cost is now the thing to measure if a real-corpus run ever becomes available.
- `dotf spec archive CORE-001` is advisable once the fresh second signature is signed PASS; the spec is otherwise in an archivably consistent state.
