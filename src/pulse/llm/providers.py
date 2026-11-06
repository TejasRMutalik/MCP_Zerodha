"""Gemini and Groq providers, called over plain HTTP.

Plain HTTP (httpx) keeps the dependencies small and avoids Google auth
libraries, so the "no direct Google API code" check can stay simple. Only the
Gemini text-generation endpoint is used; Docs, Drive and Gmail go through MCP.
"""

from __future__ import annotations

from typing import Any

import httpx

from .base import ProviderError

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
GROQ_BASE = "https://api.groq.com/openai/v1"

_RATE_PREFIXES = ("x-ratelimit", "retry-after")


def _retry_after(resp: httpx.Response) -> float | None:
    value = resp.headers.get("retry-after")
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


def _rate_headers(resp: httpx.Response) -> dict[str, str]:
    return {k: v for k, v in resp.headers.items() if k.lower().startswith(_RATE_PREFIXES)}


def _raise_for_status(resp: httpx.Response) -> None:
    if resp.status_code < 400:
        return
    retryable = resp.status_code in (408, 429) or resp.status_code >= 500
    raise ProviderError(
        f"HTTP {resp.status_code}: {resp.text[:200]}",
        status=resp.status_code,
        retryable=retryable,
        retry_after=_retry_after(resp),
    )


class _HttpProvider:
    name = ""

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        client: httpx.Client | None = None,
        min_interval_s: float = 0.0,
        temperature: float | None = 0.0,
        timeout: float = 90.0,
    ) -> None:
        self._api_key = api_key
        self.model = model
        self.min_interval_s = min_interval_s
        self.temperature = temperature
        self._client = client or httpx.Client(timeout=timeout)
        self.last_headers: dict[str, str] = {}

    def __repr__(self) -> str:  # never include the key
        return f"{type(self).__name__}(model={self.model!r})"

    def _post(self, url: str, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
        try:
            resp = self._client.post(url, headers=headers, json=body)
        except httpx.TimeoutException as exc:
            raise ProviderError("request timed out", retryable=True) from exc
        except httpx.TransportError as exc:
            raise ProviderError(f"network error: {type(exc).__name__}", retryable=True) from exc
        self.last_headers = _rate_headers(resp)
        _raise_for_status(resp)
        try:
            return resp.json()
        except ValueError as exc:
            raise ProviderError("response was not JSON") from exc


class GeminiProvider(_HttpProvider):
    name = "gemini"

    def generate(self, prompt: str, schema: dict) -> str:
        config: dict[str, Any] = {
            "responseMimeType": "application/json",
            "responseJsonSchema": schema,
        }
        if self.temperature is not None:
            config["temperature"] = self.temperature
        body = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": config,
        }
        data = self._post(
            f"{GEMINI_BASE}/models/{self.model}:generateContent",
            {"x-goog-api-key": self._api_key},
            body,
        )
        candidates = data.get("candidates") or []
        if not candidates:
            raise ProviderError(f"no candidates returned: {data.get('promptFeedback')}")
        parts = (candidates[0].get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        if not text:
            raise ProviderError(f"empty response, finishReason={candidates[0].get('finishReason')}")
        return text


class GroqProvider(_HttpProvider):
    name = "groq"

    def __init__(self, *args: Any, strict: bool = True, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.strict = strict

    def generate(self, prompt: str, schema: dict) -> str:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "result", "strict": self.strict, "schema": schema},
            },
        }
        if self.temperature is not None:
            body["temperature"] = self.temperature
        data = self._post(
            f"{GROQ_BASE}/chat/completions",
            {"Authorization": f"Bearer {self._api_key}"},
            body,
        )
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("unexpected response shape") from exc
        if not text:
            raise ProviderError("empty response")
        return text
