from schemas.task_schema import Task, TaskType
from validator import validate_worker_output


def _make_task(task_type: TaskType) -> Task:
    return Task(
        task_id="task_123",
        user_goal="test goal",
        task_type=task_type,
        constraints=["strict_json"],
        expected_output=f"{task_type.value}_result",
        confidence_required=0.98,
    )


def test_validate_classification_output() -> None:
    task = _make_task(TaskType.CLASSIFICATION)
    raw = '{"task_type":"classification","summary":"Looks like a routing request.","confidence":0.99,"recommended_action":"Route to worker.","needs_clarification":false,"clarification_question":null,"labels":["routing","classification"]}'
    result = validate_worker_output(task, raw)
    assert result.valid is True
    assert result.data is not None


def test_validate_summarization_output() -> None:
    task = _make_task(TaskType.SUMMARIZATION)
    raw = '{"task_type":"summarization","summary":"Short version.","confidence":0.99,"recommended_action":"Return summary.","needs_clarification":false,"clarification_question":null,"key_points":["point one","point two"]}'
    result = validate_worker_output(task, raw)
    assert result.valid is True
    assert result.data is not None
    assert result.data["key_points"] == ["point one", "point two"]


def test_validate_planning_output() -> None:
    task = _make_task(TaskType.PLANNING)
    raw = '{"task_type":"planning","summary":"Harness plan.","confidence":0.99,"recommended_action":"Execute plan.","needs_clarification":false,"clarification_question":null,"steps":["step one","step two"]}'
    result = validate_worker_output(task, raw)
    assert result.valid is True
    assert result.data is not None
    assert result.data["steps"] == ["step one", "step two"]


def test_rejects_summarization_without_key_points() -> None:
    task = _make_task(TaskType.SUMMARIZATION)
    raw = '{"task_type":"summarization","summary":"Short.","confidence":0.99,"recommended_action":"ok.","needs_clarification":false,"clarification_question":null,"key_points":[]}'
    result = validate_worker_output(task, raw)
    assert result.valid is False
    assert "key_point" in (result.error or "")


def test_rejects_planning_without_steps() -> None:
    task = _make_task(TaskType.PLANNING)
    raw = '{"task_type":"planning","summary":"Plan.","confidence":0.99,"recommended_action":"ok.","needs_clarification":false,"clarification_question":null,"steps":[]}'
    result = validate_worker_output(task, raw)
    assert result.valid is False
    assert "step" in (result.error or "")


def test_coerces_changes_list_of_dicts_to_strings() -> None:
    task = _make_task(TaskType.CODE)
    # Model returned changes as a list of objects instead of strings
    raw = (
        '{"task_type":"code","summary":"Fixed.","confidence":0.99,'
        '"recommended_action":"Apply fix.","needs_clarification":false,'
        '"clarification_question":null,'
        '"changes":[{"description":"Replace line 5","line":5}]}'
    )
    result = validate_worker_output(task, raw)
    assert result.valid is True
    assert result.data is not None
    assert len(result.data["changes"]) == 1
    assert isinstance(result.data["changes"][0], str)
    assert "Replace line 5" in result.data["changes"][0]


def test_coerces_labels_list_of_dicts_to_strings() -> None:
    task = _make_task(TaskType.CLASSIFICATION)
    raw = (
        '{"task_type":"classification","summary":"Classified.","confidence":0.99,'
        '"recommended_action":"Route.","needs_clarification":false,'
        '"clarification_question":null,'
        '"labels":[{"label":"routing","confidence":0.99}]}'
    )
    result = validate_worker_output(task, raw)
    assert result.valid is True
    assert result.data is not None
    assert isinstance(result.data["labels"][0], str)


def test_clean_string_lists_pass_through_unchanged() -> None:
    task = _make_task(TaskType.CODE)
    raw = (
        '{"task_type":"code","summary":"Fixed.","confidence":0.99,'
        '"recommended_action":"Apply fix.","needs_clarification":false,'
        '"clarification_question":null,"changes":["Replace line 5","Remove debug print"]}'
    )
    result = validate_worker_output(task, raw)
    assert result.valid is True
    assert result.data["changes"] == ["Replace line 5", "Remove debug print"]
