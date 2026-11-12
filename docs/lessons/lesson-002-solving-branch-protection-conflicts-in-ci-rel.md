---
id: "lesson-002-solving-branch-protection-conflicts-in-ci-rel"
type: lesson
status: active
title: "Solving Branch Protection Conflicts in CI Releases"
created: "2026-03-07"
owner: manu
tags: [pdf-modifier-mcp, lesson, ci-cd, release-please, github-actions, branch-protection]
---

# Solving Branch Protection Conflicts in CI Releases

**Context:** Handling CI/CD releases on branches with strict protection (Require Pull Request).
**Problem:** Tools like `python-semantic-release` attempt to push version commits directly to the default branch. This triggers GitHub's `GH006` error because the push isn't coming through a Pull Request, even when using an administrator token. Adding administrators to the "bypass" list doesn't work if "Require status checks" is also enabled, as the new version commit hasn't passed any checks yet.
**Solution:** Migrated to the **release-please** flow used in `hive-vault`. This tool creates a release PR with the version bump and changelog. Since it's a PR, it fulfills all branch protection requirements. Merging the PR triggers the tag creation and actual publication to PyPI/MCP Registry. This is the only robust way to maintain strict branch security while having automated releases.
**Tags:** `#ci-cd` `#release-please` `#github-actions` `#branch-protection`
