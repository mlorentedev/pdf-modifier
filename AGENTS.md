# AGENTS.md

> Single source of truth for AI coding agents working on this repository.
> Replaces CLAUDE.md as the per-repo agent configuration.

## Project Overview

**PDF Modifier** allows text modification in PDFs while preserving layout and fonts.

- **Stack**: Python 3.12+, PyMuPDF (fitz), Typer, FastMCP, Pydantic v2; SvelteKit 5 + pdf.js frontend.
- **Version**: owned by release-please — see `.release-please-manifest.json` (never hardcode it here).
- **License**: MIT
- **Vault** / **Source**: resolved per-machine via `~/.config/dotfiles/machine.json` (ADR-025); do not hardcode absolute paths — this repo is worked on from both Linux and Windows.

## Architecture

The repo is a monorepo: Python backend, SvelteKit frontend, compose stack, docs site.

```
backend/src/pdf_modifier/
├── core/                    # SACRED — reuse as-is (Standing Order #1)
│   ├── modifier.py          # Text replacement engine (two-pass)
│   ├── analyzer.py          # PDF parsing, structure, fonts, hyperlinks
│   ├── font_resolver.py     # Base14 / custom font resolution
│   ├── models.py            # Pydantic schemas (contracts)
│   └── exceptions.py        # Typed exception hierarchy
├── ai/                      # AI layer
│   ├── client.py            # NaN Cloud API client (httpx, OpenAI-compatible)
│   ├── router.py            # TaskType → model routing
│   ├── throttle.py          # Rate limiter (semaphore-based)
│   ├── prompts/             # Jinja2 prompt templates
│   ├── models.py            # AI-specific Pydantic models
│   └── exceptions.py
├── web/                     # FastAPI layer
│   ├── app.py               # App factory
│   ├── routes/              # pdf.py, ai.py, health.py
│   ├── session.py           # Session manager (in-memory + TTL)
│   ├── storage.py           # PDF storage (filesystem)
│   ├── config.py            # Pydantic Settings
│   └── deps.py              # Dependency injection
├── interfaces/
│   ├── cli.py               # Typer CLI
│   └── mcp.py               # FastMCP server (5 tools)
└── logger.py

frontend/src/                # SvelteKit 5 + pdf.js UI
├── lib/api/client.ts        # Backend client
├── lib/components/          # PdfPreview.svelte, Toast.svelte
├── lib/utils/               # grouping, highlight, scroll, zoom (+ colocated *.test.ts)
└── routes/                  # +layout.svelte, +page.svelte

specs/                       # Spec-Driven Development artifacts (+ archive/)
backend/tests/               # pytest suite
frontend/e2e/                # Playwright end-to-end suite
docs/                        # adr/ · lessons/ · runbooks/ · troubleshooting/
infra/                       # compose.{base,dev,prod}.yml · nginx.conf
scripts/                     # dump-pdf-spans.py · eval-grouping.ts · gen-env.py · safe-gh-pr
site/                        # Astro + Starlight docs site
```

> **Text-span grouping is a frontend post-process** (`frontend/src/lib/utils/grouping.ts`).
> It exists because `core/analyzer.py` is sacred — never push grouping into the analyzer.

## Decision Hierarchy

1. **Correctness** > Performance > Elegance
2. **User Understanding** > Blind Implementation
3. **Stdlib** > Battle-tested libs > New dependencies
4. **Boring tech** > Cutting edge
5. **Explicit** > Implicit

## Standing Orders

1. **Core is sacred.** `core/modifier.py` and `core/analyzer.py` are NOT modified. New features call them as-is.
2. **TDD is mandatory.** RED → GREEN → REFACTOR for every task.
3. **Conventional commits.** `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`.
4. **No manual version bumps.** release-please owns versioning: it opens a release PR from the conventional-commit history. Merging that PR cuts the tag and publishes.
5. **Specs before code.** Every feature >50 LOC needs `specs/<id>/` with proposal + tasks + verification; archive to `specs/archive/<id>/` once merged. (`dotf spec init` writes `specs/<id>/`; `backend/specs/` keeps only its historical README and the earlier `archive/`.)
6. **ADRs for decisions.** Non-reversible decisions go in `docs/adr/adr-XXX.md`.
7. **No secrets in code.** API keys via env vars only. `gitleaks` pre-commit hook enforced.
8. **Async-aware.** FastAPI is async; core is sync. Use `anyio.to_thread.run_sync` for core calls.

## Command Palette

Targets take a positional sub-argument (`make run api`), not a hyphen (`make run-api`).
Run `make help` for the authoritative list.

| Goal | Command | Description |
|------|---------|-------------|
| **Setup** | `make setup` | Install all deps & pre-commit hooks (`backend` / `frontend` to scope) |
| **Env** | `make env` | Generate `.env` from the example (idempotent; `FORCE=1` to regenerate) |
| **Run API** | `make run api` | Start FastAPI dev server |
| **Run MCP** | `make run mcp` | Start local MCP server |
| **Run CLI** | `make run cli ARGS='...'` | Run CLI locally |
| **Run frontend** | `make run frontend` | Start SvelteKit dev server |
| **Quality** | `make check` | Lint + type + test (backend) |
| **Quality (front)** | `make check-frontend` | svelte-check + vitest |
| **Lint** | `make lint` / `make format` | Check/fix style with Ruff |
| **Test** | `make test` | All tests (`backend` / `frontend` to scope) |
| **E2E** | `make test-e2e` | Playwright against the running Docker stack |
| **Mutation** | `make mutation` | Mutmut mutation testing |
| **Docker** | `make up` / `make down` | Start/stop the dev stack (`make up prod` for prod) |

## NaN Cloud Integration

- **Base URL**: `https://api.nan.builders/v1`
- **Auth**: `Authorization: Bearer $NAN_API_KEY`
- **Rate limits**: ~100 RPM / 5 concurrent (account-wide)
- **Always send**: `chat_template_kwargs: {"enable_thinking": false}`

### Model Routing

| Task | Model | Why |
|---|---|---|
| Vision / OCR | mimo-v2.5 | Only multimodal model |
| Tool calling | mimo-v2.5 | Native function calling |
| Reasoning | mimo-v2.5 | Reasoning mode, 1M context |
| Classification | qwen3.6 | Fast, cheap |
| Translation | qwen3.6 | Fast, 256K context |
| Summary | qwen3.6 | Fast |
| Embeddings | qwen3-embedding | Only embedding model |
| Rerank | rerank | Only reranking model |
| TTS | kokoro | Only TTS model |
| STT | whisper | Only STT model |

### Fallback Chain

```
mimo-v2.5 → qwen3.6 → gemma4
```

Fallback on: 429, 404, 5xx. Fail fast on: 400, 401.

## Testing Standards

- **Framework**: pytest + pytest-cov
- **Coverage**: ≥80% global, ≥90% critical paths
- **Mutation**: mutmut, score ≥70%
- **AI mocking**: NullAIClient for unit tests, never real API calls
- **File I/O**: `tmp_path` fixture, never write to real project dir
- **Naming**: `test_<unit>_<scenario>_<expected>`

## Security

- `gitleaks` pre-commit hook (mandatory)
- `bandit` for Python security linting
- `pip-audit` for dependency vulnerabilities
- Upload validation: PDF magic bytes, filename sanitization, max size
- CORS configured via env var
- Security headers on all responses
- **NEVER use double quotes or backticks in PR/commit bodies passed to `gh`.** Bash expands `$VAR` and `` `cmd` `` inside double-quoted strings, leaking environment secrets into GitHub. Always use single-quoted strings or write the body to a file with `<< 'HEREDOC_END'` (quoted delimiter prevents expansion). Use `scripts/safe-gh-pr` for all PR creation.

## Patterns Applied

| Pattern | Where |
|---|---|
| pattern-architecture | Monolith structure (core/ai/web/interfaces) |
| pattern-async-threading | anyio.to_thread for sync core |
| pattern-container-workflow | Multi-stage Docker, non-root, health checks |
| pattern-decision-persistence | ADRs in docs/adr/ |
| pattern-integration-testing | FastAPI TestClient + mocked AI |
| pattern-mcp-tool-design | MCP server preserved, <12 tools |
| pattern-nan-builders-gateway | Throttle, fallback, enable_thinking |
| pattern-python-cli | Typer CLI preserved |
| pattern-secrets-security | gitleaks, age, no secrets in code |
| pattern-spec-driven-development | specs/<id>/ per feature |
| pattern-testing-standards | TDD, mutation testing |
| pattern-workflow-protocol | Knowledge placement (ADRs → repo docs/) |
