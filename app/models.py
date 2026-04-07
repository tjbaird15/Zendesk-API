from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message line in a chat transcript."""

    sender: str
    timestamp: datetime | None = None
    text: str


class ChatTranscript(BaseModel):
    """Normalized transcript for one Zendesk chat session."""

    chat_id: str
    created_at: datetime | None = None
    customer_id: str | None = None
    messages: list[ChatMessage] = Field(default_factory=list)


class AuditResult(BaseModel):
    """OpenAI quality-audit result for one chat transcript."""

    chat_id: str
    flag: bool
    issue_type: Literal[
        "dissatisfied_customer",
        "poor_service",
        "both",
        "none",
    ]
    severity: int = Field(ge=1, le=5)
    reason: str
    coaching_tip: str


class AuditResponse(BaseModel):
    """Batch response returned by the API."""

    audited_count: int
    flagged_count: int
    flagged_items: list[AuditResult]
