---
id: lesson-026-a-check-outside-the-repository-cannot-fail-anything
type: lesson
status: active
created: "2026-10-13"
owner: manu
tags: [lesson, verification, testing, harness, process]
---

# A check that lives outside the repository cannot fail anything

**Context:** A defect was found by using the product, and the work to understand it — a reproduction, a trace of the values the fix computes, a measurement that killed the first candidate fix, a benchmark — was done with scripts written quickly in a temp directory. Every one of them answered its question, and the answers were quoted in the spec as the evidence for the change.
**Problem:** Those scripts could not fail anything. There is no build that runs them, no reviewer who re-runs them, and no successor to them: they are gone at the next reboot, and the claims they produced survive only as prose in a document. "Verified end to end" was true when it was written and unverifiable an hour later — and the shape they had exercised was not in the suite, so the next review found a failing shape in exactly that gap. The general form: **a harness whose home is a scratch directory has no way to be wrong later.** The same rule catches a check that lives only in a pipeline nobody runs on a schedule (the first build of the artifact then belongs to a third party, which is the one place the failure cannot be read locally), and a one-off command typed by hand, whose result is a sentence in a conversation rather than an exit status a machine produces.
**Solution:** Anything that decides whether a change is correct belongs in the repository, next to the code, where a machine runs it: as a test, or as a script the build invokes. Only the **case data** stays outside — the private document, the real receipt, the customer's export — and even then only by giving the in-repo fixture the same shape, so the case's *structure* is versioned while its contents are not. The question to ask while writing a scratch script is what would fail if it stopped being true; if the answer is "nothing", it is evidence for this minute, not a check. And when a claim does rest on a scratch run, say where it came from and what would reproduce it, rather than quoting a path nobody can open.
**Tags:** `#verification` `#testing` `#harness` `#process`
