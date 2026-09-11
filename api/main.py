"""
Dashboard API - FastAPI aplikacija koja izlaze test-engine kroz HTTP, da bi
dashboard/index.html mogao da pokrece test run-ove i prikazuje rezultate u
browseru (Faza 5 iz projektnog roadmap-a).

Pokretanje (iz root foldera projekta, sa aktiviranim venv-om):
    uvicorn api.main:app --reload

Zatim otvori http://127.0.0.1:8000 u browseru.
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
from config import MAX_SCENARIO_COUNT
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
from test_engine.results import save_results, summarize
from test_engine.runner import TestEngine

BASE_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = BASE_DIR / "dashboard"
RESULTS_PATH = BASE_DIR / "results" / "latest_run.json"
LKA_RESULTS_PATH = BASE_DIR / "results" / "latest_lka_run.json"
ACC_RESULTS_PATH = BASE_DIR / "results" / "latest_acc_run.json"

app = FastAPI(title="AutoTest Orchestrator API")

# Poslednji rezultati drze se u memoriji da GET /api/summary ne mora da
# ponovo generise scenarije - samo POST /api/run pokrece novi test run.
# Odvojeno po use case-u, da run jednog ne obrise rezultate drugog.
_last_run: Optional[dict] = None
_last_lka_run: Optional[dict] = None
_last_acc_run: Optional[dict] = None


class RunRequest(BaseModel):
    count: int = Field(default=1000, ge=1, le=MAX_SCENARIO_COUNT)
    seed: int = Field(default=42)


def _build_run_payload(count: int, seed: int) -> dict:
    scenarios = generate_edge_case_scenarios() + generate_random_scenarios(count, seed=seed)
    engine = TestEngine()
    results = engine.run_batch(scenarios)

    summary = summarize(results)
    patterns = failure_pattern_summary(results)
    groups = group_failures(results)

    # Sacuvaj pun JSON na disk (kao i main.py).
    save_results(results, RESULTS_PATH)

    # Salju se SVI failure-i - dashboard ih paginira na klijentu (25 po
    # strani), pa nema potrebe da ih sec ovde. failures_shown/failures_total
    # ostaju jednaki u normalnom slucaju; razlikuju se samo ako se ikad
    # ponovo uvede neki gornji limit.
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

    # Salju se SVI failure-i - dashboard ih paginira na klijentu (25 po
    # strani), vidi komentar u _build_run_payload iznad.
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


def _build_acc_run_payload(count: int, seed: int) -> dict:
    scenarios = generate_edge_case_acc_scenarios() + generate_random_acc_scenarios(count, seed=seed)
    engine = ACCTestEngine()
    results = engine.run_batch(scenarios)

    summary = summarize(results)
    patterns = acc_failure_pattern_summary(results)
    groups = acc_group_failures(results)

    save_results(results, ACC_RESULTS_PATH)

    # Salju se SVI failure-i - dashboard ih paginira na klijentu (25 po
    # strani), vidi komentar u _build_run_payload iznad.
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


# Statika (CSS/JS su inline u index.html, ali ostavljamo /static za buducnost)
if (DASHBOARD_DIR).exists():
    app.mount("/static", StaticFiles(directory=str(DASHBOARD_DIR)), name="static")


@app.get("/")
def dashboard_index() -> FileResponse:
    return FileResponse(str(DASHBOARD_DIR / "index.html"))
