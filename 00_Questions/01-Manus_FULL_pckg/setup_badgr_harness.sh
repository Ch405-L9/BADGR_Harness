#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${HOME}/projects/badgr_harness"
TODAY="$(date +%F)"

mkdir -p "$PROJECT_ROOT"
cd "$PROJECT_ROOT"

python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip
pip install pydantic pyyaml langgraph langchain litellm python-dotenv jsonschema mcp pytest

mkdir -p prompts schemas logs reports state examples tests

cat > .env <<'EOF'
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_TIMEOUT_SECONDS=120
DEFAULT_LOG_LEVEL=INFO
EOF

cat > .env.example <<'EOF'
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_TIMEOUT_SECONDS=120
DEFAULT_LOG_LEVEL=INFO
EOF

cat > README.md <<'EOF'
# BADGR Harness

Strict local LLM harness starter with routing, validation, fallback, and logs.

## What this builds first
- A model registry (`models.yaml`)
- Typed schemas for tasks and logs (`schemas/`)
- A rule-based router (`router.py`)
- A validator for worker JSON output (`validator.py`)
- A simple orchestrator loop for retry, fallback, escalation, logging, and reports (`orchestrator.py`)

## Live workflow
1. User makes request.
2. Harness converts it into a structured task object.
3. Router classifies the task.
4. Router picks the cheapest capable model.
5. Worker model runs.
6. Validator checks the output against schema.
7. If valid, return result and log success.
8. If invalid, retry once.
9. If still invalid, send to fallback model.
10. If fallback fails, escalate to supervisor model.
11. If supervisor still lacks clarity, ask the human a short question.
12. Write all steps to log.
13. Add summary to daily report.

## Starter models
- Supervisor: `qwen2.5:14b`
- Code worker: `qwen2.5-coder:7b`
- General fallback: `mistral:7b`
- Optional emergency cloud fallback: `kimi-k2.5:cloud`

## Setup
```bash
source .venv/bin/activate
python -m pytest -q
python orchestrator.py --goal "Classify this request and return strict JSON"
```
EOF

cat > requirements.txt <<'EOF'
pydantic
pyyaml
langgraph
langchain
litellm
python-dotenv
jsonschema
mcp
pytest
EOF

cat > models.yaml <<'EOF'
models:
  qwen_supervisor:
    provider: ollama
    model_name: qwen2.5:14b
    roles:
      - supervisor
      - planner
      - synthesizer
      - escalation
    strengths:
      - long_context_reasoning
      - structured_output
      - synthesis
      - recovery
    weaknesses:
      - slower_than_7b_models
      - higher_local_resource_use
    temperature: 0.2
    max_tokens: 2400
    timeout_seconds: 180
    fallback: null

  qwen_coder_worker:
    provider: ollama
    model_name: qwen2.5-coder:7b
    roles:
      - code
      - extraction
      - classification
      - formatting
    strengths:
      - code_generation
      - code_editing
      - json_friendly
      - fast_enough
    weaknesses:
      - weaker_on_ambiguous_planning
    temperature: 0.1
    max_tokens: 1600
    timeout_seconds: 120
    fallback: mistral_worker

  mistral_worker:
    provider: ollama
    model_name: mistral:7b
    roles:
      - general
      - fallback
      - extraction
      - summarization
      - classification
    strengths:
      - instruction_following
      - solid_fallback
      - cheap_local_backup
    weaknesses:
      - weaker_than_supervisor_on_complex_synthesis
    temperature: 0.1
    max_tokens: 1600
    timeout_seconds: 120
    fallback: qwen_supervisor

  kimi_cloud_emergency:
    provider: ollama
    model_name: kimi-k2.5:cloud
    roles:
      - emergency
      - external_fallback
    strengths:
      - extra_fallback
    weaknesses:
      - external_dependency
    temperature: 0.2
    max_tokens: 2400
    timeout_seconds: 180
    fallback: null
EOF

cat > config.py <<'EOF'
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_TIMEOUT_SECONDS = int(os.getenv("DEFAULT_TIMEOUT_SECONDS", "120"))
DEFAULT_LOG_LEVEL = os.getenv("DEFAULT_LOG_LEVEL", "INFO")

PROMPTS_DIR = BASE_DIR / "prompts"
SCHEMAS_DIR = BASE_DIR / "schemas"
LOGS_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports"
STATE_DIR = BASE_DIR / "state"
EXAMPLES_DIR = BASE_DIR / "examples"
MODELS_FILE = BASE_DIR / "models.yaml"
EOF

cat > prompts/worker_system.txt <<'EOF'
You are the primary local worker inside a strict harness.

Rules:
- Return valid JSON only.
- Do not add markdown fences.
- Do not explain outside the JSON.
- Follow the requested schema exactly.
- If uncertain, say so inside the JSON and keep confidence honest.
EOF

cat > prompts/fallback_system.txt <<'EOF'
You are the fallback local worker inside a strict harness.

Rules:
- Return valid JSON only.
- Do not add markdown fences.
- Repair malformed reasoning from prior attempts.
- Be conservative.
- If uncertain, say so inside the JSON and keep confidence honest.
EOF

cat > prompts/supervisor_system.txt <<'EOF'
You are the supervisor model inside a strict harness.

Rules:
- Return valid JSON only.
- Do not add markdown fences.
- Synthesize the failed attempts and produce the cleanest valid answer possible.
- If the task still lacks enough clarity, return a short clarification question in the JSON.
- Keep confidence honest.
EOF

cat > schemas/task_schema.py <<'EOF'
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
EOF

cat > schemas/log_schema.py <<'EOF'
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
EOF

cat > router.py <<'EOF'
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from schemas.task_schema import TaskType


KEYWORD_MAP = {
    TaskType.CODE: ["code", "bug", "fix", "function", "refactor", "python", "script", "syntax"],
    TaskType.CLASSIFICATION: ["classify", "category", "categorize", "route", "label", "tag"],
    TaskType.EXTRACTION: ["extract", "pull", "find fields", "parse", "collect"],
    TaskType.SUMMARIZATION: ["summarize", "summary", "shorten", "condense"],
    TaskType.PLANNING: ["plan", "design", "architecture", "roadmap", "strategy"],
}


def load_model_registry(models_file: Path) -> Dict[str, Any]:
    with models_file.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data.get("models", {})


def classify_task(user_goal: str) -> TaskType:
    text = user_goal.lower()
    for task_type, keywords in KEYWORD_MAP.items():
        if any(keyword in text for keyword in keywords):
            return task_type
    return TaskType.GENERAL


def choose_primary_model(task_type: TaskType, registry: Dict[str, Any]) -> str:
    if task_type == TaskType.CODE:
        return registry["qwen_coder_worker"]["model_name"]
    if task_type in {TaskType.PLANNING, TaskType.SUMMARIZATION}:
        return registry["qwen_supervisor"]["model_name"]
    return registry["mistral_worker"]["model_name"]


def choose_fallback_model(primary_model_name: str, registry: Dict[str, Any]) -> str:
    for config in registry.values():
        if config["model_name"] == primary_model_name:
            fallback_key = config.get("fallback")
            if fallback_key and fallback_key in registry:
                return registry[fallback_key]["model_name"]
    return registry["qwen_supervisor"]["model_name"]


def choose_supervisor_model(registry: Dict[str, Any]) -> str:
    return registry["qwen_supervisor"]["model_name"]
EOF

cat > validator.py <<'EOF'
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ValidationError

from schemas.task_schema import Task, TaskType


class ValidationOutcome(BaseModel):
    valid: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BaseWorkerResponse(BaseModel):
    task_type: str
    summary: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    recommended_action: str = Field(..., min_length=1)
    needs_clarification: bool = False
    clarification_question: Optional[str] = None


class CodeWorkerResponse(BaseWorkerResponse):
    changes: list[str] = Field(default_factory=list)


class ClassificationWorkerResponse(BaseWorkerResponse):
    labels: list[str] = Field(default_factory=list)


class ExtractionWorkerResponse(BaseWorkerResponse):
    fields: Dict[str, Any] = Field(default_factory=dict)


def _parse_json(raw_output: str) -> Dict[str, Any]:
    return json.loads(raw_output.strip())


def validate_worker_output(task: Task, raw_output: str) -> ValidationOutcome:
    try:
        parsed = _parse_json(raw_output)
    except json.JSONDecodeError as exc:
        return ValidationOutcome(valid=False, error=f"Invalid JSON: {exc}")

    try:
        if task.task_type == TaskType.CODE:
            data = CodeWorkerResponse.model_validate(parsed).model_dump()
        elif task.task_type == TaskType.CLASSIFICATION:
            data = ClassificationWorkerResponse.model_validate(parsed).model_dump()
        elif task.task_type == TaskType.EXTRACTION:
            data = ExtractionWorkerResponse.model_validate(parsed).model_dump()
        else:
            data = BaseWorkerResponse.model_validate(parsed).model_dump()
    except ValidationError as exc:
        return ValidationOutcome(valid=False, error=str(exc))

    if data["confidence"] < task.confidence_required and not data.get("needs_clarification", False):
        return ValidationOutcome(valid=False, error="Confidence below required threshold.")

    return ValidationOutcome(valid=True, data=data)
EOF

cat > orchestrator.py <<'EOF'
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from urllib import error, request

from config import LOGS_DIR, MODELS_FILE, OLLAMA_BASE_URL, PROMPTS_DIR, REPORTS_DIR
from router import (
    choose_fallback_model,
    choose_primary_model,
    choose_supervisor_model,
    classify_task,
    load_model_registry,
)
from schemas.log_schema import EventStatus, HarnessEvent
from schemas.task_schema import Task, TaskStatus, TaskType
from validator import ValidationOutcome, validate_worker_output


DEFAULT_CONSTRAINTS = ["strict_json", "ask_if_under_98_confident"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def next_task_id() -> str:
    return f"task_{utc_now().strftime('%Y%m%d%H%M%S')}"


def normalize_task(user_goal: str) -> Task:
    task_type = classify_task(user_goal)
    expected_output = {
        TaskType.CODE: "code_result",
        TaskType.CLASSIFICATION: "classification_result",
        TaskType.EXTRACTION: "extraction_result",
        TaskType.SUMMARIZATION: "summary_result",
        TaskType.PLANNING: "plan_result",
    }.get(task_type, "general_result")
    return Task(
        task_id=next_task_id(),
        user_goal=user_goal,
        task_type=task_type,
        constraints=DEFAULT_CONSTRAINTS,
        expected_output=expected_output,
        confidence_required=0.98,
        status=TaskStatus.QUEUED,
    )


def read_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").strip()


def build_prompt(task: Task, role_prompt: str, retry_note: str = "") -> str:
    schema_hint = {
        TaskType.CODE: '{"task_type":"code","summary":"...","confidence":0.99,"recommended_action":"...","needs_clarification":false,"clarification_question":null,"changes":["..."]}',
        TaskType.CLASSIFICATION: '{"task_type":"classification","summary":"...","confidence":0.99,"recommended_action":"...","needs_clarification":false,"clarification_question":null,"labels":["..."]}',
        TaskType.EXTRACTION: '{"task_type":"extraction","summary":"...","confidence":0.99,"recommended_action":"...","needs_clarification":false,"clarification_question":null,"fields":{"key":"value"}}',
    }.get(
        task.task_type,
        '{"task_type":"general","summary":"...","confidence":0.99,"recommended_action":"...","needs_clarification":false,"clarification_question":null}',
    )

    return (
        f"{role_prompt}\n\n"
        f"Task ID: {task.task_id}\n"
        f"Task Type: {task.task_type.value}\n"
        f"Expected Output: {task.expected_output}\n"
        f"Constraints: {', '.join(task.constraints)}\n"
        f"Required Confidence: {task.confidence_required}\n"
        f"User Goal: {task.user_goal}\n"
        f"{retry_note}\n"
        f"Return valid JSON only using this exact shape:\n{schema_hint}\n"
    )


def call_ollama(model_name: str, prompt: str, timeout_seconds: int = 120) -> str:
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1},
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url=f"{OLLAMA_BASE_URL}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
    except error.URLError as exc:
        raise RuntimeError(f"Ollama request failed: {exc}") from exc
    return body.get("response", "")


def append_log(event: HarnessEvent) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"{utc_now().date().isoformat()}.jsonl"
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(event.model_dump_json() + "\n")


def append_report(task: Task, final_status: str, note: str) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / f"{utc_now().date().isoformat()}.md"
    if not report_file.exists():
        report_file.write_text("# Daily Harness Report\n\n", encoding="utf-8")
    with report_file.open("a", encoding="utf-8") as handle:
        handle.write(f"- {utc_now().isoformat()} | {task.task_id} | {final_status} | {note}\n")


def make_event(
    task: Task,
    action: str,
    status: EventStatus,
    model_used: Optional[str] = None,
    role_used: Optional[str] = None,
    validation_passed: Optional[bool] = None,
    error_message: Optional[str] = None,
    next_action: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    parent_event_id: Optional[str] = None,
) -> HarnessEvent:
    event = HarnessEvent(
        task_id=task.task_id,
        model_used=model_used,
        role_used=role_used,
        action=action,
        status=status,
        validation_passed=validation_passed,
        error_message=error_message,
        next_action=next_action,
        details=details or {},
        parent_event_id=parent_event_id,
    )
    append_log(event)
    return event


def attempt_model(task: Task, model_name: str, prompt_file: str, retry_note: str = "") -> ValidationOutcome:
    role_prompt = read_prompt(prompt_file)
    prompt = build_prompt(task, role_prompt, retry_note=retry_note)
    raw_output = call_ollama(model_name, prompt)
    return validate_worker_output(task, raw_output)


def run_task(user_goal: str) -> Dict[str, Any]:
    registry = load_model_registry(MODELS_FILE)
    task = normalize_task(user_goal)
    task.status = TaskStatus.RUNNING

    start_event = make_event(
        task=task,
        action="task_started",
        status=EventStatus.STARTED,
        next_action="route_primary_model",
        details={"task_type": task.task_type.value},
    )

    primary_model = choose_primary_model(task.task_type, registry)
    primary_event = make_event(
        task=task,
        action="primary_model_selected",
        status=EventStatus.STARTED,
        model_used=primary_model,
        role_used="worker",
        next_action="run_primary_attempt",
        parent_event_id=start_event.event_id,
    )

    first_try = attempt_model(task, primary_model, "worker_system.txt")
    if first_try.valid:
        task.status = TaskStatus.SUCCESS
        make_event(
            task=task,
            action="primary_attempt_valid",
            status=EventStatus.SUCCESS,
            model_used=primary_model,
            role_used="worker",
            validation_passed=True,
            next_action="return_result",
            parent_event_id=primary_event.event_id,
        )
        append_report(task, "success", f"Primary model succeeded: {primary_model}")
        return first_try.data or {}

    retry_event = make_event(
        task=task,
        action="primary_attempt_invalid",
        status=EventStatus.RETRY,
        model_used=primary_model,
        role_used="worker",
        validation_passed=False,
        error_message=first_try.error,
        next_action="retry_primary_once",
        parent_event_id=primary_event.event_id,
    )

    second_try = attempt_model(
        task,
        primary_model,
        "worker_system.txt",
        retry_note="Retry note: your prior answer failed validation. Return only valid JSON in the exact shape required.",
    )
    if second_try.valid:
        task.status = TaskStatus.SUCCESS
        make_event(
            task=task,
            action="primary_retry_valid",
            status=EventStatus.SUCCESS,
            model_used=primary_model,
            role_used="worker",
            validation_passed=True,
            next_action="return_result",
            parent_event_id=retry_event.event_id,
        )
        append_report(task, "success", f"Primary retry succeeded: {primary_model}")
        return second_try.data or {}

    fallback_model = choose_fallback_model(primary_model, registry)
    fallback_event = make_event(
        task=task,
        action="fallback_model_selected",
        status=EventStatus.FALLBACK,
        model_used=fallback_model,
        role_used="fallback",
        validation_passed=False,
        error_message=second_try.error,
        next_action="run_fallback_attempt",
        parent_event_id=retry_event.event_id,
    )

    fallback_try = attempt_model(
        task,
        fallback_model,
        "fallback_system.txt",
        retry_note="Fallback note: repair the failed attempts and return valid JSON only.",
    )
    if fallback_try.valid:
        task.status = TaskStatus.SUCCESS
        make_event(
            task=task,
            action="fallback_valid",
            status=EventStatus.SUCCESS,
            model_used=fallback_model,
            role_used="fallback",
            validation_passed=True,
            next_action="return_result",
            parent_event_id=fallback_event.event_id,
        )
        append_report(task, "success", f"Fallback model succeeded: {fallback_model}")
        return fallback_try.data or {}

    supervisor_model = choose_supervisor_model(registry)
    supervisor_event = make_event(
        task=task,
        action="supervisor_selected",
        status=EventStatus.ESCALATED,
        model_used=supervisor_model,
        role_used="supervisor",
        validation_passed=False,
        error_message=fallback_try.error,
        next_action="run_supervisor_attempt",
        parent_event_id=fallback_event.event_id,
    )

    supervisor_try = attempt_model(
        task,
        supervisor_model,
        "supervisor_system.txt",
        retry_note="Supervisor note: failed worker attempts require synthesis or a short clarification question.",
    )
    if supervisor_try.valid:
        data = supervisor_try.data or {}
        if data.get("needs_clarification"):
            task.status = TaskStatus.NEEDS_CLARIFICATION
            clarification = data.get("clarification_question") or "Please clarify the goal in one short sentence."
            make_event(
                task=task,
                action="clarification_required",
                status=EventStatus.NEEDS_CLARIFICATION,
                model_used=supervisor_model,
                role_used="supervisor",
                validation_passed=True,
                next_action="ask_human",
                details={"clarification_question": clarification},
                parent_event_id=supervisor_event.event_id,
            )
            append_report(task, "needs_clarification", clarification)
            return {"status": "needs_clarification", "question": clarification}

        task.status = TaskStatus.SUCCESS
        make_event(
            task=task,
            action="supervisor_valid",
            status=EventStatus.SUCCESS,
            model_used=supervisor_model,
            role_used="supervisor",
            validation_passed=True,
            next_action="return_result",
            parent_event_id=supervisor_event.event_id,
        )
        append_report(task, "success", f"Supervisor succeeded: {supervisor_model}")
        return data

    task.status = TaskStatus.FAILED
    make_event(
        task=task,
        action="task_failed",
        status=EventStatus.FAILED,
        model_used=supervisor_model,
        role_used="supervisor",
        validation_passed=False,
        error_message=supervisor_try.error,
        next_action="ask_human",
        parent_event_id=supervisor_event.event_id,
    )
    clarification = "I am not confident enough to continue. Please restate the goal in one short sentence."
    append_report(task, "failed", clarification)
    return {"status": "failed", "question": clarification}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the BADGR local harness.")
    parser.add_argument("--goal", required=True, help="User goal to execute through the harness")
    args = parser.parse_args()
    result = run_task(args.goal)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
EOF

cat > state/runtime_state.json <<'EOF'
{
  "last_task_id": null,
  "notes": "Runtime state placeholder for future expansion."
}
EOF

cat > examples/sample_task.json <<'EOF'
{
  "task_id": "task_sample_001",
  "user_goal": "Classify this request and return strict JSON",
  "task_type": "classification",
  "constraints": [
    "strict_json",
    "ask_if_under_98_confident"
  ],
  "expected_output": "classification_result",
  "confidence_required": 0.98,
  "status": "queued"
}
EOF

cat > tests/test_router.py <<'EOF'
from pathlib import Path

from router import choose_primary_model, classify_task, load_model_registry
from schemas.task_schema import TaskType


MODELS_FILE = Path(__file__).resolve().parents[1] / "models.yaml"


def test_classify_task_code() -> None:
    assert classify_task("Fix this Python bug") == TaskType.CODE


def test_choose_primary_model_code() -> None:
    registry = load_model_registry(MODELS_FILE)
    assert choose_primary_model(TaskType.CODE, registry) == "qwen2.5-coder:7b"
EOF

cat > tests/test_validator.py <<'EOF'
from schemas.task_schema import Task, TaskType
from validator import validate_worker_output


def test_validate_classification_output() -> None:
    task = Task(
        task_id="task_123",
        user_goal="Classify this",
        task_type=TaskType.CLASSIFICATION,
        constraints=["strict_json"],
        expected_output="classification_result",
        confidence_required=0.98,
    )
    raw = '{"task_type":"classification","summary":"Looks like a routing request.","confidence":0.99,"recommended_action":"Route to worker.","needs_clarification":false,"clarification_question":null,"labels":["routing","classification"]}'
    result = validate_worker_output(task, raw)
    assert result.valid is True
    assert result.data is not None
EOF

cat > tests/test_orchestrator.py <<'EOF'
from orchestrator import normalize_task
from schemas.task_schema import TaskType


def test_normalize_task_sets_type() -> None:
    task = normalize_task("Plan a harness architecture")
    assert task.task_type == TaskType.PLANNING
    assert task.expected_output == "plan_result"
EOF

: > "logs/${TODAY}.jsonl"

cat > "reports/${TODAY}.md" <<'EOF'
# Daily Harness Report

EOF

python -m compileall . >/dev/null
python -m pytest -q

echo "BADGR harness scaffold created successfully at: ${PROJECT_ROOT}"
echo "Activate with: cd ${PROJECT_ROOT} && source .venv/bin/activate"
echo "Run with: python orchestrator.py --goal \"Classify this request and return strict JSON\""
