"""
Tests for run history (test_engine/results.py: append_history_entry /
read_history) - used for the "Trend over time" panel in the dashboard.

Each test runs in its own temporary directory (tempfile.TemporaryDirectory),
so the tests don't touch the project's actual results/ folder and don't depend
on each other.
"""

import json
import os
import tempfile

from test_engine.results import append_history_entry, read_history


def _sample_summary(passed=90, failed=10):
    total = passed + failed
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate_pct": round(100 * passed / total, 2),
    }


def test_read_history_empty_when_no_file():
    with tempfile.TemporaryDirectory() as d:
        assert read_history(d, "aeb", 30) == []


def test_append_then_read_round_trip():
    with tempfile.TemporaryDirectory() as d:
        entry = append_history_entry(d, "aeb", count=1000, seed=42, summary=_sample_summary(), patterns={"x": 10})
        assert entry["count"] == 1000
        assert entry["seed"] == 42
        assert "timestamp" in entry

        entries = read_history(d, "aeb", 30)
        assert len(entries) == 1
        assert entries[0]["count"] == 1000


def test_read_history_oldest_first_and_respects_limit():
    with tempfile.TemporaryDirectory() as d:
        for i in range(5):
            append_history_entry(d, "aeb", count=100 + i, seed=i, summary=_sample_summary(), patterns={})

        all_entries = read_history(d, "aeb", 30)
        assert [e["count"] for e in all_entries] == [100, 101, 102, 103, 104]

        limited = read_history(d, "aeb", 2)
        assert [e["count"] for e in limited] == [103, 104]


def test_history_is_isolated_per_usecase():
    with tempfile.TemporaryDirectory() as d:
        append_history_entry(d, "aeb", count=1, seed=1, summary=_sample_summary(), patterns={})
        assert len(read_history(d, "aeb", 30)) == 1
        assert read_history(d, "lka", 30) == []
        assert read_history(d, "acc", 30) == []


def test_corrupted_line_is_skipped_not_fatal():
    with tempfile.TemporaryDirectory() as d:
        append_history_entry(d, "aeb", count=1, seed=1, summary=_sample_summary(), patterns={})
        path = os.path.join(d, "history_aeb.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write("not valid json\n")
            f.write("\n")  # blank line should also be skipped, not error

        entries = read_history(d, "aeb", 30)
        assert len(entries) == 1


def test_entry_written_to_disk_matches_jsonl_format():
    with tempfile.TemporaryDirectory() as d:
        append_history_entry(d, "acc", count=5, seed=9, summary=_sample_summary(80, 20), patterns={"fast_closing": 5})
        path = os.path.join(d, "history_acc.jsonl")
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["failed"] == 20
        assert record["patterns"] == {"fast_closing": 5}
