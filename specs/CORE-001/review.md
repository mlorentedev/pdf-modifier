---
spec: "CORE-001"
verdict: "PASS-WITH-GAPS"
reviewed_sha: "7ad75cfb34a1036ad05fee52d5125374655be05b"
reviewer: "nan/deepseek-v4-flash"
date: "2026-10-13"
---

## Adversarial review

**Scope**: CORE-001 — "A replacement must not drop the lines that follow it" (first signature, fresh at `7ad75cf`, base `53a6974` as resolved by the launcher; `main` not substituted).
**Sources**: `specs/CORE-001/{proposal,tasks,verification,features}.md`; `git diff 53a697441c2e7f5236ff0ec0d481808d89c62d7a...HEAD`; `git log 53a6974..HEAD`; `backend/src/pdf_modifier/core/modifier.py`; `backend/tests/unit/core/test_replacement_preserves_following_lines.py`; `backend/scripts/probe_fitter_reachability.py`; the committed rounds `review-round-1..6.md` / `review-second-round-1..2.md` / `review.md` (round 7, `a1b4ae8`) / `review-second.md` (round 7, `a1b4ae8`). I did not read any launcher transcript.

### What I ran, fresh, at this head (evidence before claims)

| Command | Result |
|---|---|
| `uv run pytest -q --no-cov` (backend) | **431 passed, 19 skipped**, exit 0 |
| `uv run pytest tests/unit/core/test_replacement_preserves_following_lines.py -q --no-cov -k "all_replaced or tight_block_is_refused or reach_the_glyph_on_both_axes"` | **4 passed** (the head's new row, its counter-row, the guard row, the new axes row) |
| **M15** — the neighbour-target exemption removed (`if id(span) in targets or same_line …` → `if same_line …`) | **1 failed, 49 passed** — exactly `test_a_tight_block_whose_fields_are_all_replaced_still_converts`. Reproduces the fix round's own RED count, and nothing else in the file moves |
| `PYTHONPATH=scripts uv run pytest tests/ -q --no-cov -p probe_fitter_reachability` | `PROBE {'fits': 148, 'refused_trims': 19, 'unidentified': 1, 'collapsed': 1, 'identified_misses': 1}` over 431 passed |
| Adversarial construction, 3 variants (tight 12 pt/9 pt block where a neighbour is a *partially* replaced span, so its unreplaced prefix sits in another target's rectangle) | **no loss in any variant** — `PREFIXNEW` on both lines, prefix count 2/1/1 preserved; the hypothesis in finding 4 could not be reproduced |

M15 was reverted; `git status --porcelain` shows only the launcher's `specs/CORE-001/review-request.json`. No `[AGENT-DRAFT]` / `[AGENT-SUGGESTION]` tag remains in any contract file.

### Spec and task alignment

- **The head commit is the fix for the second signature's REAL Major, and it is genuinely fixed.** At `a1b4ae8` a tight block whose fields are *all* being replaced was REFUSED where the base commit converted it. `7ad75cf` decides the page's target objects once — before any fitting — and passes them to `_refuse_trim_that_drops_another_line`, which now returns instead of raising when the refused trim's neighbour is itself a target. I verified the behaviour, not the prose: the new row passes, and neutralising exactly that exemption (M15) turns exactly that row red, 1/50.
- **The exemption is aligned with the existing consequence check, not bolted on.** `_check_no_other_object_lost_characters` already exempted a lost span when `span is target` for some redaction tuple; `7ad75cf` builds `targets` from `_target_span(rect, before)` over the same `before` list, i.e. the same identity relation, and `_fit_redaction_to_its_own_text_object` now takes that list rather than re-parsing (which is *required* — a fresh parse would give different dicts and `id(span) in targets` would never match). The coupling is real and deliberate; see finding 3 for what is not pinned about it.
- **Acceptance criteria.** AC2 (set inclusion, all three sizes), AC3 (synthetic tight fixture), AC4 (the following lines present per row) and AC5 (existing suite unchanged: 431 passed, 19 skipped) each carried by a named test I re-ran. AC1 (RED first) still cannot be re-verified from history — `1c0ae90` is unreachable from HEAD because #186 was squash-merged — and `tasks.md` says so honestly; it is reproducible as a neutralisation, which is what M15 is.
- **ADR-014 condition 2 holds.** The diff touches private helpers only: `process()`, `ReplacementSpec`, `models.py` and `analyzer.py` are unchanged, and every refusal reuses `PDFModifierError` with no new type, so CLI/MCP/API/batch paths that already catch it are unaffected.
- **The scope disclosed in `verification.md` is honest**: the code change is the fitter and its guards + one regression file + one probe script; the reviewed *range* additionally carries the release bump, Docker/Glama, the Dependabot check, CI-001 and CORE-006. I did not treat the extra content as this spec's defect, and I did not read it line-by-line.
- **The stop-loss worked.** Round 6 FAILED on a false completion claim in `proposal.md`; the claim is gone — `review_round: 6` now names only committed verdicts and says round 7 is owed rather than asserted. I found no new over-claim; the two ledger problems below are *under*-claims, which is the milder direction and is why neither blocks.

### Findings

| Severity | Reality | Area | Finding | Evidence | Test (named, or UNTESTED) | Fix location (code / tests / spec / vault) |
|----------|---------|------|---------|----------|---------------------------|---------------------------------------------|
| Minor | REAL | spec evidence drift | `features.json` f5 records "**125 fits**, 1 collapse" and f8 "**1 unidentified in 121 fits**". At this head the probe reports **148 fits / 19 refused trims** (commit message says 148/19; round 6 measured 145/18). The qualitative claim survives — the single `collapsed` and `unidentified` are still the guard's own synthetic rows — but a number this spec's own docstring calls a measurement ("a refusal rate that climbs past the synthetic rows means the fitter became stricter than the corpus") has moved twice without the entry moving. `verification.md` re-records the probe at this head; `features.json` is contract. | my run of the documented command (table above) vs `features.json` f5/f8 | The probe is the measurement; no named test asserts the recorded counts: **UNTESTED** | **spec** — `features.json` is in the contract set, so under this verdict it is dispositioned in `verification.md`, not edited |
| Minor | REAL | ledger / handoff | `tasks.md` at the head being archived does not record the head's own work: there is no fix-round entry for `7ad75cf` (the second signature's Major and its exemption fix), the round-6 review box is still `- [ ]`, and the second signature at `a1b4ae8` (FAIL) has no entry. The file that says what was done and why omits the newest code change in the range. `proposal.md`'s `review_round: 6` also understates: verdicts for round 7 exist and are committed (`review.md` PASS by `nan/glm5.3-flash` at `a1b4ae8`, `review-second.md` FAIL by `anthropic-review/claude-sonnet-5-5`). Understating is not the round-6 fault, and the archive gate does not read these boxes — but a reviewer of the archive cannot see from `tasks.md` why `modifier.py` gained the `targets` parameter. | `git log --oneline -3 -- specs/CORE-001/tasks.md` (last touch: none at `7ad75cf`); `grep -n "round" specs/CORE-001/tasks.md`; `git show --stat 7ad75cf` (features.json, probe, modifier.py, test file, review files — no tasks.md) | n/a (spec artifact); the code fix is pinned by `test_a_tight_block_whose_fields_are_all_replaced_still_converts` via M15 | **spec** — `tasks.md`/`proposal.md` are contract; record the round in `verification.md` instead |
| Minor | THEORETICAL | maintainability / fail-safe | The exemption is keyed on object identity (`id(span) in targets`) while the two parameters it depends on are independently optional (`targets: set[int] \| None = None`, `spans: … = None`). A future caller that passes `targets` built from one parse and lets `spans` default would make every `id(span)` miss, silently switching the exemption off. The direction is fail-loud (the guard raises again, as before `7ad75cf` — page refused, no content lost), and the only production caller passes both, but nothing asserts the pairing. | code read of `_fit_redaction_to_its_own_text_object` / `_apply_replacements_to_page`; M15 shows the behaviour when the exemption is off | no test drives the mismatched-pair path: **UNTESTED** | **tests** (one unit row calling the fitter with an empty `targets` and a `spans` list), optionally **code** (derive both inside one helper) |
| Minor | THEORETICAL | correctness / span vs glyph granularity | The exemption is at **span** granularity in both places (the trimmed-against neighbour in the fit guard, and the lost-span skip in `_check_no_other_object_lost_characters`), while a replacement can target a **substring** of a span. If another target's rectangle reached characters of a partially replaced span that its own item rectangle does not cover, those characters would be redacted, exempted by identity, and never re-inserted. **I could not reproduce it**: three tight 12 pt/9 pt constructions in which a neighbour line is `PREFIX` + value with only the value replaced kept every prefix character (`PREFIXNEW` on both lines, prefix counts 2/1/1), because the y-trim or the centre-containment skip spares the prefix. The mismatch remains a genuine structural gap with no covering fixture. | my three attempted constructions, all clean (table above); code read of the identity exemptions | **UNTESTED** — no row has a partially replaced *neighbour* span | **tests** (one row: tight block, neighbour = `PREFIX`+value, only the value replaced, assert the prefix and every other line intact) |

No Blocker and no REAL Major was found. Both REAL findings are Minor, in the contract set, and are evidence/ledger drift that a user of the modifier cannot observe.

### Evaluator rubric

| Dimension | Grade (A-D) | Rationale (one line) |
|-----------|-------------|----------------------|
| Correctness        | **B** | Every acceptance criterion is met and re-run at this head (431 passed, the head's fix pinned exactly by M15); negative shapes (two-span line, overprint, sliver, collapse, tight leading, watermark, all-fields-replaced) are covered; the residual span-vs-glyph gap is THEORETICAL and could not be reproduced. |
| Verification       | **B** | I reproduced the suite, the new rows, M15 and the probe myself, and they match the fix round's claims — much better than the round-6 C — but two contract-set numbers (f5 125 fits, f8 121 fits) no longer reproduce at 148, so the record is not yet A. |
| Scope              | **B** | The code change is the fitter, its guard, one regression file, one probe script and ADR-015/lessons; the reviewed range additionally carries the release bump, Docker/Glama, the Dependabot check, CI-001 and CORE-006, all disclosed in `verification.md`. |
| Reliability        | **B** | Every unsafe fit raises a `PDFModifierError` naming page and rectangles, accepted co-located loss is warned rather than swallowed, the new exemption is bounded to objects this page is replacing and fails loud if the identity pairing breaks; not A because the co-located policy still ships a document with shared-ink characters removed (CORE-003) and the trim loop stays order-sensitive (CORE-009). |
| Maintainability    | **B** | New functions are short, CC well under the repo gate, `mypy --strict`/`ruff` clean, and the comments state why each invariant exists and which round earned it; the `id()`-keyed hidden coupling and the two `None` defaults are the smell. |
| Handoff-readiness  | **C** | Spec triad is present and the remaining work is filed (CORE-003/004/005/009, CI-004), but `tasks.md` does not record the head's own fix round, `proposal.md`'s round count lags the committed verdicts, and the two probe numbers in `features.json` are stale — the ledger is a revision behind the artifact it describes. |

Aggregation: one C, no D → **PASS WITH GAPS** by the rubric path. The severity × reality path gives the same verdict (no Blocker, no REAL Major).

### Verdict

**PASS WITH GAPS**

The defect CORE-001 exists for is fixed, and this round's fix — the one that closed the second signature's REAL Major — is correct and precisely pinned (M15: 1 failed / 49 passed, exactly the new row). I tried to break the new exemption and could not: the partial-span hypothesis, the most promising silent-loss path I could construct against it, preserved every character in three tight-leading variants. What stands between this and a clean PASS is bookkeeping, not behaviour — a stale probe number in two contract entries, a `tasks.md` that never records the head's fix, and an identity contract that is not asserted.

### Recommended next steps

All of the following are **outside the contract set** (`proposal.md`, `tasks.md`, `features.json`); editing any of those three invalidates this verdict.

- **Do not archive yet — the second signature at this head is owed.** `proposal.md` declares `risk: high`, so `dotf spec archive` needs a passing second signature *at the head being archived*. The committed one (`review-second.md`, `anthropic-review/claude-sonnet-5-5`) is at `a1b4ae8`, FAILED, and predates the fix; this review is the first signature. Run `dotf spec review CORE-001 --second` after the findings below are dispositioned.
- **Record the dispositions in `verification.md`** (excluded from the staleness check, which is why the contract corrections below belong there rather than in the contract): (a) re-run `PYTHONPATH=scripts uv run pytest -q --no-cov -p probe_fitter_reachability` and paste the `PROBE {…}` line at the archived head beside f5/f8's older numbers; (b) note the fix round this file's examples already describe, so `tasks.md`'s omission is at least compensated in the record; (c) state that `proposal.md`'s `review_round: 6` counts only verdicts at shas that are not this head.
- **Carry to a ticket** (or add to CORE-009, `#211`, which already holds the trim loop's related gaps): one row for a partially replaced *neighbour* span (finding 4), and one for the `targets`/`spans` identity pairing (finding 3). Both are THEORETICAL and fail loud; neither gates the archive.
- **If the implementer wants `tasks.md` and `features.json` corrected, that is a fix-then-re-review** — correctly so, per the staleness rule — but nothing in the code needs to move for it.

Skipped deliberately, and named as such: I did not run `mutmut` (the spec's mutation matrix is round 4's; I reproduced the newest layer with M15 instead), did not re-measure the per-rectangle parse cost (CORE-005's own number; the head does cache the spans and its own commit message records the partial gain), and did not read the non-CORE-001 content of the range (release bump, Docker/Glama, Dependabot script, CI-001) beyond confirming it is disclosed.
