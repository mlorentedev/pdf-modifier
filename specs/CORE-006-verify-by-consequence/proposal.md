---
id: "CORE-006-verify-by-consequence"
type: spec
status: draft # draft | implementing | verifying | archived
created: "2026-10-13"
issue: "mlorentedev/pdf-modifier#201"   # repo#NNN — GitHub issue / Project item that tracks this spec
risk: high   # it changes how every page with a replacement is processed, in the two files ADR-014 closes
review: required
tags: [spec, proposal]
template_version: "1.0"
---

# CORE-006-verify-by-consequence

## Why

CORE-001's repair decides whether a redaction is safe by *predicting* it: shrink the rectangle away from the neighbours, keep the shrink only if the object being replaced is still covered, and refuse when no rectangle satisfies both. Four independent review rounds found four geometries where the prediction is wrong — a same-line neighbour, an overlapping glyph run, a tight block, a page-sized object behind the text — and the current one is worse than wrong: below about 0.72 em leading the neighbour is mistaken for the target, the real target's neighbours are redacted, and **nothing fails** (`specs/CORE-001/verification.md`, round 8). A prediction of that shape has no finite argument for correctness; the *consequence* does, and it is one comparison: after the redaction, does every text object that was not replaced still carry its characters?

## What

After a page's replacements are applied, the modifier re-reads that page's text and compares it, object by object, against the text the page had before. If any object that was not the replacement target lost characters — or vanished — the document is refused with `PDFModifierError` naming the page and the object, and no output is written.

Observable behaviour after this change: for a page with a replacement, either every non-target text object keeps its characters exactly, or the conversion fails loudly. There is no third outcome, at any leading, for any arrangement of overlapping objects — including the ones the rectangle heuristic still gets wrong, which become refusals instead of silent damage.

The existing trim logic stays, demoted from *the safety mechanism* to an optimisation: it reduces how often the consequence check has to refuse, and it is no longer trusted for correctness.

## Out of scope

- **Re-inserting** the characters of a neighbour the redaction covers (CORE-003, `#199`, option A). This spec turns silent damage into a refusal; making the page whole again is that ticket's work.
- **Rewriting the trim heuristics.** They are kept as they are, deliberately: their failures are the reason this spec exists, and moving them at the same time would make both changes unprovable.
- **The per-rectangle page parse** (CORE-005, `#202`). This spec adds one more read of the page per page; CORE-005 makes the existing reads cheaper. They are independent, and the performance numbers belong there.

## Risks / open questions

- **What counts as "the same object" across the two reads.** Comparing extracted *lines* of text is not enough: `get_text()` assembles lines from spans, so a page whose spans are split differently after the redaction would look changed when nothing was lost, and a lost character inside a line would look like a changed line rather than a lost object (CORE-001's rounds 2 and 3 both died on exactly this confusion). The comparison has to be per text object, with its box, and the algorithm needs a decision before implementation: match by index, by box, or by the sequence of characters.
- **Whose characters may legitimately change.** The replacement itself, and any object whose ink the replacement's rectangle cannot avoid covering (the co-located case, CORE-003, `#199`): no rectangle separates two objects drawn in the same place, so refusing would fail a document the user cannot fix. What that case may **not** do is stay silent -- the decision on CORE-003 is that the loss is *accepted and reported*, through the `warnings` list `ModificationResult` already carries, and this check is what makes it reportable. Everything outside that allow-list is a finding and refuses. Getting the boundary wrong produces either false refusals on co-located ink or a blind spot for exactly the case this spec is for.
- **Refusal blast radius.** A refusal fails the whole document, not the page. That is the existing convention (the collapse and unidentified-fit guards both do it) and it is right for silent content loss, but it means a document with one hostile page cannot be converted at all. Confirm against CORE-001's accepted behaviour before implementing.
- **Cost.** One extra page-text extraction per page that has a replacement, on top of the parse CORE-005 measures at 1.35 s for 70 matches on an 840-span page. Measure it before and after; if the cost doubles the conversion, the check has to be scoped (per redacted rectangle rather than per page) rather than dropped.
- **Does a correct prediction still exist?** If someone later proves the geometry, the check becomes a cheap assertion rather than the mechanism. Nothing here forecloses that.

## Acceptance criteria

- [ ] For a synthetic block whose leading runs from 0.45 em to 1.30 em (including 0.60, 0.70, 0.75, 0.78 em), converting a page either keeps every non-target text object's characters exactly — verified from the written output file, not from the in-memory page — or raises `PDFModifierError`. No leading in that range loses characters silently. `specs/CORE-001/verification.md` round 8 records the current failure: `cobo` 12 pt at 0.45/0.55/0.65 em losing `ROW03` and `ROW05`.
- [ ] The documents that convert today keep converting: the two-span receipt line, the overprint shapes, the 10 pt-on-8 pt boundary, the watermark page (both span orders). A refusal that turns a previously-safe document into a failure is as much a defect as a silent loss, and the rows exist in `backend/tests/unit/core/test_replacement_preserves_following_lines.py`.
- [ ] The check fires on a **planted** loss: a test in which the redaction is deliberately allowed to damage a neighbouring object (a stubbed or mutated fitter returning the raw rectangle) and the conversion refuses. A consequence check that cannot be shown to fire is a green check that reads nothing.
- [ ] The refusal names the page and the damaged object, and no output file is written (CORE-001's collapse guard sets the precedent).
- [ ] The one accepted case -- a co-located object whose ink the rectangle cannot avoid -- adds a `warnings` entry naming the page and the object, and does NOT refuse. Accepted is not the same as silent: `ModificationResult.warnings` already exists, so this costs no contract change, and a test asserts the warning is produced for CORE-003's fixture.
- [ ] ADR-014 conditions hold: a failing test against a synthetic fixture first, no public contract change (the existing typed error is reused), and nothing opportunistic in the diff.
- [ ] The extra cost is measured and stated, against CORE-005's numbers, whether or not it is optimised here.
- [ ] CORE-001's `features.json` f9 stops overstating: after this spec, its claim holds over the full range it names, or its range is corrected — whichever the implementation earns. CORE-001 archives only once that is true, because the criterion it declares is the one that is currently false.

## References

- Bitácora board: [#201](https://github.com/mlorentedev/pdf-modifier/issues/201) — carries the reproduction, the three reverted attempts and the recommendation this spec implements
- Related ADR: `docs/adr/adr-014-core-defect-exception.md` — the only reason `core/modifier.py` may be opened
- Related spec: `specs/CORE-001/` is the repair whose remaining Major this closes; this spec is the consequence check that makes its criterion true
- Related issues: CORE-003 (`#199`, re-insertion), CORE-005 (`#202`, the page re-parse)
- Lessons: `docs/lessons/lesson-023-a-guard-that-returns-the-pre-fix-value-reinstates-the-defect.md`, `docs/lessons/lesson-027-a-refusal-is-not-harmless-when-the-refusal-is-the-protection.md`
