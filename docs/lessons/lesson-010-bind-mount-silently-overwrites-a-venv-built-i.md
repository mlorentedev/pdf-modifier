---
id: "lesson-010-bind-mount-silently-overwrites-a-venv-built-i"
type: lesson
status: active
title: "Bind mount silently overwrites a venv built into the image"
created: "2026-06-24"
owner: manu
tags: [pdf-modifier-mcp, lesson, docker, compose, venv, bind-mount, debugging]
---

# Bind mount silently overwrites a venv built into the image

**Context:** INFRA-001 — dev compose mounted the repo as `../:/app` over an image whose venv had been created at `/app/.venv` during build.
**Problem:** The container died with `uvicorn: not found` even though the build log clearly showed a successful install. Nothing in the build output hints at the failure, because the build genuinely succeeded — the breakage happens at run time.
**Solution:** Move the venv outside every mount point: create it at `/opt/venv` and point `PATH` at `/opt/venv/bin`. Update the Dockerfile and both compose files together.
**Why:** A bind mount replaces the image's directory contents at that path wholesale. Anything the build wrote under the mount point still exists in the image layer but is invisible at run time — the host directory shadows it. Any build artifact living under a path you also mount is subject to this; the venv is just the most common casualty.
**Tags:** `#docker` `#compose` `#venv` `#bind-mount` `#debugging`
