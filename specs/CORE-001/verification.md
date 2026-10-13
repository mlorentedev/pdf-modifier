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

Three lines removed by a rectangle covering one. Line spacing 11.0 pt against a line height of 12.6 pt leaves 1.6 pt of overlap between neighbours, and `apply_redactions` removes every text object that intersects.

## After the fix

```
$ uv run pytest tests/unit/core -q --no-cov
183 passed, 11 skipped          (was 177)

$ make check
385 passed, 19 skipped, coverage 84.34%   (gate 80%)
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
| Failing test first, synthetic fixture | RED committed on its own (`1c0ae90`); fixture generated inside the test |
| No public contract change | `PDFModifier`'s functions, types and signatures unchanged; one new private static helper |
| Scoped to the defect | The diff is the helper plus its two call sites; no refactor rides along |

## Not covered here

The other findings of #179 — the `--help` entry point, cloning a repeated block, metadata, page numbering — are untouched by this change and remain open on that ticket.
