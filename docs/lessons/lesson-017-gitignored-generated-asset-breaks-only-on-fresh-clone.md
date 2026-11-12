---
id: "lesson-017-gitignored-generated-asset-breaks-only-on-fresh-clone"
type: lesson
status: active
title: "A gitignored generated asset with no generator breaks only on a fresh clone"
created: "2026-10-06"
owner: manu
tags: [pdf-modifier-mcp, lesson, onboarding, frontend, pdfjs, reproducibility]
---

# A gitignored generated asset with no generator breaks only on a fresh clone

**Context:** Pre-migration audit before moving the project to a new workstation. `PdfPreview.svelte` loads the pdf.js worker from `/pdf.worker.min.mjs`, which `frontend/.gitignore` excludes. The Docker image copies it from `node_modules` at build; the dev path (`make setup` + `make run frontend`) had no step that produced it.
**Problem:** The file had been copied by hand once, so the long-lived workstation always had it and every local run looked healthy. A clean clone passed `make setup`, `make check` and `make check-frontend`, yet `frontend/static/` held only `robots.txt`: the dev preview would fail to load its worker. The hand-copied file could also drift from the installed `pdfjs-dist` version after an upgrade. No test covers it, because the unit suites never load the worker.
**Solution:** A `make pdf-worker` target copies the worker from `node_modules`, run by `make setup` and on every `make run frontend`, so it always matches the installed version. The general rule: a gitignored file the app needs at runtime must have a generator on every path that runs the app, and the only proof is a fresh clone — the established workstation is the one place the gap cannot show. The new-machine runbook (`docs/runbooks/new-machine-setup.md`) records that check.
**Tags:** `#onboarding` `#frontend` `#pdfjs` `#reproducibility`
