"""Phase 2 A: PII models.

Defines PIIMatch representing an identified piece of personal or identifying information.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PIIMatch:
    """A detected PII instance in text."""

    type: str  # 'email', 'phone', 'pan', 'upi', 'client_id', 'demat_account', 'url', 'handle'
    text: str
    start: int
    end: int

    def __str__(self) -> str:
        return self.text
