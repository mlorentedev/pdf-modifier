# ADR-015: Refuse the conversion rather than lose content, and report what is lost unavoidably

- **Status:** Accepted
- **Date:** 2026-10-13
- **Deciders:** owner (product call on failing documents), implementer
- **Related:** ADR-014 (the core-defect exception that permits this file to be touched), `specs/CORE-001/`, `specs/CORE-006-verify-by-consequence/`, issues `#179`, `#199`, `#201`

## Context

`PDFModifier.process` replaces text by drawing redaction rectangles and re-inserting the replacement. A redaction removes every glyph its rectangle reaches, and in a real document the boxes of neighbouring lines overlap — tight leading, stamps, labels drawn under values, watermarks. The repair of that defect (CORE-001) shrank the rectangle to avoid the neighbours, and that shrink is a **prediction**: it is safe when the model of the page's geometry is right.

Four adversarial review rounds found four geometries where the prediction is wrong, each with a real reproduction:

1. a neighbour on the same line collapsed the rectangle and the guard returned the raw, unfitted one;
2. a neighbour overlapping the target's glyph run let the first characters of the *old* value survive underneath the new one;
3. a block whose leading is tighter than its glyph height lost a line **silently**;
4. a page-sized object drawn under the text was mistaken for the object being replaced, and whether the page converted at all depended on the order the text objects appear in the content stream.

Round 3's silent loss is the sharpest: the operation reports success, writes the file, and characters that were never the target are simply absent from the output.

## Decision

**The guarantee is stated on the outcome, not on the geometry.** After a page's replacements are applied, the modifier re-reads the page's text and compares it with the text before, glyph by glyph:

- a character that vanished and belonged to **an object the analyzer asked to replace** is the replacement working as intended;
- a character that vanished from **another object on the same line** is an accepted consequence of ink drawn in the same place — no rectangle separates it — and it is **reported** through `ModificationResult.warnings`, never silent;
- a character that vanished from **any other object** raises `PDFModifierError` naming the page and the object, and no output file is written.

The rectangle-fitting heuristic stays, demoted: it is now an *optimisation that reduces refusals*, and it is no longer what makes a conversion safe. A wrong prediction therefore costs a refused conversion or a warning, never content.

**Consequences, accepted deliberately:**

- Some documents that previously converted now **fail loudly** — the ones where a neighbouring line's characters would have been removed. Failing is the deliberate choice: the alternative is a file that silently differs from the input in ways nobody can see. This is the same policy ADR-014 already implies for content-destroying defects, now expressed as a check rather than as care.
- The co-located case (a label under a value, an overprint, a watermark crossing a line) keeps converting, and now produces a warning naming the object whose characters went with the redaction. Re-inserting those characters is CORE-003 (`#199`); until then, the loss is visible to the caller.
- One more page read per page with a replacement: measured at **+0.08 s (+3 %)** on a 840-span page with 70 matches, beside the per-rectangle parse CORE-005 (`#202`) tracks at 1.35 s.
- The check itself cannot be argued away by geometry, so a future fitter rewrite inherits it unchanged: whatever the rectangle logic does, the outcome is verified.

## Alternatives rejected

- **Keep predicting, and enumerate the geometries.** This is what four review rounds did, one reproduction at a time; each fix was correct for its shape and blind to the next, and the failures landed on content rather than on a test. A prediction with no finite argument cannot be closed by adding cases.
- **Refuse whenever a non-target object loses any character.** Simple and safe, but it fails documents whose ink genuinely cannot be separated — a label over a value, a stamp over the field — where the user cannot change the input and the previous behaviour was to convert. That case is accepted and *reported* instead.
- **Warn instead of refusing, for every loss.** Cheaper, and it removes the silence. Rejected because a line that follows the replaced text is exactly what this component promises not to drop: a warning on a file that silently differs from its input makes the promise unenforceable, and the caller has no way to repair the page.
- **Report the loss only in the logs.** Logs are not part of the API contract; `ModificationResult.warnings` already existed and reaches every interface (CLI, MCP, HTTP, batch) without a contract change.
