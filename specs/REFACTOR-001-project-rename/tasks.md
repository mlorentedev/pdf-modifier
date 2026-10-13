---
tags: [spec, tasks]
created: "2026-10-12"
---

# Tasks - REFACTOR-001-project-rename

> TDD order. One task = one focused commit. The guard comes first: it is the only thing that can tell "renamed" from "renamed almost everywhere".

## Setup

- [x] Branch created from `master`: `refactor/REFACTOR-001-project-rename`
- [ ] `proposal.md` complete, acceptance criteria testable
- [ ] **Owner confirms the sequencing** (Risk 2: #168's release first) — MUST be resolved before the release PR, not before the code

## The guard (write it first, watch it fail)

- [ ] [P] [AC2] Write `backend/tests/unit/rename/test_no_stale_project_name.py`: list tracked files with `git ls-files`, and fail on any occurrence of `pdf-modifier-mcp` outside a declared exclusion list (`docs/lessons/`, `specs/archive/`, `backend/specs/`, `backend/CHANGELOG.md`, `specs/REFACTOR-001-project-rename/`).
      Run: `cd backend && uv run pytest tests/unit/rename -q --no-cov`
      Expected: **FAIL**, listing every live reference still present.
- [ ] [AC2] Add the negative test: the guard must trip on a **planted** occurrence, read from an in-memory file list rather than the repo, so a guard that scans nothing cannot pass. Expected: **PASS** for the planted case, **FAIL** for the real tree.

## The rename

- [ ] [AC1] `backend/pyproject.toml`: `[project].name` → `pdf-modifier`; the `[project.scripts]` key → `pdf-modifier`; every remaining `pdf-modifier-mcp` in the file (URLs, description).
      Run: `cd backend && uv run uv sync --all-extras && uv run pdf-modifier --help`. Expected: **exit 0**, usage printed.
- [ ] [P] [AC3] `backend/server.json`: `name` → `io.github.mlorentedev/pdf-modifier`, `title` → `PDF Modifier` (unchanged), `repository.url` → the new slug.
- [ ] [P] [AC2] Live identity references: `README.md`, `SECURITY.md`, `Makefile` (`APP_NAME`), `.env.example`, `smithery.yaml`, `harness/review-attestation.json`, `backend/src/pdf_modifier/{__init__,interfaces/mcp,web/app}.py`, `backend/tests/unit/{interfaces/test_mcp,scripts/test_gen_env}.py`, `backend/Dockerfile`, `docs/runbooks/new-machine-setup.md`.
      Run the guard. Expected: **PASS**.
- [ ] [P] [AC4] Docs site: `site/astro.config.mjs`, `site/package.json` and the five `site/src/content/docs/**` files.
      Run: `cd site && npm install && npm run build`. Expected: **exit 0**.
- [ ] [AC6] Full suite: `make check`, `make check-frontend`, `bash scripts/check-lessons.sh`. Expected: all green, coverage ≥ 80%.

## Cross-repo: the credential consumers (own PR in `dotfiles`)

- [ ] [AC5] In `dotfiles`, replace every `ci:mlorentedev/pdf-modifier-mcp` consumer id with `ci:mlorentedev/pdf-modifier` in `secrets/registry.yaml` (`NAN_API_KEY` today, and `PR_AGENT_ANTHROPIC_API_KEY` if CI-001 PR2 has landed). External worktree, per Standing Order #9.
- [ ] [AC5] After that merges: `dotf secrets sync ci --repo mlorentedev/pdf-modifier`. Report by **exit status**; never print the value.

## The rename is an owner action, and it is last

- [ ] [AC5] **Only after the code is on `master` and the consumers are updated**: `gh repo rename pdf-modifier --repo mlorentedev/pdf-modifier-mcp`, then update the local remote (`git remote set-url origin`).
- [ ] [AC1] Verify the redirect and the new surfaces: the old URL redirects, the Pages URL resolves at the new slug, and a fresh `git clone` of the new URL works. Record all three.
- [ ] [AC7] Deprecation for the old distribution name — per the Risk 3 decision: publish a final `pdf-modifier-mcp` shim release depending on `pdf-modifier`, or document the break in the README.

## Verification window — before archive

- [ ] [AC7] Confirm the release: `publish-pypi` ran, `pdf-modifier` resolves on PyPI at the released version, and the `pdf-modifier-api`/`-web` images carry the tag. This is also the first real exercise of #171's publish fix — if it fails, record which of the two changes it implicates.
- [ ] Propose `/adversarial-review REFACTOR-001-project-rename`. `risk: high` requires a **second signature** from another vendor; the first signer must not be Anthropic.
- [ ] Re-run the guard and `make check` on the final commit.

## Closing

- [ ] Every acceptance criterion covered by at least one test or a recorded manual check
- [ ] Every criterion has a matching `features.json` entry with a non-vacuous verification command
- [ ] `verification.md` filled in, including the two owner actions and their observed results
- [ ] PR opened referencing #143 and this spec folder
- [ ] No behaviour change: the diff is names, comments and URLs only
