"""Optional AI consistency reviewer (NaN Cloud or any OpenAI-compatible API).

The reviewer runs ONLY when an API key is configured in the environment
(``NAN_API_KEY`` for NaN, or an OpenAI-compatible endpoint via ``NAN_BASE_URL`` +
``AI_REVIEW_MODEL``). Without a key it ``skip``s — it is a second, semantic
opinion layered on top of the deterministic ``ConsistencyValidator``, never a
hard dependency, and it never blocks the replacement.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

from .client import NaNClient
from .exceptions import AIError
from .router import ModelRouter, TaskType

logger = logging.getLogger(__name__)

_PROMPT = """Strictly review the target values a PDF text-replacement will write. Flag ONLY
semantic/plausibility inconsistencies that deterministic arithmetic cannot catch, for example:
- a total that is implausible for the stated number of nights,
- a cancellation fee / refund that contradicts the stated policy ("cost of the first night"),
- a date whose declared weekday is wrong for that calendar date,
- a monetary figure that looks inconsistent with the others (a tax far from the stated rate).

The values are already mutually consistent by arithmetic — do NOT report arithmetic mismatches.
Return ONLY JSON, no prose:
{"issues": [{"severity": "error" | "warning", "message": "...", "field": "..."}]}

Target values:
{values}
"""


@dataclass(frozen=True)
class AIReviewFinding:
    """A finding raised by the AI reviewer."""

    severity: str
    message: str
    field: str

    def __str__(self) -> str:
        return f"[{self.severity}] {self.field}: {self.message}"


@dataclass
class AIReviewResult:
    """Outcome of an AI review pass."""

    skipped: bool = False
    model: str | None = None
    findings: list[AIReviewFinding] = field(default_factory=list)
    error: str | None = None


class AIReviewer:
    """Runs a semantic consistency pass via an OpenAI-compatible chat API.

    ``client`` may be injected (e.g. ``NullAIClient`` for tests). By default it
    builds a ``NaNClient``, which reads ``NAN_API_KEY`` / ``NAN_BASE_URL`` from the
    environment. The model defaults to the ``REVIEW`` routing (``mimo-v2.6-flash``) and
    can be overridden via ``AI_REVIEW_MODEL``.
    """

    def __init__(self, client: Any | None = None, model: str | None = None) -> None:
        self.client = client if client is not None else NaNClient()
        self.model = model or os.environ.get("AI_REVIEW_MODEL") or self._default_model()

    @staticmethod
    def _default_model() -> str:
        """Pick a sensible default model per provider (overridable via AI_REVIEW_MODEL)."""
        if os.environ.get("NAN_API_KEY"):
            return ModelRouter().get_model(TaskType.REVIEW)  # mimo-v2.6-flash
        if os.environ.get("OPENAI_API_KEY"):
            return "gpt-4o-mini"
        return ModelRouter().get_model(TaskType.REVIEW)

    def is_available(self) -> bool:
        """Whether an API key is present (and the reviewer can actually run)."""
        return bool(self.client.is_configured)

    async def review(
        self,
        values: dict[str, object],
        deterministic: dict[str, bool] | None = None,
    ) -> AIReviewResult:
        """Run a review pass. Returns ``skipped`` when no API key is configured."""
        if not self.is_available():
            return AIReviewResult(skipped=True, model=self.model)

        # .replace() — the prompt contains literal braces in the JSON example, so
        # str.format() would try to substitute them and raise KeyError.
        prompt = _PROMPT.replace("{values}", json.dumps(values, default=str))
        try:
            data = await self.client.chat(
                self.model,
                [{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            content = data["choices"][0]["message"]["content"]
            return AIReviewResult(model=self.model, findings=self._parse(content))
        except AIError as exc:
            logger.warning("AI review error: %s", exc)
            return AIReviewResult(model=self.model, error=str(exc))
        except Exception as exc:  # noqa: BLE001 — a failure must never block the caller
            logger.warning("AI review failed unexpectedly: %s", exc)
            return AIReviewResult(model=self.model, error=str(exc))

    @staticmethod
    def _parse(content: str) -> list[AIReviewFinding]:
        """Best-effort parse of the model's JSON response into findings."""
        try:
            obj: dict[str, Any] = json.loads(content)
        except (ValueError, TypeError):
            return []
        issues = obj.get("issues") or []
        findings: list[AIReviewFinding] = []
        for item in issues:
            if not isinstance(item, dict):
                continue
            findings.append(
                AIReviewFinding(
                    severity=str(item.get("severity", "warning")),
                    message=str(item.get("message", "")),
                    field=str(item.get("field", "")),
                )
            )
        return findings
