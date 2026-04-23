"""Phase 6 tests: model-based routing, code_block field, analyst routing."""

from __future__ import annotations

from validator import ValidationOutcome, validate_worker_output
from schemas.task_schema import Task, TaskType
import orchestrator


def _make_task(task_type: TaskType) -> Task:
    return Task(
        task_id="task_p6_001",
        user_goal="test goal",
        task_type=task_type,
        constraints=["strict_json"],
        expected_output=f"{task_type.value}_result",
        confidence_required=0.98,
    )


def test_code_response_accepts_code_block() -> None:
    task = _make_task(TaskType.CODE)
    raw = (
        '{"task_type":"code","summary":"Fixed the bug.","confidence":0.99,'
        '"recommended_action":"Replace the broken line.","needs_clarification":false,'
        '"clarification_question":null,"changes":["Line 5 fixed"],'
        '"code_block":"def foo():\\n    return 42"}'
    )
    result = validate_worker_output(task, raw)
    assert result.valid is True
    assert result.data is not None
    assert result.data["code_block"] == "def foo():\n    return 42"


def test_code_response_valid_without_code_block() -> None:
    task = _make_task(TaskType.CODE)
    raw = (
        '{"task_type":"code","summary":"Fixed.","confidence":0.99,'
        '"recommended_action":"Apply fix.","needs_clarification":false,'
        '"clarification_question":null,"changes":["fix applied"]}'
    )
    result = validate_worker_output(task, raw)
    assert result.valid is True
    assert result.data is not None
    assert result.data.get("code_block") is None


def test_normalize_task_uses_type_override() -> None:
    task = orchestrator.normalize_task("some ambiguous goal", task_type_override=TaskType.EXTRACTION)
    assert task.task_type == TaskType.EXTRACTION
    assert task.expected_output == "extraction_result"


def test_normalize_task_keyword_fallback_when_no_override() -> None:
    task = orchestrator.normalize_task("Plan a harness architecture")
    assert task.task_type == TaskType.PLANNING


def test_model_classify_task_returns_none_on_failure(monkeypatch) -> None:
    monkeypatch.setattr(orchestrator, "call_ollama", lambda *a, **kw: "not json at all")
    result = orchestrator.model_classify_task("anything", "fake-model:latest", {})
    assert result is None


def test_model_classify_task_returns_none_on_unknown_type(monkeypatch) -> None:
    monkeypatch.setattr(orchestrator, "call_ollama", lambda *a, **kw: '{"task_type": "cooking"}')
    result = orchestrator.model_classify_task("bake a cake", "fake-model:latest", {})
    assert result is None


def test_model_classify_task_returns_type_on_valid_response(monkeypatch) -> None:
    monkeypatch.setattr(orchestrator, "call_ollama", lambda *a, **kw: '{"task_type": "extraction"}')
    result = orchestrator.model_classify_task("pull all revenue fields", "llama3.2:3b", {})
    assert result == TaskType.EXTRACTION


def test_run_task_uses_model_routing_when_micro_available(monkeypatch) -> None:
    monkeypatch.setattr(orchestrator, "load_model_registry", lambda _: {"mock": {}})
    monkeypatch.setattr(orchestrator, "choose_micro_model", lambda reg: "llama3.2:3b")
    monkeypatch.setattr(
        orchestrator, "model_classify_task",
        lambda goal, model, reg: TaskType.CLASSIFICATION,
    )
    monkeypatch.setattr(orchestrator, "choose_primary_model", lambda *a, **kw: "mistral:7b")
    monkeypatch.setattr(orchestrator, "append_log", lambda e: None)
    monkeypatch.setattr(orchestrator, "append_report", lambda *a, **kw: None)
    monkeypatch.setattr(
        orchestrator,
        "attempt_model",
        lambda *a, **kw: ValidationOutcome(
            valid=True,
            data={
                "task_type": "classification",
                "summary": "Classified.",
                "confidence": 0.99,
                "recommended_action": "Route.",
                "needs_clarification": False,
                "clarification_question": None,
                "labels": ["routing"],
            },
        ),
    )
    result = orchestrator.run_task("route this request please")
    assert result["task_type"] == "classification"


def test_run_task_routes_domain_goal_to_analyst(monkeypatch) -> None:
    from router import choose_primary_model as real_choose_primary_model
    from pathlib import Path
    from router import load_model_registry
    registry = load_model_registry(Path("models.yaml"))

    monkeypatch.setattr(orchestrator, "load_model_registry", lambda _: registry)
    monkeypatch.setattr(orchestrator, "choose_micro_model", lambda reg: None)
    monkeypatch.setattr(orchestrator, "append_log", lambda e: None)
    monkeypatch.setattr(orchestrator, "append_report", lambda *a, **kw: None)
    monkeypatch.setattr(
        orchestrator,
        "attempt_model",
        lambda *a, **kw: ValidationOutcome(
            valid=True,
            data={
                "task_type": "classification",
                "summary": "Trading setup classified.",
                "confidence": 0.99,
                "recommended_action": "Route to analyst.",
                "needs_clarification": False,
                "clarification_question": None,
                "labels": ["swing_trade"],
            },
        ),
    )
    selected_models: list[str] = []
    original_attempt = orchestrator.attempt_model

    def capture_attempt(task, model_name, *args, **kwargs):
        selected_models.append(model_name)
        return ValidationOutcome(
            valid=True,
            data={
                "task_type": "classification",
                "summary": "Trading setup classified.",
                "confidence": 0.99,
                "recommended_action": "Route to analyst.",
                "needs_clarification": False,
                "clarification_question": None,
                "labels": ["swing_trade"],
            },
        )

    monkeypatch.setattr(orchestrator, "attempt_model", capture_attempt)
    orchestrator.run_task("Classify these swing trading setups by momentum indicator")
    assert selected_models[0] == "badgr-analyst:latest"


def test_run_task_falls_back_to_keyword_when_no_micro(monkeypatch) -> None:
    monkeypatch.setattr(orchestrator, "load_model_registry", lambda _: {"mock": {}})
    monkeypatch.setattr(orchestrator, "choose_micro_model", lambda reg: None)
    monkeypatch.setattr(orchestrator, "choose_primary_model", lambda *a, **kw: "qwen2.5-coder:7b")
    monkeypatch.setattr(orchestrator, "append_log", lambda e: None)
    monkeypatch.setattr(orchestrator, "append_report", lambda *a, **kw: None)
    monkeypatch.setattr(
        orchestrator,
        "attempt_model",
        lambda *a, **kw: ValidationOutcome(
            valid=True,
            data={
                "task_type": "code",
                "summary": "Fixed.",
                "confidence": 0.99,
                "recommended_action": "Apply.",
                "needs_clarification": False,
                "clarification_question": None,
                "changes": ["fix"],
                "code_block": None,
            },
        ),
    )
    result = orchestrator.run_task("Fix this Python bug")
    assert result["task_type"] == "code"
