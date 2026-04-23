from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field


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
    model_config = ConfigDict(populate_by_name=True)

    task_id: str = Field(..., min_length=3, alias="taskid")
    user_goal: str = Field(..., min_length=3, alias="usergoal")
    tasktype: TaskType = TaskType.GENERAL
    constraints: List[str] = Field(default_factory=list)
    expectedoutput: str = Field(default="generalresult")
    confidencerequired: float = Field(default=0.98, ge=0.0, le=1.0)
    status: TaskStatus = TaskStatus.QUEUED

    @property
    def taskid(self) -> str:
        return self.task_id

    @property
    def usergoal(self) -> str:
        return self.user_goal

    @property
    def task_type(self) -> TaskType:
        return self.tasktype

    @property
    def expected_output(self) -> str:
        return self.expectedoutput

    @property
    def confidence_required(self) -> float:
        return self.confidencerequired
