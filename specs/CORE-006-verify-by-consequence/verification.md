---
tags: [spec, verification]
created: "2026-10-13"
---

# Verification - CORE-006-verify-by-consequence

## Evidence

Each acceptance criterion from `proposal.md`, with the proof produced in this session. Every number below was re-run here, not carried over.

- [x] **AC1 — refuse-or-preserve over 0.45-1.30 em, no silent loss.** `test_no_leading_in_the_ailing_range_loses_characters_silently` (7 leadings, read from the written file) plus the named row `test_a_block_at_060_em_leading_is_refused_or_preserved`. Behaviour sweep on the same shapes:
  ```
  cobo 12/5.4   (0.45 em): REFUSED   Replacing text on page 1 would lose 5 character(s) of another text object...
  cobo 12/7.2   (0.60 em): REFUSED
  cobo 12/8.4   (0.70 em): REFUSED
  cobo 12/9.0   (0.75 em): REFUSED   (the fitter's own guard, as before)
  cobo 12/9.96  (0.83 em): converted, lost=none
  cobo 12/12.0  (1.00 em): converted, lost=none
  cobo 12/15.6  (1.30 em): converted, lost=none
  helv 11/4.95  (0.45 em): REFUSED
  helv 11/6.6   (0.60 em): REFUSED
  helv 11/7.7   (0.70 em): REFUSED   (the fitter's own guard)
  helv 11/9.9   (0.90 em): converted, lost=none
  helv 11/13.2  (1.20 em): converted, lost=none
  ```
- [x] **AC2 — the documents that converted still convert.** All 32 pre-existing rows pass unchanged (`test_replacement_preserves_following_lines.py`: 42 passed), including the two-span receipt line, the three overprint shapes, the sub-character-overlap rows, 10 pt-on-8 pt, 12 pt-on-10 pt, and the watermark page in both span orders. No false refusal was introduced: that was the failure mode of the first implementation attempt, caught by these rows.
- [x] **AC3 — the check fires on a planted loss.** `test_a_planted_loss_is_caught_by_the_consequence_check`: the fitter is monkeypatched to return the raw, unfitted rectangle (CORE-001's original defect) and the conversion refuses, naming the object it protected, with no output file written.
- [x] **AC4 — the refusal names the page and the object, and writes nothing.** Same row: `details = {page, object, characters}`, and `not out.exists()`.
- [x] **AC5 — ADR-014 conditions.** A failing test came first (below), no public contract is changed (`PDFModifierError` is reused, `ModificationResult.warnings` already existed), and the diff is the check and its rows — the trim heuristics are untouched.
- [x] **AC6 — the extra cost measured.** 840 spans, 70 matches, best of 5 runs each: **2.95 s with the check against 2.87 s without, i.e. +0.08 s (+3 %)**, against CORE-005's measurement of the per-rectangle parse at 1.35 s for the same match count on a similar page. The check adds one page read per page and one glyph index comparison; it is small next to the parse CORE-005 tracks.
- [x] **AC7 — CORE-001's `features.json` f9.** Still `pending` at this head on purpose: f9's claim spans a range this spec makes true, but f9 lives in CORE-001's contract and is ticked by CORE-001's own archive step (its `tasks.md` carries that task). Recorded here so the hand-off is not silent.
- [x] **The accepted loss is reported, not silent** (`#199`'s decision): `test_the_accepted_co_located_loss_is_reported_as_a_warning` — the CORE-003 fixture converts, and `ModificationResult.warnings` names the object whose characters went with the redaction.

## Test status

- `uv run pytest tests/unit/core/test_replacement_preserves_following_lines.py -q --no-cov` -> **42 passed**
- `uv run pytest tests/unit/core -q --no-cov` -> **219 passed, 11 skipped**
- `make check` -> **423 passed, 19 skipped, coverage 85.27 %**, `ruff check` and `mypy --strict` clean
- `ruff format --check …modifier.py …test_replacement_preserves_following_lines.py` -> clean, under BOTH the venv's ruff and the pinned hook (the two disagree elsewhere in the repository: CI-004, `#203`)
- No regressions: the pre-existing rows were not modified; the only edits to existing code are `missing_untouched_lines` gaining an optional `replaced` argument (see below, where its absence caused a false RED) and `_apply_replacements_to_page` gaining the before/after capture.

### RED, before any implementation

```
$ uv run pytest tests/unit/core/test_replacement_preserves_following_lines.py -q --no-cov
6 failed, 36 passed
FAILED ...::test_no_leading_in_the_ailing_range_loses_characters_silently[12.0pt-on7.2pt]
FAILED ...::test_no_leading_in_the_ailing_range_loses_characters_silently[12.0pt-on8.4pt]
FAILED ...::test_a_block_at_060_em_leading_is_refused_or_preserved
E   AssertionError: lines lost with no error at 0.60 em leading: ['keepkeep2', 'keepkeep4']
FAILED ...::test_a_planted_loss_is_caught_by_the_consequence_check
FAILED ...::test_the_accepted_co_located_loss_is_reported_as_a_warning
```

The two rows that must fail for the *right* reason did: `['keepkeep2', 'keepkeep4']` is the loss the second signer reproduced, printed by the row itself. The planted-loss row and the warning row fail because neither the check nor the warning exists yet.

## Decisions made during implementation

- **The comparison unit is the GLYPH, keyed by (character, position rounded to 0.1 pt).** Chosen before the code was written, as `tasks.md` requires, because this is where CORE-001's rounds 2 and 3 both went wrong. Rejected alternatives, with the reason each one fails:
  - *Compare extracted lines of text*: `get_text()` assembles lines from spans, so an object that survived partially comes back as a shorter object and a lost character inside a line reads as "a line changed"; the same confusion produced a PASS on a document that had lost two lines in an earlier round.
  - *Match objects by index or by text*: the redaction rewrites the runs it touches, so the surviving part of the target's object is re-emitted (sometimes split differently), and the target's own text is the one thing that is *supposed* to change. Index matching renumbers; text matching cannot describe a replacement.
  - *Ask which rectangle covered the missing glyph*: trivially true — the redactor only removes glyphs it reaches — so it asserts nothing. The discriminator has to be *intent*: the object the analyzer asked to replace, versus every other object on the page.
- **The accepted co-located case is decided by shared vertical extent, not by the rect's centre.** `_same_line` compares the vertical overlap of the two boxes against the shorter of them (>= 90 %). The centre test is what the fitter used and what the second signer broke: below 0.7 em leading the *next line's* box contains the centre, so a neighbour was treated as the object being replaced. Same-line co-location (a label under a value, a watermark crossing a line) is accepted and warned (`#199`); anything on another line refuses.
- **A false RED was caught in the first run of the new rows.** The sweep reported losses at 1.00 em and 1.30 em, where the fitter is provably safe. The cause was reused test machinery, not the code: `missing_untouched_lines` hard-coded the payment fixture's replaced line (`AC:  68D...`), so a fixture whose target line reads only the value reported its own replacement as a dropped line. `replaced` is now an argument, and the RED above is the corrected one. Recorded because "the row failed" is not evidence until the reason is the intended one.
- **The first implementation over-refused and the pre-existing rows caught it**, which is the argument for AC2 existing at all. The first version classified any object the rectangle reached as accepted; it now classifies by line, so a neighbour line that loses characters refuses instead of warning its way through.
- **`_check_no_other_object_lost_characters` came out at CC 11** against the repo's `< 10` rule, and was split into `_lost_characters` + `_dispose_of_lost_characters`. New helpers are at CC 2-3; the file's worst offenders (`_find_matches_in_merged` CC 12, `_process_pages` CC 11, `_collect_replacements` CC 10 / nesting 4) are pre-existing and deliberately untouched here.
- **The two ruff versions disagree about this repository's code, and CI-004 is now reproduced three ways.** (1) The venv's ruff (0.15.5) wants to reformat `backend/tests/unit/harness/test_reviewer_pool_contract.py`, a file this branch does not touch, while the pinned hook (v0.8.6) accepts it. (2) Every `assert condition, "message"` that wraps gets restructured in *opposite* directions by the two versions: the commit hook rewrote two of this file's asserts one way, the venv's ruff then demanded the other, and whichever runs last is what the file looks like. (3) The same disagreement is invisible to `make check`, which runs neither formatter. Resolved here by **hoisting the conditions into locals** so short lines leave both versions with nothing to disagree about, and verified with both tools (`ruff format --check` clean, `pre-commit run ruff-format` Passing) rather than by picking a side. The disagreement itself stays open in CI-004 (`#203`): until the versions are pinned together, the same construct can be reformatted back and forth by two tools that are both 'the formatter'.

## Promotion candidates

- [x] Lesson for the repo's `docs/lessons/`? yes: `docs/lessons/lesson-028-a-guard-you-cannot-check-is-a-guard-you-cannot-trust.md`
- [x] ADR-worthy decision for `docs/adr/`? yes: `docs/adr/adr-015-refuse-rather-than-lose.md` — the policy this spec implements (loud refusal over silent loss; the accepted co-located case reported rather than silent) constrains every future change to the fitter, so it is recorded as a decision with the trade-off and the rejected alternatives, not as a property of one file.
- [x] New pattern candidate for `00_meta/patterns/`? no: the transferable half is the lesson above. The geometry, the tooling and the fixture shapes are repository-specific, and the pattern catalogue already carries the general form under the verification patterns.

## Archive checklist

- [ ] `proposal.md` frontmatter set to `status: archived`
- [ ] Folder moved: `specs/CORE-006-verify-by-consequence/` -> `specs/archive/CORE-006-verify-by-consequence/`
- [ ] Bitácora board ticket for this spec moved to Done / closed with PR link (ADR-018)
- [ ] Promotions above executed (if any)
