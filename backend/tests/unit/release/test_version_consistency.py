"""Every version this release declares must be the same version.

The v1.9.1 release published PyPI and Docker and failed at the MCP registry, which
validates that the PyPI package version it is told about exists. It was told 1.9.0:
`pyproject.toml` had been bumped, `server.json`'s server version had been bumped,
and `server.json`'s package version had not.

`release-please-config.json` declares all three in `extra-files`, so the automation
knew about every one of them. The bump was lost by hand while resolving a merge
conflict, with a substitution limited to a single occurrence -- and then verified
with a single-match search. Resolution and verification shared one blind spot and
therefore agreed. This test is the one that has no blind spot: it compares what the
files say, not whether an edit appears to have landed.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path


def _backend_root() -> Path:
    """The backend directory, found rather than counted.

    `parents[3]` assumes this file sits at a fixed depth, which stops being true
    the moment the suite runs from a copy: mutmut runs it from `backend/mutants/`,
    one level deeper and without `server.json` in the copy, and the test died with
    a FileNotFoundError instead of checking versions. Walking up to the directory
    that holds both files works in both places, and does not encode the location
    of the file doing the looking.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file() and (parent / "server.json").is_file():
            return parent
    raise RuntimeError(f"no directory holding pyproject.toml and server.json above {__file__}")


BACKEND = _backend_root()


def declared_versions() -> dict[str, str]:
    """Every place a release version is declared, resolved rather than grepped."""
    pyproject = tomllib.loads((BACKEND / "pyproject.toml").read_text())
    server = json.loads((BACKEND / "server.json").read_text())
    return {
        "pyproject.toml [project].version": pyproject["project"]["version"],
        "server.json $.version": server["version"],
        "server.json $.packages[0].version": server["packages"][0]["version"],
    }


def test_every_declared_version_is_the_same() -> None:
    versions = declared_versions()
    assert len(set(versions.values())) == 1, f"versions disagree: {versions}"


def test_the_version_locations_themselves_do_not_drift() -> None:
    """A new version field must not appear without this test being told about it."""
    assert set(declared_versions()) == {
        "pyproject.toml [project].version",
        "server.json $.version",
        "server.json $.packages[0].version",
    }
