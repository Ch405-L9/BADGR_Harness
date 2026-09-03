import json
from pathlib import Path

import orchestrator
from schemas.task_schema import TaskType


def test_normalize_task_sets_type() -> None:
    task = orchestrator.normalize_task('Plan a harness architecture')
    assert task.task_type == TaskType.PLANNING
    assert task.expected_output == 'plan_result'


def test_run_task_success(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(orchestrator, 'LOGS_DIR', tmp_path / 'logs')
    monkeypatch.setattr(orchestrator, 'REPORTS_DIR', tmp_path / 'reports')
    monkeypatch.setattr(orchestrator, 'MODELS_FILE', Path(__file__).resolve().parents[1] / 'models.yaml')

    def fake_call_ollama(model_name: str, prompt: str, timeout_seconds: int = 120, temperature: float = 0.1) -> str:
        return json.dumps({
            'tasktype': 'classification',
            'summary': 'Routing request classified successfully.',
            'confidence': 0.99,
            'recommendedaction': 'Route to worker.',
            'needsclarification': False,
            'clarificationquestion': None,
            'labels': ['routing'],
        })

    monkeypatch.setattr(orchestrator, 'call_ollama', fake_call_ollama)
    result = orchestrator.run_task('Classify this request and return strict JSON')
    assert result['task_type'] == 'classification'
    assert result['labels'] == ['routing']


def test_run_task_needs_clarification(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(orchestrator, 'LOGS_DIR', tmp_path / 'logs')
    monkeypatch.setattr(orchestrator, 'REPORTS_DIR', tmp_path / 'reports')
    monkeypatch.setattr(orchestrator, 'MODELS_FILE', Path(__file__).resolve().parents[1] / 'models.yaml')

    responses = iter([
        json.dumps({'tasktype': 'classification', 'summary': 'too low', 'confidence': 0.50, 'recommendedaction': 'retry', 'needsclarification': False, 'clarificationquestion': None, 'labels': ['routing']}),
        json.dumps({'tasktype': 'classification', 'summary': 'too low again', 'confidence': 0.40, 'recommendedaction': 'fallback', 'needsclarification': False, 'clarificationquestion': None, 'labels': ['routing']}),
        json.dumps({'tasktype': 'classification', 'summary': 'still blocked', 'confidence': 0.30, 'recommendedaction': 'escalate', 'needsclarification': False, 'clarificationquestion': None, 'labels': ['routing']}),
        json.dumps({'tasktype': 'classification', 'summary': 'need more detail', 'confidence': 0.20, 'recommendedaction': 'ask user', 'needsclarification': True, 'clarificationquestion': 'Please clarify the target output.', 'labels': ['routing']}),
    ])

    monkeypatch.setattr(orchestrator, 'call_ollama', lambda *args, **kwargs: next(responses))
    result = orchestrator.run_task('Classify this request and return strict JSON')
    assert result['status'] == 'needs_clarification'
    assert 'clarify' in result['question'].lower()
