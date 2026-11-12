---
id: "lesson-004-release-please-prs-need-manual-ci-trigger"
type: lesson
status: active
title: "Release-Please PRs Need Manual CI Trigger"
created: "2026-03-13"
owner: manu
tags: [pdf-modifier-mcp, lesson, ci-cd, release-please, github-actions]
---

# Release-Please PRs Need Manual CI Trigger

**Context:** Release-please created PR #52 but CI never ran on the release-please branch
**Problem:** Release-please uses GITHUB_TOKEN which by design does not trigger workflow runs (to prevent infinite loops). The release PR sits with pending checks forever because CI never runs on it.
**Solution:** Push an empty commit (`git commit --allow-empty -m "chore: trigger CI"`) to the release-please branch to trigger CI. Alternative: add `workflow_dispatch` trigger to ci.yml so `gh workflow run` works without a push.
**Tags:** `#ci-cd` `#release-please` `#github-actions`
