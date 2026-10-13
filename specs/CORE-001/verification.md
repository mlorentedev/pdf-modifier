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

The document stays outside the repository; the fixture in the test is synthetic and reproduces the same shape.

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
