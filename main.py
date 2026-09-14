"""
Main entry point for the V1 prototype: generates scenarios, runs them
through the Virtual ECU, prints a PASS/FAIL report and failure analytics.

Usage:
    python main.py
    python main.py --usecase lka --count 5000 --seed 42
    python main.py --usecase acc --count 5000 --seed 42
"""

import argparse

from analytics.acc_failures import failure_pattern_summary as acc_failure_pattern_summary
from analytics.failures import failure_pattern_summary as aeb_failure_pattern_summary
from analytics.lka_failures import failure_pattern_summary as lka_failure_pattern_summary
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
from test_engine.results import append_history_entry, save_results, summarize
from test_engine.runner import TestEngine

# Run history (for "Trend over time" in the dashboard) always goes here,
# regardless of --out - so CLI and dashboard runs build the same trend together.
HISTORY_DIR = "results"


def run_aeb(count: int, seed: int, out: str) -> None:
    scenarios = generate_edge_case_scenarios() + generate_random_scenarios(count, seed=seed)
    results = TestEngine().run_batch(scenarios)
    summary = summarize(results)
    patterns = aeb_failure_pattern_summary(results)
    save_results(results, out)
    append_history_entry(HISTORY_DIR, "aeb", count, seed, summary, patterns)
    print_report("AEB (Automatic Emergency Braking)", summary, patterns, out)


def run_lka(count: int, seed: int, out: str) -> None:
    scenarios = generate_edge_case_lka_scenarios() + generate_random_lka_scenarios(count, seed=seed)
    results = LKATestEngine().run_batch(scenarios)
    summary = summarize(results)
    patterns = lka_failure_pattern_summary(results)
    save_results(results, out)
    append_history_entry(HISTORY_DIR, "lka", count, seed, summary, patterns)
    print_report("LKA (Lane Keep Assist)", summary, patterns, out)


def run_acc(count: int, seed: int, out: str) -> None:
    scenarios = generate_edge_case_acc_scenarios() + generate_random_acc_scenarios(count, seed=seed)
    results = ACCTestEngine().run_batch(scenarios)
    summary = summarize(results)
    patterns = acc_failure_pattern_summary(results)
    save_results(results, out)
    append_history_entry(HISTORY_DIR, "acc", count, seed, summary, patterns)
    print_report("ACC (Adaptive Cruise Control)", summary, patterns, out)


def print_report(title: str, summary: dict, patterns: dict, out: str) -> None:
    print("=" * 50)
    print(f"AUTOTEST ORCHESTRATOR - {title}")
    print("=" * 50)
    print(f"Total scenarios: {summary['total']}")
    print(f"PASS: {summary['passed']}")
    print(f"FAIL: {summary['failed']}")
    print(f"Pass rate: {summary['pass_rate_pct']}%")
    print()
    if patterns:
        print("Failure patterns:")
        for pattern, count in sorted(patterns.items(), key=lambda x: -x[1]):
            print(f"  - {pattern}: {count}")
    else:
        print("No failures.")
    print()
    print(f"Detailed results saved to: {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="AutoTest Orchestrator - V1 prototype")
    parser.add_argument(
        "--usecase",
        choices=["aeb", "lka", "acc"],
        default="aeb",
        help="Which use case to run (default: aeb)",
    )
    parser.add_argument("--count", type=int, default=1000, help="Number of randomly generated scenarios")
    parser.add_argument("--seed", type=int, default=42, help="Seed for reproducibility")
    # The default path depends on the use case (results/latest_<usecase>_run.json), so
    # running one use case without --out doesn't overwrite another's results. If --out
    # is given explicitly, that exact path is used, regardless of usecase.
    parser.add_argument(
        "--out", type=str, default=None, help="Path to save results to (default: results/latest_<usecase>_run.json)"
    )
    args = parser.parse_args()

    if not (1 <= args.count <= MAX_SCENARIO_COUNT):
        parser.error(f"--count must be between 1 and {MAX_SCENARIO_COUNT} (got: {args.count})")

    out = args.out or f"results/latest_{args.usecase}_run.json"

    if args.usecase == "aeb":
        run_aeb(args.count, args.seed, out)
    elif args.usecase == "lka":
        run_lka(args.count, args.seed, out)
    else:
        run_acc(args.count, args.seed, out)


if __name__ == "__main__":
    main()
