"""PDF text replacement engine with style preservation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

import fitz

from ..logger import setup_logging
from .exceptions import (
    FileSizeExceededError,
    PDFModifierError,
    PDFNotFoundError,
    PDFPasswordError,
    PDFReadError,
)
from .font_resolver import FontResolver
from .models import BatchResult, ModificationResult, ReplacementSpec

logger = setup_logging(__name__)

DEFAULT_MAX_FILE_SIZE_BYTES: int = 100 * 1024 * 1024  # 100 MB


class PDFModifier:
    """
    PDF text replacement engine with style preservation.

    Supports:
    - Exact text matching
    - Regex pattern matching
    - Hyperlink creation (text|URL syntax)
    - Font style preservation (Base 14 fonts)

    Example:
        >>> spec = ReplacementSpec(replacements={"old": "new"})
        >>> modifier = PDFModifier("input.pdf", "output.pdf")
        >>> result = modifier.process(spec)
        >>> print(result.replacements_made)

        # Or with context manager:
        >>> with PDFModifier("input.pdf", "output.pdf") as modifier:
        ...     result = modifier.process(spec)
    """

    def __init__(
        self,
        input_path: str | Path,
        output_path: str | Path,
        password: str | None = None,
        max_file_size: int = DEFAULT_MAX_FILE_SIZE_BYTES,
        custom_fonts: dict[str, str] | None = None,
    ) -> None:
        """Validate paths and prepare the modifier without opening the document.

        The document is opened lazily by :meth:`__enter__` (or ``_open_doc``)
        so construction is cheap and input errors surface at use time.

        Args:
            input_path: Path to the source PDF.
            output_path: Path where the modified PDF is written.
            password: Optional password for encrypted PDFs.
            max_file_size: Upload/processing size limit in bytes.
            custom_fonts: Optional map of alias -> TTF/OTF file path.

        Raises:
            ValueError: If input and output paths are equal, or a custom
                font alias points to a missing or non-font file.
        """
        self.input_path = Path(input_path).absolute()
        self.output_path = Path(output_path).absolute()
        self.password = password
        self.max_file_size = max_file_size
        self._custom_fonts = self._validate_custom_fonts(custom_fonts or {})
        self._font_resolver = FontResolver()

        if self.input_path == self.output_path:
            raise ValueError("Input and output paths cannot be the same. Risk of file corruption.")

        self._doc: fitz.Document | None = None
        self._warnings: list[str] = []

    @staticmethod
    def _parse_flags(raw_flags: int | dict[str, int] | None) -> dict[str, int] | None:
        """Convert PyMuPDF int flags to dict, or pass through if already dict."""
        if raw_flags is None:
            return None
        if isinstance(raw_flags, dict):
            return raw_flags
        # PyMuPDF int flags bitmask:
        # TEXT_FONT_BOLD=1, TEXT_FONT_ITALIC=2, TEXT_FONT_SERIFED=4,
        # TEXT_FONT_MONOSPACED=8, TEXT_FONT_SUPERSCRIPT=16
        flags: dict[str, int] = {}
        if raw_flags & 1:
            flags["bold"] = 1
        if raw_flags & 2:
            flags["italic"] = 1
        if raw_flags & 4:
            flags["serif"] = 1
        if raw_flags & 8:
            flags["mono"] = 1
        return flags

    @staticmethod
    def _validate_custom_fonts(custom_fonts: dict[str, str]) -> dict[str, str]:
        """Validate that all custom font files exist and are valid TTF/OTF."""
        for _alias, path in custom_fonts.items():
            p = Path(path)
            if not p.is_file():
                raise ValueError(f"font file does not exist: {path}")
            if p.suffix.lower() not in (".ttf", ".otf"):
                raise ValueError(f"font file must be .ttf or .otf: {path}")
        return custom_fonts

    def _open_doc(self) -> fitz.Document:
        """Safely open the document with password authentication if required."""
        if not self.input_path.exists():
            raise PDFNotFoundError(
                f"PDF file not found: {self.input_path}",
                {"path": str(self.input_path)},
            )

        file_size = self.input_path.stat().st_size
        if file_size > self.max_file_size:
            size_mb = file_size / (1024 * 1024)
            limit_mb = self.max_file_size / (1024 * 1024)
            raise FileSizeExceededError(
                f"PDF file is {size_mb:.1f} MB, exceeds limit of {limit_mb:.0f} MB",
                {
                    "path": str(self.input_path),
                    "size_bytes": file_size,
                    "limit_bytes": self.max_file_size,
                },
            )

        try:
            doc = fitz.open(self.input_path)
            if doc.needs_pass:
                if not self.password:
                    raise PDFPasswordError("PDF is password protected. Please provide a password.")
                if not doc.authenticate(self.password):
                    raise PDFPasswordError("Incorrect password provided for the PDF.")
            return doc
        except PDFPasswordError:
            raise
        except Exception as e:
            raise PDFReadError(f"Cannot open PDF: {e}", {"path": str(self.input_path)}) from e

    def __enter__(self) -> PDFModifier:
        """Open the document and return the modifier for ``with`` usage."""
        self._doc = self._open_doc()
        return self

    def __exit__(self, *args: Any) -> None:
        """Close the document when leaving the ``with`` block."""
        self.close()

    def close(self) -> None:
        """Explicitly close the document."""
        if self._doc:
            self._doc.close()
            self._doc = None

    @staticmethod
    def _text_spans(page: fitz.Page) -> list[dict[str, Any]]:
        """Every text span on the page, with its per-character boxes.

        `rawdict` rather than `dict`: the character boxes are what make "does this
        trim still reach the target's glyphs?" a question about the document
        instead of a guess made from two bounding boxes. Two rounds of review
        were needed to learn that the guess is not good enough (see the fitter).
        """
        blocks = page.get_text("rawdict")["blocks"]
        return [
            span for block in blocks for line in block.get("lines", []) for span in line["spans"]
        ]

    @staticmethod
    def _glyph_boxes(span: dict[str, Any] | None) -> list[fitz.Rect]:
        """The box of every character in one span, or nothing when there is no span."""
        if span is None:
            return []
        return [fitz.Rect(char["bbox"]) for char in span.get("chars", [])]

    @staticmethod
    def _trim_away_from(trimmed: fitz.Rect, other: fitz.Rect, centre: fitz.Point) -> fitz.Rect:
        """What ONE neighbour asks of the rect: the edge facing it, moved past it.

        A neighbour sharing the rect's vertical band is BESIDE the target, so only
        x separates them; one in another band is above or below, so only y does.
        Trimming the wrong axis collapses the rect onto itself -- the first fix
        round trimmed y unconditionally, a same-line neighbour dragged `y1` onto
        the target's own `y0`, and the guard handed the raw rect back.
        """
        candidate = fitz.Rect(trimmed)
        if other.y0 <= centre.y <= other.y1:
            if other.x1 <= centre.x:
                candidate.x0 = max(candidate.x0, other.x1 + 0.01)
            else:
                candidate.x1 = min(candidate.x1, other.x0 - 0.01)
        elif other.y1 <= centre.y:
            candidate.y0 = max(candidate.y0, other.y1 + 0.01)
        else:
            candidate.y1 = min(candidate.y1, other.y0 - 0.01)
        return candidate

    @staticmethod
    def _is_safe_trim(candidate: fitz.Rect, glyphs: list[fitz.Rect]) -> bool:
        """Whether one candidate trim may replace the rect being fitted.

        Two questions, and they answer differently. An EMPTY candidate is a fitting
        FAILURE: it is kept so the guard at the end of the fit reports it, instead
        of this loop swallowing it and handing back a rect that no longer avoids
        the neighbours. A candidate that would leave a character of the object
        behind is REFUSED: `apply_redactions` removes a character only if the rect
        reaches it, so accepting one would leave part of the replaced text on the
        page under its replacement -- round 2's Major finding, where the neighbour
        OVERLAPPED the target's glyph run and the x-trim cut inside it. Such a
        neighbour is not one to trim against: it is the same ink, so the rect has
        to cover both.
        """
        if candidate.get_area() <= 0:
            return True
        return all(candidate.intersects(glyph) for glyph in glyphs)

    @staticmethod
    def _fit_redaction_to_its_own_text_object(page: fitz.Page, rect: fitz.Rect) -> fitz.Rect:
        """Shrink a redaction rect so it cannot reach the neighbouring text objects.

        `apply_redactions` removes every glyph that INTERSECTS the rect, not only
        the glyphs inside it. Consecutive line boxes in a tight block overlap:
        11 pt of leading against 12.6 pt of line height leaves 1.6 pt of overlap, so
        a rect fitted to the target's own box also reaches the lines above and
        below and takes them with it. Only the replacement is re-inserted, so they
        are lost silently -- a receipt in `#179` lost `ARC` and `CVM` this way.

        The object being replaced is the one that CONTAINS the rect's centre; a
        neighbour can only overlap its edge. Two invariants make a trim safe, and
        each one is a review finding this helper shipped without:

        * **The axis follows the neighbour** -- x when it is beside the target,
          y when it is above or below. Round 1 trimmed y unconditionally, so a
          same-line neighbour collapsed the rect and the guard returned the raw
          one.
        * **The trim may not lose a glyph of the target** -- the candidate is
          kept only if it still reaches every character of the object being
          replaced. Round 2's neighbour *overlapped* the target's glyph run; the
          x-trim then cut inside it, the first characters of the replaced value
          survived underneath the replacement, and nothing failed.

        A neighbour that fails the second invariant is not a neighbour to trim
        against: it shares the target's own ink, so the rect has to cover both and
        the untrimmed rectangle is kept.
        """
        centre = fitz.Point((rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2)
        spans = PDFModifier._text_spans(page)
        target = next((span for span in spans if fitz.Rect(span["bbox"]).contains(centre)), None)
        glyphs = PDFModifier._glyph_boxes(target)

        trimmed = fitz.Rect(rect)
        for span in spans:
            other = fitz.Rect(span["bbox"])
            if other.contains(centre) or not other.intersects(trimmed):
                continue
            candidate = PDFModifier._trim_away_from(trimmed, other, centre)
            if PDFModifier._is_safe_trim(candidate, glyphs):
                trimmed = candidate

        if trimmed.get_area() <= 0:
            PDFModifier._refuse_collapsed_fit(page, rect, trimmed)
        return trimmed

    @staticmethod
    def _refuse_collapsed_fit(page: fitz.Page, rect: fitz.Rect, trimmed: fitz.Rect) -> None:
        """Refuse a fit whose rect has no area, naming the page and both rectangles.

        A collapsed rect is a fitting FAILURE, not a small rect: measured, a 0.02 pt
        rect removes no glyph at all, so passing one to the redactor would leave the
        original text under the replacement; passing the RAW rect re-imports the
        content loss. Neither is acceptable in silence, and this is where the fit
        says so instead of returning something unusable.
        """
        raise PDFModifierError(
            f"Cannot fit the redaction rectangle to the replaced text object on "
            f"page {page.number + 1}: {tuple(round(v, 3) for v in rect)} collapsed to "
            f"{tuple(round(v, 3) for v in trimmed)} while avoiding its neighbours.",
            {
                "page": page.number + 1,
                "rect": [float(v) for v in rect],
                "trimmed": [float(v) for v in trimmed],
            },
        )

    def _apply_replacements_to_page(
        self,
        page: fitz.Page,
        items: list[dict[str, Any]],
    ) -> int:
        """Apply replacements to a single page. Returns count of replacements."""
        for item in items:
            # fill=None (not white): removing the text glyphs must not paint a
            # box over the underlying PDF content (e.g. a colored invoice band),
            # otherwise the replaced field shows a white rectangle instead of
            # preserving the page background.
            rects = item["bboxes"] if "bboxes" in item else [item["bbox"]]
            for rect in rects:
                page.add_redact_annot(
                    self._fit_redaction_to_its_own_text_object(page, fitz.Rect(rect)),
                    fill=None,
                )

        # Remove the redacted *text* but preserve the surrounding content.
        # fill=None avoids painting a foreign color (the old white fill hid the
        # underlying vector band), and PDF_REDACT_IMAGE_NONE stops the default
        # image masking from carving a hole where text sat on an image.
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

        for item in items:
            self._insert_replacement(page, item)

        return len(items)

    def _process_pages(
        self,
        spec: ReplacementSpec,
        pages: tuple[int, int] | None = None,
    ) -> tuple[int, set[int]]:
        """Process pages and return (total_replacements, pages_modified).

        Args:
            spec: Replacement specification.
            pages: Optional (start, end) 1-indexed inclusive range.
                   None processes all pages.

        Raises:
            ValueError: If page range is invalid or out of bounds.
        """
        doc = self._doc
        assert doc is not None, "Document must be opened before processing"
        total_pages = len(doc)

        if pages is not None:
            if not pages:
                raise ValueError("Page range must have at least one page")
            if len(pages) != 2:
                raise ValueError("Page range must be a (start, end) tuple")
            start, end = pages
            if start < 1 or end < 1:
                raise ValueError("Page numbers must be 1-indexed")
            if start > end:
                raise ValueError("Page range start must not exceed end")
            if end > total_pages:
                raise ValueError(f"Page {end} exceeds document total of {total_pages} pages")
            page_indices = range(start - 1, end)
        else:
            page_indices = range(total_pages)

        total = 0
        pages_modified: set[int] = set()

        for page_num in page_indices:
            page = doc[page_num]
            items = self._collect_replacements(page, spec)
            if not items:
                continue
            pages_modified.add(page_num)
            total += self._apply_replacements_to_page(page, items)

        return total, pages_modified

    def _save_and_log(self) -> None:
        """Save the modified document and log the result."""
        # garbage=4 removes unused objects, dedups, and merges streams so a simple
        # text replacement does not bloat the file — the default save grew a 67 kB
        # PDF to ~94 kB, while garbage collection keeps it at the original size.
        self._doc.save(  # type: ignore[union-attr]
            str(self.output_path), garbage=4, deflate=True
        )
        logger.info("Saved %s", self.output_path)

    def process(
        self,
        spec: ReplacementSpec,
        pages: tuple[int, int] | None = None,
    ) -> ModificationResult:
        """
        Execute all replacements and return structured result.

        Batches redactions per page for efficiency.

        Args:
            spec: ReplacementSpec containing replacements and options.
            pages: Optional (start, end) 1-indexed inclusive page range.
                   None processes all pages.

        Returns:
            ModificationResult with success status and statistics.

        Raises:
            PDFReadError: If the PDF cannot be opened.
            ValueError: If page range is invalid.
        """
        doc_opened_here = False
        if not self._doc:
            self._doc = self._open_doc()
            doc_opened_here = True

        try:
            total, pages_modified = self._process_pages(spec, pages)
            self._save_and_log()
        except ValueError:
            raise
        except PDFModifierError:
            raise
        except Exception as e:
            raise PDFReadError(f"Failed to process PDF pages: {e}") from e
        finally:
            if doc_opened_here:
                self.close()

        return ModificationResult(
            success=True,
            input_path=str(self.input_path),
            output_path=str(self.output_path),
            replacements_made=total,
            pages_modified=len(pages_modified),
            warnings=self._warnings,
        )

    def _convert_color(
        self, color_input: int | list[float] | tuple[float, ...]
    ) -> tuple[float, float, float]:
        """Convert PyMuPDF color to RGB float tuple (0.0-1.0)."""
        if isinstance(color_input, int):
            r = ((color_input >> 16) & 0xFF) / 255.0
            g = ((color_input >> 8) & 0xFF) / 255.0
            b = (color_input & 0xFF) / 255.0
            return (r, g, b)
        elif isinstance(color_input, list | tuple) and len(color_input) >= 3:
            return tuple(c if c <= 1.0 else c / 255.0 for c in color_input[:3])  # type: ignore[return-value]
        return (0.0, 0.0, 0.0)

    def _resolve_replacement(
        self,
        replacement_raw: str,
        matched_text: str,
        target: str,
        spec: ReplacementSpec,
    ) -> tuple[str, str | None]:
        """Parse replacement text and URL from raw replacement string."""
        replacement_text = replacement_raw
        url: str | None = None

        if "|" in replacement_raw:
            candidate_text, candidate_url = replacement_raw.rsplit("|", 1)
            candidate_url = candidate_url.strip()
            if candidate_url == "void(0)" or candidate_url.startswith(
                ("http://", "https://", "mailto:", "javascript:")
            ):
                replacement_text = candidate_text
                url = "javascript:void(0)" if candidate_url == "void(0)" else candidate_url

        if spec.use_regex and spec.compiled_patterns:
            pattern = spec.compiled_patterns[target]
            new_text = pattern.sub(replacement_text, matched_text)
        else:
            new_text = matched_text.replace(target, replacement_text)

        return new_text, url

    def _match_single_span(
        self,
        span: dict[str, Any],
        spec: ReplacementSpec,
    ) -> dict[str, Any] | None:
        """Check if a single span matches any replacement target."""
        text = span["text"].strip()
        original = span["text"]

        for target, replacement_raw in spec.replacements.items():
            match_found = False
            if spec.use_regex and spec.compiled_patterns:
                pattern = spec.compiled_patterns[target]
                if pattern.fullmatch(text) if spec.whole_span else pattern.search(text):
                    match_found = True
            elif (text == target) if spec.whole_span else (target in text):
                match_found = True

            if match_found:
                new_text, url = self._resolve_replacement(replacement_raw, original, target, spec)
                # Convert int flags to dict if needed
                raw_flags = span.get("flags")
                font_flags = self._parse_flags(raw_flags)
                font_props = self._font_resolver.resolve(
                    span["font"],
                    font_flags=font_flags,
                    custom_fonts=self._custom_fonts,
                )
                return {
                    "bbox": span["bbox"],
                    "origin": span["origin"],
                    "text": new_text,
                    "url": url,
                    "fontname": font_props.fontname,
                    "fontfile": font_props.fontfile,
                    "size": span["size"],
                    "color": span["color"],
                }
        return None

    def _collect_replacements(
        self,
        page: fitz.Page,
        spec: ReplacementSpec,
    ) -> list[dict[str, Any]]:
        """Scan page and collect items to replace.

        Two-pass approach:
        1. Single-span matching (fast path for most cases).
        2. Cross-span matching per line.
        """
        items: list[dict[str, Any]] = []
        matched_span_ids: set[int] = set()
        blocks = page.get_text("dict")["blocks"]

        # Pass 1: single-span matching
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    item = self._match_single_span(span, spec)
                    if item:
                        items.append(item)
                        matched_span_ids.add(id(span))
                        break

        # Pass 2: cross-span matching
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                if len(line["spans"]) < 2:
                    continue
                items.extend(self._match_across_spans(line["spans"], spec, matched_span_ids))

        return items

    def _build_merged_text(
        self,
        spans: list[dict[str, Any]],
    ) -> tuple[str, list[tuple[int, int]]]:
        """Build concatenated text and offset map from spans."""
        merged = ""
        span_ranges: list[tuple[int, int]] = []
        for span in spans:
            start = len(merged)
            merged += span["text"]
            span_ranges.append((start, len(merged)))
        return merged, span_ranges

    def _find_matches_in_merged(
        self,
        merged: str,
        target: str,
        spec: ReplacementSpec,
    ) -> list[tuple[int, int]]:
        """Find all match positions in merged text."""
        matches: list[tuple[int, int]] = []
        if spec.whole_span:
            # Exact-match mode: the merged line text must be the target itself
            # (equality for literals, fullmatch for regex), not a container of it.
            stripped = merged.strip()
            if not stripped:
                return matches
            offset = len(merged) - len(merged.lstrip())
            if spec.use_regex and spec.compiled_patterns:
                m = spec.compiled_patterns[target].fullmatch(stripped)
                if m:
                    matches.append((offset + m.start(), offset + m.end()))
            elif stripped == target:
                idx = merged.find(target)
                matches.append((idx, idx + len(target)))
            return matches
        if spec.use_regex and spec.compiled_patterns:
            pattern = spec.compiled_patterns[target]
            for m in pattern.finditer(merged):
                matches.append((m.start(), m.end()))
        else:
            start = 0
            while True:
                idx = merged.find(target, start)
                if idx == -1:
                    break
                matches.append((idx, idx + len(target)))
                start = idx + 1
        return matches

    def _build_cross_span_item(
        self,
        spans: list[dict[str, Any]],
        involved: list[int],
        merged: str,
        m_start: int,
        m_end: int,
        replacement_raw: str,
        target: str,
        spec: ReplacementSpec,
    ) -> dict[str, Any]:
        """Build a replacement item for a cross-span match."""
        first_span = spans[involved[0]]
        bboxes = [tuple(spans[i]["bbox"]) for i in involved]
        x0 = min(b[0] for b in bboxes)
        y0 = min(b[1] for b in bboxes)
        x1 = max(b[2] for b in bboxes)
        y1 = max(b[3] for b in bboxes)

        matched_text = merged[m_start:m_end]
        new_text, url = self._resolve_replacement(replacement_raw, matched_text, target, spec)
        raw_flags = first_span.get("flags")
        font_flags = self._parse_flags(raw_flags)
        font_props = self._font_resolver.resolve(
            first_span["font"],
            font_flags=font_flags,
            custom_fonts=self._custom_fonts,
        )

        return {
            "bbox": (x0, y0, x1, y1),
            "bboxes": bboxes,
            "origin": first_span["origin"],
            "text": new_text,
            "url": url,
            "fontname": font_props.fontname,
            "fontfile": font_props.fontfile,
            "size": first_span["size"],
            "color": first_span["color"],
        }

    def _match_across_spans(
        self,
        spans: list[dict[str, Any]],
        spec: ReplacementSpec,
        matched_span_ids: set[int],
    ) -> list[dict[str, Any]]:
        """Match replacement targets across concatenated span texts."""
        items: list[dict[str, Any]] = []

        merged, span_ranges = self._build_merged_text(spans)
        if not merged.strip():
            return items

        for target, replacement_raw in spec.replacements.items():
            matches = self._find_matches_in_merged(merged, target, spec)

            for m_start, m_end in matches:
                involved = [
                    i
                    for i, (s_start, s_end) in enumerate(span_ranges)
                    if s_start < m_end and s_end > m_start
                ]

                if len(involved) < 2:
                    continue
                if any(id(spans[i]) in matched_span_ids for i in involved):
                    continue

                item = self._build_cross_span_item(
                    spans,
                    involved,
                    merged,
                    m_start,
                    m_end,
                    replacement_raw,
                    target,
                    spec,
                )
                items.append(item)

                for i in involved:
                    matched_span_ids.add(id(spans[i]))

        return items

    def _insert_link(
        self,
        page: fitz.Page,
        item: dict[str, Any],
        link_url: str,
    ) -> None:
        """Insert a hyperlink for the replacement text."""
        try:
            fontname = item["fontname"]
            fontfile = item.get("fontfile")
            if fontfile:
                fontname = f"__custom_{Path(fontfile).stem}__"
            font = fitz.Font(fontname=fontname, fontfile=fontfile)
            text_width = font.text_length(item["text"], fontsize=item["size"])
            x0 = item["origin"][0]
            y_baseline = item["origin"][1]
            link_rect = fitz.Rect(
                x0,
                y_baseline - item["size"],
                x0 + text_width,
                y_baseline + (item["size"] * 0.25),
            )
            page.insert_link({"kind": fitz.LINK_URI, "from": link_rect, "uri": link_url})
        except Exception as e:
            msg = f"Could not add link for '{item['text']}': {e}"
            logger.warning(msg)
            self._warnings.append(msg)

    def _insert_replacement(self, page: fitz.Page, item: dict[str, Any]) -> None:
        """Insert replacement text with original styling."""
        color = self._convert_color(item["color"])
        fontname = item["fontname"]
        fontfile = item.get("fontfile")

        # PyMuPDF ignores fontfile when fontname is a Base 14 font.
        # When a custom fontfile is provided, use a non-Base14 fontname
        # so PyMuPDF treats it as a custom embedded font.
        if fontfile:
            fontname = f"__custom_{Path(fontfile).stem}__"

        page.insert_text(
            item["origin"],
            item["text"],
            fontname=fontname,
            fontsize=item["size"],
            color=color,
            fontfile=fontfile,
        )

        link_url = item["url"]
        if not link_url and item["text"].strip().startswith(("http://", "https://")):
            link_url = item["text"].strip()
        if link_url:
            self._insert_link(page, item, link_url)


def batch_process(
    file_paths: Sequence[str | Path],
    output_dir: str | Path,
    spec: ReplacementSpec,
    password: str | None = None,
    max_file_size: int = DEFAULT_MAX_FILE_SIZE_BYTES,
    custom_fonts: dict[str, str] | None = None,
) -> BatchResult:
    """
    Apply the same replacements to multiple PDF files.

    Each file is processed independently; failures in one file do not
    affect the rest of the batch. Output files are written to
    ``output_dir`` using the same filename as the input.

    Args:
        file_paths: List of input PDF file paths.
        output_dir: Directory where modified PDFs will be saved.
        spec: ReplacementSpec containing replacements and options.
        password: Optional password for encrypted PDFs.
        custom_fonts: Optional map of alias -> font file path.

    Returns:
        BatchResult with per-file results and aggregate statistics.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[ModificationResult] = []
    errors: list[dict[str, str]] = []

    for file_path in file_paths:
        file_path = Path(file_path)
        output_path = output_dir / file_path.name

        if file_path.absolute() == output_path.absolute():
            errors.append({"file": str(file_path), "error": "Input and output paths are the same"})
            continue

        try:
            modifier = PDFModifier(
                str(file_path),
                str(output_path),
                password=password,
                max_file_size=max_file_size,
                custom_fonts=custom_fonts,
            )
            result = modifier.process(spec)
            results.append(result)
        except Exception as e:
            logger.warning("Batch: failed to process %s: %s", file_path, e)
            error_code = getattr(e, "code", "UNKNOWN")
            errors.append({"file": str(file_path), "error": f"[{error_code}] {e}"})

    return BatchResult(
        total_files=len(file_paths),
        successful=len(results),
        failed=len(errors),
        results=results,
        errors=errors,
    )
