"""
Property-based tests (using hypothesis) for the AEB/LKA/ACC virtual ECU
logic.

The rest of the test suite (tests/test_aeb.py, tests/test_lka.py,
tests/test_acc.py, ...) is example-based: each test picks a handful of
specific inputs and checks a hand-calculated expected output. That's
great for pinning down known cases, but it can only ever check the exact
inputs someone thought to write down.

Property-based tests work the other way around: instead of a fixed input,
hypothesis generates hundreds of random inputs per test (including
boundary values like 0, and values close to other arguments) and checks
that a *property* - something that should hold for every valid input, not
just a specific one - is never violated. When a property fails, hypothesis
automatically "shrinks" the failing example down to the smallest input
that still breaks it, which is usually far more useful for debugging than
whatever huge random value it started with.

The properties below fall into three families, mirrored across all three
use cases:
  1. Sanity bounds - a physical quantity the ECU computes (a distance, a
     time-to-crossing, a gap) should never come out negative.
  2. Monotonicity - increasing vehicle speed (holding everything else
     fixed) should never *decrease* the distance/gap the system needs.
  3. The safety-margin relationship - the "expected" oracle
     (test_engine/assertions.py and friends) is deliberately more
     conservative than the actual ECU (SAFETY_MARGIN > 1, see config.py),
     so whenever the actual ECU decides to intervene, the oracle must
     agree it should have. The dangerous direction (oracle says intervene,
     actual ECU stays silent) is exactly what analytics/failures.py is
     built to catch - it's a real, useful FAIL, not a bug in these tests.
"""

from hypothesis import given
from hypothesis import strategies as st

import pytest

from virtual_ecu.aeb import AEBVirtualECU
from virtual_ecu.lka import LKAVirtualECU
from virtual_ecu.acc import ACCVirtualECU
from test_engine.assertions import compute_expected
from test_engine.lka_assertions import compute_lka_expected
from test_engine.acc_assertions import compute_acc_expected

# ---------------------------------------------------------------------------
# AEB
# ---------------------------------------------------------------------------

aeb_speeds = st.floats(min_value=0, max_value=300, allow_nan=False, allow_infinity=False)
aeb_distances = st.floats(min_value=0, max_value=300, allow_nan=False, allow_infinity=False)
aeb_frictions = st.floats(min_value=0.01, max_value=1.5, allow_nan=False, allow_infinity=False)
aeb_delays = st.floats(min_value=0, max_value=2000, allow_nan=False, allow_infinity=False)


@given(speed=aeb_speeds, dist=aeb_distances, friction=aeb_frictions, delay=aeb_delays)
def test_aeb_stopping_distance_never_negative(speed, dist, friction, delay):
    ecu = AEBVirtualECU()
    result = ecu.process(speed, dist, friction, delay)
    assert result.stopping_distance_m >= 0
    assert result.reaction_distance_m >= 0
    assert result.braking_distance_m >= 0


@given(
    speed=aeb_speeds,
    speed_increase=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
    dist=aeb_distances,
    friction=aeb_frictions,
    delay=aeb_delays,
)
def test_aeb_higher_speed_never_needs_less_stopping_distance(speed, speed_increase, dist, friction, delay):
    """Braking (v^2 term) and reaction distance (v term) are both
    non-decreasing in speed, so the total stopping distance can never go
    down when speed goes up, all else held equal."""
    ecu = AEBVirtualECU()
    slower = ecu.process(speed, dist, friction, delay)
    faster = ecu.process(speed + speed_increase, dist, friction, delay)
    assert faster.stopping_distance_m >= slower.stopping_distance_m


@given(speed=aeb_speeds, dist=aeb_distances, friction=aeb_frictions, delay=aeb_delays)
def test_aeb_expected_margin_covers_actual_stopping_distance(speed, dist, friction, delay):
    """The oracle's required_distance_with_margin_m is stopping_distance_m
    scaled up by AEB_SAFETY_MARGIN (> 1), so it must never fall short of
    the actual ECU's own stopping_distance_m."""
    ecu = AEBVirtualECU()
    actual = ecu.process(speed, dist, friction, delay)
    expected = compute_expected(speed, dist, friction, delay)
    assert expected.required_distance_with_margin_m >= actual.stopping_distance_m


@given(speed=aeb_speeds, dist=aeb_distances, friction=aeb_frictions, delay=aeb_delays)
def test_aeb_actual_brake_implies_expected_brake(speed, dist, friction, delay):
    """The oracle brakes at a larger (safer) distance than the actual ECU,
    so actual=ON must always imply expected=ON. actual=ON with
    expected=OFF would mean the ECU is braking when even the lenient
    physical formula says it doesn't need to - a real bug."""
    ecu = AEBVirtualECU()
    actual = ecu.process(speed, dist, friction, delay)
    expected = compute_expected(speed, dist, friction, delay)
    if actual.brake:
        assert expected.brake


@given(
    speed=st.floats(min_value=-1000, max_value=-0.001, allow_nan=False, allow_infinity=False),
    dist=aeb_distances,
    friction=aeb_frictions,
    delay=aeb_delays,
)
def test_aeb_negative_speed_always_rejected(speed, dist, friction, delay):
    ecu = AEBVirtualECU()
    with pytest.raises(ValueError):
        ecu.process(speed, dist, friction, delay)


# ---------------------------------------------------------------------------
# LKA
# ---------------------------------------------------------------------------

lka_speeds = st.floats(min_value=0, max_value=300, allow_nan=False, allow_infinity=False)
lka_offsets = st.floats(min_value=-5, max_value=5, allow_nan=False, allow_infinity=False)
lka_half_widths = st.floats(min_value=0.01, max_value=5, allow_nan=False, allow_infinity=False)
lka_lateral_velocities = st.floats(min_value=-5, max_value=5, allow_nan=False, allow_infinity=False)
lka_steering = st.booleans()


@given(
    speed=lka_speeds,
    offset=lka_offsets,
    half_width=lka_half_widths,
    lat_vel=lka_lateral_velocities,
    steering=lka_steering,
)
def test_lka_time_to_crossing_never_negative(speed, offset, half_width, lat_vel, steering):
    ecu = LKAVirtualECU()
    result = ecu.process(speed, offset, half_width, lat_vel, steering)
    if result.time_to_crossing_s is not None:
        assert result.time_to_crossing_s >= 0


@given(
    speed=lka_speeds,
    offset=lka_offsets,
    half_width=lka_half_widths,
    lat_vel=lka_lateral_velocities,
    steering=lka_steering,
)
def test_lka_actual_intervene_implies_expected_intervene(speed, offset, half_width, lat_vel, steering):
    """LKA_SAFETY_MARGIN widens the oracle's TTLC threshold, so it
    intervenes at least as early as the actual ECU - actual=ON must always
    imply expected=ON."""
    ecu = LKAVirtualECU()
    actual = ecu.process(speed, offset, half_width, lat_vel, steering)
    expected = compute_lka_expected(speed, offset, half_width, lat_vel, steering)
    if actual.intervene:
        assert expected.intervene


# ---------------------------------------------------------------------------
# ACC
# ---------------------------------------------------------------------------

acc_speeds = st.floats(min_value=0, max_value=300, allow_nan=False, allow_infinity=False)
acc_gaps = st.floats(min_value=0, max_value=300, allow_nan=False, allow_infinity=False)
acc_override = st.booleans()


@given(ego=acc_speeds, lead=acc_speeds, gap=acc_gaps, override=acc_override)
def test_acc_desired_gap_never_negative(ego, lead, gap, override):
    ecu = ACCVirtualECU()
    result = ecu.process(ego, lead, gap, override)
    assert result.desired_gap_m >= 0


@given(
    ego=acc_speeds,
    ego_increase=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
    lead=acc_speeds,
    gap=acc_gaps,
    override=acc_override,
)
def test_acc_higher_ego_speed_never_needs_less_gap(ego, ego_increase, lead, gap, override):
    """desired_gap_m grows linearly with ego speed (constant time
    headway), so it can never shrink when ego speed goes up, all else
    held equal."""
    ecu = ACCVirtualECU()
    slower = ecu.process(ego, lead, gap, override)
    faster = ecu.process(ego + ego_increase, lead, gap, override)
    assert faster.desired_gap_m >= slower.desired_gap_m


@given(ego=acc_speeds, lead=acc_speeds, gap=acc_gaps, override=acc_override)
def test_acc_expected_margin_covers_actual_gap(ego, lead, gap, override):
    """The oracle's desired_gap_with_margin_m is desired_gap_m scaled up
    by ACC_SAFETY_MARGIN (> 1), so it must never fall short of the actual
    ECU's own desired_gap_m."""
    ecu = ACCVirtualECU()
    actual = ecu.process(ego, lead, gap, override)
    expected = compute_acc_expected(ego, lead, gap, override)
    assert expected.desired_gap_with_margin_m >= actual.desired_gap_m


@given(ego=acc_speeds, lead=acc_speeds, gap=acc_gaps, override=acc_override)
def test_acc_actual_decelerate_implies_expected_decelerate(ego, lead, gap, override):
    """The oracle decelerates at a larger (safer) gap than the actual
    ECU, so actual=ON must always imply expected=ON."""
    ecu = ACCVirtualECU()
    actual = ecu.process(ego, lead, gap, override)
    expected = compute_acc_expected(ego, lead, gap, override)
    if actual.decelerate:
        assert expected.decelerate
