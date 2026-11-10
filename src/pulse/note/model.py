"""B2.3: the structured note. The LLM fills this; Python renders it."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ThemeLine(BaseModel):
    model_config = ConfigDict(extra="forbid")
    theme: str
    summary: str = Field(min_length=1)


class ActionIdea(BaseModel):
    model_config = ConfigDict(extra="forbid")
    theme: str
    action: str = Field(min_length=1)


class NoteContent(BaseModel):
    """Exactly 3 of each. Quotes are IDs from the eligible list, never text."""

    model_config = ConfigDict(extra="forbid")
    themes: list[ThemeLine] = Field(min_length=3, max_length=3)
    quote_ids: list[str] = Field(min_length=3, max_length=3)
    actions: list[ActionIdea] = Field(min_length=3, max_length=3)


# JSON schema sent to the LLM (kept simple: strict-mode providers dislike $ref).
NOTE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["themes", "quote_ids", "actions"],
    "properties": {
        "themes": {
            "type": "array", "minItems": 3, "maxItems": 3,
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["theme", "summary"],
                "properties": {"theme": {"type": "string"}, "summary": {"type": "string"}},
            },
        },
        "quote_ids": {"type": "array", "minItems": 3, "maxItems": 3, "items": {"type": "string"}},
        "actions": {
            "type": "array", "minItems": 3, "maxItems": 3,
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["theme", "action"],
                "properties": {"theme": {"type": "string"}, "action": {"type": "string"}},
            },
        },
    },
}
