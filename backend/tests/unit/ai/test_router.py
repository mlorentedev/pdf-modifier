"""Tests for model router."""

from __future__ import annotations

import pytest

from pdf_modifier.ai.router import ModelRouter, TaskType


class TestModelRouter:
    """Model routing tests."""

    def test_default_vision_model(self) -> None:
        router = ModelRouter()
        assert router.get_model(TaskType.VISION) == "mimo-v2.6-flash"

    def test_default_classification_model(self) -> None:
        router = ModelRouter()
        assert router.get_model(TaskType.CLASSIFICATION) == "qwen3.6"

    def test_default_embedding_model(self) -> None:
        router = ModelRouter()
        assert router.get_model(TaskType.EMBEDDING) == "qwen3-embedding"

    def test_all_task_types_have_models(self) -> None:
        router = ModelRouter()
        for task_type in TaskType:
            model = router.get_model(task_type)
            assert isinstance(model, str)
            assert len(model) > 0

    def test_override_model(self) -> None:
        router = ModelRouter()
        router.set_model(TaskType.VISION, "custom-model")
        assert router.get_model(TaskType.VISION) == "custom-model"

    def test_fallback_chain(self) -> None:
        router = ModelRouter()
        chain = router.get_fallback_chain()
        assert chain == ["mimo-v2.6-flash", "qwen3.6", "gemma4"]

    def test_custom_routing(self) -> None:
        custom = {TaskType.VISION: "custom-vision"}
        router = ModelRouter(routing=custom)
        assert router.get_model(TaskType.VISION) == "custom-vision"
        # Other types should still use defaults
        assert router.get_model(TaskType.CLASSIFICATION) == "qwen3.6"

    def test_get_model_raises_for_missing(self) -> None:
        """Raising ValueError when no model configured for a task type."""
        # Pass None to use defaults, then remove the VISION entry
        router = ModelRouter()
        del router._routing[TaskType.VISION]
        with pytest.raises(ValueError, match="No model configured"):
            router.get_model(TaskType.VISION)

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AI_MODEL_VISION", "override-model")
        router = ModelRouter()
        assert router.get_model(TaskType.VISION) == "override-model"

    def test_env_override_classification(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AI_MODEL_CLASSIFICATION", "fast-model")
        router = ModelRouter()
        assert router.get_model(TaskType.CLASSIFICATION) == "fast-model"


# The routing table pinned per TASK, not spot-checked one task at a time.
#
# NaN retired `mimo-v2.5` on 2026-09-30 and it answered 401. The router still
# named it for VISION, TOOL_CALLING, REASONING and REVIEW, and headed the
# fallback chain -- and a 401 is fail-fast, so the chain never advanced: every
# one of those routes failed outright rather than degrading. Pinning every task
# is what makes the next retirement a one-line diff with a failing test instead
# of a 401 in production.
#
# This table is deliberately a second copy of the routing decision: it is the
# consumer-side expectation, and updating it is the edit that says "this model
# changed on purpose".
PINNED_ROUTING: dict[TaskType, str] = {
    TaskType.VISION: "mimo-v2.6-flash",
    TaskType.TOOL_CALLING: "mimo-v2.6-flash",
    TaskType.REASONING: "mimo-v2.6-flash",
    TaskType.CLASSIFICATION: "qwen3.6",
    TaskType.TRANSLATION: "qwen3.6",
    TaskType.SUMMARIZATION: "qwen3.6",
    TaskType.EMBEDDING: "qwen3-embedding",
    TaskType.RERANK: "rerank",
    TaskType.TTS: "kokoro",
    TaskType.STT: "whisper",
    TaskType.REVIEW: "mimo-v2.6-flash",
}

PINNED_FALLBACK_CHAIN = ["mimo-v2.6-flash", "qwen3.6", "gemma4"]


class TestPinnedRouting:
    """Every task's model is pinned, so a retirement cannot slip through a gap."""

    def test_every_task_type_has_a_pin(self) -> None:
        """A new task type must not escape the pin by being added to one table only."""
        assert set(PINNED_ROUTING) == set(TaskType)

    @pytest.mark.parametrize("task_type", sorted(PINNED_ROUTING, key=lambda t: t.value))
    def test_every_task_pins_its_model(self, task_type: TaskType) -> None:
        assert ModelRouter().get_model(task_type) == PINNED_ROUTING[task_type]

    def test_fallback_chain_is_pinned(self) -> None:
        assert ModelRouter().get_fallback_chain() == PINNED_FALLBACK_CHAIN

    def test_no_pinned_model_is_a_retired_one(self) -> None:
        """The retirement that caused this, named so it cannot come back."""
        retired = "mimo-v2.5"
        assert retired not in set(PINNED_ROUTING.values())
        assert retired not in PINNED_FALLBACK_CHAIN
