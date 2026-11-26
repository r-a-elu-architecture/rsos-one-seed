"""REACH: a stretch target as an instrument (owner, 18 Nov 2026)."""
from rsoslang.compiler import compile_source

HEAD = "LANGUAGE RSOS 0.2\nWORLD economy\nHOST agents KIND software CHANNELS visual\nUSE HOST agents\nOBJECT cost KIND module\nPART cost.task KIND measure\n"


def verdicts(src):
    r = compile_source(HEAD + src, govern=False)
    return r, [o["verdict"] for o in r.ir["ops"] if "verdict" in o]


def codes(r):
    return {d.code for d in r.diagnostics}


def test_measured_reach_gives_distance_and_limit():
    r, v = verdicts("REACH c ON cost.task TARGET 10 AGAINST market_best MEASURE cost RESULT 3.7 LIMIT thinking\n")
    assert r.ok and v[0]["reached_share"] == 0.37
    assert v[0]["text"] == "reached 3.7x of 10x against market_best on cost; limit: thinking"


def test_blockers_open_planets_that_particles_land_on():
    r, _ = verdicts("REACH c ON cost.task TARGET 10 AGAINST b MEASURE m BLOCKERS thinking, audit\n"
                    "PARTICLE p LAND cost.task.thinking ON effort OPENS less\nDEFICIT cost.task.audit 0.5\n")
    assert r.ok and "W002_IMPLICIT_PART" not in codes(r)


def test_missing_limit_is_flagged_when_below_target():
    r, _ = verdicts("REACH c ON cost.task TARGET 10 AGAINST b MEASURE m RESULT 3\n")
    assert r.ok and "W007_REACH_LIMIT" in codes(r)
    r, _ = verdicts("REACH c ON cost.task TARGET 10 AGAINST b MEASURE m RESULT 12\n")
    assert "W007_REACH_LIMIT" not in codes(r)


def test_target_must_be_a_factor_above_one():
    r, _ = verdicts("REACH c ON cost.task TARGET 1 AGAINST b MEASURE m\n")
    assert not r.ok and "E022_REACH" in codes(r)


def test_baseline_and_measure_are_required():
    r, _ = verdicts("REACH c ON cost.task TARGET 10 MEASURE m\n")
    assert not r.ok


def test_chain_starts_from_an_earlier_reach():
    r, v = verdicts("REACH a ON cost.task TARGET 10 AGAINST b MEASURE m RESULT 3.7 LIMIT thinking\n"
                    "REACH n ON cost.task TARGET 10 AGAINST b2 MEASURE m FROM a\n")
    assert r.ok and v[1]["from"] == {"name": "a", "result": 3.7, "limit": "thinking"}
    r, _ = verdicts("REACH n ON cost.task TARGET 10 AGAINST b MEASURE m FROM nowhere\n")
    assert "E022_REACH" in codes(r)
