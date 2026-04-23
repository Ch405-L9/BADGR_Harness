from orchestrator import normalize_task
from schemas.task_schema import TaskType


def test_normalize_task_sets_type() -> None:
    task = normalize_task("Plan a harness architecture")
    assert task.task_type == TaskType.PLANNING
    assert task.expected_output == "plan_result"
