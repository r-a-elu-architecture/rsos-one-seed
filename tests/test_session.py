"""T2/T3: a program with a person host becomes a practice session, compiled by the cue framework's own RSX compiler."""

import pytest

from rsoslang import compile_source
from rsoslang.governance import load_framework
from rsoslang.mind.session import compile_session

pytestmark = pytest.mark.skipif(load_framework()[0] is None, reason="cue framework not available")
HEAD = "LANGUAGE RSOS 0.2\nWORLD w\nHOST p KIND human CHANNELS visual, auditory, kinesthetic, olfactory STATES eagle\nUSE HOST p\n"


def session(body):
    r = compile_source(HEAD + body)
    return compile_session(r.ir)


def test_examples_become_timelines():
    for f in ("examples/healing.rsl", "examples/robot_head.rsl"):
        r = compile_source(open(f).read())
        s = compile_session(r.ir)
        assert s["timeline"]["events"] and s["rsx"].rstrip().endswith("}")
        assert "baseline" in s["rsx"].split("PHASE")[-1]          # return to baseline is the last phase


def test_blocked_operations_are_skipped_not_run():
    s = session("OBJECT country\nHEAL country SCOPE container\n")          # no consent
    assert s["steps"] == [] and s["skipped"][0]["failed"] == ["rei"]


def test_owner_language_and_vibration_code():
    s = session('CONSENT p\nOBJECT country\nOBJECT white_dragon\nHEAL country BY white_dragon SCOPE container\n'
                'CUE eagle CODE "-.." CHANNEL kinesthetic\n')
    assert "white dragon reaches country" in s["rsx"]
    assert 'TACTON "-.."' in s["rsx"] and "ACTIVATE EAGLE" in s["rsx"]


def test_schedule_compiles_to_pulses():
    s = session("CONSENT p\nSCHEDULE d STATES associated, eagle DURATIONS 300, 60 PULSE 60 REPEAT 1 CHANNEL kinesthetic\n")
    assert "HAPTIC on=300ms off=59700ms x=5" in s["rsx"] and "PHASE eagle dur=60s" in s["rsx"]


def test_scent_cue_goes_to_the_smell_channel():
    s = session('CONSENT p\nCUE lavender CODE "white_dragon" CHANNEL olfactory\n')
    assert 'SMELL "lavender"' in s["rsx"]


def test_learning_model_prediction_is_reported():
    s = session("CONSENT p\nOBJECT x\nFUTUREPACE x SCENARIOS 3\n")
    assert s["pairings_to_80pct"] == 3 and "FOR FUTURE" in s["rsx"]
