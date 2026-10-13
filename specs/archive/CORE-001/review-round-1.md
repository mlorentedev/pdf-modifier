---
spec: "CORE-001"
verdict: "FAIL"
reviewed_sha: "f1dd8eab60a4d1900d42cee37ccd39b5f6a5ef89"
reviewer: "nan/mimo-v2.6-flash"
date: "2026-10-13"
---

## Adversarial review

**Scope**: CORE-001 — "A replacement must not drop the lines that follow it"
**Sources**: `specs/CORE-001/{proposal,tasks,verification,features}.md` + `git diff 53a697441c2e7f5236ff0ec0d481808d89c62d7a...HEAD` (4 commits: ae28471 fix, 7d138d9 lessons, a1b6056 release, f1dd8ea spec docs)

### Spec and task alignment

Verified by running, not by reading claims:

- **Red-green confirmed.** I bypassed `_fit_redaction_to_its_own_text_object` (mutation, then reverted) and ran `tests/unit/core/test_replacement_preserves_following_lines.py`: **3 failed, 3 passed** — exactly the RED state tasks.md claims. Tree restored, `git status` clean.
- **Core suite**: `uv run pytest tests/unit/core -q --no-cov` → **183 passed, 11 skipped** (matches verification.md).
- **Full backend suite**: `uv run pytest -q` → **387 passed, 19 skipped** (verification.md says 385; both green, minor count drift). `ruff check .` → clean; `mypy src` → clean (31 files).
- **No existing test was modified or deleted** in the diff — the acceptance criterion "existing suite passes unchanged" holds structurally, and no test-retention questions arise.
- **ADR-014 exists** (`docs/adr/adr-014-core-defect-exception.md`); its three conditions are evidenced (RED-first, no public API change — helper is private/static, diff scoped to modifier + new test).
- **No `[AGENT-DRAFT]` / `[AGENT-SUGGESTION]` tags** in any spec file.
- **Acceptance criteria, line by line**: (1) failing test first, three rows — **met** (mutation above); (2) *every* input line present in output unless replaced — **violated**, see Blocker; (3) synthetic, tight fixture — **met** (11 pt leading vs 12.6 pt line height); (4) message per row — **met** (set-inclusion assertion subsumes the two following lines, prints the missing set); (5) existing suite unchanged — **met**.
- **Rotated pages** (rotate 0/90/180): replacement and neighbour preservation all work — no finding.
- **Performance**: helper re-extracts `page.get_text("dict")` once per rect — measured 40 replacements on one page in 0.134 s. Not a finding.

### Findings

| Severity | Reality | Area | Finding | Evidence | Test (named, or UNTESTED) | Fix location |
|----------|---------|------|---------|----------|---------------------------|--------------|
| Blocker | REAL | core/redaction | The fix silently fails on a **mixed-style target line**. When the replaced span shares its line with an adjacent text object (label + value drawn separately — e.g. value in a different colour), the helper's **y-only** trim has no correct move for a horizontal neighbour: the neighbour's `y0` is dragged onto `trimmed.y1`, the rect collapses to area 0, and the guard **returns the original, unfitted rect** — restoring exactly the defect CORE-001 exists to fix. `ARC: 00` and `CVM: 5E0000` are dropped again. This violates acceptance criterion 2 ("Every line present in the input is present in the output unless deliberately replaced") and the proposal's claim that "the re-layout … preserves the lines that follow the replacement". | Reviewer end-to-end repro (`PDFModifier.process` on a 10-line tight fixture; target line = `"AC:  "` span + value span in blue): `missing=['ARC: 00', 'CVM: 5E0000']`, `10->10` lines with old value gone, new value present — silent content loss. Trim trace: `TRIM by 'AC:  ' bbox=(72,150.94,99,163.54) → y1=150.927, area=0.0000 → final = ORIGINAL rect`. Same-line span touching the rect at x=99.0 is enough; any style change (colour/bold/size) splits a line into two spans, which is how key-value receipt lines are commonly emitted. Not a regression — the pre-fix code dropped these lines too — but the spec's general claim is unmet on a realistic shape. | UNTESTED — all six parametrised rows of `test_no_untouched_line_is_lost[...]` use single-style lines; no named test has a mixed-style line | code + tests |
| Minor | REAL | core/redaction | The empty-rect guard fails **silently**: `if trimmed.get_area() <= 0: return fitz.Rect(rect)` hands the un-fitted rectangle straight back to the redactor with no log, warning, or error, converting a detectable fitting failure into invisible content loss (the mechanism of the Blocker above). | `backend/src/pdf_modifier/core/modifier.py` lines 197-199; triggered in the Blocker repro with no output on stderr/stdout | UNTESTED | code (log/raise or fall back to a symmetric inward trim, never to the raw rect) |
| Minor | REAL | spec/tasks | tasks.md `[x]` claims "Commit the failing test on its own (`1c0ae90`) so the RED state is in the history", and verification.md repeats "RED committed on its own (`1c0ae90`)". On this line of history that is not true: `git merge-base --is-ancestor 1c0ae90 HEAD` → false; PR #186 was squash-merged, so ae28471 contains test+fix together. `1c0ae90` is only reachable from `refs/heads/fix/CORE-001-reflow-drops-lines`. The RED evidence survives in the squash message and the branch ref, not in HEAD's history as claimed. | commands above; `git log --follow 53a6974..HEAD -- <test file>` shows only ae28471 | n/a | spec (contract: `tasks.md`; also `verification.md`, non-contract) |
| Minor | REAL | spec/features | `features.json` is untouched scaffold from `dotf spec init`: `state: "pending"`, `verification: "echo 'not implemented' && exit 1"`, `evidence: ""`. Whatever consumes it (the archive lists it among the contract files) sees an unimplemented, failing placeholder instead of CORE-001's real feature description. | file content as quoted | n/a | spec (contract: `features.json`) |

Code-level checklist over the diff: no injection surface (rects only, no shell/SQL), no secrets, no auth, no async blocking (helper runs in the existing sync core path), performance measured negligible, helper ≈30 lines / CC ≈8 (within limits), docstring explains WHY thoroughly. No hits beyond the findings above.

### Evaluator rubric

| Dimension | Grade (A-D) | Rationale (one line) |
|-----------|-------------|----------------------|
| Correctness        | D | A REAL, reproduced instance of the spec's exact content-loss defect remains on a realistic document shape; acceptance criterion 2 is violated ("defects present"). |
| Verification       | B | Strong reproducible evidence for what it covers (red-green, real document, set-inclusion), but fixture-bound: no evidence could cover the mixed-style shape, and the `1c0ae90` RED-history claim does not hold on HEAD. |
| Scope              | B | The CORE-001 commits match the proposal exactly (modifier helper + new test + spec docs); the range also carries unrelated release/lessons commits from separate PRs, documented as such. |
| Reliability        | C | One demonstrated silent-failure path: fitting failure falls back to the buggy original rect with no signal, losing content without an error. |
| Maintainability    | A | Clear naming, <40-line helper, CC ≤10, docstring documents the mechanism and its history; ruff/mypy clean. |
| Handoff-readiness  | B | Spec triad + ADR + lessons written; but features.json scaffold untouched and tasks/verification contain one inaccurate history claim. |

### Verdict
FAIL

One **REAL Blocker** (mixed-style line → silent fallback → dropped lines, reproduced end-to-end) and a **D** in Correctness. Per severity × reality, a REAL Blocker forces FAIL regardless of the rubric; the rubric agrees via Correctness D. The failing shape is **UNTESTED** — no named test exercises it, so the implementer's fixture-green claim cannot close it.

### Recommended next steps

Contract-set edits (`proposal.md` / `tasks.md` / `features.json`) are in scope precisely because this is FAIL — they are part of what a re-review will examine:

1. **code**: teach the helper about horizontal neighbours — trim in **x** when the intersecting span shares the target's vertical band (same line), keep the y-trim only for spans whose band differs; and when the rect would collapse, never return the raw original — trim symmetrically toward the centre or fail loudly.
2. **tests**: add a named regression row where the target line is two spans (label + value, different colour/style), in the same three sizes; verify red-green (fails with the helper neutralised, passes with the fix). This is the test that closes the Blocker's UNTESTED status.
3. **spec (contract)**: correct the `1c0ae90` claim in tasks.md (RED lives on `fix/CORE-001-reflow-drops-lines`, not in HEAD's history — squash-merged), and replace the `features.json` scaffold with the real feature state. Re-record the Blocker and its repro in `verification.md` (non-contract) as part of the fix round.
4. **vault/repo (optional)**: the fixture gap is another instance of lesson-021's shape ("a check that assumes the world") — one line appended there, or a note on #179, keeps the knowledge in-session.
5. After the fix: re-run `dotf spec review CORE-001`. `proposal.md` declares `risk: high`, so a **second signer** (`--second`) is required alongside the re-review before archive.

**Minimum set to flip to PASS**: items 1 and 2 (fix + named regression test, red-green evidenced), plus disposition of items 3 in the same round. `dotf spec archive` is **not advisable** in the current state — the verdict is FAIL and the archive would record CORE-001 as fixed while the content-loss defect survives on mixed-style lines.
