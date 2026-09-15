"""
Critical scenario search - deliberately hunts for the parameter
combination closest to the safety-margin boundary, instead of hoping
random scenario generation (scenarios/generator.py) stumbles into it.

One file per use case (critical_search/aeb.py, lka.py, acc.py), following
the same "deliberately identical structure, proof the pattern repeats"
convention already used across virtual_ecu/, test_engine/, and
analytics/. See critical_search/aeb.py for the full rationale.
"""
