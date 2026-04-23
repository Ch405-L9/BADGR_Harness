from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def _isolate_state_file(tmp_path, monkeypatch):
    """Redirect STATE_FILE to a temp path so tests never touch the real state."""
    import state.state_manager as sm
    monkeypatch.setattr(sm, "STATE_FILE", tmp_path / "test_runtime_state.json")
