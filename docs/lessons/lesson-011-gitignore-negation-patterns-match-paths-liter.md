---
id: "lesson-011-gitignore-negation-patterns-match-paths-liter"
type: lesson
status: active
title: ".gitignore negation patterns match paths literally, not by suffix"
created: "2026-06-24"
owner: manu
tags: [pdf-modifier-mcp, lesson, git, gitignore, ci, file-tracking]
---

# .gitignore negation patterns match paths literally, not by suffix

**Context:** Moved the test suite to `backend/tests/` and the fixture `sample.pdf` stopped being tracked.
**Problem:** CI failed with "PDF file not found". The un-ignore rule `!tests/data/*.pdf` was still present and looked correct, but no longer matched anything after the move.
**Solution:** Add `!backend/tests/data/*.pdf` to match the new location, and drop the over-broad `data/` rule that was ignoring the directory in the first place.
**Why:** A pattern containing a `/` anywhere except at the end is anchored to the `.gitignore` file's directory — `tests/data/*.pdf` means exactly `<root>/tests/data/`, not "any path ending in tests/data". Moving a directory therefore silently invalidates every anchored negation that pointed into it. A negation also cannot resurrect a file whose *parent directory* is excluded, so the broad `data/` rule had to go regardless. Verify with `git check-ignore -v <path>`, which prints the exact rule that decided.
**Tags:** `#git` `#gitignore` `#ci` `#file-tracking`
