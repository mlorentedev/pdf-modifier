"""A replacement wider than its slot must not overprint the next object silently.

The engine replaces text in place: it redacts the target span and inserts the new
text at the same origin. When the new text is wider than the gap to the next span
on the same baseline, the two draw on top of each other and the line becomes
unreadable, while the run reports success with no warning.

The fixture is a label span and a value span sharing one baseline, split into two
objects by a colour change -- the shape of any key-value line.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import fitz

from pdf_modifier.core import PDFModifier
from pdf_modifier.core.models import ReplacementSpec

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

LABEL_ORIGIN = (50.0, 100.0)
FONTSIZE = 12.0


def _label_value_pdf(path: Path, label: str = "Short", value: str = ": 12345") -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(LABEL_ORIGIN, label, fontname="helv", fontsize=FONTSIZE)
    label_width = fitz.get_text_length(label, fontname="helv", fontsize=FONTSIZE)
    page.insert_text(
        (LABEL_ORIGIN[0] + label_width, LABEL_ORIGIN[1]),
        value,
        fontname="helv",
        fontsize=FONTSIZE,
        color=(0.2, 0.2, 0.2),
    )
    doc.save(str(path))
    doc.close()
    return path


def _run(tmp_path: Path, replacement: str) -> list[str]:
    source = _label_value_pdf(tmp_path / "in.pdf")
    result = PDFModifier(str(source), str(tmp_path / "out.pdf")).process(
        ReplacementSpec(replacements={"Short": replacement})
    )
    return result.warnings


def test_replacement_wider_than_slot_warns_about_overprint(tmp_path: Path) -> None:
    warnings = _run(tmp_path, "A much longer label")

    overprint = [w for w in warnings if "overprint" in w]
    assert len(overprint) == 1
    assert "A much longer label" in overprint[0]
    assert ": 12345" in overprint[0]


def test_replacement_that_fits_does_not_warn(tmp_path: Path) -> None:
    warnings = _run(tmp_path, "Tiny")

    assert not [w for w in warnings if "overprint" in w]


def test_replacement_keeps_neighbour_text(tmp_path: Path) -> None:
    _run(tmp_path, "A much longer label")

    with fitz.open(str(tmp_path / "out.pdf")) as doc:
        text = doc[0].get_text()
    assert "12345" in text


def test_two_replacements_that_collide_warn(tmp_path: Path) -> None:
    """Both originals are redacted, so neither is in the surviving text to collide with."""
    source = _label_value_pdf(tmp_path / "in.pdf")
    result = PDFModifier(str(source), str(tmp_path / "out.pdf")).process(
        ReplacementSpec(replacements={"Short": "A much longer label", ": 12345": ": 67890"})
    )

    overprint = [w for w in result.warnings if "overprint" in w]
    assert len(overprint) == 1
    assert "A much longer label" in overprint[0]
    assert ": 67890" in overprint[0]


def test_overprint_log_carries_no_document_text(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """The returned warning names the text; the application log must not."""
    with caplog.at_level(logging.WARNING, logger="pdf_modifier.core.modifier"):
        _run(tmp_path, "A much longer label")

    logged = [r.getMessage() for r in caplog.records if "overprint" in r.getMessage()]
    assert logged
    assert not [m for m in logged if "12345" in m or "longer label" in m]
