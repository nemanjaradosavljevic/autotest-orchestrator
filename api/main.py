"""
Dashboard API - a FastAPI application that exposes the test engine over
HTTP, so dashboard/index.html can trigger test runs and display results in
the browser (Phase 5 of the project roadmap).

Running it (from the project root folder, with the venv activated):
    uvicorn api.main:app --reload

Then open http://127.0.0.1:8000 in the browser.
"""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from analytics.acc_failures import failure_pattern_summary as acc_failure_pattern_summary
from analytics.acc_failures import group_failures as acc_group_failures
from analytics.failures import failure_pattern_summary, group_failures
from analytics.lka_failures import failure_pattern_summary as lka_failure_pattern_summary
from analytics.lka_failures import group_failures as lka_group_failures
from config import MAX_SCENARIO_COUNT, RUN_HISTORY_DISPLAY_LIMIT
from critical_search.acc import find_critical_scenarios as find_acc_critical_scenarios
from critical_search.aeb import find_critical_scenarios as find_aeb_critical_scenarios
from critical_search.lka import find_critical_scenarios as find_lka_critical_scenarios
from scenarios.generator import (
    generate_edge_case_acc_scenarios,
    generate_edge_case_lka_scenarios,
    generate_edge_case_scenarios,
    generate_random_acc_scenarios,
    generate_random_lka_scenarios,
    generate_random_scenarios,
)
from test_engine.acc_runner import ACCTestEngine
from test_engine.lka_runner import LKATestEngine
from test_engine.results import append_history_entry, read_history, save_results, summarize
from test_engine.runner import TestEngine

BASE_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = BASE_DIR / "dashboard"
RESULTS_PATH = BASE_DIR / "results" / "latest_run.json"
LKA_RESULTS_PATH = BASE_DIR / "results" / "latest_lka_run.json"
ACC_RESULTS_PATH = BASE_DIR / "results" / "latest_acc_run.json"
HISTORY_DIR = BASE_DIR / "results"

app = FastAPI(title="AutoTest Orchestrator API")

# The latest results are kept in memory so GET /api/summary doesn't have to
# regenerate scenarios - only POST /api/run starts a new test run.
# Kept separate per use case, so running one doesn't wipe out another's results.
_last_run: Optional[dict] = None
_last_lka_run: Optional[dict] = None
_last_acc_run: Optional[dict] = None


class RunRequest(BaseModel):
    count: int = Field(default=1000, ge=1, le=MAX_SCENARIO_COUNT)
    seed: int = Field(default=42)


class CriticalSearchRequest(BaseModel):
    restarts: int = Field(default=40, ge=1, le=500)
    iterations: int = Field(default=150, ge=1, le=2000)
    seed: int = Field(default=123)


def _build_run_payload(count: int, seed: int) -> dict:
    scenarios = generate_edge_case_scenarios() + generate_random_scenarios(count, seed=seed)
    engine = TestEngine()
    results = engine.run_batch(scenarios)

    summary = summarize(results)
    patterns = failure_pattern_summary(results)
    groups = group_failures(results)

    # Save the full JSON to disk (same as main.py).
    save_results(results, RESULTS_PATH)

    # Append to the history (see test_engine/results.py) - used for the
    # "Trend over time" panel in the dashboard. This is separate from
    # RESULTS_PATH above: RESULTS_PATH holds only the LATEST run, the
    # history REMEMBERS all of them.
    append_history_entry(HISTORY_DIR, "aeb", count, seed, summary, patterns)

    # ALL failures are sent - the dashboard paginates them client-side (25
    # per page), so there's no need to trim them here. failures_shown and
    # failures_total stay equal in the normal case; they only differ if an
    # upper cap is ever reintroduced.
    failures_for_ui = []
    for group_items in groups.values():
        failures_for_ui.extend(r.to_dict() for r in group_items)

    return {
        "count": count,
        "seed": seed,
        "summary": summary,
        "patterns": patterns,
        "failures": failures_for_ui,
        "failures_shown": len(failures_for_ui),
        "failures_total": summary["failed"],
    }


@app.post("/api/run")
def run_tests(req: RunRequest) -> dict:
    global _last_run
    _last_run = _build_run_payload(req.count, req.seed)
    return _last_run


@app.get("/api/summary")
def get_summary() -> dict:
    if _last_run is None:
        return _empty_payload()
    return _last_run


@app.get("/api/history")
def get_history() -> dict:
    return {"entries": read_history(HISTORY_DIR, "aeb", RUN_HISTORY_DISPLAY_LIMIT)}


def _empty_payload() -> dict:
    return {
        "count": 0,
        "seed": None,
        "summary": {"total": 0, "passed": 0, "failed": 0, "pass_rate_pct": 0.0},
        "patterns": {},
        "failures": [],
        "failures_shown": 0,
        "failures_total": 0,
        "no_run_yet": True,
    }


def _build_lka_run_payload(count: int, seed: int) -> dict:
    scenarios = generate_edge_case_lka_scenarios() + generate_random_lka_scenarios(count, seed=seed)
    engine = LKATestEngine()
    results = engine.run_batch(scenarios)

    summary = summarize(results)
    patterns = lka_failure_pattern_summary(results)
    groups = lka_group_failures(results)

    save_results(results, LKA_RESULTS_PATH)

    append_history_entry(HISTORY_DIR, "lka", count, seed, summary, patterns)

    # ALL failures are sent - the dashboard paginates them client-side (25
    # per page), see the comment in _build_run_payload above.
    failures_for_ui = []
    for group_items in groups.values():
        failures_for_ui.extend(r.to_dict() for r in group_items)

    return {
        "count": count,
        "seed": seed,
        "summary": summary,
        "patterns": patterns,
        "failures": failures_for_ui,
        "failures_shown": len(failures_for_ui),
        "failures_total": summary["failed"],
    }


@app.post("/api/lka/run")
def run_lka_tests(req: RunRequest) -> dict:
    global _last_lka_run
    _last_lka_run = _build_lka_run_payload(req.count, req.seed)
    return _last_lka_run


@app.get("/api/lka/summary")
def get_lka_summary() -> dict:
    if _last_lka_run is None:
        return _empty_payload()
    return _last_lka_run


@app.get("/api/lka/history")
def get_lka_history() -> dict:
    return {"entries": read_history(HISTORY_DIR, "lka", RUN_HISTORY_DISPLAY_LIMIT)}


def _build_acc_run_payload(count: int, seed: int) -> dict:
    scenarios = generate_edge_case_acc_scenarios() + generate_random_acc_scenarios(count, seed=seed)
    engine = ACCTestEngine()
    results = engine.run_batch(scenarios)

    summary = summarize(results)
    patterns = acc_failure_pattern_summary(results)
    groups = acc_group_failures(results)

    save_results(results, ACC_RESULTS_PATH)

    append_history_entry(HISTORY_DIR, "acc", count, seed, summary, patterns)

    # ALL failures are sent - the dashboard paginates them client-side (25
    # per page), see the comment in _build_run_payload above.
    failures_for_ui = []
    for group_items in groups.values():
        failures_for_ui.extend(r.to_dict() for r in group_items)

    return {
        "count": count,
        "seed": seed,
        "summary": summary,
        "patterns": patterns,
        "failures": failures_for_ui,
        "failures_shown": len(failures_for_ui),
        "failures_total": summary["failed"],
    }


@app.post("/api/acc/run")
def run_acc_tests(req: RunRequest) -> dict:
    global _last_acc_run
    _last_acc_run = _build_acc_run_payload(req.count, req.seed)
    return _last_acc_run


@app.get("/api/acc/summary")
def get_acc_summary() -> dict:
    if _last_acc_run is None:
        return _empty_payload()
    return _last_acc_run


@app.get("/api/acc/history")
def get_acc_history() -> dict:
    return {"entries": read_history(HISTORY_DIR, "acc", RUN_HISTORY_DISPLAY_LIMIT)}


# ---------------------------------------------------------------------------
# Critical scenario search (critical_search/) - deliberately hunts for
# scenarios inside the safety-margin "gray zone" instead of relying on
# scenarios/generator.py's random sampling to stumble into it. Unlike
# /api/run and friends above, this doesn't keep in-memory "last result"
# state or write to results/ - each search is self-contained and returned
# directly, ranked by risk_score (most robust counterexample first).
# ---------------------------------------------------------------------------


def _critical_search_payload(results, req: CriticalSearchRequest) -> dict:
    items = []
    for critical_result in results:
        item = critical_result.result.to_dict()
        item["risk_score"] = critical_result.risk_score
        items.append(item)
    return {
        "restarts": req.restarts,
        "iterations": req.iterations,
        "seed": req.seed,
        "found": len(items),
        "results": items,
    }


@app.post("/api/critical-search")
def run_critical_search(req: CriticalSearchRequest) -> dict:
    results = find_aeb_critical_scenarios(req.restarts, req.iterations, req.seed)
    return _critical_search_payload(results, req)


@app.post("/api/lka/critical-search")
def run_lka_critical_search(req: CriticalSearchRequest) -> dict:
    results = find_lka_critical_scenarios(req.restarts, req.iterations, req.seed)
    return _critical_search_payload(results, req)


@app.post("/api/acc/critical-search")
def run_acc_critical_search(req: CriticalSearchRequest) -> dict:
    results = find_acc_critical_scenarios(req.restarts, req.iterations, req.seed)
    return _critical_search_payload(results, req)


# Static assets (CSS/JS are inline in index.html, but we keep /static for the future)
if (DASHBOARD_DIR).exists():
    app.mount("/static", StaticFiles(directory=str(DASHBOARD_DIR)), name="static")


@app.get("/")
def dashboard_index() -> FileResponse:
    return FileResponse(str(DASHBOARD_DIR / "index.html"))
