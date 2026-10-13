---
id: "REFACTOR-001-project-rename"
type: spec
status: draft
created: "2026-10-12"
issue: "mlorentedev/pdf-modifier-mcp#143"
risk: high   # renames a public distribution, the MCP registry identity and the GitHub repo; the last also breaks credential consumers named after the old slug
tags: [spec, proposal, rename]
template_version: "1.0"
---

# REFACTOR-001-project-rename

> **Naming**: file lives at `<repo>/specs/REFACTOR-001-project-rename/proposal.md`. `REFACTOR-001-project-rename` is `AREA-NNN-slug`.

## Why

The project ships a Web UI, an MCP server and a CLI, but its identity says MCP only. The name is wrong on the three surfaces a stranger meets first — the PyPI distribution they install, the repo they land on, and the MCP registry entry — so the description contradicts the product before anyone reads a feature list. `pdf-modifier` is free on PyPI (verified 2026-10-12, HTTP 404), and the rename is cheapest now: the release path is broken since 1.6.0 and about to be exercised for the first time, so this is the last moment when "the publish failed" is a single-variable question.

## What

**Option A** (owner decision, 2026-10-12): the brand, repo, distribution, registry entry, CLI command and docs move to `pdf-modifier`; the import package stays `pdf_modifier`, so no Python `import` anywhere breaks.

1. **Distribution**: `backend/pyproject.toml` `[project].name` becomes `pdf-modifier`, and the console script becomes `pdf-modifier` (today `pdf-modifier-mcp`; `make run cli` invokes it by name).
2. **MCP registry identity**: `backend/server.json` `name` (`io.github.mlorentedev/pdf-modifier-mcp`), `title` and `repository.url` move to the new identity, so the published registry entry matches the repo it points at.
3. **Repo references in this repository**: `README.md`, `SECURITY.md`, `Makefile` (`APP_NAME`), `.env.example`, `smithery.yaml`, `harness/review-attestation.json`, the docs site (`site/`), and the string mentions in `backend/src/pdf_modifier/{__init__,interfaces/mcp,web/app}.py` and their tests.
4. **The GitHub repo slug and the credential consumers that name it**: `mlorentedev/pdf-modifier-mcp` → `mlorentedev/pdf-modifier`. Every consumer id in `dotfiles/secrets/registry.yaml` written as `ci:mlorentedev/pdf-modifier-mcp` (today: `NAN_API_KEY`, and `PR_AGENT_ANTHROPIC_API_KEY` once CI-001 PR2 adds it) must move with it, or `dotf secrets sync ci --repo …` stops matching and CI loses its credentials silently.
5. **Deprecation for the old distribution name**: decided below, because it is the one part a downstream consumer can feel.

## Out of scope

- **The import package is NOT renamed.** `pdf_modifier` stays. Renaming it would touch 44 files for no user-visible gain and break any third-party import. That is Option B, declined.
- **Historical and archived artifacts are NOT rewritten**: `docs/lessons/*` (19 files), `docs/lessons/_index.md`, `specs/archive/*`, `backend/specs/*`, `backend/CHANGELOG.md`, and the archived session handoffs. They record what was true when they were written, and rewriting them would falsify the record to make a grep clean. GitHub redirects the old repo URLs, so their links keep working. A guard must know these paths are the exclusions, not gaps.
- **No functional change.** No endpoint, CLI flag, MCP tool signature, or PDF behaviour changes. If a diff in this spec alters behaviour, it is a bug in this spec.
- **Docker image names are already correct** (`mlorentedev/pdf-modifier-api`, `-web`) and do not move; `.github/workflows/{docker-build,release}.yml` keep their `IMAGE_*` values.

## Risks / open questions

- **The GitHub repo rename breaks credential consumers named after the old slug.** `dotf secrets sync ci --repo <slug>` selects a registry entry by the consumer id; `ci:mlorentedev/pdf-modifier-mcp` stops matching the moment the repo is renamed. Until `dotfiles/secrets/registry.yaml` is updated **and** the secrets re-synced, this repo's CI has no `NAN_API_KEY` and PR-Agent fails. **MUST be resolved before the repo is renamed**, and the rename happens after the code lands, not before.
- **Sequencing against #168, and it is not cosmetic.** #168 is the first release since 1.6.0, on a publish path fixed in #171 and never yet exercised. If the rename lands in the same release window, a failed publish has two candidate causes. **Recommendation: land #168's release first and confirm `publish-pypi`/`publish-docker` actually ran and the version reached PyPI; then rename.** MUST be confirmed by the owner before the rename's release PR.
- **The old distribution name on PyPI.** `pip install pdf-modifier-mcp` stops resolving once `pdf-modifier` is published, and a `pdf-modifier-mcp` release already exists up to 1.6.0. Options: (a) publish a final `pdf-modifier-mcp` *shim* release whose only content is a dependency on `pdf-modifier` plus a deprecation notice; (b) document the break in the README and let the old name stand at 1.6.0. **Recommendation: (a)**, one small release, so an existing pinned install still functions.
- **`template_version: "1.0"` is unrelated to the project version** and is not renamed; it names the spec template.
- **The docs site's Pages URL** follows the repo slug, so links to the current URL redirect but the canonical URL changes. Verified after the rename, not before.

## Acceptance criteria

- [ ] **AC1 — The distribution is renamed and the import is not.** `backend/pyproject.toml` declares `name = "pdf-modifier"` and a `pdf-modifier` console script; `python -c "import pdf_modifier"` works; `uv run pdf-modifier --help` exits 0 from `backend/`.
- [ ] **AC2 — No live reference to the old name survives, and the exclusions are declared.** A commit-time guard finds `pdf-modifier-mcp` in no tracked file outside an explicit exclusion list (historical lessons, archives, CHANGELOG, this spec, and the deprecation shim), and fails when a new occurrence appears outside it.
- [ ] **AC3 — The MCP registry identity matches the repo it points at.** `backend/server.json` names the new identity, and the MCP server starts and lists its 5 tools.
- [ ] **AC4 — The docs site builds from the new identity.** `site/` builds and its configured URL/base names `pdf-modifier`.
- [ ] **AC5 — The credential consumers move with the slug.** In `dotfiles`, every `ci:mlorentedev/pdf-modifier-mcp` consumer id becomes `ci:mlorentedev/pdf-modifier`, and `dotf secrets sync ci --repo mlorentedev/pdf-modifier` selects them (verified by exit status, never by printing a value).
- [ ] **AC6 — CI is green end to end under the new name**: `make check`, `make check-frontend`, the docker-build job, and the hygiene guard.
- [ ] **AC7 — The published release carries the new name.** `publish-pypi` runs, `pdf-modifier` resolves on PyPI at the released version, and the old name's deprecation path (AC of the shim decision) is what was decided — not something discovered afterwards.

## References

- Bitácora board: `mlorentedev/pdf-modifier-mcp` #143 (`REFACTOR-001-project-rename`, Project #1)
- Blocking sibling: #168 (retired model; its release PR is the untested publish path), #171 (the publish fix)
- Blocking sibling in another repo: CI-001 PR2 (#174), which adds `PR_AGENT_ANTHROPIC_API_KEY` as a consumer named after the current slug
- `dotfiles/secrets/registry.yaml` (consumer ids), `dotfiles/docs/runbooks/guide-pr-agent-reviewer.md`
- Related patterns: `00_meta/patterns/pattern-knowledge-placement.md` (historical artifacts are records, not stale references)
