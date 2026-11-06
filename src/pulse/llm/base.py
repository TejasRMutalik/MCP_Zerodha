"""Errors and the provider interface for the swappable LLM layer (D-020, D-022)."""

from __future__ import annotations

from typing import Protocol


class LLMError(Exception):
    """Base class for everything this package raises on purpose."""


class PromptBlocked(LLMError):
    """The prompt guard refused to send this text (for example, PII was found)."""


class LLMUnavailable(LLMError):
    """Every configured provider failed. Never fall back to a paid service."""


class ProviderError(LLMError):
    """One provider failed. `retryable` says whether trying it again can help."""

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        retryable: bool = False,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.retryable = retryable
        self.retry_after = retry_after


class Provider(Protocol):
    name: str
    min_interval_s: float

    def generate(self, prompt: str, schema: dict) -> str:
        """Return the model's raw JSON text for `prompt`, shaped by `schema`."""
        ...
