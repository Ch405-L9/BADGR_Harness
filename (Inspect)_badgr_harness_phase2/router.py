from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

try:
    from schemas.task_schema import TaskType
except ImportError:
    from schemas.taskschema import TaskType

KEYWORD_MAP = {
    TaskType.CODE: ['code', 'bug', 'fix', 'function', 'refactor', 'python', 'script', 'syntax'],
    TaskType.CLASSIFICATION: ['classify', 'category', 'categorize', 'route', 'label', 'tag'],
    TaskType.EXTRACTION: ['extract', 'pull', 'find fields', 'parse', 'collect'],
    TaskType.SUMMARIZATION: ['summarize', 'summary', 'shorten', 'condense'],
    TaskType.PLANNING: ['plan', 'design', 'architecture', 'roadmap', 'strategy'],
}


def _cfg_value(config: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in config:
            return config[key]
    return default


def load_model_registry(models_file: Path) -> Dict[str, Any]:
    with models_file.open('r', encoding='utf-8') as handle:
        data = yaml.safe_load(handle) or {}
    return data.get('models', {})


def classify_task(user_goal: str) -> TaskType:
    text = user_goal.lower()
    for task_type, keywords in KEYWORD_MAP.items():
        if any(keyword in text for keyword in keywords):
            return task_type
    return TaskType.GENERAL


def choose_primary_model(task_type: TaskType, registry: Dict[str, Any]) -> str:
    if task_type == TaskType.CODE:
        return _cfg_value(registry['qwen_coder_worker'], 'model_name', 'modelname')
    if task_type in {TaskType.PLANNING, TaskType.SUMMARIZATION}:
        return _cfg_value(registry['qwen_supervisor'], 'model_name', 'modelname')
    return _cfg_value(registry['mistral_worker'], 'model_name', 'modelname')


def choose_fallback_model(primary_model_name: str, registry: Dict[str, Any]) -> str:
    for _, config in registry.items():
        model_name = _cfg_value(config, 'model_name', 'modelname')
        if model_name != primary_model_name:
            continue
        fallback_key = config.get('fallback')
        if fallback_key and fallback_key in registry:
            return _cfg_value(registry[fallback_key], 'model_name', 'modelname')
    return _cfg_value(registry['qwen_supervisor'], 'model_name', 'modelname')


def choose_supervisor_model(registry: Dict[str, Any]) -> str:
    return _cfg_value(registry['qwen_supervisor'], 'model_name', 'modelname')


loadmodelregistry = load_model_registry
classifytask = classify_task
chooseprimarymodel = choose_primary_model
choosefallbackmodel = choose_fallback_model
choosesupervisormodel = choose_supervisor_model
