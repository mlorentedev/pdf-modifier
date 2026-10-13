---
spec: "CORE-006-verify-by-consequence"
verdict: "PASS-WITH-GAPS"
reviewed_sha: "4b5d9b4df27041234cce1f62aa2fc8cf53df356f"
reviewer: "nan/qwen3.8-flash"
date: "2026-10-13"
---

## Adversarial review

**Scope**: `CORE-006-verify-by-consequence` — `git diff 01624dee3bc417bd0688b183778781674b4c8a9f...HEAD` (26 files, +2619/-68), branch head `4b5d9b4`.
**Sources**: `specs/CORE-006-verify-by-consequence/{proposal,tasks,verification,features}.md`, `specs/CORE-001/{verification,features,tasks}.md`, `backend/src/pdf_modifier/core/modifier.py`, `backend/tests/unit/core/test_replacement_preserves_following_lines.py`, `docs/adr/adr-015-refuse-rather-than-lose.md`, `docs/lessons/lesson-023/027/028`. I did not read `review-request.json`'s digest block beyond the base sha, and I did not read any prior `review-round-*.md` as evidence — only as provenance context.

Everything below was run fresh at `4b5d9b4`; the working tree was restored after each mutation (`git status --short src/` clean).

### Spec and task alignment

- **The mechanism matches the proposal.** `_apply_replacements_to_page` captures `_text_spans(page)` before, applies the redactions and the re-insertion, then `_check_no_other_object_lost_characters` re-reads the page and diffs it glyph by glyph (`(char, round(x0,1), round(y0,1))`). A non-target object on another line raises `PDFModifierError` with `{page, object, characters}`; a co-located one appends to `self._warnings`. That is what `proposal.md` "What" and AC5 describe.
- **The claim "nothing fails below ~0.72 em" is no longer true.** Classified the refusal source per leading on the tight-block fixture: 0.45/0.60/0.70 em → the consequence check ("would lose 9 character(s) of another text object"); 0.72/0.75/0.78 em → the fitter's own guard; 0.83/1.00/1.30 em → converts, `warnings=[]`, no line lost. Matches `verification.md`'s sweep exactly.
- **The check is load-bearing, not decorative.** Neutralising it (M1 below) turns 6 rows red — including three sweep rows and the 0.60 em row, which are real geometries, not stubs.
- **AC1–AC7 hold on the evidence I could reproduce.** AC8 (CORE-001 f9) is deliberately still `pending`, and `verification.md` says so; that is the correct disposition, not a gap in this spec — but note `specs/CORE-001/` has `review-round-*.md`/`review-second-round-*.md` and **no `review.md`**, so CORE-001 cannot archive yet regardless.
- **No `[AGENT-DRAFT]` / `[AGENT-SUGGESTION]` tags remain** in `proposal.md`, `tasks.md`, `verification.md`, `features.json`.
- **The proposal's own acceptance-criteria boxes are all still `[ ]`** while `tasks.md` claims `[x]` and `features.json` claims `state: "verified"`. The archive gate reads `features.json`, so this is state-drift in a contract file rather than a missing claim (F7).

### Verification I ran (not read)

| Command | Result |
|---|---|
| `make check` (ruff + mypy + pytest `--cov=src`) | `All checks passed!` · `Success: no issues found in 31 source files` · **423 passed, 19 skipped** · coverage **85.31 %** |
| `uv run pytest tests/unit/core/test_replacement_preserves_following_lines.py -q --no-cov` | **42 passed** |
| `features.json` f1 `…::test_a_sub_half_leading_block_is_refused_or_preserved` | **exit 4** — no such test |
| `features.json` f5 `…::test_the_refusal_names_the_damaged_object_and_writes_no_output` | **exit 4** — no such test |
| Refusal-source classification, tight block, 10 leadings | see above; consequence check fires at 0.45/0.60/0.67/0.70/1.11-em-on-9pt |
| **M1** `_check_no_other_object_lost_characters` → `return` | **6 rows red** (sweep 0.45/0.60/0.70, 0.60 named row, planted loss, warning row) |
| **M2** `_refuse_trim_that_drops_another_line` → no-op | **2 rows red** (both `test_a_tight_block_is_refused_rather_than_losing_the_line_below`) |
| **M3** `_same_line` 0.9 → 0.5 | **4 rows red** (threshold is pinned, incl. `…_at_060_em_…`) |
| **M4** `_same_line` → `False` | **18 rows red** (over-refusal; the accept-list is what keeps documents converting) |
| **M5** `GLYPH_COVERAGE_FLOOR` 0.12 → 0.20 | **2 rows red** (`test_a_slightly_tight_block_is_still_fitted_…` both params) |
| **M6** `GLYPH_COVERAGE_FLOOR` 0.12 → 0.02 | **5 rows red** |
| Multi-page probe (hostile block on page 3 only) | `PDFModifierError` "…on page 3…", `details["page"] == 3`, output file **not** written |
| Real fixtures (`sample.pdf`, `anonymized.pdf`, `price_adjustment.pdf`, `frontend/e2e/fixtures/eval-doc.pdf`), 7 token replacements | all converted, no refusal; **`eval-doc.pdf` page 2 produced a co-located warning** (1 char of the object at `(104.7, 84.9, 109.7, 104.2)`) |
| Cost, 840 spans / 70 matches, with vs without the check | 1.84 s vs 1.83 s → **+0.7 %**; same order as the claimed +0.08 s / +3 % |
| Redaction paths in `src/` | one only (`add_redact_annot` modifier.py:476 → `apply_redactions` :482 → check :487) — no path that redacts and skips the check |
| Do warnings reach the callers? | CLI `cli.py:171`, MCP `model_dump_json`, web `pdf.py:165 result.model_dump()` — yes at all three interfaces |

Test deletions: the diff **adds** 670 lines to the test file and modifies no existing assertion except `missing_untouched_lines` gaining the optional `replaced` argument (default preserves the old behaviour, so no row was weakened). Retention bar not applicable.

### Findings

| Severity | Reality | Area | Finding | Evidence | Test (named, or UNTESTED) | Fix location |
|---|---|---|---|---|---|---|
| Major | THEORETICAL | correctness / accept-list | "Accepted co-located" is decided by **vertical band alone** (`_same_line`, ≥90 % height overlap), not by whether the lost glyph was actually under a rectangle that could not avoid it. A same-band object whose characters could have been spared by an x-trim that `_is_safe_trim` refused for an unrelated reason is warned, never refused — the "blind spot" `proposal.md` §Risks names as one of the two ways to get this boundary wrong. Reproduced shape (not its avoidability): `eval-doc.pdf` p2 warned for a 5×19 pt object rather than refusing. | `modifier.py:_dispose_of_lost_characters` `co_located = any(_same_line(target, box) …)`; my probe on `frontend/e2e/fixtures/eval-doc.pdf` → `warnings=[…]`, `success=True` | `test_the_accepted_co_located_loss_is_reported_as_a_warning` proves the warn path; the *refusal* of a same-band-but-avoidable loss is **UNTESTED** | code + tests (a row with a same-line neighbour whose glyphs sit outside the fitted rect), or a disposition line accepting the approximation |
| Minor | REAL | verification artifacts | `tasks.md` "Mutation: neutralise the comparison … **Record both numbers**" is `[x]` but `verification.md` has **no mutation section at all** (`grep -i mutation` → 0 hits in the file). The claim is true — I reproduced it (M1: 6 red) — it is simply not recorded where the task says it was. | grep above; my M1 run | the six rows named in M1 | `verification.md` (outside the contract set — paste the M1–M6 numbers) |
| Minor | REAL | test traceability / contract | `features.json` f1 and f5 name tests that do not exist: `test_a_sub_half_leading_block_is_refused_or_preserved` (actual `test_a_block_at_060_em_leading_is_refused_or_preserved`) and `test_the_refusal_names_the_damaged_object_and_writes_no_output` (the assertions live inside `test_a_planted_loss_is_caught_by_the_consequence_check`). Both `verification` commands exit 4. | my two pytest runs above | behaviours are covered by the renamed row + `test_a_planted_loss_is_caught_by_the_consequence_check` | `features.json` — **contract set**: editing it invalidates this review, so this is the human's decision, not a demand |
| Minor | REAL | scope / provenance | The reviewed range is not one spec: five commits rewrite the trim heuristics (1daac30, 981bdc1, d0d43d4, afe11d4, 29fe2f6 — 282 lines in `modifier.py`) that `proposal.md` §Out of scope says are "kept as they are, deliberately", and the range also carries #204 (`scripts/check-dependabot-alerts.py`) and #207 (CI-001 `tasks.md`). CORE-006's own commit is clean (+119, the check and its rows), so this is unstated branch provenance, not opportunistic code — but AC6's "nothing opportunistic in the diff" cannot be checked as written. | `git log --stat 01624dee..HEAD -- …/modifier.py`; `git show --stat 4b5d9b4` | n/a | `verification.md` (state which commits are CORE-001's) — outside the contract set |
| Minor | REAL | tests | No test has more than one page (`new_page` appears 6×, one page each), so AC4's "names the **page**" is proven only for page 1. The implementation is correct — my 3-page probe names page 3 and writes no output — so this is a coverage gap, not a defect. | my multi-page probe | `test_a_planted_loss_is_caught_by_the_consequence_check` (page 1 only) | tests (a row asserting `details["page"] == 3`) |
| Minor | SPECULATIVE | correctness / masking | `_glyph_index` keys `(char, round(x0,1), round(y0,1))` with last-writer-wins, so two identical glyphs at the same rounded position collapse to one owner: a loss can be attributed to the allow-listed target, or masked by a replacement glyph drawn within 0.1 pt of the removed one. Both require co-located identical ink, and co-located losses are warned anyway — surfaced, not gated. | code read of `_glyph_index` / `_check_no_other_object_lost_characters`; no repro | UNTESTED | — (surface only; do not gate) |
| Minor | REAL | artifact precision | `tasks.md` states `make check` green at **85.27 %**; a fresh run reports **85.31 %** (423 passed / 19 skipped, ruff and mypy clean). Direction and threshold (above CORE-001's 84.9 %) confirmed; the number drifted. | my `make check` run | n/a | `tasks.md`/`verification.md` — `tasks.md` is contract set; note only |
| Question | — | limitation not stated | The check is text-only: `apply_redactions(images=PDF_REDACT_IMAGE_NONE)` leaves the `graphics` behaviour at its default, so a redaction can still cost line art and the consequence check cannot see it. `proposal.md` scopes to text objects, so this is a declared limitation — but neither ADR-015 nor the lessons say the guard's visibility ends at glyphs. | `modifier.py:482` | n/a | `docs/adr/adr-015` or `verification.md` — one line |

### Evaluator rubric

| Dimension | Grade (A-D) | Rationale (one line) |
|-----------|-------------|----------------------|
| Correctness        | B | Refuse-or-preserve reproduced at every leading, the check shown to fire on real geometries and a real PDF; the accept-list decides by band, not by unavoidability (open Major, THEORETICAL). |
| Verification       | B | Every headline number reproduced (423 passed, 85.31 %, +0.7 % cost, sweep classification); two `features.json` commands exit 4 and the recorded mutation numbers are absent from `verification.md`. |
| Scope              | B | CORE-006's commit is exactly the check; the range additionally carries CORE-001's trim rewrite and #204/#207, which the proposal declares out of scope and the artifacts do not name. |
| Reliability        | A | One redaction path, so no bypass; refusals raise the typed error with page/object/characters, write no output, and multi-page naming verified; warnings reach CLI, MCP and web. |
| Maintainability    | B | New helpers small, typed, WHY-comments; the split into `_lost_characters`/`_dispose_of_lost_characters` is real. CC was read, not measured with the `cyclomatic-complexity` tool; pre-existing CC 10-12 functions untouched and declared. |
| Handoff-readiness  | A | ADR-015, lessons 023/027/028, CORE-001's f9 left pending with the reason and the owner named, next steps explicit. |

Aggregation: no D, no C → rubric path says PASS. The findings path has one open Major, tagged THEORETICAL, so the combined verdict is PASS WITH GAPS.

### Verdict

**PASS WITH GAPS**

`dotf spec archive CORE-006-verify-by-consequence` is **advisable** now: the contract files were not touched by this review, `reviewed_sha` is the head I examined, no Blocker and no REAL Major is open, and no `[AGENT-DRAFT]` tag remains. The gaps are tracked, not fixed — and on a PASS-WITH-GAPS the contract set (`proposal.md`, `tasks.md`, `features.json`) is closed: editing any of them to fix F3/F6/F7 invalidates this verdict.

### Recommended next steps

All of these are outside the contract set, or are explicitly *not* to be done under this verdict:

- **`verification.md` (free to edit)** — record the mutation matrix the ticked task promised, with the numbers measured here: check neutralised → 6 red; refusal neutralised → 2 red; `_same_line` 0.9→0.5 → 4 red; `_same_line`→`False` → 18 red; floor 0.12→0.20 → 2 red; floor 0.12→0.02 → 5 red. Say which commits in `01624dee..HEAD` belong to CORE-001's rounds, so AC6's "nothing opportunistic in the diff" is checkable by the next reader. Note the text-only visibility of the guard (the `graphics` question).
- **tests (free to edit)** — one row where a same-line neighbour loses characters that a rectangle *could* have spared, to turn F1 (the open Major) from THEORETICAL into either a defect or a demonstrated non-issue; and one multi-page row asserting `details["page"] == 3`.
- **ticket, do not silently absorb** — `features.json` f1/f5 name tests that do not exist. Fixing it is a contract edit and costs a re-review round; the honest options are (a) leave the ids, dispositioned in `verification.md`, or (b) edit and re-run `dotf spec review`. Do not let an archive step execute those commands blindly — if the gate ever runs `verification` strings, this becomes a Blocker; that behaviour is the one thing I did not reach and mark **UNVERIFIED**.
- **follow-up, not this diff** — CORE-001 still has no `review.md`, so its `f9` and its archive stay blocked; that is AC8's own wording, and this spec should not tick it.
- **UNVERIFIED at the deadline** — the CORE-001 mutation-matrix re-run (ticked in `tasks.md`); I verified the equivalent fitter mutations (M2, M5, M6) rather than re-running CORE-001's five rows against its recorded counts.
