"""
Assertions - referentni ("oracle") proracun ocekivanog ponasanja, koriscen
da se proveri da li Virtual ECU (virtual_ecu/aeb.py) radi ispravno.

Namerno je odvojen u svoj fajl (kao u projektnom planu: test_engine/{runner,
assertions, results}.py), da bi test infrastruktura ostala razdvojena od
implementacije koju testira.

BEZBEDNOSNA MARGINA: ovaj modul namerno NIJE identican virtual_ecu/aeb.py.
Realan safety-critical zahtev (i u pravom automotive svetu) je da sistem
koci PRE nego sto fizicki dodje do granice - sa rezervom, jer stvarni uslovi
(neravnina puta, gume, senzor sum) nikad nisu savrseno poznati. Zato
"expected" ovde zahteva SAFETY_MARGIN (15%) vise prostora nego sto AEB
implementacija (aeb.py) trenutno koristi. Kada je stvarna udaljenost do
prepreke izmedju "gole" fizicke granice i granice sa marginom, ECU (actual)
kaze OFF, a specifikacija (expected) kaze da je trebalo ON -> FAIL. To su
realni, korisni failure-i za failure analizu (analytics/failures.py), a ne
vestacki ubaceni bug.

Kada se u V2/V3 doda pravi STM32/CAN ECU ili integracija sa CANoe/dSPACE,
ovaj isti kod ostaje "expected" strana poredjenja, a "actual" dolazi sa
stvarnog uredjaja - razdvajanje tada pocinje da hvata i prave razlike u
firmveru, zaokruzivanjima i kasnjenjima.

Za potpuno nezavisnu proveru da je sama fizicka formula (bez margine)
ispravno implementirana, videti rucno izracunate granicne slucajeve u
tests/test_aeb.py - oni testiraju aeb.py direktno i ne zavise od ovog
fajla.
"""

from dataclasses import dataclass

from config import AEB_SAFETY_MARGIN as SAFETY_MARGIN
from config import GRAVITY_M_S2

# Napomena: SAFETY_MARGIN ("rezerva" za neizvesnost u realnim uslovima) i
# GRAVITY_M_S2 sada zive u config.py, da bi bili na istom mestu kao svi
# ostali podesivi pragovi u sistemu.


@dataclass(frozen=True)
class ExpectedResult:
    brake: bool
    stopping_distance_m: float
    required_distance_with_margin_m: float


def compute_expected(
    vehicle_speed_kmh: float,
    obstacle_distance_m: float,
    road_friction: float,
    sensor_delay_ms: float,
) -> ExpectedResult:
    speed_m_s = vehicle_speed_kmh / 3.6
    reaction_distance = speed_m_s * (sensor_delay_ms / 1000.0)
    braking_distance = (speed_m_s ** 2) / (2 * road_friction * GRAVITY_M_S2)
    stopping_distance = reaction_distance + braking_distance
    required_distance_with_margin = stopping_distance * SAFETY_MARGIN
    brake = obstacle_distance_m <= required_distance_with_margin
    return ExpectedResult(
        brake=brake,
        stopping_distance_m=round(stopping_distance, 2),
        required_distance_with_margin_m=round(required_distance_with_margin, 2),
    )
