"""A replacement must not drop the lines that follow it.

CORE-001 / #179. Replacing a span inside a multi-line block of a real receipt
silently removed the two lines after it: `ARC: 00` and `CVM: 5E0000` were absent
from the output, the file opened and rendered normally, and a check for "are the
values I expect present?" passed while the document was missing lines.

The fixture is generated here, not committed: ten short Courier-Bold lines in one
block, the shape of a receipt's payment block. It is deliberately **synthetic** --
the document that found this is the owner's and does not belong in the repository.

Two things the fixture must get right, both learned the hard way:

* **One text object per line.** The same block built with a single `insert_textbox`
  splits into two blocks and loses nothing. Only the multi-object build reproduces
  the defect, so a fixture written the convenient way cannot fail, and a fixture
  that cannot fail is not a fixture.
* **The three replacement sizes**, because that is what rules out the obvious fix.
  Wider, narrower and a four-character value all lose the same two lines, so
  "make the new text fit" cannot be the mechanism.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import fitz
import pytest

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


def write_payment_block(path: Path, *, one_object_per_line: bool) -> None:
    """Ten short monospace lines in one block, in two possible structures."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    if one_object_per_line:
        y = 72.0
        for line in LINES:
            page.insert_text((72, y), line, fontname="cobo", fontsize=9)
            y += 11.0
    else:
        page.insert_textbox(
            fitz.Rect(72, 72, 540, 500), "\n".join(LINES), fontname="cobo", fontsize=9
        )
    doc.save(str(path))
    doc.close()


def read_lines(path: Path) -> list[str]:
    doc = fitz.open(str(path))
    lines = [line.strip() for line in doc[0].get_text().splitlines() if line.strip()]
    doc.close()
    return lines


def run_replacement(tmp_path: Path, replacement: str, *, one_object_per_line: bool) -> tuple:
    src, out = tmp_path / "in.pdf", tmp_path / "out.pdf"
    write_payment_block(src, one_object_per_line=one_object_per_line)
    PDFModifier(str(src), str(out)).process(ReplacementSpec(replacements={TARGET: replacement}))
    return read_lines(src), read_lines(out)


@pytest.mark.parametrize(
    "one_object_per_line", [True, False], ids=["object-per-line", "single-object"]
)
@pytest.mark.parametrize(
    "replacement",
    ["9F3C1D7A4E620B85", "1111111111111111", "ABCD"],
    ids=["wider", "narrower", "shorter"],
)
def test_no_untouched_line_is_lost(
    tmp_path: Path, replacement: str, one_object_per_line: bool
) -> None:
    """Set inclusion, not presence of expectations: the check that can see a deletion.

    A line is allowed to be absent only if it is the one that was replaced.
    """
    before, after = run_replacement(tmp_path, replacement, one_object_per_line=one_object_per_line)
    replaced = f"AC:  {TARGET}"
    missing = [line for line in before if line != replaced and line not in after]
    assert not missing, (
        f"the replacement of a {len(TARGET)}-character span in a "
        f"{'multi-object' if one_object_per_line else 'single-object'} block dropped "
        f"{len(missing)} line(s) that were not replaced: {missing}"
    )
