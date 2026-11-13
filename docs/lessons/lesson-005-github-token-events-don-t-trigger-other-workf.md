---
id: "lesson-005-github-token-events-don-t-trigger-other-workf"
type: lesson
status: active
title: "GITHUB_TOKEN events don't trigger other workflows — release-please CI workaround"
created: "2026-03-14"
owner: manu
tags: [pdf-modifier-mcp, lesson, github-actions, release-please, ci, branch-protection, pattern]
---

# GITHUB_TOKEN events don't trigger other workflows — release-please CI workaround

**Context:** Using release-please with branch protection that requires CI status checks (e.g. test matrix jobs)
**Problem:** release-please pushes to its branch using GITHUB_TOKEN. By GitHub design, events from GITHUB_TOKEN don't trigger other workflows. This means the CI workflow never runs on the release-please branch, leaving required status checks perpetually pending and blocking the merge.
**Solution:** Run the test matrix inside the Release workflow itself, conditioned on release_created != true. Checkout the release-please branch, run tests, then use the GitHub Statuses API (gh api repos/OWNER/REPO/statuses/SHA) to report the check results on the correct commit SHA. The status context names must match branch protection's required checks exactly (e.g. "test (3.12)"). Add statuses: write to workflow permissions.
**Tags:** `#github-actions` `#release-please` `#ci` `#branch-protection` `#pattern`
