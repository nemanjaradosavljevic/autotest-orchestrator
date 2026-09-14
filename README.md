# AutoTest Orchestrator - V1 (software-only prototype)

[![Tests](https://github.com/nemanjaradosavljevic/autotest-orchestrator/actions/workflows/tests.yml/badge.svg)](https://github.com/nemanjaradosavljevic/autotest-orchestrator/actions/workflows/tests.yml)

A Python application that generates automotive test scenarios, runs them
through software ECU models, automatically checks PASS/FAIL, and groups
failed scenarios by recognizable patterns. It also has a web dashboard for
running test runs and reviewing results.

It currently covers three use cases, all three following the same pattern
(Scenario Engine -> Virtual ECU -> Test Engine -> Analytics -> Dashboard) -
proof that the architecture generalizes to more than one automotive
function:

- **AEB** (Automatic Emergency Braking) - the first use case, from PROJECT 01.
- **LKA** (Lane Keep Assist) - the second use case, added to verify that
  the architecture really works for more than just braking.
- **ACC** (Adaptive Cruise Control) - the third use case, maintaining a
  safe gap from the vehicle ahead.

This is phase **V1: Python -> Virtual ECU -> Test Engine -> Dashboard**
from the project plan.

## Project structure

```
autotest-orchestrator/
├── .github/workflows/    # GitHub Actions - automatically runs the tests (see "CI/CD")
│   └── tests.yml
├── config.py             # All tunable values (margins, thresholds, ranges, limits) - one place
├── virtual_ecu/          # The "system under test" - one file per use case
│   ├── aeb.py             #   AEB: speed, obstacle -> brake ON/OFF
│   ├── lka.py              #   LKA: lateral offset/speed -> intervention ON/OFF
│   └── acc.py               #   ACC: gap/speed of lead vehicle -> decelerate ON/OFF
├── scenarios/            # Scenario Engine - test scenario generation
│   ├── schemas.py          #   Scenario (AEB), LKAScenario, ACCScenario dataclasses
│   └── generator.py        #   generators for all three use cases
├── test_engine/          # The heart of the system - execution, comparison, saving results
│   ├── assertions.py       #   AEB expected/oracle (with safety margin)
│   ├── runner.py            #   AEB TestEngine
│   ├── lka_assertions.py    #   LKA expected/oracle
│   ├── lka_runner.py        #   LKA TestEngine
│   ├── acc_assertions.py    #   ACC expected/oracle
│   ├── acc_runner.py        #   ACC TestEngine
│   └── results.py           #   shared: summarize/save (works for all three use cases)
├── analytics/             # Failure Analysis - grouping failures by pattern
│   ├── failures.py          #   AEB
│   ├── lka_failures.py      #   LKA
│   └── acc_failures.py      #   ACC
├── api/                    # FastAPI - exposes the test engine over HTTP for the dashboard
│   └── main.py               #   /api/run + /api/lka/run + /api/acc/run (and their /summary counterparts)
├── dashboard/                # Web UI (a single HTML file, no build step)
│   └── index.html             #   AEB/LKA/ACC tabs, config-driven table columns
├── tests/                  # pytest tests (unit + integration), per use case
├── results/                # JSON results from each run are saved here
├── main.py                 # CLI entry point (--usecase aeb|lka|acc)
├── requirements.txt
├── Dockerfile               # One-command dashboard demo (see "Run with Docker")
├── docker-compose.yml
└── .dockerignore
```

## Installation (Windows)

Open a terminal (PowerShell or cmd) in this folder and run:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Every time you reopen a terminal to work on the project, activate the
virtual environment first: `venv\Scripts\activate` (you'll see `(venv)`
at the start of the line when it's active).

## Running (CLI)

Run the whole pipeline (generate scenarios -> test -> report):

```
python main.py
python main.py --usecase lka
python main.py --usecase acc
```

By default (`--usecase aeb`) it generates 1000 random scenarios + 4
manually defined edge cases, and saves detailed results to
`results/latest_aeb_run.json` (or `latest_lka_run.json` /
`latest_acc_run.json` for the other two use cases - each use case has its
own default path, so running one doesn't overwrite another's results).

Options:

```
python main.py --usecase lka --count 5000 --seed 123 --out results/run2.json
```

- `--usecase` - `aeb` (default), `lka`, or `acc`
- `--count` - number of randomly generated scenarios (default 1000)
- `--seed` - seed for reproducibility (same seed = same scenarios)
- `--out` - path where the results JSON is saved (default
  `results/latest_<usecase>_run.json`)

## Dashboard (web UI)

Instead of (or alongside) the terminal, you can run test runs and view
results in a browser:

```
uvicorn api.main:app --reload
```

Then open **http://127.0.0.1:8000** in your browser. The dashboard has:

- **AEB / LKA / ACC tabs** at the top - switch between use cases (each
  has its own endpoint, its own results, its own table columns),
- a field for the number of scenarios and the seed, plus a "Run tests"
  button (calls the test engine via `POST /api/run`, `POST /api/lka/run`,
  or `POST /api/acc/run`, depending on the active tab, without reloading
  the page),
- a summary (total / PASS / FAIL / pass rate),
- **"Trend over time"** - a chart of pass rate across the last 30 runs
  (a line + a table below it with the time, scenario count, seed, and
  FAIL count per run; hovering over a point shows the details). Every
  run - from the dashboard or the CLI (`main.py`) - adds one entry to
  the history, so the trend builds up no matter where the tests were run
  from,
- failure patterns as a horizontal bar chart,
- a table of failed scenarios with actual/expected values, paginated
  (25 per page) when there are many,
- a "Download CSV" button (downloads ALL failed scenarios for the active
  use case as a CSV file, not just the current table page).

If you enter an invalid number of scenarios/seed (e.g. an empty field, a
number outside the 1-50000 range, a decimal number) or the backend isn't
running, the dashboard reports it with a clear message instead of just
breaking silently.

`Ctrl+C` in the terminal stops the server. `--reload` means the server
will restart itself when you change `api/main.py` (useful while developing).

### Run history (for the trend chart)

Every test run (CLI or dashboard) writes one row to
`results/history_<usecase>.jsonl` (e.g. `history_aeb.jsonl`,
`history_lka.jsonl`, `history_acc.jsonl`) - JSON Lines format, one JSON
record per line (`{timestamp, count, seed, total, passed, failed,
pass_rate_pct, patterns}`). The file grows append-only (nothing is ever
rewritten), so it's safe even if two runs overlap. The dashboard only
reads the last `RUN_HISTORY_DISPLAY_LIMIT` entries (30 by default,
configurable in `config.py`) via `/api/history`, `/api/lka/history`, and
`/api/acc/history`, but the complete history stays on disk. If you want
to reset the trend, just delete the corresponding `history_*.jsonl` file.

## Run with Docker

The fastest way to try the dashboard - no Python, venv, or `pip install`
needed on your machine, only [Docker Desktop](https://www.docker.com/products/docker-desktop/):

```
docker compose up --build
```

Then open **http://localhost:8000**, same as running `uvicorn` directly.
`docker-compose.yml` mounts `./results` into the container, so run history
and the latest-run JSON files persist on your machine across rebuilds -
`docker compose down` and `docker compose up --build` again won't lose them.

`Ctrl+C` stops it. Rebuild after changing `requirements.txt` or any
Python/HTML file with `docker compose up --build` again (plain
`docker compose up` reuses the last built image).

Without Compose, the same image can be built and run directly:

```
docker build -t autotest-orchestrator .
docker run -p 8000:8000 -v "$(pwd)/results:/app/results" autotest-orchestrator
```

(On Windows PowerShell, replace `$(pwd)` with `${PWD}`.)

The CLI (`python main.py`) still needs a local Python environment - the
Docker image only packages the FastAPI/dashboard side.

## Tests

```
pytest
pytest -v
```

The tests cover all three use cases: ECU logic (manually calculated edge
cases, independent of `assertions.py`/`lka_assertions.py`/`acc_assertions.py`),
scenario generators, test engines, and failure analytics.

## CI/CD (GitHub Actions)

The project has `.github/workflows/tests.yml`, which automatically runs
`pytest -v` on GitHub's servers (Python 3.10/3.11/3.12) on every
`push`/pull request, and can also be run manually from the "Actions" tab
on GitHub ("Run workflow"). This doesn't depend on anything on your own
computer - CI has its own clean environment and its own internet access,
so `pip install` works there normally.

For this to start working, the project needs to be a git repository
pushed to GitHub (if that hasn't been done yet):

1. Check whether git is installed: in a terminal, in the project folder,
   run `git --version` - if it prints a version, you're all set.
2. Initialize the repo (if it isn't already) and make the first commit:
   ```
   git init
   git add .
   git commit -m "Initial commit - AutoTest Orchestrator V1"
   ```
   (`.gitignore` already exists and excludes `venv/`, `__pycache__/`,
   `.idea/`, and `results/*.json`, so they won't get committed by accident.)
3. On [github.com](https://github.com), create a new, **empty**
   repository (without the README/gitignore/license options - to avoid
   conflicts with files that already exist locally), e.g. named
   `autotest-orchestrator`.
4. Connect the local repo to GitHub and push (GitHub will show you the
   exact commands right after creating the repo, but for the account
   `nemanjaradosavljevic` and repo `autotest-orchestrator` they look like
   this):
   ```
   git remote add origin https://github.com/nemanjaradosavljevic/autotest-orchestrator.git
   git branch -M main
   git push -u origin main
   ```
   (If you name the repo differently, just swap `autotest-orchestrator`
   in the URL above and in the badge at the top of this README.)
5. Open the **Actions** tab on GitHub - you'll see the "Tests" workflow
   has already run on its own. Once it gets a green checkmark, CI is working.

From that point on, every subsequent `git push` automatically runs all
the tests on GitHub (not on your own computer) - if you accidentally
break something, you'll find out right away from a red "X" on the
commit, before you'd notice it yourself.

## How the AEB logic works

For a given scenario (speed, obstacle distance, road friction, sensor
delay), the Virtual ECU calculates the required stopping distance:

```
reaction_distance = speed * (sensor_delay / 1000)
braking_distance   = speed^2 / (2 * friction * 9.81)
stopping_distance  = reaction_distance + braking_distance

brake = ON  if obstacle_distance <= stopping_distance
brake = OFF otherwise
```

## How the LKA logic works

For a given scenario (lateral offset from the lane center, half the lane
width, lateral speed toward the edge, whether the driver is actively
steering), the Virtual ECU calculates the "time to line crossing" (TTLC)
- how many seconds until the vehicle would cross the lane edge if nothing
changes:

```
distance_to_edge = half_lane_width - abs(lateral_offset)

if distance_to_edge <= 0:            TTLC = 0 (already past the edge)
if the vehicle isn't drifting toward the edge:  TTLC = undefined (safe)
otherwise:                           TTLC = distance_to_edge / lateral_speed

intervene = ON  if the driver is NOT actively steering AND TTLC <= threshold (1.0s)
intervene = OFF otherwise
```

Same pattern as AEB (a spatial/time budget against a threshold), just
applied to a different automotive function - that's the whole point of
this use case: it shows that the Scenario Engine / Test Engine /
Analytics layer knows nothing use-case-specific, it just calls whatever
it's given.

## How the ACC logic works

For a given scenario (my speed, lead vehicle's speed, current gap,
whether the driver is pressing the throttle), the Virtual ECU calculates
the desired (safe) gap using a "constant time headway" model - the faster
you're driving, the more space you need, plus a fixed minimum that
applies even at a standstill:

```
desired_gap = MIN_GAP + my_speed * TIME_HEADWAY

decelerate = ON  if actual_gap < desired_gap
decelerate = OFF otherwise (or if the driver is actively pressing the throttle - override)
```

The third use case, same pattern as AEB/LKA (a spatial/time budget
against a threshold, with a driver override like in LKA) - further
confirmation that the architecture generalizes.

## An important note on "expected vs actual" (why there are any FAILs at all)

`virtual_ecu/aeb.py`, `virtual_ecu/lka.py`, and `virtual_ecu/acc.py`
(actual - the systems under test) work right at the edge, with no margin.
`test_engine/assertions.py`, `test_engine/lka_assertions.py`, and
`test_engine/acc_assertions.py` (expected - the spec/oracle) are
deliberately stricter: they require `SAFETY_MARGIN = 1.15` (15% more
space for AEB and ACC, a 15% longer time threshold for LKA), because
that's a realistic safety requirement (road conditions, tires, and
sensor noise are never perfectly known). When a scenario falls in that
"margin gap", actual says "I don't need to react yet", while expected
says "it should have already reacted" -> FAIL. That's why, with a larger
number of scenarios, you'll see a realistic FAIL percentage and a
populated failure analysis, instead of 100% PASS.

This is NOT an artificially inserted bug - it's a genuine, typical
finding a test engineer would look for: "the system technically works,
but doesn't have enough safety margin." The real (independent) regression
protection for the physics/logic itself comes from `tests/test_aeb.py`,
`tests/test_lka.py`, and `tests/test_acc.py`, where the expected values
are calculated by hand and don't depend on
`assertions.py`/`lka_assertions.py`/`acc_assertions.py`.

When a real STM32/CAN ECU or a CANoe/dSPACE integration is added in
V2/V3, `assertions.py`/`lka_assertions.py`/`acc_assertions.py` stay the
"expected" side of the comparison, while "actual" comes from the real
device - the separation then starts catching real differences in
firmware, rounding, and timing too, on top of the margin.

## Configuration (config.py)

Every "number someone might want to tweak" - safety margins
(`AEB_SAFETY_MARGIN`, `LKA_SAFETY_MARGIN`, `ACC_SAFETY_MARGIN`), decision
thresholds (`LKA_TTLC_THRESHOLD_S`, `ACC_MIN_GAP_M`,
`ACC_TIME_HEADWAY_S`), ranges for randomly generating scenarios
(`AEB_SCENARIO_RANGES`, `LKA_SCENARIO_RANGES`, `ACC_SCENARIO_RANGES`),
thresholds for the failure analytics, and the upper limit on the number
of scenarios per run (`MAX_SCENARIO_COUNT`) - all live in one place, in
`config.py` in the project's root folder. There's no need to search
through multiple files to, say, make AEB more conservative - it's enough
to change `AEB_SAFETY_MARGIN` in `config.py`.

The exception is `dashboard/index.html` (`<input max="50000">` and
`MAX_SCENARIO_COUNT` in the JS part) - it's a static HTML file with no
build step, so those two values need to be kept manually in sync with
`config.MAX_SCENARIO_COUNT` if it changes.

## What's next (upcoming phases from the roadmap)

1. More use cases, following the same pattern (e.g. Forward Collision
   Warning, Blind Spot Detection).
2. CAN communication and an STM32 as the physical ECU (V2) - waiting on
   practical embedded knowledge/hardware.
3. Integration with CANoe/dSPACE/ECU-TEST (V3).

Working principle from the project plan: **learn -> build -> test -> show
the user -> validate -> expand.**
