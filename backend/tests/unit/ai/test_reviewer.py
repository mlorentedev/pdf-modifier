"""Tests for the optional AI consistency reviewer.

The reviewer must SKIP (not crash) when no API key is configured, and must parse
the model's JSON findings when one is. Never hits a real API.
"""

from __future__ import annotations

import asyncio
from typing import Any

from pdf_modifier.ai.reviewer import AIReviewer


class _StubAI:
    """Minimal OpenAI-compatible stub for deterministic tests."""

    def __init__(self, content: str, configured: bool = True) -> None:
        self.is_configured = configured
        self._content = content
        self.calls = 0

    async def chat(self, model: str, messages: list[dict[str, str]], **_: Any) -> dict[str, Any]:
        self.calls += 1
        return {"choices": [{"message": {"content": self._content}}]}


class _Unconfigured:
    is_configured = False


class TestAIReviewer:
    def test_skipped_when_no_key(self) -> None:
        reviewer = AIReviewer(client=_Unconfigured())
        result = asyncio.run(reviewer.review({"total": 2566.57}))
        assert result.skipped is True
        assert result.findings == []

    def test_calls_chat_and_parses_findings(self) -> None:
        stub = _StubAI(
            '{"issues": [{"severity": "error", "message": "total implausible", "field": "total"}]}'
        )
        reviewer = AIReviewer(client=stub)
        result = asyncio.run(reviewer.review({"total": 999999}))
        assert result.skipped is False
        assert stub.calls == 1
        assert len(result.findings) == 1
        assert result.findings[0].severity == "error"
        assert result.findings[0].field == "total"

    def test_parse_non_json_returns_no_findings(self) -> None:
        assert AIReviewer._parse("this is not json") == []

    def test_parse_missing_issues_key_returns_empty(self) -> None:
        assert AIReviewer._parse('{"document_type": "invoice"}') == []

    def test_parse_ignores_non_dict_items(self) -> None:
        # The bare string "x" is ignored; the dict item becomes a finding.
        findings = AIReviewer._parse('{"issues": ["x", {"severity": "warning", "message": "m"}]}')
        assert len(findings) == 1
        assert findings[0].message == "m"

    def test_default_model_from_router(self) -> None:
        reviewer = AIReviewer(client=_Unconfigured())
        # REVIEW routes to mimo-v2.6-flash unless overridden by AI_REVIEW_MODEL.
        assert reviewer.model == "mimo-v2.6-flash"
