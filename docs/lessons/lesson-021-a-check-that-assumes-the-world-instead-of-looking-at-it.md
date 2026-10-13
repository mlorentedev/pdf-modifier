---
id: lesson-021-a-check-that-assumes-the-world-instead-of-looking-at-it
type: lesson
status: active
created: "2026-10-13"
owner: manu
tags: [pdf-modifier, lesson, verification, guards, ci]
---

# Six times in one session, a check assumed something about the world instead of looking at it

**Context:** A day of work that produced four defects found by *using* the product rather than reading it, plus two found in CI. Each was caught late because the check that was supposed to catch it was looking at a proxy: an exit code, a flag, a position, a single match.
**Problem:** The same shape six times, in six different tools — and none of them is a bug in the tool.
1. A `sed` used `\s`, which the platform's implementation does not support. The pattern matched nothing, the file was unchanged, **exit 0**. The missing edit was found later, by reading the artifact.
2. A version fix was verified with `grep -m1 '"version"'`. The file had **two** version fields. The search printed the first, the fix had changed the first, and the two agreed with each other while the second was wrong. **Resolution and verification shared one blind spot, so they confirmed each other.**
3. A generated PDF was checked against a **stale** file — the output had been written under a new name. Every expected string reported absent, which was correct for a file that was no longer the target. A test suite that can point at the previous artifact is not a test suite.
4. `dotf secrets sync ci` selected **zero** secrets and exited **0**, so a rename delivered no credentials and reported success.
5. A library's `get_fonts()` reported a font as embedded while the same experiment's `extract_font()` returned zero bytes. Both could not be true; the PDF object settled it — `/BaseFont /Courier-Bold`, no `/FontFile`, a base-14 font, nothing embedded.
6. A new test resolved the repository root as `parents[3]`, encoding where the file itself sits. CI runs the suite from a deeper copy; the test died with `FileNotFoundError` instead of checking anything — **the same mistake as the defect it had been written to catch.**

**Solution:** Treat every check as a claim about the world and ask what it actually observes. An exit status, a boolean flag, a single match, a relative path, and a green tick are all **proxies**, and a proxy can agree with a mistake. What decides is the artifact: the file's contents, the field that was meant to change, the line count, the object in the document. Concretely: compare what files **say** rather than whether an edit appears to have landed; assert **sets** and counts, not the first match; verify in the shape that **failed** (the deeper copy, the tight page, the renamed file) and not only where it already works; and when two signals disagree, the object decides — never the convenient one. The corollary that makes it bearable: a check that only asserts what should be present **cannot see a deletion**, so anything reachable by a modification needs a comparison against the input, not a list of expectations.
**Tags:** `#verification` `#guards` `#ci` `#testing`
