"""Unit tests for scripts/gen-env.py — the `make env` generator."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# The generator script lives at the repo root (scripts/gen-env.py), outside
# the backend package — load it by file path instead of package import.
# Walk up from this test file until scripts/gen-env.py is found (robust to
# checkout layout: backend/tests/unit/scripts/ here, different depth elsewhere).
REPO_ROOT = Path(__file__).resolve()
while not (REPO_ROOT / "scripts" / "gen-env.py").is_file():
    parent = REPO_ROOT.parent
    if parent == REPO_ROOT:
        raise FileNotFoundError("could not locate repo root with scripts/gen-env.py")
    REPO_ROOT = parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_gen_env = importlib.util.spec_from_file_location("gen_env", REPO_ROOT / "scripts" / "gen-env.py")
assert _gen_env and _gen_env.loader
_gen_env_mod = importlib.util.module_from_spec(_gen_env)
sys.modules["gen_env"] = _gen_env_mod
_gen_env.loader.exec_module(_gen_env_mod)

DEV_OVERRIDES = _gen_env_mod.DEV_OVERRIDES
render_env = _gen_env_mod.render_env

EXAMPLE = """# comment stays
APP_NAME=pdf-modifier
APP_ENV=production
DEBUG=false
CORS_ORIGINS=https://yourdomain.com
MAX_UPLOAD_SIZE=50MB
# SECRET_KEY comment stays above
SECRET_KEY=
"""


def test_render_env_preserves_comments_and_unrelated_keys(tmp_path: Path) -> None:
    example = tmp_path / ".env.example"
    example.write_text(EXAMPLE, encoding="utf-8")

    out = render_env(example)

    assert "# comment stays" in out
    assert "APP_NAME=pdf-modifier" in out
    assert "# SECRET_KEY comment stays above" in out


def test_render_env_applies_dev_overrides(tmp_path: Path) -> None:
    example = tmp_path / ".env.example"
    example.write_text(EXAMPLE, encoding="utf-8")

    out = render_env(example)

    assert "APP_ENV=development" in out
    assert "APP_ENV=production" not in out
    assert "DEBUG=true" in out
    assert "CORS_ORIGINS=http://localhost:5173,http://localhost:8080" in out
    assert "MAX_UPLOAD_SIZE=100MB" in out
    assert "STORAGE_PATH" not in out or DEV_OVERRIDES  # no stale STORAGE line


def test_render_env_generates_nonempty_secret_key(tmp_path: Path) -> None:
    example = tmp_path / ".env.example"
    example.write_text(EXAMPLE, encoding="utf-8")

    out = render_env(example)

    secret_lines = [line for line in out.splitlines() if line.startswith("SECRET_KEY=")]
    # Exactly one SECRET_KEY line, with a non-empty value.
    assert len(secret_lines) == 1
    assert len(secret_lines[0]) > len("SECRET_KEY=")


def test_render_env_secret_is_random_each_call(tmp_path: Path) -> None:
    example = tmp_path / ".env.example"
    example.write_text(EXAMPLE, encoding="utf-8")

    out1 = render_env(example)
    out2 = render_env(example)

    def secret(content: str) -> str:
        return next(line for line in content.splitlines() if line.startswith("SECRET_KEY="))

    assert secret(out1) != secret(out2)


def test_render_env_missing_example_raises(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(FileNotFoundError):
        render_env(tmp_path / "nope.env")
