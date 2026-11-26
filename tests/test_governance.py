"""T1: governance from the cue framework's own Spine, applied to compiled programs."""

import pytest

from rsoslang import compile_source
from rsoslang.governance import load_framework

pytestmark = pytest.mark.skipif(load_framework()[0] is None, reason="cue framework not available")
HEAD = "LANGUAGE RSOS 0.2\nWORLD w\nHOST p KIND human CHANNELS visual, kinesthetic, auditory\nUSE HOST p\nOBJECT country\n"


def codes(src):
    return [d.code for d in compile_source(src).diagnostics]


def test_person_practice_needs_consent():
    assert "E018_CONSENT" in codes(HEAD + "HEAL country SCOPE container\n")
    assert "E018_CONSENT" not in codes(HEAD + "CONSENT p FOR practice\nHEAL country SCOPE container\n")


def test_spine_wording_is_blocked():
    src = HEAD + 'CONSENT p\nOBJECT ice_bath\nHEAL country BY ice_bath\n'
    assert "E019_SPINE" in codes(src)
    assert "E019_SPINE" in codes(HEAD + 'CONSENT p\nCUE calm CODE "hold your breath until you faint" CHANNEL auditory\n')
    assert "E019_SPINE" not in codes(HEAD + 'CONSENT p\nOBJECT warm_bath\nHEAL country BY warm_bath\n')


def test_rank_claims_about_a_person_are_blocked():
    assert "E019_SPINE" in codes(HEAD + 'CONSENT p\nCUE x CODE "you are top 1% of people" CHANNEL auditory\n')


def test_safety_mode_limits_deep_work_but_allows_regulating_cues():
    base = HEAD + "CONSENT p\nSAFETY p MODE stabilise\n"
    assert "E020_GOVERNANCE" in codes(base + "HEAL country SCOPE container\n")
    assert "E020_GOVERNANCE" not in codes(base + 'CUE calm CODE "-" CHANNEL kinesthetic\n')
    crisis = HEAD + "CONSENT p\nSAFETY p MODE crisis\n"
    assert "E020_GOVERNANCE" in codes(crisis + 'CUE calm CODE "-" CHANNEL kinesthetic\n')


def test_baseline_is_always_added_and_audit_is_chained():
    res = compile_source(HEAD + "CONSENT p\nHEAL country\nBEAM country\n")
    assert "W006_BASELINE_ADDED" in [d.code for d in res.diagnostics]
    g = res.ir["governance"]
    assert g["passed"] == 2 and g["baseline"] == ["p"] and len(g["audit_head"]) == 64
    assert all(op.get("governance", {}).get("ok") for op in res.ir["ops"] if op["op"] in ("heal", "beam"))


def test_non_person_hosts_are_not_person_gated():
    src = "LANGUAGE RSOS 0.2\nWORLD w\nHOST b KIND bacterium CHANNELS light\nUSE HOST b\nOBJECT x\nHEAL x\n"
    assert "E018_CONSENT" not in codes(src)
