"""
harness_inspect.py — BADGR harness log analysis tool.

Usage:
    python harness_inspect.py                  # today's log
    python harness_inspect.py 2026-04-23       # specific date
    python harness_inspect.py --all            # all log files

Output: per-task summary table + aggregate stats.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOGS_DIR = Path(__file__).resolve().parent / "logs"
STATE_DIR = Path(__file__).resolve().parent / "state"


def _load_events(log_file: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with log_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return events


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def _seconds_between(start: str, end: str) -> float:
    return (_parse_ts(end) - _parse_ts(start)).total_seconds()


def _terminal_status(events: list[dict]) -> str:
    """Return the final meaningful status from the task event chain."""
    priority = ["failed", "needs_clarification", "success", "fallback", "escalated", "retry"]
    seen = {e["status"] for e in events}
    for s in priority:
        if s in seen:
            return s
    return events[-1]["status"] if events else "unknown"


def _models_used(events: list[dict]) -> list[str]:
    seen: list[str] = []
    for e in events:
        m = e.get("model_used")
        if m and m not in seen:
            seen.append(m)
    return seen


def _errors(events: list[dict]) -> list[str]:
    return [e["error_message"] for e in events if e.get("error_message")]


def analyze(log_file: Path) -> dict[str, Any]:
    events = _load_events(log_file)
    if not events:
        return {"date": log_file.stem, "tasks": [], "stats": {}}

    by_task: dict[str, list[dict]] = defaultdict(list)
    for ev in events:
        by_task[ev["task_id"]].append(ev)

    tasks = []
    outcome_counts: dict[str, int] = defaultdict(int)
    total_latency = 0.0
    completed = 0

    for task_id, tevents in by_task.items():
        tevents.sort(key=lambda e: e["timestamp"])
        task_type = tevents[0].get("details", {}).get("task_type", "unknown")
        status = _terminal_status(tevents)
        models = _models_used(tevents)
        errors = _errors(tevents)
        start_ts = tevents[0]["timestamp"]
        end_ts = tevents[-1]["timestamp"]
        latency = _seconds_between(start_ts, end_ts)

        complete = any(
            e["action"] in {
                "primary_attempt_valid", "primary_retry_valid",
                "fallback_valid", "supervisor_valid",
                "clarification_required", "task_failed",
            }
            for e in tevents
        )

        outcome_counts[status] += 1
        if complete:
            total_latency += latency
            completed += 1

        tasks.append({
            "task_id": task_id,
            "task_type": task_type,
            "status": status,
            "complete": complete,
            "models": models,
            "latency_s": round(latency, 1),
            "retries": sum(1 for e in tevents if e["action"] == "primary_attempt_invalid"),
            "escalations": sum(1 for e in tevents if e["action"] == "supervisor_selected"),
            "errors": errors,
        })

    avg_latency = round(total_latency / completed, 1) if completed else 0.0

    return {
        "date": log_file.stem,
        "tasks": tasks,
        "stats": {
            "total": len(tasks),
            "completed": completed,
            "incomplete": len(tasks) - completed,
            "by_status": dict(outcome_counts),
            "avg_latency_s": avg_latency,
        },
    }


def _status_icon(status: str) -> str:
    return {
        "success": "OK",
        "needs_clarification": "ASK",
        "failed": "FAIL",
        "fallback": "FALL",
        "escalated": "ESC",
        "retry": "RETRY",
    }.get(status, status.upper()[:4])


def print_report(result: dict[str, Any]) -> None:
    date = result["date"]
    tasks = result["tasks"]
    stats = result["stats"]

    print(f"\n{'='*64}")
    print(f"  BADGR Harness Log — {date}")
    print(f"{'='*64}")

    if not tasks:
        print("  No events found.\n")
        return

    # Per-task table
    print(f"\n{'TASK ID':<28} {'TYPE':<14} {'STATUS':<8} {'LATENCY':>8}  {'MODELS'}")
    print("-" * 80)
    for t in sorted(tasks, key=lambda x: x["task_id"]):
        icon = _status_icon(t["status"])
        model_str = " → ".join(t["models"]) if t["models"] else "—"
        complete_mark = "" if t["complete"] else " [incomplete]"
        print(
            f"  {t['task_id'][-20:]:<26} {t['task_type']:<14} {icon:<8} "
            f"{t['latency_s']:>6.1f}s  {model_str}{complete_mark}"
        )
        if t["retries"]:
            print(f"    {'':26} retries={t['retries']}, escalations={t['escalations']}")
        for err in t["errors"]:
            print(f"    {'':26} error: {err[:70]}")

    # Aggregate stats
    s = stats
    print(f"\n{'─'*64}")
    print(f"  Tasks total:     {s['total']}")
    print(f"  Completed:       {s['completed']}")
    if s["incomplete"]:
        print(f"  Incomplete:      {s['incomplete']}  (shell or run interrupted)")
    print(f"  Avg latency:     {s['avg_latency_s']}s")
    print(f"  By outcome:      ", end="")
    print("  ".join(f"{k}={v}" for k, v in sorted(s.get("by_status", {}).items())))
    print()


def _load_state() -> dict[str, Any]:
    state_file = STATE_DIR / "runtime_state.json"
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def print_state_summary(state: dict[str, Any]) -> None:
    if not state or state.get("schema_version") != "2.0":
        return

    lifetime = state.get("lifetime", {})
    total = lifetime.get("total_tasks", 0)
    if total == 0:
        return

    print(f"\n{'='*64}")
    print("  BADGR Harness — Lifetime State Summary")
    print(f"{'='*64}")

    success = lifetime.get("success", 0)
    clarify = lifetime.get("needs_clarification", 0)
    failed = lifetime.get("failed", 0)
    success_rate = round(100 * success / total, 1) if total else 0.0
    print(f"\n  Total tasks:     {total}")
    print(f"  Success:         {success}  ({success_rate}%)")
    if clarify:
        print(f"  Clarification:   {clarify}")
    if failed:
        print(f"  Failed:          {failed}")

    model_rows = []
    for model_name, stats in state.get("model_stats", {}).items():
        uses = stats.get("uses", 0)
        successes = stats.get("successes", 0)
        failures = stats.get("failures", 0)
        outcome_total = successes + failures
        total_lat = stats.get("total_latency_s", 0.0)
        avg_lat = round(total_lat / outcome_total, 1) if outcome_total else 0.0
        model_rows.append((uses, model_name, stats.get("primary_uses", 0),
                           stats.get("fallback_uses", 0), successes, failures, avg_lat))
    model_rows.sort(reverse=True)

    if model_rows:
        print(f"\n  {'MODEL':<30} {'USES':>5} {'PRIM':>5} {'FALL':>5} {'OK':>5} {'ERR':>5} {'AVG_LAT':>8}")
        print(f"  {'-'*62}")
        for uses, name, prim, fall, ok, err, lat in model_rows:
            print(f"  {name:<30} {uses:>5} {prim:>5} {fall:>5} {ok:>5} {err:>5} {lat:>7.1f}s")

    patterns = state.get("error_patterns", {})
    if patterns:
        top = sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"\n  Top error patterns:")
        for pat, count in top:
            print(f"    [{count:>3}x] {pat[:60]}")

    updated = state.get("last_updated", "")
    if updated:
        print(f"\n  State last updated: {updated[:19]} UTC")
    print()


def main() -> None:
    args = sys.argv[1:]

    if "--all" in args:
        log_files = sorted(LOGS_DIR.glob("*.jsonl"))
    elif args and not args[0].startswith("-"):
        log_files = [LOGS_DIR / f"{args[0]}.jsonl"]
    else:
        today = datetime.now(timezone.utc).date().isoformat()
        log_files = [LOGS_DIR / f"{today}.jsonl"]

    if not log_files:
        print("No log files found.")
        return

    for lf in log_files:
        if lf.exists():
            print_report(analyze(lf))
        else:
            print(f"Log not found: {lf}")

    print_state_summary(_load_state())


if __name__ == "__main__":
    main()
