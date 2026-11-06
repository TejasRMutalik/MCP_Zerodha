"""Swappable LLM interface. Gemini first, Groq as backup, never paid (D-022)."""

from .base import LLMError, LLMUnavailable, PromptBlocked, Provider, ProviderError
from .batch import ResultCache, chunks, run_batched
from .client import LLM
from .factory import build_llm
from .providers import GeminiProvider, GroqProvider

__all__ = [
    "LLM",
    "LLMError",
    "LLMUnavailable",
    "PromptBlocked",
    "Provider",
    "ProviderError",
    "GeminiProvider",
    "GroqProvider",
    "ResultCache",
    "build_llm",
    "chunks",
    "run_batched",
]
