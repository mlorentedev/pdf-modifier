---
id: lesson-022-a-conflict-in-a-generated-file-is-resolved-by-regenerating-it
type: lesson
status: active
created: "2026-10-13"
owner: manu
tags: [pdf-modifier, lesson, release, release-please, conflict-resolution]
---

# A conflict in a generated file is resolved by regenerating it, not by patching the side that looks like a version bump

**Context:** Release-please opened the release PR for `v1.9.1` and it conflicted with `master`, because a rename had just landed in the two files the version bump touches. The conflict was mechanical and the resolution looked obvious: keep both changes. The rename from `master`, the bumped version from the release branch.
**Problem:** `backend/server.json` carries **two** version fields — the server's and the pinned PyPI package's. `release-please-config.json` declared **both** in `extra-files`, so the generator had produced both correctly. The hand resolution used a substitution hard-coded to a **single** occurrence. It changed the first, left the second at `1.9.0`, and the release published PyPI and Docker and failed at the MCP registry, which validates that the package version it is told about exists — it was told `1.9.0`, never published. Then the fix was checked with a single-match search, which printed the field that had been changed and said nothing about the one that had not. **The generator knew about every location; the hand resolution knew about one, and the verification agreed with the resolution rather than with the file.**
**Solution:** When a conflict lands in a file a tool generates, resolve it by **regenerating that file** — re-run the generator, or take the generator's version wholesale and re-apply nothing by hand. Patching a generated file is how a mechanical conflict becomes a semantic loss, and the fields a generator maintains are exactly the ones a human does not know the full list of. If a hand resolution is unavoidable, verify it against what the file **declares** — every occurrence, compared for agreement — never against the one edit just made. A version is a value several places claim simultaneously; a check for it must compare them to each other.
**Tags:** `#release` `#release-please` `#conflicts` `#verification`
