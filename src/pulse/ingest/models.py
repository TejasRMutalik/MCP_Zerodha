"""Phase 1 A: Ingestion models.

IngestedReview captures the allowlisted fields (D-008).
Identifying fields (author, username, avatar, reviewId, link) are strictly forbidden (C4).
"""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class IngestedReview(BaseModel):
    """Raw review row before PII scrubbing and theme assignment.
    
    extra='forbid' guarantees identifying fields are rejected immediately (C4).
    """
    model_config = ConfigDict(extra="forbid")

    store: Literal["app_store", "play_store"]
    rating: int = Field(ge=1, le=5)
    title: str = ""
    text: str = Field(min_length=1)
    date: dt.date
