from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError

try:
    from schemas.task_schema import Task, TaskType
except ImportError:
    from schemas.taskschema import Task, TaskType


class ValidationOutcome(BaseModel):
    valid: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BaseWorkerResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    task_type: str = Field(..., alias="tasktype")
    summary: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    recommended_action: str = Field(..., min_length=1, alias="recommendedaction")
    needs_clarification: bool = Field(False, alias="needsclarification")
    clarification_question: Optional[str] = Field(None, alias="clarificationquestion")


class CodeWorkerResponse(BaseWorkerResponse):
    changes: list[str] = Field(default_factory=list)
    code_block: Optional[str] = Field(None)


class ClassificationWorkerResponse(BaseWorkerResponse):
    labels: list[str] = Field(default_factory=list)


class ExtractionWorkerResponse(BaseWorkerResponse):
    fields: Dict[str, Any] = Field(default_factory=dict)


class SummarizationWorkerResponse(BaseWorkerResponse):
    key_points: list[str] = Field(default_factory=list)


class PlanningWorkerResponse(BaseWorkerResponse):
    steps: list[str] = Field(default_factory=list)


def _strip_code_fences(raw_output: str) -> str:
    text = (raw_output or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _extract_json_object(raw_output: str) -> str:
    text = _strip_code_fences(raw_output)
    if text.startswith("{") and text.endswith("}"):
        return text

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def parse_json(raw_output: str) -> Dict[str, Any]:
    return json.loads(_extract_json_object(raw_output))


def _task_attr(task: Task, *names: str, default: Any = None) -> Any:
    for name in names:
        if hasattr(task, name):
            return getattr(task, name)
    return default


def _task_type_value(task: Task) -> str:
    value = _task_attr(task, "task_type", "tasktype")
    return value.value if hasattr(value, "value") else str(value)


def _required_confidence(task: Task) -> float:
    value = _task_attr(task, "confidence_required", "confidencerequired", default=0.98)
    return float(value)


def validate_worker_output(task: Task, raw_output: str) -> ValidationOutcome:
    try:
        parsed = parse_json(raw_output)
    except json.JSONDecodeError as exc:
        return ValidationOutcome(valid=False, error=f"Invalid JSON: {exc}")

    try:
        expected_type = _task_type_value(task)

        if expected_type == TaskType.CODE.value:
            response = CodeWorkerResponse.model_validate(parsed)
        elif expected_type == TaskType.CLASSIFICATION.value:
            response = ClassificationWorkerResponse.model_validate(parsed)
        elif expected_type == TaskType.EXTRACTION.value:
            response = ExtractionWorkerResponse.model_validate(parsed)
        elif expected_type == TaskType.SUMMARIZATION.value:
            response = SummarizationWorkerResponse.model_validate(parsed)
        elif expected_type == TaskType.PLANNING.value:
            response = PlanningWorkerResponse.model_validate(parsed)
        else:
            response = BaseWorkerResponse.model_validate(parsed)

        data = response.model_dump()
    except ValidationError as exc:
        return ValidationOutcome(valid=False, error=str(exc))

    if data["task_type"] != expected_type:
        return ValidationOutcome(valid=False, error="Task type mismatch")

    if data["confidence"] < _required_confidence(task) and not data.get("needs_clarification", False):
        return ValidationOutcome(valid=False, error="Confidence below required threshold.")

    if data.get("needs_clarification") and not (data.get("clarification_question") or "").strip():
        return ValidationOutcome(valid=False, error="clarification_question required")

    if expected_type == TaskType.CLASSIFICATION.value and not data.get("labels"):
        return ValidationOutcome(valid=False, error="at least one label is required")

    if expected_type == TaskType.SUMMARIZATION.value and not data.get("key_points"):
        return ValidationOutcome(valid=False, error="at least one key_point is required")

    if expected_type == TaskType.PLANNING.value and not data.get("steps"):
        return ValidationOutcome(valid=False, error="at least one step is required")

    return ValidationOutcome(valid=True, data=data)


parsejson = parse_json
validateworkeroutput = validate_worker_output
