"""Which spans a spec matches, and with which of its rules.

Two defects in `_collect_replacements` / `_match_single_span`:

* A line with two separately styled spans that BOTH match lost the second one: the
  span loop stopped at the first hit, so the second target stayed in the output
  while the run reported success.
* With overlapping literal targets (`Total` and `Total due`), the rule entered first
  won, so the more specific rule never fired on the text it was written for. The
  longest literal target must win, whatever order the caller listed them in.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import fitz

from pdf_modifier.core import PDFModifier
from pdf_modifier.core.models import ReplacementSpec

if TYPE_CHECKING:
    from pathlib import Path

FONTSIZE = 12.0


def _one_line_two_spans(path: Path, left: str, right: str) -> Path:
    """Two spans in ONE text object, split by a colour change.

    Built from a raw content stream on purpose: two `insert_text` calls land in two
    blocks, and the span loop's early exit only bites inside a single line, so the
    convenient fixture cannot fail.
    """
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((0, 0), " ", fontname="helv", fontsize=FONTSIZE)  # registers /helv
    stream = f"BT /helv {FONTSIZE} Tf 50 742 Td ({left}) Tj 0.2 0.2 0.2 rg ( {right}) Tj ET"
    xref = doc.get_new_xref()
    doc.update_object(xref, "<<>>")
    doc.update_stream(xref, stream.encode())
    doc.xref_set_key(page.xref, "Contents", f"{xref} 0 R")
    doc.save(str(path))
    doc.close()
    with fitz.open(str(path)) as check:
        lines = [ln for b in check[0].get_text("dict")["blocks"] for ln in b.get("lines", [])]
        assert len(lines) == 1, "fixture must put both spans on one line"
        assert len(lines[0]["spans"]) == 2, "fixture must split the line into two spans"
    return path


def _single_span(path: Path, text: str) -> Path:
    doc = fitz.open()
    doc.new_page().insert_text((50, 100), text, fontname="helv", fontsize=FONTSIZE)
    doc.save(str(path))
    doc.close()
    return path


def _page_text(path: Path) -> str:
    with fitz.open(str(path)) as doc:
        return str(doc[0].get_text())


def test_two_matching_spans_on_one_line_are_both_replaced(tmp_path: Path) -> None:
    source = _one_line_two_spans(tmp_path / "in.pdf", "Alpha", "Beta")
    out = tmp_path / "out.pdf"

    result = PDFModifier(str(source), str(out)).process(
        ReplacementSpec(replacements={"Alpha": "One", "Beta": "Two"})
    )

    assert result.replacements_made == 2
    text = _page_text(out)
    assert "One" in text
    assert "Two" in text
    assert "Beta" not in text


def test_longest_literal_target_wins_regardless_of_order(tmp_path: Path) -> None:
    source = _single_span(tmp_path / "in.pdf", "Total due now")
    out = tmp_path / "out.pdf"

    PDFModifier(str(source), str(out)).process(
        ReplacementSpec(replacements={"Total": "Sum", "Total due": "Balance"})
    )

    text = _page_text(out)
    assert "Balance now" in text
    assert "Sum" not in text


def test_longest_literal_wins_across_the_two_matching_passes(tmp_path: Path) -> None:
    """#220: `Total due` drawn as two spans must beat `Total` matching the first one.

    The single-span pass used to reserve `Total` before the cross-span pass could
    see the longer rule, so precedence followed pass order instead of length.
    """
    source = _one_line_two_spans(tmp_path / "in.pdf", "Total", "due")
    out = tmp_path / "out.pdf"

    result = PDFModifier(str(source), str(out)).process(
        ReplacementSpec(replacements={"Total": "Sum", "Total due": "Balance"})
    )

    assert result.replacements_made == 1
    text = _page_text(out)
    assert "Balance" in text
    assert "Sum" not in text


def test_regex_rules_keep_the_callers_order_across_passes(tmp_path: Path) -> None:
    """Pattern length says nothing about specificity, so regex order is the caller's."""
    source = _one_line_two_spans(tmp_path / "in.pdf", "Total", "due")
    out = tmp_path / "out.pdf"

    PDFModifier(str(source), str(out)).process(
        ReplacementSpec(replacements={"Tot": "Sum", "Total due": "Balance"}, use_regex=True)
    )

    text = _page_text(out)
    assert "Sum" in text
    assert "Balance" not in text


def test_a_cross_span_match_keeps_the_text_around_it(tmp_path: Path) -> None:
    """A rule matching the END of one span and the START of the next must not
    take the rest of those spans with it: `Invoice ` and ` today` stay."""
    source = _one_line_two_spans(tmp_path / "in.pdf", "Invoice Total", "due today")
    out = tmp_path / "out.pdf"

    PDFModifier(str(source), str(out)).process(
        ReplacementSpec(replacements={"Total due": "Balance"})
    )

    text = _page_text(out)
    assert "Balance" in text
    assert "Invoice" in text
    assert "today" in text
