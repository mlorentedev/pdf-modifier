---
id: "lesson-014-redact-fill-white-overwrites-pdf-background"
type: lesson
status: active
title: "`add_redact_annot(fill=(1,1,1))` overwrites a vector-drawn PDF background with white"
created: "2026-09-07"
owner: manu
tags: [pdf-modifier-mcp, lesson, pymupdf, redact, background, fonts]
---

# `add_redact_annot(fill=(1,1,1))` overwrites a vector-drawn PDF background with white

**Context:** Replacing text in a PDF via PyMuPDF redaction + reinsert (the `core/modifier.py` path). Target file was a booking confirmation whose invoice body sits on a light gray-blue vector rectangle `fill=(0.949, 0.957, 0.965)`.
**Problem:** Every replaced field rendered as a **white box**. Root cause: `page.add_redact_annot(bbox, fill=(1,1,1))` paints solid white over the redaction rectangle. `apply_redactions()` removes the *text* glyphs but does **not** remove vector drawings, so the background band was still there — then the white `fill` covered it. Verified by sampling pixels: `fill=(1,1,1)` → `(255,255,255)`; `fill=None` → `(241,244,245)` (the original band color).
**Solution:** Use `fill=None` (or omit it — it is the default). The text is still erased; the underlying vector drawing stays visible. Also fixed a second fidelity bug in the same pass: embedded `LiberationSans`/`LiberationSans-Bold`/`LiberationSerif-Italic` were falling through `FontResolver` to a plain Helvetica code, **losing bold/italic**. Added explicit `Liberation*` patterns (specific before generic) to map `LiberationSans-Bold`→`HeBo`, `LiberationSerif-Italic`→`TiI`, etc.
**Tags:** `#pymupdf` `#redact` `#background` `#fonts` `#pdf`
