"""T4: identity, archetypes, built persons and host-specific protocol choice."""

import pytest

from rsoslang import compile_source
from rsoslang.governance import load_framework
from rsoslang.identity import population, override_type, archetypes

pytestmark = pytest.mark.skipif(load_framework()[0] is None, reason="cue framework not available")
HEAD = "LANGUAGE RSOS 0.2\nWORLD w\n"


def codes(src):
    return [d.code for d in compile_source(src).diagnostics]


def test_cardiac_70_gets_calmness_and_drive_is_blocked():
    base = HEAD + "PERSONA anna AGE 70 ORGANS heart_attack GOAL calm SOURCE synthetic\nUSE HOST anna\nCONSENT anna\n"
    assert "E020_GOVERNANCE" in codes(base + "OVERRIDE anna TYPE drive\n")
    assert "E020_GOVERNANCE" not in codes(base + "OVERRIDE anna TYPE calmness\n")
    op = [o for o in compile_source(base + "OVERRIDE anna TYPE drive\n").ir["ops"] if o["op"] == "override"][0]
    assert op["recommended_override"] == "calmness"


def test_athlete_gets_drive():
    assert override_type({"age": 25, "organs": [], "goal": "sport"}) == "drive"
    assert "E020_GOVERNANCE" not in codes(HEAD + "PERSONA tom AGE 25 GOAL sport\nUSE HOST tom\nCONSENT tom\nOVERRIDE tom TYPE drive\n")


def test_identity_levels_and_archetypes():
    assert not compile_source(HEAD + 'PERSONA anna AGE 40\nIDENTITY anna mission = "help people grow"\n').errors
    assert archetypes()["EAGLE"]["tacton"] == "-.."


def test_population_is_synthetic_and_seeded():
    a, b = population(100, 7), population(100, 7)
    assert a == b and all(p["source"] == "synthetic" for p in a)
    assert {p["override"] for p in a} >= {"calmness", "regulation"}
