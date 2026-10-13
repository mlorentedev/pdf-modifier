---
spec: "CORE-001"
verdict: "PASS-WITH-GAPS"
reviewed_sha: "e2071e453d0f1bce93ba16254fc81ae6f7f5ed32"
reviewer: "anthropic-review/claude-sonnet-5-5"
date: "2026-10-13"
---

## Adversarial review

**Scope**: CORE-001 (#179), the whole change `53a697441c2e7f5236ff0ec0d481808d89c62d7a...HEAD` (`e2071e4`). This is the second signature, because `proposal.md` declares `risk: high`. I did not read `review.md`, the earlier round files or any transcript.
**Sources**: `specs/CORE-001/{proposal,tasks,features.json,verification}.md`, `docs/adr/adr-014`, `adr-015`, the diff of `backend/src/pdf_modifier/core/modifier.py`, and `backend/tests/unit/core/test_replacement_preserves_following_lines.py`.

### Spec and task alignment

- **The fix holds.** The acceptance criterion is that no line present in the input is missing from the output, and it holds in everything I ran.
  - I rotated the receipt fixture to 0, 90, 180 and 270 degrees. The base commit loses `ARC`, `CVM` and the target line; HEAD loses only the target.
  - I built text drawn with `rotate=90` at 11, 13 and 16 pt leading. At 11 pt the base loses `ROW3`, `VALUE300`, `END3`, `ROW5`, `VALUE500` and `END5` as well as the target. HEAD loses only `VALUE400`.
- **No silent regression in the fuzz.** I fuzzed base against HEAD on synthetic pages: random fonts and sizes, 4 to 12 lines, label and value spans in two colours, varied line lengths, and leading from 0.6 to 1.6 em.
  - Across about 1100 runs HEAD had no silent neighbour loss.
  - HEAD never refused a page the base converted without loss, apart from the watermark case in finding 3.
  - Refusals appear only at leading of 0.7 em or less. All 124 of them were pages where the base silently dropped lines. At 0.8 em and above nothing was refused.
- **The shared-ink superscript and watermark cases stay accepted.** HEAD reports them through `ModificationResult.warnings`, and a warning was present in every such run I inspected.
- **Evidence matches what the spec records.** `uv run pytest -q --no-cov` gives **433 passed, 19 skipped**. `ruff check`, `ruff check --select C901` at max complexity 10, and `mypy --strict src` are clean.
- **Stale claims in the spec files.**
  - `features.json` f6 says "431 passed", but the suite now has 433.
  - f6 also says "No pre-existing test is modified", yet the range modifies `tests/unit/rename/test_no_stale_project_name.py`. That change comes from the already-merged #197.
  - `proposal.md`'s acceptance checkboxes are all unticked while the status is `verifying`.
  - `tasks.md` has a round-6 review item still unticked, and its "Close" section lists the rounds out of order.
  - These are contract-set files, so I am not asking for edits alongside a passing verdict. They are for the implementer to disposition in `verification.md`.
- **ADR-014 condition 1 (failing test first).** The RED commit `1c0ae90` is not in the history, as `tasks.md` itself admits. The repo's own record is that the RED was captured and reproduced, not that it is reachable. I accept that, with the caveat that I cannot verify it from the diff.
- **ADR-014 conditions 2 and 3 (no contract change, scoped).** `core/modifier.py` grows by about 513 lines. The public signatures are unchanged. Behaviour is not unchanged: documents that previously converted lossily now raise `PDFModifierError`. ADR-015 records this as a deliberate policy. I judge it within the ADR-014 exception, but the "no opportunistic refactor" condition is stretched. The CORE-006 consequence check is carried in this branch's diff rather than in a separate change.
- **Diff range includes unrelated work.** The range also carries the Dockerfile, release workflow, Dependabot checker, `glama.json` and CI-001 changes (#187 to #207). The base predates them, so this is a launcher artefact rather than a defect. I did not review those files and they are UNVERIFIED.

### Findings

| Severity | Reality | Area | Finding | Evidence | Test (named, or UNTESTED) | Fix location |
|----------|---------|------|---------|----------|---------------------------|--------------|
| Major | THEORETICAL | tests / target identification | The "best match" branch of `_target_span` is not pinned by any test. Every test fixture builds a rect equal to a span's bbox, so the `other == rect` early return always fires. The production path for replacing a word inside a line (rect smaller than the span) uses the IoU scoring, and it has no coverage. In a scratch worktree I replaced `_overlap_ratio(rect, other)` with `1.0 if rect.intersects(other) else 0.0`, so the first intersecting span wins, which is the pre-f11 behaviour. The full suite still gave 433 passed. Mutating `if score > best_score` to `... and False` fails one test. Mutating `if union <= 0` survives. I could not demonstrate harm on my probes, because the consequence check backstops a wrong identification, so this is THEORETICAL. | Mutant survives the entire suite. | UNTESTED. `test_a_large_object_behind_the_text_does_not_decide_whether_the_page_converts` covers only the identical-bbox path. | tests: add a case where the rect is a sub-rect of a span and a watermark or a longer span precedes it in order |
| Major | THEORETICAL | tests / accepted-loss policy | The `all(...)` in `_dispose_of_lost_characters` is not pinned. The docstring says that accepting an object because some of its characters were co-located "would readmit the defect through the middle of the span". Mutating `all(` to `any(` leaves all 52 tests green. The implementation is correct. The invariant it guards has no test that fails if it regresses. | Mutant survives the file, 52 passed. | UNTESTED. `test_a_second_replacement_on_the_lost_line_does_not_excuse_the_loss` pins which rectangle is blamed, not all-versus-any. | tests: one object losing characters to two rectangles, one co-located and one not, must refuse |
| Minor | REAL | policy / usability | A document with a large light object (a "DRAFT" watermark) crossing a line that is replaced is now refused when the geometry falls under the same-line test, where the base converted it. Reproduced with fuzz seeds 162 and 289: the target line's overlap with the 30 or 60 pt watermark box was below 90% of the shorter height, so `_same_line` is false and the loss is classed as another line. The base silently dropped the watermark glyphs in those pages too, so ADR-015's refuse-rather-than-lose applies. The same page shape with a slightly different vertical offset (seed 160) converts and warns. The outcome flips on a 90% threshold, the user has no override, and the message says "no fitted rectangle spares it", which is not true of an object whose ink is merely behind the line. | Seeds 160, 162, 289 of `/tmp/fuzz.py`. | UNTESTED at the threshold. `test_the_watermark_page_reports_the_same_loss_in_both_span_orders` covers one geometry. Mutating `shorter * 0.9` to `0.99` survives. Mutating it to `0.3` fails 6. | code/tests: pin the boundary, or document it in ADR-015 as a known cliff |
| Minor | REAL | performance | The cost is about 7x the base on a dense page: 60 replacements in an 840-span page took 0.67 s against 0.09 s for the base. The per-rectangle loop over all spans and the glyph index make it quadratic-ish. The spec ticketed it as CORE-005 (`#202`, still OPEN) and measured a similar figure, so it is disclosed. | `/tmp/perf.py` | none, and it is not a correctness property | follow-up CORE-005 |
| Minor | REAL | maintainability | `modifier.py` goes from 674 to 1181 lines. The `PDFModifier` class was already over the repo's 250-line class threshold and now has about 17 new static helpers (geometry, glyph indexing, three refusal builders). Function complexity is fine (ruff C901 at 10 passes). The fitter and the consequence check are self-contained and could live in a sibling core module without changing the public API. | `wc -l`; diff | not applicable | code (follow-up refactor, deliberately not in this ADR-014 change) |
| Minor | REAL | spec artifacts | Stale numbers and claims in `features.json` f6 (431 against 433 passed, "no pre-existing test modified"). Unticked acceptance boxes and an unticked round-6 task. | See "Spec and task alignment". | none | spec (`verification.md` disposition; these files are in the contract set, so they are not edits to request alongside this verdict) |
| Question | n/a | Scope | The diff range includes the Dockerfile, `release.yml`, `check-dependabot-alerts.py`, `docker-build.yml` and 9 lessons. All of it belongs to already-merged master PRs (#187 to #207), and I did not review it. Please confirm this is a base-resolution artefact and not part of CORE-001's claimed scope. | `git log` of the range | not applicable | none |

### Evaluator rubric

| Dimension | Grade (A-D) | Rationale (one line) |
|-----------|-------------|----------------------|
| Correctness        | B | The fix holds under rotation and ~1100 fuzz pages; failure is loud and every refusal I inspected had a base-version loss behind it. |
| Verification       | B | The RED matrix is strong, and 8 of 8 consequence-check mutants fail the suite. The IoU identification and the `all` invariant survive mutation. |
| Scope              | B | The diff matches the fix and the refuse-rather-than-lose policy it adopted; the extra range is merged-master noise, not this branch's. |
| Reliability        | B | Errors are typed and name the page and the object. Warnings surface the accepted shared-ink loss. The refusal cliff at the 90% same-line test has no override. |
| Maintainability    | C | A 500-line core addition in an already-oversized class, with its own helper cluster. CC is fine but the class threshold is far exceeded. |
| Handoff-readiness  | B | The spec, ADR-015, lessons and the verification trail are present. Stale counts remain, and the tasks and proposal ticks are out of date. |

### Verdict
PASS WITH GAPS

No Blocker. The two Majors are THEORETICAL, with no demonstrated harm, so under `severity x reality` they cannot force a FAIL. The Maintainability grade of C keeps the verdict from being a clean PASS.

### Recommended next steps

All of these are outside the contract set. The implementer should disposition them (apply, ticket or decline) in `verification.md` or a follow-up ticket. None needs an edit to `proposal.md`, `tasks.md` or `features.json`.

- Add a test where the replaced rect is a sub-rect of a span and a watermark or longer span precedes it. Name it so it kills the surviving `_overlap_ratio` mutant.
- Add a test with one object losing characters to two rectangles, one co-located and one not, that must refuse. It kills the `all` to `any` mutant.
- Pin the `_same_line` 0.9 boundary with a named case on each side, or record the cliff in ADR-015 as accepted. Consider a user-visible way past a refusal, which is a CORE-00x-class decision and not part of this change.
- Track the class and module size as a follow-up refactor.
- Correct the stale counts and ticks in `verification.md`.
- `dotf spec archive` is advisable once the first signer's verdict stands and the implementer has dispositioned the above.
