---
id: lesson-020-a-rename-guard-cannot-see-a-dead-distribution-lookup
type: lesson
status: active
created: "2026-10-12"
owner: manu
tags: [pdf-modifier-mcp, lesson, rename, packaging, guards, importlib-metadata]
---

# A rename guard goes green while `import` still raises: presence guards cannot see a dead lookup

**Context:** REFACTOR-001 (#143) renamed the project to `pdf-modifier`. "Renamed everywhere" is not a claim a human can check across a repository, so `backend/tests/unit/rename/test_no_stale_project_name.py` was written first and watched to fail: it lists tracked files with `git ls-files` and fails on any `pdf-modifier-mcp` outside a declared exclusion list.
**Problem:** Two separate traps, and both point the same way. First, the guard's own failure list was 29 files while an unfiltered `grep -rI` reported **thousands** — the difference was `.mypy_cache` and `coverage.xml`, neither tracked. A guard scoped to the whole working tree would have been noisy enough to be widened, and a guard scoped by an extension list would have been a second thing to keep true. Second, and worse: `backend/src/pdf_modifier/__init__.py` and `web/app.py` resolve the version through `importlib.metadata.version("pdf-modifier-mcp")`. Rename the distribution without that string and the lookup raises `PackageNotFoundError`, so `import pdf_modifier` fails — while the guard reports success, because the failing string is *absent* and a guard that fails on presence cannot see absence from a place that needed it. The grep is green and the package cannot be imported.
**Solution:** Split the two claims. The presence guard proves no *live* file still carries the retired identity, and it declares both halves in the same file: the exclusions with the reason each is a historical record, and a `LIVE_SURFACES` tuple asserted to be outside them, so widening the list to silence the check is a visible edit rather than a quiet one. The absence claim needs its own test that *executes* the thing: `test_the_distribution_lookup_resolves_under_the_new_name` imports the package and compares `__version__` to `version("pdf-modifier")`. The general rule: a rename has two failure directions, and only one of them is a string you can grep for. Enumerate what *reads* the name at runtime — `importlib.metadata`, badge URLs, registry markers that must equal a manifest field — and test those by execution.
**Tags:** `#rename` `#packaging` `#guards` `#importlib-metadata`
