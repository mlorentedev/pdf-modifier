---
id: "lesson-015-pr-agent-empty-reviewable-diff-misdiagnosed-as-concurrency"
type: lesson
status: active
title: "A lockfile-only PR makes the review guard fail permanently — misdiagnosed as NaN concurrency"
created: "2026-09-22"
owner: manu
tags: [pdf-modifier-mcp, lesson, ci, pr-agent, review, lockfiles, dependabot]
---

# A lockfile-only PR makes the review guard fail permanently — misdiagnosed as NaN concurrency

**Context:** Dependabot bumps #157 (`site/package-lock.json`) and #158 (`backend/uv.lock`) failed the `review` check in `.github/workflows/pr-agent.yml` on every attempt (3 retries across 2 PRs, all failing in 36-40 s). The guard's error message names "NaN concurrency exhaustion" as the most likely cause.
**Problem:** The real cause is deterministic and has nothing to do with concurrency. Each PR's *only* changed file is on PR-Agent's `[ignore]` list (generated lockfiles are deliberately excluded from review). PR-Agent filters them out → `Empty diff for PR` → `No PR diff fits the /review request` for both models → PR-Agent swallows the failure and exits green → the guard correctly fails ("no review published") but attributes it to the wrong cause. Retrying can never succeed: every future lockfile-only bump fails `review` forever.
**Diagnosis method:** The guard's stderr is a hypothesis, not evidence. Reading the actual PR-Agent step log (JSON lines, grep for `filtered_files` / `Empty diff`) showed `filtered_files: []` with the whole PR reduced to nothing — measured in runs 35677911532 and 35678085166. PRs with real files (e.g. #159) reviewed fine in the same window, which alone disproved the concurrency theory.
**Solution (tracked in #161):** The guard should compute the reviewable diff (changed files minus the same ignore list) and, when empty, exit 0 with a `::notice::nothing reviewable` instead of red. Interim: lockfile-only bumps merge under the machine-generated AND machine-verified exception — `review` is not a required check, and an ignored lockfile is by construction outside what the review gate protects.
**Tags:** `#ci` `#pr-agent` `#review` `#lockfiles` `#dependabot` `#debugging`
