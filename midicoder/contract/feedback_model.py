from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class FeedbackMeta(BaseModel):
    version: str
    author: str
    created_at: str
    scope: str

    model_config = {"extra": "forbid"}


class FeedbackItem(BaseModel):
    id: str
    file: str
    location: str
    status: Literal["pending", "in_progress", "done", "error"]
    issue: str
    suggestion: str | None = None
    last_error: str | None = None

    model_config = {"extra": "forbid"}


class FeedbackFile(BaseModel):
    meta: FeedbackMeta
    items: list[FeedbackItem]
    notes: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}
