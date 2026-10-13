"""
PDF Modifier - A dual-interface PDF modification tool.

Provides both CLI (pdf-mod) and MCP server interfaces for PDF manipulation.
"""

from __future__ import annotations

from importlib.metadata import version

from .core import (
    PDFAnalyzer,
    PDFModifier,
    PDFModifierError,
    ReplacementSpec,
)

__version__ = version("pdf-modifier")

__all__ = [
    "PDFAnalyzer",
    "PDFModifier",
    "PDFModifierError",
    "ReplacementSpec",
    "__version__",
]
