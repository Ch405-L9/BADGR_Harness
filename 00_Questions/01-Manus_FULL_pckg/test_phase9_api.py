"""Phase 9 tests: BADGR Harness HTTP API."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import api
from api import app

client = TestClient(app, raise_server_exceptions=False)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _mock_run_task(result: dict):
    return patch("api.orchestrator.run_task", return_value=result)


_EXTRACTION_RESULT = {
    "task_type": "extraction",
    "summary": "BADGR provides web dev, branding, and SEO.",
    "confidence": 0.98,
    "recommended_action": "Review service catalogue.",
    "needs_clarification": False,
    "clarification_question": None,
    "fields": {"services": ["web", "branding", "SEO"]},
}

_CODE_RESULT = {
    "task_type": "code",
    "summary": "Fixed off-by-one error.",
    "confidence": 0.99,
    "recommended_action": "Apply patch.",
    "needs_clarification": False,
    "clarification_question": None,
    "changes": ["fix loop bound"],
    "code_block": "for i in range(len(items)):",
}


# ── 1. GET /health returns 200 and expected fields ────────────────────────────

def test_health_returns_200():
    with patch("api._check_ollama", return_value=False):
        resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body
    assert body["status"] == "ok"
    assert "ollama_reachable" in body
    assert "rag_db_present" in body
    assert "timestamp" in body


# ── 2. POST /task returns 200 with valid goal ─────────────────────────────────

def test_post_task_success():
    with _mock_run_task(_EXTRACTION_RESULT):
        resp = client.post("/task", json={"goal": "What services does BADGR offer?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["task_type"] == "extraction"
    assert body["confidence"] == 0.98


# ── 3. POST /task with task_type override ─────────────────────────────────────

def test_post_task_with_type_override():
    with _mock_run_task(_CODE_RESULT):
        resp = client.post("/task", json={"goal": "Fix this bug", "task_type": "code"})
    assert resp.status_code == 200
    assert resp.json()["task_type"] == "code"


# ── 4. POST /task with invalid task_type returns 422 ─────────────────────────

def test_post_task_invalid_task_type():
    resp = client.post("/task", json={"goal": "Do something", "task_type": "nonexistent"})
    assert resp.status_code == 422
    assert "task_type" in resp.json()["detail"].lower()


# ── 5. POST /task with empty goal returns 422 ─────────────────────────────────

def test_post_task_empty_goal():
    resp = client.post("/task", json={"goal": ""})
    assert resp.status_code == 422


# ── 6. POST /task with missing goal returns 422 ───────────────────────────────

def test_post_task_missing_goal():
    resp = client.post("/task", json={})
    assert resp.status_code == 422


# ── 7. POST /task source tag is echoed back ───────────────────────────────────

def test_post_task_source_tag_echoed():
    with _mock_run_task(_EXTRACTION_RESULT):
        resp = client.post("/task", json={"goal": "Any goal", "source": "n8n:test"})
    assert resp.status_code == 200
    assert resp.json().get("_source") == "n8n:test"


# ── 8. POST /task orchestrator exception → 500 ───────────────────────────────

def test_post_task_orchestrator_error_returns_500():
    with patch("api.orchestrator.run_task", side_effect=RuntimeError("Ollama down")):
        resp = client.post("/task", json={"goal": "Something"})
    assert resp.status_code == 500
    assert "Ollama down" in resp.json()["detail"]


# ── 9. GET /state returns dict ────────────────────────────────────────────────

def test_get_state_returns_dict():
    mock_state = {"schema_version": "2.0", "lifetime": {"total_tasks": 5}}
    with patch("api._load_state", return_value=mock_state):
        resp = client.get("/state")
    assert resp.status_code == 200
    assert resp.json()["schema_version"] == "2.0"


# ── 10. GET /state with empty state returns message ──────────────────────────

def test_get_state_empty():
    with patch("api._load_state", return_value={}):
        resp = client.get("/state")
    assert resp.status_code == 200
    assert "message" in resp.json()


# ── 11. GET /logs returns today's analysis ───────────────────────────────────

def test_get_logs_today(tmp_path):
    fake_result = {"date": "2026-04-24", "tasks": [], "stats": {"total": 0}}
    with patch("api._today_log", return_value=tmp_path / "nonexistent.jsonl"):
        resp = client.get("/logs")
    assert resp.status_code == 200
    body = resp.json()
    assert "date" in body
    assert "tasks" in body


# ── 12. GET /logs/{date} with valid date returns analysis ─────────────────────

def test_get_logs_specific_date(tmp_path):
    (tmp_path / "logs").mkdir()
    log_file = tmp_path / "logs" / "2026-04-20.jsonl"
    log_file.write_text(
        '{"task_id":"t1","timestamp":"2026-04-20T10:00:00+00:00","action":"task_started",'
        '"status":"started","details":{"task_type":"classification","rag_hit":false}}\n'
        '{"task_id":"t1","timestamp":"2026-04-20T10:00:05+00:00","action":"primary_attempt_valid",'
        '"status":"success","details":{}}\n',
        encoding="utf-8",
    )
    with patch("api._REPO_ROOT", tmp_path):
        resp = client.get("/logs/2026-04-20")
    assert resp.status_code == 200
    body = resp.json()
    assert body["date"] == "2026-04-20"
    assert len(body["tasks"]) == 1


# ── 13. GET /logs/{date} with bad date format returns 422 ────────────────────

def test_get_logs_bad_date_format():
    resp = client.get("/logs/not-a-date")
    assert resp.status_code == 422


# ── 14. GET /logs/{date} for missing log returns 404 ─────────────────────────

def test_get_logs_date_not_found(tmp_path):
    with patch("api._REPO_ROOT", tmp_path):
        resp = client.get("/logs/2020-01-01")
    assert resp.status_code == 404


# ── 15. POST /task needs_clarification passes through ────────────────────────

def test_post_task_clarification_response():
    clarification_result = {
        "status": "needs_clarification",
        "question": "Which service specifically are you asking about?",
    }
    with _mock_run_task(clarification_result):
        resp = client.post("/task", json={"goal": "Tell me more"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "needs_clarification"
    assert "question" in body
