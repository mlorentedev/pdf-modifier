# ADR-014 — The sacred core opens to defects that destroy data

**Status:** Accepted · 2026-10-13
**Supersedes:** nothing. **Amends:** Standing Order #1 (*Core is sacred*), in one direction only.
**Traces to:** #179

## Context

Standing Order #1 says `core/modifier.py` and `core/analyzer.py` are *not modified*, and that new features call them as-is. The rule exists so that the engine that everything else trusts cannot drift under opportunistic refactors: a modifier that behaves differently after a cosmetic PR is a modifier nobody can reason about.

Using the tool on a real two-page receipt found a defect in the core that **destroys content**:

```
pdf-mod modify APAKO00227333.pdf out.pdf -r '68D489883C5B7A25=9F3C1D7A4E620B85'
```

Page 2 goes from 37 lines to 35. The two lines following the replaced span — `ARC: 00` and `CVM: 5E0000` — are gone from the output, deterministically. The replacement is the *same length* as the original.

Three follow-up experiments falsified the first two explanations, and each result narrows the bug:

| Replacement | Result |
|---|---|
| 16 chars, wider | −2 lines |
| 16 chars, narrower | −2 lines |
| 4 chars, shorter | −2 lines |

So the trigger is not the new text's length or width — it is **replacing that span at all**. Patching the replacement's geometry would not fix it: a four-character substitution breaks it.

The rule as written forbids the only place the fix can go. Left unamended, it protects the defect instead of the user, and a modifier that drops a line from a receipt drops one from a contract, an invoice or a certificate.

## Decision

The core stays closed to features and opens to **defects that destroy or silently alter existing content**, under three conditions, all mandatory:

1. **A failing test first, against a synthetic fixture.** The reproduction must be in the repository and must fail before the fix. The fixture is synthetic with the same shape — never a redacted copy of the owner's document.
2. **No public contract change.** The fix repairs behaviour inside the existing API: the same functions, the same types, the same signatures. A fix that needs a new parameter is a design change and needs its own ADR.
3. **Scoped to the defect.** No opportunistic refactor rides along. If the surrounding code wants restructuring, that is a separate, separately justified change.

Everything else stays as it was: new features do not modify the core, they call it.

## Consequences

**Positive.** The engine can be repaired where it damages documents, which is the only failure mode that justifies touching it. The three conditions keep the reason the rule existed: a core change always arrives with a failing test, a limited surface, and no API drift — so the next reader can tell a repair from a refactor.

**Negative.** The rule is now conditional, and a conditional rule is easier to bend. The guard against that is condition 3 plus review: "it was a data-destroying defect" must be *demonstrated* by the failing test, not asserted. A change to the core without a test that fails before it is a violation, whatever its justification.

**Neutral.** This ADR does not license touching `core/analyzer.py` for anything that is not the same class of defect. The amendment is about the failure mode, not about the files.

## Alternatives considered

**Leave the rule absolute and work around the core.** Rejected: the workaround is the caller not replacing such spans, which is a rule no caller can follow — the defect is invisible until the line count is checked against the input.

**Amend the rule by listing the defect.** Rejected: it would need a new ADR per bug, and it makes the core's openness a function of how recently something broke.

**Open the core to all bug fixes.** Rejected: it removes the guard for behaviour that is wrong but harmless, which is exactly the kind of change the rule was written to keep out.
