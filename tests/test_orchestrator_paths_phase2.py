from validator import ValidationOutcome
import orchestrator


def test_supervisor_clarification_path(monkeypatch) -> None:
    monkeypatch.setattr(orchestrator, "load_model_registry", lambda _: {"mock": {}})
    monkeypatch.setattr(orchestrator, "choose_primary_model", lambda *args, **kwargs: "worker-model")
    monkeypatch.setattr(orchestrator, "choose_fallback_model", lambda *args, **kwargs: "fallback-model")
    monkeypatch.setattr(orchestrator, "choose_supervisor_model", lambda *args, **kwargs: "supervisor-model")
    monkeypatch.setattr(orchestrator, "append_log", lambda event: None)
    monkeypatch.setattr(orchestrator, "append_report", lambda *args, **kwargs: None)

    responses = iter([
        ValidationOutcome(valid=False, error="bad json"),
        ValidationOutcome(valid=False, error="bad retry"),
        ValidationOutcome(valid=False, error="bad fallback"),
        ValidationOutcome(
            valid=True,
            data={
                "task_type": "planning",
                "summary": "Need clarification.",
                "confidence": 0.99,
                "recommended_action": "Ask user a short question.",
                "needs_clarification": True,
                "clarification_question": "What exact architecture output do you want?",
            },
        ),
    ])

    monkeypatch.setattr(orchestrator, "attempt_model", lambda *args, **kwargs: next(responses))

    result = orchestrator.run_task("Plan a harness architecture")
    assert result["status"] == "needs_clarification"
    assert "question" in result


def test_primary_success_path(monkeypatch) -> None:
    monkeypatch.setattr(orchestrator, "load_model_registry", lambda _: {"mock": {}})
    monkeypatch.setattr(orchestrator, "choose_primary_model", lambda *args, **kwargs: "worker-model")
    monkeypatch.setattr(orchestrator, "append_log", lambda event: None)
    monkeypatch.setattr(orchestrator, "append_report", lambda *args, **kwargs: None)

    monkeypatch.setattr(
        orchestrator,
        "attempt_model",
        lambda *args, **kwargs: ValidationOutcome(
            valid=True,
            data={
                "task_type": "classification",
                "summary": "Looks like routing.",
                "confidence": 0.99,
                "recommended_action": "Route to worker.",
                "needs_clarification": False,
                "clarification_question": None,
                "labels": ["routing"],
            },
        ),
    )

    result = orchestrator.run_task("Classify this request")
    assert result["task_type"] == "classification"
    assert result["labels"] == ["routing"]
