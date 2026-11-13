---
id: "lesson-013-gitleaks-custom-config-replaces-default-ruleset"
type: lesson
status: active
title: "A gitleaks config without `[extend]` runs with zero rules"
created: "2026-08-08"
owner: manu
tags: [pdf-modifier-mcp, lesson, security, gitleaks, pre-commit, ci]
---

# A gitleaks config without `[extend]` runs with zero rules

**Context:** `.gitleaks.toml` existed only to allowlist `scripts/safe-gh-pr`, which legitimately contains detection patterns. Both the pre-commit hook and the `gitleaks-action@v3` CI job auto-discover this file from the repo root. Surfaced while checking why every pre-commit hook ran three times per commit ([PR #126](https://github.com/mlorentedev/pdf-modifier-mcp/pull/126), whose description records the before/after scan output).
**Problem:** A planted GitHub PAT committed cleanly and passed CI. The same file scanned with the default ruleset reported `RuleID: github-pat, leaks found: 1`; scanned with this repo's config it reported `no leaks found`. Every green gitleaks result before the fix was vacuous.
**Solution:** Add `[extend] useDefault = true` to `.gitleaks.toml` and keep the `[allowlist]` block below it. Re-verify with a planted PAT: the hook now fails with `RuleID: github-pat` and the commit is blocked, while the `scripts/safe-gh-pr` allowlist still applies. In the same PR, `default_stages: [pre-commit]` was pinned in `.pre-commit-config.yaml` so stage-agnostic hooks stop firing once per git hook type under a machine-wide `core.hooksPath` dispatcher (3 runs per commit became 1).
**Why:** A custom gitleaks config *replaces* the built-in ruleset rather than adding to it, so a file carrying only an allowlist leaves the scanner with nothing to match. A passing secret scanner is only evidence when it has been shown to fail on a canary; "no leaks found" on its own says nothing about coverage. Verify enforcement gates by consequence (plant, scan, expect a block), never by the absence of findings.
**Tags:** `#security` `#gitleaks` `#pre-commit` `#ci`
