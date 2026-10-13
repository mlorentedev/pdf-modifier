# ADR-013: Project identity — rename to `pdf-modifier`

- **Status:** ACCEPTED
- **Date:** 2026-10-12
- **Deciders:** Manu
- **Supersedes:** the naming decision in ADR-001 that scoped the project as an MCP server

## Context

The project ships three surfaces — a Web UI, an MCP server and a CLI — from one sacred core, but its identity says MCP only. That name is what a stranger meets first: the PyPI distribution they install, the GitHub repository they land on, and the MCP registry entry they match against. The description contradicts the product before anyone reads a feature list, and the mismatch has been carried since ADR-001 when the MCP server was the only surface.

Two facts made this the moment to decide:

- `pdf-modifier` is free on PyPI (verified 2026-10-12, HTTP 404). `pdfmod` and `pdftext` are taken; generic names do not stay free.
- The release path has been broken since 1.6.0 — v1.7.0 through v1.9.0 never reached PyPI or DockerHub (the path-prefixed outputs bug fixed in #171, not yet exercised). This is the last window in which a failed publish has a single candidate cause.

## Decision

Rename the **identity**, not the **code**.

| Surface | From | To |
|---|---|---|
| PyPI distribution | `pdf-modifier-mcp` | `pdf-modifier` |
| Console script | `pdf-modifier-mcp` | `pdf-modifier` |
| MCP registry identity | `io.github.mlorentedev/pdf-modifier-mcp` | `io.github.mlorentedev/pdf-modifier` |
| GitHub repo | `mlorentedev/pdf-modifier-mcp` | `mlorentedev/pdf-modifier` |
| Docs site | slug-derived | slug-derived |
| **Import package** | `pdf_modifier` | **`pdf_modifier` (unchanged)** |

Also decided:

- **The import package is not renamed.** It is an internal detail, it already reads as the product rather than the protocol, and renaming it touches 44 files for no user-visible gain while breaking any third-party `import pdf_modifier`.
- **Historical artifacts are not rewritten.** Lessons, archived specs and the CHANGELOG record what was true when they were written; rewriting them to make a grep clean would falsify the record. GitHub redirects the old repo URLs, so their links keep working. The commit-time guard declares these as exclusions rather than treating them as gaps.
- **The old distribution name gets one final shim release** depending on `pdf-modifier`, so an install pinned to `pdf-modifier-mcp` keeps functioning and learns the new name from a deprecation notice.
- **Docker image names already match** (`mlorentedev/pdf-modifier-api`, `-web`) and do not move.

## Consequences

- **Renaming the repo breaks credential consumers named after the old slug.** `dotf secrets sync ci --repo <slug>` selects a registry entry by its consumer id, so `ci:mlorentedev/pdf-modifier-mcp` in `dotfiles/secrets/registry.yaml` stops matching the moment the repo is renamed — silently depriving this repo's CI of `NAN_API_KEY`. The registry must be updated **and the secrets re-synced before the repo is renamed**, and the rename is the last step, after the code is on `master`.
- **Release ordering matters, and it is not cosmetic.** #168's release PR is the first exercise of the publish path fixed in #171. If the rename lands in the same release window, a failed publish has two candidate causes. Land #168's release and confirm PyPI and DockerHub received it first.
- **The Pages URL changes** with the slug. Old links redirect; the canonical URL moves, which is a broadcast and not a break.
- **A guard becomes the mechanism.** "Renamed everywhere" is not a claim a human can check across a repository, so a test enforces it, with the exclusions listed explicitly and a planted occurrence proving the guard scans something.
- **This ADR is the SSOT for the name.** `AGENTS.md`, the README, the registry entry and the docs site point at it rather than restating the rationale.

## Alternatives considered

- **Keep the current name.** Rejected: the identity misdescribes the product on every surface a new user meets, and the cost only grows with adoption.
- **Option B — also rename the import package.** Rejected: 44 files of churn, zero user-visible benefit, and it breaks third-party imports of `pdf_modifier` for a rename that was never about the code.
- **A different name entirely** (`pdfmod`, `pdftext`, `pdf-smith`). Rejected as taken on PyPI or less descriptive; `pdf-modifier` is free, matches what the tool does, and keeps the existing Docker image names coherent.
