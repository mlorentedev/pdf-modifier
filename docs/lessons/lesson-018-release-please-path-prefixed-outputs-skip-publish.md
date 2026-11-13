---
id: "lesson-018-release-please-path-prefixed-outputs-skip-publish"
type: lesson
status: active
title: "release-please outputs are path-prefixed outside the root, so the publish jobs skipped silently for four releases"
created: "2026-10-06"
owner: manu
tags: [pdf-modifier-mcp, lesson, ci, release-please, github-actions, pypi, docker]
---

# release-please outputs are path-prefixed outside the root, so the publish jobs skipped silently for four releases

**Context:** #103 (2026-06-24) moved the release-please package from the repo root to `backend/` after the monorepo restructure. `release.yml` gates `publish-pypi`, `publish-docker` and `publish-mcp` on `steps.release.outputs.release_created`.
**Problem:** release-please-action emits the unprefixed `release_created` / `tag_name` only for a package at path `.`; any other path gets `<path>--release_created` (`src/index.ts`, `path === '.'` branch). The gate read an output that no longer existed, evaluated to empty, and the three publish jobs went `skipped`, not `failed`. The GitHub Release and tag were still created, so every release looked done. v1.7.0, v1.7.1, v1.8.0 and v1.9.0 never reached PyPI (stuck at 1.6.0, 2026-06-23), DockerHub (only `latest` and `sha-*` tags) or the MCP registry. Found three months later, during a pre-migration audit that compared the registry versions against the git tags.
**Solution:** Read `outputs['backend--release_created']` and `outputs['backend--tag_name']`, and fail the step when `releases_created` is missing, or when a release exists that is not the `backend` one or lacks the backend outputs, so a renamed output or a moved package path turns the build red instead of skipping. The general rule: a job gated on an `if:` that can evaluate to empty fails open — a skipped publish is green. Verify a release by what it produced (registry versions), not by the workflow's colour.
**Tags:** `#ci` `#release-please` `#github-actions` `#pypi` `#docker`
