# Contributing to PDF Modifier

Thank you for your interest in contributing! We follow standard GitHub Flow and use specific conventions to ensure quality and automated releases.

## Development Setup

### Quick Start

```bash
# Full setup (dependencies + pre-commit hooks)
make setup

# Run all checks (lint, type, test)
make check

# Start MCP server
make run-mcp
```

### Makefile Commands

| Command | Description |
|---------|-------------|
| `make setup` | Install dependencies and pre-commit hooks |
| `make test` | Run tests with coverage |
| `make lint` | Run ruff linter |
| `make format` | Format code with ruff |
| `make type` | Run mypy type checker |
| `make check` | Run all checks (lint, type, test) |
| `make run-mcp` | Start MCP server (stdio) |
| `make run-cli` | Run CLI (use `ARGS="..."` for arguments) |
| `make build` | Build distribution artifacts |
| `make clean` | Remove build artifacts |

### Manual Commands (uv)

```bash
# Install with dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing

# Linting and type checking
uv run ruff check src/
uv run mypy src/
```

## Git Workflow

We use **GitHub Flow**:

1.  **Fork** the repository.
2.  **Clone** your fork locally.
3.  **Create a feature branch** from `master`:
    ```bash
    git checkout -b feat/my-awesome-feature
    ```
4.  **Make changes** and ensure tests pass (`make check`).
5.  **Commit** your changes using Conventional Commits (see below).
6.  **Push** to your fork and submit a **Pull Request** to `master`.

## Commit Convention

We use [Conventional Commits](https://conventionalcommits.org/) to automate versioning and changelogs.
Pre-commit hooks will validate your commit messages automatically.

| Prefix | Meaning | Version Bump |
|--------|---------|--------------|
| `feat:` | New feature | Minor (0.x.0) |
| `fix:` | Bug fix | Patch (0.0.x) |
| `docs:` | Documentation only | None |
| `style:` | Formatting, missing semi-colons, etc. | None |
| `refactor:` | Code change that neither fixes a bug nor adds a feature | None |
| `perf:` | Code change that improves performance | Patch (0.0.x) |
| `test:` | Adding missing tests or correcting existing tests | None |
| `chore:` | Changes to the build process or auxiliary tools | None |
| `BREAKING CHANGE:` | (Footer) Introduces a breaking API change | Major (x.0.0) |

**Examples:**
```text
feat: allow replacement of images
fix: correct layout alignment issue
docs: update contributing guide
```

## Pull Request Process

1.  Ensure `make check` passes locally.
2.  Update `README.md` if you changed functionality.
3.  The CI pipeline will run automatically on your PR.
4.  Once merged to `master`, a new release will be published automatically if applicable.
