---
id: "CI-001-harness-review-pool-parity"
type: spec
status: draft # draft | implementing | verifying | archived
created: "2026-10-12"
issue: "mlorentedev/pdf-modifier-mcp#174"   # repo#NNN — GitHub issue / Project item that tracks this spec
risk: high   # widens a production credential's consumer surface and changes the review gate
tags: [spec, proposal]
template_version: "1.0"
---

# CI-001-harness-review-pool-parity

> **Naming**: file lives at `<repo>/specs/CI-001-harness-review-pool-parity/proposal.md`. `CI-001-harness-review-pool-parity` is `AREA-NNN-slug`.

## Why

<!-- from issue #174: CI-001: Bring the review pool and CI to harness parity with dotfiles main -->

The reviewer is a gate, and a gate that silently degrades is worse than no gate. This repo's review pool names `nan/mimo-v2.5`, which NaN retired on 2026-09-30: it hangs, then answers 401, and a review job goes green with no review. That is how the retirement was found the first time, on a PR, hours late. The same stale shape also means the archive gate cannot express the second-signature and fallback roles it enforces, and the CI reviewer runs on one provider with no draw, no risk route and no canary. If we do not ship this, the next retirement repeats the incident, and every `dotf spec archive` here runs with a weaker gate than the one dotfiles main defines.

## What

Bring this repo's review harness to parity with `dotfiles` `main` (`e31c4ee4`), in three observable steps:

1. **The pool describes models that answer, in the shape the gate reads.** `harness/reviewer-pool.json` gains `vendor` on every entry, legal `signs` values, the `mimo-v2.5` successor, the two SSOT members admitted 2026-08-29, and the two Anthropic members (`signs: second`, `signs: fallback`). After this, `dotf spec review` can launch a second signature and a recorded fallback here, and `dotf spec archive` refuses an Anthropic-only signature.
2. **CI reviews through the pool, across two providers.** `.pr_agent.toml` plus four `scripts/pr-agent-*.sh` replace the hardcoded `CONFIG__MODEL` with a weighted draw over members that answered a preflight probe. A PR reaching `pr_agent_risk.min_changed_lines` (1500) or carrying `deep-review` reviews first on the `route: risk` member. With the Anthropic secret absent the draw is NaN-only and the job summary says why; the steps do not fail.
3. **A retirement is found before a PR finds it.** `harness/model-map.json`, `harness/model-pins.json`, `harness/nan-quotas.json`, `scripts/model-canary.sh` and `.github/workflows/model-canary.yml` send one minimal call a day to every bound model and keep exactly one labelled issue in step with the result.

Plus the enabling change in `dotfiles`: `ci:mlorentedev/pdf-modifier-mcp` joins `PR_AGENT_ANTHROPIC_API_KEY`'s consumers (owner-approved spend), then `dotf secrets sync ci --repo mlorentedev/pdf-modifier-mcp`.

## Out of scope

- **No change to the review engine.** `core/modifier.py`, `core/analyzer.py` and the AI router stay as they are; the retired-model defect in the application router is issue #168, not this spec.
- **No new runtime dependency in the shipped product.** `PyPI`, `Dockerfile`, `compose.*.yml` and the SvelteKit app are untouched.
- **No re-measurement of dotfiles' own weights.** This repo adapts the draw to its own key; it does not re-derive dotfiles' budget history.
- **No change to branch protection or merge policy.**

## Risks / open questions

- **The pool has two consumers and one file.** `harness/reviewer-pool.json` feeds both the local archive gate and the CI draw, so a member added for reviews also becomes a candidate signer and vice versa. The SSOT solves this with per-entry `role` plus `pr_agent` blocks; this repo must keep the two readings consistent, and a test must hold the CI preflight chain equal to the pool's NaN members.
- **The Anthropic key is one shared console key with one spend limit.** `pr_agent_risk` at 1500 lines was calibrated for dotfiles alone (~$28 of a $60-65 month). Adding this repo's CI to the same key spends from the same budget. This repo has far fewer PRs, so the marginal cost is small, but the number is unmeasured here and must be stated rather than assumed.
- **The CI tests are `bats`, which this repo does not run.** dotfiles verifies these scripts with ~2,900 lines of `bats` (`tests/pr-agent-*.bats`). Adopting them means adding a test runner to a repo whose gates are `pytest` + `vitest` + Playwright. **MUST be resolved before PR2 code**: either adopt `bats` for `scripts/`, or port the assertions to a runner already present. Deciding later means shipping shell with no test.
- **PR1's evidence bar is set by the pool's own rule**, not by this spec: the file says adding a member is "a decision with the same evidence bar as the SSOT — a measured review, not a model name". So PR1 must record at least one measured review run here, not just a passing JSON check.

## Acceptance criteria

- [ ] **AC1 — The pool conforms to the gate's shape and refuses an Anthropic-only first signature.** Every entry has a non-blank `id`, a `vendor`, and a `signs` value in {`first`(default), `second`, `fallback`}; no Anthropic entry resolves to `first`; and asking the launcher to sign first with a `signs: second` member is refused before any model is launched.
- [ ] **AC2 — No pool entry names a model the canary reports refused.**
- [ ] **AC3 — Pool membership is evidenced here.** At least one member is exercised with a real `dotf spec review` run in this repo, and the result is recorded in `verification.md`.
- [ ] **AC4 — The CI draw spans both providers when funded, and degrades loudly-but-green when not.** With the Anthropic secret present, the job draws by weight across NaN and Anthropic and names the drawn member in the job summary; with it absent, the draw is NaN-only, the summary says why, and no step fails.
- [ ] **AC5 — The risk route fires.** A PR whose additions plus deletions reach `pr_agent_risk.min_changed_lines`, or that carries the `deep-review` label, reviews first on the `route: risk` member.
- [ ] **AC6 — The canary reports a retirement before a PR does.** With a planted dead model bound in `harness/model-map.json`, the canary exits non-zero and rewrites exactly one labelled issue; when every model answers, it closes that issue. Verified with a planted defect, never by absence of findings.
- [ ] **AC7 — No secret value reaches any output.** The canary and the sync report by consequence; `PR_AGENT_ANTHROPIC_API_KEY` and `NAN_API_KEY` are never printed, and the CI preflight names a chosen member, never the credential.

## References

- Bitácora board: `mlorentedev/pdf-modifier-mcp` #174 (`CI-001-harness-review-pool-parity`, Project #1)
- `dotfiles` SSOT: `harness/reviewer-pool.json`, `harness/review-attestation.json`, `docs/runbooks/guide-pr-agent-reviewer.md`
- Upstream decisions: `dotfiles` #786 (TOOL-013, CodeRabbit to PR-Agent), #1923 amendment B (two-vendor signatures), #1860 (AI-045 AC8, model canary)
- This repo: `.github/workflows/pr-agent.yml`, `.pr_agent.toml`, `harness/reviewer-pool.json`, `harness/review-attestation.json`, #161 (review guard on lockfile-only PRs), #168 (retired model in the application router)
- Related patterns: `00_meta/patterns/pattern-spec-driven-development.md`, `00_meta/patterns/pattern-secrets-security.md`, `00_meta/patterns/pattern-nan-builders-gateway.md`
