---
spec: "CORE-001"
verdict: "FAIL"
reviewed_sha: "a7ef1a2cf31b0e6a13c6f3a8b5880669f1867a22"
reviewer: "nan/deepseek-v4-flash"
date: "2026-10-13"
---

## Adversarial review

**Scope**: CORE-001 — "A replacement must not drop the lines that follow it" (round 2, after the round-1 FAIL)
**Sources**: `specs/CORE-001/{proposal,tasks,verification}.md`, `specs/CORE-001/features.json`, `specs/CORE-001/review-round-1.md`, `git diff 53a697441c2e7f5236ff0ec0d481808d89c62d7a...HEAD` (5 commits: ae28471 fix, 7d138d9 lessons, a1b6056 release, f1dd8ea spec docs, a7ef1a2 fix round)

### Spec and task alignment

Everything below was re-run in this session; nothing is quoted from `verification.md`.

- **Round-1 Blocker is fixed, re-reproduced independently.** I rebuilt the mixed-style fixture (label span + value span on one baseline, value in another colour) and ran `PDFModifier.process` in three variants the spec does not test: touching spans, spans overlapping by 0.1/1.0/4.0 pt, and the value split across two further spans (cross-span pass 2). In every variant: no untouched line missing, old value absent, new value present. The mechanism also holds as documented — trimming the rect away from the same-line neighbour leaves the target object intersecting, and `apply_redactions` removes a whole object that intersects at all.
- **Full suite, fresh**: `uv run pytest -q --no-cov` → **391 passed, 19 skipped** (matches `features.json` f4). `uv run ruff check .` → clean. `uv run mypy src` → clean (31 files).
- **features.json verification paths resolve.** f1 → 6 passed, f2 → 3 passed, f3 → 1 passed (`backend/tests/unit/core/test_replacement_preserves_following_lines.py::{test_no_untouched_line_is_lost,test_no_untouched_line_is_lost_when_the_target_line_has_two_spans,test_a_collapsing_fit_raises_instead_of_redacting_the_raw_rect}`).
- **Red-green reproduced by mutation.** Inserting `return fitz.Rect(rect)` as the fitter's first statement (tree restored immediately; `git status` clean for `modifier.py` afterwards) gives the test file **7 failed, 3 passed** — the number `verification.md` records — and **6 failed, 3 passed** on the narrower `-k "two_spans or (not two_spans and not collapsing)"` selection. The single-object control rows stay green. The neutralisation-fails / fix-passes relation is real.
- **Round-1 findings were dispositioned, not restated.** `tasks.md` now records the squash-merge truth about `1c0ae90`, and the diff confirms it structurally: the whole test file arrives as **+181 added lines** in `ae28471`, so test and fix are one commit and no pre-existing test was modified or deleted. `features.json` is no longer the `dotf spec init` scaffold.
- **Review freshness confirmed.** I recomputed the normalised `contract_digests` from disk and all three match `review-request.json` (`proposal.md` 099dc607…, `tasks.md` 6de85ffc…, `features.json` d8d88e24…) once the tool's normalisation is reproduced: line endings, list-checkbox state, `status:` value folded while **keeping** the trailing comment (`^(status:\s+)\S+(.*)$`), and Go's `json.Marshal` HTML escaping on `features.json`. This review is about the contract on disk.
- **Acceptance criteria, line by line**: (1) failing test first, three rows — met (mutation above); (2) every input line present unless replaced — met on every shape I could build except where it cannot be, see Finding 1, which is a different failure (the *replaced* text surviving, not an untouched line vanishing); (3) synthetic, tight fixture — met (11 pt leading vs 12.6 pt line height); (4) per-row message — met, the assertion prints the missing set and I saw real messages; (5) existing suite unchanged — met.
- **No `[AGENT-DRAFT]` / `[AGENT-SUGGESTION]` tags** in `proposal.md`, `tasks.md` or `verification.md` (read in full).
- **Not a finding, disclosed for completeness**: after running the suite, `backend/uv.lock` was dirty (`pdf-modifier` 1.9.1 vs `pyproject.toml` 1.9.2) — `uv run` rewrites that field from `pyproject.toml`. CI uses plain `uv run`, not `--locked`, so nothing is broken by it. I restored the file; the tree is otherwise clean apart from this review.

### Findings

| Severity | Reality | Area | Finding | Evidence | Test (named, or UNTESTED) | Fix location |
|----------|---------|------|---------|----------|---------------------------|--------------|
| Major | REAL | core/redaction | **A neighbour that OVERLAPS the target's own glyph run is misclassified as "beside" it, and the x-trim then cuts into the target.** The same-band branch assumes neighbours are disjoint: it trims `x0` to `other.x1 + 0.01` whenever `other.x1 <= centre.x`. If an overlapping text object ends inside the target span but before its centre (nested span, stamp/overprint text, any doubled-text object wider than one glyph), that trim lands *inside* the target's own glyph run. Redaction is per-glyph (verified separately), so the target's first glyphs are never covered and survive, while the replacement is re-inserted at the item origin on top of them — the replaced value is left visible under its replacement. | Two independent fixtures, both through `PDFModifier.process` on the tight 3-line block. (a) Neighbour `ZZZZZZ` at the value's own x: value span `(99.0, 73.9, 185.4, 86.5)`, neighbour span `(99.0, 73.9, 131.4, 86.5)` (x1 < centre 142.2) → output text `'ARC: 00\n68D489\nZZZZZZ\nCVM: 5E0000\n9F3C1D7A4E620B85\n'` — `68D489` is six surviving characters of the replaced value. (b) Neighbour `ZZZZZZZZZZ` at 72 (x1 = 126.0) → `'ARC: 00\n68D48\nZZZZZZZZZZ\nCVM: 5E0000\n9F3C1D7A4E620B85\n'`. Granularity check that makes the residue possible: redacting only the left third of a one-span string leaves `'DEFGH'` — partial cover removes only the covered glyphs. Not a pre-existing defect: before the fix the item's full bbox was redacted, so the whole target object went. This is new behaviour introduced by the fitter, and it is silent. | UNTESTED — every row of `test_no_untouched_line_is_lost*` uses touching or disjoint spans; no named test has a neighbour whose bbox overlaps the target span | code + tests |
| Minor | REAL | core/quality | The helper exceeds two of the repo's stated code-quality thresholds: cyclomatic complexity ≈ 11 (`< 10` required) and nesting depth 5 (`< 4` required) at the inner x-branch. No configured tool catches it — `ruff` selects `E,F,I,N,UP,B,C4,SIM,A,TCH`, with no `C90`. | Counted from the diff: three loops plus five conditionals, two of them compound; the `if other.y0 <= …` block contains a nested `if/else`. Round 1 graded Maintainability A with "CC ≤10", which the code does not support. | n/a | code (or record an accepted exception) |
| Minor | THEORETICAL | core/resilience | The fail-loud guard changes a silent loss into a **document-level failure**: a collapsed fit raises `PDFModifierError`, which `process` re-raises, so one unfit rect fails the whole conversion (no partial output). Whether a *non-overlapping* real document can reach that collapse is unproven — round 1's probe measured `calls=64 collapses=0` over the then-183-test suite, and I did not construct one. | Code read of `_fit_redaction_to_its_own_text_object` + `process`; no reproduction | UNTESTED | code (intended per lesson-023 — needs an explicit "accepted: fail the document rather than corrupt it" disposition, and a check that the web/CLI layers surface it) |
| Minor | REAL | spec/verification | `verification.md` states flatly "new value in place, old value gone". That is true for the shapes it tested and false for the overlapping-neighbour shape of Finding 1, which leaves the old value's prefix on the page. A verification claim broader than its fixtures is the same class the round-1 review caught, one level down. | Finding 1's outputs | n/a | spec (`verification.md`, non-contract; `features.json` f2's evidence line is also contract-if-edited — leave it, or expect a re-review) |

Code-level checklist over the diff: no injection surface (rects and spans only), no secrets, no auth, no async path touched, no unbounded loop beyond one `get_text("dict")` scan per rect (round-1 measured 40 replacements in 0.134 s; I did not re-measure). The docstring and lesson-023 explain the *why* thoroughly. Findings 1–3 are the only hits.

### Evaluator rubric

| Dimension | Grade (A-D) | Rationale (one line) |
|-----------|-------------|----------------------|
| Correctness        | C | All five acceptance criteria are met and the round-1 Blocker is genuinely closed, but an observed defect remains on an untested negative path (Finding 1). |
| Verification       | B | Reproducible, mutation-checked evidence for every criterion; one claim ("old value gone") is broader than its fixtures, and the real-document check cannot be reproduced from the repo. |
| Scope              | B | The CORE-001 slice matches the proposal exactly (helper + one regression file + spec/lessons); the range also carries a release bump and unrelated lessons commits from other PRs, documented as such in round 1. |
| Reliability        | C | The silent fallback is gone (good), but Finding 1 is a silent wrong output on a new shape, and the fail-loud path turns one unfit rect into a whole-document failure. |
| Maintainability    | B | Clear naming, private static helper, docstring explains the mechanism and its history, ruff/mypy clean — but CC ≈ 11 and nesting depth 5 are above the repo's own thresholds. |
| Handoff-readiness  | A | Spec triad updated and truthful, `features.json` real, lesson-023 written, round-1 findings each dispositioned, next steps recorded as unticked boxes. |

### Verdict
FAIL

One **REAL Major** (Finding 1, reproduced twice) forces FAIL under `severity × reality`; the rubric agrees via Correctness C and Reliability C. The finding is **UNTESTED** — no named test exercises a neighbour that overlaps the target — so a green fixture suite cannot close it. Coverage (84.38%) and `make mutation` were **UNVERIFIED** in this run for time; neither affects the verdict.

### Recommended next steps

The contract set (`proposal.md`, `tasks.md`, `features.json`) does **not** need to change for Finding 1 or 2 — they are code and tests. That is deliberate: a fix under this verdict is followed by a fresh review, and a contract edit would stale it.

1. **code**: classify a neighbour that materially overlaps the target span as part of the object being replaced, not as "beside" it — e.g. skip a neighbour whose intersection with the replacement's own span bbox is significant, or refuse to trim an edge that would move inside the target's bbox, raising as the existing guard does. The failure mode to avoid either way is trimming past the target's first glyph. *(Owner of Finding 1.)*
2. **tests**: add a named regression row with an overlapping same-band neighbour — nested inside the target and longer-but-still-before-the-centre — in the same three replacement sizes, and record the neutralised-fitter RED beside the GREEN, exactly as the two-span rows do today. This is the test that closes Finding 1's UNTESTED status. *(Finding 1.)*
3. **spec (`verification.md`, non-contract)**: narrow the "old value gone" claim to the shapes it covers, and disposition Findings 2–4 there — applied, ticketed, or declined with a reason. *(Findings 2–4.)*
4. **code/tests (optional, Finding 2)**: either split the helper so each branch is under the CC/depth thresholds, or record the exception next to the thresholds it exceeds.
5. After 1–2 land with red-green evidence: re-run `dotf spec review CORE-001`. `proposal.md` declares `risk: high`, so a **second signer** (`--second`) is required before archive.

**Minimum set to flip to PASS**: items 1 and 2 (overlap classification fixed + a named, red-green regression test for it), with Findings 2–4 dispositioned. In the current state the verdict is FAIL and `dotf spec archive` is **not advisable**: the archive gate would record CORE-001 as fixed while a shape exists in which the replaced text stays visible under its replacement.
