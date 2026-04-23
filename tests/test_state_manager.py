"""Tests for state/state_manager.py — load, save, record_task, model_summary."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from state.state_manager import (
    SCHEMA_VERSION,
    _empty_state,
    _migrate,
    load_state,
    model_summary,
    record_task,
    save_state,
)


@pytest.fixture
def state_file(tmp_path, monkeypatch):
    """Redirect STATE_FILE to a temp path for each test."""
    import state.state_manager as sm
    target = tmp_path / "test_runtime_state.json"
    monkeypatch.setattr(sm, "STATE_FILE", target)
    return target


# ── load / save ──────────────────────────────────────────────────────────────

def test_load_state_missing_file_returns_empty(state_file):
    state = load_state()
    assert state["schema_version"] == SCHEMA_VERSION
    assert state["lifetime"]["total_tasks"] == 0


def test_save_and_reload(state_file):
    original = _empty_state()
    original["lifetime"]["total_tasks"] = 5
    save_state(original)
    reloaded = load_state()
    assert reloaded["lifetime"]["total_tasks"] == 5


def test_load_corrupted_file_returns_empty(state_file):
    state_file.write_text("NOT JSON", encoding="utf-8")
    state = load_state()
    assert state["lifetime"]["total_tasks"] == 0


def test_load_migrates_old_schema(state_file):
    old = {"schema_version": "1.0", "lifetime": {"total_tasks": 7, "success": 3}}
    state_file.write_text(json.dumps(old), encoding="utf-8")
    state = load_state()
    assert state["schema_version"] == SCHEMA_VERSION
    assert state["lifetime"]["total_tasks"] == 7
    assert state["lifetime"]["success"] == 3


# ── record_task ───────────────────────────────────────────────────────────────

def test_record_task_increments_lifetime(state_file):
    record_task(
        task_id="t1",
        task_type="classification",
        status="success",
        primary_model="mistral:7b",
        routing_method="keyword",
        models_tried=["mistral:7b"],
        latency_s=1.5,
    )
    state = load_state()
    assert state["lifetime"]["total_tasks"] == 1
    assert state["lifetime"]["success"] == 1


def test_record_task_failed_increments_failed(state_file):
    record_task(
        task_id="t2",
        task_type="code",
        status="failed",
        primary_model="qwen2.5-coder:7b",
        routing_method="keyword",
        models_tried=["qwen2.5-coder:7b", "mistral:7b", "qwen2.5:14b"],
        latency_s=95.0,
    )
    state = load_state()
    assert state["lifetime"]["failed"] == 1
    assert state["lifetime"]["success"] == 0


def test_record_task_needs_clarification(state_file):
    record_task(
        task_id="t3",
        task_type="planning",
        status="needs_clarification",
        primary_model="qwen2.5:14b",
        routing_method="keyword",
        models_tried=["qwen2.5:14b"],
        latency_s=12.0,
    )
    state = load_state()
    assert state["lifetime"]["needs_clarification"] == 1


def test_record_task_model_stats_primary(state_file):
    record_task(
        task_id="t4",
        task_type="classification",
        status="success",
        primary_model="mistral:7b",
        routing_method="keyword",
        models_tried=["mistral:7b"],
        latency_s=20.0,
    )
    state = load_state()
    stats = state["model_stats"]["mistral:7b"]
    assert stats["uses"] == 1
    assert stats["primary_uses"] == 1
    assert stats["fallback_uses"] == 0
    assert stats["successes"] == 1
    assert stats["failures"] == 0
    assert stats["total_latency_s"] == 20.0


def test_record_task_model_stats_fallback_chain(state_file):
    record_task(
        task_id="t5",
        task_type="code",
        status="success",
        primary_model="qwen2.5-coder:7b",
        routing_method="keyword",
        models_tried=["qwen2.5-coder:7b", "mistral:7b"],
        latency_s=55.0,
    )
    state = load_state()
    coder = state["model_stats"]["qwen2.5-coder:7b"]
    mistral = state["model_stats"]["mistral:7b"]

    assert coder["primary_uses"] == 1
    assert coder["fallback_uses"] == 0
    assert coder["successes"] == 0  # not the last in chain
    assert coder["failures"] == 0

    assert mistral["fallback_uses"] == 1
    assert mistral["successes"] == 1  # last in chain gets credit
    assert mistral["total_latency_s"] == 55.0


def test_record_task_error_patterns(state_file):
    record_task(
        task_id="t6",
        task_type="code",
        status="failed",
        primary_model="qwen2.5-coder:7b",
        routing_method="keyword",
        models_tried=["qwen2.5-coder:7b"],
        latency_s=10.0,
        errors=["Invalid JSON: Expecting value", "Invalid JSON: Expecting value"],
    )
    state = load_state()
    patterns = state["error_patterns"]
    assert "Invalid JSON" in patterns
    assert patterns["Invalid JSON"] == 2


def test_record_task_recent_tasks_appended(state_file):
    record_task(
        task_id="task_abc",
        task_type="summarization",
        status="success",
        primary_model="mistral:7b",
        routing_method="model",
        models_tried=["mistral:7b"],
        latency_s=8.0,
    )
    state = load_state()
    assert len(state["recent_tasks"]) == 1
    entry = state["recent_tasks"][0]
    assert entry["task_id"] == "task_abc"
    assert entry["routing_method"] == "model"


def test_record_task_recent_tasks_capped(state_file):
    import state.state_manager as sm
    original_max = sm.MAX_RECENT_TASKS
    sm.MAX_RECENT_TASKS = 5
    try:
        for i in range(7):
            record_task(
                task_id=f"task_{i:03d}",
                task_type="classification",
                status="success",
                primary_model="mistral:7b",
                routing_method="keyword",
                models_tried=["mistral:7b"],
                latency_s=1.0,
            )
        state = load_state()
        assert len(state["recent_tasks"]) == 5
        assert state["recent_tasks"][0]["task_id"] == "task_002"
    finally:
        sm.MAX_RECENT_TASKS = original_max


# ── model_summary ─────────────────────────────────────────────────────────────

def test_model_summary_sorted_by_uses(state_file):
    for i in range(3):
        record_task(
            task_id=f"a{i}",
            task_type="classification",
            status="success",
            primary_model="mistral:7b",
            routing_method="keyword",
            models_tried=["mistral:7b"],
            latency_s=5.0,
        )
    record_task(
        task_id="b0",
        task_type="code",
        status="success",
        primary_model="qwen2.5-coder:7b",
        routing_method="keyword",
        models_tried=["qwen2.5-coder:7b"],
        latency_s=10.0,
    )
    state = load_state()
    rows = model_summary(state)
    assert rows[0]["model"] == "mistral:7b"
    assert rows[0]["uses"] == 3
    assert rows[1]["model"] == "qwen2.5-coder:7b"
    assert rows[1]["uses"] == 1


def test_model_summary_avg_latency(state_file):
    record_task(
        task_id="l1",
        task_type="classification",
        status="success",
        primary_model="mistral:7b",
        routing_method="keyword",
        models_tried=["mistral:7b"],
        latency_s=10.0,
    )
    record_task(
        task_id="l2",
        task_type="classification",
        status="success",
        primary_model="mistral:7b",
        routing_method="keyword",
        models_tried=["mistral:7b"],
        latency_s=20.0,
    )
    state = load_state()
    rows = model_summary(state)
    assert rows[0]["avg_latency_s"] == 15.0
