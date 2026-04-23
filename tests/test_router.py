from pathlib import Path

from router import (
    choose_micro_model,
    choose_primary_model,
    classify_task,
    is_badgr_domain,
    load_model_registry,
)
from schemas.task_schema import TaskType


MODELS_FILE = Path(__file__).resolve().parents[1] / "models.yaml"


# --- classify_task ---

def test_classify_task_code() -> None:
    assert classify_task("Fix this Python bug") == TaskType.CODE


def test_classify_task_planning() -> None:
    assert classify_task("Plan a harness architecture") == TaskType.PLANNING


def test_classify_task_extraction() -> None:
    assert classify_task("Extract all fields from the document") == TaskType.EXTRACTION


def test_classify_task_general_fallback() -> None:
    assert classify_task("What is happening with revenue") == TaskType.GENERAL


# --- is_badgr_domain ---

def test_domain_detected_for_trading_goal() -> None:
    assert is_badgr_domain("Analyze the swing trading indicators for this setup") is True


def test_domain_detected_for_leads_goal() -> None:
    assert is_badgr_domain("Classify these lead generation results by source") is True


def test_domain_not_detected_for_generic_goal() -> None:
    assert is_badgr_domain("Classify this request and return strict JSON") is False


def test_domain_not_detected_for_empty_goal() -> None:
    assert is_badgr_domain("") is False


# --- choose_primary_model ---

def test_choose_primary_model_code() -> None:
    registry = load_model_registry(MODELS_FILE)
    assert choose_primary_model(TaskType.CODE, registry) == "qwen2.5-coder:7b"


def test_choose_primary_model_planning() -> None:
    registry = load_model_registry(MODELS_FILE)
    assert choose_primary_model(TaskType.PLANNING, registry) == "qwen2.5:14b"


def test_choose_primary_model_generic_classification_uses_mistral() -> None:
    registry = load_model_registry(MODELS_FILE)
    result = choose_primary_model(TaskType.CLASSIFICATION, registry, user_goal="Classify this request")
    assert result == "mistral:7b"


def test_choose_primary_model_domain_classification_uses_analyst() -> None:
    registry = load_model_registry(MODELS_FILE)
    result = choose_primary_model(
        TaskType.CLASSIFICATION, registry,
        user_goal="Classify these swing trading setups by momentum indicator",
    )
    assert result == "badgr-analyst:latest"


def test_choose_primary_model_domain_extraction_uses_analyst() -> None:
    registry = load_model_registry(MODELS_FILE)
    result = choose_primary_model(
        TaskType.EXTRACTION, registry,
        user_goal="Extract all lead generation metrics from this campaign report",
    )
    assert result == "badgr-analyst:latest"


def test_choose_primary_model_generic_extraction_uses_mistral() -> None:
    registry = load_model_registry(MODELS_FILE)
    result = choose_primary_model(TaskType.EXTRACTION, registry, user_goal="Extract the name field")
    assert result == "mistral:7b"


def test_choose_primary_model_no_goal_uses_mistral_for_classification() -> None:
    registry = load_model_registry(MODELS_FILE)
    result = choose_primary_model(TaskType.CLASSIFICATION, registry)
    assert result == "mistral:7b"


# --- choose_micro_model ---

def test_choose_micro_model_present() -> None:
    registry = load_model_registry(MODELS_FILE)
    micro = choose_micro_model(registry)
    assert micro == "llama3.2:3b"


def test_choose_micro_model_absent() -> None:
    assert choose_micro_model({}) is None
