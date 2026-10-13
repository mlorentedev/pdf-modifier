"""
MCP (Model Context Protocol) server for PDF Modifier.

Provides LLM-friendly tools for PDF analysis and modification.
Uses FastMCP with stdio transport for Claude Desktop integration.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from functools import wraps
from typing import Any

from fastmcp import FastMCP

from ..core.analyzer import PDFAnalyzer
from ..core.exceptions import PDFModifierError
from ..core.models import ReplacementSpec
from ..core.modifier import DEFAULT_MAX_FILE_SIZE_BYTES, PDFModifier, batch_process
from ..logger import setup_logging

logger = setup_logging(__name__)

mcp = FastMCP(
    "pdf-modifier",
)


def handle_mcp_errors(func: Callable[..., str]) -> Callable[..., str]:
    """Decorator to handle exceptions in MCP tools and return JSON error responses."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> str:
        try:
            return func(*args, **kwargs)
        except PDFModifierError as e:
            return json.dumps(e.to_dict(), indent=2)
        except Exception as e:
            logger.exception("Unexpected error in MCP tool %s", func.__name__)
            return json.dumps(
                {
                    "success": False,
                    "error": "UNEXPECTED_ERROR",
                    "message": str(e),
                },
                indent=2,
            )

    return wrapper


@mcp.tool()
@handle_mcp_errors
def read_pdf_structure(
    input_path: str,
    password: str | None = None,
    max_file_size: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> str:
    """
    Extract the complete structural content of a PDF document.

    Returns detailed information about each page including:
    - Page dimensions (width, height)
    - All text elements with their:
      - Exact text content
      - Bounding box coordinates (x0, y0, x1, y1)
      - Origin point for text insertion
      - Font name and size
      - Color value

    Use this tool FIRST to understand the document layout before
    making any modifications. The output helps identify exact text
    to target for replacements.

    Args:
        input_path: Absolute path to the PDF file to analyze.
                   Must be a valid, accessible PDF file.
        password: Optional password if the PDF is encrypted.
        max_file_size: Maximum allowed input file size in bytes (default: 100 MB).

    Returns:
        JSON string containing the complete page structure.
        On error, returns JSON with success=false and error details.

    Example:
        read_pdf_structure("/home/user/documents/invoice.pdf")
    """
    analyzer = PDFAnalyzer(input_path, password=password, max_file_size=max_file_size)
    result = analyzer.get_structure()
    return result.model_dump_json(indent=2)


@mcp.tool()
@handle_mcp_errors
def inspect_pdf_fonts(
    input_path: str,
    terms: list[str],
    password: str | None = None,
    max_file_size: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> str:
    """
    Search for specific text terms and report their font properties.

    Use this tool to understand the exact font styling of text you
    want to replace. This ensures replacements will match the
    surrounding document style as closely as possible.

    The tool searches through all pages and returns matches with:
    - Page number where the term was found
    - The search term that matched
    - Surrounding context (first 100 characters)
    - Font name (e.g., "Helvetica-Bold", "Times-Roman")
    - Font size in points
    - Origin coordinates for precise positioning

    Args:
        input_path: Absolute path to the PDF file to inspect.
        terms: List of text strings to search for (1-50 terms).
               Each term is searched as a substring.
        password: Optional password if the PDF is encrypted.
        max_file_size: Maximum allowed input file size in bytes (default: 100 MB).

    Returns:
        JSON string with all matches and their font properties.
        Returns empty matches array if no terms are found.

    Example:
        inspect_pdf_fonts("/path/to/doc.pdf", ["Invoice", "$99.99", "Total"])
    """
    analyzer = PDFAnalyzer(input_path, password=password, max_file_size=max_file_size)
    result = analyzer.inspect_fonts(terms)
    return result.model_dump_json(indent=2)


@mcp.tool()
@handle_mcp_errors
def modify_pdf_content(
    input_path: str,
    output_path: str,
    replacements: dict[str, str],
    use_regex: bool = False,
    whole_span: bool = False,
    password: str | None = None,
    pages: str | None = None,
    max_file_size: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> str:
    """
    Find and replace text in a PDF while preserving font styles.

    This tool performs text replacement by:
    1. Locating all occurrences of the search text
    2. Redacting the original text (white fill)
    3. Inserting the replacement text with matched styling

    IMPORTANT BEHAVIORS:
    - Text is matched within individual text spans
    - Font style is approximated using Base 14 fonts (Helvetica, Times, Courier)
    - Replacement text should be similar length to avoid overlap
    - Multiple replacements can be specified in a single call

    HYPERLINK SUPPORT:
    - Append "|URL" to create a clickable link: "Click Here|https://example.com"
    - Use "|void(0)" to neutralize existing links: "Product|void(0)"

    REGEX SUPPORT:
    - Set use_regex=true to treat keys as regex patterns
    - Useful for matching dates, IDs, or variable content
    - Example: {"Order #\\d+": "Order #REDACTED"}

    PAGE RANGE:
    - Use pages="1-3" to process only pages 1 through 3 (1-indexed, inclusive)
    - Use pages="5" to process only page 5
    - Omit to process all pages

    Args:
        input_path: Absolute path to the source PDF file.
        output_path: Absolute path where the modified PDF will be saved.
                    Parent directory must exist.
        replacements: Dictionary mapping old text to new text.
                     Keys are search strings (or regex if use_regex=true).
                     Values are replacement strings (optionally with |URL).
        use_regex: If true, treat replacement keys as regex patterns.
                  Default is false for literal string matching.
        password: Optional password if the source PDF is encrypted.
        pages: Optional page range, e.g. "1-3" or "5". Defaults to all pages.
        max_file_size: Maximum allowed input file size in bytes (default: 100 MB).

    Returns:
        JSON string with modification results including:
        - success: boolean indicating if operation completed
        - replacements_made: count of text spans modified
        - pages_modified: count of pages with changes
        - warnings: any non-fatal issues encountered

    Examples:
        # Simple text replacement
        modify_pdf_content(
            "/path/input.pdf",
            "/path/output.pdf",
            {"$99.99": "$149.99", "Draft": "Final"}
        )

        # Regex replacement for dates
        modify_pdf_content(
            "/path/input.pdf",
            "/path/output.pdf",
            {"\\d{2}/\\d{2}/\\d{4}": "01/01/2025"},
            use_regex=True
        )

        # Create hyperlink
        modify_pdf_content(
            "/path/input.pdf",
            "/path/output.pdf",
            {"Learn More": "Visit Website|https://example.com"}
        )

        # Only modify pages 1-2
        modify_pdf_content(
            "/path/input.pdf",
            "/path/output.pdf",
            {"Draft": "Final"},
            pages="1-2"
        )
    """
    spec = ReplacementSpec(replacements=replacements, use_regex=use_regex, whole_span=whole_span)

    page_range: tuple[int, int] | None = None
    if pages:
        parts = pages.split("-")
        if len(parts) == 1:
            page_range = (int(parts[0]), int(parts[0]))
        elif len(parts) == 2:
            page_range = (int(parts[0]), int(parts[1]))

    modifier = PDFModifier(
        input_path,
        output_path,
        password=password,
        max_file_size=max_file_size,
    )
    result = modifier.process(spec, pages=page_range)
    return result.model_dump_json(indent=2)


@mcp.tool()
@handle_mcp_errors
def list_pdf_hyperlinks(
    input_path: str,
    password: str | None = None,
    max_file_size: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> str:
    """
    Extract all existing hyperlinks and clickable URIs from a PDF.

    Use this tool to inventory the links in a document before or after
    making modifications. It reports the target URI, its location (bbox),
    and the text covered by the link if detectable.

    Args:
        input_path: Absolute path to the PDF file to scan.
        password: Optional password if the PDF is encrypted.
        max_file_size: Maximum allowed input file size in bytes (default: 100 MB).

    Returns:
        JSON string with the inventory of found hyperlinks.

    Example:
        list_pdf_hyperlinks("/path/to/report.pdf")
    """
    analyzer = PDFAnalyzer(input_path, password=password, max_file_size=max_file_size)
    result = analyzer.get_hyperlinks()
    return result.model_dump_json(indent=2)


@mcp.tool()
@handle_mcp_errors
def extract_embedded_fonts(
    input_path: str,
    password: str | None = None,
    max_file_size: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> str:
    """
    Extract metadata and buffers of all embedded fonts in a PDF.

    Use this tool to inspect which fonts are actually embedded in a document.
    Custom fonts (TrueType, OpenType) appear as Type0 with their binary
    buffer. Base 14 system fonts (Helvetica, Times, Courier) are NOT
    embedded and will not appear in the results.

    Args:
        input_path: Absolute path to the PDF file to inspect.
        password: Optional password if the PDF is encrypted.
        max_file_size: Maximum allowed input file size in bytes (default: 100 MB).

    Returns:
        JSON string with embedded font metadata including:
        - name: human-readable font name
        - type: font type (Type0, TrueType, etc.)
        - subtype: font subtype (ttf, etc.)
        - buffer_size: size of the font buffer in bytes
        - page_numbers: pages where this font appears

    Example:
        extract_embedded_fonts("/path/to/document.pdf")
    """
    analyzer = PDFAnalyzer(input_path, password=password, max_file_size=max_file_size)
    fonts = analyzer.extract_embedded_fonts()

    return json.dumps(
        {
            "success": True,
            "file_path": input_path,
            "total_fonts": len(fonts),
            "fonts": [
                {
                    "name": f.name,
                    "type": f.type,
                    "subtype": f.subtype,
                    "buffer_size": len(f.buffer),
                    "page_numbers": f.page_numbers,
                }
                for f in fonts
            ],
        },
        indent=2,
    )


@mcp.tool()
@handle_mcp_errors
def batch_modify_pdf_content(
    input_paths: list[str],
    output_dir: str,
    replacements: dict[str, str],
    use_regex: bool = False,
    whole_span: bool = False,
    password: str | None = None,
    max_file_size: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> str:
    """
    Apply the same text replacements to multiple PDF files at once.

    Each file is processed independently -- a failure in one file does
    not stop the rest of the batch. Output files are written to
    ``output_dir`` using the same filename as the input.

    Args:
        input_paths: List of absolute paths to input PDF files.
        output_dir: Directory where modified PDFs will be saved.
        replacements: Dictionary mapping old text to new text.
        use_regex: If true, treat keys as regex patterns.
        password: Optional password if PDFs are encrypted.
        max_file_size: Maximum allowed input file size in bytes (default: 100 MB).

    Returns:
        JSON string with batch results including per-file status.

    Example:
        batch_modify_pdf_content(
            ["/path/a.pdf", "/path/b.pdf"],
            "/path/output",
            {"Draft": "Final", "2024": "2025"}
        )
    """
    spec = ReplacementSpec(replacements=replacements, use_regex=use_regex, whole_span=whole_span)
    result = batch_process(
        input_paths,
        output_dir,
        spec,
        password=password,
        max_file_size=max_file_size,
    )
    return result.model_dump_json(indent=2)


def main() -> None:
    """Run the MCP server with stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
