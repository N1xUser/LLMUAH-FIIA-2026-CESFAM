from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.domain.entities.message import Message


class Conversation(BaseModel):


    id: str | None = None
    channel: str  
    external_user_id: str  
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
