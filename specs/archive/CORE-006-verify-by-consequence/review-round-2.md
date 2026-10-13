---
spec: "CORE-006-verify-by-consequence"
verdict: "PASS-WITH-GAPS"
reviewed_sha: "47a9ca0a1a30c83f9ee75fb6898906d9ad10a8b5"
reviewer: "nan/mimo-v2.6-flash"
date: "2026-10-13"
---

## Adversarial review

**Scope**: `CORE-006-verify-by-consequence` — `git diff 01624dee3bc417bd0688b183778781674b4c8a9f...HEAD`, whole range (27 files, +2788/−68), head `47a9ca0`.
**Sources**: `specs/CORE-006-verify-by-consequence/{proposal,tasks,verification,features}.md`, `specs/CORE-001/{features,verification}.md`, `backend/src/pdf_modifier/core/modifier.py`, `backend/tests/unit/core/test_replacement_preserves_following_lines.py`, `docs/adr/adr-015-refuse-rather-than-lose.md`, `scripts/check-dependabot-alerts.py`, `backend/scripts/probe_fitter_reachability.py`. This is round 2; `review-round-1.md` (at `4b5d9b4`) was read as provenance, not as evidence — every number below was produced fresh at `47a9ca0`.

### Spec and task alignment

- **The mechanism matches the proposal.** `_apply_replacements_to_page` captures `_text_spans(page)` before redaction, applies `apply_redactions(images=PDF_REDACT_IMAGE_NONE)` + re-insertion, then `_check_no_other_object_lost_characters` re-reads the page and diffs it glyph-by-glyph (`(char, round(x0,1), round(y0,1))`). A non-target object on another line raises `PDFModifierError` with `{page, object, characters}` and no output file; a co-located one appends to `ModificationResult.warnings` (which reaches CLI `cli.py:171`, MCP docs, and web via `result.model_dump()` — `models.py:124`). One redaction path only, so no bypass around the check.
- **AC1 reproduced directly.** My own probe on the tight-block fixture: 0.45/0.60/0.70 em → `REFUSED … would lose 9 character(s) of another text object`; 0.83 em → `CONVERTED missing=[]`. The sub-0.72 em silent loss that motivated the spec is gone: refuse-or-preserve at every leading I drove.
- **AC2/AC3/AC4/AC5 verified by run.** The target file is **43 passed**; planted loss (`test_a_planted_loss_is_caught_by_the_consequence_check`) refuses and writes nothing; the new `test_the_refusal_names_the_page_that_holds_the_loss` proves `details["page"] == 3` on a three-page document (round-1's coverage gap, closed); `make check` → ruff `All checks passed!`, mypy `Success: no issues found in 31 source files`, **424 passed, 19 skipped, coverage 85.31 %** — matching `verification.md` exactly.
- **AC6 corroborated a third time.** My probe (900 spans, 75 matches, best of 5): **+0.012 s (+2.0 %)** with vs without the check, beside the claimed +0.08 s (+3 %) and round-1's +0.7 %. Same order; the check does not double the conversion.
- **AC7 is met on its named-range branch, with a residue.** `specs/CORE-001/features.json` f9's range was corrected to 0.75/0.78 em and its verification command passes (inside the 43/424 runs). Two factual errors remain in the recorded artifacts (findings 3 and 4 below); neither is in CORE-006's contract set.
- **AC-ADR-014 conditions hold**: RED is recorded with the exact failure (`['keepkeep2', 'keepkeep4']`), the existing typed error is reused, no public contract changed, and the check's rows are the diff's own code.
- **All six `features.json` verification commands now run clean** — round-1's phantom test ids (f1, f5) were corrected: f1+f2+f3+f5 → **11 passed**, f4 → 43 passed, f6 → 424 passed.
- **Round-1 findings dispositioned**: mutation matrix recorded (with one staleness, finding 2); provenance section names CORE-001's five trim commits + #204/#207; multi-page row added and pinned by M7; the text-only visibility limit and the band-vs-unavoidability limit are now stated in ADR-015; the open Major is ticketed as **CORE-007 (#209), which I confirmed is OPEN** via `gh issue view`.
- **No `[AGENT-DRAFT]` / `[AGENT-SUGGESTION]` tags** in any spec file. No test was deleted: the one removed `def test_` line in the range is a signature rename of `test_no_untouched_line_is_lost`, which still exists at line 169; retention bar not applicable.
- **Mutation spot-checks I ran (tree restored after each; `git status` clean):**
  - **M1** `_check_no_other_object_lost_characters` → `return`: **7 red** — the three sweep rows (0.45/0.60/0.70), the 0.60 named row, planted loss, warning row, *and the new page-naming row*. The check is load-bearing at this head.
  - **M7** `_dispose_of_lost_characters` names page 1 unconditionally: **1 failed, 42 passed** — exactly as `verification.md` records; only `test_the_refusal_names_the_page_that_holds_the_loss` can see it.

### Findings

| Severity | Reality | Area | Finding | Evidence | Test (named, or UNTESTED) | Fix location |
|----------|---------|------|---------|----------|---------------------------|--------------|
| Major | THEORETICAL | accept-list precision | (carried from round 1) "Accepted co-located" is decided by shared vertical band (`_same_line`, ≥90 % of the shorter box), not by whether the lost glyph was genuinely unreachable — a same-line neighbour whose characters a rectangle *could* have spared is warned instead of refused. Mechanism unchanged at `47a9ca0`; round-1's only real-document instance (`eval-doc.pdf` p2) was a whitespace span, so no observed content loss. | `modifier.py:_dispose_of_lost_characters` `co_located = any(_same_line(target, box) …)`; round-1 repro carried as provenance | Warn path: `test_the_accepted_co_located_loss_is_reported_as_a_warning`. Refusal of an avoidable same-band loss: **UNTESTED** | Tracked, not fixed: **CORE-007 (#209)** (confirmed OPEN) — disposition in `verification.md` |
| Minor | REAL | verification accuracy | The new mutation matrix's **M1 row is stale for this head**: it records **6 red**, measured at `4b5d9b4` before the page-naming row existed. At `47a9ca0` M1 gives **7 red** (adds `test_the_refusal_names_the_page_that_holds_the_loss`). The claim it supports (check is load-bearing) is only strengthened. | my M1 run: FAILED list = sweep×3 + 0.60 row + planted + warning + page row | the seven rows named in the M1 run | `verification.md` (outside contract set — update 6 → 7) |
| Minor | REAL | verification accuracy / AC7 | `verification.md` AC7 says f9 is "Still `pending` at this head on purpose"; at the reviewed sha `specs/CORE-001/features.json` f9 `state == "verified"` (touched in `29fe2f6`, before round 1's head). The recorded statement is false as written. | json read at HEAD + `git show 4b5d9b4:specs/CORE-001/features.json` → `verified` | n/a | `verification.md` (outside contract set — correct the sentence) |
| Minor | REAL | spec accuracy (CORE-001 contract) | CORE-001 f9's carve-out now **understates** current behaviour: its prose says below 0.72 em "the loss is **SILENT**" and its evidence says "it converts and loses lines", but at this head those leadings **refuse** via the consequence check. AC7's named-range claim (0.75/0.78 em refused) holds and the range was corrected, so AC7's branch is met; the stale carve-out is what remains for CORE-001's own archive to reconcile. | my sweep probe: 0.45/0.60/0.70 em `REFUSED … would lose 9 character(s)`; 0.83 em converts | `test_no_leading_in_the_ailing_range_loses_characters_silently` (7 params) + my probe | `specs/CORE-001/features.json` — CORE-001's contract, not CORE-006's; disposition at CORE-001's archive (AC7 already names that gate) |
| Minor | REAL | state drift | `proposal.md`'s eight acceptance-criteria checkboxes are all `[ ]` while `tasks.md` is all `[x]` and `features.json` says `state: verified`. Carried from round 1 (F7); unresolved because the contract set is closed under a passing verdict. The archive gate reads `features.json`, so this is drift, not missing work. | my read of `proposal.md` vs `tasks.md` vs `features.json` | n/a | `proposal.md` is contract set: do **not** edit under this verdict — disposition in `verification.md` |
| Minor | SPECULATIVE | glyph-key masking | (carried from round 1) `_glyph_index` is last-writer-wins on `(char, round(x0,1), round(y0,1))`, so co-located identical glyphs collapse to one owner; a loss could be attributed to the allow-listed target or masked by a replacement glyph within 0.1 pt. Requires co-located identical ink, which is warned anyway. | code read at `47a9ca0`; no reproduction | UNTESTED | surface only; do not gate |

Security/quality walk over the diff: no secrets, no shell interpolation (`check-dependabot-alerts.py` uses argv lists, no `shell=`), no auth surface, no unbounded buffers (glyph index is O(page glyphs), transient), core stays sync and thread-offloaded. No HALT-category issue.

### Evaluator rubric

| Dimension | Grade (A-D) | Rationale (one line) |
|-----------|-------------|----------------------|
| Correctness        | B | All eight ACs reproduced at this head (sweep, planted loss, page naming, warning, cost); the accept-list band approximation remains an open THEORETICAL Major, and f9's carve-out prose is stale (CORE-001 side). |
| Verification       | B | Every headline number reproduced (424/85.31 %, 43, M7 1/42, sweep, +2 %); but two recorded statements are wrong at this head — M1's count (6 vs actual 7) and AC7's "still pending". |
| Scope              | A | CORE-006's own commit is exactly the check and its rows; the range's carry (CORE-001's trim rewrite, #204, #207) is now named per commit in `verification.md`, closing round-1's provenance finding. |
| Reliability        | A | One redaction path, typed refusal with page/object/characters, no partial output, multi-page naming proven by a named test, warnings reach CLI/MCP/web. |
| Maintainability    | B | Helpers small and split (`_lost_characters` / `_dispose_of_lost_characters`), WHY-comments; CC claimed at 2–3 for new code but read, not tool-measured, by me as by round 1. |
| Handoff-readiness  | A | ADR-015 states both guard limits, lessons 023/027/028 recorded, open Major ticketed as CORE-007 #209 with evidence, round-1 findings dispositioned in `verification.md`. |

Aggregation: no C, no D → rubric path says PASS. Findings path: one open Major, tagged THEORETICAL and tracked → **PASS WITH GAPS**. No Blocker; no REAL Major.

### Verdict

**PASS WITH GAPS**

`dotf spec archive CORE-006-verify-by-consequence` is **advisable** in this state: `reviewed_sha` is the head examined, the contract set (`proposal.md`, `tasks.md`, `features.json`) was not touched by this review, no `[AGENT-DRAFT]` tag remains, and every open finding above is either a `verification.md` correction (free to edit) or a tracked disposition. The gaps are tracked, not fixed — on a passing verdict the contract set is closed, so findings 4 and 5 are *not* to be fixed by editing `proposal.md` or CORE-001's `features.json` in the same breath as this archive; finding 4 belongs to CORE-001's own archive session, where AC7 already routes it.

### Recommended next steps

All outside CORE-006's contract set, for disposition in `verification.md` or a follow-up ticket:

- **`verification.md` (free to edit)** — correct M1's row to 7 red at `47a9ca0` (or annotate "6 at `4b5d9b4`, 7 after the page row"), and fix AC7's "still pending" sentence: f9 is `verified` with a corrected range as of `29fe2f6`.
- **`specs/CORE-001/` (CORE-001's contract, its own session)** — f9's carve-out prose and evidence still describe sub-0.72 em as a silent, unpinned loss; at this head those leadings refuse. AC7 already says CORE-001 archives only once this is true; this is the remaining half of that criterion. Raise it there, not here.
- **tests (free to edit, future round or follow-up)** — the one test that would retire the open Major: a same-line neighbour whose glyphs sit outside the fitted rectangle, expecting refusal. Until it exists the Major stays THEORETICAL; CORE-007 (#209) is the right home.
- **follow-up, not this diff** — `features.json` f6's cost figure (+3 %) could cite a third measurement (+2.0 % here, +0.7 % round 1); optional, all three agree on order of magnitude.
- **UNVERIFIED at the deadline** — the CORE-001 mutation-matrix re-run ticked in `tasks.md` (round 1 also did not reach it), and cyclomatic complexity of the new helpers was read, not tool-measured.
