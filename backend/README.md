<!-- mcp-name: io.github.mlorentedev/pdf-modifier -->

# PDF Modifier

[![CI](https://github.com/mlorentedev/pdf-modifier/actions/workflows/ci.yml/badge.svg)](https://github.com/mlorentedev/pdf-modifier/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/pdf-modifier)](https://pypi.org/project/pdf-modifier/)
[![codecov](https://codecov.io/gh/mlorentedev/pdf-modifier/graph/badge.svg)](https://codecov.io/gh/mlorentedev/pdf-modifier)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Docs](https://img.shields.io/badge/docs-live-blue.svg)](https://mlorentedev.github.io/pdf-modifier/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Give your AI coding assistant the ability to natively read, edit, and redact PDF documents.**

Most AI assistants can generate Python scripts to edit PDFs, but running them requires manual execution, debugging missing fonts, and fixing broken layouts. PDF Modifier is an MCP server that gives your AI direct, native tools to safely manipulate PDFs in place.

**The numbers:**

| Metric | Without PDF Modifier | With PDF Modifier |
|---|---|---|
| Workflow | AI writes script -> You run it -> Debug errors | AI edits PDF directly via MCP |
| Time to redact 10 invoices | ~15 minutes (trial & error) | Seconds (autonomous) |
| Layout preservation | Often breaks styling or coordinates | 100% (Base 14 font matching) |
| Interface | Terminal only | Native AI Tools + CLI fallback |

## Quick Install (30 seconds)

One command. No cloning, no venv. **Use user scope (`-s user`) so the tools are available across all your projects.**

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

Then ask your assistant:

> "Read the structure of invoice.pdf and redact all credit card numbers"

That's it. You're running.

## What You Get

### 5 MCP Tools — PDF manipulation, on demand

| Tool | What it does |
|---|---|
| `read_pdf_structure` | Extract complete PDF structure with text positions, sizes, and fonts |
| `inspect_pdf_fonts` | Search for terms and report their exact font properties |
| `list_pdf_hyperlinks` | Inventory all existing hyperlinks and URIs in the document |
| `modify_pdf_content` | Find and replace text (or regex) with strict style and layout preservation |
| `batch_modify_pdf_content` | Apply the same replacements to multiple PDFs at once |

### CLI Interface (For Humans)

Still want to script it yourself? The package includes a powerful Typer CLI:

```bash
# Simple text replacement
pdf-mod modify input.pdf output.pdf -r "old text=new text"

# Inventory hyperlinks
pdf-mod links input.pdf

# Batch process multiple PDFs
pdf-mod batch *.pdf -o output/ -r "Draft=Final"
```
# Regex replacement (dates, IDs, etc.)
pdf-mod modify input.pdf output.pdf -r "Order #\d+=Order #REDACTED" --regex

# Create hyperlinks
pdf-mod modify input.pdf output.pdf -r "Click Here=Visit Site|https://example.com"
```

## Before / After

**Before PDF Modifier** — Manual scripting workflow:
```python
# The AI generates a script like this for you to run:
import fitz
doc = fitz.open("invoice.pdf")
for page in doc:
    # Hope the AI calculated the rects and fonts correctly...
    page.insert_text((100, 100), "REDACTED", fontname="helv")
doc.save("out.pdf")
```

**With PDF Modifier** — Autonomous AI action:
```python
# The AI natively calls the tool without asking you to run scripts
modify_pdf_content(
    input_path="invoice.pdf",
    replacements={"pattern": r"\b\d{4}-\d{4}-\d{4}-\d{4}\b", "replacement": "XXXX-XXXX-XXXX-XXXX"},
    use_regex=True
)
```

## Architecture

```text
MCP Host (Claude, Gemini, Copilot)
  ↓ MCP protocol (stdio)
pdf-modifier (FastMCP Server)
  │
  ├── Core Layer (PDFModifier, PDFAnalyzer)
  │     ├── Regex matching & text extraction
  │     ├── Base 14 font fallback mapping
  │     └── Layout & coordinate preservation
  │
  └── PyMuPDF (fitz) Engine
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, code standards, and PR workflow.

```bash
git clone https://github.com/mlorentedev/pdf-modifier.git
cd pdf-modifier
make setup     # create venv + install deps
make check     # lint + typecheck + test
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Documentation

Project-bound knowledge lives in [`docs/`](docs/) (docs-as-code): ADRs, runbooks, troubleshooting, and lessons.
