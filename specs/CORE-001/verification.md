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

A collapsed fit raises `PDFModifierError`, which `process` re-raises: one unfit rect fails the whole conversion rather than producing a partly-corrupt file. **This is the intended behaviour and it is accepted, not waived** (lesson-023: a guard must never fall back to the value from before the fix). It is bounded by measurement rather than by hope: the collapse branch was reached **0 times in 68 fits** across the suite before it was made loud, and the only synthetic case that reaches it is the guard's own test.

Surfaced to the user, not swallowed: `interfaces/cli.py`, `interfaces/mcp.py` and `web/routes/pdf.py` all catch `PDFModifierError` and report it (the API as a 400 with the message), and `batch_process` records it per file so one unfit document does not stop a batch. The failure needs no new exception type, which is why the layers needed no edit.

### Finding 4 (claim broader than its fixtures) — applied above

"Old value gone" is now scoped to the shapes measured, and the missing assertion is in the test file: `surviving_fragments` checks that no fragment of the replaced value remains, at a 2-character window after the measurement that a 4-character window missed a 3-character tail and a 1-character window flags ordinary digits.

### One more defect the new check found in itself

The first version of the residue assertion reported the fix as broken: `3C` occurs in both the old value and `9F3C1D7A4E620B85`, so a window shared with the replacement reads as residue. The subtraction of the replacement's own windows is that fix, and it is why the check is described here rather than just trusted.

## ADR-014 conditions

| Condition | Evidence |
|---|---|
| Failing test first, synthetic fixture | `test_replacement_preserves_following_lines.py`, fixture generated inside the test. The round-1 RED commit (`1c0ae90`) is on `fix/CORE-001-reflow-drops-lines` and **not** in `master`'s history — `git merge-base --is-ancestor 1c0ae90 HEAD` exits **1**, because #186 was squash-merged and `ae28471` carries test and fix together. Round 2's RED is the neutralised-fitter run above |
| No public contract change | `PDFModifier`'s functions, types and signatures unchanged; one private static helper changed, plus a fail-loud path on a fitting failure that reuses `PDFModifierError` — **no new exception type**, so every layer that already catches it handles this without edits |
| Scoped to the defect | The diff is the fitter's trim and its guard, plus the regression tests and this spec. Nothing else rides along |

## How this relates to #179

The dropped-lines defect is **not** one of #179's original five findings. It was found afterwards, by generating a real receipt, and added to that ticket with priority **first** there — because it is the only one that destroys content rather than failing to add or preserve it. #179 stays open for the other findings; CORE-001 closes only this one. The chain of reasoning, including the two hypotheses that were falsified by measurement, is in that ticket's comments.

## Promotion candidates

- [ ] Lesson for the repo's `docs/lessons/`? yes: docs/lessons/lesson-023-a-guard-that-returns-the-pre-fix-value-reinstates-the-defect.md
- [ ] ADR-worthy decision for `docs/adr/`? no: ADR-014 already authorises this class of core change and its three conditions are unchanged
- [ ] New pattern candidate for `00_meta/patterns/`? no: the geometry is repository-specific; the transferable half is the lesson above

## Not covered here

The other findings of #179 — the `--help` entry point, cloning a repeated block, metadata, page numbering — are untouched by this change and remain open on that ticket.
