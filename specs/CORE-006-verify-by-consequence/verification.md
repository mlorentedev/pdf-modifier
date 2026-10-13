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
- [x] **AC7 — CORE-001's `features.json` f9.** `f9` is `verified` with its range corrected to the leadings CORE-001 pinned (0.75/0.78 em, commit `29fe2f6`), so the condition AC7 names holds. What remains is its carve-out prose: it still describes the sub-0.72 em range as a **silent** loss that converts, which this check has since made a refusal. A second review found that at `47a9ca0`; it belongs to CORE-001's contract and is corrected in CORE-001's own archive step, **before** its reviews run, so the review reads the corrected text. Recorded here so the hand-off is not silent.
- [x] **The accepted loss is reported, not silent** (`#199`'s decision): `test_the_accepted_co_located_loss_is_reported_as_a_warning` — the CORE-003 fixture converts, and `ModificationResult.warnings` names the object whose characters went with the redaction.

## Test status

- `uv run pytest tests/unit/core/test_replacement_preserves_following_lines.py -q --no-cov` -> **46 passed**
- `uv run pytest tests/unit/core -q --no-cov` -> **219 passed, 11 skipped**
- `make check` -> **427 passed, 19 skipped**, `ruff check` and `mypy --strict` clean (the coverage figure was 85.27 % before the multi-page row below; a first review measured 85.31 % and was right)
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

## Mutation matrix

Each row neutralises one thing and counts the tests that notice. Run by a first review at `4b5d9b4` (`nan/qwen3.8-flash`) and re-run here for M7, which this revision added; a mutation that turns nothing red is a claim nothing checks.

| # | Mutation | Rows red | What it shows |
|---|---|---|---|
| M1 | `_check_no_other_object_lost_characters` -> immediate `return` | **7** (8 after the two-replacement row; see the second-round matrix) | The consequence check is load-bearing: three sweep rows, the 0.60 em row, the planted-loss row, the warning row and the page-naming row all go red. It is not decoration beside the fitter. Six at `4b5d9b4`; a second review measured seven at `47a9ca0`, when the page-naming row existed, and re-running here confirms the larger count is the current one. |
| M2 | `_refuse_trim_that_drops_another_line` -> no-op | **2** | CORE-001's refusal guard is pinned by both params of `test_a_tight_block_is_refused_rather_than_losing_the_line_below`. |
| M3 | `_same_line` threshold 0.9 -> 0.5 | **4** | The 90 % band is pinned, including by the 0.60 em row. |
| M4 | `_same_line` -> `False` (never accept) | **18** | The accept-list is what keeps documents converting: refusing every co-located loss fails 18 rows. This is the cost of getting the boundary wrong in the strict direction. |
| M5 | `GLYPH_COVERAGE_FLOOR` 0.12 -> 0.20 | **2** | The floor's upper bound, via `test_a_slightly_tight_block_is_still_fitted_...`. |
| M6 | `GLYPH_COVERAGE_FLOOR` 0.12 -> 0.02 | **5** | The floor's lower bound: below it, glyphs the redactor acts on are left uncovered. |
| M7 | The refusal names page 1 unconditionally | **1** | `test_the_refusal_names_the_page_that_holds_the_loss` is the ONLY row that can see it, because every other row in the file is one page. Re-run here: `1 failed, 42 passed`. |

## What this revision added on top of the reviewed one

`4b5d9b4` was the reviewed head. This revision adds `test_the_refusal_names_the_page_that_holds_the_loss` (with its fixture), the M7 number above, this section, the provenance note below, and the corrected test ids in `features.json` that the review found non-existent. Those are the only changes, and the review that follows is at this head.

## Provenance of the reviewed range

This branch carries two specs. `git log 01624dee..HEAD -- backend/src/pdf_modifier/core/modifier.py` shows five commits rewriting the trim heuristics -- `1daac30`, `981bdc1`, `d0d43d4`, `afe11d4`, `29fe2f6`, 282 lines -- and those belong to **CORE-001**, which is the spec that opened this file under ADR-014's exception and whose acceptance criteria they satisfy. CORE-006's own commit is `4b5d9b4` (+119, the check and its rows). The range also carries `#204` (`scripts/check-dependabot-alerts.py`) and `#207` (CI-001's `tasks.md`), which are separate PRs stacked on the same branch for the same reason: they were the pieces that unblocked this one. AC6's "nothing opportunistic in the diff" therefore has to be read per commit, and this is the list.

## The guard's visibility ends at glyphs

`apply_redactions(images=PDF_REDACT_IMAGE_NONE)` keeps the default `graphics` behaviour, so a redaction can still cost **line art** (a rule, a border, a chart line) and this check cannot see it: it compares text, and text is what it promises. That is a declared limit, not an oversight -- `proposal.md` scopes to text objects -- but it belongs in writing rather than in the reader's inference. Filed with the other visibility questions in `#202`'s neighbourhood, not fixed here.

## The second signature's REAL Major, and what fixing it uncovered

The second signer (`anthropic-review/claude-sonnet-5-5`) FAILED this spec with one REAL Major and three Minors. The Major was real, reproduced, and fixed here.

**The finding.** The co-located exemption asked whether *any* target on the page shares the lost object's line (`any(_same_line(target, box) for _, target in redactions)`) instead of whether the rectangle that TOOK the glyph belongs to a target on that line. So an unrelated replacement elsewhere on the lost line downgraded a refusal to a warning -- and the warning then said "its ink is drawn in the same place" about an object sharing ink with nothing.

**Reproduced exactly** (`LOST_LINE_TARGET` at 72, `LOST_LINE_NEIGHBOUR` at 72 on the next line, `LOST_LINE_BYSTANDER` at 250 on the neighbour's line, Helvetica 12 pt at 7.2 pt = 0.6 em leading):

```
replace {VALTHREE: X}              -> REFUSED  would lose 8 character(s) of another text object at (72.0, 66.3, 136.0, 82.8)
replace {VALTHREE: X, VALFOUR: Y}  -> CONVERTED ['X', 'Y'], warnings=['page 1: 8 character(s) ... because its ink is drawn in the same place']
```

`KEEPKEEP` is gone from the second output and the warning blames co-location. Two replacements on one page is the normal case; the one-replacement fixtures could not see it.

**The fix.** `_lost_characters` now returns the glyphs' KEYS, so the check knows where each vanished character was drawn; `_co_located_redaction_took` accepts a loss only when a rectangle that **removes** that glyph has a target on the lost object's line; and `_dispose_of_lost_characters` requires **every** lost character to be accounted for that way, so an object cannot be half-excused through the middle of the span. New row: `test_a_second_replacement_on_the_lost_line_does_not_excuse_the_loss` (RED first: `DID NOT RAISE`).

**Fixing it uncovered a second defect, in the predicate.** Attribution first used `_reaches_glyph`, which is the TRIM's safety predicate (the measured 10.0% transition plus a margin, `GLYPH_COVERAGE_FLOOR = 0.12`). Attribution asks what the redactor DID, and the redactor's own rule is the measured fraction with no margin. Asking the trim's question refused `backend/tests/data/sample.pdf` page 1 -- caught by the integration suite (`test_regex_replacement`), not by any unit row. Two constants now exist, each with the question it answers: `GLYPH_REMOVAL_FRACTION` (0.10, measured) for what happened, `GLYPH_COVERAGE_FLOOR` (0.12) for what is safe.

**And a third: a rewrite drops what no rectangle reached.** With attribution fixed, the same document still refused -- for a **space**. Inspected: the lone whitespace-only span between `Visa` and `ending in 3777` disappears when PyMuPDF rewrites the line it touches, with a **zero-width overlap against every rectangle on the page**. `_lost_characters` therefore does not count whitespace: the promise is that *content* does not vanish, and refusing a convertible document over a space is not a refusal the user can act on. Both directions are pinned (`test_a_vanished_space_is_not_a_lost_character`, `test_a_vanished_letter_is_a_lost_character`).

## Mutation matrix, second round

Added to the M1-M7 above, all measured on the code this revision ships. The tree was restored after each.

| # | Mutation | Rows red | What it shows |
|---|---|---|---|
| M1 | the check -> immediate `return` | **8** | Was 7; the new two-replacement row goes red too. |
| M8 | drop "this rectangle REMOVES the glyph" (the bug the second signer found) | **1** | Exactly and only `test_a_second_replacement_on_the_lost_line_does_not_excuse_the_loss` -- the row is aimed at the defect, and no other row pretends to cover it. |
| M9 | drop "the rectangle's target is on the lost line" | **7** | The other half of the attribution is pinned by the sweep, the planted loss and the page-naming rows. |
| M10 | count whitespace again | **1** | Only the whitespace row sees it, in the direction that matters: a dropped space must not refuse a document. |

## Checkbox and evidence drift, and why it needed no re-review

Both reviews found `proposal.md`'s acceptance-criteria boxes still `[ ]` while `tasks.md` and `features.json` said the work was done. It is drift, not missing work, and it is fixed here rather than left open: `contract_digest.go` normalises list-checkbox state before digesting -- *ticking `- [ ]` to `- [x]` is progress and a review whose own finding was "tick the boxes" does not invalidate itself* (`#998` part 2) -- so ticking them leaves both reviews fresh against the same contract content. The same normalisation covers `features.json`'s `state` and `evidence`, which are harness-written progress rather than contract. Nothing else in the contract set was edited: no criterion was reworded, no task added.

## Open finding, tracked not absorbed

The first review's one Major: "accepted co-located" is decided by the **vertical band** (`_same_line`, 90 % of the shorter box) rather than by whether the lost glyph was genuinely unreachable, so a same-line neighbour whose characters a rectangle *could* have spared is warned instead of refused. Reproduced as a *shape*, not as an avoidable loss -- and the only instance the review found on a real document (`frontend/e2e/fixtures/eval-doc.pdf` page 2) is a **whitespace span**, the `' '` between `Page` and `Two`, inspected here: it costs no visible content.

Not fixed here, deliberately: deciding unavoidability per glyph is a new prediction about geometry -- the thing ADR-015 demoted the fitter away from -- and it changes which real documents convert, so it needs its own fixture, its own ADR-014 justification and its own review. The loss is *reported* in every case, which is the promise ADR-015 actually makes. Filed as **CORE-007 (`#209`)** with the fix options and the evidence; the review classified it Major / **THEORETICAL** and its verdict admits the archive with the gap tracked.

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

- [x] Lesson for the repo's `docs/lessons/`? yes, two: `docs/lessons/lesson-028-a-guard-you-cannot-check-is-a-guard-you-cannot-trust.md` and `docs/lessons/lesson-029-attribute-a-loss-to-the-thing-that-caused-it.md` (the second from the second signature's Major).
- [x] ADR-worthy decision for `docs/adr/`? yes: `docs/adr/adr-015-refuse-rather-than-lose.md` — the policy this spec implements (loud refusal over silent loss; the accepted co-located case reported rather than silent) constrains every future change to the fitter, so it is recorded as a decision with the trade-off and the rejected alternatives, not as a property of one file.
- [x] New pattern candidate for `00_meta/patterns/`? no: the transferable half is the lesson above. The geometry, the tooling and the fixture shapes are repository-specific, and the pattern catalogue already carries the general form under the verification patterns.

## Archive checklist

- [ ] `proposal.md` frontmatter set to `status: archived`
- [ ] Folder moved: `specs/CORE-006-verify-by-consequence/` -> `specs/archive/CORE-006-verify-by-consequence/`
- [ ] Bitácora board ticket for this spec moved to Done / closed with PR link (ADR-018)
- [ ] Promotions above executed (if any)
