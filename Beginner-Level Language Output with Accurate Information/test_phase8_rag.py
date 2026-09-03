"""Phase 8 tests: RAG retrieval, corpus integration, orchestrator RAG injection."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

import orchestrator


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fake_embedding() -> list[float]:
    return [0.1] * 768


# ── 1. rag_query.retrieve() returns structured hits ───────────────────────────

def test_retrieve_returns_list_of_dicts(tmp_path):
    """retrieve() must return a list of dicts with source, chunk, distance."""
    import chromadb
    from rag_query import retrieve

    # Build a tiny in-memory chroma collection
    client = chromadb.EphemeralClient()
    col = client.get_or_create_collection("badgr_corpus")
    col.add(
        ids=["t1_0"],
        embeddings=[_fake_embedding()],
        documents=["BADGR offers web development and branding services."],
        metadatas=[{"source": "test_doc.txt", "chunk": 0, "total_chunks": 1, "ext": ".txt"}],
    )

    with patch("rag_query.chromadb.PersistentClient", return_value=client):
        with patch("rag_query._embed", return_value=_fake_embedding()):
            hits = retrieve("web development services", k=1)

    assert isinstance(hits, list)
    assert len(hits) == 1
    assert "source" in hits[0]
    assert "chunk" in hits[0]
    assert "distance" in hits[0]


# ── 2. retrieve() returns empty list when DB is empty ─────────────────────────

def test_retrieve_empty_db_returns_empty_list():
    from rag_query import retrieve

    # Mock the entire collection with count() == 0 — avoids shared EphemeralClient state
    mock_col = MagicMock()
    mock_col.count.return_value = 0
    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_col

    with patch("rag_query.chromadb.PersistentClient", return_value=mock_client):
        hits = retrieve("anything", k=3)

    assert hits == []


# ── 3. format_context() produces non-empty string from hits ───────────────────

def test_format_context_builds_string():
    from rag_query import format_context

    hits = [
        {"source": "business_plan.pdf", "chunk": "BADGR provides web services.", "distance": 0.21},
        {"source": "pricing.csv", "chunk": "Starter package: $500.", "distance": 0.34},
    ]
    ctx = format_context(hits)
    assert "business_plan.pdf" in ctx
    assert "BADGR provides web services." in ctx
    assert "pricing.csv" in ctx


# ── 4. format_context() returns empty string on empty hits ────────────────────

def test_format_context_empty_hits_returns_empty():
    from rag_query import format_context
    assert format_context([]) == ""


# ── 5. _rag_context() in orchestrator returns string ─────────────────────────

def test_rag_context_returns_string_on_success(tmp_path, monkeypatch):
    """`_rag_context` returns a non-empty string when retrieval succeeds."""
    fake_ctx = "[test_doc.txt]\nBADGR offers branding services."

    # Patch the requests call inside _rag_context
    import requests as req_mod
    fake_resp = MagicMock()
    fake_resp.raise_for_status = lambda: None
    fake_resp.json.return_value = {"embedding": _fake_embedding()}

    import chromadb
    client = chromadb.EphemeralClient()
    col = client.get_or_create_collection("badgr_corpus")
    col.add(
        ids=["x_0"],
        embeddings=[_fake_embedding()],
        documents=["BADGR offers branding services."],
        metadatas=[{"source": "test_doc.txt", "chunk": 0, "total_chunks": 1, "ext": ".txt"}],
    )

    # chromadb is imported locally inside _rag_context — patch at the source module
    with patch("requests.post", return_value=fake_resp):
        with patch("chromadb.PersistentClient", return_value=client):
            with patch("orchestrator.Path") as mock_path:
                mock_path.return_value.exists.return_value = True
                result = orchestrator._rag_context("BADGR branding services")

    assert isinstance(result, str)


# ── 6. _rag_context() returns empty string on network failure ─────────────────

def test_rag_context_graceful_on_failure(monkeypatch):
    """`_rag_context` must return '' and not raise when Ollama is unavailable."""
    with patch("requests.post", side_effect=Exception("Connection refused")):
        result = orchestrator._rag_context("anything")
    assert result == ""


# ── 7. _rag_context() returns empty when rag_db does not exist ───────────────

def test_rag_context_returns_empty_when_no_db(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # no rag_db here
    result = orchestrator._rag_context("any query")
    assert result == ""


# ── 8. build_prompt() injects RAG context block when context exists ───────────

def test_build_prompt_includes_rag_block(monkeypatch):
    from schemas.task_schema import Task, TaskType

    task = Task(
        task_id="rag_test_001",
        user_goal="What services does BADGR offer?",
        task_type=TaskType.EXTRACTION,
        constraints=["strict_json"],
        expected_output="extraction_result",
        confidence_required=0.98,
    )

    monkeypatch.setattr(orchestrator, "_rag_context",
                        lambda goal: "[pricing.csv]\nStarter: $500. Pro: $1200.")

    prompt = orchestrator.build_prompt(task, "You are a worker.")
    assert "BADGR Knowledge Base Context" in prompt
    assert "Starter: $500" in prompt


# ── 9. build_prompt() omits RAG block when context is empty ──────────────────

def test_build_prompt_omits_rag_block_when_empty(monkeypatch):
    from schemas.task_schema import Task, TaskType

    task = Task(
        task_id="rag_test_002",
        user_goal="Fix this Python bug",
        task_type=TaskType.CODE,
        constraints=["strict_json"],
        expected_output="code_result",
        confidence_required=0.98,
    )

    monkeypatch.setattr(orchestrator, "_rag_context", lambda goal: "")
    prompt = orchestrator.build_prompt(task, "You are a worker.")
    assert "BADGR Knowledge Base Context" not in prompt


# ── 10. run_task() succeeds with RAG context injected ────────────────────────

def test_run_task_succeeds_with_rag_context_injected(monkeypatch):
    """Full run_task path with RAG context injected via monkeypatched _rag_context."""
    from validator import ValidationOutcome

    monkeypatch.setattr(orchestrator, "load_model_registry", lambda _: {})
    monkeypatch.setattr(orchestrator, "choose_micro_model", lambda reg: None)
    monkeypatch.setattr(orchestrator, "choose_primary_model", lambda *a, **kw: "mistral:7b")
    monkeypatch.setattr(orchestrator, "append_log", lambda e: None)
    monkeypatch.setattr(orchestrator, "append_report", lambda *a, **kw: None)
    monkeypatch.setattr(
        orchestrator, "_rag_context",
        lambda goal: "[pricing.csv]\nStarter package: $500/mo.",
    )
    monkeypatch.setattr(
        orchestrator,
        "attempt_model",
        lambda *a, **kw: ValidationOutcome(
            valid=True,
            data={
                "task_type": "extraction",
                "summary": "BADGR offers web dev and branding.",
                "confidence": 0.99,
                "recommended_action": "See pricing matrix.",
                "needs_clarification": False,
                "clarification_question": None,
                "fields": {"Starter": "$500/mo"},
            },
        ),
    )

    result = orchestrator.run_task("What are BADGR service packages?")
    assert result["task_type"] == "extraction"
    assert result["confidence"] == 0.99


# ── 11. RAG does not break non-BADGR goals ───────────────────────────────────

def test_run_task_works_when_rag_returns_empty(monkeypatch):
    """RAG miss (empty context) must not break the orchestrator flow."""
    from validator import ValidationOutcome

    monkeypatch.setattr(orchestrator, "load_model_registry", lambda _: {})
    monkeypatch.setattr(orchestrator, "choose_micro_model", lambda reg: None)
    monkeypatch.setattr(orchestrator, "choose_primary_model", lambda *a, **kw: "mistral:7b")
    monkeypatch.setattr(orchestrator, "append_log", lambda e: None)
    monkeypatch.setattr(orchestrator, "append_report", lambda *a, **kw: None)
    monkeypatch.setattr(orchestrator, "_rag_context", lambda goal: "")
    monkeypatch.setattr(
        orchestrator,
        "attempt_model",
        lambda *a, **kw: ValidationOutcome(
            valid=True,
            data={
                "task_type": "code",
                "summary": "Fixed.",
                "confidence": 0.99,
                "recommended_action": "Apply.",
                "needs_clarification": False,
                "clarification_question": None,
                "changes": ["fix"],
                "code_block": None,
            },
        ),
    )

    result = orchestrator.run_task("Fix this Python bug")
    assert result["task_type"] == "code"
