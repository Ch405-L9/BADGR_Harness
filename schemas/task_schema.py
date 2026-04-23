from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    GENERAL = "general"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    CODE = "code"
    SUMMARIZATION = "summarization"
    PLANNING = "planning"


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    NEEDS_CLARIFICATION = "needs_clarification"
    FAILED = "failed"


class Task(BaseModel):
    task_id: str = Field(..., min_length=3)
    user_goal: str = Field(..., min_length=3)
    task_type: TaskType = TaskType.GENERAL
    constraints: List[str] = Field(default_factory=list)
    expected_output: str = Field(default="general_result")
    confidence_required: float = Field(default=0.98, ge=0.0, le=1.0)
    status: TaskStatus = TaskStatus.QUEUED
