#!/usr/bin/env python3
"""Report which open Dependabot alerts still describe this repository.

An open alert is a claim about a locked version, and it is only as fresh as
Dependabot's last scan: the version it names may already be gone. Reading the
alert text alone tells you what was true when it was created, which is how a
"critical, fix available" list came to be 21 parts stale out of 23.

This resolves each alert's package against the lockfiles the repository actually
commits and says which ones are still vulnerable, which ones are already fixed
and which have no patch published. Exit status is 1 when anything is genuinely
vulnerable, so it can gate a scheduled job later.

Usage:
    python3 scripts/check-dependabot-alerts.py [--repo OWNER/NAME]

Requires `gh` authenticated for the repository's alerts API.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCKFILES = (
    REPO_ROOT / "backend" / "uv.lock",
    REPO_ROOT / "frontend" / "package-lock.json",
    REPO_ROOT / "site" / "package-lock.json",
)


def version_key(version: str) -> tuple[int, ...]:
    """A comparable key for a version string, without needing a library."""
    parts: list[int] = []
    for chunk in version.replace("-", ".").split("."):
        digits = "".join(char for char in chunk if char.isdigit())
        if digits:
            parts.append(int(digits))
        elif parts:
            break
    return tuple(parts)


def locked_versions() -> dict[str, str]:
    """Every package the repository has pinned, by name, from its lockfiles."""
    pinned: dict[str, str] = {}
    for path in LOCKFILES:
        if not path.exists():
            continue
        if path.suffix == ".lock" and path.name == "uv.lock":
            for package in tomllib.loads(path.read_text()).get("package", []):
                pinned.setdefault(package["name"].lower(), package["version"])
            continue
        data = json.loads(path.read_text())
        for name, meta in (data.get("packages") or {}).items():
            version = (meta or {}).get("version")
            if not name or not version:
                continue
            # npm keys are paths: the package name is what follows the last
            # node_modules/ segment.
            pinned.setdefault(name.split("node_modules/")[-1], version)
    return pinned


def open_alerts(repo: str) -> list[dict[str, Any]]:
    """The repository's open alerts, straight from the API the UI reads."""
    out = subprocess.run(
        ["gh", "api", f"repos/{repo}/dependabot/alerts?state=open&per_page=100"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return json.loads(out)


def classify(
    alert: dict[str, Any], pinned: dict[str, str]
) -> tuple[str, str, str | None]:
    """(package, verdict, patched version) for one alert, against the lockfiles."""
    package = alert["dependency"]["package"]["name"]
    patched = (alert["security_vulnerability"].get("first_patched_version") or {}).get(
        "identifier"
    )
    have = pinned.get(package.lower())
    if not have:
        return package, "not in any lockfile", patched
    if not patched:
        return package, "no patch published", patched
    already = version_key(have) >= version_key(patched)
    return package, "already fixed" if already else "VULNERABLE", patched


def main() -> int:
    repo = sys.argv[sys.argv.index("--repo") + 1] if "--repo" in sys.argv else None
    if repo is None:
        repo = subprocess.run(
            ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    pinned = locked_versions()
    rows = []
    for alert in open_alerts(repo):
        severity = alert["security_advisory"]["severity"]
        package, verdict, patched = classify(alert, pinned)
        have = pinned.get(package.lower(), "-")
        rows.append((verdict, severity, package, have, patched or "-"))
    rows.sort(key=lambda row: (row[0] != "VULNERABLE", row[0], row[1]))
    for verdict, severity, package, have, patched in rows:
        print(
            f"{verdict:20} {severity:8} {package:30} locked={have:14} patched={patched}"
        )
    vulnerable = [row for row in rows if row[0] == "VULNERABLE"]
    print(
        f"\n{len(rows)} open alert(s): {len(vulnerable)} still vulnerable, "
        f"{sum(1 for r in rows if r[0] == 'already fixed')} already fixed"
    )
    if vulnerable:
        print("Fix these, or dismiss the alert with the reason it no longer applies.")
        return 1
    print(
        "Nothing to fix: every open alert names a version the lockfiles no longer carry."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
