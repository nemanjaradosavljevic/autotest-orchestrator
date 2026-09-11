# AutoTest Orchestrator - V1 (software-only prototip)

Python aplikacija koja generise automotive test scenarije, pusta ih kroz
softverske modele ECU-a, automatski proverava PASS/FAIL i grupise
neuspesne scenarije po prepoznatljivim obrascima. Ima i web dashboard za
pokretanje test run-ova i pregled rezultata.

Trenutno pokriva tri use case-a, sva tri po istom obrascu (Scenario Engine
-> Virtual ECU -> Test Engine -> Analytics -> Dashboard) - dokaz da
arhitektura generalizuje na vise od jedne automotive funkcije:

- **AEB** (Automatic Emergency Braking) - prvi use case, iz PROJECT 01.
- **LKA** (Lane Keep Assist) - drugi use case, dodat da se proveri da
  arhitektura zaista radi za vise od kocenja.
- **ACC** (Adaptive Cruise Control) - treci use case, odrzavanje
  bezbednog razmaka od vozila ispred.

Ovo je faza **V1: Python -> Virtual ECU -> Test Engine -> Dashboard** iz
projektnog plana.

## Struktura projekta

```
autotest-orchestrator/
├── .github/workflows/    # GitHub Actions - automatsko pokretanje testova (vidi "CI/CD")
│   └── tests.yml
├── config.py             # Sve podesive vrednosti (margine, pragovi, opsezi, limiti) - jedno mesto
├── virtual_ecu/          # "Sistem pod testom" - po jedan fajl po use case-u
│   ├── aeb.py             #   AEB: brzina, prepreka -> brake ON/OFF
│   ├── lka.py              #   LKA: lateralni ofset/brzina -> intervencija ON/OFF
│   └── acc.py               #   ACC: razmak/brzina vozila ispred -> decelerate ON/OFF
├── scenarios/            # Scenario Engine - generisanje test scenarija
│   ├── schemas.py          #   Scenario (AEB), LKAScenario, ACCScenario dataclass-ovi
│   └── generator.py        #   generatori za sva tri use case-a
├── test_engine/          # Srce sistema - izvrsavanje, poredjenje, cuvanje rezultata
│   ├── assertions.py       #   AEB expected/oracle (sa bezbednosnom marginom)
│   ├── runner.py            #   AEB TestEngine
│   ├── lka_assertions.py    #   LKA expected/oracle
│   ├── lka_runner.py        #   LKA TestEngine
│   ├── acc_assertions.py    #   ACC expected/oracle
│   ├── acc_runner.py        #   ACC TestEngine
│   └── results.py           #   zajednicko: summarize/save (radi za sva tri use case-a)
├── analytics/             # Failure Analysis - grupisanje failure-a po obrascima
│   ├── failures.py          #   AEB
│   ├── lka_failures.py      #   LKA
│   └── acc_failures.py      #   ACC
├── api/                    # FastAPI - izlaze test engine kroz HTTP za dashboard
│   └── main.py               #   /api/run + /api/lka/run + /api/acc/run (i /summary parnjaci)
├── dashboard/                # Web UI (jedan HTML fajl, bez build koraka)
│   └── index.html             #   AEB/LKA/ACC tabovi, config-driven tabela kolona
├── tests/                  # pytest testovi (unit + integracioni), po use case-u
├── results/                # Ovde se cuvaju JSON rezultati svakog pokretanja
├── main.py                 # CLI ulazna tacka (--usecase aeb|lka|acc)
└── requirements.txt
```

## Instalacija (Windows)

Otvori terminal (PowerShell ili cmd) u ovom folderu i pokreni:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Svaki put kad ponovo otvoris terminal za rad na projektu, prvo aktiviraj
virtuelno okruzenje: `venv\Scripts\activate` (videces `(venv)` na pocetku
linije kad je aktivno).

## Pokretanje (CLI)

Pokreni ceo pipeline (generisanje scenarija -> testiranje -> izvestaj):

```
python main.py
python main.py --usecase lka
python main.py --usecase acc
```

Podrazumevano (`--usecase aeb`) generise 1000 nasumicnih scenarija + 4
rucno definisana granicna slucaja, i cuva detaljne rezultate u
`results/latest_aeb_run.json` (odnosno `latest_lka_run.json` /
`latest_acc_run.json` za druga dva use case-a - svaki use case ima svoju
podrazumevanu putanju, da run jednog ne prepise rezultate drugog).

Opcije:

```
python main.py --usecase lka --count 5000 --seed 123 --out results/run2.json
```

- `--usecase` - `aeb` (podrazumevano), `lka` ili `acc`
- `--count` - broj nasumicno generisanih scenarija (podrazumevano 1000)
- `--seed` - seed za reproduktivnost (isti seed = isti scenariji)
- `--out` - putanja gde se cuva JSON sa rezultatima (podrazumevano
  `results/latest_<usecase>_run.json`)

## Dashboard (web UI)

Umesto (ili pored) terminala, mozes da pokreces test run-ove i gledas
rezultate u browseru:

```
uvicorn api.main:app --reload
```

Zatim otvori **http://127.0.0.1:8000** u browseru. Dashboard ima:

- **tabove AEB / LKA / ACC** na vrhu - prebacuju izmedju use case-ova
  (svaki ima svoj endpoint, svoje rezultate, svoje kolone u tabeli),
- polje za broj scenarija i seed + dugme "Pokreni testove" (poziva test
  engine preko `POST /api/run`, `POST /api/lka/run` ili `POST /api/acc/run`,
  u zavisnosti od aktivnog taba, bez reload-a stranice),
- rezime (ukupno / PASS / FAIL / pass rate),
- failure pattern-e kao horizontalni bar prikaz,
- tabelu neuspelih scenarija sa actual/expected vrednostima, paginiranu
  (25 po strani) kad ih ima puno,
- dugme "Preuzmi CSV" (skida SVE neuspele scenarije aktivnog use case-a
  kao CSV fajl, ne samo trenutnu stranu tabele).

Ako unesesh neispravan broj scenarija/seed (npr. prazno polje, broj van
opsega 1-50000, decimalni broj) ili backend nije pokrenut, dashboard to
prijavljuje jasnom porukom umesto da samo prestane da radi.

`Ctrl+C` u terminalu gasi server. `--reload` znaci da ce se server sam
restartovati kad izmenis `api/main.py` (korisno dok razvijas).

## Testovi

```
pytest
pytest -v
```

Testovi pokrivaju sva tri use case-a: ECU logiku (rucno izracunati granicni
slucajevi, nezavisno od `assertions.py`/`lka_assertions.py`/`acc_assertions.py`),
scenario generatore, test engine-e i failure analitiku.

## CI/CD (GitHub Actions)

Projekat ima `.github/workflows/tests.yml` koji automatski pokrece
`pytest -v` na GitHub-ovim serverima (Python 3.10/3.11/3.12) na svaki
`push`/pull request, i moze se pokrenuti i rucno iz "Actions" taba na
GitHub-u ("Run workflow"). Ovo ne zavisi ni od cega na tvom racunaru - CI
ima svoje cisto okruzenje i svoj internet pristup, pa `pip install` tamo
radi normalno.

Da bi ovo pocelo da radi, projekat mora da bude git repozitorijum
pushovan na GitHub (ako to jos nije uradjeno):

1. Proveri da li je git instaliran: u terminalu, u folderu projekta,
   pokreni `git --version` - ako ispise verziju, sve je spremno.
2. Inicijalizuj repo (ako vec nije) i napravi prvi commit:
   ```
   git init
   git add .
   git commit -m "Initial commit - AutoTest Orchestrator V1"
   ```
   (`.gitignore` vec postoji i iskljucuje `venv/`, `__pycache__/`,
   `.idea/` i `results/*.json`, pa se oni nece slucajno commit-ovati.)
3. Na [github.com](https://github.com) napravi novi, **prazan**
   repozitorijum (bez README/gitignore/license opcije - da ne bi bilo
   konflikta sa vec postojecim fajlovima), npr. nazvan
   `autotest-orchestrator`.
4. Poveži lokalni repo sa GitHub-om i pushuj (GitHub ce ti odmah nakon
   kreiranja repo-a i sam pokazati tacne komande za tvoj nalog, ali
   obicno izgledaju ovako):
   ```
   git remote add origin https://github.com/<tvoj-github-username>/autotest-orchestrator.git
   git branch -M main
   git push -u origin main
   ```
5. Otvori tab **Actions** na GitHub-u - videces da se "Testovi" workflow
   sam pokrenuo. Kad dobije zelenu kvacicu, CI radi.

Od tog trenutka, svaki sledeci `git push` automatski pokrece sve testove
na GitHub-u (ne na tvom racunaru) - ako nesto slucajno pokvaris, saznaces
odmah kroz crveni "X" na commit-u, pre nego sto to sam primetis.

## Kako radi AEB logika

Za dati scenario (brzina, udaljenost prepreke, trenje puta, kasnjenje senzora),
Virtual ECU racuna potrebnu udaljenost za zaustavljanje:

```
reakciona_udaljenost = brzina * (kasnjenje_senzora / 1000)
kociona_udaljenost   = brzina^2 / (2 * trenje * 9.81)
potrebna_udaljenost  = reakciona_udaljenost + kociona_udaljenost

brake = ON  ako je udaljenost_do_prepreke <= potrebna_udaljenost
brake = OFF inace
```

## Kako radi LKA logika

Za dati scenario (lateralni ofset od centra trake, pola sirine trake,
lateralna brzina priblizavanja ivici, da li vozac aktivno upravlja),
Virtual ECU racuna "time to line crossing" (TTLC) - za koliko sekundi bi
vozilo preslo ivicu trake ako se nista ne promeni:

```
udaljenost_do_ivice = pola_sirine_trake - abs(lateralni_ofset)

ako je udaljenost_do_ivice <= 0:      TTLC = 0 (vec preko ivice)
ako se vozilo ne priblizava ivici:    TTLC = nedefinisano (bezbedno)
inace:                                TTLC = udaljenost_do_ivice / lateralna_brzina

intervencija = ON  ako vozac NE upravlja aktivno I TTLC <= prag (1.0s)
intervencija = OFF inace
```

Isti obrazac kao AEB (prostorni/vremenski budzet naspram praga), samo
primenjen na drugu automotive funkciju - to i jeste poenta ovog use case-a:
pokazuje da Scenario Engine / Test Engine / Analytics sloj ne zna nista
use-case-specificno, samo poziva ono sto mu se prosledi.

## Kako radi ACC logika

Za dati scenario (moja brzina, brzina vozila ispred, trenutni razmak, da
li vozac pritiska gas), Virtual ECU racuna zeljeni (bezbedni) razmak po
"constant time headway" modelu - sto brze vozis, treba ti vise prostora,
plus fiksni minimum koji vazi i pri stajanju:

```
zeljeni_razmak = MIN_GAP + moja_brzina * TIME_HEADWAY

decelerate = ON  ako je stvarni_razmak < zeljeni_razmak
decelerate = OFF inace (ili ako vozac aktivno pritiska gas - override)
```

Treci use case, isti obrazac kao AEB/LKA (prostorni/vremenski budzet
naspram praga, sa driver override-om kao kod LKA-e) - dodatna potvrda da
arhitektura generalizuje.

## Vazna napomena o "expected vs actual" (zasto uopste ima FAIL-ova)

`virtual_ecu/aeb.py`, `virtual_ecu/lka.py` i `virtual_ecu/acc.py` (actual -
sistemi pod testom) rade tacno na granici, bez rezerve.
`test_engine/assertions.py`, `test_engine/lka_assertions.py` i
`test_engine/acc_assertions.py` (expected - specifikacija/oracle) su
namerno strozi: zahtevaju `SAFETY_MARGIN = 1.15` (15% vise prostora kod
AEB-a i ACC-a, 15% duzi vremenski prag kod LKA-e), jer je to realan
bezbednosni zahtev (uslovi na putu, gume, senzorski sum nikad nisu
savrseno poznati). Kada je scenario u tom "margin gap"-u, actual kaze "jos
ne moram da reagujem", a expected kaze "trebalo je vec da reagujem" ->
FAIL. To objasnjava zasto ces sa vecim brojem scenarija videti realan
procenat FAIL-ova i popunjenu failure analizu, umesto 100% PASS.

Ovo NIJE vestacki ubaceni bug - to je stvaran, tipican nalaz koji bi test
inzenjer trazio: "sistem tehnicki radi, ali nema dovoljno bezbednosne
rezerve." Prava (nezavisna) regresiona zastita za samu fiziku/logiku
dolazi iz `tests/test_aeb.py`, `tests/test_lka.py` i `tests/test_acc.py`,
gde su ocekivane vrednosti rucno izracunate i ne zavise od
`assertions.py`/`lka_assertions.py`/`acc_assertions.py`.

Kada se u V2/V3 doda pravi STM32/CAN ECU ili integracija sa CANoe/dSPACE,
`assertions.py`/`lka_assertions.py`/`acc_assertions.py` ostaju "expected"
strana poredjenja, a "actual" dolazi sa stvarnog uredjaja - razdvajanje
tada pocinje da hvata i prave razlike u firmveru, zaokruzivanjima i
kasnjenjima, pored margine.

## Podesavanje (config.py)

Sve "brojke koje bi neko mogao pozeleti da promeni" - bezbednosne margine
(`AEB_SAFETY_MARGIN`, `LKA_SAFETY_MARGIN`, `ACC_SAFETY_MARGIN`), pragovi za
odluke (`LKA_TTLC_THRESHOLD_S`, `ACC_MIN_GAP_M`, `ACC_TIME_HEADWAY_S`),
opsezi za nasumicno generisanje scenarija (`AEB_SCENARIO_RANGES`,
`LKA_SCENARIO_RANGES`, `ACC_SCENARIO_RANGES`), pragovi za failure analitiku
i gornja granica broja scenarija po run-u (`MAX_SCENARIO_COUNT`) - zive na
jednom mestu, u `config.py` u root folderu projekta. Ne treba pretrazivati
vise fajlova da bi se npr. AEB ucinio konzervativnijim - dovoljno je
promeniti `AEB_SAFETY_MARGIN` u `config.py`.

Izuzetak je `dashboard/index.html` (`<input max="50000">` i
`MAX_SCENARIO_COUNT` u JS delu) - to je staticki HTML fajl bez build
koraka, pa te dve vrednosti treba rucno drzati u skladu sa
`config.MAX_SCENARIO_COUNT` ako se ona promeni.

## Sta je sledece (sledece faze iz roadmap-a)

1. Jos use case-ova, po istom obrascu (npr. Forward Collision Warning,
   Blind Spot Detection).
2. CAN komunikacija i STM32 kao fizicki ECU (V2) - ceka se prakticno
   embedded znanje/hardver.
3. Integracija sa CANoe/dSPACE/ECU-TEST (V3).

Radni princip iz projektnog plana: **uci -> napravi -> testiraj -> pokazi
korisniku -> validiraj -> prosiri.**
