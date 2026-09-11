"""
Results - sumiranje i cuvanje rezultata testiranja.
"""

import json
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
