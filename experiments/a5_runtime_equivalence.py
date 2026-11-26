"""A5 runtime equivalence: the shipped State Runtime (rsoslang.state) reproduces the measured A5 result.

Replays every recorded X5 plan (results/a5_transcripts_S*.jsonl, the operations the model actually wrote) through
rsoslang.state.Ledger from each task's initial state, and compares the final state with the recorded one
(results/a5_results_S*.jsonl). 0 model calls. Pass = every task matches on both sets.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(ROOT, "src")]
from rsoslang import state as S      # noqa: E402
import a5_run as R                   # noqa: E402
import a1_agents as A                # noqa: E402

STEP = re.compile(r"^#\s*\d+\s*$")


def arm(r):
    return r.get("arm") or r.get("cond")


def check(set_name):
    R.setup(set_name)
    rec = {r["seed"]: r for r in map(json.loads, open(os.path.join(ROOT, f"results/a5_results_{set_name}.jsonl")))
           if arm(r) == "X5" and not r.get("tag")}
    trs = [t for t in map(json.loads, open(os.path.join(ROOT, f"results/a5_transcripts_{set_name}.jsonl")))
           if arm(t) == "X5" and not t.get("tag")]
    match, diffs = 0, []
    for t in trs:
        task = A.make_task(t["seed"])
        last = {}
        for m in t["msgs"]:
            if m["from"] == "planner" and m["to"] == "runtime" and m.get("kind", "msg") == "msg":
                last[m["step"]] = m["text"]          # the accepted (last) operations of each step
        led = S.Ledger(A.state_of_text(A.text_of(task["init"])))
        for st in sorted(last):
            led.apply("\n".join(l for l in last[st].split("\n") if not STEP.match(l)))
        want = rec[t["seed"]]["final_state"]
        if led.state == want:
            match += 1
        else:
            diffs.append(t["seed"])
    return {"tasks": len(trs), "match": match, "mismatch_seeds": diffs}


if __name__ == "__main__":
    out = {s: check(s) for s in ("S1", "S2")}
    out["verdict"] = "PASS" if all(v["match"] == v["tasks"] > 0 for v in out.values() if isinstance(v, dict)) else "FAIL"
    print(json.dumps(out, indent=1))
    sys.exit(0 if out["verdict"] == "PASS" else 1)
