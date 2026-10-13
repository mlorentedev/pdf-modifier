---
spec: "CORE-006-verify-by-consequence"
verdict: "PASS-WITH-GAPS"
reviewed_sha: "65d2eef2335123ab1783079233cdec651c06638a"
reviewer: "nan/deepseek-v4-flash"
date: "2026-10-13"
---

## Adversarial review

**Scope**: `CORE-006-verify-by-consequence` — whole range `git diff 01624dee3bc417bd0688b183778781674b4c8a9f...HEAD`, head `65d2eef` (33 files, `core/modifier.py` +483, one test file +810). This is round 3; `review-round-1.md` (`4b5d9b4`, PASS-WITH-GAPS) and `review-round-2.md` (`47a9ca0`, PASS-WITH-GAPS) were read as provenance only — every number below was produced fresh at `65d2eef`. `review-second.md` (`anthropic-review/claude-sonnet-5-5`, **FAIL** at `e6a418c`) was also read, because the fix under review is the one it demanded.
**Sources**: `specs/CORE-006-verify-by-consequence/{proposal,tasks,verification,features}.md`, `specs/CORE-001/features.json`, the full `core/modifier.py` diff, `docs/adr/adr-015-refuse-rather-than-lose.md`, `backend/tests/unit/core/test_replacement_preserves_following_lines.py`.

Run in this session, tree clean apart from this file:
- `uv run pytest -q --no-cov` -> **427 passed, 19 skipped** (matches `verification.md`).
- `uv run pytest tests/unit/core/test_replacement_preserves_following_lines.py -q --no-cov` -> **46 passed** (this is where `features.json` is stale; see F3).
- `uv run ruff check` on `modifier.py` + the test file -> **All checks passed**; `uv run mypy --strict src/pdf_modifier/core/modifier.py` -> **Success**.
- Four mutations, each patched in and reverted (tree verified clean afterwards): M1 `_check_no_other_object_lost_characters` returns immediately -> **8 red**; M8 drop the `_removes_glyph` half of attribution -> **1 red**; M9 drop the `_same_line` half -> **7 red**; M10 count whitespace again -> **1 red**. All four reproduce `verification.md`'s matrix exactly.
- The second signer's Major, reproduced end to end through `PDFModifier.process` (`/tmp/rv3/repro.py`, Helvetica 12 pt / 7.2 pt = 0.6 em, `VALTHREE` / `KEEPKEEP` / `VALFOUR`):
  `{VALTHREE: X}` -> REFUSED; `{VALTHREE: X, VALFOUR: Y}` -> **REFUSED** (was CONVERTED with `KEEPKEEP` gone and a false-reason warning at `e6a418c`). The verdict no longer depends on an unrelated second replacement.
- **Not reached (UNVERIFIED here)**: the second signer's ~2000-page random fuzz; the CORE-005 cost measurement; `backend/tests/data/sample.pdf` and the integration suite beyond `-q --no-cov` (which does include them: 427 passed).

### Spec and task alignment
- AC1/AC2/AC3/AC4/AC5/AC6 hold with named, reproducible evidence; AC7 holds by its own disjunction (`f9`'s named range corrected to 0.75/0.78 em) with a residual prose drift carried as F4.
- `tasks.md`: the implemented boxes are ticked; the two unticked boxes (CORE-001 f9/archive, this spec's archive) are accurately unticked. No `[AGENT-DRAFT]` or `[AGENT-SUGGESTION]` tags in any spec file.
- The proposal's "no third outcome" sentence is true again at this head for the multi-replacement case the second signer broke — that was my first reproduction and it now refuses.
- Fitter invariant vs. spec: `proposal.md`'s allow-list ("the replacement itself, and any object whose ink the replacement's rectangle cannot avoid covering") is implemented as *co-located on the same line*, which is a proxy, not the property. That gap is F1, tracked, not silent.
- The trim heuristics are still not "untouched" in the *range*: five commits (`1daac30`..`29fe2f6`, 282 lines) rewrite them. They belong to CORE-001 and are declared in `verification.md`'s Provenance; CORE-006's own commit `4b5d9b4` leaves them alone. Read as F6.

### Findings

| Severity | Reality | Area | Finding | Evidence | Test (named, or UNTESTED) | Fix location |
|----------|---------|------|---------|----------|---------------------------|--------------|
| Major | THEORETICAL | `_same_line` / accepted-loss boundary | "Co-located" is decided by shared vertical extent (`_same_line`: vertical overlap >= 90% of the shorter box), not by whether the lost characters were genuinely unreachable. A same-line neighbour whose glyphs a trim *could* have spared is therefore **warned, not refused** — widest case: `_is_safe_trim` refuses any trim below `GLYPH_COVERAGE_FLOOR = 0.12` while the redactor acts at `GLYPH_REMOVAL_FRACTION = 0.10`, so a trim covering a target glyph by 10-11.9% is refused, and a same-line neighbour that a 10-11.9% trim would have spared is then redacted and only reported. Not reproduced: no fixture constructs an *avoidable* same-line loss; the only real-document instance any round has found is a whitespace-only span (`frontend/e2e/fixtures/eval-doc.pdf` p2, `' '` between `Page` and `Two`), which costs no content. | code read of `_same_line`, `_is_safe_trim`, `_refuse_trim_that_drops_another_line`; `verification.md` "Open finding, tracked not absorbed"; prior reviews' classification Major/THEORETICAL | UNTESTED — no row asserts refuse-or-preserve for an avoidable same-line loss | code + tests (tracked as CORE-007 / #209; needs its own ADR-014 fixture) |
| Minor | REAL | Accepted-loss reporting surfaces | "Accepted is not silent" holds only where a consumer reads `ModificationResult.warnings`: the SvelteKit frontend never reads it, and the CLI batch table prints only `replacements_made` with status `OK`. The user of those two surfaces sees a converted document and no report. | `grep -rn warnings frontend/src` (type + test fixture only); batch loop in `cli.py`; ADR-015's own corrected sentence names both surfaces | UNTESTED on those surfaces (the unit row proves the list is populated, not that a consumer shows it) | ticket (CORE-008 / #210). Outside the contract set |
| Minor | REAL | `features.json` evidence counts | The evidence text is stale against this head: `CORE-006-f4` says "43 passed in the file" where 46 pass; `CORE-006-f6` says "424 passed, 19 skipped" where the suite is 427 passed, 19 skipped. The criteria are unaffected; the recorded proof numbers are not the ones that run. | my runs above; `features.json` F4/F6 evidence | n/a (claim-vs-run) | `features.json`'s `evidence` field — folded by `contract_digest.go` before digesting, so correcting it does not stale this review; `verification.md` if the file is left alone |
| Minor | REAL | CORE-001 `f9` prose (AC7 residual) | `f9`'s named range was corrected to 0.75/0.78 em, so AC7's disjunction is met — but its carve-out still asserts that below ~0.72 em the loss is **SILENT** and the document converts, which this change falsified: it now refuses. The statement now understates instead of overstating. Declared in `verification.md` and routed to CORE-001's own archive step before its reviews run. | `specs/CORE-001/features.json` f9 `behavior`; `verification.md` AC7 bullet; the refusal behaviour reproduced in `/tmp/rv3/repro.py` | UNTESTED (no row reads `f9`'s prose) | CORE-001's contract (a different spec's set), not this one's |
| Minor | SPECULATIVE | `_glyph_index` keys | The key `(char, round(x0,1), round(y0,1))` maps one owner per key, so an exact overprint (same character, same rounded origin, two spans) has its earlier owner overwritten by the later one. If the later span is the target, a co-located object sharing those glyphs is exempt from both refusal and warning. Not constructed, not observed. | code read; flagged by the second signer and dispositioned into #209 | UNTESTED | tests (an exact-overprint row), or key by `(owner, char, pos)` — #209 |
| Question | n/a | Second signature / archive gate | `proposal.md` declares `risk: high`, so `dotf spec archive` requires a **second** signature. The only second signature on disk (`review-second.md`) is a **FAIL** signed at `e6a418c`, i.e. *before* the fix `65d2eef`; there is no passing second signature at this head. This review is the primary and cannot stand in for it. | `review-second-request.json` (`reviewed_sha: e6a418c`); `review-second.md` frontmatter; `git log` shows `65d2eef` after it | n/a | process — relaunch `dotf spec review CORE-006-verify-by-consequence --second` at this head |
| Question | n/a | Scope of the reviewed range | The range is the union of four stacked pieces: CORE-006, CORE-001's trim rewrite (282 lines), `scripts/check-dependabot-alerts.py` (#204), CI-001's docs (#207), plus `.gitignore`. `verification.md` declares each and attributes it per commit, which is the honest form; AC5's "nothing opportunistic" is defensible read per commit, not as a range. The PR body must carry the same list, since the reviewer's diff is the union. | `git diff --name-status 01624dee...HEAD`; `verification.md` Provenance | n/a | PR body (outside the contract set) |

Strengths that directly mitigate a documented risk (not balance-praise): the check is demonstrably load-bearing (M1 -> 8 red), the new attribution is pinned in both directions by exactly the rows aimed at it (M8 -> 1, M9 -> 7), the whitespace rule is pinned in both directions (M10 -> 1), and the refusal path leaves no output file — all re-measured here, not carried over.

### Evaluator rubric

| Dimension | Grade (A-D) | Rationale (one line) |
|-----------|-------------|----------------------|
| Correctness        | B | The previous REAL Major is fixed and re-verified; the remaining Major is a proxy-for-the-property boundary that is reported rather than silent, and unreproduced. |
| Verification       | B | Every criterion has a named, reproducible command and I reproduced the mutation matrix and the Major fix; two evidence counts in `features.json` are stale and no row covers a multi-replacement page's attribution beyond the one added here. |
| Scope              | B | The check and its rows match the proposal; the stacked CORE-001/#204/#207 content is declared and per-commit attributable, but it is in the reviewer's diff. |
| Reliability        | B | Refusal writes nothing and names page and object (verified); error paths are handled; the accepted loss reaches only some consumers. |
| Maintainability    | B | Lint and `mypy --strict` clean, helpers small (the CC-11 function was split), constants carry their measurement; the trim/fit code is now dense with cross-referenced rationale. |
| Handoff-readiness  | A | ADR-015, four lessons, an explicit open-finding section, promotion candidates and a per-commit provenance table are all present and candid. |

### Verdict
**PASS WITH GAPS**

The reference to the second signer's FAIL is not a defect: F1 is the one open Major, labelled THEORETICAL (no reproduction in any round; the only real instance is a whitespace span), so it is tracked under CORE-007 / #209 and does not move this verdict below passing. `severity × reality`, not severity alone, is the rule applied here.

`dotf spec archive CORE-006-verify-by-consequence` is **not yet advisable** — not because of a code defect, but because `risk: high` needs a passing second signature at `65d2eef` and the one on disk is a stale FAIL (F5). Once that second signature exists, the archive is advisable: the contract set (`proposal.md`, `tasks.md`, `features.json`) was not touched by this review, `reviewed_sha` is the head examined, and no `[AGENT-DRAFT]` tag remains.

### Recommended next steps
On a passing verdict the contract set is closed: do **not** edit `proposal.md`, `tasks.md` or `features.json` alongside this verdict. F3 may still be corrected in `features.json`'s `evidence` field, which `contract_digest.go` folds before digesting, but the safer route is `verification.md`.

1. **Process (blocks the archive, not the code).** Run `dotf spec review CORE-006-verify-by-consequence --second` at `65d2eef`. The existing second signature predates the fix it demanded; a FAIL at an older sha cannot serve as the second signer for a change that has moved.
2. **`verification.md` (outside the contract set).** Disposition each open finding as applied, ticketed, or declined with a reason:
   - F1: already tracked as CORE-007 / #209 — record that this round confirmed the classification and reproduced no avoidable loss.
   - F2: CORE-008 / #210 is filed; state that the ADR-015 sentence was corrected rather than left overstating.
   - F3: correct the two stale counts (46 in the file, 427 in the suite) or note them as drift, the way the checkbox drift was noted.
   - F4: carry it into CORE-001's archive session, where `f9`'s prose is corrected before CORE-001's reviews run.
   - F6: confirm the PR body lists the four stacked pieces, since AC5 is judged against the union.
3. **No code change is required by this review.** F1's fix, if it is ever taken, is a new fixture plus an ADR-014 justification, and it belongs to CORE-007 — not to this archive.
