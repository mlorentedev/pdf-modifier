---
spec: "CORE-001"
verdict: "FAIL"
reviewed_sha: "a1b4ae8fda07acb04799697c4fb1c4663cabdb4d"
reviewer: "anthropic-review/claude-sonnet-5-5"
date: "2026-10-13"
---
## Adversarial review

**Scope**: CORE-001 (`risk: high`, second signature), whole range `git diff 53a697441c2e7f5236ff0ec0d481808d89c62d7a...HEAD`.
**Sources**: `specs/CORE-001/{proposal,tasks,features.json,verification}.md`; `backend/src/pdf_modifier/core/modifier.py`; `backend/tests/unit/core/test_replacement_preserves_following_lines.py`; `docs/adr/adr-015-refuse-rather-than-lose.md`. I did not read `review.md`, its transcript, or any `review-round-*` file.

### Spec and task alignment
- The ticked tasks have diff evidence. All eleven `features.json` verification commands were re-run here and exit 0 (f1 6, f2 3, f3 48, f4 9, f5 1, f6 429 + 19 skipped, f7 3, f8 1, f9 9, f10 2, f11 4 passed). `ruff check`, `ruff --select C901` at max-complexity 10, and `mypy --strict src` are clean.
- The regression file is real RED on the base: with the base `src` on `PYTHONPATH` it gives **40 failed / 8 passed**. At HEAD it gives 48 passed.
- Black-box differential testing against the base, with a generated-layout fuzzer (2,100 layouts: random fonts, sizes, leading, columns, label+value spans touching, watermarks, rotated text, 1-5 targets):
  - At HEAD, no layout converted with a non-target token missing, and no target value survived under its replacement. The base lost tokens in 280/400, 455/600 and 601/700 of the layouts in the three groups of runs.
  - In the three runs of uniform-leading layouts (1,400 layouts), no layout that the base converted without loss was refused at HEAD.
  - The chaotic mixed-size run (700 layouts) is where the Major below appeared (8 over-refusals).
- Refusal leaves no output file, and a pre-existing output file is untouched (CLI check at 12 pt on 7.2 pt leading: exit 1, no `out.pdf`).
- **Spec vs code mismatch.** `proposal.md` "What does not change" says behaviour not reachable through a replacement that currently drops lines is unchanged. At HEAD a replacement that drops nothing in the base can now be refused (Finding 1).
- No `[AGENT-DRAFT]` / `[AGENT-SUGGESTION]` tags found in the spec files.

### Findings

| Severity | Reality | Area | Finding | Evidence | Test (named, or UNTESTED) | Fix location (code / tests / spec / vault) |
|----------|---------|------|---------|----------|---------------------------|---------------------------------------------|
| Major | REAL | `_refuse_trim_that_drops_another_line` (modifier.py) | The prospective refusal raises when the trim is refused against a neighbour on another line, **without asking whether that neighbour is itself a replacement target**. A neighbour being replaced has its characters removed by design, so no content is dropped, and the post-hoc consequence check already exempts targets (`if any(span is target ...)`). Result: a tight block whose fields are all being replaced converts in the base and is refused at HEAD, and the user has no workaround (a single-field replace on the same block is also refused, by design). | Repro (`/tmp/fz/adj2.py`): three 12 pt Courier-Bold lines `FIELD0..2` at 9 pt leading (0.75 em), isolated from the other text, replace all three. Base: `OK 'keepkeep\nNEWVAL0\nNEWVAL1\nNEWVAL2'`, no loss. HEAD: `PDFModifierError: Cannot fit the redaction rectangle on page 1: covering (72.0, 76.916, 115.2, 93.716) needs the rectangle to reach the neighbouring line ...`. Sweep (`/tmp/fz/adj3.py`): HEAD refuses at exactly 0.75 em for 9 pt and 12 pt, and is OK at 0.5-0.7 and 0.8-1.0; the base converts every row. Mixed sizes: fuzz seed 9109 (8 pt lines beside 14 pt lines, three adjacent targets) was refused at HEAD and converted without loss in the base. Mutation: neutralising the early return of `_refuse_trim_that_drops_another_line` makes the repro convert correctly and the whole 0.5-1.0 sweep pass, and turns red **only** the two single-target rows `test_a_tight_block_is_refused_rather_than_losing_the_line_below[12.0pt-on9.0pt]` and `[9.0pt-on7.0pt]`. Everything else, including the CORE-006 sweep, is carried by the post-hoc check. | UNTESTED. No row replaces several adjacent fields of a tight block. All 0.75/0.78 em rows replace a single field. | code + tests: skip neighbours that are targets of another rectangle, or drop the prospective raise and let `_check_no_other_object_lost_characters` decide, as ADR-015 states it should ("the rectangle-fitting heuristic stays, demoted"). Add a row replacing 2-3 adjacent fields at 0.75 em, with a non-target line far away. |
| Minor | REAL | performance | Per-rectangle page re-parse plus an O(spans) loop per rectangle makes the fit quadratic, and the added consequence check re-reads the page once more. Ticketed (CORE-005, `#202`, still OPEN), not fixed. | `/tmp/fz/perf.py`: 70 literal replacements on an 840-span page took 0.10 s on the base and 1.32 s at HEAD (13x). `/tmp/fz/perf2.py`: one regex matching 840 spans took 4.07 s on the base and 23.2 s at HEAD. Passing the already-computed `before` spans into the fitter (tried, reverted) only brought 23.2 s to 9.9 s, so a real fix needs spatial filtering and not just caching. | UNTESTED (no perf test; `probe_fitter_reachability.py` counts fits, not time) | code (`#202`) |
| Minor | REAL | test strength | The height clause of `_removes_glyph` is unpinned: replacing `enough_height` with `True` leaves all 414 unit tests green. The floor is pinned only to within ±0.01 (0.11 and 0.13 also pass 414), which is acceptable since 0.12 is a deliberate margin. | Mutation runs this session. Every other mutation tried was killed: `_same_line` 0.9 to 0.1, `GLYPH_REMOVAL_FRACTION` 0.5 and 0.0, the `_same_line` term in `_co_located_redaction_took`, the whitespace skip, the target exemption, forcing `same_line = False`, the IoU tie-break, floor 0.0, dropping the `contains(centre)` skip, the warning append, and forcing the x-axis branch. | UNTESTED for the height clause | tests |
| Minor | REAL | handoff / spec artifacts | `features.json` evidence has drifted from what its own commands print: f3 says "28 passed in the file" (now 48), f6 says "409 passed" (now 429), and f5/f8 say 125 fits (the probe at this head records 145 fits / 18 refused trims in `verification.md`). `verification.md` also numbers rounds inconsistently with `proposal.md` and `tasks.md` (it has "Round 6" twice, with different meanings, and a "Round 7" and a "Round 8" that are the same review cycle as `tasks.md`'s round 5 and second-signature round 2). The commands all pass, so this is bookkeeping, not correctness. | `features.json` against the re-run output above. | n/a | `verification.md` (record the current counts). `features.json` is in the contract set, so edit it only if a re-review follows anyway. |
| Minor | THEORETICAL | scope | The reviewed range carries unrelated content: the release workflow, Dockerfile, `.gitignore`, the Dependabot check, the `Glama` files, the rename-guard test exclusion, and the whole CORE-006 consequence check (its own spec, archived at `fb6f87a`). `features.json` f6 ("the diff adds the one regression file") is false of this range, since `tests/unit/rename/test_no_stale_project_name.py` also changed. `verification.md` already scopes this claim to the spec's own commits, so I record it and do not escalate. | `git diff --stat` for the range | n/a | spec (already acknowledged in `verification.md`) |
| Question | n/a | accepted limits | ADR-015's "co-located is a proxy for unavoidable" (CORE-007 `#209`) means a different-line neighbour that the redactor takes can be warned instead of refused when its box lies within 90% vertical extent of the target. I saw this only in chaotic mixed-size fuzz layouts where the small text's box lay inside a 24 pt neighbour and the warning was emitted (seeds 9006, 9011); I could not construct a non-overlapping-ink example. This is disclosed and ticketed, so I record it, not as a finding. | fuzz seeds 9006, 9011 | UNVERIFIED beyond the above | none |

### Evaluator rubric

| Dimension | Grade (A-D) | Rationale (one line) |
|-----------|-------------|----------------------|
| Correctness        | C | The defect is fixed in 2,100 generated layouts with no silent loss; one REAL regression: all-targets tight blocks that the base converted are now refused. |
| Verification       | B | Every command reproduces; mutation kills are strong; no row covers adjacent-targets-in-a-tight-block, and the `_removes_glyph` height clause is unpinned. |
| Scope              | B | Code change is scoped; the range carries unrelated merges and CORE-006's check, both acknowledged. |
| Reliability        | C | Fails loudly and cleanly (no output written), but refuses a document it need not, and the quadratic fit regresses 6-13x. |
| Maintainability    | B | CC <= 10 per `ruff C901`, mypy strict clean, comments explain why; `modifier.py` grows by about 480 lines with a long static-helper cluster. |
| Handoff-readiness  | B | ADR-015, lessons and tickets in place; evidence counts and round numbering have drifted. |

### Verdict
FAIL

A REAL Major (Finding 1) that is UNTESTED. No Blocker and no rubric D. The fix is code and tests only (outside the contract set), so a re-review at the new head should flip it.

### Recommended next steps
- **Needed to flip to PASS (code + tests, contract set untouched):**
  - Fix Finding 1: exempt neighbours that are themselves replacement targets from `_refuse_trim_that_drops_another_line`, or remove the prospective raise and rely on the post-hoc check.
  - Add a named regression row for it: 2-3 adjacent fields of a tight block (0.75 em, 12 pt on 9 pt) converting with the far non-target line intact, plus the counter-row that a non-target neighbour on the next line still refuses.
  - Re-run `test_a_tight_block_is_refused_rather_than_losing_the_line_below` and the CORE-006 sweep, and check that the two single-target rows still refuse, now through the post-hoc check with its own message. Confirm the tests assert on the page-naming content and not on the pre-emptive wording.
- **Track, not blocking:** pin the `_removes_glyph` height clause with a row; CORE-005 (`#202`) should name the 13x/5.7x figures above as its baseline and note that caching `before` alone is not sufficient; refresh the `features.json` evidence counts in `verification.md`, since `features.json` itself stays closed unless a re-review follows.
- `dotf spec archive` is **not** advisable at this head.
