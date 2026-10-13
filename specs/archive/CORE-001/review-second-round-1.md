---
spec: "CORE-001"
verdict: "FAIL"
reviewed_sha: "a479628598c7c4f780720212c29d22adec8d83fd"
reviewer: "anthropic-review/claude-sonnet-5-5"
date: "2026-10-13"
---

## Adversarial review

**Scope**: CORE-001 (`risk: high`), second signer. Diff `53a697441c2e7f5236ff0ec0d481808d89c62d7a...HEAD` (HEAD `a479628`).
**Sources**: `specs/CORE-001/{proposal,tasks,features.json}`, `backend/src/pdf_modifier/core/modifier.py`, `backend/tests/unit/core/test_replacement_preserves_following_lines.py`, `backend/scripts/probe_fitter_reachability.py`. I did not read `review.md`, its transcript or the `review-round-*.md` files.

### Spec and task alignment
- The proposal's three rows (same width / same width / 4 chars) are covered, plus the two-span, overlap and sliver rows added later. I ran them: **24 passed** in the file, **405 passed / 19 skipped** for the whole backend suite, `ruff check` and `mypy --strict src` clean.
- The central claim is "a replacement must not drop the lines that follow it, with no reliance on length, width or content". It holds for the fixture geometry (9 pt font, 11 pt leading, ratio 1.22). It does **not** hold for tighter blocks. That is the finding below, and it is the same defect class on a different leading.
- ADR-014 conditions: public signatures unchanged, `analyzer.py` untouched, no refactor. Held.
- Tasks: the `[ ]` boxes for review rounds 3 and 4 are stale, since those rounds happened. Cosmetic. `tasks.md` is in the contract set, so it is not a reason to edit anything now.
- Working tree: `specs/CORE-001/verification.md` was modified, uncommitted, by something other than me during this run (a "Round 5" section). I did not touch it. It is outside the contract set but is not in the reviewed diff.

### Findings

| Severity | Reality | Area | Finding | Evidence | Test (named, or UNTESTED) | Fix location |
|---|---|---|---|---|---|---|
| **Major** | **REAL** | core/modifier.py `GLYPH_COVERAGE_FLOOR`, `_is_safe_trim` | **The 15% floor refuses legitimate trims, and the refusal silently destroys the neighbour.** With the target line sandwiched between two overlapping neighbours, each single trim is accepted, but the combined rect is thin. The next trim is then refused because it would leave the target under 15% of glyph height, and that neighbour is redacted without being re-inserted. Repro (this session, Courier-Bold, one text object per line, replace `TARGET3` with `ZZZZ`): font 12 / leading 9 gives `keepkeep4` -> `p4`. Font 9 / leading 7 and font 10 / leading 8 give the same. Output of the first: `[keepkeep0, keepkeep1, keepkeep2, p4, keepkeep5, keepkeep6, keepkeep7, ZZZZ]`. With `GLYPH_COVERAGE_FLOOR = 0.0`, all three cases keep every neighbour and still erase `TARGET3`. The boundary is leading/font about 0.8 (0.83 passes, 0.79 and 0.78 fail). The floor's own docstring claims "being stricter than the redactor costs a refused trim, and a refused trim only leaves the rectangle where it was". That is false: leaving the rectangle where it was is exactly the original defect, and it is silent. I measured the redactor's height transition in this session: 8% leaves the glyph, 10% removes it, for font 9 and 12. The height transition matches the width one, so 0.15 is over-strict on height. This is a different mechanism from the "shared ink" policy: here the trim is geometrically fine and only the floor vetoes it. Strictly better than the base commit (the base loses `keepkeep2` and `keepkeep4`), but it is the spec's defect, reproduced, outside the tested geometry. | `_is_safe_trim` returns False -> `_fit_redaction_to_its_own_text_object` keeps the previous rect -> neighbour intersected -> `apply_redactions` removes it. Reproduced via `PDFModifier.process`, ad-hoc scripts in `/tmp` (not committed). | **UNTESTED.** Mutating the floor to 0.5 leaves all 24 tests green, so no named test pins the floor from above. Only mutations toward `intersects` or 0.0 are caught (13 failed at 0.0). | code + tests. Add a tight-leading row (ratio 0.75-0.8) to the regression file. Then either derive the floor from the measured 10% (plus margin) per axis, or, when a trim is refused for insufficient coverage and the neighbour still intersects the rect, raise `PDFModifierError` like the collapsed case instead of continuing. Re-review after the fix. |
| Minor | REAL | tests / spec: refusal cost claim | `probe_fitter_reachability.py` counts only `collapsed` and `unidentified`. It does not count refused trims, which is the path that causes the Major above. The "refusal costs nothing in practice" evidence therefore cannot see the one refusal that costs content. | Script read. | UNTESTED | tests/script, `verification.md` |
| Minor | REAL | performance | Redaction fitting re-parses the whole page with `rawdict` for every rect (O(N x spans)). Measured on an 840-span page: 70 matches took **1.35 s** vs **0.10 s** at the base commit; 840 matches took **18.8 s** vs **4.2 s**. `verification.md` acknowledges the cost, but only measured 40-60 replacements. | `/tmp/rv/perf.py`, run at HEAD and at `53a6974` | UNTESTED | code (parse once per page, pass spans in) |
| Minor | REAL | hygiene | `ruff format --check` fails on `test_replacement_preserves_following_lines.py` (three wrapped `assert ... , msg` forms). `.pre-commit-config.yaml` runs `ruff-format`, so the hook will rewrite or reject it. `make check` does not catch it. | `uv run ruff format --check src tests scripts` -> "Would reformat" for this file | n/a | tests (format) |
| Minor | THEORETICAL | `_fit_redaction_to_its_own_text_object` | The target is the *first* span whose bbox contains the rect centre (`next(...)`), so with two containing spans (overprint or a stamp) the span order decides whose glyphs are protected. Also, `_trim_away_from` assumes horizontal text; my 90-degree-rotated block happened to pass, so the risk is untested rather than demonstrated. | Code read. Rotated 6-line block: only the target changed. | UNTESTED (the ticketed two-candidate case is not in the suite) | code + tests |
| Question | n/a | scope | Is a leading/font ratio below 0.8 in scope? The proposal says "tight page" and uses thermal-receipt data. A 12 pt font at 9 pt leading is plausible on such printers. If the owner declares it out of scope, the Major becomes a documented limit, but the code comment must stop claiming a refusal is harmless. | n/a | n/a | spec / `verification.md` |

### Evaluator rubric

| Dimension | Grade (A-D) | Rationale (one line) |
|---|---|---|
| Correctness | C | Fixture shapes and all acceptance rows pass; a tight-leading shape still silently truncates a neighbour (`keepkeep4` -> `p4`). |
| Verification | C | Strong mutation matrix, but the floor is not pinned from above (0.5 passes all 24) and the reachability probe cannot see refused trims. |
| Scope | A | Diff matches the proposal; public API and `analyzer.py` untouched; one regression file and one probe script. |
| Reliability | B | Collapsed and unidentified fits fail loudly, a good call; the floor-veto path fails silently. |
| Maintainability | B | Helper decomposition is reasonable and documented; a false comment on the floor and a per-rect page re-parse remain. |
| Handoff-readiness | B | Lessons and a follow-up ticket (CORE-004) exist; the `verification.md` claims about refusal cost are over-stated. |

### Verdict
**FAIL**: one REAL Major (a reproduced silent loss of a neighbouring line's content, on the defect class this spec exists to close), UNTESTED, with a code-and-tests fix location. No Blocker and no D grade. The fix and its test are outside the contract set, so the next round needs no spec edit unless the owner answers the scope question by changing `proposal.md`.

### Recommended next steps
- **Code + tests (outside the contract set):** add the tight-leading rows (font 12 / leading 9, font 9 / leading 7, font 10 / leading 8; assert set inclusion and that no value fragment survives). Watch them fail, then fix. Options: lower the floor to the measured 10% transition plus a small margin, applied per axis. Or make a veto-by-coverage with an intersecting neighbour raise like the collapsed case, so it fails loudly instead of damaging silently. Add a test that fails when the floor is raised well above the measured transition (e.g. 0.5).
- **Code:** correct the `GLYPH_COVERAGE_FLOOR` comment, which claims a refused trim is harmless. Parse the page once per page instead of once per rect, or record why it is acceptable at 840 matches.
- **Tests/tooling:** run `ruff format` on the regression file. Extend the probe to count refused trims.
- **`verification.md`** (outside the set): record the disposition of each finding, including the Question above.
- `dotf spec archive` is **not advisable** at this head. After the fix a fresh review round is needed. The second signature is the one required by `risk: high`.
