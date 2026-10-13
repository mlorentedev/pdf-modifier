# CORE-001 — verification

Every claim below is a command and its output, produced in the session that made the change.

## The defect reproduced

```
$ uv run pytest tests/unit/core/test_replacement_preserves_following_lines.py -q --no-cov
3 failed, 3 passed
  FAILED [...wider-object-per-line]
  FAILED [...narrower-object-per-line]
  FAILED [...shorter-object-per-line]
  PASSED [...single-object] ×3
```

Fails only in the structure that has the defect, and the passing half is kept to record which structure is not affected.

## The mechanism, isolated

Redacting **only** the target line's own tight box on a ten-line fixture:

```
ARC: 00                 y=139.9 .. 152.5
AC:  68D489883C5B7A25   y=150.9 .. 163.5   <- rect redacted: [72.0, 150.9, 185.4, 163.5]
CVM: 5E0000             y=161.9 .. 174.5

after: 7 lines (was 10)   ARC gone   CVM gone   AC gone
```

Three lines removed by a rectangle covering one. Line spacing 11.0 pt against a line height of 12.6 pt leaves 1.6 pt of overlap between neighbours, and `apply_redactions` removes every glyph that intersects.

## Round 2 — the review's Blocker, reproduced and closed

Round 1 (`nan/mimo-v2.6-flash`) returned **FAIL**: one REAL Blocker. The trim changed `y` only, so a neighbour **on the same line** — label and value drawn as two objects, which is how a receipt emits a key-value line — dragged `y1` onto the target's own `y0`, the rect collapsed to area 0, and the guard handed the **raw, unfitted** rect back to the redactor. Reproduced here before the fix, and re-run after it.

### The Blocker, end to end through `PDFModifier.process`

Same ten-line block, with the target line drawn as two objects (the value in another colour):

```
spans on the AC line:
    'AC:  ' bbox= (72.0, 150.94, 99.0, 163.54)
    '68D489883C5B7A25' bbox= (99.0, 150.94, 185.4, 163.54)
```

Before the fix, replacing the value span:

```
lines 10 -> 11
missing = ['ARC: 00', 'CVM: 5E0000']
```

`ARC: 00` and `CVM: 5E0000` — dropped again, by the code that exists to stop exactly that. The review's trace, replayed on this fixture with the round-1 trim, is the arithmetic of it:

```
$ uv run python /tmp/old_trim_trace.py
  neighbour 'ARC: 00' bbox=(72.00,139.94,109.80,152.54) -> (99.000,152.547,185.400,163.540) area=949.7950
  neighbour 'AC:  ' bbox=(72.00,150.94,99.00,163.54)   -> (99.000,152.547,185.400,150.927) area=0.0000
ROUND-1 y-only trim -> area=0.0000
guard: area <= 0 -> return the RAW rect
```

(The review reported the same collapse as `y1=150.927 area=0.0000 → final = RECT ORIGINAL`; its trace printed the label as the rect because both spans sit on one band, and the outcome is the same rectangle.)

After the fix, the same span, the same fixture:

```
$ uv run python /tmp/trim_trace.py
TRIM by '68D489883C5B7A25' bbox=(99.00,150.94,185.40,163.54)
  -> (99.010,152.547,185.400,161.927)  area=810.3371
  -> x trimmed: True   y trimmed: True
missing = []
```

`x0` moves off the label on the same line, `y0` and `y1` move off the lines above and below, and the rect keeps a non-zero area. Re-running the end-to-end repro on the fixed code gives `missing = []`.

### Where the replacement lands

```
before
    '68D489883C5B7A25' origin= (99.0, 160.0) bbox= (99.0, 150.94, 185.4, 163.54)
after
    '9F3C1D7A4E620B85' origin= (99.0, 160.0) bbox= (99.0, 150.94, 185.4, 163.54)
```

Identical origin and bbox: the new value is drawn where the old one was, on the label's baseline. One caveat recorded rather than hidden: `get_text()` on that output lists **11** lines for 10, because the re-inserted value is a separate text object appended to the page's content stream, so the extractor reports it after `CVM` instead of inside the `AC:` line. Its geometry is byte-identical to the span it replaced, so it renders in the same place — the count is an extraction-order artifact of a two-object line, and it is why the fixture asserts **set inclusion of the input's lines**, never a line count.

### RED, with the fitter neutralised

Neutralisation: `return fitz.Rect(rect)` inserted as the fitter's first statement, the tree otherwise untouched and restored immediately after.

```
$ uv run pytest tests/unit/core/test_replacement_preserves_following_lines.py -q --no-cov -k two_spans
3 failed, 7 deselected
  FAILED [...two_spans[wider]]   FAILED [...two_spans[narrower]]   FAILED [...two_spans[shorter]]

$ uv run pytest tests/unit/core/test_replacement_preserves_following_lines.py -q --no-cov \
    -k "two_spans or (single-object and not collapsing)"
3 failed, 3 passed, 4 deselected

$ uv run pytest tests/unit/core/test_replacement_preserves_following_lines.py -q --no-cov
7 failed, 3 passed
```

One row's message, naming the same two lines as the review's repro:

```
E  AssertionError: the replacement of a 16-character span on a line drawn as two objects
   dropped 2 line(s) that were not replaced: ['ARC: 00', 'CVM: 5E0000']
```

**On the numbers.** The task asked for `3 failed / 3 passed`. That is what the two-span rows against the single-object control give (`-k "two_spans or (single-object and not collapsing)"`), and it is the pair that matters: the failing structure and the structure that never had the defect. The new rows alone are `3 failed`; the whole file is `7 failed / 3 passed`, because neutralising the fitter also breaks the three round-1 `object-per-line` rows and the guard test. Three selections, one behaviour, and the narrowest one overstates nothing.

### GREEN

```
$ uv run pytest tests/unit/core/test_replacement_preserves_following_lines.py -q --no-cov
10 passed

$ uv run pytest tests/unit/core -q --no-cov
187 passed, 11 skipped          (177 before the fix; 183 at round 1)

$ make check
391 passed, 19 skipped, coverage 84.38%   (gate 80%)   ruff clean, mypy --strict clean
```

### The guard: a collapse is reported, not silently delegated

The round-1 guard's failure was not that it existed but what it returned. Two candidate replacements were measured before either was written:

```
$ uv run python /tmp/probe_dot2.py     # how much of the target must be covered to remove it
frac=0.0    rect_w=  0.020 -> ['ARC: 00', 'AC:  68D489883C5B7A25', 'CVM: 5E0000']   <- nothing removed
frac=0.001  rect_w=  0.086 -> ['ARC: 00', 'AC:  68D489883C5B7A25', 'CVM: 5E0000']   <- nothing removed
frac=0.01   rect_w=  0.864 -> ['ARC: 0', 'AC:  8D489883C5B7A25', 'CVM: E0000']
frac=1.0    rect_w= 86.400 -> ['ARC:', 'AC:', 'CVM:']
```

A collapsed rect is not a small rect: at 0.02 pt it removes **no glyph at all**, so a "tiny rect" fallback would leave the original text sitting under the replacement. There is no safe rectangle to fall back to, so the fit raises `PDFModifierError` naming the page and both rectangles, and a named test pins it:

```
$ uv run pytest tests/unit/core/test_replacement_preserves_following_lines.py::test_a_collapsing_fit_raises_instead_of_redacting_the_raw_rect -q --no-cov
1 passed
```

Before making it loud, the branch was measured across the suite that already existed, so the change could not be assumed harmless:

```
GUARD PROBE: calls=64 collapses=0
183 passed, 11 skipped
```

## Against the real document, not only the fixture

The first attempt at this **appeared to pass and proved nothing**: the reproduction script still had the offending substitution commented out — disabled as a workaround for this very defect — so the neighbours survived with the fix doing no work. With the substitution restored and active, which is the operation that used to take the two lines:

```
ARC: present   CVM: present   new value: present   old value: absent   lines: 135
```

The document stays outside the repository; the fixture in the test is synthetic and reproduces the same shape. **Scope of that "old value: absent" line, narrowed after round 2:** it holds on the shapes measured here, and round 2 found one where it does not hold — a neighbour overlapping the target's own glyph run, which left part of the value on the page (round 3 above). It is a claim about this document's shape, not about the class; the class is now carried by the per-shape rows and the residue assertion in the test file.

## Round 3 — the review's Major finding, reproduced and closed

Round 2 (`nan/deepseek-v4-flash`) also returned **FAIL**, with one REAL Major: a same-band neighbour that **overlaps the target's own glyph run** (an overprint, a stamp, any doubled text object) was classified as "beside" the target, so the x-trim cut **inside** the target. Redaction is per character, so the characters left outside the rect survived *under* the replacement: the old value stayed partly visible, and nothing failed.

### The finding, reproduced here first

Same tight block, the value drawn together with a second object over its first six characters:

```
  span 'ARC: 00'            bbox=(72.0, 62.9, 109.8, 75.5)
  span '68D489883C5B7A25'   bbox=(72.0, 73.9, 158.4, 86.5)   <- the target
  span 'ZZZZZZ'             bbox=(72.0, 73.9, 104.4, 86.5)   <- overlapping, x1 < centre
  span 'CVM: 5E0000'        bbox=(72.0, 84.9, 131.4, 97.5)

BEFORE: ['ARC: 00', '68D489883C5B7A25', 'ZZZZZZ', 'CVM: 5E0000']
AFTER : ['ARC: 00', '68D489', 'ZZZZZZ', 'CVM: 5E0000', '9F3C1D7A4E620B85']
```

`68D489` — the first six characters of the replaced value — is still on the page, with the new value drawn after it. The reviewer's two fixtures and this one agree.

### The rule that closes it

The invariant the axis-only rule was missing: **a trim may not lose a glyph of the object being replaced.** `apply_redactions` removes a character only if the rect reaches it, so a candidate rect is kept only if it still reaches every character of the target. The target is the span holding the rect's centre, and its characters come from `get_text("rawdict")` — the question is put to the document instead of to a heuristic about two bounding boxes, which is where rounds 1 and 2 both went wrong.

A neighbour that would fail that test is not a neighbour to trim against: it shares the target's own ink, so the rect covers both and the untrimmed rectangle is kept. That is the reviewer's own recommendation ("classify a neighbour that materially overlaps the target span as part of the object being replaced"), decided per character rather than by a threshold.

```
$ uv run python /tmp/repro_overprint.py      # the overlap shape above
AFTER : ['ARC: 00', 'CVM: 5E0000', '9F3C1D7A4E620B85']
```

The value is gone and both neighbouring lines survive. The overlapping object goes with the target — asserting that *it* survives would assert the defect back, since a redaction that reaches one of two objects sharing a glyph run reaches the other.

### RED, with the coverage rule neutralised (the precise one)

Neutralisation: `_is_safe_trim` returns `candidate.get_area() > 0`, so the axis rule stays and only the new glyph-coverage rule is removed.

```
$ uv run pytest tests/unit/core/test_replacement_preserves_following_lines.py -q --no-cov
10 failed, 9 passed
```

The 10 failures are the 9 overlapping-neighbour rows plus the guard's test; the 6 original rows and the 3 two-span rows stay green, so the coverage rule is pinned by exactly the shape it was written for. Each overlap shape leaves a different piece of the value:

```
'nested'           -> ['48', '68', '89', '8D', 'D4'] survived
'overlapping-head' -> ['48', '68', '89', '8D', 'D4'] survived
'overlapping-tail' -> ['25', 'A2'] survived
```

### RED, with the whole fitter neutralised

```
$ uv run pytest tests/unit/core/test_replacement_preserves_following_lines.py -q --no-cov
16 failed, 3 passed
```

The 3 that pass are the three `single-object` rows: the structure that never had the defect. Same shape as round 1's RED, on a fixture set three times larger.

### GREEN

```
$ uv run pytest tests/unit/core/test_replacement_preserves_following_lines.py -q --no-cov
19 passed

$ uv run pytest tests/unit/core -q --no-cov
196 passed, 11 skipped

$ make check
400 passed, 19 skipped, coverage 84.63%   ruff clean, mypy --strict clean
```

### Finding 2 (complexity) — applied, not waived

The same round measured the fitter at **CC ≈ 11 and nesting depth 5**, above the repo's thresholds (`< 10`, `< 4`). The rewrite decomposes it into six functions with one job each:

```
_text_spans                             CC=4   nesting=0  code_lines=4
_glyph_boxes                            CC=3   nesting=1  code_lines=3
_trim_away_from                         CC=4   nesting=2  code_lines=11
_is_safe_trim                           CC=3   nesting=1  code_lines=3
_fit_redaction_to_its_own_text_object   CC=7   nesting=2  code_lines=17
_refuse_collapsed_fit                   CC=5   nesting=0  code_lines=10
```

Checked with the repo's own tool, and the tool was shown to fire before its verdict was trusted:

```
$ uv run ruff check --select C901 --config "lint.mccabe.max-complexity=10" src/pdf_modifier/core/modifier.py
All checks passed!

$ uv run ruff check --select C901 --config "lint.mccabe.max-complexity=2" src/pdf_modifier/core/modifier.py
Found 17 errors.        <- the rule is running; at 10 nothing is over
```

### Finding 3 (fail-loud guard) — accepted, disclosed, and checked in the layers

A collapsed fit raises `PDFModifierError`, which `process` re-raises: one unfit rect fails the whole conversion rather than producing a partly-corrupt file. **This is the intended behaviour and it is accepted, not waived** (lesson-023: a guard must never fall back to the value from before the fix). It is bounded by measurement rather than by hope: instrumenting the fitter across the whole suite — `backend/scripts/probe_fitter_reachability.py`, which prints the count on exit — gives **125 fits, 15 refused trims, 1 collapse and 1 unidentified target, the last two both from the guard's own stub-page rows and none from a real document**. (Round 3 measured 0 collapses in 68 fits, on a smaller suite; the round-4 count was 121 fits and no refused-trim counter, which is the blind spot round 5's second signer named — the one refusal that cost content was invisible.) The only fit that reaches the collapse branch is the test that exists to reach it.

Surfaced to the user, not swallowed: `interfaces/cli.py`, `interfaces/mcp.py` and `web/routes/pdf.py` all catch `PDFModifierError` and report it (the API as a 400 with the message), and `batch_process` records it per file so one unfit document does not stop a batch. The failure needs no new exception type, which is why the layers needed no edit.

### Finding 4 (claim broader than its fixtures) — applied above

"Old value gone" is now scoped to the shapes measured, and the missing assertion is in the test file: `surviving_fragments` checks that no fragment of the replaced value remains, at a 2-character window after the measurement that a 4-character window missed a 3-character tail and a 1-character window flags ordinary digits.

### One more defect the new check found in itself

The first version of the residue assertion reported the fix as broken: `3C` occurs in both the old value and `9F3C1D7A4E620B85`, so a window shared with the replacement reads as residue. The subtraction of the replacement's own windows is that fix, and it is why the check is described here rather than just trusted.

## Round 4 — round 3's two Majors, one measured rule, and a policy stated

Round 3 (`nan/deepseek-v4-flash`) also returned **FAIL**, with two REAL Majors and three minors. Both Majors were reproduced here before anything changed, and both came from one mistake: the safety check was asking a question the redactor does not answer.

### The redactor's predicate, measured

`_is_safe_trim` accepted a candidate whenever it **intersected** a glyph. `apply_redactions` does not work that way. Bisecting the transition at five font sizes shows it removes a character once the rectangle covers **10.0% of the character's width**, at every size — a fraction of the box, not a distance:

```
  fontsize=6.0   char width=  3.60  removal threshold=0.360 pt  (10.0% of the char width)
  fontsize=9.0   char width=  5.40  removal threshold=0.540 pt  (10.0% of the char width)
  fontsize=12.0  char width=  7.20  removal threshold=0.720 pt  (10.0% of the char width)
  fontsize=18.0  char width= 10.80  removal threshold=1.080 pt  (10.0% of the char width)
  fontsize=24.0  char width= 14.40  removal threshold=1.440 pt  (10.0% of the char width)
```

So a rectangle reaching a glyph by a 7% sliver passed the check and the glyph stayed on the page. The floor was set to 0.15 at the time, above the measured 10% and above that sliver. **The justification written with it was wrong**, and round 5's second signature is the reason it is corrected here: "a check stricter than the redactor costs a refused trim, and a refused trim only leaves the rectangle where it was" reads as harmless, and leaving the rectangle where it was is *the defect this file exists to fix*. A refused trim is the trim that keeps the rectangle off the neighbouring lines. The floor is now **0.12** — the measured transition on both axes plus a small margin — and a refusal that would cost another line its characters raises instead of proceeding.

### Major A: one character of the replaced value survived (Finding 1)

The reviewer's fixture, rebuilt here: a label whose **box** crosses the value's first glyph by 0.4 pt — `ACCOUNT: ` ends in a space, so its box runs 5.4 pt past its ink:

```
  'ACCOUNT: '            (72.0, 73.9, 120.6, 86.5)
  '68D489883C5B7A25'     (115.6, 73.9, 202.0, 86.5)
```

`intersects` accepted a trim to x=120.61; the glyph box is (115.6 .. 121.0), and 0.39 pt of overlap is not enough for the redactor, so `6` stayed, drawn at the same origin as its replacement. With the floor the trim is refused, the rectangle keeps x0=115.6, and the value goes whole:

```
$ uv run python /tmp/sliver_check.py
spans after: ['ARC: 00', 'ACCOUNT:', 'CVM: 5E0000', '9F3C1D7A4E620B85']
```

### Major B: the shared-ink policy, stated and pinned (Finding 2)

When a neighbour's **ink** lies inside the fitted rectangle — not a sliver, but characters drawn in the same place — the coverage rule refuses the trim, the raw rectangle is kept, and the neighbour's characters inside it are redacted and never re-inserted:

```
before: 'ACCOUNT: '  +  the value drawn at x=84
after : 'AC'                                    <- 'COUNT:' was inside the target's rectangle
```

**Accepted, and no longer silent.** There is no geometry that separates two objects drawn in the same place: a redaction that reaches one reaches the other. The alternatives were refusing the whole document — worse for a receipt that is otherwise fine — or re-inserting the neighbour's characters, a capability this repair does not add (ADR-014 condition 3, and a re-insertion through a subset-embedded font is the trap `#179` lost a day to). A named row pins the exact shape of the loss — the label survives as a truncated prefix of itself, with nothing added or reordered — so it cannot grow unnoticed, and the capability is filed as CORE-003.

### Minor A: the residue assertion could not see one character (Finding 3)

`surviving_fragments(window=2)` is blind to a one-character residue by construction, which is exactly what Major A left behind. `surviving_value_spans` reads the output's own text objects instead — after a redaction rewrites what is left of the object, a single survivor is its own object — and every row asserts it now.

### Minor B: an unidentified object was a licence to trim (Finding 4)

`_glyph_boxes(None)` is `[]` and `all()` over an empty list is `True`, so a target that could not be identified made every trim "safe" and rounds 1-2's misclassification would have returned silently. It is a refusal now, with its own stub-page row, on the same principle as the empty rectangle. Reachability, from `backend/scripts/probe_fitter_reachability.py`: **125 fits in the suite, 1 with an unidentified target, and it is this row's own stub page** — no real document reaches the branch.

### Minor C: the layer-surfacing claim, cited (Finding 5)

Round 3 marked "checked to surface in CLI/MCP/API/batch" as unverified, correctly. It is a citation now rather than a claim: `interfaces/cli.py` (five catch sites), `interfaces/mcp.py:37`, `web/routes/pdf.py:105,166` and `batch_process` each catch `PDFModifierError`, and `tests/unit/interfaces/test_mcp.py::TestMCPErrorHandling` exercises the MCP path. The document-level failure stays accepted for the collapse guard.

### RED, with the measured floor neutralised

```
$ uv run pytest tests/unit/core/test_replacement_preserves_following_lines.py -q --no-cov
3 failed, 21 passed
E  AssertionError: the value is still on the page in pieces after a 0.4 pt overlap:
   ['6'] survived, because the trim was accepted on `intersects` rather than on the
   share of the glyph the redactor actually needs
```

Exactly the three sliver rows fail; nothing else moves. Neutralising the **refusal** adds its own row (4 failed), and neutralising the **whole fitter** gives **21 failed / 3 passed** — the 3 being the single-object control.

### GREEN

```
$ uv run pytest tests/unit/core/test_replacement_preserves_following_lines.py -q --no-cov
24 passed

$ uv run pytest tests/unit/core -q --no-cov
201 passed, 11 skipped

$ make check
405 passed, 19 skipped, coverage 84.70%   ruff clean, mypy --strict clean
```

### Performance, including what round 3 measured

`_text_spans` parses the page once per rectangle, so a page with N replacements does N parses. Round 3 measured 60 replacements on a dense page in **0.279 s**; this session measured 40 on a lighter page in **0.137 s**. Same order, and now recorded: it is the price of asking the document which characters are there, instead of inferring them from two bounding boxes.

## Round 5 — the round-4 verdict, and what it left

Round 4 (`nan/glm5.3-flash`, drawn from the pool) returned **PASS** against `a479628`. It is the first round that did not fail, and it is worth recording *how* it checked rather than only that it passed: the reviewer re-ran the whole RED matrix itself — applying each mutation, restoring the tree, and checking `git status` — and got exactly the recorded numbers (`intersects` → 3 failed / 21 passed, the three sliver rows; refusal neutralised → 1 failed; whole fitter neutralised → 21 failed / 3 passed), re-ran `make check` (405 passed, 84.70%), and re-ran the reachability probe with the invocation the script's docstring prescribes.

It left two THEORETICAL minors found by reading rather than by a failing fixture, and one note about how to read a future mutation run:

| Finding | Disposition | Where |
|---|---|---|
| The 15% floor is applied to the glyph's **height** as well, and only the **width** transition was measured (10.0%, five sizes). Argued from the code, not reproduced: a height-only refusal does not appear in the suite. | **Ticketed** | CORE-004 (`#201`): bisect the height transition the way the width one was bisected, then set the constant from the measurement or say why one covers both. |
| Target identification takes the **first** span whose bbox holds the rect's centre, so with two containing spans (a stamp over the value) rawdict order decides whose glyphs are protected. Argued, not reproduced. | **Ticketed** | CORE-004 (`#201`): prefer the span whose bbox best matches the rect, with a stub-page row for the two-candidate case. |
| The overprint rows are insensitive to weakening the floor *below* `intersects` (13 rows fail at floor 0.0, 3 at the `intersects` baseline) — protection comes from `_is_safe_trim`'s empty-candidate path below that line. A mutation run reading the 3-row delta as the floor's total coverage would under-credit it. | **Recorded** | CORE-004 (`#201`), under "Note for mutation testing", so the recipe can carry it. |
| The accepted shared-ink deletion (a label losing the characters the rectangle covers) stands as dispositioned in round 3. | **Already tracked** | CORE-003 (`#199`), pinned by `test_a_label_sharing_the_target_ink_loses_exactly_the_shared_characters`. |

No finding was declined. `proposal.md` declares `risk: high`, so the archive gate requires a second signature from another vendor; this review is the first, and `dotf spec review CORE-001 --second` launches the second.

## Round 6 — the second signature's Major, reproduced and closed

Round 5 is the first signature (`nan/glm5.3-flash`, PASS). The second, required because `proposal.md` declares `risk: high`, was `anthropic-review/claude-sonnet-5-5`, and it returned **FAIL** with one REAL Major that the first signature did not find. It was reproduced here before anything changed, and it is the reason CORE-001 did not archive at `a479628`.

### The finding

With the leading tighter than the glyph height, the fitter can be left with no safe rectangle, and the revision at `a479628` chose silently which line to lose. At 12 pt on 9 pt leading (ratio 0.75), replacing the third line:

```
$ uv run python /tmp/rv_repro.py
font=12 leading=9 (0.75): ['keepkeep0', 'keepkeep1', 'keepkeep2', 'p4', 'keepkeep5', 'keepkeep6', 'keepkeep7', 'ZZZZ']
font=9  leading=7 (0.78): ['keepkeep0', 'keepkeep1', 'keepkeep2', 'p4', 'keepkeep5', 'keepkeep6', 'keepkeep7', 'ZZZZ']
font=10 leading=8 (0.80): ['keepkeep0', 'keepkeep1', 'keepkeep2', 'p4', 'keepkeep5', 'keepkeep6', 'keepkeep7', 'ZZZZ']
```

`keepkeep4` became `p4`: the line BELOW the target lost six characters, with no error and no warning. The mechanism, traced (`/tmp/rv_trace.py`): the target's glyph box is 16.8 pt tall and the next line starts 9 pt lower, so the two boxes overlap by 7.8 pt. Each single trim is accepted and the rectangle is left thin; the next trim is then refused because it would leave the target under the floor -- and the rectangle it keeps still reaches the line below.

### Why no floor value fixes it, and why the docstring was wrong

The second signer proposed deriving the floor from the measured transition. Measured here, the transition is **10.0% on both axes** (width at 6/9/12/18/24 pt, height at the same sizes), so 0.15 was over-strict -- but lowering the floor is not sufficient, and the sweep shows it:

```
floor=0.15   12/9:LOST ['keepkeep4'] | 9/7:LOST ['keepkeep4'] | 10/8:LOST ['keepkeep4']
floor=0.12   12/9:LOST ['keepkeep4'] | 9/7:LOST ['keepkeep4'] | 10/8:OK
floor=0.10   12/9:LOST ['keepkeep4'] | 9/7:OK                 | 10/8:OK
```

At the exact 10% transition the tightest case still loses the line, because the trim that would spare it leaves 7% of the target's own glyphs -- below the redactor's threshold, so accepting it would leave the replaced value on the page under its replacement. **There is no rectangle that both covers the target and spares that line.** The only remaining choice is which failure to have, and the revision at `a479628` was choosing silently.

The related defect is prose: the floor's own comment claimed "being stricter than the redactor costs a refused trim, and a refused trim only leaves the rectangle where it was". Leaving the rectangle where it was IS the defect this file fixes. The comment is corrected, and it now says what a refusal costs.

### The fix

- The floor is **0.12**: the measured 10% transition plus a small margin, on both axes (both measured, so the first signer's "height was never measured" Minor is answered by measurement rather than by argument). Every point above the transition is a trim refused for no reason, and an unnecessary refusal is now an unnecessary failure -- so the boundary row below exists to keep it honest.
- A refused trim that would cost a neighbour **on another line** its characters raises `PDFModifierError`, naming the page, the target's rect and the neighbouring line. Refusing beats dropping a line, and it is the same rule the collapsed and unidentified fits already follow. `_refuse_trim_that_drops_another_line` is a new helper; the fitter stays under the repo's thresholds (CC <= 8, nesting <= 2).
- A co-located neighbour (same band: a label under a value, an overprint) keeps its accepted behaviour: its ink is in the same place, so there is no rectangle to prefer and the fit is not refused. That boundary is deliberate -- CORE-003 (`#199`) tracks the capability that would re-insert those characters.

```
$ uv run python /tmp/tight_matrix.py
font=12 leading=9 (0.75): REFUSED
font=9  leading=7 (0.78): REFUSED
font=10 leading=8 (0.80): converted; lost=none; new_value=True
font=12 leading=10 (0.83): converted; lost=none; new_value=True
font=9  leading=8 (0.89): converted; lost=none; new_value=True
```

### RED, three mutations, each aimed at a different claim

```
M5  refusal neutralised (silent damage returns)     2 failed / 26 passed   <- the two refusal rows
M6  floor back to the over-strict 0.15               1 failed / 27 passed   <- the 10pt-on8pt boundary
M7  floor 0.5 (the second signer's probe)            2 failed
```

M6 is the answer to the second signer's sharpest methodological point -- "mutating the floor to 0.5 leaves all 24 tests green", so nothing pinned the floor from above. Something does now: an over-strict floor is caught by the boundary row, not only an under-strict one.

### Minor findings from the second signature, dispositioned

| Finding | Disposition | Evidence |
|---|---|---|
| The probe cannot see refused trims, so "a refusal costs nothing" was unmeasurable | **Applied** | `probe_fitter_reachability.py` counts them: 15 refused trims across the suite, of which the damaging one is gone. |
| Re-parsing the page per rectangle: 70 matches on an 840-span page in 1.35 s against 0.10 s at the base, 840 matches in 18.8 s against 4.2 s | **Ticketed** | CORE-005 (`#202`): parse the page once per page rather than once per rectangle. Accepted here because the alternative is inferring the glyphs from bounding boxes, which is the defect. |
| `ruff format --check` fails on the regression file | **Applied** | Real, and it exposed a skew rather than a formatting slip: the venv resolves ruff 0.15.5 while `.pre-commit-config.yaml` pins v0.8.6, and the two formatters disagree on those lines. The file now satisfies both, and the skew is filed as CI-004 (`#203`). `make check` does not run `ruff format`, which is why it was green despite this. |
| The two-candidate span-order path, and rotated text | **Already ticketed** | CORE-004 (`#201`), filed from the first signature's same finding; the second signature adds "rotated text is untested rather than demonstrated". |
| Is leading/font below 0.8 in scope? | **Answered: yes** | The proposal says "tight page" and the corpus is thermal-receipt data, where 12 pt on 9 pt leading is plausible. Declaring it out of scope would have turned a reproduced content loss into a documented limit, so the code was changed instead. |

## ADR-014 conditions

| Condition | Evidence |
|---|---|
| Failing test first, synthetic fixture | `test_replacement_preserves_following_lines.py`, fixture generated inside the test. The round-1 RED commit (`1c0ae90`) is on `fix/CORE-001-reflow-drops-lines` and **not** in `master`'s history — `git merge-base --is-ancestor 1c0ae90 HEAD` exits **1**, because #186 was squash-merged and `ae28471` carries test and fix together. Round 2's RED is the neutralised-fitter run above |
| No public contract change | `PDFModifier`'s functions, types and signatures unchanged; the fitter is private and grows two private helpers, and a fitting failure reuses `PDFModifierError` — **no new exception type**, so every layer that already catches it handles it without edits |
| Scoped to the defect | The diff is the fitter's trim and its guard, plus the regression tests and this spec. Nothing else rides along |

## How this relates to #179

The dropped-lines defect is **not** one of #179's original five findings. It was found afterwards, by generating a real receipt, and added to that ticket with priority **first** there — because it is the only one that destroys content rather than failing to add or preserve it. #179 stays open for the other findings; CORE-001 closes only this one. The chain of reasoning, including the two hypotheses that were falsified by measurement, is in that ticket's comments.

## Promotion candidates

- [ ] Lesson for the repo's `docs/lessons/`? yes: docs/lessons/lesson-023-a-guard-that-returns-the-pre-fix-value-reinstates-the-defect.md
- [ ] ADR-worthy decision for `docs/adr/`? no: ADR-014 already authorises this class of core change and its three conditions are unchanged
- [ ] New pattern candidate for `00_meta/patterns/`? no: the geometry is repository-specific; the transferable half is the lesson above

## Not covered here

The other findings of #179 — the `--help` entry point, cloning a repeated block, metadata, page numbering — are untouched by this change and remain open on that ticket.
