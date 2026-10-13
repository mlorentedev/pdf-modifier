---
title: Getting Started
description: Install pdf-modifier, use the CLI, and configure the MCP server for AI agents.
---

## Installation

Install from PyPI:

```bash
pip install pdf-modifier
```

Or run directly without installing (requires [uv](https://docs.astral.sh/uv/)):

```bash
uvx pdf-modifier
```

Requires **Python 3.12** or later.

To install from source:

```bash
git clone https://github.com/mlorentedev/pdf-modifier.git
cd pdf-modifier
make setup
```

## CLI Usage

The `pdf-mod` command exposes six operations.

### Replace text

```bash
pdf-mod modify input.pdf output.pdf -r "old text=new text"
```

Stack multiple replacements in a single pass:

```bash
pdf-mod modify input.pdf output.pdf -r "$99.99=$149.99" -r "Draft=Final"
```

Font style (family, weight, size, color) is preserved automatically. The tool maps embedded fonts to the nearest Base 14 family — Helvetica, Times-Roman, or Courier — with bold variant detection.

### Regex replacement

Enable pattern matching with `--regex`:

```bash
pdf-mod modify input.pdf output.pdf -r "Order #\d+=Order #REDACTED" --regex
pdf-mod modify input.pdf output.pdf -r "January \d{2}, \d{4}=DATE REDACTED" --regex
```

Patterns are validated at input. Invalid regex returns an error before touching the PDF.

### Create and neutralize hyperlinks

Append a URL after `|` to make the replacement text clickable:

```bash
pdf-mod modify input.pdf output.pdf -r "Click Here=Visit Site|https://example.com"
```

Neutralize an existing link with `void(0)`:

```bash
pdf-mod modify input.pdf output.pdf -r "Click Here=Click Here|void(0)"
```

Supported schemes: `http://`, `https://`, `mailto:`, `javascript:`.

### Analyze PDF structure

Plain text extraction with page separators:

```bash
pdf-mod analyze input.pdf
```

Full structure as JSON — every text span with position, font, size, and color:

```bash
pdf-mod analyze input.pdf --json
```

### Inspect fonts

Search for terms and display their font properties in a Rich table:

```bash
pdf-mod inspect input.pdf "Invoice" "Total" "$"
```

Output columns: Page, Term, Font, Size, Context (first 100 characters of the containing span).

### List hyperlinks

Inventory all existing links in the document:

```bash
pdf-mod links input.pdf
```

Output includes page number, target URI, and the text area covered by the link.

### Batch processing

Apply the same replacements to multiple files at once:

```bash
pdf-mod batch file1.pdf file2.pdf -o output/ -r "Draft=Final"
```

Each file is processed independently — failures in one file don't stop the batch. Output files are saved to `--output-dir` with the same filename.

```bash
pdf-mod batch *.pdf -o redacted/ -r "\d{4}-\d{4}-\d{4}-\d{4}=XXXX-XXXX-XXXX-XXXX" --regex
```

## MCP Server

The MCP server exposes the same functionality over stdio for AI agent integration. **Use user scope (`-s user`) so the tools are available across all your projects.**

### Claude Code

```bash
claude mcp add -s user pdf-modifier -- uvx --upgrade pdf-modifier
```

### Gemini CLI

```bash
gemini mcp add -s user pdf-modifier uvx -- --upgrade pdf-modifier
```

### OpenAI Codex CLI

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.pdf-modifier]
command = "uvx"
args = ["--upgrade", "pdf-modifier"]
```

### GitHub Copilot (VS Code)

Add to `.vscode/mcp.json` or your User Settings:

```json
{
  "mcp": {
    "servers": {
      "pdf-modifier": {
        "command": "uvx",
        "args": ["--upgrade", "pdf-modifier"]
      }
    }
  }
}
```

### Other Clients

Any MCP-compatible client (like Cursor or Windsurf) that supports stdio transport will work. Point the client to `uvx --upgrade pdf-modifier`.

### Available tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `read_pdf_structure` | `input_path`, `password?` | Returns complete PDF structure — text, bounding boxes, font names, sizes, colors — as JSON. Use this first to understand the document layout before making changes. |
| `inspect_pdf_fonts` | `input_path`, `terms[]`, `password?` | Searches for text terms (substring match) and returns font name, size, and position for each match. Run this before replacements to verify font handling. |
| `list_pdf_hyperlinks` | `input_path`, `password?` | Extracts all existing hyperlinks and URIs from the document, including their location and covered text. |
| `modify_pdf_content` | `input_path`, `output_path`, `replacements{}`, `use_regex?`, `password?` | Find and replace text with style preservation. Supports regex patterns and hyperlink syntax (`text\|URL`). Returns replacements made, pages modified, and any warnings. |
| `batch_modify_pdf_content` | `input_paths[]`, `output_dir`, `replacements{}`, `use_regex?`, `password?` | Apply the same replacements to multiple PDFs at once. Per-file error isolation. |

All tools return structured JSON. Errors include a typed error code (`FILE_NOT_FOUND`, `READ_ERROR`, `WRITE_ERROR`), a human-readable message, and a details object.

### Typical agent workflow

1. Call `read_pdf_structure` to get the full document layout.
2. Call `inspect_pdf_fonts` with the target terms to confirm font properties.
3. Call `modify_pdf_content` with the replacement map.

## Web UI

The project includes a browser-based interface (FastAPI + SvelteKit) for interactive editing.

### With Docker (recommended)

```bash
make up
# API: http://localhost:8000 | Web UI: http://localhost:8080
```

Upload a PDF by drag & drop (or click to select), browse the detected structure in the
sidebar, preview pages with zoom and page jump, and click an element to highlight it on
the canvas before applying replacements.

### Without Docker

```bash
# Terminal 1 — backend API
make run api

# Terminal 2 — frontend dev server (http://localhost:5173)
make run frontend
```

The Vite dev server proxies `/api` to the backend on port 8000.

## How it works

1. The PDF is opened with PyMuPDF and each page is scanned for text spans matching the target.
2. All matches on a page are collected, then redacted in batch (`apply_redactions()` called once per page).
3. Replacement text is inserted at the original coordinates with matched font properties.
4. Embedded font names are mapped to Base 14 equivalents: `"Arial-BoldMT"` becomes Helvetica-Bold (`HeBo`), `"TimesNewRomanPSMT"` becomes Times-Roman (`TiRo`), etc.

Text matching uses a two-pass strategy: first within individual spans, then across span boundaries within the same line. This handles most cases where PDF producers split text across multiple spans.

## Architecture

```
Entry Points               Core Layer                  Engine
+-----------------------+   +-----------------------+   +----------------+
| CLI (Typer + Rich)    |-->| PDFModifier           |-->| PyMuPDF (fitz) |
| MCP Server (FastMCP)  |   | PDFAnalyzer           |   +----------------+
+-----------------------+   | Pydantic v2 models    |
                            +-----------------------+
```

- **PDFModifier** — context manager that opens, modifies, and saves the PDF. Two-pass matching (single-span + cross-span) with batch-redact strategy.
- **PDFAnalyzer** — reads structure via `page.get_text("dict")`, traverses the block/line/span hierarchy.
- **batch_process()** — processes multiple PDFs independently with per-file error isolation.
- **Pydantic models** — `ReplacementSpec` validates input (regex compilation, max 100 replacements). `ModificationResult`, `BatchResult`, `PDFStructure`, and `FontInspectionResult` are the typed outputs.
