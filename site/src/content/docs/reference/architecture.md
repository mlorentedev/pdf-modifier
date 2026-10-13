---
title: Architecture
description: Technical architecture of pdf-modifier — layers, data flow, and design decisions.
---

## Overview

```
Entry Points               Core Layer         Engine              Web Layer
+-----------------------+   +---------------+   +-------------+   +-------------------+
| CLI (Typer + Rich)    |-->|               |   |             |   | FastAPI (backend)  |
| MCP Server (FastMCP)  |-->| PDFModifier   |-->| PyMuPDF     |   | SvelteKit (front)  |
| Web UI (browser)      |-->| PDFAnalyzer   |   | (fitz)      |   | nginx (proxy)      |
+-----------------------+   | Pydantic v2   |   +-------------+   +-------------------+
                            +---------------+
```

The project follows a clean architecture with three layers:

- **Interface layer** — thin wrappers that handle I/O format (CLI output, JSON-RPC responses, HTTP API)
- **Core layer** — pure business logic with typed inputs and outputs
- **Web layer** — FastAPI REST API + SvelteKit frontend served behind nginx

All interfaces share the same core. Adding a new interface requires only a new file with no core changes.

## Core layer

### PDFModifier

The main modification engine. Uses a two-pass matching strategy with batch redaction:

1. **Pass 1** — match within individual spans (fast path for most cases)
2. **Pass 2** — concatenate spans per line and match across boundaries, mapping results back to individual spans
3. **Redact** — add redaction annotations for all matches, then call `apply_redactions()` once per page
4. **Insert** — place replacement text at original coordinates with matched font properties

Batch redaction is more efficient because `apply_redactions()` is expensive and benefits from batching.

A module-level `batch_process()` function applies the same replacements across multiple files with per-file error isolation.

**Font mapping:** Embedded PDF font names are mapped to Base 14 equivalents using substring matching:

| Font name contains | Code | Base 14 name |
|-------------------|------|--------------|
| `courier` + `bold` | `CoBo` | Courier-Bold |
| `courier` | `Cour` | Courier |
| `times` or `serif` + `bold` | `TiBo` | Times-Bold |
| `times` or `serif` | `TiRo` | Times-Roman |
| (any) + `bold` | `HeBo` | Helvetica-Bold |
| (default) | `helv` | Helvetica |

**Hyperlink support:** Replacement values can include a URL suffix (`text|URL`). The modifier calculates text width using `fitz.Font.text_length()` and creates a link annotation covering the text area.

### PDFAnalyzer

Read-only analysis of PDF structure. Provides:

- `get_structure()` — full page/element hierarchy as Pydantic models
- `extract_text()` — plain text with page separators
- `inspect_fonts()` — search for terms and report font properties
- `get_hyperlinks()` — inventory all URI links in the document

All methods use `_open_doc()` for consistent password handling.

### Pydantic models

Input and output contracts are defined as Pydantic v2 models:

- **`ReplacementSpec`** — validates input, compiles regex patterns via `model_validator`
- **`ModificationResult`** — success status, counts, warnings
- **`BatchResult`** — aggregate results for multi-file processing
- **`PDFStructure` / `PageStructure` / `TextElement`** — document structure hierarchy
- **`FontInspectionResult` / `FontMatch`** — font inspection output
- **`HyperlinkInventory` / `Hyperlink`** — link extraction output

### Exception hierarchy

All exceptions inherit from `PDFModifierError`, which includes:
- Typed `code` field (e.g., `"FILE_NOT_FOUND"`)
- `to_dict()` method for JSON serialization
- `details` dict for structured error context

```
PDFModifierError
├── PDFNotFoundError       (FILE_NOT_FOUND)
├── FileSizeExceededError  (FILE_TOO_LARGE)
├── PDFReadError           (READ_ERROR)
├── PDFWriteError          (WRITE_ERROR)
├── PDFPasswordError       (PASSWORD_ERROR)
└── InvalidPatternError    (INVALID_PATTERN)
```

## Interface layer

### MCP server

Uses FastMCP with stdio transport. Each tool is a thin wrapper:

1. Construct core objects from parameters
2. Call core method
3. Serialize result to JSON string

The `@handle_mcp_errors` decorator catches all exceptions and returns structured JSON error responses, so tool calls never raise — they always return parseable JSON.

### CLI

Uses Typer with Rich console output. Commands map 1:1 to core methods:

| Command | Core method |
|---------|-------------|
| `modify` | `PDFModifier.process()` |
| `batch` | `batch_process()` |
| `analyze` | `PDFAnalyzer.get_structure()` / `extract_text()` |
| `inspect` | `PDFAnalyzer.inspect_fonts()` |
| `links` | `PDFAnalyzer.get_hyperlinks()` |

## Logging

Structured JSON logging to `~/.pdf-modifier/logs/pdf-modifier.log` with 5MB rotation (3 backups). Uses UTC timestamps. Logging is file-only — no stdout pollution for MCP server compatibility.

## Design decisions

**Why Base 14 fonts only?** PDF viewers are required to have Base 14 fonts available. Using them guarantees the replacement text will render correctly on any viewer without embedding custom fonts.

**Why batch redactions?** PyMuPDF's `apply_redactions()` rebuilds the page content stream. Calling it once per page (with all redactions queued) is significantly faster than calling it per-match.

**Why no async?** PDF operations are CPU-bound (parsing, rendering). Async would add complexity without performance benefit. The MCP server uses synchronous tool handlers, which FastMCP runs in threads for concurrency.

**Why file size validation?** Large PDFs can cause OOM during processing. Both `PDFModifier` and `PDFAnalyzer` validate file size before opening (default 100 MB, configurable via `max_file_size` parameter). The limit is generous enough for typical use while protecting against accidental processing of multi-GB files.
