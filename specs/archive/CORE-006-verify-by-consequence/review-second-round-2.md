---
spec: "CORE-006-verify-by-consequence"
verdict: "PASS-WITH-GAPS"
reviewed_sha: "5e3599762d19b81a6a73896e1bcf52aa5bbe6dd8"
reviewer: "anthropic-review/claude-sonnet-5-5"
date: "2026-10-13"
---

## Adversarial review

**Scope**: CORE-006-verify-by-consequence, `git diff 01624dee3bc417bd0688b183778781674b4c8a9f...HEAD` (34 files, whole union: CORE-001's trim rewrite, the consequence check, #204, #207, lessons, ADR-015).
**Sources**: `specs/CORE-006-verify-by-consequence/{proposal,tasks,verification}.md`, `features.json`, `backend/src/pdf_modifier/core/modifier.py`, `backend/tests/unit/core/test_replacement_preserves_following_lines.py`, `docs/adr/adr-015-*.md`. I did not read `review.md` or any transcript of the first signer.

Commands run at `5e35997` (all fresh):
- `uv run pytest -q --no-cov` -> 427 passed, 19 skipped. `ruff check`, `mypy --strict` on modifier.py, and `ruff format --check` on both touched files all clean.
- Independent fuzz, with ground truth taken from a per-page character multiset of the PDFs and no use of the modifier's own comparison:
  - 3 x 400 random multi-line, multi-span, multi-font pages with 1-3 replacements: 0 silent losses at HEAD. The base commit lost characters silently on 77/400 and 90/400 pages of the same seeds.
  - On the same seed, HEAD refused only pages the base converted with a silent loss (57 refused, all of them base-silent). I found no false refusal.
  - The 193 single-word replacements across the 4 real PDFs in the repo converted with nothing lost.
  - Rotated text, a rotated page, and a multi-page document (the loss on page 2 is named as page 2) all behave.
  - 500 pathological pages of overlapping lines at mixed sizes: 0 silent losses. 140 were converted with a warning and 248 refused.
- Mutation edits, each reverted (`git status` clean for `backend/` afterwards): see the findings table.

### Spec and task alignment
- AC1 (0.45-1.30 em, refuse-or-preserve, read from the file), AC2 (existing documents still convert), AC3 (planted loss fires) and AC4 (names page and object, no output written) are met and reproduced by the commands above. Neutralising the check turns 8 rows red in `tests/unit/core` (M1).
- AC6 (cost): the check itself is ~free. I measured 1.62 s with it and 1.63 s with the call removed on an 840-span / 70-match page. The same page takes **1.26 s on the base commit and 1.63 s at HEAD**. That +29% comes from CORE-001's per-rectangle `rawdict` parse and glyph work, which this diff also carries. The verification states "+3 %" for the check, which is true, but the union's cost against the base is not stated anywhere. See finding 5.
- AC8 is ticked `[x]`, but CORE-001's `features.json` f9 still says the sub-0.72 em range converts and loses lines **silently** and is "NOT fixed here". That is false after this change. `verification.md` admits it, and `tasks.md` leaves "tick f9 and archive CORE-001" unticked. The criterion's first alternative ("claim holds over the full range") is not what shipped, and the second ("range corrected") was done only for the range, not the prose. The hand-off is disclosed, so I record it as a gap and not as a lie.
- Proposal wording vs behaviour: "There is no third outcome" is not literally true. The code has two: a **warned conversion with loss** (co-located, expressly allowed in the proposal's Risks) and a **vanished whitespace span is not counted** (not in the proposal; justified in verification and ADR-015). Both are documented, but the Why/What prose overstates.
- No `[AGENT-DRAFT]` / `[AGENT-SUGGESTION]` tags found in the spec files.

### Findings

| Severity | Reality | Area | Finding | Evidence | Test (named, or UNTESTED) | Fix location |
|----------|---------|------|---------|----------|---------------------------|--------------|
| Major | THEORETICAL | tests / warnings | The target-object exemption in `_check_no_other_object_lost_characters` (`if any(span is target ...): continue`) and the choice of `_target_span` for it are pinned by **no test**. With the exemption removed (`if False: continue`) the whole suite is 427 passed, and so is the 46-row file. The shipped behaviour is correct (`sample.pdf`, replace "Visa": `warnings == []`). Under the mutant every ordinary replacement emits a false "its ink is drawn in the same place" warning. Replacing the exemption's target lookup with "first span containing the rect centre" (the order-dependent identification CORE-001 round 4 fixed) also leaves all 223 `tests/unit/core` tests green. The only warnings assertion in the file is the positive one at line ~719. | Mutations M13 and M14, run here. | UNTESTED. Needs a row that asserts `warnings == []` for an ordinary conversion and for the watermark page in both span orders. | tests |
| Minor | REAL | repo hygiene | `.gitignore` ignores `specs/*/review-transcript.jsonl*` but not the second signer's `review-second-transcript.jsonl` / `.stderr`. `git status` shows both untracked at this moment. This is the same 2.5 MB accidental-staging hazard the new comment says it removes. | `git status --short` | UNTESTED (no test for ignore rules) | repo (`.gitignore`) |
| Minor | REAL | spec artifacts | CORE-001 f9 (behavior and evidence) is stale: it claims a silent loss below 0.72 em, which this spec turned into a refusal, while CORE-006's AC8 is ticked. | `specs/CORE-001/features.json` f9; `tasks.md` last open task | n/a (prose); behaviour covered by `test_no_leading_in_the_ailing_range_loses_characters_silently[...]` | spec: CORE-001's own archive step (outside CORE-006's contract set) |
| Minor | THEORETICAL | classification | "Co-located" is decided by a 90% vertical band, not by unavoidability. In 500 pathological overlapping-size pages 140 converted with a warning. I could not show that any of them was avoidable, so this is the already-tracked CORE-007 (#209), and I am not escalating it. No silent loss occurred. | fuzz4 run: `warned_with_loss` 140, `SILENT` 0 | `test_the_accepted_co_located_loss_is_reported_as_a_warning` covers the shape, not avoidability. UNTESTED for the avoidable subset. | code + tests (CORE-007) |
| Minor | REAL | cost / verification | The stated cost (+3%, "extra cost of the check") is correct for the check, but the same conversion is +29% slower than at the base commit (1.26 s -> 1.63 s), and the cost of the diff as a whole is not recorded. | `/tmp/cost.py` on 840 spans / 70 matches, base vs HEAD vs HEAD-without-check | n/a (no perf test) | spec artifacts (`verification.md`), possibly CORE-005 |
| Minor | THEORETICAL | scope | The union carries ~3.2k added lines; the executable core change of this spec is about 120 LOC. The rest is CORE-001's trim rewrite, #204, #207 and spec bookkeeping. This is disclosed per commit in `verification.md`, but AC5 ("nothing opportunistic") can only be judged per commit. | `git log 01624dee..HEAD`, `git diff --stat` | n/a | spec artifacts (already disclosed) |
| Question | n/a | glyph key | The glyph key `(char, x0 rounded to 0.1, y0 rounded to 0.1)` is last-writer-wins on duplicates (overprint). I measured kept-glyph drift as 0.0 across ~10k glyphs, and rounding at 1 vs 3 decimals made no difference to the 46 rows, so there is no evidence of a rounding-boundary false refusal. Confirm that the tracked CORE-007 covers duplicate keys. | drift probe | UNTESTED | none |

### Evaluator rubric

| Dimension | Grade (A-D) | Rationale (one line) |
|-----------|-------------|----------------------|
| Correctness        | A | 0 silent losses in 1,200 fuzz pages plus 500 pathological ones, against 20-22% silent loss at the base; no false refusal found |
| Verification       | C | Check-fires and range sweeps are strong, but two of the check's load-bearing branches (target exemption, target identification) survive mutation and no row asserts "no spurious warning" |
| Scope              | C | The union mixes CORE-001, #204, #207 and spec bookkeeping with the ~120-LOC check; disclosed, but significant |
| Reliability        | B | Refusal reuses the typed error, names page and object, and writes no output; web returns 400, CLI exits 1; the check adds no measurable runtime |
| Maintainability    | B | Helpers are small and named for the question they answer; `ruff` and `mypy --strict` are clean; no new function near CC 10 |
| Handoff-readiness  | B | ADR-015 and lessons 028-029 added and limits stated; CORE-001 f9 prose and the CORE-001 archive step are left open, disclosed |

### Verdict
PASS WITH GAPS

No Blocker and no REAL Major. The one open Major is a THEORETICAL test gap, and the rubric has two Cs and no D.

### Recommended next steps
(All routed outside the contract set: `proposal.md`, `tasks.md` and `features.json` need no edit for this verdict. Disposition each in `verification.md`: applied, ticketed, or declined with a reason.)
- **Tests** (finding 1): add a row asserting `warnings == []` for a plain single replacement and for the watermark page in both span orders. Confirm it turns red under M13 (drop the target exemption) and M14 (order-dependent target lookup).
- **Repo** (finding 2): add `specs/*/review-second-transcript.jsonl*` to `.gitignore`.
- **CORE-001 hand-off** (finding 3): rewrite f9's prose and evidence as part of CORE-001's archive step, before its review runs, as `verification.md` already plans.
- **Spec artifacts** (finding 5): record the base -> HEAD cost (1.26 s -> 1.63 s on 840 spans / 70 matches, mine) beside the check's own +3%, and give the rawdict cost to CORE-005 (#202).
- Keep CORE-007 (#209) open with the duplicate-key question above.

`dotf spec archive` is advisable once the first signer's review also passes. The gaps are tracked and none is a contract-set edit.
