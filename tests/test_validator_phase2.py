from schemas.taskschema import Task, TaskType
from validator import validateworkeroutput


def make_task(tasktype: TaskType) -> Task:
    return Task(
        taskid="task123",
        usergoal="test",
        tasktype=tasktype,
        constraints=["strictjson"],
        expectedoutput="result",
        confidencerequired=0.98,
        status="queued",
    )


def test_rejects_wrong_tasktype() -> None:
    task = make_task(TaskType.CLASSIFICATION)
    raw = '{"tasktype":"general","summary":"x","confidence":0.99,"recommendedaction":"route","needsclarification":false,"clarificationquestion":null,"labels":["routing"]}'
    result = validateworkeroutput(task, raw)
    assert result.valid is False
    assert "Task type mismatch" in (result.error or "")


def test_rejects_low_confidence_without_clarification() -> None:
    task = make_task(TaskType.CLASSIFICATION)
    raw = '{"tasktype":"classification","summary":"x","confidence":0.70,"recommendedaction":"route","needsclarification":false,"clarificationquestion":null,"labels":["routing"]}'
    result = validateworkeroutput(task, raw)
    assert result.valid is False
    assert result.error == "Confidence below required threshold."


def test_requires_question_when_needs_clarification() -> None:
    task = make_task(TaskType.GENERAL)
    raw = '{"tasktype":"general","summary":"x","confidence":0.60,"recommendedaction":"ask","needsclarification":true,"clarificationquestion":""}'
    result = validateworkeroutput(task, raw)
    assert result.valid is False
    assert "clarification_question" in (result.error or "")


def test_requires_labels_for_classification() -> None:
    task = make_task(TaskType.CLASSIFICATION)
    raw = '{"tasktype":"classification","summary":"x","confidence":0.99,"recommendedaction":"route","needsclarification":false,"clarificationquestion":null,"labels":[]}'
    result = validateworkeroutput(task, raw)
    assert result.valid is False
    assert "at least one label" in (result.error or "")


def test_accepts_markdown_fenced_json() -> None:
    task = make_task(TaskType.CLASSIFICATION)
    raw = '```json\n{"tasktype":"classification","summary":"x","confidence":0.99,"recommendedaction":"route","needsclarification":false,"clarificationquestion":null,"labels":["routing"]}\n```'
    result = validateworkeroutput(task, raw)
    assert result.valid is True
    assert result.data is not None
