"""NaN Cloud API client using httpx async + null client for testing."""

from __future__ import annotations

import os
from typing import Any

import httpx

from ..logger import setup_logging
from .exceptions import AIAuthenticationError, AIError, AIRateLimitError, AIServerError

logger = setup_logging(__name__)

DEFAULT_BASE_URL = "https://api.nan.builders/v1"
DEFAULT_TIMEOUT = 30.0


class NaNClient:
    """Async HTTP client for NaN Cloud API.

    Handles authentication, rate limiting retries, and error mapping.

    Example:
        >>> async with NaNClient() as client:
        ...     msgs = [{"role": "user", "content": "Hello"}]
        ...     result = await client.chat("mimo-v2.6-flash", msgs)
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 3,
    ) -> None:
        # Accept either NaN Cloud or any OpenAI-compatible provider so the AI
        # features work for more people. NaN key wins when both are present.
        nan_key = os.environ.get("NAN_API_KEY")
        openai_key = os.environ.get("OPENAI_API_KEY")
        self._api_key = api_key or nan_key or openai_key or ""
        # Base URL: explicit > NAN_BASE_URL > OPENAI_BASE_URL > provider default.
        raw_url: str | None = (
            base_url or os.environ.get("NAN_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
        )
        if raw_url is None:
            if nan_key:
                raw_url = DEFAULT_BASE_URL
            elif openai_key:
                raw_url = "https://api.openai.com/v1"
            else:
                raw_url = DEFAULT_BASE_URL
        self._base_url = (raw_url or DEFAULT_BASE_URL).rstrip("/")
        self._is_nan = bool(nan_key)
        self._timeout = timeout
        self._max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    @property
    def is_configured(self) -> bool:
        """Whether an API key is available."""
        return bool(self._api_key)

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy-initialize the httpx client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        **extra_kwargs: Any,
    ) -> dict[str, Any]:
        """Send a chat completion request to NaN Cloud."""
        client = await self._get_client()

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "chat_template_kwargs": {"enable_thinking": False},
            **extra_kwargs,
        }

        last_exception: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                response = await client.post("/chat/completions", json=payload)

                if response.status_code == 401:
                    raise AIAuthenticationError("Invalid API key")
                if response.status_code == 429:
                    raise AIRateLimitError(
                        f"Rate limit exceeded (attempt {attempt + 1}/{self._max_retries})"
                    )
                if response.status_code >= 500:
                    raise AIServerError(f"Server error: {response.status_code}")
                response.raise_for_status()

                data: dict[str, Any] = response.json()
                logger.debug("AI chat completed for model=%s", model)
                return data

            except (AIAuthenticationError, AIError):
                raise
            except httpx.HTTPStatusError:
                raise
            except httpx.RequestError as e:
                last_exception = e
                logger.warning(
                    "AI chat attempt %d/%d failed for model=%s: %s",
                    attempt + 1,
                    self._max_retries,
                    model,
                    e,
                )
                if attempt < self._max_retries - 1:
                    import asyncio

                    await asyncio.sleep(2**attempt)

        if last_exception:
            raise last_exception
        raise AIError("Chat request failed after retries")

    async def embed(
        self,
        model: str,
        input_text: str | list[str],
    ) -> dict[str, Any]:
        """Send an embedding request with retry logic."""
        client = await self._get_client()

        payload = {
            "model": model,
            "input": input_text,
        }

        last_exception: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                response = await client.post("/embeddings", json=payload)

                if response.status_code == 401:
                    raise AIAuthenticationError("Invalid API key")
                if response.status_code == 429:
                    raise AIRateLimitError(
                        f"Rate limit exceeded (attempt {attempt + 1}/{self._max_retries})"
                    )
                if response.status_code >= 500:
                    raise AIServerError(f"Server error: {response.status_code}")
                response.raise_for_status()

                data: dict[str, Any] = response.json()
                logger.debug("AI embed completed for model=%s", model)
                return data

            except (AIAuthenticationError, AIError):
                raise
            except httpx.HTTPStatusError:
                raise
            except httpx.RequestError as e:
                last_exception = e
                logger.warning(
                    "AI embed attempt %d/%d failed for model=%s: %s",
                    attempt + 1,
                    self._max_retries,
                    model,
                    e,
                )
                if attempt < self._max_retries - 1:
                    import asyncio

                    await asyncio.sleep(2**attempt)

        if last_exception:
            raise last_exception
        raise AIError("Embed request failed after retries")

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> NaNClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()


class NullAIClient:
    """Mock AI client that returns predefined responses.

    Used in unit tests to avoid real API calls.
    """

    def __init__(self) -> None:
        self._call_count = 0
        self._responses: dict[str, dict[str, Any]] = {
            "chat": {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"fields": [{'
                                '"name": "invoice_number", '
                                '"value": "INV-2024-001", '
                                '"confidence": 0.95}], '
                                '"document_type": "invoice"}'
                            )
                        }
                    }
                ]
            },
            "classify": {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"document_type": "invoice", '
                                '"confidence": 0.92, '
                                '"alternatives": [{'
                                '"type": "receipt", '
                                '"confidence": 0.05}]}'
                            )
                        }
                    }
                ]
            },
            "redact": {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"items": [{'
                                '"pii_type": "email", '
                                '"value": "test@example.com", '
                                '"suggested_replacement": "[REDACTED]"}]}'
                            )
                        }
                    }
                ]
            },
        }

    @property
    def is_configured(self) -> bool:
        return True

    @property
    def call_count(self) -> int:
        return self._call_count

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        **extra_kwargs: Any,
    ) -> dict[str, Any]:
        self._call_count += 1
        return self._responses["chat"]

    async def embed(
        self,
        model: str,
        input_text: str | list[str],
    ) -> dict[str, Any]:
        self._call_count += 1
        return {
            "data": [{"embedding": [0.1] * 1536}],
            "model": model,
        }

    async def close(self) -> None:
        pass

    async def __aenter__(self) -> NullAIClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
