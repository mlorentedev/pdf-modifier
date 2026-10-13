---
id: pdf-modifier-troubleshooting-release-publishing
type: troubleshooting
status: active
tags: [troubleshooting, release, pypi, trusted-publishing, rename, mcp-registry]
created: "2026-10-13"
owner: manu
---

# Release Publishing (PyPI, Docker, MCP registry)

Failure modes of the `Release` workflow (`.github/workflows/release.yml`), from the OIDC
identity PyPI refuses to the registry validating a version the index has not served yet. Both
were found on real releases, and one of them was caused by renaming the repository.

## PyPI answers `400 Non-user identities cannot create new projects`

### Problem

A release published its Docker images and failed at PyPI, while the other jobs stayed green:

```
400 Non-user identities cannot create new projects. This was probably caused by
successfully using a pending publisher but specifying the project name incorrectly
(either in the publisher or in your project's metadata).
```

### Root cause

Trusted Publishing is keyed by **repository slug**, and an OIDC identity can never *create* a
project — a human registers a **pending publisher** for the name first, and the first successful
upload creates it. Two independent misconfigurations produce the same 400, and fixing only one
leaves the other silent until someone tries the second path:

1. **The new name had no pending publisher.** `pdf-modifier` did not exist on PyPI, and no
   identity can bring it into existence.
2. **The old name's publisher still pointed at the old repository slug.** `pdf-modifier-mcp` was
   configured for `mlorentedev/pdf-modifier-mcp`; after the rename that repository no longer
   exists, so the legacy name could not be published either — which is exactly what the planned
   deprecation shim needs. **The shim was blocked by the same rename**, in a way unrelated to the
   shim itself.

### Diagnostic steps

1. Read which job failed: `publish-docker` green + `publish-pypi` red + `publish-mcp` skipped is
   this, not a broken workflow.
2. Compare the project name in `backend/pyproject.toml` against the pending publishers listed at
   PyPI → *Your projects* → *Publishing*.
3. Check whether a repository rename happened since the last release (`git log --oneline --follow
   .github/workflows/release.yml`, or the repo's own rename ADR). If it did, every trusted
   publisher keyed by the old slug is now dead, including ones for other package names.

### Solution

Both registrations are manual — PyPI publishes no API or IaC for publisher configuration, so
there is nothing to automate here and the steps are the artifact:

- a **pending publisher** for the new project name (`pdf-modifier`), owner `mlorentedev`,
  repository `pdf-modifier`, workflow `release.yml`, the environment the job declares (`pypi`);
- an **updated** trusted publisher for the legacy name (`pdf-modifier-mcp`) with the same new
  repository slug.

Then re-run the **failed job** — not the whole workflow. The tag, the GitHub release and the
Docker images were already correct, so there is nothing to recreate.

### Prevention

- **A repository rename is a publishing-credential operation, not only a GitHub operation.** Put
  "re-register every trusted publisher keyed by the old slug" in the rename's own checklist; the
  coupling is otherwise invisible until the release that needs it.
- Symptom shape to recognise: **one red job among green ones**, at the last step of a release
  that otherwise succeeded, with an OIDC message about creating a project. Nothing earlier in the
  pipeline is wrong.
- Keep the rename out of the same release as a functional change. This failure was diagnosed in
  one log read, but only because the rename was already merged and its ADR known; merged
  together, a red publish has two candidate causes and no way to order them.

## MCP registry validation fails with `404` for a version PyPI has not served yet

### Problem

`publish-mcp` fails on a release that otherwise succeeded:

```
registry validation failed for package 0 (pdf-modifier): PyPI package 'pdf-modifier'
exists, but version '1.9.2' was not found (status: 404).
A newly published release can take a moment to appear on PyPI. Wait and retry, or
publish version '1.9.2' before registering it
```

### Root cause

Not job ordering. `publish-mcp` already waits for `publish-pypi`
(`needs: [release-please, publish-pypi]`), and the run timeline confirms it: on v1.9.2,
`publish-pypi` finished at `06:11:28Z` and the failing validation ran at `06:11:35Z` — seven
seconds later. The race is between a **finished upload** and **PyPI's index**, which the registry
queries on its own side.

### Diagnostic steps

1. Check the job order in the run, not the assumption about it:
   `gh run view <run-id> --json jobs --jq '.jobs[] | "\(.name) \(.startedAt) \(.completedAt)"'`.
2. If `publish-pypi` completed *before* the failure timestamp, it is index lag, not ordering.
3. Re-run the failed job: it passes, which confirms the diagnosis.

### Solution

`.github/workflows/release.yml` retries `mcp-publisher publish` five times with a growing
backoff (15/30/45/60 s), exiting on the first success so a publish that already landed is never
repeated. A permanent failure still fails the step with an `::error::` naming it.

### Prevention

- **Re-running a failed job is a diagnosis, not a fix.** It is exactly what hides this class: the
  release goes green afterwards, so nothing pushes anyone to fix the ordering or the wait.
- An error message that names its own remedy ("wait and retry") is the library telling you the
  operation is not atomic with its precondition. Encode the wait; do not retry by hand.
