from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class TaskType(str, Enum):
    GENERAL = "general"
    RESEARCH = "research"
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
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    task_id: str = Field(..., min_length=3, alias="taskid")
    user_goal: str = Field(..., min_length=3, alias="usergoal")
    task_type: TaskType = Field(default=TaskType.GENERAL, alias="tasktype")
    constraints: List[str] = Field(default_factory=list)
    expected_output: str = Field(default="general_result", alias="expectedoutput")
    confidence_required: float = Field(default=0.98, ge=0.0, le=1.0, alias="confidencerequired")
    status: TaskStatus = Field(default=TaskStatus.QUEUED, alias="status")
