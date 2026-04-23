from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

try:
    from schemas.task_schema import TaskType
except ImportError:
    from schemas.taskschema import TaskType


KEYWORD_MAP = {
    TaskType.CODE: ["code", "bug", "fix", "function", "refactor", "python", "script", "syntax"],
    TaskType.CLASSIFICATION: ["classify", "category", "categorize", "route", "label", "tag"],
    TaskType.EXTRACTION: ["extract", "pull", "find fields", "parse", "collect"],
    TaskType.SUMMARIZATION: ["summarize", "summary", "shorten", "condense"],
    TaskType.PLANNING: ["plan", "design", "architecture", "roadmap", "strategy"],
}

# Keywords that signal BADGR domain work — only then should badgr_analyst be used.
# Kept intentionally specific to avoid false positives on generic business language.
BADGR_DOMAIN_KEYWORDS = [
    # Trading / market intel
    "trading", "swing trade", "stock", "equity", "ticker", "candlestick",
    "indicator", "momentum", "breakout", "support level", "resistance",
    "market data", "market intel", "volatility", "moving average",
    # Lead generation
    "lead generation", "leads", "prospect", "pipeline", "outreach", "crm",
    # Campaign / ad performance
    "campaign", "ad performance", "click-through", "engagement rate",
    "impression", "social media analytics",
    # Web performance
    "web performance", "page speed", "bounce rate", "seo",
    # BADGR brand
    "badgr",
]


def _model_name(config: Dict[str, Any]) -> str:
    if "model_name" in config:
        return config["model_name"]
    if "modelname" in config:
        return config["modelname"]
    raise KeyError("Model config missing 'model_name'/'modelname'")


def _registry_get(registry: Dict[str, Any], *keys: str) -> Dict[str, Any]:
    for key in keys:
        if key in registry:
            return registry[key]
    raise KeyError(f"None of the registry keys were found: {keys}")


def _registry_find_role(registry: Dict[str, Any], role: str) -> Optional[Dict[str, Any]]:
    """Return first registry entry whose roles list contains `role`, or None."""
    for config in registry.values():
        if role in config.get("roles", []):
            return config
    return None


def is_badgr_domain(user_goal: str) -> bool:
    """Return True if the goal contains BADGR-domain signals warranting the analyst model."""
    text = user_goal.lower()
    return any(kw in text for kw in BADGR_DOMAIN_KEYWORDS)


def load_model_registry(models_file: Path) -> Dict[str, Any]:
    with models_file.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data.get("models", {})


def classify_task(user_goal: str) -> TaskType:
    text = user_goal.lower()
    for task_type, keywords in KEYWORD_MAP.items():
        if any(keyword in text for keyword in keywords):
            return task_type
    return TaskType.GENERAL


def choose_primary_model(task_type: TaskType, registry: Dict[str, Any], user_goal: str = "") -> str:
    if task_type == TaskType.CODE:
        return _model_name(
            _registry_get(registry, "qwen_coder_worker", "qwencoderworker")
        )

    if task_type in {TaskType.PLANNING, TaskType.SUMMARIZATION}:
        return _model_name(
            _registry_get(registry, "qwen_supervisor", "qwensupervisor")
        )

    if task_type in {TaskType.CLASSIFICATION, TaskType.EXTRACTION}:
        # Only route to the domain specialist when the goal is clearly BADGR-domain work.
        # Generic classification/extraction stays on the general worker.
        if user_goal and is_badgr_domain(user_goal):
            analyst = _registry_find_role(registry, "analyst")
            if analyst:
                return _model_name(analyst)
        return _model_name(
            _registry_get(registry, "mistral_worker", "mistralworker")
        )

    return _model_name(
        _registry_get(registry, "mistral_worker", "mistralworker")
    )


def choose_fallback_model(primary_model_name: str, registry: Dict[str, Any]) -> str:
    for config in registry.values():
        if _model_name(config) == primary_model_name:
            fallback_key = config.get("fallback")
            if fallback_key and fallback_key in registry:
                return _model_name(registry[fallback_key])
            break

    return _model_name(
        _registry_get(registry, "qwen_supervisor", "qwensupervisor")
    )


def choose_supervisor_model(registry: Dict[str, Any]) -> str:
    return _model_name(
        _registry_get(registry, "qwen_supervisor", "qwensupervisor")
    )


def choose_micro_model(registry: Dict[str, Any]) -> Optional[str]:
    """Return the micro-classifier model name if one is registered, else None."""
    config = _registry_find_role(registry, "micro_classifier")
    if config:
        return _model_name(config)
    return None


# Backward-compatible aliases
KEYWORDMAP = KEYWORD_MAP
BADGRDOMAINKEYWORDS = BADGR_DOMAIN_KEYWORDS
isbadgrdomain = is_badgr_domain
loadmodelregistry = load_model_registry
classifytask = classify_task
chooseprimarymodel = choose_primary_model
choosefallbackmodel = choose_fallback_model
choosesupervisormodel = choose_supervisor_model
choosemicromodel = choose_micro_model
