from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class EventStatus(str, Enum):
    STARTED = 'started'
    SUCCESS = 'success'
    INVALID = 'invalid'
    RETRY = 'retry'
    FALLBACK = 'fallback'
    ESCALATED = 'escalated'
    NEEDS_CLARIFICATION = 'needs_clarification'
    FAILED = 'failed'


class HarnessEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='ignore')

    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_id: str = Field(default_factory=lambda: str(uuid4()), alias='eventid')
    parent_event_id: Optional[str] = Field(default=None, alias='parenteventid')
    task_id: str = Field(..., alias='taskid')
    model_used: Optional[str] = Field(default=None, alias='modelused')
    role_used: Optional[str] = Field(default=None, alias='roleused')
    action: str
    status: EventStatus
    validation_passed: Optional[bool] = Field(default=None, alias='validationpassed')
    error_message: Optional[str] = Field(default=None, alias='errormessage')
    next_action: Optional[str] = Field(default=None, alias='nextaction')
    details: Dict[str, Any] = Field(default_factory=dict)
