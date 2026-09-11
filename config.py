"""
Centralna konfiguracija - AutoTest Orchestrator.

Sve "podesive" vrednosti (bezbednosne margine, pragovi za odluke, opsezi
za generisanje nasumicnih scenarija, gornje granice) su ovde na jednom
mestu, umesto razbacane po vise fajlova (virtual_ecu/, test_engine/,
scenarios/, analytics/, api/). Menjanje vrednosti ovde automatski utice
na ceo sistem (CLI, dashboard, testove) - nema dupliranih kopija koje bi
mogle da se raziradju.

Primer: ako zelis da AEB bude konzervativniji, promeni AEB_SAFETY_MARGIN
ovde - test_engine/assertions.py, main.py, api/main.py i testovi ce svi
automatski koristiti novu vrednost.
"""

# ---------------------------------------------------------------------------
# Opste
# ---------------------------------------------------------------------------

GRAVITY_M_S2 = 9.81

# Gornja granica za broj scenarija po jednom test run-u (CLI --count i
# dashboard-ovo polje "Broj scenarija"). Sprecava slucajno pokretanje
# run-a koji bi potrosio previse memorije/vremena. Dashboard-ov
# <input max="..."> u dashboard/index.html treba rucno drzati u skladu
# sa ovom vrednoscu (HTML je staticki fajl bez build koraka).
MAX_SCENARIO_COUNT = 50000


# ---------------------------------------------------------------------------
# AEB (Automatic Emergency Braking)
# ---------------------------------------------------------------------------

# Koliko vise prostora "expected" strana (test_engine/assertions.py)
# zahteva u odnosu na golu fizicku kocionu udaljenost koju virtual_ecu/aeb.py
# stvarno koristi. Vidi detaljno objasnjenje u test_engine/assertions.py.
AEB_SAFETY_MARGIN = 1.15

# Opsezi iz kojih scenarios/generator.py nasumicno bira AEB scenarije.
AEB_SCENARIO_RANGES = {
    "speed_kmh": (30, 130),
    "obstacle_distance_m": (5, 100),
    "road_friction": (0.4, 1.0),
    "sensor_delay_ms": (0, 500),
}

# Kisa efektivno smanjuje trenje izmedju guma i puta.
AEB_WEATHER_FRICTION_ADJUSTMENT = {
    "dry": 1.0,
    "rain": 0.7,
}

# Pragovi koje analytics/failures.py koristi da prepozna failure obrasce.
AEB_HIGH_SPEED_THRESHOLD_KMH = 100
AEB_LOW_DISTANCE_THRESHOLD_M = 15
AEB_HIGH_SENSOR_DELAY_THRESHOLD_MS = 300


# ---------------------------------------------------------------------------
# LKA (Lane Keep Assist)
# ---------------------------------------------------------------------------

# Prag: ako je vreme do prelaska linije <= ovoliko sekundi, sistem
# (virtual_ecu/lka.py) intervenise.
LKA_TTLC_THRESHOLD_S = 1.0

# Isti princip kao AEB_SAFETY_MARGIN, samo primenjen na vremenski prag
# umesto na prostorni - vidi test_engine/lka_assertions.py.
LKA_SAFETY_MARGIN = 1.15

# Opsezi iz kojih scenarios/generator.py nasumicno bira LKA scenarije.
LKA_SCENARIO_RANGES = {
    "speed_kmh": (30, 130),
    "lane_half_width_m": (1.5, 2.0),
    "lateral_velocity_m_s": (0.0, 2.0),
}

# Pragovi koje analytics/lka_failures.py koristi da prepozna failure obrasce.
LKA_HIGH_SPEED_THRESHOLD_KMH = 100
LKA_FAST_DRIFT_THRESHOLD_M_S = 1.5


# ---------------------------------------------------------------------------
# ACC (Adaptive Cruise Control)
# ---------------------------------------------------------------------------

# "Constant time headway" model (koristi se i u pravim ACC sistemima):
# zeljeni razmak od vozila ispred raste linearno sa brzinom (vremenski
# razmak, ACC_TIME_HEADWAY_S), plus fiksni minimum koji vazi i pri
# stajanju/malim brzinama (ACC_MIN_GAP_M).
ACC_MIN_GAP_M = 5.0
ACC_TIME_HEADWAY_S = 1.5

# Isti princip kao AEB_SAFETY_MARGIN/LKA_SAFETY_MARGIN - "expected" strana
# (test_engine/acc_assertions.py) zahteva veci razmak (rezervu) nego sto
# virtual_ecu/acc.py stvarno koristi.
ACC_SAFETY_MARGIN = 1.15

# Opsezi iz kojih scenarios/generator.py nasumicno bira ACC scenarije.
ACC_SCENARIO_RANGES = {
    "ego_speed_kmh": (0, 130),
    "lead_speed_kmh": (0, 130),
    "gap_distance_m": (2, 150),
}

# Pragovi koje analytics/acc_failures.py koristi da prepozna failure obrasce.
# ACC_FAST_CLOSING_THRESHOLD_M_S je na relativnoj brzini (moja brzina minus
# brzina vozila ispred) - koliko brzo se "topi" razmak.
ACC_HIGH_SPEED_THRESHOLD_KMH = 100
ACC_FAST_CLOSING_THRESHOLD_M_S = 5.0
