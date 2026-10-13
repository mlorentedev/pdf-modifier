---
tags: [spec, verification]
created: "2026-10-12"
---

# Verification - CI-001-harness-review-pool-parity

> PR1 evidence only. AC2 and AC6 belong to PR3, AC4/AC5/AC7 to PR2, and AC3 plus the second-signature check to the verification window before archive. Recorded here as the PRs land, not at the end.

## Evidence

- [x] **AC1** — pool conforms to the gate's shape and refuses an Anthropic-only first signature.
  - Contract test: `backend/tests/unit/harness/test_reviewer_pool_contract.py`, commit `e5e2629`. Before: `4 failed` (no `vendor` on any entry, no `pr_agent` weight, no `signs: second`/`signs: fallback` member). After the pool port (`adc423b`): `10 passed`.
  - Non-vacuity: the Anthropic-signs-first rule is driven by a pure predicate with a **planted offender** (`test_anthropic_first_detector_catches_a_planted_offender`), because asserting it against the real pool alone passed while the pool held no Anthropic member. `test_pool_carries_a_second_signer_and_a_fallback` asserts both roles exist and that a `signs: second` vendor differs from every first-signer vendor, so a `risk: high` spec is satisfiable here.
  - Launcher, refuse the second signer as first (commit `1a11ee1`):
    `dotf spec review CI-001-harness-review-pool-parity --reviewer anthropic-review/claude-sonnet-5-5 --dry-run`
    → **exit 1**: `reviewer "anthropic-review/claude-sonnet-5-5" cannot sign this review: it only gives a second signature (launch it with --second, after a first signer)`. The pool loaded, so this is the eligibility rule and not a schema error.
  - Launcher, a fallback first signer needs a classified reason:
    `--reviewer anthropic-review/claude-haiku-5-5 --dry-run` → **exit 1**: `it is a fallback, which signs first only when the first signers failed: pass --fallback-reason`.
    `--reviewer anthropic-review/claude-haiku-5-5 --fallback-reason rate-limit --dry-run` → **exit 0**, and the printed command pins `--provider anthropic-review --model claude-haiku-5-5` and injects **only** `REVIEW_ANTHROPIC_API_KEY` preceded by `secrets run --only`.
  - Launcher, a legal first signer resolves and pins the provider explicitly:
    `--reviewer nan/deepseek-v4-flash --dry-run` → **exit 0**, `--provider nan --model deepseek-v4-flash`, injecting only `NAN_API_KEY`.
  - `--second` before any first review is refused: `no first review was launched ... (review-request.json is missing)`.
  - Attestation half: the registry's own rule (`review_markers ARE MEASURED HERE, NOT COPIED`) is now enforced by `test_every_reviewer_records_its_marker_provenance`. `## Incremental PR Reviewer Guide` is deliberately **not** declared — measured on none of #165..#173 — because declaring a marker widens the gate (commit `c9a6110`, lesson-019).
- [ ] **AC2** — pending PR3 (canary over the ported model map).
- [ ] **AC3** — pending the verification window; see "Decisions" for why it is not in PR1.
- [ ] **AC4** — pending PR2.
- [ ] **AC5** — pending PR2.
- [ ] **AC6** — pending PR3.
- [ ] **AC7** — pending PR2 (workflow guard; PR1 touches no workflow).

## Test status

- Backend: `make check` → **358 passed**, 19 skipped, coverage **84.20%** (gate 80%). Was 348 passed before; +10 are the new contract tests.
- Frontend: `make check-frontend` → svelte-check 0 errors, **50 passed** (6 files). Unchanged by PR1.
- Lessons guard: `bash scripts/check-lessons.sh` → `check-lessons: OK (19 lessons)`.
- Manual smoke: the four `dotf spec review --dry-run` invocations above, which exercise pool loading, member resolution, provider pinning and the secret scoping without spending a token.
- No regressions: **yes**.

## Decisions made during implementation

- **`## Incremental PR Reviewer Guide` is NOT declared**, against a literal reading of parity. Measured 0 of 7 recent PRs; declaring a marker widens the attestation gate while omitting it fails closed. Recorded in the entry's `why` and deferred to PR2. This is the one place PR1 departs from the SSOT on purpose.
- **The real adversarial review moved from PR1 to the verification window.** `dotf spec review` diffs the spec folder from the commit that added it, so it cannot run before the folder is committed; and reviewing a change that is one third written would judge an incomplete implementation. AC3 stays in `proposal.md` and its task moved to a dedicated section in `tasks.md`.
- **Weights ported as parity, not recalibrated.** The SSOT's 19/27/19/35 allocation was calibrated against dotfiles' review volume, and this repo spends from the same Anthropic key and shared monthly limit. Borrowed numbers are stated as borrowed in the pool's `$comment` rather than presented as measured here.
- **Pool membership evidence is attributed, not re-measured.** The pool's SSOT rule requires a measured review per member; each ported `why` marks which evidence is the SSOT's, and this repo's own run is AC3. Copying a name would have satisfied the same rule only by pretending.
- **A stale claim was corrected in passing**: the attestation entry asserted the workflow "has NEVER been observed" here, which the 3 observed PRs made false. Fixed with the measurement that replaced it (`c9a6110`).

## Promotion candidates

- [x] Lesson for the repo's `docs/lessons/`? yes: `docs/lessons/lesson-019-declaring-an-unobserved-review-marker-widens-the-gate.md`
- [x] ADR-worthy decision for the repo's `docs/adr/adr-XXX.md`? no: the pool shape and the signing rule are governed by the dotfiles SSOT; this repo ports a decision, it does not make one.
- [x] New pattern candidate for `00_meta/patterns/`? no: "measure a gate's allow-list before widening it" is already the rule this file states and the test now enforces; it is not new cross-project knowledge.

## Archive checklist

- [ ] `proposal.md` frontmatter set to `status: archived`
- [ ] Folder moved: `specs/CI-001-harness-review-pool-parity/` -> `specs/archive/CI-001-harness-review-pool-parity/`
- [ ] Bitácora board ticket for this spec moved to Done / closed with PR link (ADR-018)
- [ ] Promotions above executed (if any)
