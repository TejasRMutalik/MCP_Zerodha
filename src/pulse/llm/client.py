"""LLM.complete(): retry, pace, fail over, and never pay (D-022 rules 2, 6)."""

from __future__ import annotations

import json
import time
from typing import Any, Callable, Sequence

import jsonschema

from .base import LLMUnavailable, PromptBlocked, Provider, ProviderError


class LLM:
    def __init__(
        self,
        providers: Sequence[Provider],
        *,
        max_retries: int = 3,
        base_delay: float = 5.0,  # 5, 10, 20 seconds: long enough to outlast a per-minute window
        max_delay: float = 30.0,
        max_wait: float = 60.0,
        prompt_guard: Callable[[str], None] | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not providers:
            raise ValueError("at least one provider is required")
        self.providers = list(providers)
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        # A provider asking us to wait longer than this (for example until the
        # daily quota resets) is skipped instead of waited for.
        self.max_wait = max_wait
        self.prompt_guard = prompt_guard
        self._sleep = sleep
        self._clock = clock
        self._last_call: dict[str, float] = {}
        self.last_provider: str | None = None
        self.stats: dict[str, int] = {"calls": 0, "retries": 0, "failovers": 0}

    # -- public -----------------------------------------------------------
    def complete(self, prompt: str, schema: dict) -> Any:
        """Return parsed JSON that validates against `schema`, or raise."""
        if self.prompt_guard is not None:
            self.prompt_guard(prompt)  # raises PromptBlocked; nothing is sent

        failures: list[str] = []
        for index, provider in enumerate(self.providers):
            if index > 0:
                self.stats["failovers"] += 1
            try:
                result = self._try_provider(provider, prompt, schema)
            except ProviderError as exc:
                failures.append(f"{provider.name}: {exc}")
                continue
            self.last_provider = provider.name
            return result
        raise LLMUnavailable("all providers failed: " + "; ".join(failures))

    # -- internals --------------------------------------------------------
    def _pace(self, provider: Provider) -> None:
        gap = getattr(provider, "min_interval_s", 0.0) or 0.0
        last = self._last_call.get(provider.name)
        if gap > 0 and last is not None:
            wait = gap - (self._clock() - last)
            if wait > 0:
                self._sleep(wait)
        self._last_call[provider.name] = self._clock()

    def _try_provider(self, provider: Provider, prompt: str, schema: dict) -> Any:
        attempt = 0
        bad_output = 0
        while True:
            self._pace(provider)
            self.stats["calls"] += 1
            try:
                text = provider.generate(prompt, schema)
                data = json.loads(text)
                jsonschema.validate(data, schema)
                return data
            except ProviderError as exc:
                if not exc.retryable or attempt >= self.max_retries:
                    raise
                if exc.retry_after is not None:
                    if exc.retry_after > self.max_wait:
                        raise
                    delay = exc.retry_after
                else:
                    delay = min(self.max_delay, self.base_delay * (2**attempt))
                attempt += 1
                self.stats["retries"] += 1
                self._sleep(delay)
            except (json.JSONDecodeError, jsonschema.ValidationError) as exc:
                # One more try for malformed or off-schema output, then move on.
                if bad_output >= 1:
                    raise ProviderError(f"invalid output after retry: {type(exc).__name__}") from exc
                bad_output += 1
                self.stats["retries"] += 1


__all__ = ["LLM", "PromptBlocked"]
