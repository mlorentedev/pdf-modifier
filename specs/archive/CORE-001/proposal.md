---
id: "CORE-001"
type: spec
status: archived # draft | implementing | verifying | archived
created: "2026-10-13"
issue: "mlorentedev/pdf-modifier#179"   # repo#NNN — GitHub issue / Project item that tracks this spec
risk: high   # the change lands inside core/modifier.py, which every other component trusts; the round-1 review's Blocker is why the declaration is machine-readable, not prose
review: required
review_round: 6   # ONLY the rounds with a committed verdict: 1-3 FAIL (nan/mimo-v2.6-flash, then nan/deepseek-v4-flash x2), 4 PASS (nan/glm5.3-flash), 5 PASS (nan/deepseek-v4-flash, f7b1324), 6 FAIL (nan/qwen3.8-flash, this head -- a REAL Major in this file's own frontmatter, below). A review is not recyclable, so each round is relaunched against the frozen head; round 7 is owed after the fix and is not claimed here.
tags: [spec, proposal]
template_version: "1.0"
---

# CORE-001 — A replacement must not drop the lines that follow it

**Traces to:** #179 · **ADR:** `docs/adr/adr-014-core-defect-exception.md`
**Risk:** high — this changes `core/modifier.py`, which every other component trusts.

## Why

`core/modifier.py` is the reason this repository exists: it edits text inside a PDF while preserving the document. Its contract is *preservation*. It has a defect that violates that contract directly — and it is silent.

```
pdf-mod modify in.pdf out.pdf -r '68D489883C5B7A25=9F3C1D7A4E620B85'
```

Page 2 goes from 37 lines to 35. `ARC: 00` and `CVM: 5E0000` — the two lines immediately following the replaced span — are absent from the output. The user sees a PDF that opens, renders, and looks right.

Why this is worth an ADR and a spec rather than a patch:

- **It destroys content.** Every other defect found in #179 fails to add something or fails to preserve metadata. This one deletes lines from the user's document.
- **It is invisible to the obvious test.** A check for "are the values I expect present?" passes while the file is missing two lines. The failure is discovered only by comparing the input's lines against the output's.
- **It is not about the replacement.** Three experiments on the same span — sixteen characters wider, sixteen narrower, four characters — all lose the same two lines. So the fix cannot be "make the new text fit"; the paragraph's re-layout has to preserve what follows it.
- **It came from ordinary use.** Not from a fuzzer or an edge case: a real receipt, a real substitution.

## What changes

The re-layout of a paragraph whose text was replaced preserves the lines that follow the replacement. No reliance on the replacement's length, width or content.

## What does not change

- The public API of `core/modifier.py`: same functions, same types, same signatures (ADR-014 condition 2).
- `core/analyzer.py` — not in scope (ADR-014, "Neutral").
- Any behaviour not reachable through a replacement that currently drops lines.

## Acceptance criteria

- [ ] The failing test exists first and fails before the fix, covering **all three** rows below — one row alone would have confirmed a wrong theory
- [ ] Every line present in the input is present in the output unless deliberately replaced (**set inclusion**, not expected-string presence)
- [ ] The fixture is **synthetic**, with a **tight** page — a loose page hides the defect entirely
- [ ] `message` for each of the three rows: the two lines following the span are present in the output
- [ ] The existing suite passes unchanged: this fixes a defect, it does not change intended behaviour

| Replacement | Chars | Observed |
|---|---|---|
| `9F3C1D7A4E620B85` | 16 (same) | −2 lines |
| `1111111111111111` | 16 (same) | −2 lines |
| `ABCD` | 4 (shorter) | −2 lines |

## Risks

| Risk | Mitigation |
|---|---|
| A change to the core alters behaviour that worked, in documents unlike the fixture | The three rows plus the untouched existing suite; ADR-014 condition 3 forbids the refactor that would make this likely |
| The fix lands as "make the new text fit", which the four-character row proves cannot work | The four-character row is an acceptance criterion, not an example |
| Fixing the symptom in the caller instead | The assertion is on `core/modifier.py`'s output, not on a caller's |
| A synthetic fixture that is too easy — no tight page | The fixture must reproduce the defect before the fix; if it does not fail, it is not the fixture |

## Out of scope

- The other five findings in #179 (each has its own disposition there).
- Cloning a repeated block — the capability, which needs its own spec.
- `core/analyzer.py`.

## Evidence of the defect

Reproduction and the falsified hypotheses: #179 (two comments). Working document: the owner's receipt, which stays outside git — the repository's fixture is synthetic.
