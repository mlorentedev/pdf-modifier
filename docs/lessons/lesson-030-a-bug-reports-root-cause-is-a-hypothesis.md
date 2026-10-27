---
id: lesson-030-a-bug-reports-root-cause-is-a-hypothesis
type: lesson
status: active
created: "2026-10-26"
owner: manu
tags: [pdf-modifier, lesson, verification, testing, triage]
---

# A bug report's root cause is a hypothesis, and a fixture decides whether it can be tested

**Context:** An externally written report listed six engine defects, each with a confident root cause and a recommended patch. Three were fixed in #219; three were not.
**Problem:** Two of the reported causes were false for the pinned PyMuPDF (1.27.1): `insert_text` on a page whose indirect `/Resources` lacks `/Font` *does* add the font to that object, and `import fitz` emits no `FutureWarning`. Patching them would have shipped core changes with no test able to fail. A third defect was real but hid behind its fixture: the span loop's early `break` only bites when two matching spans share ONE text object, and two `insert_text` calls produce two blocks, so the convenient fixture passed against the bug.
**Solution:** **(1) Reproduce the reported cause on a synthetic fixture before writing a fix**; a report that cannot be made to fail is answered with the reproduction, not a patch (ADR-014 already demands the failing test for core changes). **(2) Assert the fixture's shape inside the fixture**: the single-line helper in `test_replacement_matching.py` asserts one line with two spans, so a refactor that splits it fails loudly instead of silently testing nothing. **(3) Measure Base14 widths with `fitz.get_text_length`**: `fitz.Font` rejects the short aliases (`CoBo`, `HeBo`) that `insert_text` accepts, which had silently broken hyperlink rects for those fonts. **(4) Run tests with `backend/.venv/bin/python -m pytest`**: `uv run pytest` can resolve a user-site pytest without `pytest-cov` and fail on `--cov-fail-under`.
**Tags:** `#verification` `#testing` `#triage` `#fixtures`
