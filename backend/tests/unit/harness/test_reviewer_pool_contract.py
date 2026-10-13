"""Contract tests for the review harness ports read by `dotf spec review` and `dotf spec archive`.

`harness/reviewer-pool.json` and `harness/review-attestation.json` are cross-repo
ports of the dotfiles SSOT. These assertions pin the shape the gate reads, so a
field that disappears or a model that a vendor retires fails here rather than at
the moment a review is launched — which is how `nan/mimo-v2.5` was found the
first time: on a pull request whose review job went green with no review.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# The harness ports live at the repo root, outside the backend package. Walk up
# from this test file until harness/reviewer-pool.json is found, so the test is
# robust to checkout layout (backend/tests/unit/harness/ here).
REPO_ROOT = Path(__file__).resolve()
while not (REPO_ROOT / "harness" / "reviewer-pool.json").is_file():
    parent = REPO_ROOT.parent
    if parent == REPO_ROOT:
        raise FileNotFoundError("could not locate repo root with harness/reviewer-pool.json")
    REPO_ROOT = parent

POOL_PATH = REPO_ROOT / "harness" / "reviewer-pool.json"
ATTESTATION_PATH = REPO_ROOT / "harness" / "review-attestation.json"

LEGAL_SIGNS = {"first", "second", "fallback"}
PR_AGENT_MARKER = "## PR Reviewer Guide"


def anthropic_first_offenders(entries: list[dict]) -> list[str]:
    """Return the ids of Anthropic entries that would sign first.

    A pure helper so the rule can be driven by a planted offender. Asserting it
    only against the real pool passes vacuously while the pool carries no
    Anthropic member, and a check that scans nothing is indistinguishable from a
    green one.
    """
    return [
        e["id"]
        for e in entries
        if str(e.get("vendor", "")).lower() == "anthropic"
        and str(e.get("signs", "first")) == "first"
    ]


@pytest.fixture(scope="module")
def pool() -> dict:
    return json.loads(POOL_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def entries(pool: dict) -> list[dict]:
    return pool["pool"]


def test_pool_is_not_empty(entries: list[dict]) -> None:
    assert entries, f"{POOL_PATH} declares an empty pool"


def test_every_entry_declares_an_id_and_a_vendor(entries: list[dict]) -> None:
    """`id` is what the gate matches; `vendor` is the unit a second signature must differ in."""
    missing = [i for i, e in enumerate(entries) if not str(e.get("id", "")).strip()]
    assert not missing, f"pool entries {missing} have a blank id"

    no_vendor = [e["id"] for e in entries if not str(e.get("vendor", "")).strip()]
    assert not no_vendor, (
        f"these entries declare no `vendor`, so the second-signature check cannot "
        f"tell whether two signers are of different vendors: {no_vendor}"
    )


def test_entry_ids_are_unique(entries: list[dict]) -> None:
    ids = [e["id"] for e in entries]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    assert not duplicates, f"duplicate pool ids: {duplicates}"


def test_signs_is_legal_when_declared(entries: list[dict]) -> None:
    """`signs` absent means `first`; anything else is a typo the gate would refuse at load."""
    illegal = [
        (e["id"], e["signs"]) for e in entries if str(e.get("signs", "first")) not in LEGAL_SIGNS
    ]
    assert not illegal, f"entries declare an illegal `signs` value: {illegal}"


def test_no_anthropic_member_signs_first(entries: list[dict]) -> None:
    """dotfiles#1923 amendment B: an Anthropic model never signs a review alone.

    `dotf spec archive` refuses the file outright when this holds, so failing here
    is the earlier and clearer signal.
    """
    offenders = anthropic_first_offenders(entries)
    assert not offenders, (
        f"these Anthropic entries would sign first, which the gate refuses: {offenders}. "
        f'Declare `"signs": "second"` or `"signs": "fallback"` on them.'
    )


def test_anthropic_first_detector_catches_a_planted_offender() -> None:
    """The guard above must trip on a real offender, or it is a green check that scans nothing."""
    planted = [
        {"id": "anthropic-review/claude-sonnet-5-5", "vendor": "anthropic", "signs": "second"},
        {"id": "anthropic-review/claude-haiku-5-5", "vendor": "anthropic", "signs": "fallback"},
        {"id": "anthropic-review/claude-opus-9", "vendor": "anthropic"},  # no signs -> first
        {"id": "nan/deepseek-v4-flash", "vendor": "deepseek"},  # first is fine off-Anthropic
    ]

    assert anthropic_first_offenders(planted) == ["anthropic-review/claude-opus-9"]


def test_pool_carries_a_second_signer_and_a_fallback(entries: list[dict]) -> None:
    """The roles the archive gate enforces must be expressible here, not merely absent.

    Without these two, a `risk: high` spec could not satisfy the second signature
    and a failed first signer could not be replaced -- the capability would exist
    in the tooling and nowhere in this repo.
    """
    second = [e["id"] for e in entries if str(e.get("signs", "first")) == "second"]
    fallback = [e["id"] for e in entries if str(e.get("signs", "first")) == "fallback"]

    assert second, "no pool member declares `signs: second`, so no spec can take a second signature"
    assert (
        fallback
    ), "no pool member declares `signs: fallback`, so a failed first signer has no replacement"

    second_vendors = {e["vendor"] for e in entries if str(e.get("signs", "first")) == "second"}
    first_vendors = {e["vendor"] for e in entries if str(e.get("signs", "first")) == "first"}
    assert second_vendors - first_vendors, (
        "every `signs: second` member shares a vendor with a first signer, so a second "
        "signature could never satisfy the cross-vendor rule"
    )


def test_drawn_pr_agent_weights_sum_to_100(entries: list[dict]) -> None:
    """The draw's share of every member is its declared weight, so the shares must be a whole."""
    weights = {
        e["id"]: e["pr_agent"]["weight"] for e in entries if "weight" in e.get("pr_agent", {})
    }
    assert (
        weights
    ), "no pool entry declares a pr_agent.weight, so the CI draw has nothing to draw from"
    total = sum(weights.values())
    assert total == 100, f"pr_agent weights sum to {total}, not 100: {weights}"


def test_attestation_declares_the_observed_pr_agent_marker() -> None:
    """The registry must recognise the heading PR-Agent actually posts under."""
    registry = json.loads(ATTESTATION_PATH.read_text(encoding="utf-8"))
    pr_agent = [r for r in registry["reviewers"] if PR_AGENT_MARKER in r.get("review_markers", [])]
    assert pr_agent, f"no reviewer entry declares the {PR_AGENT_MARKER!r} marker"


def marker_provenance_problems(reviewers: list[dict]) -> list[str]:
    """Return one problem string per marker that has no recorded provenance.

    Per MARKER, and against a LIST of sightings rather than prose. Scanning `why`
    for the marker string accepted a note recording that the heading was observed
    ZERO times -- the note names the marker, so the marker could be declared while
    its own evidence said nobody had ever seen it. A non-empty list has no such
    reading: an unobserved marker has no sighting to record.
    """
    problems: list[str] = []
    for r in reviewers:
        login = str(r.get("login", "?"))
        measured = r.get("markers_measured") or {}
        for marker in r.get("review_markers", []):
            entry = measured.get(marker)
            if not isinstance(entry, dict):
                problems.append(f"{login}: no `markers_measured` entry for {marker!r}")
                continue
            seen = entry.get("observed_in")
            if not isinstance(seen, list) or not seen:
                problems.append(
                    f"{login}: the entry for {marker!r} records no observation "
                    f"(observed_in={seen!r}); a marker nobody has seen cannot be declared"
                )
    return problems


def test_every_declared_marker_records_its_own_provenance() -> None:
    """`review_markers ARE MEASURED HERE, NOT COPIED` -- this file's own rule, made executable.

    A marker declared without a measurement is a claim about an actor nobody has
    observed, and the reading it produces is a green check that scans nothing.
    """
    registry = json.loads(ATTESTATION_PATH.read_text(encoding="utf-8"))
    problems = marker_provenance_problems(registry["reviewers"])
    assert not problems, (
        "these reviewer entries declare a marker without recording where it was "
        f"observed: {problems}"
    )


def test_marker_provenance_detector_catches_the_zero_observation_form() -> None:
    """The guard must reject a marker whose own note says it was seen zero times.

    That is the form the prose check could not tell from provenance: the note
    names the marker, and the marker gets declared on evidence that says nobody
    has ever seen it.
    """
    planted = [
        {
            "login": "clean",
            "review_markers": ["## One"],
            "markers_measured": {"## One": {"on": "2026-10-12", "observed_in": ["#1"]}},
        },
        {
            "login": "zero-observation",
            "review_markers": ["## Two"],
            "why": "Measured 2026-10-12: '## Two' appears on none of those 7.",
            "markers_measured": {"## Two": {"on": "2026-10-12", "observed_in": []}},
        },
        {"login": "unrecorded", "review_markers": ["## Three"], "markers_measured": {}},
    ]

    problems = marker_provenance_problems(planted)

    assert any(p.startswith("zero-observation:") for p in problems)
    assert any(p.startswith("unrecorded:") for p in problems)
    assert not [p for p in problems if p.startswith("clean:")]
