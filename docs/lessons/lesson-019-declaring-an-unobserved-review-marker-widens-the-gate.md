---
id: lesson-019-declaring-an-unobserved-review-marker-widens-the-gate
type: lesson
status: active
created: "2026-10-12"
owner: manu
tags: [pdf-modifier-mcp, lesson, ci, pr-agent, review, attestation, gates]
---

# A reviewer marker declared without a measurement widens the gate; omitting it only fails closed

**Context:** `harness/review-attestation.json` is this repo's port of a dotfiles SSOT and states its own rule in prose: `review_markers ARE MEASURED HERE, NOT COPIED`. CI-001 (#174) ports the file to parity, and the SSOT declares two PR-Agent headings: `## PR Reviewer Guide` and `## Incremental PR Reviewer Guide`.
**Problem:** Parity says copy both. Measuring first said otherwise: over the comments of #165..#173, `## PR Reviewer Guide` appears on 3 PRs (#171, #170, #167) and on none of the four Dependabot PRs, while `## Incremental PR Reviewer Guide` appears on **none** of the 7. The two errors are not symmetric, and that asymmetry is the whole decision. Declaring a marker makes the attestation gate accept one more shape — it **widens**, and a heading anyone can paste turns "no review happened" into "attested". Omitting an unobserved marker only **fails closed**: if the heading ever does appear, that PR reads unattested and a merge stalls. Separately, the entry's `why` still asserted the marker "has NEVER been observed in pdf-modifier-mcp, because this workflow has not run here" — a claim that had quietly become false the first time the workflow ran.
**Solution:** Measure before declaring, and decide with the counting direction in mind: on a gate, an unobserved allowance is not free, and the cheap error is refusing to accept something that never happens. The incremental heading was left undeclared with the measurement recorded in the entry's `why`, and a task was filed for the PR that may make the workflow emit it (PR2). The rule was made executable rather than trusted: `backend/tests/unit/harness/test_reviewer_pool_contract.py` fails when any reviewer entry declares markers without recording where they were observed. Same failure class as lesson-013 — a gate is only as real as its last negative test.
**Tags:** `#ci` `#pr-agent` `#review` `#attestation` `#gates`
