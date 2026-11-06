"""Build an LLM from config.toml and the secrets in .env."""

from __future__ import annotations

import sys
from typing import Any, Callable

from ..config import get_secret, load_config
from .base import LLMUnavailable
from .client import LLM
from .providers import GeminiProvider, GroqProvider

_KEY_NAMES = {"gemini": "GEMINI_API_KEY", "groq": "GROQ_API_KEY"}
_CLASSES = {"gemini": GeminiProvider, "groq": GroqProvider}


def build_llm(
    cfg: dict[str, Any] | None = None,
    *,
    only: str | None = None,
    prompt_guard: Callable[[str], None] | None = None,
    secret: Callable[[str], str | None] = get_secret,
    **llm_kwargs: Any,
) -> LLM:
    """Providers are tried in config order. One without a key is skipped.

    Only gemini and groq exist, both free. Anything else in the config is an
    error, so a paid provider cannot be added by accident (D-019).
    """
    cfg = cfg or load_config()
    llm_cfg = cfg["llm"]
    names = [only] if only else list(llm_cfg["providers"])

    providers = []
    for name in names:
        if name not in _CLASSES:
            raise ValueError(f"unknown provider '{name}'; allowed: {sorted(_CLASSES)}")
        key = secret(_KEY_NAMES[name])
        if not key:
            print(f"note: {_KEY_NAMES[name]} is not set; skipping {name}", file=sys.stderr)
            continue
        opts = llm_cfg.get(name, {})
        providers.append(
            _CLASSES[name](
                key,
                opts["model"],
                min_interval_s=float(opts.get("min_interval_s", 0.0)),
                temperature=opts.get("temperature", 0.0),
            )
        )
    if not providers:
        raise LLMUnavailable("no provider has an API key; fill in .env")

    llm_kwargs.setdefault("max_retries", int(llm_cfg.get("max_retries", 3)))
    return LLM(providers, prompt_guard=prompt_guard, **llm_kwargs)
