---
id: "lesson-012-github-actions-uv-installed-tools-need-uv-run"
type: lesson
status: active
title: "GitHub Actions: uv-installed tools need `uv run`, not bare names"
created: "2026-06-24"
owner: manu
tags: [pdf-modifier-mcp, lesson, ci, github-actions, uv, debugging]
---

# GitHub Actions: uv-installed tools need `uv run`, not bare names

**Context:** Security and mutation workflows invoking `pip-audit`, `bandit`, and `mutmut` after installing them with uv.
**Problem:** Every job failed with `command not found`, despite the install step reporting success.
**Solution:** Invoke them through the project environment — `uv run pip-audit`, `uv run bandit`, `uv run mutmut`. (Fixed alongside a wrong gitleaks action major version, v8 → v3.)
**Why:** uv installs into the project's `.venv` without activating it; each `run:` step is a fresh non-login shell that never sources it, so the venv's `bin/` is absent from `PATH`. `uv run` resolves the environment explicitly per invocation, which is why it works where the bare name does not. The alternative — activating the venv in every step — is more fragile because activation does not persist across steps.
**Tags:** `#ci` `#github-actions` `#uv` `#debugging`
