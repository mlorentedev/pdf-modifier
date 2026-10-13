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
- [x] Independent adversarial review, round 3 (`nan/deepseek-v4-flash`) — **FAIL**: two REAL Majors, three minors. Both Majors were real and were reproduced here before anything changed (below). Round 1's Blocker and round 2's Major were confirmed genuinely closed.
- [x] Independent adversarial review, round 4 (`nan/glm5.3-flash`, drawn from the pool) — **PASS**, the first round that did not fail. It re-ran the whole RED matrix itself and reproduced every recorded number; it left two THEORETICAL minors and a mutation-testing note, both ticketed as CORE-004 (`#201`).
- [x] Second signature (`anthropic-review/claude-sonnet-5-5`, required because `risk: high`) — **FAIL**: one REAL Major the first signature did not find, plus a real format finding, a real performance finding and a methodology point. Reproduced here before anything changed; closed by fix round 4 below.
- [ ] Independent adversarial review, round 6 — **fresh at this head**, because a review is not recyclable and the branch moved since round 5 (`f7b1324`): CORE-006's check and the whitespace/attribution fixes are all in this revision. Second signature for this spec: rounds 1-2 FAILED on real defects (`anthropic-review/claude-sonnet-5-5`; both reproduced and fixed in CORE-006), round 3 PASSED at `5e35997` -- CORE-006's reviews, at this branch's heads, so they read CORE-001's code too, but this spec needs its own at the final head. All kept as `review-round-*.md` / `review-second-round-*.md`.
- [x] Independent adversarial review, round 5 (`nan/deepseek-v4-flash`, random draw) — **PASS** at `f7b1324`. Re-measured the predicate, reproduced the mutation matrix, confirmed the refusal names the line it protects. Its minors are recorded in `verification.md` and ticketed in CORE-004 (`#201`), except the `uv.lock` one, which is CI-002 (`#191`) from the other side.
- [x] Second signature, round 2 (`anthropic-review/claude-sonnet-5-5`) — **FAIL** on the same revision: two REAL Majors from one root cause (target identification by "the first span containing the rect's centre"). One closed by fix round 5 with a regression row; one left open, reproduced and re-ticketed. See `verification.md`, round 8.
- [ ] Archive to `specs/archive/CORE-001/` — unblocked: CORE-006 closed the Major (`#201` is closed with the PR link) and the reviews are green

## Fix round 2 — the review's Major finding (round 2: **FAIL**)

- [x] Reproduce the finding end to end: a same-band neighbour that **overlaps the target's own glyph run**. The x-trim cut inside the target, redaction is per character, and `68D489` — the first six characters of the replaced value — stayed on the page under the new one. No failure, no warning.
- [x] Make the invariant explicit instead of patching a third axis case: **a trim may not lose a glyph of the object being replaced.** The candidate rect is kept only if it still reaches every character of the target, whose boxes come from `get_text("rawdict")`. A neighbour failing that test shares the target's ink, so the rect covers both.
- [x] Decompose the helper for the round-2 **Finding 2**: CC 11 and nesting 5 became six functions at CC 4/3/4/3/7/5 and nesting 0/1/2/1/2/0, verified with `ruff --select C901`, whose firing was shown at `max-complexity=2` before the `=10` verdict was trusted.
- [x] Named regression rows for **three** overlap shapes (head, nested, tail) × the same three replacement sizes, plus the assertion set inclusion cannot make: `surviving_fragments`, so a partially surviving value fails. RED with the coverage rule neutralised: **10 failed, 9 passed** (the 9 new rows and the guard), and with the whole fitter neutralised: **16 failed, 3 passed** (the single-object control).
- [x] **Finding 3** dispositioned, not waived: the fail-loud guard is accepted (fail the document rather than corrupt it), measured as unreachable in 68 real fits, and checked to surface in CLI, MCP, API and batch. **Finding 4** applied: the "old value gone" claim is scoped to the shapes measured.
- [x] Re-measure the cost of `rawdict`: 40 replacements in 0.137 s against round 1's 0.134 s with `dict`.
- [x] `make check` **400 passed**, coverage **84.63%**; `ruff` and `mypy --strict` clean.

## Fix round 3 — the review's two Major findings (review round 3: **FAIL**)

- [x] Reproduce both Majors before touching anything. **Finding 1**: `_is_safe_trim` accepted a candidate on `intersects`, but `apply_redactions` removes a character only from a measured share of its box — a label whose box crosses the value's first glyph by 0.4 pt left `6` on the page under its replacement. **Finding 2**: a neighbour whose ink lies inside the rectangle was redacted and never re-inserted, silently (`ACCOUNT: ` → `AC`).
- [x] Replace the guessed predicate with the measured one: bisect the redactor's transition at 6, 9, 12, 18 and 24 pt → **10.0% of the character's width at every size**, so the rule is a fraction of the box and `GLYPH_COVERAGE_FLOOR = 0.15` sits above it. A stricter-than-the-redactor check costs a refused trim; a laxer one costs content, silently.
- [x] Make the shared-ink loss a stated policy rather than a silent one: it is accepted (no geometry separates two objects drawn in the same place; the alternatives are refusing the whole document or re-inserting through a subset font), pinned by a named row that fails if the loss grows, and the capability is filed as CORE-003 — not added here, per ADR-014 condition 3.
- [x] **Finding 3** applied: `surviving_fragments(window=2)` cannot see one character, so `surviving_value_spans` reads the output's own text objects and every row asserts both. **Finding 4** applied: an unidentified target is refused, not trimmed unguarded (`all()` over an empty list is `True`). **Finding 5** answered with citations — `cli.py` (5 sites), `mcp.py:37`, `routes/pdf.py:105,166`, `batch_process`, and `TestMCPErrorHandling` — instead of the unverified claim round 3 flagged.
- [x] RED, three mutations, each precise: coverage floor → `intersects` = **3 failed / 21 passed**, exactly the three new rows, with `['6'] survived`; refusal neutralised = **4 failed**; whole fitter neutralised = **21 failed / 3 passed** (the single-object control).
- [x] Make the refusal's cost a measurement instead of an assertion: `backend/scripts/probe_fitter_reachability.py` counts **121 fits, 1 collapse, 1 unidentified target over the whole suite — both from the guard's own stub pages, none from a real document**.
- [x] All eight `features.json` verification commands are run here and exit 0 with a plain whitespace split (no shell quoting required), because a verification command that cannot run is not one.
- [x] `make check` **405 passed**, coverage **84.70%**; `ruff` and `mypy --strict` clean; fitter functions at CC 8/5/4/4/3/3/2, nesting ≤ 2.

## Fix round 4 — the second signature's Major (second signer: **FAIL**, first signer had PASSed)

- [x] Reproduce the Major before touching anything: with the leading tighter than the glyph height, `keepkeep4` became `p4` at 12 pt on 9 pt leading — the line BELOW the target losing six characters with no error and no warning. Traced the mechanism: the target's 16.8 pt glyph box overlaps the next line's box by 7.8 pt, so every rect that covers the target reaches that line, and the trim that would spare it is refused.
- [x] Measure what the second signer could not: the redactor's **height** transition, at 6/9/12/18/24 pt, which is **10.0% of the character's height at every size** — the same as the width. So the first signer's "the height rule was never measured" Minor is answered by measurement, not by argument.
- [x] Correct a claim this spec wrote and the second signer was right to call false: the floor's comment said "a refused trim only leaves the rectangle where it was", and leaving the rectangle where it was IS the defect. The comment now states what a refusal costs, and the code no longer treats it as free.
- [x] Sweep the floor to show that lowering it cannot fix this case: 15% and 12% lose the line at 12/9 and 9/7; even the exact 10% transition loses it, because the trim that would spare the line leaves 7% of the target's own glyphs. There is no rect that covers the target and spares that line, so the fit must choose which failure to have — loudly.
- [x] Set the floor to **0.12** (measured transition plus a margin, both axes) and add `_refuse_trim_that_drops_another_line`: a refused trim that would cost a neighbour on ANOTHER LINE its characters raises `PDFModifierError` naming the page, the target's rect and the line. A same-band neighbour keeps its accepted behaviour (CORE-003, `#199`) — its ink is in the same place, so there is no rect to prefer.
- [x] Regression rows at 12/9 and 9/7 asserting the refusal, that it names the line it protects, and that no half-written document is left; plus boundary rows at 10/8 and 12/10 asserting they still convert without losing anything, since every unnecessary refusal is a document that used to convert.
- [x] RED, one mutation per claim: refusal neutralised -> **2 failed / 26 passed**; floor back to 0.15 -> **1 failed / 27 passed** (the boundary row, which is the second signer's "0.5 leaves all 24 green" answered from above); floor 0.5 -> **2 failed**.
- [x] Extend the probe to count **refused trims** — the blind spot the second signer named, because the refusal that costs content was invisible in the counts: **125 fits, 15 refused trims, 1 collapse, 1 unidentified target** across the suite.
- [x] File what was not fixed here: CORE-005 (`#202`, the page re-parsed per rectangle: 1.35 s against 0.10 s for 70 matches on an 840-span page) and CI-004 (`#203`, the venv's ruff 0.15.5 against the hook's pinned v0.8.6, which disagree about formatting while `make check` runs neither).
- [x] `make check` **409 passed**, coverage **84.88%**; `ruff` and `mypy --strict` clean.

## Fix round 5 — the second signature's two Majors (one closed, one open)

- [x] Reproduce Major 1 before touching anything: a 60 pt watermark drawn BEFORE ten lines makes the page refuse; drawn AFTER them, with nothing else different, it converts. Span order decided a document's fate, and this revision is where it became fatal — the watermark was identified as the object being replaced, no trim can reach every glyph of a page-sized object, and a refused trim that reaches a neighbouring line now raises.
- [x] Fix it with the identification change the reviewer prescribed, and only that: `_target_span` takes the span whose bbox best matches the rect (identical bbox first, then largest overlap-over-union), both order-independent. All eight watermark variants now convert with every line kept, and the 32 pre-existing rows stay green.
- [x] Pin it with four rows (watermark first and last x two leadings) and capture the RED with the precision the fix deserves: restoring the first-containing-span rule fails exactly the two watermark-first rows, the watermark-last controls stay green.
- [x] Major 2 (below ~0.72 em the neighbour's box holds the centre, so the real target's lines were redacted SILENTLY) — **CLOSED by CORE-006**, which implemented the recommended design: verify the consequence instead of predicting a safe rectangle. Not fixed by repairing the identification, which stays CORE-004 (`#201`, now closed): three axis/identification attempts were tried and reverted here, each recorded in `verification.md` with why, and the check makes the wrong identification cost a refusal rather than a line.
- [x] Correct two claims of this spec that the round found false: `f9`'s "tighter than its glyph height is REFUSED" (true only from about 0.75 em up, now scoped and the open range named) and the scope row's "nothing else rides along" (the commit range also carries the release bump and lessons 021/022).
- [x] `make check` **413 passed**, coverage 84.9%; `ruff` and `mypy --strict` clean; `ruff format --check` now passes for BOTH the venv's ruff and the pinned hook, which is the claim the second signer caught regressing.
