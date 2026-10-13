---
spec: "CORE-001"
verdict: "PASS"
reviewed_sha: "a1b4ae8fda07acb04799697c4fb1c4663cabdb4d"
reviewer: "nan/glm5.3-flash"
date: "2026-10-13"
---

## Adversarial review

**Scope**: CORE-001 — "A replacement must not drop the lines that follow it" (round 7, first signature, fresh at `a1b4ae8`)
**Sources**: `specs/CORE-001/{proposal,tasks,verification,features.json}`; `git diff 53a697441c2e7f5236ff0ec0d481808d89c62d7a...HEAD` (code: `backend/src/pdf_modifier/core/modifier.py`, tests: `backend/tests/unit/core/test_replacement_preserves_following_lines.py`, `backend/scripts/probe_fitter_reachability.py`); `git log 53a6974..HEAD`; `docs/adr/adr-015-refuse-rather-than-lose.md`; `harness/reviewer-pool.json`; the committed prior rounds `review-round-1..6.md` / `review-second-round-1..2.md`.

### What I ran, fresh, at this head (evidence before claims)

| Command | Result |
|---|---|
| `make check` (repo root) | exit 0 — **429 passed, 19 skipped**, coverage **85.43%** (≥80% gate met), ruff and mypy clean |
| `uv run pytest -q --no-cov` (backend) | **429 passed, 19 skipped**, exit 0 |
| `uv run pytest tests/unit/core/test_replacement_preserves_following_lines.py -q --no-cov` | **48 passed** |
| `uv run ruff check src tests` | All checks passed |
| `uv run ruff format --check .` | **1 file would be reformatted** (`tests/unit/harness/test_reviewer_pool_contract.py`, a pre-existing CI-004 skew) — see F-2 |
| `uv run mypy --strict src/pdf_modifier/core/modifier.py` | Success, no issues |
| All **11** `features.json` verification commands, run verbatim | every one exit 0 with the recorded row counts (f1: 6, f2: 3, f3: 48, f4: 9, f5: 1, f6: 429+19 skipped, f7: 3, f8: 1, f9: 9, f10: 2, f11: 4) |
| `PYTHONPATH=scripts uv run pytest tests/ -q --no-cov -p probe_fitter_reachability` | `PROBE {'fits': 145, 'refused_trims': 18, 'unidentified': 1, 'collapsed': 1, 'identified_misses': 1}` — matches the fresh record in `verification.md` ("The probe at this head") |
| M-A: `_check_no_other_object_lost_characters` call removed | **8 failed / 40 passed** — exactly f9's "M1 turns 8 rows red" |
| M-B: `GLYPH_COVERAGE_FLOOR` 0.12 → 0.15 | **1 failed** — exactly `test_a_slightly_tight_block_is_still_fitted_without_losing_anything[10pt-on8pt]`, reproduces f10's recorded boundary; re-run 5× for stability, deterministic |
| M-C: `_refuse_trim_that_drops_another_line` neutralised | **3 failed** (the two tight-block refusal rows + the 10pt-on8pt boundary) — the refusal is load-bearing |
| M-D: fitter returns the raw rect | **27 failed / 21 passed** — the fitter is what the whole file tests (round 6 measured 30/18 with a slightly deeper neutralisation; consistent) |
| `git merge-base --is-ancestor 1c0ae90 HEAD` | exit **1** — confirms tasks.md's corrected RED-history claim (squash-merge; RED evidenced by neutralisation, honestly recorded) |

Every mutation was reverted; `git status --short` shows only the launcher's own `specs/CORE-001/review-request.json`. No `[AGENT-DRAFT]` / `[AGENT-SUGGESTION]` tags remain in any spec file. One process note: my first M-B run reported 3 failed because my own sequencing left mutation C unreverted alongside it — I chased it as possible flakiness, proved the steady state deterministic (5 consecutive identical runs), and do not report it as a product defect.

### Spec and task alignment

- **AC1 (failing test first, all three rows)** — the three replacement rows are parametrised in every shape family; M-D reproduces the pre-fix loss across them. The RED commit is not in merged history (squash), and `proposal.md`/`tasks.md`/`verification.md` now say so honestly instead of claiming it — the correction rounds 1 and 6 demanded.
- **AC2 (set inclusion, not expected-string presence)** — genuine: `missing_untouched_lines()` iterates the input's lines; span-level residue assertions (`surviving_value_spans`) cover what set inclusion structurally cannot (a partially surviving line).
- **AC3 (synthetic fixture, tight page)** — fixture generated in-test, object-per-line vs single-object control isolating the trigger.
- **AC4 (the two following lines present, per row)** — covered by the 48 rows; f1–f11 all re-run green this session.
- **AC5 (existing suite unchanged)** — 429 passed; the only pre-existing test touched in the range is another spec's rename-guard entry, disclosed in `verification.md` (F-6).
- **Round 6's REAL Major is verified fixed.** It was `proposal.md` frontmatter claiming a round-6 PASS and a second-round-3 PASS with no artifact. At this head the frontmatter names only rounds with committed verdicts (1–3 FAIL, 4 PASS, 5 PASS, **6 FAIL** at `8b071e9` — and `review-round-6.md` exists, FAIL, at that sha), `tasks.md` leaves round 6 unticked and round 7 (this run) owed, and both correcting commits (`8b071e9`, `a1b4ae8`) are prose-only. The claim is now true by evidence.
- **ADR-014 condition 2 (no public contract change)** — holds: only private helpers inside `PDFModifier`; refusals reuse `PDFModifierError` with no new exception type, so CLI/MCP/API/batch error handling is untouched.
- Round 6's findings 2–7 are dispositioned in `verification.md` (applied / ticketed as CORE-009 `#211` and CI-002/CI-004), and the ones I re-ran reproduce exactly as recorded.

### Findings

| Severity | Reality | Area | Finding | Evidence | Test (named, or UNTESTED) | Fix location (code / tests / spec / vault) |
|----------|---------|------|---------|----------|---------------------------|---------------------------------------------|
| Minor | REAL | contract evidence strings | `features.json` evidence fields record the counts at each fix round, not at this head: f6 says "409 passed" (now 429), f5 "125 fits" and f8 "121 fits" (probe now 145/18/1/1). Each was true when recorded; the fresh record lives in `verification.md` (probe section matches my run byte-for-byte). Editing the contract strings would invalidate this review, so this is a record-location question, not a fixable-here defect. | the 11 commands I ran above vs the JSON strings | the probe is the measurement, no named test guards evidence freshness: **UNTESTED** (drift class) | **verification.md** (already carries the fresh record); optionally extend the disposition row to name f6's 409→429 explicitly |
| Minor | REAL | tooling claim | Under the venv's ruff 0.15.5, `ruff format --check` wants to reformat `backend/tests/unit/harness/test_reviewer_pool_contract.py`; the pinned 0.8.6 is clean. The file predates this spec's base and `make check` runs neither formatter, so CI stays green — this is the CI-004 (`#203`) skew seen from a third direction, and `verification.md` already scopes the fix-round-5 claim to the files this spec touches. | my run above (`1 file would be reformatted, 77 already formatted`) | no format gate in the suite — the class CI-004 files: **UNTESTED** | **code-tooling** (CI-004, already ticketed); disposition stands in `verification.md` |
| Minor | THEORETICAL | fitter order-dependence | The neighbour loop mutates `trimmed` as it goes, so with two or more asymmetric neighbours the accepted-rect-vs-refusal outcome can depend on span drawing order — the same class as the second signer's Major 1, fixed for target identification (IoU, order-independent) but not for the trim sequence. Loud only: CORE-006's consequence check refuses rather than losing a line. Carried from round 6; ticketed. | code read of `_fit_redaction_to_its_own_text_object`; no two-neighbour fixture exists | `test_a_large_object_behind_the_text_does_not_decide_whether_the_page_converts` pins one watermark (target identity); the multi-neighbour order row is **UNTESTED** (CORE-009, `#211`) | **tests** (order-symmetry row), then **code** if it disagrees — CORE-009 |
| Minor | THEORETICAL | predicate divergence | Two notions of "same line" coexist: `_same_line` (shared vertical extent ≥ 0.9, attribution path) and centre-containment in `_refuse_trim_that_drops_another_line` (raise path). Under ~0.7 em leading the raise path classifies the next line as same-line and defers to CORE-006's check — the designed mechanism, pinned by the sweep, but expressed as two similar predicates a future "consolidation" could silently merge. | code read; `verification.md`'s own account of why containment was wrong | `test_no_leading_in_the_ailing_range_loses_characters_silently` (0.45–1.30 em) pins the outcome; the predicate split itself **UNTESTED** (CORE-009, `#211`) | **code** (naming comment at the guard) — CORE-009 |
| Minor | SPECULATIVE | test-helper strength | `missing_untouched_lines` is membership-based: a duplicate-line fixture would hide one dropped copy. Production is per-glyph (the consequence check), so this is a blind spot in the test, not in the code; no fixture has repeated lines. | code read of the helper and fixtures | **UNTESTED** (no duplicate-line fixture) | **tests** — surface only, recorded in CORE-009 |
| Minor | REAL | scope of stated claim | f6's "the diff adds the one regression file" is true of CORE-001's own commits and false of the stated review range, which also carries the rename-guard test change (`918df67`), the 1.9.2 release bump, Docker/Glama, dependabot, CI-001 and CORE-006. `verification.md` states the scope plainly ("the code change is scoped; the commit range is not only the code change"). | `git diff --name-status 53a6974...HEAD -- 'backend/tests/**'` | n/a (not a code defect) | **spec** (scope the sentence) — dispositioned in `verification.md` |
| Question | THEORETICAL | performance | `_text_spans` (rawdict) runs once for `before`, again per rectangle in the fit, and twice more in the consequence check — 145 fits across the suite. Filed as CORE-005 (`#202`, 1.35 s vs 0.10 s on an 840-span page). Not re-measured on a large page here. | diff hunks; probe count | n/a | already ticketed (CORE-005) — **UNVERIFIED** by me, deliberately |

### Evaluator rubric

| Dimension | Grade (A-D) | Rationale (one line) |
|-----------|-------------|----------------------|
| Correctness        | **A** | All five ACs verified by running them this session; all 48 regression rows and all 11 contract commands green; four independent neutralisations reproduced the recorded RED counts exactly; no silent-loss path found in the code I could reach. |
| Verification       | **B** | Evidence is reproducible — I re-ran every command and matched the probe and mutation numbers — but three contract evidence strings are counts of earlier heads (F-1), which is why not A. |
| Scope              | **B** | The code change is the fitter, its guards, one regression file, the probe and ADR-015; the stated range additionally carries release/Docker/CI/CORE-006 work, disclosed in `verification.md`. |
| Reliability        | **B** | Every unsafe fit raises naming the page and rectangles; accepted co-located loss is warned, not swallowed; the whitespace exemption is measured and pinned. Not A because the accepted co-located loss still ships a document with ink removed (CORE-003 policy) and the trim loop stays order-sensitive (loud, CORE-009). |
| Maintainability    | **B** | New functions small and CC ≤ 6 (repo gate 10); comments cite the round that earned each rule; two near-identical "same line" predicates and the `0.9` / `0.01` constants are the remaining smell (CORE-009). |
| Handoff-readiness  | **B** | ADR-015, eight lessons, CORE-003/004/005/006/009 tickets, honest round bookkeeping and a correct proposal frontmatter; not A only because the risk: high second signature at this final head is still owed (a state, not a defect). |

Aggregation: all B or above → **PASS** by the rubric path. The severity × reality path agrees: no Blocker, no Major of any reality; six Minors and one Question, each tracked above with a disposition target.

### Verdict

**PASS**

The defect CORE-001 exists for is fixed and I could not break it: set inclusion, residue, sub-character coverage, refusal, boundary, watermark and leading-sweep rows all hold at this head, and every neutralisation I ran failed exactly the rows the spec says it should. Round 6's REAL Major was about the review record itself, and the record is now honest — verified against the committed artifacts, not the prose. What remains is six tracked Minors and the process step that `dotf spec archive` will enforce on its own.

### Recommended next steps

Dispositions for the findings above belong in `verification.md` (outside the staleness check); the contract set is closed under this verdict, and editing `proposal.md`, `tasks.md` or `features.json` now would invalidate it.

- Record F-1's explicit disposition: the stale f5/f6/f8 evidence strings are historical counts per fix round, with the fresh probe and suite counts carried in `verification.md` — or, if the owner prefers the contract strings current, edit them and expect a re-review by construction.
- Carry the remaining CORE-009 items (two-neighbour order-symmetry row, predicate consolidation guard, duplicate-line fixture) as ticketed follow-up; they are loud-failing and do not affect this verdict.
- CI-004 (`#203`) remains the home of the ruff version-skew finding; no action in this spec.
- This run is the **first signature**. `proposal.md` declares `risk: high`, so `dotf spec archive` will refuse until a second signature from a different vendor (`anthropic-review/claude-sonnet-5-5`, the pool's `role: second` member) passes at this same head. Run `dotf spec review CORE-001 --second` next.
