"""SC2 versus its control SC2-C (PREREGISTRATION_SC2.md, amendment 3). 0 model calls. Written before the draw.

    python experiments/sc2c_analyse.py       # -> results/sc2c.json

For every model with both cells complete (16 tasks per arm): JSON Patch's failure rate on the 8 FLOW requests per task
(SC2, the planner must find the objects) against the same requests with the objects named (SC2-C).
"""
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(os.path.dirname(HERE), "results")
sys.path.insert(0, HERE)
import sc2_tasks as S2                     # noqa: E402


def load(cell):
    out = {}
    for p in glob.glob(os.path.join(R, f"a7_results_{cell}_*.jsonl")):
        label = re.match(rf"a7_results_{cell}_(.+)\.jsonl$", os.path.basename(p)).group(1)
        for line in open(p):
            r = json.loads(line)
            out.setdefault(label, {}).setdefault(r["arm"], {})[r["seed"]] = r
    return {l: a for l, a in out.items() if all(len(a.get(x, {})) == 16 for x in ("B2", "X5b"))}


def flow_steps(seed):
    t = S2.make_task(seed)
    return {k for k, r in enumerate(t["requests"]) if re.match(S2.FLOW_REQ, r)}


def main():
    a, c = load("SC2"), load("SC2C")
    models = sorted(set(a) & set(c))
    rows, tot = {}, {"flow_fail": 0, "named_fail": 0, "steps": 0}
    for m in models:
        ff = nf = n = 0
        for seed, r in a[m]["B2"].items():
            fs = flow_steps(seed); n += len(fs)
            ff += sum(1 for s in r["steps"] if s["step"] in fs and (not s["ok"] or not s["correct"]))
            nf += sum(1 for s in c[m]["B2"][seed]["steps"] if s["step"] in fs and (not s["ok"] or not s["correct"]))
        rows[m] = {"flow_steps": n, "B2_failed_flow_wording": ff, "B2_failed_named_wording": nf,
                   "X5b_exact_SC2C": sum(r["success"] for r in c[m]["X5b"].values())}
        tot["flow_fail"] += ff; tot["named_fail"] += nf; tot["steps"] += n
    rf = tot["flow_fail"] / tot["steps"] if tot["steps"] else 0
    rn = tot["named_fail"] / tot["steps"] if tot["steps"] else 0
    V = {"Q10_finding_is_the_cause": bool(models) and tot["flow_fail"] >= 2 and rf >= 2 * rn,
         "Q11_blind_exact_control": bool(models) and all(v["X5b_exact_SC2C"] == 16 for v in rows.values())}
    out = {"models": rows, "pooled": {**tot, "rate_flow_wording": rf, "rate_named_wording": rn}, "verdicts": V}
    out["sha256"] = hashlib.sha256(json.dumps(out, sort_keys=True).encode()).hexdigest()
    json.dump(out, open(os.path.join(R, "sc2c.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
