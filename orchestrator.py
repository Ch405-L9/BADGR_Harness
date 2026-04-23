from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from urllib import error, request

try:
    from config import LOGS_DIR, MODELS_FILE, OLLAMA_BASE_URL, PROMPTS_DIR, REPORTS_DIR
except ImportError:
    from config import (
        LOGSDIR as LOGS_DIR,
        MODELSFILE as MODELS_FILE,
        OLLAMABASEURL as OLLAMA_BASE_URL,
        PROMPTSDIR as PROMPTS_DIR,
        REPORTSDIR as REPORTS_DIR,
    )

try:
    from router import (
        choose_fallback_model,
        choose_micro_model,
        choose_primary_model,
        choose_supervisor_model,
        classify_task,
        load_model_registry,
    )
except ImportError:
    from router import (
        choosefallbackmodel as choose_fallback_model,
        choosemicromodel as choose_micro_model,
        chooseprimarymodel as choose_primary_model,
        choosesupervisormodel as choose_supervisor_model,
        classifytask as classify_task,
        loadmodelregistry as load_model_registry,
    )

try:
    from schemas.log_schema import EventStatus, HarnessEvent
except ImportError:
    from schemas.logschema import EventStatus, HarnessEvent

try:
    from schemas.task_schema import Task, TaskStatus, TaskType
except ImportError:
    from schemas.taskschema import Task, TaskStatus, TaskType

try:
    from validator import ValidationOutcome, validate_worker_output
except ImportError:
    from validator import ValidationOutcome, validateworkeroutput as validate_worker_output


DEFAULT_CONSTRAINTS = ["strict_json", "ask_if_under_98_confident"]

PROMPT_NAME_CANDIDATES = {
    "worker": ["worker_system.txt", "workersystem.txt"],
    "fallback": ["fallback_system.txt", "fallbacksystem.txt"],
    "supervisor": ["supervisor_system.txt", "supervisorsystem.txt"],
}

loadmodelregistry = load_model_registry
chooseprimarymodel = choose_primary_model
choosefallbackmodel = choose_fallback_model
choosesupervisormodel = choose_supervisor_model
choosemicromodel = choose_micro_model
classifytask = classify_task


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _task_attr(task: Task, *names: str, default: Any = None) -> Any:
    for name in names:
        if hasattr(task, name):
            return getattr(task, name)
    return default


def _set_task_attr(task: Task, value: Any, *names: str) -> None:
    for name in names:
        if hasattr(task, name):
            setattr(task, name, value)
            return
    if names:
        setattr(task, names[0], value)


def _task_status(name: str) -> Any:
    if hasattr(TaskStatus, name):
        return getattr(TaskStatus, name)
    compact = name.replace("_", "")
    if hasattr(TaskStatus, compact):
        return getattr(TaskStatus, compact)
    return name.lower()


def _event_status(name: str) -> Any:
    if hasattr(EventStatus, name):
        return getattr(EventStatus, name)
    compact = name.replace("_", "")
    if hasattr(EventStatus, compact):
        return getattr(EventStatus, compact)
    return name.lower()


def _task_type_value(task: Task) -> str:
    value = _task_attr(task, "task_type", "tasktype")
    return str(_enum_value(value))


def _expected_output(task: Task) -> str:
    return str(_task_attr(task, "expected_output", "expectedoutput", default="general_result"))


def _constraints(task: Task) -> list[str]:
    value = _task_attr(task, "constraints", default=[])
    return list(value or [])


def _required_confidence(task: Task) -> float:
    return float(_task_attr(task, "confidence_required", "confidencerequired", default=0.98))


def _task_id(task: Task) -> str:
    return str(_task_attr(task, "task_id", "taskid"))


def _user_goal(task: Task) -> str:
    return str(_task_attr(task, "user_goal", "usergoal"))


def _model_fields(model_cls: Any) -> Dict[str, Any]:
    return getattr(model_cls, "model_fields", {})


def _dump_model(instance: Any) -> str:
    if hasattr(instance, "model_dump_json"):
        return instance.model_dump_json()
    return instance.json()


def _make_task(
    *,
    task_id: str,
    user_goal: str,
    task_type: Any,
    constraints: list[str],
    expected_output: str,
    confidence_required: float,
    status: Any,
) -> Task:
    fields = _model_fields(Task)
    kwargs: Dict[str, Any] = {"constraints": constraints, "status": status}
    kwargs["task_id" if "task_id" in fields else "taskid"] = task_id
    kwargs["user_goal" if "user_goal" in fields else "usergoal"] = user_goal
    kwargs["task_type" if "task_type" in fields else "tasktype"] = task_type
    kwargs["expected_output" if "expected_output" in fields else "expectedoutput"] = expected_output
    kwargs[
        "confidence_required" if "confidence_required" in fields else "confidencerequired"
    ] = confidence_required
    return Task(**kwargs)


def _make_harness_event(
    *,
    task: Task,
    action: str,
    status: Any,
    model_used: Optional[str] = None,
    role_used: Optional[str] = None,
    validation_passed: Optional[bool] = None,
    error_message: Optional[str] = None,
    next_action: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    parent_event_id: Optional[str] = None,
) -> HarnessEvent:
    fields = _model_fields(HarnessEvent)
    kwargs: Dict[str, Any] = {"action": action, "status": status, "details": details or {}}
    kwargs["task_id" if "task_id" in fields else "taskid"] = _task_id(task)

    if "model_used" in fields:
        kwargs["model_used"] = model_used
    elif "modelused" in fields:
        kwargs["modelused"] = model_used

    if "role_used" in fields:
        kwargs["role_used"] = role_used
    elif "roleused" in fields:
        kwargs["roleused"] = role_used

    if "validation_passed" in fields:
        kwargs["validation_passed"] = validation_passed
    elif "validationpassed" in fields:
        kwargs["validationpassed"] = validation_passed

    if "error_message" in fields:
        kwargs["error_message"] = error_message
    elif "errormessage" in fields:
        kwargs["errormessage"] = error_message

    if "next_action" in fields:
        kwargs["next_action"] = next_action
    elif "nextaction" in fields:
        kwargs["nextaction"] = next_action

    if "parent_event_id" in fields:
        kwargs["parent_event_id"] = parent_event_id
    elif "parenteventid" in fields:
        kwargs["parenteventid"] = parent_event_id

    return HarnessEvent(**kwargs)


def _event_id(event: HarnessEvent) -> Optional[str]:
    return getattr(event, "event_id", getattr(event, "eventid", None))


def _model_config_by_name(model_name: str, registry: Dict[str, Any]) -> Dict[str, Any]:
    for config in registry.values():
        if config.get("modelname") == model_name or config.get("model_name") == model_name:
            return config
    return {}


def _prompt_path(name: str) -> Path:
    if name in PROMPT_NAME_CANDIDATES:
        for candidate in PROMPT_NAME_CANDIDATES[name]:
            path = PROMPTS_DIR / candidate
            if path.exists():
                return path
        return PROMPTS_DIR / PROMPT_NAME_CANDIDATES[name]
    return PROMPTS_DIR / name


def next_task_id() -> str:
    return f"task_{utc_now().strftime('%Y%m%d%H%M%S%f')}"


def normalize_task(user_goal: str, task_type_override: Optional[TaskType] = None) -> Task:
    task_type = task_type_override if task_type_override is not None else classify_task(user_goal)
    expected_output = {
        TaskType.CODE: "code_result",
        TaskType.CLASSIFICATION: "classification_result",
        TaskType.EXTRACTION: "extraction_result",
        TaskType.SUMMARIZATION: "summary_result",
        TaskType.PLANNING: "plan_result",
    }.get(task_type, "general_result")

    return _make_task(
        task_id=next_task_id(),
        user_goal=user_goal,
        task_type=task_type,
        constraints=DEFAULT_CONSTRAINTS,
        expected_output=expected_output,
        confidence_required=0.98,
        status=_task_status("QUEUED"),
    )


def read_prompt(name: str) -> str:
    return _prompt_path(name).read_text(encoding="utf-8").strip()


def build_prompt(task: Task, role_prompt: str, retry_note: str = "") -> str:
    task_type = _task_attr(task, "task_type", "tasktype")
    schema_hint = {
        TaskType.CODE: (
            '{"task_type":"code","summary":"...","confidence":0.99,'
            '"recommended_action":"brief description of the fix","needs_clarification":false,'
            '"clarification_question":null,"changes":["..."],'
            '"code_block":"full corrected code here as a plain string"}'
        ),
        TaskType.CLASSIFICATION: (
            '{"task_type":"classification","summary":"...","confidence":0.99,'
            '"recommended_action":"...","needs_clarification":false,'
            '"clarification_question":null,"labels":["..."]}'
        ),
        TaskType.EXTRACTION: (
            '{"task_type":"extraction","summary":"...","confidence":0.99,'
            '"recommended_action":"...","needs_clarification":false,'
            '"clarification_question":null,"fields":{"key":"value"}}'
        ),
        TaskType.SUMMARIZATION: (
            '{"task_type":"summarization","summary":"...","confidence":0.99,'
            '"recommended_action":"...","needs_clarification":false,'
            '"clarification_question":null,"key_points":["..."]}'
        ),
        TaskType.PLANNING: (
            '{"task_type":"planning","summary":"...","confidence":0.99,'
            '"recommended_action":"...","needs_clarification":false,'
            '"clarification_question":null,"steps":["..."]}'
        ),
    }.get(
        task_type,
        '{"task_type":"general","summary":"...","confidence":0.99,'
        '"recommended_action":"...","needs_clarification":false,'
        '"clarification_question":null}',
    )

    retry_block = f"{retry_note}\n" if retry_note else ""
    return (
        f"{role_prompt}\n\n"
        f"Task ID: {_task_id(task)}\n"
        f"Task Type: {_task_type_value(task)}\n"
        f"Expected Output: {_expected_output(task)}\n"
        f"Constraints: {', '.join(_constraints(task))}\n"
        f"Required Confidence: {_required_confidence(task)}\n"
        f"User Goal: {_user_goal(task)}\n"
        f"{retry_block}"
        f"Return valid JSON only using this exact shape:\n{schema_hint}\n"
    )


def call_ollama(model_name: str, prompt: str, timeout_seconds: int = 120, temperature: float = 0.1) -> str:
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": temperature},
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
    except error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Ollama HTTP error {exc.code}: {message}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Ollama request failed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Ollama returned non-JSON response: {exc}") from exc
    return body.get("response", "")


_VALID_TASK_TYPES = {t.value for t in TaskType}

_MICRO_CLASSIFY_PROMPT = (
    "You are a task classifier. Read the goal and return exactly one JSON object.\n"
    "Valid values for task_type: code, classification, extraction, summarization, planning, general\n\n"
    'Return: {{"task_type": "<one of the above>"}}\n\n'
    "Goal: {goal}"
)


def model_classify_task(user_goal: str, micro_model: str, registry: Dict[str, Any]) -> Optional[TaskType]:
    """Use the micro model to classify a task. Returns None on any failure — caller falls back to keyword routing."""
    model_config = _model_config_by_name(micro_model, registry)
    timeout_seconds = int(model_config.get("timeout_seconds", model_config.get("timeoutseconds", 30)))
    try:
        prompt = _MICRO_CLASSIFY_PROMPT.format(goal=user_goal)
        raw = call_ollama(micro_model, prompt, timeout_seconds=timeout_seconds, temperature=0.0)
        parsed = json.loads(raw) if raw.strip().startswith("{") else json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
        task_type_str = str(parsed.get("task_type", "")).lower().strip()
        if task_type_str in _VALID_TASK_TYPES:
            return TaskType(task_type_str)
    except Exception:  # noqa: BLE001 — micro classification failure is always non-fatal
        pass
    return None


def append_log(event: HarnessEvent) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"{utc_now().date().isoformat()}.jsonl"
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(_dump_model(event) + "\n")


def append_report(task: Task, final_status: str, note: str) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / f"{utc_now().date().isoformat()}.md"
    if not report_file.exists():
        report_file.write_text(
            f"# BADGR Harness — Daily Report {utc_now().date().isoformat()}\n\n"
            f"| Time (UTC) | Task ID | Type | Status | Note |\n"
            f"|------------|---------|------|--------|------|\n",
            encoding="utf-8",
        )
    ts = utc_now().strftime("%H:%M:%S")
    task_type = _task_type_value(task)
    with report_file.open("a", encoding="utf-8") as handle:
        handle.write(
            f"| {ts} | `{_task_id(task)[-16:]}` | {task_type} | **{final_status}** | {note} |\n"
        )


def make_event(
    task: Task,
    action: str,
    status: Any,
    model_used: Optional[str] = None,
    role_used: Optional[str] = None,
    validation_passed: Optional[bool] = None,
    error_message: Optional[str] = None,
    next_action: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    parent_event_id: Optional[str] = None,
) -> HarnessEvent:
    event = _make_harness_event(
        task=task,
        action=action,
        status=status,
        model_used=model_used,
        role_used=role_used,
        validation_passed=validation_passed,
        error_message=error_message,
        next_action=next_action,
        details=details,
        parent_event_id=parent_event_id,
    )
    append_log(event)
    return event


def attempt_model(
    task: Task,
    model_name: str,
    prompt_file: str,
    retry_note: str = "",
    registry: Optional[Dict[str, Any]] = None,
) -> ValidationOutcome:
    role_prompt = read_prompt(prompt_file)
    prompt = build_prompt(task, role_prompt, retry_note=retry_note)
    model_config = _model_config_by_name(model_name, registry or {})
    timeout_seconds = int(model_config.get("timeoutseconds", model_config.get("timeout_seconds", 120)))
    temperature = float(model_config.get("temperature", 0.1))
    raw_output = call_ollama(
        model_name,
        prompt,
        timeout_seconds=timeout_seconds,
        temperature=temperature,
    )
    return validate_worker_output(task, raw_output)


def run_task(user_goal: str) -> Dict[str, Any]:
    registry = load_model_registry(MODELS_FILE)

    # Sidechain: try micro-model classification before keyword routing
    micro_model = choose_micro_model(registry)
    detected_type: Optional[TaskType] = None
    if micro_model:
        detected_type = model_classify_task(user_goal, micro_model, registry)

    task = normalize_task(user_goal, task_type_override=detected_type)
    _set_task_attr(task, _task_status("RUNNING"), "status")

    routing_method = "model" if detected_type is not None else "keyword"
    start_event = make_event(
        task=task,
        action="task_started",
        status=_event_status("STARTED"),
        next_action="route_primary_model",
        details={"task_type": _task_type_value(task), "routing_method": routing_method},
    )

    task_type = _task_attr(task, "task_type", "tasktype")
    primary_model = choose_primary_model(task_type, registry)
    if task_type in {TaskType.PLANNING, TaskType.SUMMARIZATION}:
        primary_role = "planner"
    elif task_type in {TaskType.CLASSIFICATION, TaskType.EXTRACTION}:
        primary_role = "analyst"
    else:
        primary_role = "worker"
    primary_event = make_event(
        task=task,
        action="primary_model_selected",
        status=_event_status("STARTED"),
        model_used=primary_model,
        role_used=primary_role,
        next_action="run_primary_attempt",
        parent_event_id=_event_id(start_event),
    )

    first_try = attempt_model(task, primary_model, "worker", registry=registry)
    if first_try.valid:
        _set_task_attr(task, _task_status("SUCCESS"), "status")
        make_event(
            task=task,
            action="primary_attempt_valid",
            status=_event_status("SUCCESS"),
            model_used=primary_model,
            role_used="worker",
            validation_passed=True,
            next_action="return_result",
            parent_event_id=_event_id(primary_event),
        )
        append_report(task, "success", f"Primary model succeeded: {primary_model}")
        return first_try.data or {}

    retry_event = make_event(
        task=task,
        action="primary_attempt_invalid",
        status=_event_status("RETRY"),
        model_used=primary_model,
        role_used="worker",
        validation_passed=False,
        error_message=first_try.error,
        next_action="retry_primary_once",
        parent_event_id=_event_id(primary_event),
    )

    second_try = attempt_model(
        task,
        primary_model,
        "worker",
        retry_note="Retry note: your prior answer failed validation. Return only valid JSON in the exact shape required.",
        registry=registry,
    )
    if second_try.valid:
        _set_task_attr(task, _task_status("SUCCESS"), "status")
        make_event(
            task=task,
            action="primary_retry_valid",
            status=_event_status("SUCCESS"),
            model_used=primary_model,
            role_used="worker",
            validation_passed=True,
            next_action="return_result",
            parent_event_id=_event_id(retry_event),
        )
        append_report(task, "success", f"Primary retry succeeded: {primary_model}")
        return second_try.data or {}

    fallback_model = choose_fallback_model(primary_model, registry)
    fallback_event = make_event(
        task=task,
        action="fallback_model_selected",
        status=_event_status("FALLBACK"),
        model_used=fallback_model,
        role_used="fallback",
        validation_passed=False,
        error_message=second_try.error,
        next_action="run_fallback_attempt",
        parent_event_id=_event_id(retry_event),
    )

    fallback_try = attempt_model(
        task,
        fallback_model,
        "fallback",
        retry_note="Fallback note: repair the failed attempts and return valid JSON only.",
        registry=registry,
    )
    if fallback_try.valid:
        _set_task_attr(task, _task_status("SUCCESS"), "status")
        make_event(
            task=task,
            action="fallback_valid",
            status=_event_status("SUCCESS"),
            model_used=fallback_model,
            role_used="fallback",
            validation_passed=True,
            next_action="return_result",
            parent_event_id=_event_id(fallback_event),
        )
        append_report(task, "success", f"Fallback model succeeded: {fallback_model}")
        return fallback_try.data or {}

    supervisor_model = choose_supervisor_model(registry)
    supervisor_event = make_event(
        task=task,
        action="supervisor_selected",
        status=_event_status("ESCALATED"),
        model_used=supervisor_model,
        role_used="supervisor",
        validation_passed=False,
        error_message=fallback_try.error,
        next_action="run_supervisor_attempt",
        parent_event_id=_event_id(fallback_event),
    )

    supervisor_try = attempt_model(
        task,
        supervisor_model,
        "supervisor",
        retry_note="Supervisor note: failed worker attempts require synthesis or a short clarification question.",
        registry=registry,
    )
    if supervisor_try.valid:
        data = supervisor_try.data or {}
        if data.get("needs_clarification"):
            _set_task_attr(task, _task_status("NEEDS_CLARIFICATION"), "status")
            clarification = data.get("clarification_question") or "Please clarify the goal in one short sentence."
            make_event(
                task=task,
                action="clarification_required",
                status=_event_status("NEEDS_CLARIFICATION"),
                model_used=supervisor_model,
                role_used="supervisor",
                validation_passed=True,
                next_action="ask_human",
                details={"clarification_question": clarification},
                parent_event_id=_event_id(supervisor_event),
            )
            append_report(task, "needs_clarification", clarification)
            return {"status": "needs_clarification", "question": clarification}

        _set_task_attr(task, _task_status("SUCCESS"), "status")
        make_event(
            task=task,
            action="supervisor_valid",
            status=_event_status("SUCCESS"),
            model_used=supervisor_model,
            role_used="supervisor",
            validation_passed=True,
            next_action="return_result",
            parent_event_id=_event_id(supervisor_event),
        )
        append_report(task, "success", f"Supervisor succeeded: {supervisor_model}")
        return data

    _set_task_attr(task, _task_status("FAILED"), "status")
    make_event(
        task=task,
        action="task_failed",
        status=_event_status("FAILED"),
        model_used=supervisor_model,
        role_used="supervisor",
        validation_passed=False,
        error_message=supervisor_try.error,
        next_action="ask_human",
        parent_event_id=_event_id(supervisor_event),
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


utcnow = utc_now
nexttaskid = next_task_id
normalizetask = normalize_task
readprompt = read_prompt
buildprompt = build_prompt
callollama = call_ollama
appendlog = append_log
appendreport = append_report
appendlogevent = append_log
appendreporttask = append_report
makeevent = make_event
attemptmodel = attempt_model
modelclassifytask = model_classify_task
normalizetask = normalize_task
runtask = run_task

if __name__ == "__main__":
    main()
