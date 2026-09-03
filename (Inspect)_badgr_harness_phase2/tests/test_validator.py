from schemas.task_schema import Task, TaskType
from validator import validate_worker_output


def test_validate_classification_output() -> None:
    task = Task(
        task_id='task123',
        user_goal='Classify this',
        task_type=TaskType.CLASSIFICATION,
        constraints=['strict_json'],
        expected_output='classification_result',
        confidence_required=0.98,
    )
    raw = '{"tasktype":"classification","summary":"Looks like a routing request.","confidence":0.99,"recommendedaction":"Route to worker.","needsclarification":false,"clarificationquestion":null,"labels":["routing"]}'
    result = validate_worker_output(task, raw)
    assert result.valid is True
    assert result.data is not None


def test_clarification_requires_question() -> None:
    task = Task(
        task_id='task124',
        user_goal='Classify this',
        task_type=TaskType.CLASSIFICATION,
        constraints=['strict_json'],
        expected_output='classification_result',
        confidence_required=0.98,
    )
    raw = '{"tasktype":"classification","summary":"Need more info.","confidence":0.40,"recommendedaction":"Ask user.","needsclarification":true,"clarificationquestion":"","labels":["routing"]}'
    result = validate_worker_output(task, raw)
    assert result.valid is False
