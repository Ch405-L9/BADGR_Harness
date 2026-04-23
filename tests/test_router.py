from pathlib import Path

from router import choose_micro_model, choose_primary_model, classify_task, load_model_registry
from schemas.task_schema import TaskType


MODELS_FILE = Path(__file__).resolve().parents[1] / "models.yaml"


def test_classify_task_code() -> None:
    assert classify_task("Fix this Python bug") == TaskType.CODE


def test_classify_task_planning() -> None:
    assert classify_task("Plan a harness architecture") == TaskType.PLANNING


def test_classify_task_extraction() -> None:
    assert classify_task("Extract all fields from the document") == TaskType.EXTRACTION


def test_classify_task_general_fallback() -> None:
    assert classify_task("What is happening with revenue") == TaskType.GENERAL


def test_choose_primary_model_code() -> None:
    registry = load_model_registry(MODELS_FILE)
    assert choose_primary_model(TaskType.CODE, registry) == "qwen2.5-coder:7b"


def test_choose_primary_model_planning() -> None:
    registry = load_model_registry(MODELS_FILE)
    assert choose_primary_model(TaskType.PLANNING, registry) == "qwen2.5:14b"


def test_choose_primary_model_classification_uses_analyst() -> None:
    registry = load_model_registry(MODELS_FILE)
    # badgr_analyst is registered with analyst role — should be selected for classification
    result = choose_primary_model(TaskType.CLASSIFICATION, registry)
    assert result == "badgr-analyst:latest"


def test_choose_primary_model_extraction_uses_analyst() -> None:
    registry = load_model_registry(MODELS_FILE)
    result = choose_primary_model(TaskType.EXTRACTION, registry)
    assert result == "badgr-analyst:latest"


def test_choose_micro_model_present() -> None:
    registry = load_model_registry(MODELS_FILE)
    micro = choose_micro_model(registry)
    assert micro == "llama3.2:3b"


def test_choose_micro_model_absent() -> None:
    assert choose_micro_model({}) is None
