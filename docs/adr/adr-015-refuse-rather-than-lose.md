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
- a character that vanished from **another object that the rectangle which removed it shares a line with** is an accepted consequence of ink drawn in the same place — no rectangle separates it — and it is **reported** through `ModificationResult.warnings`, never silent. The rectangle that *removed* the character is the one that counts: a replacement drawn elsewhere on that line, reaching none of the lost object's ink, does not excuse the loss, and a lost character no rectangle could have reached (a whitespace-only span dropped while the line is rewritten) is not content and is not counted;
- a character that vanished from **any other object** raises `PDFModifierError` naming the page and the object, and no output file is written.

The rectangle-fitting heuristic stays, demoted: it is now an *optimisation that reduces refusals*, and it is no longer what makes a conversion safe. A wrong prediction therefore costs a refused conversion or a warning, never content.

**Consequences, accepted deliberately:**

- Some documents that previously converted now **fail loudly** — the ones where a neighbouring line's characters would have been removed. Failing is the deliberate choice: the alternative is a file that silently differs from the input in ways nobody can see. This is the same policy ADR-014 already implies for content-destroying defects, now expressed as a check rather than as care.
- The co-located case (a label under a value, an overprint, a watermark crossing a line) keeps converting, and now produces a warning naming the object whose characters went with the redaction. Re-inserting those characters is CORE-003 (`#199`); until then, the loss is visible to the caller.
- One more page read per page with a replacement: measured at **+0.08 s (+3 %)** on a 840-span page with 70 matches, beside the per-rectangle parse CORE-005 (`#202`) tracks at 1.35 s.
- The check itself cannot be argued away by geometry, so a future fitter rewrite inherits it unchanged: whatever the rectangle logic does, the outcome is verified.

**Two limits of this check, stated rather than implied:**

- **"Co-located" is a proxy for "unavoidable".** It is decided by a shared vertical band (>= 90 % of the shorter box), not by asking, per lost glyph, whether some rectangle could have covered the target and missed it. So a same-line neighbour whose characters a rectangle *could* have spared is warned where it should be refused. The loss is still reported, which is the promise above; tightening the classification is a new prediction about geometry and is tracked as CORE-007 (`#209`) rather than absorbed here.
- **The guard sees text, not graphics.** The comparison is glyph by glyph, so a redaction that costs line art (a rule, a border, a chart line) is invisible to it -- `apply_redactions` keeps the default `graphics` behaviour. The component promises not to drop *text* objects, and this is where that promise ends.

## Alternatives rejected

- **Keep predicting, and enumerate the geometries.** This is what four review rounds did, one reproduction at a time; each fix was correct for its shape and blind to the next, and the failures landed on content rather than on a test. A prediction with no finite argument cannot be closed by adding cases.
- **Refuse whenever a non-target object loses any character.** Simple and safe, but it fails documents whose ink genuinely cannot be separated — a label over a value, a stamp over the field — where the user cannot change the input and the previous behaviour was to convert. That case is accepted and *reported* instead.
- **Warn instead of refusing, for every loss.** Cheaper, and it removes the silence. Rejected because a line that follows the replaced text is exactly what this component promises not to drop: a warning on a file that silently differs from its input makes the promise unenforceable, and the caller has no way to repair the page.
- **Decide unavoidability per glyph (do it now).** The correct rule: for each lost character, ask whether a rectangle covering the target's own ink can miss it; refuse if it can. Rejected *at this spec's scale* rather than in principle -- it is a new prediction about geometry, the thing this ADR demotes, it changes which real documents convert, and the only instance found on a real document was a whitespace span. Tracked as CORE-007 (`#209`) with the recommended shape and the fixture it needs.
- **Report the loss only in the logs.** Logs are not part of the API contract; `ModificationResult.warnings` already existed and reaches the single-file CLI output, the MCP payload, the HTTP JSON and the batch result model without a contract change. Two surfaces do not yet show it: the web UI never reads `warnings`, and the CLI's batch table prints only `replacements_made` with status `OK`, so an accepted loss is invisible there. "Accepted is not silent" therefore holds where a consumer reads the list, which is what the field guarantees; making those two surfaces show it is CORE-008 (`#210`).
