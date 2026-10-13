"""Guard: no live file names the project by its retired identity.

The rename's whole risk is *"renamed almost everywhere"* — a stale slug inside a
workflow comment, a console-script key, a registry entry. Each one goes green
until the moment it is exercised, and the moment is usually a release.

An unwritten grep is not a mechanism, and a grep whose exclusion list lives in
somebody's head reports the historical records as failures until somebody widens
it carelessly. So both halves are declared here: the exclusions with the reason
each one is a record rather than a live reference, and a test that no live
surface is inside them.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

# The retired identity, in BOTH spellings it ships in -- and the second one is
# the reason this is a tuple. The slug `pdf-modifier-mcp` is what a package
# manager resolves; `PDF Modifier MCP` is what a human reads. The second survived
# the first pass of this rename in AGENTS.md's opening line while this guard
# reported success: it was looking for one string in a file that used the other.
# A slug and its prose form are the same identity, so a rename that moves one and
# not the other is half a rename that reports as whole.
RETIRED_NAMES = ("pdf-modifier-mcp", "PDF Modifier MCP")

# The guard's own path, as a constant so the exclusion key fits on one line.
GUARD_FILE = "backend/tests/unit/rename/test_no_stale_project_name.py"

# Historical records that name the project as it was called then. Rewriting them
# to make this guard green would falsify the record, which is a worse defect than
# a stale string in a document nobody installs. GitHub redirects the old repo
# URLs, so their links keep working.
EXCLUSIONS: dict[str, str] = {
    "docs/lessons/": "historical records: each says what was true when it was written",
    "docs/lessons.md": "the lessons pointer stub, part of that record",
    "docs/adr/adr-013-project-rename.md": "the decision record must name the from and the to",
    # The rename CAUSED this failure, so the doc cannot explain it without the old
    # name: Trusted Publishing is keyed by the project slug, and the retired slug is
    # the reason the publish was rejected. Rewriting it would leave a troubleshooting
    # note that no longer describes the problem it is filed under.
    "docs/troubleshooting/release-publishing.md": "a failure the rename caused, so it names both",
    "specs/": "spec folders are audit artifacts, including the issue they trace to",
    "backend/specs/": "pre-move spec artifacts, archived the same way",
    "backend/CHANGELOG.md": "release-please owns it; it narrates the old name by definition",
    # The only self-exclusion. A guard that cannot name what it searches for cannot
    # search for it, and this file names no product surface -- every path in
    # LIVE_SURFACES below is still asserted to be outside this list.
    GUARD_FILE: "this guard names the retired identity in order to search for it",
}

# Surfaces whose job is to be installed, executed or followed. None of these may
# ever be excluded, or the guard could be silenced by widening the list above.
LIVE_SURFACES = (
    "Makefile",
    "README.md",
    "SECURITY.md",
    "smithery.yaml",
    ".env.example",
    "backend/pyproject.toml",
    "backend/server.json",
    "backend/uv.lock",
    ".github/workflows/pr-agent.yml",
)

REPO_ROOT = Path(__file__).resolve()
while not (REPO_ROOT / ".git").exists():
    parent = REPO_ROOT.parent
    if parent == REPO_ROOT:
        raise FileNotFoundError("could not locate the repository root")
    REPO_ROOT = parent


def is_excluded(path: str, exclusions: dict[str, str] | None = None) -> bool:
    """True when `path` is a declared historical record rather than a live file."""
    rules = EXCLUSIONS if exclusions is None else exclusions
    return any(path == rule or path.startswith(rule) for rule in rules)


def stale_references(
    contents: dict[str, str], exclusions: dict[str, str] | None = None
) -> list[str]:
    """Return the paths that still carry the retired name outside the exclusions."""
    return sorted(
        path
        for path, text in contents.items()
        if any(name in text for name in RETIRED_NAMES) and not is_excluded(path, exclusions)
    )


def tracked_contents() -> dict[str, str]:
    """Every tracked text file, keyed by repo-relative path.

    `git ls-files`, so an untracked scratch file cannot fail the build and a
    tracked one cannot hide. Binary files are skipped by their NUL byte rather
    than by an extension list, which would be a second thing to keep true.
    """
    listed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    contents: dict[str, str] = {}
    for rel in listed.splitlines():
        try:
            raw = (REPO_ROOT / rel).read_bytes()
        except OSError:
            continue
        if b"\x00" in raw:
            continue
        contents[rel] = raw.decode("utf-8", errors="ignore")
    return contents


def test_no_live_reference_to_the_retired_name() -> None:
    """The repo is renamed everywhere a user, an installer or CI can read it."""
    problems = stale_references(tracked_contents())
    assert not problems, (
        f"these still name the project {RETIRED_NAMES} (either spelling), and none "
        f"is a declared historical record:\n  " + "\n  ".join(problems)
    )


def test_guard_catches_a_planted_live_reference() -> None:
    """The guard must trip on a real occurrence, or it is a green check that scans nothing."""
    assert stale_references({"README.md": f"install {RETIRED_NAMES[0]}"}) == ["README.md"]
    assert stale_references({"AGENTS.md": "**PDF Modifier MCP** tool"}) == ["AGENTS.md"]


def test_guard_ignores_a_declared_exclusion() -> None:
    """A record that names the old identity is the past, not a defect."""
    assert stale_references({"docs/lessons/lesson-001-x.md": RETIRED_NAMES[0]}) == []


def test_every_exclusion_states_why_it_is_a_record() -> None:
    """Widening this list is the one edit that can silence the guard, so it must read as one."""
    unexplained = [rule for rule, reason in EXCLUSIONS.items() if not reason.strip()]
    assert not unexplained, f"these exclusions carry no reason: {unexplained}"


def test_no_live_surface_is_excluded() -> None:
    """The anti-gaming half: a live surface may never be excluded to make the guard pass."""
    excluded = [path for path in LIVE_SURFACES if is_excluded(path)]
    assert not excluded, (
        f"these live surfaces are inside the exclusion list, which silences the guard "
        f"exactly where it matters: {excluded}"
    )


def test_the_distribution_lookup_resolves_under_the_new_name() -> None:
    """`version("pdf-modifier")` must find the distribution, or importing the package raises.

    The guard above cannot see this defect: it fails on a string that is PRESENT,
    and this one is a string that is GONE from a lookup that is now dead. Renaming
    the distribution without renaming `importlib.metadata.version(...)` leaves a
    repo that greps clean and raises `PackageNotFoundError` on `import`.
    """
    from importlib.metadata import version

    import pdf_modifier

    assert pdf_modifier.__version__ == version("pdf-modifier")
