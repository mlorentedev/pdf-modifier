# PDF Modifier

**CLI + MCP server + Web UI** for PDF text replacement with font style preservation.

[![CI](https://github.com/mlorentedev/pdf-modifier/actions/workflows/ci.yml/badge.svg)](https://github.com/mlorentedev/pdf-modifier/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/pdf-modifier)](https://pypi.org/project/pdf-modifier/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Docs](https://img.shields.io/badge/docs-live-blue.svg)](https://mlorentedev.github.io/pdf-modifier/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Quick start

```bash
pip install pdf-modifier

# CLI
pdf-mod modify input.pdf output.pdf -r "Draft=Final"

# MCP server (for Claude/Cursor/Codex)
claude mcp add -s user pdf-modifier -- uvx pdf-modifier
```

## Interfaces

| Interface | Description | Run |
|-----------|-------------|-----|
| **CLI** | `pdf-mod` — batch jobs, scripting, CI pipelines | `make run cli ARGS="..."` |
| **MCP Server** | `pdf-modifier` — AI agents edit PDFs | `make run mcp` |
| **Web UI** | FastAPI + SvelteKit — drag & drop, preview, replace | `make up` (Docker) or `make run api` + `make run frontend` |

## Features

- **Text replacement** — find and replace with font style preservation (family, weight, size, color)
- **Regex support** — pattern-based bulk replacements (`--regex`)
- **Hyperlinks** — create clickable links or neutralize existing ones
- **Batch processing** — apply same replacements to multiple files
- **Web UI** — drag & drop PDF upload, structure browser, page preview with zoom, text highlighting
- **MCP tools** — `read_pdf_structure`, `inspect_pdf_fonts`, `list_pdf_hyperlinks`, `modify_pdf_content`

## Development

```bash
# Setup
make setup

# Run tests
make test

# Full check (lint + type + test)
make check

# Start dev stack (Docker)
make up
# API: http://localhost:8000 | Web: http://localhost:8080

# Start servers locally
make run api          # FastAPI dev server
make run frontend     # SvelteKit dev server
```

## Documentation

- [Full documentation site](https://mlorentedev.github.io/pdf-modifier/)
- [Architecture Decision Records](docs/adr/)
- [Troubleshooting](docs/troubleshooting/)
- [Lessons learned](docs/lessons.md)

## License

MIT
