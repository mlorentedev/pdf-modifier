---
id: lesson-025-a-reviewers-claim-is-verified-against-the-artifact-not-obeyed
type: lesson
status: active
created: "2026-10-13"
owner: manu
tags: [lesson, review, verification, triage, process]
---

# A reviewer's claim is verified against the artifact before it is obeyed — and before it is dismissed

**Context:** A working session that filed, fixed and merged a handful of changes, with several independent reviewers in the loop: a pooled adversarial reviewer on a spec, a CI code-review bot, and the issue author's own diagnosis — which is a reviewer of the change too, one whose claim arrives as a prescribed fix.
**Problem:** The claims were right more often than not, and wrong often enough that treating either way as a policy fails. The prescribed one-line fix for a release-job race (`needs: [release-please, publish-pypi]`) was **already on `master`**, four months before the issue — applying it would have produced a green diff that closed the class while the next release failed identically, which is worse than leaving it open: the record would say fixed. On the same day a reviewer's finding that the retry loop slept after its **last** attempt was real, cheap and applied; a reviewer's claim that a CI job's stated mitigation was overstated was real and led to a filed ticket rather than a reworded comment; and one reviewer's finding about a genuinely failing shape was reproduced twice before anything was touched. The failure mode of obeying an unverified claim and the failure mode of dismissing one are the same failure: **the artifact was never asked.**
**Solution:** Every reviewer claim is a hypothesis with a cheap test, and the test is not agreement — it is the artifact: `git blame` for a claim about history, the run timeline for a claim about ordering, a reproduction for a claim about behaviour, the exit status of the check for a claim about a check. Answer three questions before disposition: **is it there**, **does it do that**, **does the fix change the outcome**. Then record the disposition where the change lives (a `## Review triage` comment naming who reviewed and what happened to each finding, applied / ticketed / declined with a reason), so the next reader can tell "verified and applied" from "restated and forgotten". Two corollaries earn their keep: a claim can be right about the defect and wrong about the fix (the retry was real, the ordering was not the cause), and a *notice that no review ran* — a quota, a rate limit, a limit reached — is not a review: it leaves the change unreviewed, and saying so is the honest record.
**Tags:** `#review` `#verification` `#triage` `#process`
