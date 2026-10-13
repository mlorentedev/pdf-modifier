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


def missing_untouched_lines(
    before: list[str], after: list[str], replaced: str | None = None
) -> list[str]:
    """Set inclusion, not presence of expectations: the check that can see a deletion.

    A line is allowed to be absent only if it is the one that was replaced, and the
    caller says which line that is: a fixture whose target line reads just the value
    (the tight blocks and the watermark page) would otherwise report its own
    replacement as a dropped line, which is the shape of a false alarm this file has
    already been bitten by.
    """
    target_line = f"AC:  {TARGET}" if replaced is None else replaced
    return [line for line in before if line != target_line and line not in after]


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
    fragments = surviving_fragments("\n".join(after), replacement)
    assert not fragments, "part of the replaced value is still on the page"
    survived = surviving_value_spans(read_span_texts(out))
    assert not survived, "a piece of the replaced value survives as its own text object"


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
    fragments = surviving_fragments("\n".join(after), replacement)
    assert not fragments, "part of the replaced value is still on the page"
    survived = surviving_value_spans(read_span_texts(out))
    assert not survived, "a piece of the value survives as its own object"


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
    named = raised.value.details["neighbour"]
    assert named == [float(v) for v in neighbour], "the refusal must name the line it protects"
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


WATERMARK_LINES = 10
WATERMARK_TARGET_LINE = 5
WATERMARK_XY = (72.0, 140.0)
WATERMARK_SIZE = 60.0


def write_large_object_under_the_text(path: Path, *, leading: float, watermark_first: bool) -> None:
    """A page-sized text object drawn under the lines, before or after them.

    Its bbox covers the centre of every line it crosses, which is all the old
    target test needed to mistake it for the object being replaced.
    """
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    for second in [0, 1] if watermark_first else [1, 0]:
        if second == 0:
            page.insert_text(WATERMARK_XY, "DRAFT", fontname="helv", fontsize=WATERMARK_SIZE)
        else:
            for index in range(WATERMARK_LINES):
                text = TARGET if index == WATERMARK_TARGET_LINE else f"ROW{index:02d}"
                page.insert_text((72, 72 + index * leading), text, fontname="helv", fontsize=11)
    doc.save(str(path))
    doc.close()


@pytest.mark.parametrize("leading", (14.0, 13.2), ids=["14pt-leading", "13.2pt-leading"])
@pytest.mark.parametrize(
    "watermark_first", (True, False), ids=["watermark-first", "watermark-last"]
)
def test_a_large_object_behind_the_text_does_not_decide_whether_the_page_converts(
    tmp_path: Path, leading: float, watermark_first: bool
) -> None:
    """The second signer's first Major: a watermark drawn FIRST made a page fail.

    The fitter used to take "the first span whose bbox contains the rect's centre".
    A 60 pt watermark drawn before the lines satisfies that everywhere it crosses
    them, so the watermark became the object being replaced: no trim reaches every
    glyph of a page-sized object, every trim was refused, and a refusal that reaches
    a neighbouring line raises. The same page with the watermark drawn LAST
    converted, which made span order the thing deciding a document's fate. The
    target is now the span whose bbox best matches the rect, so the object behind
    the text is a neighbour, and a neighbour the loop skips is not trimmed against.
    """
    src, out = tmp_path / "in.pdf", tmp_path / "out.pdf"
    write_large_object_under_the_text(src, leading=leading, watermark_first=watermark_first)

    PDFModifier(str(src), str(out)).process(ReplacementSpec(replacements={TARGET: REPLACEMENTS[0]}))

    lines = read_lines(out)
    dropped = [
        f"ROW{index:02d}"
        for index in range(WATERMARK_LINES)
        if index != WATERMARK_TARGET_LINE and f"ROW{index:02d}" not in lines
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


AILING_BLOCKS = (
    (12.0, 5.4),  # 0.45 em
    (12.0, 7.2),  # 0.60 em -- the leading CORE-006 exists for
    (12.0, 8.4),  # 0.70 em
    (12.0, 9.0),  # 0.75 em
    (9.0, 7.0),  # 0.78 em
    (12.0, 12.0),  # 1.00 em
    (9.0, 11.7),  # 1.30 em
)


def convert_or_refuse(src: Path, out: Path) -> str | None:
    """Convert, returning the refusal message, or None when a file was written."""
    try:
        PDFModifier(str(src), str(out)).process(
            ReplacementSpec(replacements={TARGET: REPLACEMENTS[0]})
        )
    except PDFModifierError as exc:
        assert not out.exists(), "a refused conversion must not leave a half-written document"
        return str(exc)
    assert out.exists(), "a conversion that did not refuse must have written its output"
    return None


@pytest.mark.parametrize(
    ("font", "leading"),
    AILING_BLOCKS,
    ids=[f"{font}pt-on{leading}pt" for font, leading in AILING_BLOCKS],
)
def test_no_leading_in_the_ailing_range_loses_characters_silently(
    tmp_path: Path, font: float, leading: float
) -> None:
    """CORE-006: at every leading either the neighbours survive, or the fit refuses.

    The fitter chooses its rectangle by predicting which one is safe, and the second
    signer's two Majors are both that prediction failing. What this row asserts is
    not that the prediction is right -- it is not, below about 0.72 em -- but that a
    wrong prediction cannot pass unnoticed: either every line that was not the target
    keeps its characters in the written file, or the conversion refuses.
    """
    src, out = tmp_path / "in.pdf", tmp_path / "out.pdf"
    write_tight_leading_block(src, font=font, leading=leading)
    before = read_lines(src)

    if convert_or_refuse(src, out) is not None:
        return  # loud, which is allowed: a refusal is the alternative to losing a line

    missing = missing_untouched_lines(before, read_lines(out), TARGET)
    assert not missing, (
        f"a block at {leading / font:.2f} em leading converted and lost {missing} with no "
        f"error and no warning: the defect CORE-006 exists to make impossible"
    )


def test_a_block_at_060_em_leading_is_refused_or_preserved(tmp_path: Path) -> None:
    """The row that opens core/modifier.py: 0.60 em, the reproduced silent loss.

    Measured on the base revision and again on CORE-001's head: at 12 pt on 7.2 pt
    leading the fitter takes a neighbour for the object being replaced, two lines
    lose their characters, and the conversion reports success. It is the one shape
    in this file where a wrong prediction is still silent.
    """
    src, out = tmp_path / "in.pdf", tmp_path / "out.pdf"
    write_tight_leading_block(src, font=12.0, leading=7.2)
    before = read_lines(src)

    if convert_or_refuse(src, out) is not None:
        return

    missing = missing_untouched_lines(before, read_lines(out), TARGET)
    assert not missing, f"lines lost with no error at 0.60 em leading: {missing}"


def test_a_planted_loss_is_caught_by_the_consequence_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The check must be shown to FIRE on a loss that is real but unintended.

    The fitter is made to hand back the raw, unfitted rectangle -- CORE-001's own
    original defect, and the shape `#179`'s receipt lost `ARC: 00` and `CVM: 5E0000`
    to. With the trim bypassed the redaction reaches the neighbouring lines, and the
    conversion must refuse rather than return a document with those lines gutted. A
    consequence check that has never been shown to fire is a green check that reads
    nothing.
    """
    monkeypatch.setattr(
        PDFModifier,
        "_fit_redaction_to_its_own_text_object",
        staticmethod(lambda page, rect, targets=None, spans=None: fitz.Rect(rect)),
    )
    src, out = tmp_path / "in.pdf", tmp_path / "out.pdf"
    write_payment_block(src, structure="mixed-style-line")

    with pytest.raises(PDFModifierError) as raised:
        PDFModifier(str(src), str(out)).process(
            ReplacementSpec(replacements={TARGET: REPLACEMENTS[0]})
        )

    message = str(raised.value)
    assert "another text object" in message, f"the refusal must name what it protected: {message}"
    assert not out.exists(), "a refused conversion must not leave a half-written document"


def test_the_accepted_co_located_loss_is_reported_as_a_warning(tmp_path: Path) -> None:
    """`#199`'s decision: the co-located loss is accepted, and therefore not silent.

    No rectangle separates two objects drawn in the same place, so the conversion
    must not refuse -- but `ModificationResult.warnings` already exists, so the
    caller can be told which object's characters went with the redaction.
    """
    src, out = tmp_path / "in.pdf", tmp_path / "out.pdf"
    write_shared_ink_line(src)

    result = PDFModifier(str(src), str(out)).process(
        ReplacementSpec(replacements={TARGET: REPLACEMENTS[0]})
    )

    assert result.success
    reported = any("page 1" in warning for warning in result.warnings)
    assert reported, f"the accepted co-located loss must be reported: {result.warnings}"
    assert read_lines(out), "the conversion still has to produce a document"


def write_a_tight_block_after_two_benign_pages(path: Path, *, font: float, leading: float) -> None:
    """The same hostile block, on the THIRD page.

    Every other row in this file is one page, so "the refusal names the page" was
    only ever proven for page 1: a check that named the first page by accident
    would pass all of them. The two pages before it carry text, so the loss this
    row is about is three pages into the document and is not the first thing the
    page loop touches.
    """
    doc = fitz.open()
    for index in range(2):
        page = doc.new_page(width=612, height=792)
        page.insert_text((72, 72), f"page {index + 1} header", fontname="cobo", fontsize=9)
        page.insert_text((72, 83), f"ARC: 00{index}", fontname="cobo", fontsize=9)
    page = doc.new_page(width=612, height=792)
    for index in range(TIGHT_LINES):
        text = TARGET if index == TIGHT_TARGET_LINE else f"keepkeep{index}"
        page.insert_text((72, 72 + index * leading), text, fontname="cobo", fontsize=font)
    doc.save(str(path))
    doc.close()


def test_the_refusal_names_the_page_that_holds_the_loss(tmp_path: Path) -> None:
    """The page in `details` and in the message is the one that lost the characters.

    A refusal the user can act on has to say WHERE: a document of forty pages that
    reports "page 1" is a refusal nobody can act on, and the check reads one page
    at a time, so the page it names is a value it can get wrong.
    """
    src, out = tmp_path / "in.pdf", tmp_path / "out.pdf"
    write_a_tight_block_after_two_benign_pages(src, font=12.0, leading=7.2)

    with pytest.raises(PDFModifierError) as raised:
        PDFModifier(str(src), str(out)).process(
            ReplacementSpec(replacements={TARGET: REPLACEMENTS[0]})
        )

    named = raised.value.details["page"]
    assert named == 3, f"the refusal named page {named}, and the loss is on page 3"
    assert "page 3" in str(raised.value), f"the message must say which page: {raised.value}"
    assert not out.exists(), "a refused conversion must not leave a half-written document"


# The three values the second signer's reproduction is built from: a target, the
# neighbour it drops on the next line at 0.6 em leading, and an unrelated value far
# to the right ON the neighbour's own line.
LOST_LINE_TARGET = "VALTHREE"
LOST_LINE_NEIGHBOUR = "KEEPKEEP"
LOST_LINE_BYSTANDER = "VALFOUR"


def write_a_line_lost_next_to_an_unrelated_bystander(path: Path) -> None:
    """A target whose neighbour below is on the same line as an unrelated value.

    Helvetica at 12 pt with 7.2 pt leading, which is 0.6 em: the neighbour's box
    overlaps the target's, so every rectangle that covers the target reaches the
    neighbour. The bystander shares the neighbour's LINE and none of its ink.
    """
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), LOST_LINE_TARGET, fontname="helv", fontsize=12)
    page.insert_text((72, 79.2), LOST_LINE_NEIGHBOUR, fontname="helv", fontsize=12)
    page.insert_text((250, 79.2), LOST_LINE_BYSTANDER, fontname="helv", fontsize=12)
    doc.save(str(path))
    doc.close()


def test_a_second_replacement_on_the_lost_line_does_not_excuse_the_loss(
    tmp_path: Path,
) -> None:
    """A loss is accepted only from the rectangle that TOOK it.

    The co-located exemption asked whether ANY target on the page shares the lost
    object's line, so an unrelated replacement elsewhere on that line turned a
    refusal into a warning -- one saying "its ink is drawn in the same place" about an
    object that shares ink with nothing. Reproduced by the second signer: replacing
    the target alone REFUSES, and adding a value drawn on the neighbour's line
    CONVERTS, loses the neighbour (the output is just `X`, `Y`) and reports it as
    accepted. Two replacements on one page is the normal case, not an edge case, so
    the verdict must not depend on the second one.
    """
    src, out = tmp_path / "in.pdf", tmp_path / "out.pdf"
    write_a_line_lost_next_to_an_unrelated_bystander(src)
    alone = {LOST_LINE_TARGET: "X"}
    with_bystander = {LOST_LINE_TARGET: "X", LOST_LINE_BYSTANDER: "Y"}

    with pytest.raises(PDFModifierError) as refused_alone:
        PDFModifier(str(src), str(out)).process(ReplacementSpec(replacements=alone))

    with pytest.raises(PDFModifierError) as refused_with_bystander:
        PDFModifier(str(src), str(out)).process(ReplacementSpec(replacements=with_bystander))

    assert "another text object" in str(refused_alone.value)
    assert "another text object" in str(refused_with_bystander.value), (
        "a replacement on the lost line must not excuse the loss, and this said: "
        f"{refused_with_bystander.value}"
    )
    assert not out.exists(), "a refused conversion must not leave a half-written document"


def _text_span(text: str, x: float, y: float) -> dict:
    """One rawdict-shaped span: a glyph per character, left to right, 6 pt wide."""
    chars = [
        {"c": character, "bbox": (x + index * 6.0, y - 8.0, x + index * 6.0 + 6.0, y)}
        for index, character in enumerate(text)
    ]
    return {"bbox": (x, y - 8.0, x + len(text) * 6.0, y), "chars": chars}


def test_a_vanished_space_is_not_a_lost_character() -> None:
    """The whitespace rule, and the document it was measured on.

    A redaction rewrites the line it touches, and while rewriting it PyMuPDF drops
    an adjacent whitespace-only span even though no rectangle reaches it: on
    `tests/data/sample.pdf` the space between `Visa` and `ending in 3777` goes that
    way, with a zero-width overlap against every rectangle on the page. Counting it
    refused a document that had converted, over a character that carries no text.
    """
    before = [_text_span("Visa", 72.0, 72.0), _text_span(" ", 90.4, 72.0)]
    after = [_text_span("Visa", 72.0, 72.0)]

    assert PDFModifier._lost_characters(before, after) == {}


def test_a_vanished_letter_is_a_lost_character() -> None:
    """The other direction: the whitespace rule must not swallow content.

    The character is removed from the span it was drawn in rather than the text
    being rebuilt from scratch -- a shorter string left-aligned moves every glyph
    after it, and the check would then read the whole tail as lost.
    """
    before = [_text_span("Visa", 72.0, 72.0)]
    after = [_text_span("Visa", 72.0, 72.0)]
    del after[0]["chars"][-1]

    lost = PDFModifier._lost_characters(before, after)

    assert ["".join(key[0] for key in keys) for keys in lost.values()] == ["a"]


def test_an_ordinary_replacement_reports_no_loss(tmp_path: Path) -> None:
    """The target's exemption is what keeps an ordinary page quiet.

    Removing it (`if False: continue`) leaves this whole file green, because the
    only warnings assertion in it is the positive one: a check that warned on every
    ordinary conversion would have shipped unnoticed, and the warning would be
    FALSE -- the target's own characters are the ones the replacement is allowed to
    remove. Asserting the empty list is the row that can fail.
    """
    src, out = tmp_path / "in.pdf", tmp_path / "out.pdf"
    write_payment_block(src, structure="mixed-style-line")

    result = PDFModifier(str(src), str(out)).process(
        ReplacementSpec(replacements={TARGET: REPLACEMENTS[0]})
    )

    assert result.success
    assert result.warnings == [], f"an ordinary conversion reported a loss: {result.warnings}"


def test_the_watermark_page_reports_the_same_loss_in_both_span_orders(tmp_path: Path) -> None:
    """Whatever this page loses, SPAN ORDER must not decide it.

    The page-sized object behind the text genuinely loses characters -- a 60 pt
    `DRAFT` crossing the lines has ink no rectangle can separate from the target's --
    and that loss is REPORTED, which is correct. What must not differ is the answer:
    identifying the target by "the first span containing the rect's centre" (the rule
    CORE-001 round 4 replaced) made the watermark-drawn-first page fail while the
    watermark-drawn-last one converted, and every core test stayed green while it
    did. Two orders, one result -- the assertion is equality, not emptiness, because
    an empty list would be a false expectation about this page.
    """
    reports: dict[bool, list[str]] = {}
    for watermark_first in (True, False):
        src = tmp_path / f"in-{watermark_first}.pdf"
        out = tmp_path / f"out-{watermark_first}.pdf"
        write_large_object_under_the_text(src, leading=13.2, watermark_first=watermark_first)

        result = PDFModifier(str(src), str(out)).process(
            ReplacementSpec(replacements={TARGET: REPLACEMENTS[0]})
        )

        assert result.success
        reports[watermark_first] = list(result.warnings)

    same = reports[True] == reports[False]
    assert same, f"span order changed what the page loses: {reports[True]} vs {reports[False]}"


def write_a_tight_block_whose_fields_are_all_replaced(
    path: Path, *, font: float = 12.0, leading: float = 9.0
) -> None:
    """Three adjacent fields of one tight block, ALL of them being replaced."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 40), "far above", fontname="cobo", fontsize=9)
    for index in range(3):
        page.insert_text(
            (72, 72 + index * leading), f"FIELD{index}", fontname="cobo", fontsize=font
        )
    page.insert_text((72, 120), "far below", fontname="cobo", fontsize=9)
    doc.save(str(path))
    doc.close()


def test_a_tight_block_whose_fields_are_all_replaced_still_converts(
    tmp_path: Path,
) -> None:
    """A neighbour that is itself a target is not a loss, and must not refuse.

    The second signature's Major at `a1b4ae8`: the trim guard raised when a refused
    trim left the rectangle reaching a neighbour on another line, without asking
    whether that neighbour was going to be replaced. Every field of this block is,
    so nothing is dropped -- the base commit converted this page and this branch
    REFUSED it, and the user had no workaround, because replacing one field at a
    time is refused too, by design (the row above pins that refusal).
    """
    src, out = tmp_path / "in.pdf", tmp_path / "out.pdf"
    write_a_tight_block_whose_fields_are_all_replaced(src)

    result = PDFModifier(str(src), str(out)).process(
        ReplacementSpec(replacements={f"FIELD{index}": f"NEWVALUE{index}" for index in range(3)})
    )

    assert result.success
    lines = read_lines(out)
    for index in range(3):
        assert f"NEWVALUE{index}" in lines, f"field {index} was not replaced: {lines}"
        assert f"FIELD{index}" not in lines, f"field {index} survived: {lines}"
    kept = "far above" in lines and "far below" in lines
    assert kept, f"a line that was not replaced was dropped: {lines}"
    assert result.warnings == [], f"nothing should have been reported lost: {result.warnings}"


def test_removal_needs_the_rectangle_to_reach_the_glyph_on_both_axes() -> None:
    """The height clause of the removal rule, which nothing pinned.

    Attribution asks whether a rectangle REMOVED a glyph, and the rule is a fraction
    of the box on BOTH axes -- the measurement bisected width and height
    separately. Replacing the height comparison with `True` left every unit test
    green, so a rectangle covering a glyph's full width by a hair of its height
    counted as "removed" and a loss could be excused by a rectangle that never
    touched it.
    """
    glyph = fitz.Rect(100.0, 100.0, 110.0, 120.0)
    full_width_sliver_of_height = fitz.Rect(100.0, 100.0, 110.0, 101.0)
    tall_enough = fitz.Rect(100.0, 100.0, 110.0, 102.0)

    assert not PDFModifier._removes_glyph(full_width_sliver_of_height, glyph)
    assert PDFModifier._removes_glyph(tall_enough, glyph)


def test_the_target_exemption_needs_targets_and_spans_from_one_parse(tmp_path: Path) -> None:
    """The identity pairing, which nothing asserted, in both directions.

    `targets` is keyed by `id(span)` and both parameters are independently optional,
    so a caller that passes a target set built from one parse while `spans` defaults
    to its own switches the exemption off silently. The direction is the safe one --
    the guard refuses again, as it did before the exemption existed, and no content is
    lost -- but "silently off" and "loudly off" are different bugs and only this row
    tells them apart. The geometry is the tight block whose fields are all replaced:
    with one parse it converts (the row above), with two it refuses.
    """
    src = tmp_path / "in.pdf"
    write_a_tight_block_whose_fields_are_all_replaced(src)
    document = fitz.open(str(src))
    page = document[0]
    middle = fitz.Rect(
        next(
            span["bbox"]
            for span in PDFModifier._text_spans(page)
            if "".join(char["c"] for char in span["chars"]) == "FIELD1"
        )
    )

    with pytest.raises(PDFModifierError) as raised:
        PDFModifier._fit_redaction_to_its_own_text_object(
            page, middle, {id(span) for span in PDFModifier._text_spans(page)}, spans=None
        )

    message = str(raised.value)
    assert "neighbouring line" in message, f"the guard must refuse here: {message}"

    spans = PDFModifier._text_spans(page)
    fitted = PDFModifier._fit_redaction_to_its_own_text_object(
        page, middle, {id(span) for span in spans}, spans
    )

    document.close()
    assert fitted is not None, "one parse must exempt the neighbouring field"


def test_a_partially_replaced_neighbour_span_keeps_its_prefix(tmp_path: Path) -> None:
    """A replacement can target a SUBSTRING of a span, and the prefix must survive.

    The exemptions are span-level (the neighbour in the trim guard, the lost span in
    the consequence check) while a match can be part of a span, so characters of a
    partially replaced neighbour that some other rectangle reached could be redacted,
    exempted by identity and never re-inserted. The reviewing round could not
    construct that in three attempts; this row pins the direction rather than leaving
    the gap to inference.
    """
    src, out = tmp_path / "in.pdf", tmp_path / "out.pdf"
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "PREFIXFORWARD", fontname="cobo", fontsize=12)
    page.insert_text((72, 81), "PREFIXBACKWARD", fontname="cobo", fontsize=12)
    doc.save(str(src))
    doc.close()

    PDFModifier(str(src), str(out)).process(
        ReplacementSpec(replacements={"FORWARD": "NEWVALUE", "BACKWARD": "NEWVALUE"})
    )

    document = fitz.open(str(out))
    text = document[0].get_text()
    document.close()
    assert text.count("PREFIX") == 2, f"a prefix was dropped: {text!r}"
    assert "FORWARD" not in text and "BACKWARD" not in text, f"a value survived: {text!r}"
    assert text.count("NEWVALUE") == 2, f"a value was not replaced: {text!r}"


# Leadings where the fitter is provably safe: nothing is lost and the conversion
# must happen (the sweep in `verification.md` records the same three).
SAFE_LEADINGS = ((12.0, 10.0), (12.0, 12.0), (9.0, 11.7))


def test_the_safe_leadings_still_convert(tmp_path: Path) -> None:
    """The other half of the refuse-or-preserve contract.

    Every ailing-range row RETURNS when the conversion refuses, which is what the
    contract allows and what a wrong prediction is supposed to cost. A regression
    that refused the WHOLE range would therefore pass every one of them and stop
    converting documents without failing anything -- a suite cannot notice that about
    itself, and a PR reviewer reading the rows did. These leadings are the ones the
    fitter is safe at, and each has to produce a file.
    """
    for font, leading in SAFE_LEADINGS:
        src = tmp_path / f"in-{leading}.pdf"
        out = tmp_path / f"out-{leading}.pdf"
        write_tight_leading_block(src, font=font, leading=leading)

        result = PDFModifier(str(src), str(out)).process(
            ReplacementSpec(replacements={TARGET: REPLACEMENTS[0]})
        )

        assert result.success, f"a safe leading ({leading / font:.2f} em) failed to convert"
        assert out.exists(), f"a safe leading ({leading / font:.2f} em) wrote no file"
        assert TARGET not in read_lines(out), "the target must be replaced, not preserved"


def test_the_target_is_chosen_by_overlap_not_by_being_the_first_to_intersect() -> None:
    """The IoU branch of `_target_span`, which every other row bypasses.

    Every fixture in this file builds a rectangle equal to a span's bbox, so the
    "identical bbox wins" early return always fires and the scoring branch never
    runs. The production path for replacing a word INSIDE a line has a rectangle
    smaller than its span, and that is where a wrong tie-break reintroduces the
    span-order defect: with the score replaced by "first intersecting span wins",
    a page-sized object drawn before the real span is chosen instead, and the whole
    suite still passes.
    """
    watermark = (0.0, 0.0, 600.0, 700.0)
    real = (100.0, 100.0, 110.0, 112.0)
    spans = PDFModifier._text_spans(cast("fitz.Page", _StubPage([watermark, real])))
    sub_rect = fitz.Rect(100.0, 100.0, 105.0, 112.0)

    chosen = PDFModifier._target_span(sub_rect, spans)

    assert chosen is spans[1], "the object the rectangle belongs to must win on overlap"


def test_a_loss_only_partly_explained_by_a_co_located_rectangle_is_refused() -> None:
    """`all`, not `any`, decides which vanished characters are excused.

    A loss is accepted only when EVERY vanished character was removed by a rectangle
    whose target shares the lost object's line; accepting the object because some of
    its characters were co-located "would readmit the defect through the middle of
    the span", as `_dispose_of_lost_characters` says. Mutating that `all` to `any`
    left every row green, so the invariant is pinned here, where it is decided.
    """
    shared = [(72.0, 72.0, 78.0, 82.0), (78.0, 72.0, 84.0, 82.0), (84.0, 72.0, 90.0, 82.0)]
    span = {
        "bbox": (72.0, 72.0, 90.0, 82.0),
        "chars": [
            {"c": "a", "bbox": shared[0]},
            {"c": "b", "bbox": shared[1]},
            {"c": "c", "bbox": shared[2]},
        ],
    }
    co_located_target = {"bbox": (72.0, 72.0, 84.0, 82.0)}
    other_line_target = {"bbox": (84.0, 92.0, 90.0, 102.0)}
    redactions = [
        (fitz.Rect(72.0, 72.0, 80.0, 82.0), co_located_target),
        (fitz.Rect(84.0, 72.0, 90.0, 82.0), other_line_target),
    ]
    lost = [("a", 72.0, 72.0), ("b", 78.0, 72.0), ("c", 84.0, 72.0)]
    modifier = PDFModifier.__new__(PDFModifier)

    with pytest.raises(PDFModifierError) as raised:
        modifier._dispose_of_lost_characters(
            cast("fitz.Page", _StubPage([(0.0, 0.0, 1.0, 1.0)])), span, redactions, lost
        )

    assert "another text object" in str(raised.value)
