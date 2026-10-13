"""Measure how often the redaction fitter refuses, across the whole test suite.

The fitter refuses a fit it cannot make safely, and a refusal fails the whole
document. The claim "that costs nothing in practice" is a measurement, so this
script takes it instead of asserting it:

    cd backend && PYTHONPATH=scripts uv run pytest tests/ -q --no-cov \\
        -p probe_fitter_reachability

It prints one `PROBE {...}` line on exit: how many fits ran, how many refused
because the target could not be identified, and how many collapsed. Both
refusals should come from the guard's own synthetic rows -- a real document that
reaches one is a fixture worth having, and a refusal rate that climbs past the
synthetic rows means the fitter became stricter than the corpus.
"""

import atexit
from typing import Any
from unittest import mock

from pdf_modifier.core import modifier

_ORIGINAL_FIT = modifier.PDFModifier._fit_redaction_to_its_own_text_object
_ORIGINAL_GLYPHS = modifier.PDFModifier._glyph_boxes
_STATS: dict[str, int] = {"fits": 0, "unidentified": 0, "collapsed": 0, "identified_misses": 0}


def _fit(page: Any, rect: Any) -> Any:
    _STATS["fits"] += 1
    try:
        return _ORIGINAL_FIT(page, rect)
    except modifier.PDFModifierError as exc:
        if "collapsed" in str(exc):
            _STATS["collapsed"] += 1
        elif "cannot be identified" in str(exc):
            _STATS["unidentified"] += 1
        raise


def _glyph_boxes(target: Any) -> Any:
    glyphs = _ORIGINAL_GLYPHS(target)
    if not glyphs:
        _STATS["identified_misses"] += 1
    return glyphs


_PATCHERS: list[Any] = [
    mock.patch.object(
        modifier.PDFModifier, "_fit_redaction_to_its_own_text_object", staticmethod(_fit)
    ),
    mock.patch.object(modifier.PDFModifier, "_glyph_boxes", staticmethod(_glyph_boxes)),
]
for _patcher in _PATCHERS:
    _patcher.start()
    atexit.register(_patcher.stop)

atexit.register(lambda: print(f"PROBE {_STATS}", flush=True))
