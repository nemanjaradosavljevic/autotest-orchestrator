"""
Results - summarizing, saving, and history of test results.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Union

from test_engine.runner import TestResult


def summarize(results: List[TestResult]) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate_pct": round(100 * passed / total, 2) if total else 0.0,
    }


def save_results(results: List[TestResult], path: Union[str, Path]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in results], f, indent=2, ensure_ascii=False)


def failed_only(results: List[TestResult]) -> List[TestResult]:
    return [r for r in results if not r.passed]


# ---------------------------------------------------------------------------
# Run history - used for the trend display in the dashboard (pass rate over
# time). Independent of save_results/latest_<usecase>_run.json above: that
# file gets OVERWRITTEN each time (only the latest run), while the history
# gets APPENDED to (every run stays recorded). The format is JSON Lines (one
# line = one run) so that appending is simple and safe - append to the end
# of the file, with no need to read/rewrite the whole file every time (a
# full JSON array would require reading the whole file, modifying it in
# memory, and writing it back, risking corruption if the process is
# interrupted mid-write; a jsonl append is a single atomic write of one
# line).
#
# This is written (like summarize/save_results above) to work for any use
# case - main.py (CLI) and api/main.py (dashboard) both call it, so the
# trend covers runs started in any way.
# ---------------------------------------------------------------------------


def _history_path(history_dir: Union[str, Path], usecase: str) -> Path:
    return Path(history_dir) / f"history_{usecase}.jsonl"


def append_history_entry(
    history_dir: Union[str, Path],
    usecase: str,
    count: int,
    seed: int,
    summary: dict,
    patterns: dict,
) -> dict:
    """Appends one line to the run history for the given use case. Returns
    the written entry (useful e.g. so the API immediately knows the exact
    timestamp without having to re-read the file)."""
    path = _history_path(history_dir, usecase)
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": count,
        "seed": seed,
        "total": summary["total"],
        "passed": summary["passed"],
        "failed": summary["failed"],
        "pass_rate_pct": summary["pass_rate_pct"],
        "patterns": patterns,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def read_history(history_dir: Union[str, Path], usecase: str, limit: int) -> List[dict]:
    """Reads the run history for the given use case - returns at most
    `limit` of the most recent entries, ordered from oldest to newest
    (convenient for plotting a trend left-to-right). If the file doesn't
    exist, returns an empty list. An invalid/incomplete line (e.g. the file
    got interrupted mid-write) is skipped instead of bringing down the whole
    dashboard."""
    path = _history_path(history_dir, usecase)
    if not path.exists():
        return []
    entries: List[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries[-limit:] if limit > 0 else entries
