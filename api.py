"""
api.py — BADGR Harness HTTP API (Phase 9).

Exposes run_task() as a REST service that n8n (or any HTTP client) can call.

Start with:
    uvicorn api:app --host 0.0.0.0 --port 8765 --reload

Endpoints:
    POST /task          Submit a goal; returns structured result
    GET  /health        Liveness check + Ollama reachability
    GET  /state         Lifetime stats from runtime_state.json
    GET  /logs          Today's log analysis (harness_inspect data)
    GET  /logs/{date}   Specific date log, e.g. /logs/2026-04-24
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Ensure repo root is on the path when api.py is invoked via uvicorn from
# a directory that isn't the repo root.
_REPO_ROOT = Path(__file__).resolve().parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

os.chdir(_REPO_ROOT)  # orchestrator uses relative paths for rag_db, logs, etc.

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import orchestrator
from harness_inspect import analyze, _load_state


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="BADGR Harness API",
    description="Local LLM orchestration layer for BADGR LLC business intelligence.",
    version="1.0.0",
)


# ── Request / response models ─────────────────────────────────────────────────

class TaskRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=4000, description="The task goal in plain English")
    task_type: Optional[str] = Field(
        None,
        description="Override task type: code, classification, extraction, summarization, planning",
    )
    source: Optional[str] = Field(None, description="Caller identity tag for traceability (e.g. 'n8n:email_draft')")


class TaskResponse(BaseModel):
    task_type: str
    summary: str
    confidence: float
    recommended_action: str
    needs_clarification: bool
    clarification_question: Optional[str]
    status: Optional[str] = None

    model_config = {"extra": "allow"}  # pass through task-type-specific fields


class HealthResponse(BaseModel):
    status: str
    ollama_reachable: bool
    rag_db_present: bool
    timestamp: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _check_ollama() -> bool:
    try:
        import urllib.request as _ur
        with _ur.urlopen("http://localhost:11434/api/tags", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def _today_log() -> Path:
    return _REPO_ROOT / "logs" / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["system"])
def health():
    """Liveness + dependency check. n8n can poll this before submitting tasks."""
    return {
        "status": "ok",
        "ollama_reachable": _check_ollama(),
        "rag_db_present": (_REPO_ROOT / "rag_db").exists(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/task", tags=["harness"])
def run_task(req: TaskRequest):
    """
    Submit a plain-English goal to the BADGR harness.

    The orchestrator classifies the task, routes to the best local model,
    retries/escalates on failure, and returns a structured JSON result.
    """
    task_type_override = None
    if req.task_type:
        try:
            from schemas.task_schema import TaskType
            task_type_override = TaskType(req.task_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown task_type '{req.task_type}'. "
                       "Valid: code, classification, extraction, summarization, planning",
            )

    try:
        result: dict[str, Any] = orchestrator.run_task(req.goal)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Attach source tag if provided — useful for n8n workflow tracing
    if req.source:
        result["_source"] = req.source

    return JSONResponse(content=result)


@app.get("/state", tags=["system"])
def get_state():
    """Return the lifetime stats from runtime_state.json."""
    state = _load_state()
    if not state:
        return {"message": "No state file found yet."}
    return JSONResponse(content=state)


@app.get("/logs", tags=["system"])
def get_logs_today():
    """Return today's log analysis (same data as harness_inspect)."""
    lf = _today_log()
    if not lf.exists():
        today = datetime.now(timezone.utc).date().isoformat()
        return {"date": today, "tasks": [], "stats": {}}
    return JSONResponse(content=analyze(lf))


@app.get("/logs/{date}", tags=["system"])
def get_logs_date(date: str):
    """Return log analysis for a specific date (YYYY-MM-DD)."""
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=422, detail="Date must be YYYY-MM-DD")
    lf = _REPO_ROOT / "logs" / f"{date}.jsonl"
    if not lf.exists():
        raise HTTPException(status_code=404, detail=f"No log for {date}")
    return JSONResponse(content=analyze(lf))
