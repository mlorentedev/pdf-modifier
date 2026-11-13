---
id: "lesson-009-pdf-js-v6-render-api-grouping-real-world-pdf-"
type: lesson
status: active
title: "pdf.js v6 render API + grouping real-world PDF spans"
created: "2026-08-06"
owner: manu
tags: [pdf-modifier-mcp, lesson, frontend, pdfjs, svelte5, grouping, type3, canvas]
---

# pdf.js v6 render API + grouping real-world PDF spans

**Context:** WEB-002 — PDF preview element grouping, click-to-locate, precise highlight (Svelte + pdf.js).
**Problem:**
1. **pdf.js v6 `render()`** — `page.render({ canvasContext, viewport })` fails type-check; v6 requires `{ canvas, viewport }` (canvas is the primary param, canvasContext is a compat shim).
2. **Multi-item term matching** — a search term crossing several pdf.js text items needs a space inserted between items on the same baseline only when there is a horizontal gap (real word boundary); visually contiguous items (one word split by a style change, e.g. subset/Type3 fonts) join without a separator. PyMuPDF span bboxes carry ~1e-5pt float jitter, so `gap > 0` must be `gap > JOIN_SPACE_EPSILON` (0.5pt) or tightly packed glyph runs get spurious spaces.
3. **Svelte 5 + pdf.js concurrency** — a sidebar click fires two effects that both render the same canvas; pdf.js throws "Cannot use the same canvas during multiple render()". Fix: cancel the in-flight RenderTask, expose the render promise synchronously (before `await getPage()`), and abort a superseded render right after `getPage()` if the render token changed.
**Solution:** Two-tier grouping heuristic — strong rule (gap ≤ 0.5×size, same baseline) merges regardless of font/size to recover Type3 fragments ("B"+"ooking" → "Booking"); weak rule (gap ≤ 1.2×size + same font/size) for inter-word spacing; column gutters stay split. Validate against real PDFs locally with `scripts/dump-pdf-spans.py` + `scripts/eval-grouping.ts`.
**Tags:** `#frontend` `#pdfjs` `#svelte5` `#grouping` `#type3` `#canvas`
