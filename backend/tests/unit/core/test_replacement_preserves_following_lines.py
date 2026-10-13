"""A replacement must not drop the lines that follow it.

CORE-001 / #179. Replacing a span inside a multi-line block of a real receipt
silently removed the two lines after it: `ARC: 00` and `CVM: 5E0000` were absent
from the output, the file opened and rendered normally, and a check for "are the
values I expect present?" passed while the document was missing lines.

The fixture is generated here, not committed: ten short Courier-Bold lines in one
block, the shape of a receipt's payment block. It is deliberately **synthetic** --
the document that found this is the owner's and does not belong in the repository.

Three things the fixture must get right, all learned the hard way:

* **One text object per line.** The same block built with a single `insert_textbox`
  splits into two blocks and loses nothing. Only the multi-object build reproduces
  the defect, so a fixture written the convenient way cannot fail, and a fixture
  that cannot fail is not a fixture.
* **The three replacement sizes**, because that is what rules out the obvious fix.
  Wider, narrower and a four-character value all lose the same two lines, so
  "make the new text fit" cannot be the mechanism.
* **A target line drawn as two objects.** A key-value receipt line is a label span
  and a value span sharing one baseline, and a style change (colour here) is what
  splits them. The first fix round trimmed the redaction rect in y unconditionally,
  so such a neighbour -- which is BESIDE the target, not above it -- dragged the
  rect onto itself and the guard returned the raw one, dropping `ARC: 00` and
  `CVM: 5E0000` again. Every row of the first version used single-style lines, so
  none could see it: the same trap as the one above, one level up.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import fitz
import pytest

from pdf_modifier.core.exceptions import PDFModifierError
from pdf_modifier.core.models import ReplacementSpec

if TYPE_CHECKING:
    from pathlib import Path
from pdf_modifier.core.modifier import PDFModifier

TARGET = "68D489883C5B7A25"

LINES = [
    "************* EMV PURCHASE",
    "App Label:                VISA CREDIT",
    "Mode:                             Issuer",
    "AID: A0000000031010",
    "TVR: 0000008000",
    "IAD: 0602120360A002",
    "TSI: E800",
    "ARC: 00",
    f"AC:  {TARGET}",
    "CVM: 5E0000",
]


STRUCTURES = ("object-per-line", "mixed-style-line", "single-object")


def write_payment_block(path: Path, *, structure: str) -> None:
    """Ten short monospace lines in one block, in three possible structures."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    if structure == "single-object":
        page.insert_textbox(
            fitz.Rect(72, 72, 540, 500), "\n".join(LINES), fontname="cobo", fontsize=9
        )
    else:
        y = 72.0
        for line in LINES:
            if structure == "mixed-style-line" and line.startswith("AC:"):
                # Label and value as two objects on ONE baseline, the value in a
                # different colour: how a receipt emits a key-value line.
                label = "AC:  "
                page.insert_text((72, y), label, fontname="cobo", fontsize=9)
                offset = fitz.get_text_length(label, fontname="cobo", fontsize=9)
                page.insert_text(
                    (72 + offset, y), TARGET, fontname="cobo", fontsize=9, color=(0, 0, 1)
                )
            else:
                page.insert_text((72, y), line, fontname="cobo", fontsize=9)
            y += 11.0
    doc.save(str(path))
    doc.close()


def read_lines(path: Path) -> list[str]:
    doc = fitz.open(str(path))
    lines = [line.strip() for line in doc[0].get_text().splitlines() if line.strip()]
    doc.close()
    return lines


def run_replacement(tmp_path: Path, replacement: str, *, structure: str) -> tuple:
    src, out = tmp_path / "in.pdf", tmp_path / "out.pdf"
    write_payment_block(src, structure=structure)
    PDFModifier(str(src), str(out)).process(ReplacementSpec(replacements={TARGET: replacement}))
    return read_lines(src), read_lines(out)


def missing_untouched_lines(before: list[str], after: list[str]) -> list[str]:
    """Set inclusion, not presence of expectations: the check that can see a deletion.

    A line is allowed to be absent only if it is the one that was replaced.
    """
    replaced = f"AC:  {TARGET}"
    return [line for line in before if line != replaced and line not in after]


REPLACEMENTS = ("9F3C1D7A4E620B85", "1111111111111111", "ABCD")
SIZES = ("wider", "narrower", "shorter")


@pytest.mark.parametrize("structure", ["object-per-line", "single-object"])
@pytest.mark.parametrize("replacement", REPLACEMENTS, ids=SIZES)
def test_no_untouched_line_is_lost(tmp_path: Path, replacement: str, structure: str) -> None:
    """The original defect: a multi-object block loses the lines after the span."""
    before, after = run_replacement(tmp_path, replacement, structure=structure)
    missing = missing_untouched_lines(before, after)
    assert not missing, (
        f"the replacement of a {len(TARGET)}-character span in a "
        f"{structure} block dropped {len(missing)} line(s) that were not "
        f"replaced: {missing}"
    )


@pytest.mark.parametrize("replacement", REPLACEMENTS, ids=SIZES)
def test_no_untouched_line_is_lost_when_the_target_line_has_two_spans(
    tmp_path: Path, replacement: str
) -> None:
    """The Blocker from CORE-001's independent review, in the same three sizes.

    The label and the value are two text objects on one baseline, so the neighbour
    that overlaps the redaction rect is horizontal. A y-only trim dragged the rect
    onto itself, the guard returned the raw rect, and `ARC: 00` and `CVM: 5E0000`
    were dropped again -- the defect CORE-001 exists to fix, restored by its fix.
    """
    before, after = run_replacement(tmp_path, replacement, structure="mixed-style-line")
    missing = missing_untouched_lines(before, after)
    assert not missing, (
        f"the replacement of a {len(TARGET)}-character span on a line drawn as two "
        f"objects dropped {len(missing)} line(s) that were not replaced: {missing}"
    )


class _StubPage:
    """A page whose only text object sits where the test needs it.

    The fitter reads the page through `get_text("dict")` alone, so the failing fit
    can be pinned exactly instead of hoping a real layout collapses.
    """

    number = 0

    def __init__(self, spans: list[tuple[float, float, float, float]]) -> None:
        self._spans = spans

    def get_text(self, _kind: str) -> dict[str, object]:
        return {"blocks": [{"lines": [{"spans": [{"bbox": s} for s in self._spans]}]}]}


def test_a_collapsing_fit_raises_instead_of_redacting_the_raw_rect() -> None:
    """Area 0 is a fitting failure, not a small rect: say so, never fall through.

    The fall-through to the raw rect is the mechanism of the Blocker, and the raw
    rect here is the one that loses the neighbouring lines.
    """
    rect = fitz.Rect(100.0, 100.0, 100.01, 112.0)
    # Same vertical band, so only x separates them: it overlaps the rect's left
    # edge and, trimmed in x, leaves the rect inverted.
    neighbour = (50.0, 100.0, 100.004, 112.0)
    page = cast("fitz.Page", _StubPage([neighbour]))

    with pytest.raises(PDFModifierError) as raised:
        PDFModifier._fit_redaction_to_its_own_text_object(page, rect)

    assert "collapsed" in str(raised.value), "the fit must report the collapse it hit"
    assert raised.value.details["page"] == 1
