"""
state_manager.py — BADGR harness runtime state persistence.

Tracks lifetime stats, per-model performance, recent task lineage,
and recurring error patterns across all harness runs.

State is stored in state/runtime_state.json and updated after each
completed task. The file is human-readable and safe to inspect at
any time.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

STATE_FILE = Path(__file__).resolve().parent / "runtime_state.json"
SCHEMA_VERSION = "2.0"
MAX_RECENT_TASKS = 100


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_state() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "last_updated": _utc_now(),
        "lifetime": {
            "total_tasks": 0,
            "success": 0,
            "needs_clarification": 0,
            "failed": 0,
        },
        "model_stats": {},
        "recent_tasks": [],
        "error_patterns": {},
    }


def load_state() -> Dict[str, Any]:
    """Load state from disk. Returns empty state if file is missing or unreadable."""
    if not STATE_FILE.exists():
        return _empty_state()
    try:
        with STATE_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("schema_version") != SCHEMA_VERSION:
            return _migrate(data)
        return data
    except (json.JSONDecodeError, KeyError, TypeError):
        return _empty_state()


def save_state(state: Dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["last_updated"] = _utc_now()
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def _migrate(old: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate legacy state (schema v1 / placeholder) to v2."""
    fresh = _empty_state()
    # Carry over any lifetime counts that might exist
    if isinstance(old.get("lifetime"), dict):
        for key in fresh["lifetime"]:
            if key in old["lifetime"]:
                fresh["lifetime"][key] = old["lifetime"][key]
    return fresh


def record_task(
    *,
    task_id: str,
    task_type: str,
    status: str,
    primary_model: str,
    routing_method: str,
    models_tried: List[str],
    latency_s: float,
    errors: Optional[List[str]] = None,
) -> None:
    """Record a completed task into the persistent state file."""
    state = load_state()

    # Lifetime counters
    state["lifetime"]["total_tasks"] += 1
    outcome_key = (
        "success" if status == "success"
        else "needs_clarification" if status == "needs_clarification"
        else "failed"
    )
    state["lifetime"][outcome_key] = state["lifetime"].get(outcome_key, 0) + 1

    # Per-model stats
    model_stats: Dict[str, Any] = state.setdefault("model_stats", {})
    for i, model in enumerate(models_tried):
        entry = model_stats.setdefault(model, {
            "uses": 0, "primary_uses": 0, "fallback_uses": 0,
            "successes": 0, "failures": 0, "total_latency_s": 0.0,
        })
        entry["uses"] += 1
        if i == 0:
            entry["primary_uses"] += 1
        else:
            entry["fallback_uses"] += 1
        # Only the last model in the chain gets credit for outcome
        if i == len(models_tried) - 1:
            if status in {"success", "needs_clarification"}:
                entry["successes"] += 1
            else:
                entry["failures"] += 1
            entry["total_latency_s"] = round(entry.get("total_latency_s", 0.0) + latency_s, 2)

    # Recent task lineage (capped)
    lineage: List[Dict[str, Any]] = state.setdefault("recent_tasks", [])
    lineage.append({
        "task_id": task_id,
        "task_type": task_type,
        "status": status,
        "primary_model": primary_model,
        "routing_method": routing_method,
        "models_tried": models_tried,
        "latency_s": round(latency_s, 1),
        "timestamp": _utc_now(),
    })
    if len(lineage) > MAX_RECENT_TASKS:
        state["recent_tasks"] = lineage[-MAX_RECENT_TASKS:]

    # Error pattern tracking
    if errors:
        patterns: Dict[str, int] = state.setdefault("error_patterns", {})
        for err in errors:
            # Bucket by the first meaningful segment of the error
            key = err.split(":")[0].strip() if ":" in err else err[:60].strip()
            patterns[key] = patterns.get(key, 0) + 1

    save_state(state)


def model_summary(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return per-model stats sorted by total uses descending."""
    rows = []
    for model_name, stats in state.get("model_stats", {}).items():
        uses = stats.get("uses", 0)
        successes = stats.get("successes", 0)
        total_latency = stats.get("total_latency_s", 0.0)
        success_count = stats.get("successes", 0) + stats.get("failures", 0)
        avg_latency = round(total_latency / success_count, 1) if success_count else 0.0
        rows.append({
            "model": model_name,
            "uses": uses,
            "primary": stats.get("primary_uses", 0),
            "fallback": stats.get("fallback_uses", 0),
            "successes": successes,
            "failures": stats.get("failures", 0),
            "avg_latency_s": avg_latency,
        })
    return sorted(rows, key=lambda r: r["uses"], reverse=True)
