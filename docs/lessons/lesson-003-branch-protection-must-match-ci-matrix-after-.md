---
id: "lesson-003-branch-protection-must-match-ci-matrix-after-"
type: lesson
status: active
title: "Branch Protection Must Match CI Matrix After Python Version Bump"
created: "2026-03-13"
owner: manu
tags: [pdf-modifier-mcp, lesson, ci-cd, github-actions, branch-protection, python]
---

# Branch Protection Must Match CI Matrix After Python Version Bump

**Context:** Bumped Python target from 3.10 to 3.12 and updated CI matrix from [3.10, 3.12] to [3.12, 3.13]
**Problem:** PR checks showed perpetually pending — GitHub branch protection still required `test (3.10)` which no longer exists in the CI matrix. The check name includes the Python version from the matrix, so changing the matrix silently breaks branch protection.
**Solution:** Update branch protection required status checks via `gh api repos/.../branches/master/protection/required_status_checks -X PATCH` to match the new matrix names. Always update branch protection as part of any CI matrix change.
**Tags:** `#ci-cd` `#github-actions` `#branch-protection` `#python`
