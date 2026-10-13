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


def read_span_texts(path: Path) -> list[str]:
    """Every text object's own text, which is where a ONE-character residue shows up."""
    doc = fitz.open(str(path))
    texts = [
        span["text"].strip()
        for block in doc[0].get_text("dict")["blocks"]
        for line in block.get("lines", [])
        for span in line["spans"]
    ]
    doc.close()
    return [text for text in texts if text]


def surviving_value_spans(after_spans: list[str]) -> list[str]:
    """Output text objects whose text is a piece of the replaced value.

    The assertion a substring window cannot make at ONE character, which is the
    length round 3's Finding 1 was: after a redaction rewrites what is left of the
    object, a single surviving character is its own text object, so the span level
    is where it is still visible as itself.
    """
    return [text for text in after_spans if text in TARGET]


def run_replacement(tmp_path: Path, replacement: str, *, structure: str) -> tuple:
    """Run one replacement over a generated block; return its lines before, after, and its path."""
    src, out = tmp_path / "in.pdf", tmp_path / "out.pdf"
    write_payment_block(src, structure=structure)
    PDFModifier(str(src), str(out)).process(ReplacementSpec(replacements={TARGET: replacement}))
    return read_lines(src), read_lines(out), out


def missing_untouched_lines(before: list[str], after: list[str]) -> list[str]:
    """Set inclusion, not presence of expectations: the check that can see a deletion.

    A line is allowed to be absent only if it is the one that was replaced.
    """
    replaced = f"AC:  {TARGET}"
    return [line for line in before if line != replaced and line not in after]


def surviving_fragments(after_text: str, replacement: str, window: int = 2) -> list[str]:
    """Parts of the replaced value still on the page, after the replacement ran.

    The assertion set inclusion cannot make. A line that survived PARTIALLY is not
    a missing line, it is an extra one, so `missing_untouched_lines` reports
    nothing while a piece of the old value sits under the new one -- which is what
    round 2's Major finding produced (`68D489`).

    Two windows, measured. A 4-character window missed a 3-character tail (`A25`),
    and a 1-character window flags ordinary digits on the neighbouring lines. The
    windows the REPLACEMENT also contains are subtracted first: `3C` occurs in both
    `9F3C1D7A4E620B85` and the value it replaces, so without that subtraction the
    check reports the fix as a defect.
    """
    old = {TARGET[i : i + window] for i in range(len(TARGET) - window + 1)}
    new = {replacement[i : i + window] for i in range(len(replacement) - window + 1)}
    return sorted(fragment for fragment in old - new if fragment in after_text)


REPLACEMENTS = ("9F3C1D7A4E620B85", "1111111111111111", "ABCD")
SIZES = ("wider", "narrower", "shorter")


@pytest.mark.parametrize("structure", ["object-per-line", "single-object"])
@pytest.mark.parametrize("replacement", REPLACEMENTS, ids=SIZES)
def test_no_untouched_line_is_lost(tmp_path: Path, replacement: str, structure: str) -> None:
    """The original defect: a multi-object block loses the lines after the span."""
    before, after, out = run_replacement(tmp_path, replacement, structure=structure)
    missing = missing_untouched_lines(before, after)
    assert not missing, (
        f"the replacement of a {len(TARGET)}-character span in a "
        f"{structure} block dropped {len(missing)} line(s) that were not "
        f"replaced: {missing}"
    )
    assert not surviving_fragments(
        "\n".join(after), replacement
    ), "part of the replaced value is still on the page"
    assert not surviving_value_spans(
        read_span_texts(out)
    ), "a piece of the replaced value survives as its own text object"


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
    before, after, out = run_replacement(tmp_path, replacement, structure="mixed-style-line")
    missing = missing_untouched_lines(before, after)
    assert not missing, (
        f"the replacement of a {len(TARGET)}-character span on a line drawn as two "
        f"objects dropped {len(missing)} line(s) that were not replaced: {missing}"
    )
    assert not surviving_fragments(
        "\n".join(after), replacement
    ), "part of the replaced value is still on the page"
    assert not surviving_value_spans(
        read_span_texts(out)
    ), "a piece of the value survives as its own object"


SLIVER_LABEL = "ACCOUNT: "
SLIVER_VALUE_X = 115.6


def write_sliver_neighbour(path: Path) -> None:
    """A label whose BOX overlaps the value's first glyph with no ink in common.

    `ACCOUNT: ` ends in a space, so its box runs 5.4 pt past its ink. A value drawn
    0.4 pt into that box overlaps the first glyph by 0.4 pt -- 7% of a 5.4 pt
    glyph -- which `intersects` calls a hit and `apply_redactions` does not act on.
    That is round 3's Finding 1, and it is ONE character long: no substring window
    of two can see it.
    """
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "ARC: 00", fontname="cobo", fontsize=9)
    page.insert_text((72, 83), SLIVER_LABEL, fontname="cobo", fontsize=9)
    page.insert_text((SLIVER_VALUE_X, 83), TARGET, fontname="cobo", fontsize=9, color=(0, 0, 1))
    page.insert_text((72, 94), "CVM: 5E0000", fontname="cobo", fontsize=9)
    doc.save(str(path))
    doc.close()


@pytest.mark.parametrize("replacement", REPLACEMENTS, ids=SIZES)
def test_no_character_of_the_value_survives_a_sub_character_overlap(
    tmp_path: Path, replacement: str
) -> None:
    """Round 3's Finding 1: `intersects` is not the redactor's predicate.

    A candidate kept because it *intersects* a glyph can leave that glyph in place,
    because `apply_redactions` acts only from GLYPH_COVERAGE_FLOOR of the box
    (measured at 10.0% of the width across five font sizes). The assertion is the
    span-level one: a single surviving character is invisible to the two-character
    window and to line-level inclusion, and this residue is one character long.
    """
    src, out = tmp_path / "in.pdf", tmp_path / "out.pdf"
    write_sliver_neighbour(src)
    PDFModifier(str(src), str(out)).process(ReplacementSpec(replacements={TARGET: replacement}))

    dropped = [line for line in ("ARC: 00", "CVM: 5E0000") if line not in read_lines(out)]
    assert not dropped, f"a line beside the value was dropped: {dropped}"
    residue = surviving_value_spans(read_span_texts(out))
    assert not residue, (
        f"the value is still on the page in pieces after a 0.4 pt overlap: {residue!r} "
        f"survived, because the trim was accepted on `intersects` rather than on the "
        f"share of the glyph the redactor actually needs"
    )


# The overprint shapes round 2 measured. Each one moves the second object to a
# different part of the target's own run, so each one makes the fitter trim a
# different edge -- and each one used to leave a different part of the value: the
# head, a middle piece, or the tail.
OVERPRINTS = {
    # characters of the target to skip before the overprint starts, and its text
    "overlapping-head": (0, "ZZZZZZ"),
    "nested": (4, "ZZ"),
    "overlapping-tail": (13, "ZZZZZZ"),
}


def write_overprinted_value(path: Path, *, shape: str) -> None:
    """A tight three-line block whose target line carries a SECOND object over it.

    A key-value line drawn as two objects and a stamp or an overprinted object are
    one shape to the redactor: a neighbour box that overlaps the target's own glyph
    run. The block stays three lines, so a neighbour dropped beside the target is
    unmistakable.
    """
    skip, overprint = OVERPRINTS[shape]
    label = "AC:  "
    value_x = 72.0 + fitz.get_text_length(label, fontname="cobo", fontsize=9)
    char_width = fitz.get_text_length(TARGET, fontname="cobo", fontsize=9) / len(TARGET)

    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    for y, line in ((72.0, "ARC: 00"), (83.0, label + TARGET), (94.0, "CVM: 5E0000")):
        if line != label + TARGET:
            page.insert_text((72.0, y), line, fontname="cobo", fontsize=9)
            continue
        page.insert_text((72.0, y), label, fontname="cobo", fontsize=9)
        page.insert_text((value_x, y), TARGET, fontname="cobo", fontsize=9, color=(0, 0, 1))
    page.insert_text(
        (value_x + skip * char_width, 83.0), overprint, fontname="cobo", fontsize=9, color=(1, 0, 0)
    )
    doc.save(str(path))
    doc.close()


@pytest.mark.parametrize("shape", sorted(OVERPRINTS))
@pytest.mark.parametrize("replacement", REPLACEMENTS, ids=SIZES)
def test_no_untouched_line_is_lost_when_a_neighbour_overlaps_the_target(
    tmp_path: Path, replacement: str, shape: str
) -> None:
    """Round 2's Major finding: the neighbour OVERLAPS the target's own glyph run.

    Trimming x to get past such a neighbour cuts INSIDE the target, and redaction
    is per character, so the characters left outside the rect survive under the
    replacement: the replaced value stays visible, and nothing fails. It is not a
    neighbour to trim against -- it is the same ink, so the rect covers both --
    and the assertion that catches that is the one set inclusion cannot make: no
    fragment of the replaced value may remain.

    The overprint itself is expected to go with the target, and asserting it stays
    would be asserting the defect back: the two objects share the glyph run, so a
    redaction that reaches one reaches the other. What must not happen is the
    VALUE outliving its own replacement, which is the line below.
    """
    src, out = tmp_path / "in.pdf", tmp_path / "out.pdf"
    write_overprinted_value(src, shape=shape)
    PDFModifier(str(src), str(out)).process(ReplacementSpec(replacements={TARGET: replacement}))
    after = read_lines(out)

    dropped = [line for line in ("ARC: 00", "CVM: 5E0000") if line not in after]
    assert not dropped, f"a line beside an overprinted target was dropped: {dropped}"
    fragments = surviving_fragments("\n".join(after), replacement)
    assert not fragments, (
        f"the replaced value is still on the page in the {shape!r} shape: {fragments} "
        f"survived the redaction, so the trim cut inside the target's own glyph run"
    )


SHARED_LABEL = "ACCOUNT: "
SHARED_VALUE_X = 84.0


def write_shared_ink_line(path: Path) -> None:
    """A label whose INK runs under the value: 12 pt of real overlap, not a sliver.

    No trim can separate these two objects -- their characters are drawn in the
    same place -- so removing the target removes the characters it shares.
    """
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "ARC: 00", fontname="cobo", fontsize=9)
    page.insert_text((72, 83), SHARED_LABEL, fontname="cobo", fontsize=9)
    page.insert_text((SHARED_VALUE_X, 83), TARGET, fontname="cobo", fontsize=9, color=(0, 0, 1))
    page.insert_text((72, 94), "CVM: 5E0000", fontname="cobo", fontsize=9)
    doc.save(str(path))
    doc.close()


def test_a_label_sharing_the_target_ink_loses_exactly_the_shared_characters(
    tmp_path: Path,
) -> None:
    """Round 3's Finding 2: accepted, stated, and pinned so it cannot GROW.

    Removing the target removes the characters drawn where it is. There is no
    geometry that separates them -- a redaction reaching one reaches the other -- so
    the label loses the characters the rectangle covers. The alternatives were
    refusing the whole document (worse for a receipt that is otherwise fine) and
    re-inserting the neighbour's characters (a capability this repair does not add:
    ADR-014 condition 3, and re-insertion through a subset-embedded font is the trap
    `#179` lost a day to). What must not happen is the loss going unnoticed or
    growing, so this row asserts the exact shape of it: the label survives as a
    truncated prefix of itself, with nothing added, reordered or invented.
    """
    src, out = tmp_path / "in.pdf", tmp_path / "out.pdf"
    write_shared_ink_line(src)
    PDFModifier(str(src), str(out)).process(ReplacementSpec(replacements={TARGET: REPLACEMENTS[0]}))
    spans = read_span_texts(out)

    dropped = [line for line in ("ARC: 00", "CVM: 5E0000") if line not in read_lines(out)]
    assert not dropped, f"a line beside the value was dropped: {dropped}"
    assert not surviving_value_spans(spans), "the replaced value left a piece behind"

    label = SHARED_LABEL.strip()
    survivors = [s for s in spans if s != label and label.startswith(s)]
    assert len(survivors) == 1, f"the label must survive as one truncated run, not {spans!r}"
    assert 0 < len(survivors[0]) < len(label), (
        f"the surviving label {survivors[0]!r} is not shorter than {label!r}: the "
        f"shared-ink deletion did not happen, so this row no longer pins anything"
    )


TIGHT_BLOCKS = ((12.0, 9.0), (9.0, 7.0))
TIGHT_LINES = 8
TIGHT_TARGET_LINE = 3


def write_tight_leading_block(path: Path, *, font: float, leading: float) -> None:
    """A block whose leading is tighter than its own glyph height.

    The target's glyph box overlaps the line below it, so every rect that covers
    the target also reaches that neighbour's characters. Trimming is the only way
    to spare them, and the trim that would is refused for leaving the target under
    the coverage floor: there is no safe rect, only a choice of which line to lose.
    """
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    for index in range(TIGHT_LINES):
        text = TARGET if index == TIGHT_TARGET_LINE else f"keepkeep{index}"
        page.insert_text((72, 72 + index * leading), text, fontname="cobo", fontsize=font)
    doc.save(str(path))
    doc.close()


@pytest.mark.parametrize(
    ("font", "leading"),
    TIGHT_BLOCKS,
    ids=[f"{font}pt-on{leading}pt" for font, leading in TIGHT_BLOCKS],
)
def test_a_tight_block_is_refused_rather_than_losing_the_line_below(
    tmp_path: Path, font: float, leading: float
) -> None:
    """The second signer's Major: a refused trim handed the damage to a line.

    At 12 pt on 9 pt leading each single trim is accepted and the rect is left
    thin; the next one is refused, and the neighbour it was trimming against --
    the line BELOW, not the object being replaced -- was redacted and never
    re-inserted. Measured on the previous revision, with no error and no warning:
    `keepkeep4` became `p4`. A refused trim is not free, so the fit refuses.
    """
    src, out = tmp_path / "in.pdf", tmp_path / "out.pdf"
    write_tight_leading_block(src, font=font, leading=leading)

    with pytest.raises(PDFModifierError) as raised:
        PDFModifier(str(src), str(out)).process(
            ReplacementSpec(replacements={TARGET: REPLACEMENTS[0]})
        )

    assert "neighbouring line" in str(raised.value), "the refusal must name what it protects"
    source = fitz.open(str(src))[0]
    neighbour = next(
        span["bbox"]
        for block in source.get_text("rawdict")["blocks"]
        for line in block.get("lines", [])
        for span in line["spans"]
        if "".join(char["c"] for char in span["chars"]) == f"keepkeep{TIGHT_TARGET_LINE + 1}"
    )
    assert raised.value.details["neighbour"] == [
        float(v) for v in neighbour
    ], "the refusal must name the line it protects, not a line at random"
    assert not out.exists(), "a refused conversion must not leave a half-written document"


@pytest.mark.parametrize(
    ("font", "leading"), ((10.0, 8.0), (12.0, 10.0)), ids=["10pt-on8pt", "12pt-on10pt"]
)
def test_a_slightly_tight_block_is_still_fitted_without_losing_anything(
    tmp_path: Path, font: float, leading: float
) -> None:
    """The boundary from the other side: the measured floor must not over-refuse.

    10 pt on 8 pt leading is the third shape the second signer listed, and it
    failed only because 15% of a glyph is stricter than the redactor needs: at the
    measured 10% transition the trim is accepted, the line below keeps every
    character, and the target is still replaced. Without this row, "refuse when
    unsure" is indistinguishable from a fitter that refuses too much -- and every
    unnecessary refusal is a document that used to convert.
    """
    src, out = tmp_path / "in.pdf", tmp_path / "out.pdf"
    write_tight_leading_block(src, font=font, leading=leading)

    PDFModifier(str(src), str(out)).process(ReplacementSpec(replacements={TARGET: REPLACEMENTS[0]}))

    lines = read_lines(out)
    dropped = [
        f"keepkeep{index}"
        for index in range(TIGHT_LINES)
        if index != TIGHT_TARGET_LINE and f"keepkeep{index}" not in lines
    ]
    assert not dropped, f"a line beside the target was dropped: {dropped}"
    assert REPLACEMENTS[0] in lines, "the target was not replaced"
    assert TARGET not in lines, "the target survived"


class _StubPage:
    """A page whose text objects sit exactly where a test needs them.

    The fitter reads the page through `get_text("rawdict")` alone, so a failing fit
    can be pinned exactly instead of hoping a real layout produces one. `chars` is
    what the fitter identifies the object being replaced by, so a span without them
    is a different case -- the one the refusal row below pins.
    """

    number = 0

    def __init__(
        self,
        spans: list[tuple[float, float, float, float]],
        *,
        with_chars: bool = True,
    ) -> None:
        self._spans = spans
        self._with_chars = with_chars

    def get_text(self, _kind: str) -> dict[str, object]:
        def span(box: tuple[float, float, float, float]) -> dict[str, object]:
            entry: dict[str, object] = {"bbox": box}
            if self._with_chars:
                # One character box filling the span, which is all the fitter reads.
                entry["chars"] = [{"bbox": box}]
            return entry

        return {"blocks": [{"lines": [{"spans": [span(b) for b in self._spans]}]}]}


def test_a_collapsing_fit_raises_instead_of_redacting_the_raw_rect() -> None:
    """Area 0 is a fitting failure, not a small rect: say so, never fall through.

    The fall-through to the raw rect is the mechanism of the Blocker, and the raw
    rect here is the one that loses the neighbouring lines.
    """
    rect = fitz.Rect(100.0, 100.0, 100.01, 112.0)
    # Same vertical band, so only x separates them: it overlaps the rect's left edge
    # and, trimmed in x, leaves the rect inverted.
    neighbour = (50.0, 100.0, 100.004, 112.0)
    # The object being replaced, which has to hold the rect's centre for the fit to
    # know whose glyphs to protect.
    target = (100.004, 100.0, 110.0, 112.0)
    page = cast("fitz.Page", _StubPage([neighbour, target]))

    with pytest.raises(PDFModifierError) as raised:
        PDFModifier._fit_redaction_to_its_own_text_object(page, rect)

    assert "collapsed" in str(raised.value), "the fit must report the collapse it hit"
    assert raised.value.details["page"] == 1


def test_a_target_that_cannot_be_identified_is_refused_not_trimmed_unguarded() -> None:
    """No glyph boxes means no coverage rule, and nothing to trim against.

    `all(... for glyph in [])` is True, so an unidentified object made every trim
    "safe" and rounds 1 and 2's misclassifications would return silently (round-3
    Finding 4). The same rule as the empty rectangle: refuse rather than proceed.
    """
    rect = fitz.Rect(100.0, 100.0, 100.01, 112.0)
    page = cast("fitz.Page", _StubPage([(100.0, 100.0, 110.0, 112.0)], with_chars=False))

    with pytest.raises(PDFModifierError) as raised:
        PDFModifier._fit_redaction_to_its_own_text_object(page, rect)

    assert "cannot be identified" in str(raised.value)
