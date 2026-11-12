---
id: "lesson-016-pymupdf-preserves-metadata-on-save-make-it-explicit"
type: lesson
status: active
title: "PyMuPDF preserves metadata on `save()` — make preservation an explicit option, not an assumption"
created: "2026-09-22"
owner: manu
tags: [pdf-modifier-mcp, lesson, pymupdf, metadata, pdf]
---

# PyMuPDF preserves metadata on `save()` — make preservation an explicit option, not an assumption

**Context:** Text replacement in `core/modifier.py` (redact + reinsert + save). Spec PDF-001-preserve-metadata (feature merged via #138, spec landed retroactively via #159) required that a "faithful replica" keep `creationDate`/`modDate`/`producer` identical, while an opt-out stamps a fresh `modDate`.
**Problem:** Preservation was an emergent behavior of PyMuPDF's `save()`, not a contract: any change of save flags, garbage collection, or incremental write could silently rewrite the Info dictionary. Empirically verified during the spec: a plain `save()` already preserves metadata — so the risk was a future regression, not an observed loss.
**Solution:** Capture `doc.metadata` on open excluding PyMuPDF-internal keys (`format`, `encryption` — feeding them to `set_metadata` is invalid), keep only writable string fields, and restore explicitly before save when `preserve_metadata=True` (default). The opt-out stamps only `modDate` via `fitz.get_pdf_now()` and never touches `creationDate`. Deterministic > incidental.
**Tags:** `#pymupdf` `#metadata` `#pdf` `#determinism`
