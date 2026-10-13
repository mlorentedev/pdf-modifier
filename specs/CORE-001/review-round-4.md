---
spec: "CORE-001"
verdict: "PASS"
reviewed_sha: "a479628598c7c4f780720212c29d22adec8d83fd"
reviewer: "nan/glm5.3-flash"
date: "2026-10-13"
---

## Adversarial review

**Scope**: CORE-001 — "A replacement must not drop the lines that follow it" (round 4, after FAIL rounds 1–3)
**Sources**: `specs/CORE-001/{proposal,tasks,verification}.md`, `specs/CORE-001/features.json`, `specs/CORE-001/review-round-{1,2,3}.md`, `git diff 53a697441c2e7f5236ff0ec0d481808d89c62d7a...HEAD` (7 commits; base as resolved and stated by the launcher)

### Spec and task alignment

Everything below was re-run in this session; nothing is quoted from `verification.md`.

- **Round-3's two REAL Majors are closed, verified by mutation, not by reading.** I applied the mutations myself and restored the tree after each one (`git status` clean, confirmed):
  - coverage floor → `intersects`: **3 failed / 21 passed**, exactly the three `test_no_character_of_the_value_survives_a_sub_character_overlap[*]` rows — matches `tasks.md`'s recorded RED to the row;
  - floor = 0.0 (weaker than `intersects`): the same three rows fail with residue `['6']` — the exact round-3 Finding 1 signature, one character, invisible to the window-2 fragment check and to line inclusion;
  - unidentified-target refusal neutralised: **1 failed**, exactly `test_a_target_that_cannot_be_identified_is_refused_not_trimmed_unguarded`;
  - whole fitter neutralised (`return rect`): **21 failed / 3 passed** — the 3 survivors are the single-object control, exactly as recorded.
- **Suite, fresh**: `make check` → **405 passed, 19 skipped, coverage 84.70%, exit 0**. `uv run pytest tests/unit/core/test_replacement_preserves_following_lines.py -q --no-cov` → **24 passed**. `ruff check` and `mypy --strict src` → clean. All match `features.json` f6 and `tasks.md`.
- **Reachability claim reproduced with the correct invocation** (the probe is a pytest plugin, not a script — run as `PYTHONPATH=scripts uv run pytest tests/ -q --no-cov -p probe_fitter_reachability`): `PROBE {'fits': 121, 'unidentified': 1, 'collapsed': 1, 'identified_misses': 1}` — both refusals are the guard's own stub rows, none from a real document, as claimed.
- **Round-3 Finding 5 (surfacing) closed**: `PDFModifierError` is caught at the CLI, MCP and web route boundaries (`interfaces/cli.py:295`, `interfaces/mcp.py:37`, `web/routes/pdf.py:105/166`, verified by grep).
- **Round-3 Finding 2 disposition applied as recommended**: the shared-ink deletion is stated as accepted policy in `verification.md`, pinned by `test_a_label_sharing_the_target_ink_loses_exactly_the_shared_characters` (asserts the exact surviving shape: one truncated prefix, nothing invented), and the re-insertion capability is filed as CORE-003 rather than smuggled into this repair (ADR-014 condition 3). This reviewer accepts that disposition; see Findings.
- **AC5 (existing suite unchanged) verified by diff**: the range touches `backend/tests/` only by *adding* `test_replacement_preserves_following_lines.py` (446 lines, additions only; no pre-existing test modified or deleted). Nothing to audit under the test-deletion bar.
- **No `[AGENT-DRAFT]` / `[AGENT-SUGGESTION]` tags** in the contract files (grep over `specs/CORE-001/*.md`; the only hits are round-1..3 reviews *reporting* their absence).
- **AC1's RED history**: the squash-merge orphans `1c0ae90` from merged history — the spec discloses this itself (`tasks.md`), and the mechanism is red-green-verified by my four mutations above, which is the stronger evidence. The branch ref `fix/CORE-001-reflow-drops-lines` exists locally for the record.
- **Contract digests and the round-3 "identified_misses" cross-check were not re-derived** — **UNVERIFIED** for time; neither can change the verdict (the launcher froze the contract, and the probe's `identified_misses=1` matches the one stub row).

### Findings

| Severity | Reality | Area | Finding | Evidence | Test (named, or UNTESTED) | Fix location (code / tests / spec / vault) |
|----------|---------|------|---------|----------|---------------------------|---------------------------------------------|
| Major | REAL | core/redaction | **None.** Round 3's Finding 1 (sliver survival through the trim path) and Finding 2 (silent shared-ink deletion) were both reproduced by *this* reviewer through the recorded mutations before anything was changed; both fixes hold against the mutations that reproduced them. | Mutation runs listed above; probe output | `test_no_character_of_the_value_survives_a_sub_character_overlap` (3 rows), `test_a_label_sharing_the_target_ink_loses_exactly_the_shared_characters` | — |
| Minor | THEORETICAL | core/redaction | **`_reaches_glyph` applies the measured width threshold to height as well, but only width was measured.** The bisection (6/9/12/18/24 pt) established the 10%-of-*width* transition; the code additionally requires 15% of the glyph's *height*. A stricter-than-measured height rule can only *refuse* trims (safe direction), and a refused trim leaves the previous rect — which, in a false-positive refusal, could still intersect a neighbour that does *not* share ink. Not reproduced: no fixture in the suite or argument from the code produces a height-only refusal that is not also a shared-ink case. | Code read of `_reaches_glyph` vs the measurement table in `verification.md` (lines 278–288); no repro | UNTESTED | tests (bisect the height transition the way the width one was bisected; a row that produces a height-only refusal) |
| Minor | THEORETICAL | core/redaction | **Target identification takes the FIRST span whose bbox contains the rect's centre.** With two spans containing the centre (a stamp drawn over the value), rawdict order decides whose glyphs are protected; if the stamp sorts first, trims are judged against the wrong glyph set and the value's own glyphs could be cut. Not reproduced — the rect comes from the analyzer's own span, so the same span normally wins; requires an overlapping span whose bbox contains the target's centre and sorts earlier. | Code read of `_fit_redaction_to_its_own_text_object` (`next(...)` over `_text_spans`) | UNTESTED | code (prefer the span whose bbox best matches the rect, e.g. smallest containing area) + tests (stub-page row) |
| Minor | REAL | tests | **The overprint rows pin the coverage rule only down to `intersects`, not below it.** With floor = 0.0, 13 rows fail (9 overprint + 3 sliver + 1 shared-ink); with floor → `intersects`, only the 3 sliver rows fail. The overprint rows are insensitive to weakening the floor *past* the intersects baseline — their protection below that line comes from `_is_safe_trim`'s empty-candidate/guard path, not from the floor. Correct as-is (intersects is the redactor's documented predicate, and the floor's whole job is to be stricter than it); recorded so future mutation testing does not read the 3-row delta as the floor's total coverage. | My mutation runs (13 vs 3 failures, same tree) | the overprint rows themselves (`test_no_untouched_line_is_lost_when_a_neighbour_overlaps_the_target`) | none required (note only) |
| Minor | REAL | core/redaction | **Accepted shared-ink deletion of non-replaced characters remains**, exactly as pinned: `ACCOUNT: ` → `AC` when its ink runs 12 pt under the value. Dispositioned in round 3, disclosed in `verification.md`, pinned by a named row asserting the exact surviving shape, and the re-insertion capability is filed as CORE-003. Tracked; not open. | `test_a_label_sharing_the_target_ink_loses_exactly_the_shared_characters` (green); CORE-003 ticket | that named test | follow-up ticket CORE-003 (already filed) |

Code-level checklist over the diff: no injection surface (rects/spans only, no shell, no paths from input), no secrets, no auth change, no async path touched (the fitter is sync inside the sync core, called via `anyio.to_thread` upstream). Performance: `get_text("rawdict")` runs once per rectangle per page — measured by the implementers at 40 replacements in 0.137 s, same order as round 3's independent measurement; bounded, accepted. Complexity: `ruff --select C901 --config 'lint.mccabe.max-complexity=10'` → clean (re-verified this session).

### Evaluator rubric

| Dimension | Grade (A-D) | Rationale (one line) |
|-----------|-------------|----------------------|
| Correctness        | B+ | Every acceptance criterion holds on all tested shapes, and the negative paths are pinned by mutations this reviewer reproduced exactly; the two residual gaps are argued, not observed. |
| Verification       | A | Every claim I checked reproduced fresh, including the probe's correct plugin invocation, the 4-mutation RED matrix, and the round-3 defect signatures; the implementers recorded commands, not assertions. |
| Scope              | B | The CORE-001 slice matches the proposal exactly (fitter + one regression file + spec/lessons); the range also carries release-please artifacts and lessons from the same defect stream, documented as such since round 2. |
| Reliability        | B+ | Silent fallback is gone (refusal raises with page and both rects, measured unreachable outside its own stub); the accepted shared-ink deletion is pinned so it cannot grow silently. |
| Maintainability    | A- | Six single-job functions, C901 clean at the repo's threshold (verified), docstrings carry the mechanism *and* the review history that shaped each invariant. |
| Handoff-readiness  | A- | Spec triad truthful including corrections of its own earlier false claims; probe script committed so the reachability claim stays re-runnable; CORE-003 filed for the accepted gap. |

### Verdict

PASS

No Blocker and no open REAL Major: round 3's two REAL Majors were reproduced by this reviewer via mutation and both fixes hold; the shared-ink deletion is a dispositioned, pinned, ticketed acceptance rather than an open finding. The remaining Minors are THEORETICAL (argued, not observed) plus one tracked acceptance, none of which can move the verdict per severity × reality. The rubric has no C or D.

### Recommended next steps

The contract set (`proposal.md`, `tasks.md`, `features.json`) is closed by this verdict — do not edit it; an edit would stale this review. Route the following as dispositions in `verification.md` (applied / ticketed / declined with a reason) or into follow-up tickets:

1. **tests**: measure the *height* transition of `apply_redactions` the way the width transition was bisected, and add (or justify not adding) a row for a height-only refusal. *(Finding 2.)*
2. **code + tests**: make target identification prefer the span whose bbox best matches the rect instead of the first containing span, with a stub-page row for the two-candidates case. *(Finding 3; cheap, and it removes the last order-dependent path in the fitter.)*
3. Carry Finding 4's note into the mutation-testing recipe (e.g. `docs/lessons/` or the mutmut config comments): when mutating `GLYPH_COVERAGE_FLOOR`, the overprint rows go red only at the `intersects` baseline, not below it.
4. `dotf spec archive` is **advisable** in the current state. `proposal.md` declares `risk: high`, so the archive gate will require the second signature per the reviewer-pool rule — this review counts as the first.
