from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class EventStatus(str, Enum):
    STARTED = "started"
    SUCCESS = "success"
    INVALID = "invalid"
    RETRY = "retry"
    FALLBACK = "fallback"
    ESCALATED = "escalated"
    NEEDS_CLARIFICATION = "needs_clarification"
    FAILED = "failed"


class HarnessEvent(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    parent_event_id: Optional[str] = None
    task_id: str
    model_used: Optional[str] = None
    role_used: Optional[str] = None
    action: str
    status: EventStatus
    validation_passed: Optional[bool] = None
    error_message: Optional[str] = None
    next_action: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
