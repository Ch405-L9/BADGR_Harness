from pathlib import Path

from router import choose_primary_model, classify_task, load_model_registry
from schemas.task_schema import TaskType


MODELS_FILE = Path(__file__).resolve().parents[1] / "models.yaml"


def test_classify_task_code() -> None:
    assert classify_task("Fix this Python bug") == TaskType.CODE


def test_choose_primary_model_code() -> None:
    registry = load_model_registry(MODELS_FILE)
    assert choose_primary_model(TaskType.CODE, registry) == "qwen2.5-coder:7b"
