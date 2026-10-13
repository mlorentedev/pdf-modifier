# CORE-006 — tasks, in the order they will be done

Written before the code exists, as the RED step ADR-014 requires. Each line is
small enough to see fail on its own; the first one is the reason
`core/modifier.py` may be opened at all.

## RED — the test that opens core/modifier.py

- [ ] Add the failing row at **0.60 em leading** to `backend/tests/unit/core/test_replacement_preserves_following_lines.py`: ten lines, one replaced, leading `0.6 * fontsize`, asserting the contract directly — every text object that was not the target keeps its characters, read from the written output file. It must FAIL today, with the loss printed, exactly as `specs/CORE-001/verification.md` round 8 records (`cobo` 12 pt: `ROW03` and `ROW05` lose characters).
- [ ] Record the RED output verbatim in `verification.md`. A row that fails for a different reason (an exception in the fixture) is not RED, it is a broken test.

## The comparison, decided before it is written

- [ ] Decide how two reads of a page are matched: by index, by box, or by character sequence. The comparison must survive the redaction rewriting what is left of the target (a partially redacted runner becomes a shorter object at the same origin) and must NOT report the target itself as damaged. Write the decision and the rejected alternatives in `verification.md` before implementing, because this is where CORE-001's rounds 2 and 3 both went wrong.
- [ ] Decide what may legitimately change: the replacement, and any object whose ink the replacement's rectangle was allowed to cover (CORE-003's accepted co-located case, `#199`). Everything else is a finding. Encode it as an explicit allow-list, with a test for each entry.

## GREEN — the check

- [ ] Capture the page's text objects with their boxes BEFORE the redaction, from the parse the fitter already does (`_text_spans`, `get_text("rawdict")`).
- [ ] After `apply_redactions` and the re-insertion, re-read the page and compare: any object that lost characters, or vanished, and is not on the allow-list, raises `PDFModifierError` naming the page and the damaged object, with the existing details convention (`page`, `rect`, plus the object's box). No output file is written — the collapse guard's precedent.
- [ ] Keep the trim logic untouched. It is an optimisation that reduces refusals now, not the safety mechanism.
- [ ] Sweep the leading range in a row-level parametrisation: 0.45, 0.60, 0.70, 0.75, 0.78, 1.00, 1.30 em, each asserting **refuse-or-preserve** and reading the outcome from the file.
- [ ] Confirm the documents that convert today still convert: the two-span receipt, the overprint shapes, 10 pt-on-8 pt, 12 pt-on-10 pt, the watermark page in both span orders.
- [ ] For the ONE accepted case -- a co-located object the rectangle cannot avoid -- emit a `warnings` entry naming the page and the object instead of refusing, and assert it for CORE-003's fixture (`test_a_label_sharing_the_target_ink_loses_exactly_the_shared_characters`). This is the decision recorded on `#199`: accepted and reported.

## The check must be shown to FIRE

- [ ] Planted loss: a test in which the fitter is made to return the raw, unfitted rectangle (the pattern CORE-001 already uses for its guard rows), asserting the conversion refuses. If this row passes without the check, the check is not what is being tested.
- [ ] Mutation: neutralise the comparison (make it return "no findings") and confirm the 0.60 em row goes red again. Record both numbers.

## Cost, and what closes CORE-001

- [ ] Measure the extra cost: the same page with and without the check, and the 840-span page CORE-005 (`#202`) measured at 1.35 s for 70 matches. State the number whether or not it is optimised here.
- [ ] Re-run CORE-001's mutation matrix (floor -> `intersects`, refusal neutralised, floor 0.15, whole fitter neutralised, first-containing-span restored) and confirm each row still fails where it should.
- [ ] `make check` green, coverage not lower than CORE-001's 84.9%, `ruff format --check` clean for BOTH the venv's ruff and the pinned hook (CI-004, `#203`).
- [ ] Once the full range holds, tick CORE-001's `features.json` f9 to the range the code actually covers and archive `specs/CORE-001/` — its own Major is closed by then, and its review rounds can be relaunched against a revision whose criterion is true.

## Close

- [ ] Independent adversarial review (`dotf spec review CORE-006-verify-by-consequence`); second cross-vendor signature required, because `proposal.md` declares `risk: high`.
- [ ] Archive to `specs/archive/CORE-006-verify-by-consequence/`.
