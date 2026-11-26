from rsoslang.agents.workflow import build
from rsoslang.agents.tickets import make_tickets
from rsoslang.timeline import record, play, pause_at, rewind, branch, painting_at

T = make_tickets(20, 5, typo_rate=0.5)


def test_record_play_pause_rewind_and_cut():
    f = record(build(), T)
    assert f[0]["node"] == "intake" and len(play(f, 0, 1, 5)) == 5 and len(play(f, 0, 3, 5)) == 5
    i = pause_at(f, "classify")[0]
    assert f[i]["node"] == "classify" and rewind(f, i, 2)[0]["node"] == "classify"


def test_branch_is_a_counterfactual_and_frames_are_paintings():
    f = record(build(), T)
    tid = next(fr["ticket"] for fr in f if fr["node"] == "classify" and fr["state"] != "crashed"
               and fr["state"].get("category") == "other")
    b, _ = branch(build(), T, tid, "PIERCE spell_corrector THROUGH classify.brain\n")
    assert [fr["ticket"] for fr in b] and all(fr["ticket"] == tid for fr in b)   # the same ticket, run again
    assert any(fr["node"] == "classify" for fr in b)
    p = painting_at(f, 5)
    assert p["active"] == f[5]["node"] and "intake" in p["nodes"]
