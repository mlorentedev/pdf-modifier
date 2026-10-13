"""Tests for MCP interface."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import fitz

from pdf_modifier.interfaces.mcp import (
    batch_modify_pdf_content,
    inspect_pdf_fonts,
    list_pdf_hyperlinks,
    mcp,
    modify_pdf_content,
    read_pdf_structure,
)

from ...conftest import SAMPLE_PDF, create_encrypted_pdf, create_pdf

if TYPE_CHECKING:
    from pathlib import Path


class TestMCPServer:
    """Tests for MCP server configuration."""

    def test_server_name(self) -> None:
        assert mcp.name == "pdf-modifier"


class TestMCPReadStructure:
    """Tests for read_pdf_structure tool."""

    def test_returns_valid_json(self) -> None:
        result = read_pdf_structure(str(SAMPLE_PDF))
        parsed = json.loads(result)
        assert "total_pages" in parsed
        assert parsed["total_pages"] >= 1

    def test_contains_pages_array(self) -> None:
        result = read_pdf_structure(str(SAMPLE_PDF))
        parsed = json.loads(result)
        assert "pages" in parsed
        assert len(parsed["pages"]) == parsed["total_pages"]

    def test_error_on_invalid_file(self, tmp_path: Path) -> None:
        result = read_pdf_structure(str(tmp_path / "missing.pdf"))
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert "error" in parsed

    def test_error_json_has_message(self, tmp_path: Path) -> None:
        result = read_pdf_structure(str(tmp_path / "missing.pdf"))
        parsed = json.loads(result)
        assert "message" in parsed
        assert len(parsed["message"]) > 0


class TestMCPInspectFonts:
    """Tests for inspect_pdf_fonts tool."""

    def test_returns_matches(self) -> None:
        result = inspect_pdf_fonts(str(SAMPLE_PDF), ["Order", "$"])
        parsed = json.loads(result)
        assert parsed["total_matches"] >= 1

    def test_no_matches(self) -> None:
        result = inspect_pdf_fonts(str(SAMPLE_PDF), ["XYZNONEXISTENT"])
        parsed = json.loads(result)
        assert parsed["total_matches"] == 0

    def test_error_on_invalid_file(self, tmp_path: Path) -> None:
        result = inspect_pdf_fonts(str(tmp_path / "missing.pdf"), ["anything"])
        parsed = json.loads(result)
        assert parsed["success"] is False


class TestMCPModifyContent:
    """Tests for modify_pdf_content tool."""

    def test_simple_replacement(self, tmp_path: Path) -> None:
        output_pdf = tmp_path / "output.pdf"
        result = modify_pdf_content(str(SAMPLE_PDF), str(output_pdf), {"$27.99": "$99.99"})
        parsed = json.loads(result)
        assert parsed["success"] is True
        assert output_pdf.exists()

    def test_regex_replacement(self, tmp_path: Path) -> None:
        output_pdf = tmp_path / "output.pdf"
        result = modify_pdf_content(
            str(SAMPLE_PDF),
            str(output_pdf),
            {r"January \d{2}, \d{4}": "February 01, 2030"},
            use_regex=True,
        )
        parsed = json.loads(result)
        assert parsed["success"] is True

    def test_hyperlink_syntax(self, tmp_path: Path) -> None:
        output_pdf = tmp_path / "output.pdf"
        result = modify_pdf_content(
            str(SAMPLE_PDF), str(output_pdf), {"Order Summary": "Click|https://example.com"}
        )
        parsed = json.loads(result)
        assert parsed["success"] is True

    def test_void_link_syntax(self, tmp_path: Path) -> None:
        output_pdf = tmp_path / "output.pdf"
        result = modify_pdf_content(
            str(SAMPLE_PDF), str(output_pdf), {"Order Summary": "Summary|void(0)"}
        )
        parsed = json.loads(result)
        assert parsed["success"] is True

    def test_error_on_invalid_file(self, tmp_path: Path) -> None:
        result = modify_pdf_content(
            str(tmp_path / "missing.pdf"), str(tmp_path / "out.pdf"), {"a": "b"}
        )
        parsed = json.loads(result)
        assert parsed["success"] is False

    def test_result_contains_stats(self, tmp_path: Path) -> None:
        output_pdf = tmp_path / "output.pdf"
        result = modify_pdf_content(str(SAMPLE_PDF), str(output_pdf), {"$27.99": "$99.99"})
        parsed = json.loads(result)
        assert "replacements_made" in parsed
        assert "pages_modified" in parsed


class TestMCPListHyperlinks:
    """Tests for list_pdf_hyperlinks tool."""

    def test_returns_valid_json(self) -> None:
        result = list_pdf_hyperlinks(str(SAMPLE_PDF))
        parsed = json.loads(result)
        assert "total_links" in parsed
        assert "links" in parsed

    def test_pdf_with_links(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "with_links.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((100, 100), "Click here")
        link_rect = fitz.Rect(95, 90, 200, 110)
        page.insert_link({"from": link_rect, "uri": "https://example.com", "kind": fitz.LINK_URI})
        doc.save(str(pdf_path))
        doc.close()

        result = list_pdf_hyperlinks(str(pdf_path))
        parsed = json.loads(result)
        assert parsed["total_links"] == 1
        assert parsed["links"][0]["uri"] == "https://example.com"

    def test_error_on_invalid_file(self, tmp_path: Path) -> None:
        result = list_pdf_hyperlinks(str(tmp_path / "missing.pdf"))
        parsed = json.loads(result)
        assert parsed["success"] is False


class TestMCPBatchModify:
    """Tests for batch_modify_pdf_content tool."""

    def test_batch_multiple_files(self, tmp_path: Path) -> None:
        pdf1 = create_pdf(tmp_path / "a.pdf", text="Hello World")
        pdf2 = create_pdf(tmp_path / "b.pdf", text="Hello World")
        output_dir = tmp_path / "out"

        result = batch_modify_pdf_content(
            [str(pdf1), str(pdf2)],
            str(output_dir),
            {"Hello": "Goodbye"},
        )
        parsed = json.loads(result)
        assert parsed["total_files"] == 2
        assert parsed["successful"] == 2
        assert parsed["failed"] == 0

    def test_batch_with_missing_file(self, tmp_path: Path) -> None:
        pdf_good = create_pdf(tmp_path / "good.pdf", text="Hello")
        output_dir = tmp_path / "out"

        result = batch_modify_pdf_content(
            [str(pdf_good), str(tmp_path / "missing.pdf")],
            str(output_dir),
            {"Hello": "Goodbye"},
        )
        parsed = json.loads(result)
        assert parsed["total_files"] == 2
        assert parsed["successful"] == 1
        assert parsed["failed"] == 1
        assert len(parsed["errors"]) == 1

    def test_batch_empty_list(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "out"
        result = batch_modify_pdf_content([], str(output_dir), {"a": "b"})
        parsed = json.loads(result)
        assert parsed["total_files"] == 0
        assert parsed["successful"] == 0
        assert parsed["failed"] == 0

    def test_batch_regex(self, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "test.pdf", text="Date: 2024-01-01")
        output_dir = tmp_path / "out"

        result = batch_modify_pdf_content(
            [str(pdf)],
            str(output_dir),
            {r"\d{4}-\d{2}-\d{2}": "REDACTED"},
            use_regex=True,
        )
        parsed = json.loads(result)
        assert parsed["successful"] == 1


class TestMCPErrorHandling:
    """Tests for error handling decorator behavior."""

    def test_encrypted_pdf_returns_error_json(self, tmp_path: Path) -> None:
        pdf_path = create_encrypted_pdf(tmp_path / "encrypted.pdf")
        result = read_pdf_structure(str(pdf_path))
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert parsed["error"] == "PASSWORD_ERROR"

    def test_same_input_output_returns_error(self, tmp_path: Path) -> None:
        pdf_path = create_pdf(tmp_path / "test.pdf")
        result = modify_pdf_content(str(pdf_path), str(pdf_path), {"a": "b"})
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert parsed["error"] == "UNEXPECTED_ERROR"


class TestMCPWholeSpan:
    """MCP tools accept and propagate whole_span (CORE-146)."""

    def test_modify_whole_span_rejects_substring(self, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "in.pdf", text="24 hours")
        output_pdf = tmp_path / "output.pdf"
        result = modify_pdf_content(str(pdf), str(output_pdf), {"24": "X"}, whole_span=True)
        parsed = json.loads(result)
        assert parsed["success"] is True
        assert parsed["replacements_made"] == 0

    def test_modify_whole_span_accepts_exact(self, tmp_path: Path) -> None:
        """Positive path: an exact-span target still replaces under whole_span."""
        pdf = create_pdf(tmp_path / "in.pdf", text="24")
        output_pdf = tmp_path / "output.pdf"
        result = modify_pdf_content(str(pdf), str(output_pdf), {"24": "25"}, whole_span=True)
        parsed = json.loads(result)
        assert parsed["success"] is True
        assert parsed["replacements_made"] == 1

    def test_batch_whole_span_rejects_substring(self, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "in.pdf", text="24 hours")
        result = batch_modify_pdf_content(
            [str(pdf)], str(tmp_path / "out"), {"24": "X"}, whole_span=True
        )
        parsed = json.loads(result)
        assert parsed["failed"] == 0
        assert all(r["replacements_made"] == 0 for r in parsed["results"])
