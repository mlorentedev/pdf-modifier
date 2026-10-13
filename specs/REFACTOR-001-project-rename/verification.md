---
tags: [spec, verification]
created: "2026-10-12"
---

# Verification - REFACTOR-001-project-rename

> AC5 (the cross-repo consumers, the repo rename and the vault folder) describes a **window**, not this PR: the repo rename is the owner's action and goes last, after the code is on `master` and after the consumers are updated. AC7 likewise waits for the release. Everything below is what this PR can prove.

## Evidence

- [x] **AC1 — distribution renamed, import unchanged.** `uv run python -c 'import pdf_modifier'` → `1.9.0`; `uv run pdf-modifier --help` → exit 0, `Server: pdf-modifier`; `grep -qx 'name = "pdf-modifier"' backend/pyproject.toml` and the console-script key `pdf-modifier =` both pass.
  - The half the guard cannot see is tested explicitly: `__init__.py` and `web/app.py` resolve the version with `importlib.metadata.version()`, which raises `PackageNotFoundError` if the distribution is renamed and the lookup is not. `test_the_distribution_lookup_resolves_under_the_new_name` imports the package and compares `__version__` to `version("pdf-modifier")`. The guard fails on a string that is present; this defect was a string that was gone from a lookup that was dead.
- [x] **AC2 — no live reference survives.** `uv run pytest tests/unit/rename` → **6 passed**. Written first and watched to fail with all 29 live references listed; the guard declares its exclusions with a reason each, and refuses to let a `LIVE_SURFACES` path be excluded.
  - Of the 29, two were **regenerated, not edited**: `backend/uv.lock` (`uv sync` → `pdf-modifier==1.9.0`) and `site/package-lock.json` (`npm install`). Neither is excluded, so a stale lock fails the guard rather than hiding.
  - One was rewritten **slug-agnostically**: the historical measurement in `harness/review-attestation.json` now reads `<owner>/<repo>`. Replacing it with the new slug would have claimed the measurement was taken on a name that did not exist yet.
- [x] **AC3 — MCP registry identity.** `backend/server.json` → `io.github.mlorentedev/pdf-modifier`, package identifier `pdf-modifier`, `repository.url` on the new slug. The ownership marker in `backend/README.md` (`<!-- mcp-name: … -->`) must equal `server.json`'s `name` exactly, so both moved together. `uv run pytest tests/unit/interfaces/test_mcp.py` → **26 passed**.
- [x] **AC4 — docs site.** `npm run build` in `site/` → **6 pages**, exit 0. `base: '/pdf-modifier'` is the GitHub Pages project path, which follows the slug; the internal links that path carries moved with it.
- [ ] **AC5 — the window.** Pending, and deliberately: the `dotfiles` consumer ids (`ci:mlorentedev/pdf-modifier-mcp` → `-pdf-modifier`) must merge and the secrets re-sync **before** `gh repo rename`, which is the owner's action and lasts. The vault folder `10_projects/pdf-modifier-mcp/` moves in that same window, because `dotf mem thread --project <repo>` resolves it by repo name.
- [ ] **AC6 — CI.** Pending this PR's own checks; local evidence below.
- [ ] **AC7 — the release.** Pending, and sequenced after #168 by decision: #168's release PR is the first exercise of the publish path fixed in #171, and landing the rename in the same window would leave a failed publish with two candidate causes. The deprecation shim for the old PyPI name goes with it, so the old project page can carry the notice — without a new release it can never mention the rename.

## Test status

- Guard: `uv run pytest tests/unit/rename -q --no-cov` → **6 passed**.
- Backend: `make check` → **365 passed**, 19 skipped, coverage **84.20%** (gate 80%). Was 359; +6 are the rename guard and the identity-resolution test.
- Frontend: `make check-frontend` → **50 passed** (6 files), svelte-check 0 errors. Unchanged by this PR.
- Docs site: `npm run build` → 6 pages.
- Lessons guard: `bash scripts/check-lessons.sh` → `check-lessons: OK (19 lessons)`.
- Ruff/mypy: clean on the new test module.
- No regressions: **yes**.

## Decisions made during implementation

- **The guard excludes itself**, the only self-exclusion, with its reason in the list: a guard that cannot name what it searches for cannot search for it. `LIVE_SURFACES` still asserts that no product surface is inside the exclusions, so the list cannot be widened to silence the check.
- **The guard fails on `.mypy_cache`-free, tracked-only content.** An unfiltered grep reported thousands of hits; `git ls-files` reported 29. Untracked scratch files cannot fail the build and tracked ones cannot hide, and binary files are skipped by their NUL byte rather than by an extension list that would be a second thing to keep true.
- **Historical artifacts stay as they were written** — lessons, archived specs, `backend/specs/`, the CHANGELOG. Rewriting a record to make a grep clean is a worse defect than a stale string in a document nobody installs, and GitHub redirects the old URLs.
- **The vault folder rename is not done here.** It is coupled to the repo rename, and it must happen in the same window: before it, the memory sink would point at a name that does not exist; after it, `dotf mem thread` misses its own project. Permission recorded; execution waits for the window.

## Promotion candidates

- [x] Lesson for the repo's `docs/lessons/`? yes: `docs/lessons/lesson-020-a-rename-guard-must-fail-on-a-string-that-is-present.md`
- [x] ADR-worthy decision for the repo's `docs/adr/adr-XXX.md`? yes: `docs/adr/adr-013-project-rename.md`
- [x] New pattern candidate for `00_meta/patterns/`? no: "a rename is a guard, not a sed" is a special case of the existing measure-before-declaring lesson; it is not new cross-project knowledge.

## Archive checklist

- [ ] `proposal.md` frontmatter set to `status: archived`
- [ ] Folder moved: `specs/REFACTOR-001-project-rename/` -> `specs/archive/REFACTOR-001-project-rename/`
- [ ] Bitácora board ticket for this spec moved to Done / closed with PR link (ADR-018)
- [ ] Promotions above executed (if any)
