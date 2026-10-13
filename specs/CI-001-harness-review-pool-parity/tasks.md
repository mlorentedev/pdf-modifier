---
tags: [spec, tasks]
created: "2026-10-12"
---

# Tasks - CI-001-harness-review-pool-parity

> TDD order. One task = one focused commit. Tick as you go. Reorder freely while spec is in `draft` state; freeze once you start `implementing`.
>
> **Inline markers**:
> - `[P]` — no dependency on another unchecked task, safe to parallelize. TDD chains (test → implement → refactor of the same behavior) are sequential and must NOT carry `[P]`.
> - `[AC<n>]` — this task helps satisfy acceptance criterion `#<n>` from `proposal.md`.
>
> **Delivery**: PR1 (pool + attestation + docs) is detailed below and is the only one frozen now. PR2 and PR3 are grouped: they are gated on the open question in `proposal.md` (the `bats` decision) and each gets its own branch and PR, referencing #174.

## Setup

- [x] Branch created from `master`: `feat/CI-001-harness-review-pool-parity`
- [x] `proposal.md` is complete and acceptance criteria are testable
- [ ] Open question in `proposal.md` "Risks / open questions" about the `bats` runner is resolved **before PR2 starts** (not before PR1)

## PR1 — pool, attestation, docs

### Behavior: the pool conforms to the shape the gate reads

- [x] [P] [AC1] Write the failing contract test at `backend/tests/unit/harness/test_reviewer_pool_contract.py`: load `harness/reviewer-pool.json` and assert (a) every entry has a non-blank `id` and `vendor`; (b) `signs`, when present, is one of `first`/`second`/`fallback`; (c) no entry with `vendor == "anthropic"` resolves to `first`; (d) ids are unique.
      Run: `cd backend && uv run pytest tests/unit/harness/test_reviewer_pool_contract.py -q --no-cov`
      Observed: **4 FAILED** — no entry declared `vendor`, no `pr_agent` weight, and the pool carried no `signs: second`/`signs: fallback` member.
- [x] [AC1] Bring `harness/reviewer-pool.json` to the SSOT shape: `vendor` on every entry; `mimo-v2.5` replaced by its successor `mimo-v2.6-flash`; `glm5.3-flash` and `qwen3.8-flash` added; `anthropic-review/claude-haiku-5-5` with `signs: fallback` and `anthropic-review/claude-sonnet-5-5` with `signs: second`; `role` on every entry; `pr_agent` blocks with `weight` plus `reasoning_effort` where the SSOT sets one; `pr_agent_risk` (`min_changed_lines: 1500`, `label: deep-review`); the `$comment` rewritten to state the current rule from `dotfiles#1923` amendment B and to attribute the ported weights and evidence.
      Run the test above. Observed: **PASS** (10 passed).
- [x] [AC1] Add the `pr_agent` weight invariant to the same test: the drawn members' weights sum to 100. Run it. Observed: **PASS**.
- [x] Refactor: extract the signs predicate into a pure helper so a planted offender can drive it, and add `test_pool_carries_a_second_signer_and_a_fallback` so the two roles the archive gate needs cannot be merely absent. Re-run. Observed: **PASS**.
      The predicate test exists because the pass-state assertion alone was vacuous while the pool held no Anthropic member. The CI preflight-chain assertion is deferred to PR2: that chain is defined by `.pr_agent.toml`, which PR1 does not touch.

### Behavior: an Anthropic-only first signature is refused by the launcher

- [x] [AC1] Local, recorded check (CI has no `dotf` binary — that is why this is not a CI test):
      `dotf spec review CI-001-harness-review-pool-parity --reviewer anthropic-review/claude-sonnet-5-5 --dry-run`
      Observed: **exit 1**, `reviewer "anthropic-review/claude-sonnet-5-5" cannot sign this review: it only gives a second signature (launch it with --second, after a first signer)`. Reloaded the pool, so the entry is reachable and the refusal is the eligibility rule, not a schema error.
- [x] [AC1] Local, recorded check that `--fallback-reason` is required for the fallback member:
      `dotf spec review CI-001-harness-review-pool-parity --reviewer anthropic-review/claude-haiku-5-5 --dry-run`
      Observed: **exit 1**, `it is a fallback, which signs first only when the first signers failed: pass --fallback-reason`.
- [x] [AC1] Local, recorded check for a legal first signer:
      `dotf spec review CI-001-harness-review-pool-parity --reviewer nan/deepseek-v4-flash --dry-run`
      Observed: the pool entry resolves and the launcher proceeds past selection; it then refuses with `cannot resolve a review base`, which is the recorded reason the real review moved to the verification window.

### Behavior: the attestation registry declares only observed markers

- [x] [P] [AC1] Extend the contract test: the PR-Agent entry declares `## PR Reviewer Guide`, and every reviewer's `why` records where its marker was observed.
      Run: observed **FAIL** on the provenance assertion — the entry still claimed the workflow had never run here.
- [x] [AC1] Measure before declaring anything. Observed 2026-10-12 over the comments of #165..#173: `## PR Reviewer Guide` on 3 PRs (#171, #170, #167) and on none of the four Dependabot PRs; `## Incremental PR Reviewer Guide` on **none** of the 7. Record both in the entry's `why`, and commit the earlier claim about never having run here as the false statement it had become. Run: **PASS**.
- [x] [AC1] Do **not** declare `## Incremental PR Reviewer Guide`. Declaring a marker WIDENS the gate and this file's own rule is `review_markers ARE MEASURED HERE, NOT COPIED`; the heading is unobserved here, so it waits for PR2, when the reworked workflow may emit it.

### Behavior: the docs point at the specs directory the tooling actually uses

- [x] [P] [AC1] Fix `AGENTS.md`: the `backend/specs/` tree row and Standing Order #5 must say `specs/<id>/` (what `dotf spec init` writes and where `CORE-146` and `PDF-001` live). `backend/specs/` keeps only the historical `README.md` and the `archive/` it already holds.

### Evidence

- [x] Update `features.json` states as the harness captures evidence; never hand-write `passing`.
- [ ] Open PR1 referencing #174 and this spec folder.

## Verification window — before archive

> The real review moved here from PR1. `dotf spec review` diffs the spec folder's first commit against HEAD, so it needs a committed base to run at all, and reviewing a change that is one third written would judge an incomplete implementation. AC3 is satisfied here, not in PR1.

- [ ] [AC3] Run one real review on a pooled member here and record the run in `verification.md`:
      `dotf spec review CI-001-harness-review-pool-parity --reviewer nan/deepseek-v4-flash`
      Expected: `review.md` written under `specs/CI-001-harness-review-pool-parity/`, signed by the member named.
- [ ] [AC1] With `risk: high` declared, launch the second signature (`--second`) and confirm the gate accepts an Anthropic member only beside a first signer of another vendor.

## PR2 — PR-Agent CI through the pool  (own branch, own PR)

**Blocked on:** the `bats`-runner decision in `proposal.md`.

- [ ] [AC4] Resolve the runner decision and record it in `verification.md` before writing any script.
- [ ] [P] [AC4] Port `scripts/pr-agent-model-preflight.sh` (168 lines) and its test.
- [ ] [P] [AC4] Port `scripts/pr-agent-route.sh` (341 lines) and its test, keeping the NaN/Anthropic draw and the `PR_AGENT_PROVIDER` override (`draw`/`nan`/`anthropic`/`nan-only`).
- [ ] [P] [AC4] Port `scripts/pr-agent-publish-guard.sh` (233 lines) and `scripts/pr-agent-push-gate.sh` (211 lines) with their tests.
- [ ] [AC5] Adapt `.pr_agent.toml` from the SSOT to this repo: model from the pool, `fallback_models` from the pool, `reasoning_effort` for the members the pool sets it on, and this repo's own measurements in the comments instead of dotfiles'.
- [ ] [AC4] [AC5] Rework `.github/workflows/pr-agent.yml`: replace the hardcoded `CONFIG__MODEL`/`CONFIG__FALLBACK_MODELS` with the preflight probe, the weighted draw, the risk route, and the two-provider attempt pair. Assert the two Anthropic attempt copies are identical.
- [ ] [AC5] Create the `deep-review` label: `gh label create deep-review --repo mlorentedev/pdf-modifier-mcp --color 5319e7 --description "Route the PR-Agent review to the risk-route model"`.
- [ ] [AC4] Add the credential-presence path: with `PR_AGENT_ANTHROPIC_API_KEY` unset the job draws NaN-only, the summary says why, and no step fails.
- [ ] [AC7] Keep every credential out of `run:` interpolation: both workflows pass secrets to steps only through `env:`, and the guard passes:
      `! grep -nE 'run:[[:space:]]*\$\{\{[[:space:]]*secrets\.' .github/workflows/pr-agent.yml .github/workflows/model-canary.yml`

## PR3 — model canary  (own branch, own PR)

- [ ] [P] [AC2] Port `harness/model-map.json`, `harness/model-pins.json` and `harness/nan-quotas.json`, with `model-pins.json` re-derived for this repo's pin sites (it names files and spellings, so it is adapted, not copied).
- [ ] [P] [AC6] Port `scripts/model-canary.sh` (118 lines).
- [ ] [AC6] Add `.github/workflows/model-canary.yml` (daily cron + `workflow_dispatch`), building `dotf` from the `dotfiles` checkout since this repo has no `cli/`.
- [ ] [AC2] [AC6] Plant a dead model id in `harness/model-map.json`, run `dotf secrets run --only NAN_API_KEY -- dotf harness canary`, and record: **exit non-zero** and exactly one labelled issue rewritten. Revert the plant.
- [ ] [AC6] With every model answering, run the canary again and record: **exit 0** and the issue closed.

## Cross-repo task (dotfiles)

- [ ] [AC4] In `dotfiles`, add `ci:mlorentedev/pdf-modifier-mcp` to `PR_AGENT_ANTHROPIC_API_KEY`'s `consumers` in `secrets/registry.yaml`, in its own PR (external worktree, per Standing Order #9).
- [ ] [AC4] After that PR merges: `dotf secrets sync ci --repo mlorentedev/pdf-modifier-mcp`. Report by exit status; never print the value.

## Closing

- [ ] Every acceptance criterion from `proposal.md` is covered by at least one test
- [ ] Every acceptance criterion has a matching entry in `features.json` with a non-vacuous verification command
- [ ] Type checks pass (`make check`, `make check-frontend`)
- [ ] Lint passes
- [ ] No unrelated changes in the diff (no scope creep)
- [ ] `verification.md` filled in
- [ ] PRs opened referencing this spec folder
