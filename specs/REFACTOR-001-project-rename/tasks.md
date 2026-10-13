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
- [ ] [P] [AC2] Live identity references: `README.md`, `SECURITY.md`, `Makefile` (`APP_NAME`), `.env.example`, `smithery.yaml`, `harness/review-attestation.json`, `backend/src/pdf_modifier/{__init__,interfaces/mcp,web/app}.py`, `backend/tests/unit/{interfaces/test_mcp,scripts/test_gen_env}.py`, `backend/Dockerfile`, `docs/runbooks/new-machine-setup.md`, `.github/ISSUE_TEMPLATE/config.yml`, `.github/templates/CHANGELOG.md.j2`.
      Run the guard. Expected: **PASS**.
- [ ] [AC1] **The runtime distribution lookups are not strings — they raise.** `backend/src/pdf_modifier/__init__.py` and `web/app.py` call `importlib.metadata.version("pdf-modifier-mcp")`; once the distribution is renamed that raises `PackageNotFoundError`, so `import pdf_modifier` fails and the version endpoint breaks. Replace both with the new name and add a test that **imports the package and reads `__version__`**, because the guard above passes on a string that is gone from a lookup that is now dead.
- [ ] [AC1] `backend/README.md` line 1 carries `<!-- mcp-name: io.github.mlorentedev/pdf-modifier-mcp -->`, the MCP registry ownership marker. It must equal `server.json`'s `name` exactly, so both move together or the registry entry stops matching the repo.
- [ ] [AC2] **Slug-agnostic rewrite where the string is historical.** `harness/review-attestation.json` records a measurement taken with `gh api repos/mlorentedev/pdf-modifier-mcp/…`; the measurement is real and the slug was accurate when it was made. Rewrite the path as `<owner>/<repo>` rather than replacing it with the new slug, which would claim the measurement was taken on a name that did not exist yet.
- [ ] [P] [AC4] Docs site: `site/astro.config.mjs`, `site/package.json` and the five `site/src/content/docs/**` files. Two non-obvious ones: `base: '/pdf-modifier-mcp'` is the **GitHub Pages project path**, which follows the repo slug, and the internal links `/pdf-modifier-mcp/getting-started/` must move with it or they 404 on the published site.
      Run: `cd site && npm install && npm run build`. Expected: **exit 0**.
- [ ] [AC6] Full suite: `make check`, `make check-frontend`, `bash scripts/check-lessons.sh`. Expected: all green, coverage ≥ 80%.

## The vault project folder is coupled to the repo name

- [ ] [AC5] Rename `$VAULT_PATH/10_projects/pdf-modifier-mcp/` to `pdf-modifier/`, together with the `memory/` symlink in this repo, because `dotf mem thread --project <repo>` resolves the project directory **by repo name**: rename the repo without this and every future session's handoff lookup misses its own memory. `docs/runbooks/new-machine-setup.md` names the vault path and must follow. Do this **in the same window as the repo rename**, not before (the vault is the memory sink and must not point at a name that does not exist yet) and not after (the lookup breaks in the gap).

## Cross-repo: `dotfiles` carries three registries, not one (own PR there)

- [ ] [AC5] `secrets/registry.yaml`: the `ci:mlorentedev/pdf-modifier-mcp` consumer id appears on **two** secrets — `BITACORA_PAT` (line 73) and `NAN_API_KEY` (line 165), plus `PR_AGENT_ANTHROPIC_API_KEY` if CI-001 PR2 has landed. All move to `ci:mlorentedev/pdf-modifier`.
- [ ] [AC5] `forge/branch-protection.json`: the repo is a **key** in `repos`, holding the required status checks (`test (3.12)`, `test (3.13)`). Rename the repo without moving this key and the forge registry stops managing protection for the repo that now exists, while still naming one that does not.
- [ ] [AC5] Four places launch the tool by **package name**, not by repo: `mcp-servers.json` (`uvx pdf-modifier-mcp`), `ai/copilot/mcp-config.json`, `ai/opencode/opencode.jsonc`, and `cli/internal/claude/mcp_test.go` (the fixtures for the first three). These follow the distribution, not the repo slug.
- [ ] [AC5] **Not changed**: `docs/lessons/*`, `specs/archive/*` and the comments in `scripts/bitacora-rollout.sh` name the repo as it was; they are records, and rewriting them would falsify them. Same rule as in-repo.
- [ ] [AC5] After that merges: `dotf secrets sync ci --repo mlorentedev/pdf-modifier`. Report by **exit status**; never print the value.
- [ ] [AC5] **The exposure is the sync path, not the credential already in place.** A repository's Actions secrets travel with it through a rename, so CI is not left credential-less by renaming first — what breaks is `dotf secrets sync ci`, which selects a consumer **by slug** and would match nothing until the registry moves. That matters on a rotation or on delivering a new secret, not on an ordinary run, and `pr-agent.yml`'s credential step fails loudly with the sync remedy rather than degrading.

## The rename is an owner action, and it is last

- [ ] [AC5] **Only after the code is on `master` and the consumers are updated**: `gh repo rename pdf-modifier --repo mlorentedev/pdf-modifier-mcp`, then update the local remote (`git remote set-url origin`).
- [ ] [AC1] Verify the redirect and the new surfaces: the old URL redirects, the Pages URL resolves at the new slug, and a fresh `git clone` of the new URL works. Record all three.
- [ ] [AC7] Deprecation for the old distribution name — per the Risk 3 decision: publish a final `pdf-modifier-mcp` shim release depending on `pdf-modifier`, or document the break in the README. **The reason is the notice, not a break**: `pip install pdf-modifier-mcp` keeps resolving to 1.6.0, and without a new release the old project page can never mention the rename. Measured 2026-10-12: ~1,206 downloads a week on the old name.

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
