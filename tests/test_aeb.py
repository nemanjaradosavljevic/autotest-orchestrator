"""
Unit tests for the Virtual ECU (AEB logic), with manually calculated expected
values - independent of test_engine/assertions.py. This is real
regression protection: if someone accidentally breaks the formula in aeb.py,
these tests will fail.
"""

import pytest

from virtual_ecu.aeb import AEBVirtualECU


def test_brake_on_example_from_project_plan():
    """Example from the project document: 80 km/h, 20m, friction 0.6, delay 100ms -> BRAKE ON."""
    ecu = AEBVirtualECU()
    result = ecu.process(
        vehicle_speed_kmh=80,
        obstacle_distance_m=20,
        road_friction=0.6,
        sensor_delay_ms=100,
    )
    assert result.brake is True


def test_brake_off_when_enough_room_to_stop():
    ecu = AEBVirtualECU()
    result = ecu.process(
        vehicle_speed_kmh=130,
        obstacle_distance_m=100,
        road_friction=1.0,
        sensor_delay_ms=0,
    )
    assert result.brake is False


def test_brake_on_very_close_obstacle():
    ecu = AEBVirtualECU()
    result = ecu.process(
        vehicle_speed_kmh=30,
        obstacle_distance_m=2,
        road_friction=1.0,
        sensor_delay_ms=0,
    )
    assert result.brake is True


def test_brake_on_worst_case_rain_high_speed_slow_sensor():
    ecu = AEBVirtualECU()
    result = ecu.process(
        vehicle_speed_kmh=130,
        obstacle_distance_m=30,
        road_friction=0.4,
        sensor_delay_ms=500,
    )
    assert result.brake is True


def test_zero_speed_never_needs_to_brake():
    ecu = AEBVirtualECU()
    result = ecu.process(
        vehicle_speed_kmh=0,
        obstacle_distance_m=1,
        road_friction=1.0,
        sensor_delay_ms=0,
    )
    assert result.brake is False
    assert result.stopping_distance_m == 0


def test_higher_speed_needs_more_stopping_distance():
    ecu = AEBVirtualECU()
    slow = ecu.process(vehicle_speed_kmh=50, obstacle_distance_m=50, road_friction=0.8, sensor_delay_ms=0)
    fast = ecu.process(vehicle_speed_kmh=100, obstacle_distance_m=50, road_friction=0.8, sensor_delay_ms=0)
    assert fast.stopping_distance_m > slow.stopping_distance_m


def test_lower_friction_needs_more_stopping_distance():
    ecu = AEBVirtualECU()
    dry = ecu.process(vehicle_speed_kmh=80, obstacle_distance_m=50, road_friction=1.0, sensor_delay_ms=0)
    wet = ecu.process(vehicle_speed_kmh=80, obstacle_distance_m=50, road_friction=0.4, sensor_delay_ms=0)
    assert wet.stopping_distance_m > dry.stopping_distance_m


def test_invalid_negative_speed_raises():
    ecu = AEBVirtualECU()
    with pytest.raises(ValueError):
        ecu.process(vehicle_speed_kmh=-10, obstacle_distance_m=10, road_friction=1.0, sensor_delay_ms=0)


def test_invalid_zero_friction_raises():
    ecu = AEBVirtualECU()
    with pytest.raises(ValueError):
        ecu.process(vehicle_speed_kmh=50, obstacle_distance_m=10, road_friction=0, sensor_delay_ms=0)


def test_invalid_negative_sensor_delay_raises():
    ecu = AEBVirtualECU()
    with pytest.raises(ValueError):
        ecu.process(vehicle_speed_kmh=50, obstacle_distance_m=10, road_friction=1.0, sensor_delay_ms=-5)
