# Runbook: set up the project on a new machine

Brings a fresh clone to the same working state as an existing workstation.
Verified end to end on a clean clone of `master` (backend 348 passed, frontend 50 passed).

## Prerequisites

| Tool | Version | Why |
|---|---|---|
| Python | ≥ 3.12 (`backend/pyproject.toml`) | backend runtime |
| uv | any recent | backend deps (`backend/uv.lock`) |
| Node.js | 22 (Docker image) — newer works locally | frontend, docs site |
| Docker + Compose | any recent | `make up` stack, `make test-e2e` |
| gh | authenticated | PR / issue workflow |
| pre-commit | any recent | hooks, including `gitleaks` |

Git hooks are not installed per repo: they are dispatched machine-wide through
`core.hooksPath` by the dotfiles setup. Check with `git config core.hooksPath`.
Without it, nothing runs `gitleaks` before a commit.

## Steps

```bash
git clone https://github.com/mlorentedev/pdf-modifier.git
cd pdf-modifier
make setup          # backend (uv sync) + frontend (npm install) + pdf.js worker copy
make env            # writes infra/.env from .env.example with a fresh SECRET_KEY
```

`make env` leaves `NAN_API_KEY` as a placeholder. It is the only real secret the
project needs, and it lives in the secrets registry under the id `NAN_API_KEY`.
Write it into `infra/.env` without echoing it to the terminal. Only the AI
routes need it; PDF editing, the CLI and the MCP server work without it.

## Verify

```bash
make check            # ruff + mypy + pytest, coverage ≥ 80%
make check-frontend   # svelte-check + vitest
make run api          # http://localhost:8000/health
make run frontend     # http://localhost:5173 — open a PDF, the preview must render
```

The preview is the check that catches a missing `frontend/static/pdf.worker.min.mjs`.
That file is gitignored and copied from `node_modules` by `make setup` and
`make run frontend`; if the preview stays blank, run `make pdf-worker`.

## Knowledge that does not travel with the clone

- **Agent memory and session journals**: the maintainer's knowledge store
  (`10_projects/pdf-modifier/` — `context.md`, `memory/`, `sessions/`). The
  agent memory directory is a symlink into it; recreate the link on the new machine.
- **Backlog**: GitHub issues and the bitácora GitHub Project.
- Everything build/operate lives here: `docs/adr/`, `docs/lessons/`,
  `docs/troubleshooting/`, `docs/runbooks/`, `backend/specs/`.
