"""
Central configuration - AutoTest Orchestrator.

All "tunable" values (safety margins, decision thresholds, ranges for
generating random scenarios, upper limits) are kept here in one place,
instead of scattered across multiple files (virtual_ecu/, test_engine/,
scenarios/, analytics/, api/). Changing a value here automatically affects
the whole system (CLI, dashboard, tests) - there are no duplicate copies
that could drift out of sync.

Example: if you want AEB to be more conservative, change AEB_SAFETY_MARGIN
here - test_engine/assertions.py, main.py, api/main.py and the tests will
all automatically use the new value.
"""

# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------

GRAVITY_M_S2 = 9.81

# Upper limit on the number of scenarios per test run (CLI --count and
# the dashboard's "Number of scenarios" field). Prevents accidentally
# starting a run that would consume too much memory/time. The dashboard's
# <input max="..."> in dashboard/index.html needs to be kept in sync with
# this value by hand (the HTML is a static file with no build step).
MAX_SCENARIO_COUNT = 50000

# How many of the most recent runs the dashboard shows in the "Trend over
# time" panel (chart + history table). The history on disk
# (results/history_<usecase>.jsonl) stays complete - this only limits how
# much is sent/rendered per request.
RUN_HISTORY_DISPLAY_LIMIT = 30


# ---------------------------------------------------------------------------
# AEB (Automatic Emergency Braking)
# ---------------------------------------------------------------------------

# How much extra room the "expected" side (test_engine/assertions.py)
# requires compared to the raw physical braking distance that
# virtual_ecu/aeb.py actually uses. See the detailed explanation in
# test_engine/assertions.py.
AEB_SAFETY_MARGIN = 1.15

# Ranges from which scenarios/generator.py randomly picks AEB scenarios.
AEB_SCENARIO_RANGES = {
    "speed_kmh": (30, 130),
    "obstacle_distance_m": (5, 100),
    "road_friction": (0.4, 1.0),
    "sensor_delay_ms": (0, 500),
}

# Rain effectively reduces the friction between tires and the road.
AEB_WEATHER_FRICTION_ADJUSTMENT = {
    "dry": 1.0,
    "rain": 0.7,
}

# Thresholds that analytics/failures.py uses to recognize failure patterns.
AEB_HIGH_SPEED_THRESHOLD_KMH = 100
AEB_LOW_DISTANCE_THRESHOLD_M = 15
AEB_HIGH_SENSOR_DELAY_THRESHOLD_MS = 300


# ---------------------------------------------------------------------------
# LKA (Lane Keep Assist)
# ---------------------------------------------------------------------------

# Threshold: if the time to lane crossing is <= this many seconds, the
# system (virtual_ecu/lka.py) intervenes.
LKA_TTLC_THRESHOLD_S = 1.0

# Same principle as AEB_SAFETY_MARGIN, just applied to a time threshold
# instead of a distance one - see test_engine/lka_assertions.py.
LKA_SAFETY_MARGIN = 1.15

# Ranges from which scenarios/generator.py randomly picks LKA scenarios.
LKA_SCENARIO_RANGES = {
    "speed_kmh": (30, 130),
    "lane_half_width_m": (1.5, 2.0),
    "lateral_velocity_m_s": (0.0, 2.0),
}

# Thresholds that analytics/lka_failures.py uses to recognize failure patterns.
LKA_HIGH_SPEED_THRESHOLD_KMH = 100
LKA_FAST_DRIFT_THRESHOLD_M_S = 1.5


# ---------------------------------------------------------------------------
# ACC (Adaptive Cruise Control)
# ---------------------------------------------------------------------------

# "Constant time headway" model (also used in real ACC systems): the
# desired gap to the vehicle ahead grows linearly with speed (time
# headway, ACC_TIME_HEADWAY_S), plus a fixed minimum that also applies
# when standing still/at low speeds (ACC_MIN_GAP_M).
ACC_MIN_GAP_M = 5.0
ACC_TIME_HEADWAY_S = 1.5

# Same principle as AEB_SAFETY_MARGIN/LKA_SAFETY_MARGIN - the "expected"
# side (test_engine/acc_assertions.py) requires a larger gap (a reserve)
# than virtual_ecu/acc.py actually uses.
ACC_SAFETY_MARGIN = 1.15

# Ranges from which scenarios/generator.py randomly picks ACC scenarios.
ACC_SCENARIO_RANGES = {
    "ego_speed_kmh": (0, 130),
    "lead_speed_kmh": (0, 130),
    "gap_distance_m": (2, 150),
}

# Thresholds that analytics/acc_failures.py uses to recognize failure patterns.
# ACC_FAST_CLOSING_THRESHOLD_M_S is on the relative speed (my speed minus
# the speed of the vehicle ahead) - how fast the gap is "closing".
ACC_HIGH_SPEED_THRESHOLD_KMH = 100
ACC_FAST_CLOSING_THRESHOLD_M_S = 5.0
