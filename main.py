"""
Glavna ulazna tacka za V1 prototip: generise scenarije, pokrece ih kroz
Virtual ECU, prikazuje PASS/FAIL izvestaj i failure analitiku.

Pokretanje:
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
from test_engine.results import save_results, summarize
from test_engine.runner import TestEngine


def run_aeb(count: int, seed: int, out: str) -> None:
    scenarios = generate_edge_case_scenarios() + generate_random_scenarios(count, seed=seed)
    results = TestEngine().run_batch(scenarios)
    summary = summarize(results)
    patterns = aeb_failure_pattern_summary(results)
    save_results(results, out)
    print_report("AEB (Automatic Emergency Braking)", summary, patterns, out)


def run_lka(count: int, seed: int, out: str) -> None:
    scenarios = generate_edge_case_lka_scenarios() + generate_random_lka_scenarios(count, seed=seed)
    results = LKATestEngine().run_batch(scenarios)
    summary = summarize(results)
    patterns = lka_failure_pattern_summary(results)
    save_results(results, out)
    print_report("LKA (Lane Keep Assist)", summary, patterns, out)


def run_acc(count: int, seed: int, out: str) -> None:
    scenarios = generate_edge_case_acc_scenarios() + generate_random_acc_scenarios(count, seed=seed)
    results = ACCTestEngine().run_batch(scenarios)
    summary = summarize(results)
    patterns = acc_failure_pattern_summary(results)
    save_results(results, out)
    print_report("ACC (Adaptive Cruise Control)", summary, patterns, out)


def print_report(title: str, summary: dict, patterns: dict, out: str) -> None:
    print("=" * 50)
    print(f"AUTOTEST ORCHESTRATOR - {title}")
    print("=" * 50)
    print(f"Ukupno scenarija: {summary['total']}")
    print(f"PASS: {summary['passed']}")
    print(f"FAIL: {summary['failed']}")
    print(f"Pass rate: {summary['pass_rate_pct']}%")
    print()
    if patterns:
        print("Failure pattern-i:")
        for pattern, count in sorted(patterns.items(), key=lambda x: -x[1]):
            print(f"  - {pattern}: {count}")
    else:
        print("Nema failure-a.")
    print()
    print(f"Detaljni rezultati sacuvani u: {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="AutoTest Orchestrator - V1 prototip")
    parser.add_argument(
        "--usecase",
        choices=["aeb", "lka", "acc"],
        default="aeb",
        help="Koji use case pokrenuti (podrazumevano: aeb)",
    )
    parser.add_argument("--count", type=int, default=1000, help="Broj nasumicno generisanih scenarija")
    parser.add_argument("--seed", type=int, default=42, help="Seed za reproduktivnost")
    # Podrazumevana putanja zavisi od use case-a (results/latest_<usecase>_run.json), da run
    # jednog use case-a bez --out ne prepise rezultate drugog. Ako je --out eksplicitno dat,
    # koristi se tacno ta putanja, bez obzira na usecase.
    parser.add_argument(
        "--out", type=str, default=None, help="Putanja za cuvanje rezultata (podrazumevano: results/latest_<usecase>_run.json)"
    )
    args = parser.parse_args()

    if not (1 <= args.count <= MAX_SCENARIO_COUNT):
        parser.error(f"--count mora biti izmedju 1 i {MAX_SCENARIO_COUNT} (dobijeno: {args.count})")

    out = args.out or f"results/latest_{args.usecase}_run.json"

    if args.usecase == "aeb":
        run_aeb(args.count, args.seed, out)
    elif args.usecase == "lka":
        run_lka(args.count, args.seed, out)
    else:
        run_acc(args.count, args.seed, out)


if __name__ == "__main__":
    main()
