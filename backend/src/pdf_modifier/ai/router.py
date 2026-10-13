"""Task-type to model routing with fallback chain."""

from __future__ import annotations

import os
from enum import StrEnum

from ..logger import setup_logging

logger = setup_logging(__name__)

# Fallback chain for main models
#
# Heads with `mimo-v2.6-flash`, the successor to `mimo-v2.5` that NaN retired on
# 2026-09-30: it hung, then answered 401, and every VISION, TOOL_CALLING,
# REASONING and REVIEW route failed outright. A 401 is fail-fast by policy, so
# this chain never advanced to `qwen3.6` -- the fallback could not save it.
FALLBACK_CHAIN: list[str] = ["mimo-v2.6-flash", "qwen3.6", "gemma4"]


class TaskType(StrEnum):
    """Types of AI tasks supported by the router."""

    VISION = "vision"
    TOOL_CALLING = "tool_calling"
    REASONING = "reasoning"
    CLASSIFICATION = "classification"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    EMBEDDING = "embedding"
    RERANK = "rerank"
    TTS = "tts"
    STT = "stt"
    REVIEW = "review"


# Default model mapping (defined after TaskType)
DEFAULT_ROUTING: dict[TaskType, str] = {
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


class ModelRouter:
    """Routes task types to appropriate AI models.

    Supports environment variable override via AI_MODEL_<TASKTYPE>.
    Example: AI_MODEL_VISION="custom-model" overrides the default for vision.

    Example:
        >>> router = ModelRouter()
        >>> model = router.get_model(TaskType.VISION)
        >>> print(model)  # "mimo-v2.6-flash"
    """

    def __init__(self, routing: dict[TaskType, str] | None = None) -> None:
        self._routing: dict[TaskType, str] = dict(DEFAULT_ROUTING)
        if routing:
            self._routing.update(routing)
        self._load_overrides()

    def _load_overrides(self) -> None:
        """Load model overrides from environment variables."""
        for task_type in TaskType:
            env_key = f"AI_MODEL_{task_type.value.upper()}"
            env_value = os.environ.get(env_key)
            if env_value:
                logger.info("Model override: %s -> %s", env_key, env_value)
                self._routing[task_type] = env_value

    def get_model(self, task_type: TaskType) -> str:
        """Get the model name for a given task type.

        Args:
            task_type: The task type to route.

        Returns:
            Model name string.

        Raises:
            ValueError: If no model is configured for the task type.
        """
        model = self._routing.get(task_type)
        if model is None:
            raise ValueError(f"No model configured for task type: {task_type.value}")
        return model

    def get_fallback_chain(self) -> list[str]:
        """Get the fallback model chain.

        Returns:
            Ordered list of model names to try.
        """
        return list(FALLBACK_CHAIN)

    def set_model(self, task_type: TaskType, model: str) -> None:
        """Override the model for a specific task type.

        Args:
            task_type: The task type to override.
            model: The model name to use.
        """
        self._routing[task_type] = model
