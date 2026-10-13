# CORE-001 — tasks, in the order they were done

## Reproduce, before touching anything

- [x] Build a synthetic fixture and confirm it reproduces the loss: a block of ten short Courier-Bold lines as **one text object per line**. The same block built with a single `insert_textbox` loses nothing — so the structure had to be the one that fails.
- [x] Cross the fixture with three replacement sizes (wider, narrower, four characters). All three lose the same two lines, which rules out "make the new text fit" as the mechanism.

## RED

- [x] Write `backend/tests/unit/core/test_replacement_preserves_following_lines.py` and watch it fail: **3 failed, 3 passed** — the multi-object cases lose `ARC: 00` and `CVM: 5E0000`; the single-object cases lose nothing.
- [x] Commit the failing test on its own (`1c0ae90`) — **on `fix/CORE-001-reflow-drops-lines`, not in `master`'s history.** Corrected in the fix round: #186 was squash-merged, so `ae28471` carries test and fix together and `git merge-base --is-ancestor 1c0ae90 HEAD` exits **1**. The claim that the RED state is in the merged history described an intent, not the artifact; the RED survives in the branch ref, the squash message and this file's evidence.

## Locate, by measurement

- [x] Redact **only** the target line's tight bounding box in isolation: three lines disappear. Consecutive line boxes overlap by **1.6 pt** (11 pt leading against 12.6 pt line height), and `apply_redactions` removes every text object that intersects.
- [x] Record and discard two hypotheses that were plausible and wrong: the replacement's rendered width, and an embedded font (`get_fonts()` reported *embedded*; the font object is base-14 with no `/FontFile`).

## GREEN

- [x] `_fit_redaction_to_its_own_text_object`: trim the rectangle away from the neighbours. The object being replaced is the one that **contains** the rect's centre; a neighbour can only overlap its edge.
- [x] Guard against an empty rectangle, which would redact nothing and leave the original text under the replacement.
- [x] `6 passed`; core suite `177 → 183`; `make check` **385 passed**, coverage **84.34%**.
- [x] Verify against the **real document** with the substitution active: `ARC` and `CVM` present, new value in place, old value gone.

## Fix round — the independent review's Blocker (round 1: **FAIL**, `nan/mimo-v2.6-flash`)

- [x] Reproduce the Blocker end to end through `PDFModifier.process`: the target span shares its line with a **label span in another colour**, the two touch at x, and the y-only trim drags `y1` up to the neighbour's `y0`. The rect collapses to area 0 and the guard returns the raw one. `missing=['ARC: 00', 'CVM: 5E0000']` — the defect CORE-001 exists to fix, restored by its fix.
- [x] Choose the trim axis **per neighbour**: **x** when the neighbour shares the rect's vertical band (same line, so it is beside the target), **y** when it is above or below. The y-only branch was the Blocker.
- [x] **The guard no longer returns the raw rect.** A collapsed fit raises `PDFModifierError` naming the page and both rectangles. Measured before choosing: a 0.02 pt rect removes **no glyph at all**, so a "tiny rect" fallback would leave the original text under the replacement — the guard has no safe rect to return, only a failure to report.
- [x] Named regression test for a target line drawn as two spans, in the same three sizes, with the helper-neutralised RED recorded (`-k two_spans` **3 failed**; against the single-object control **3 failed / 3 passed**) and the GREEN after it.
- [x] Named test for the guard: a collapsing fit raises instead of handing the raw rect back.
- [x] Correct the two false claims the review found: the `1c0ae90` history claim (this file) and `features.json`'s untouched `dotf spec init` scaffold. Re-recorded the Blocker and its repro in `verification.md`.
- [x] `make check` **391 passed**, coverage **84.38%**; `ruff` and `mypy --strict` clean.

## Close

- [x] Independent adversarial review, round 1 (`dotf spec review CORE-001`) — **FAIL**: one REAL Blocker (above) plus two minor findings. The archive gate refused, correctly.
- [x] Independent adversarial review, round 2 (`nan/deepseek-v4-flash`) — **FAIL**: one REAL Major (round 3 below), three minors. Round 1's Blocker was confirmed genuinely closed, by independent reproduction of four shapes the spec never tested.
- [ ] Independent adversarial review, round 3 — **fresh**, because a review is not recyclable and the branch moved after each one
- [ ] Archive to `specs/archive/CORE-001/`

## Fix round 2 — the review's Major finding (round 2: **FAIL**)

- [x] Reproduce the finding end to end: a same-band neighbour that **overlaps the target's own glyph run**. The x-trim cut inside the target, redaction is per character, and `68D489` — the first six characters of the replaced value — stayed on the page under the new one. No failure, no warning.
- [x] Make the invariant explicit instead of patching a third axis case: **a trim may not lose a glyph of the object being replaced.** The candidate rect is kept only if it still reaches every character of the target, whose boxes come from `get_text("rawdict")`. A neighbour failing that test shares the target's ink, so the rect covers both.
- [x] Decompose the helper for the round-2 **Finding 2**: CC 11 and nesting 5 became six functions at CC 4/3/4/3/7/5 and nesting 0/1/2/1/2/0, verified with `ruff --select C901`, whose firing was shown at `max-complexity=2` before the `=10` verdict was trusted.
- [x] Named regression rows for **three** overlap shapes (head, nested, tail) × the same three replacement sizes, plus the assertion set inclusion cannot make: `surviving_fragments`, so a partially surviving value fails. RED with the coverage rule neutralised: **10 failed, 9 passed** (the 9 new rows and the guard), and with the whole fitter neutralised: **16 failed, 3 passed** (the single-object control).
- [x] **Finding 3** dispositioned, not waived: the fail-loud guard is accepted (fail the document rather than corrupt it), measured as unreachable in 68 real fits, and checked to surface in CLI, MCP, API and batch. **Finding 4** applied: the "old value gone" claim is scoped to the shapes measured.
- [x] Re-measure the cost of `rawdict`: 40 replacements in 0.137 s against round 1's 0.134 s with `dict`.
- [x] `make check` **400 passed**, coverage **84.63%**; `ruff` and `mypy --strict` clean.
