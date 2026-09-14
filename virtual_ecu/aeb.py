"""
Virtual ECU - Automatic Emergency Braking (AEB) logic.

This is the "system under test": a simple software model of an ECU that
makes a braking decision based on input parameters. The MVP's goal is not
a realistic physical model of a car, but a controlled system with inputs,
logic, and outputs that we can test automatically and at scale.

Later (V2/V3) this module can be replaced or complemented by a real STM32
device connected over CAN, while the Test Engine and Scenario Engine stay
the same.
"""

from dataclasses import dataclass

from config import GRAVITY_M_S2


@dataclass(frozen=True)
class ECUOutput:
    brake: bool
    stopping_distance_m: float
    reaction_distance_m: float
    braking_distance_m: float


class AEBVirtualECU:
    """Simulates the ECU logic for Automatic Emergency Braking."""

    def process(
        self,
        vehicle_speed_kmh: float,
        obstacle_distance_m: float,
        road_friction: float,
        sensor_delay_ms: float,
    ) -> ECUOutput:
        if vehicle_speed_kmh < 0:
            raise ValueError("vehicle_speed_kmh cannot be negative")
        if obstacle_distance_m < 0:
            raise ValueError("obstacle_distance_m cannot be negative")
        if not (0 < road_friction <= 1.5):
            raise ValueError("road_friction must be in range (0, 1.5]")
        if sensor_delay_ms < 0:
            raise ValueError("sensor_delay_ms cannot be negative")

        speed_m_s = vehicle_speed_kmh / 3.6

        # Reaction distance - how far the vehicle travels while the sensor/ECU "notices" the obstacle
        reaction_distance_m = speed_m_s * (sensor_delay_ms / 1000.0)

        # Braking distance from motion physics: v^2 / (2 * mu * g)
        braking_distance_m = (speed_m_s ** 2) / (2 * road_friction * GRAVITY_M_S2)

        stopping_distance_m = reaction_distance_m + braking_distance_m

        # If the required stopping distance >= the actual distance to the
        # obstacle, the system must brake.
        brake = obstacle_distance_m <= stopping_distance_m

        return ECUOutput(
            brake=brake,
            stopping_distance_m=round(stopping_distance_m, 2),
            reaction_distance_m=round(reaction_distance_m, 2),
            braking_distance_m=round(braking_distance_m, 2),
        )
