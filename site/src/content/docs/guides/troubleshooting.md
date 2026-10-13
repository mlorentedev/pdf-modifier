---
title: Troubleshooting
description: Common problems and solutions when using pdf-modifier.
---

## Text not being replaced

### Check span boundaries

PDF text that appears contiguous on screen may be split across multiple internal spans. The modifier uses a two-pass strategy to handle this:

1. **Pass 1** — matches within individual spans (fast path)
2. **Pass 2** — concatenates all spans in a line and matches across boundaries

This handles most cross-span cases automatically. If text still isn't matching:

**Diagnose:** Use `read_pdf_structure` or `pdf-mod analyze --json` to inspect span boundaries:

```bash
pdf-mod analyze document.pdf --json | python -m json.tool
```

Look for your target text in the `elements` array. Cross-span matching works within the same line but not across lines or blocks.

### Whitespace differences

PDF text often contains leading or trailing whitespace within spans. If `"Invoice"` doesn't match, try `" Invoice"` or inspect the exact span text via `read_pdf_structure`.

## Font style mismatch

The modifier maps embedded fonts to the nearest Base 14 family:

| Original font contains | Maps to |
|------------------------|---------|
| `Courier` | Courier |
| `Times`, `Serif` | Times-Roman |
| `Bold` (any family) | Bold variant |
| Everything else | Helvetica |

This means custom fonts (e.g., `Calibri`, `Segoe UI`) will be replaced with Helvetica. The size, color, and position are preserved exactly.

## Encrypted PDF errors

### `PASSWORD_ERROR: PDF is password protected`

The PDF has a user password. Pass it via `--password` (CLI) or the `password` parameter (MCP):

```bash
pdf-mod modify encrypted.pdf output.pdf -r "old=new" --password "secret"
```

### `PASSWORD_ERROR: Incorrect password provided`

The password is wrong. Note that PDFs can have two passwords:
- **User password** — required to open the document
- **Owner password** — controls permissions (print, copy, modify)

You need the user password to open the document.

## Replacement text overlaps

If the replacement text is significantly longer than the original, it may visually overlap with adjacent text. The modifier inserts at the original position without reflowing the page.

**Best practice:** Keep replacement text similar in length to the original. For longer replacements, consider a smaller font size (not currently configurable — the original size is always preserved).

## CLI output not showing

### Subprocess mode

If running the CLI via `python -m pdf_modifier.interfaces.cli`, Rich output (colors, tables) may not render in all terminals. Use the installed entry point `pdf-mod` instead.

### JSON mode for scripting

For programmatic use, prefer `--json` output:

```bash
pdf-mod analyze document.pdf --json
```

## MCP server not connecting

### Check uvx availability

```bash
uvx --version
```

If not installed, install [uv](https://docs.astral.sh/uv/getting-started/installation/).

### Test the server directly

```bash
uvx pdf-modifier
```

The server communicates over stdio. You should see no output (it's waiting for JSON-RPC input). Press `Ctrl+C` to exit.

### Verify client configuration

Each MCP client has its own configuration format. See the [Getting Started](/pdf-modifier/getting-started/#mcp-server) guide for client-specific setup instructions.
