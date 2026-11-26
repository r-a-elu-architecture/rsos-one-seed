"""A7 analysis: exactness, cost per correct task, ratios to M* (B2), error split, P1-P8. PREREGISTRATION_A7.md §5-6.
0 model calls.

    python experiments/a7_analyse.py [default|off]     # -> results/a7_<think>.json (hash of the numbers)
    python experiments/a7_analyse.py default L1,L2,L3  # A7b long tasks -> results/a7_long_default.json
"""

import json
import os
import statistics as stt
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a5_cost as C                      # noqa: E402
from common import save                  # noqa: E402

ROOT = os.path.dirname(HERE)
R = os.path.join(ROOT, "results")
ARMS = ["B2", "X5r", "X5b", "B2s"]
SETS = ["S1", "S2"]
DEPENDENT = {"INHERIT", "FUSE", "SCALE", "ROUTE", "REHOST"}      # value depends on the current state


def load(set_name, think):
    p = os.path.join(R, f"a7_results_{set_name}_{think}.jsonl")
    out = {}
    if os.path.exists(p):
        for line in open(p):
            r = json.loads(line)
            out[(r["arm"], r["seed"])] = r
    return out


def scaffold(set_name, think):
    p = os.path.join(R, "a7_scaffold.jsonl")
    t = [v for r in map(json.loads, open(p)) if r["set"] == set_name and r["think"] == think for v in r["tokens"]] \
        if os.path.exists(p) else []
    return (stt.mean(t) if t else 0.0), t


def cost(r, P, basis, sc):
    return sum(C.call_cost(c, P, basis, sc) for c in r["calls_full"])


def ratio_ci(a, b, n=10000, seed=12345):
    a, b = np.asarray(a, float), np.asarray(b, float)
    idx = np.random.default_rng(seed).integers(0, len(a), size=(n, len(a)))
    rat = a[idx].mean(axis=1) / b[idx].mean(axis=1)
    return [float(np.percentile(rat, 2.5)), float(np.percentile(rat, 97.5))]


def per_correct(costs, exact):
    return (sum(costs) / exact) if exact else None


def summary(set_name, think, P, runs, sc):
    out = {}
    seeds = sorted({s for (_, s) in runs})
    for arm in ARMS:
        rs = [runs[(arm, s)] for s in seeds if (arm, s) in runs]
        if not rs:
            continue
        ca = [cost(r, P, "api", sc) for r in rs]
        cb = [cost(r, P, "billed", 0) for r in rs]
        ex = sum(r["success"] for r in rs)
        wrong = [s for r in rs for s in r["steps"] if s["ok"] and not s["correct"]]
        failed = [s for r in rs for s in r["steps"] if not s["ok"]]
        out[arm] = {"tasks": len(rs), "exact": ex, "replica_exact": sum(r["replica_success"] for r in rs),
                    "line_acc": stt.mean(r["line_acc"] for r in rs),
                    "calls": stt.mean(r["n_calls"] for r in rs), "in_tok": stt.mean(r["in_tok"] - sc * r["n_calls"]
                                                                                 for r in rs),
                    "out_tok": stt.mean(r["out_tok"] for r in rs), "think_tok": stt.mean(r["think_tok"] for r in rs),
                    "invalid": sum(r["invalid_ops"] for r in rs), "steps_wrong": len(wrong),
                    "steps_failed": len(failed),
                    "wrong_dependent": sum(1 for s in wrong + failed if s["kind"] in DEPENDENT),
                    "cost_api": stt.mean(ca), "cost_billed": stt.mean(cb),
                    "cost_per_correct_api": per_correct(ca, ex), "wall_sec": stt.mean(r["wall_sec"] for r in rs),
                    "healed_zero_call": sum(e["healed_zero_call"] for r in rs for e in r["drift"]),
                    "drifts": sum(len(r["drift"]) for r in rs), "_ca": ca}
    for arm in ("X5r", "X5b"):
        if arm in out and "B2" in out and out[arm]["tasks"] == out["B2"]["tasks"]:
            a, b = out[arm]["_ca"], out["B2"]["_ca"]
            o = out[arm]
            if out["B2"]["cost_api"] > 0:                    # local models (A7c) cost 0: no ratio
                o["cost_ratio_vs_B2"] = o["cost_api"] / out["B2"]["cost_api"]
                o["cost_ratio_vs_B2_ci"] = ratio_ci(a, b)
            pb, pa = out["B2"]["cost_per_correct_api"], o["cost_per_correct_api"]
            o["cost_per_correct_ratio_vs_B2"] = (pa / pb) if (pa and pb) else None
            o["reach_distance_x"] = (pb / pa) if (pa and pb) else None       # how many times below M*
    for v in out.values():
        v.pop("_ca", None)
    return out


def verdicts(T, label="default"):
    def g(s, a, k):
        return T.get(s, {}).get(a, {}).get(k)
    if set(T) == {"L1", "L2", "L3"}:                     # A7b long tasks (amendment of 18 Nov 13:40)
        if any(g(s, a, "tasks") != 16 for s in ("L1", "L2", "L3") for a in ("B2", "X5b")):
            return {"status": "incomplete"}
        x = g("L3", "X5b", "in_tok") / g("L1", "X5b", "in_tok")
        b = g("L3", "B2", "in_tok") / g("L1", "B2", "in_tok")
        return {"P9_long_tasks_M*_breaks": g("L2", "B2", "exact") <= 8 and g("L2", "X5b", "exact") >= 15,
                "P10_blind_input_flat_in_state": x <= 1.5 and b >= 3,
                "P10_input_growth_L3_over_L1": {"X5b": x, "B2": b},
                "exact": {c: {a: g(c, a, "exact") for a in ARMS if g(c, a, "tasks")} for c in ("L1", "L2", "L3")},
                "cost_per_correct_ratio_X5b_vs_B2": {c: g(c, "X5b", "cost_per_correct_ratio_vs_B2")
                                                     for c in ("L1", "L2", "L3")},
                "REACH_cost_tenfold_distance_x": {c: g(c, "X5b", "reach_distance_x") for c in ("L1", "L2", "L3")}}
    if label.startswith("local"):                         # A7c: P11 on S1 (pre-registration section 5)
        if g("S1", "X5b", "tasks") != 16 or g("S1", "B2", "tasks") != 16:
            return {"status": "incomplete"}
        return {"P11_local_floor": g("S1", "X5b", "exact") >= 12 and g("S1", "B2", "exact") <= 4,
                "S1_exact": {a: g("S1", a, "exact") for a in ARMS if g("S1", a, "tasks")},
                "S1_steps_wrong_or_failed": {a: g("S1", a, "steps_wrong") + g("S1", a, "steps_failed")
                                             for a in ARMS if g("S1", a, "tasks")},
                "S1_invalid": {a: g("S1", a, "invalid") for a in ARMS if g("S1", a, "tasks")}}
    have = all(g(s, a, "tasks") == 16 for s in SETS for a in ("B2", "X5r", "X5b"))
    if not have:
        return {"status": "incomplete"}
    V = {}
    V["P1_runtime_beats_M*"] = all(g(s, "X5r", "exact") >= 15 for s in SETS) and \
        any(g(s, "B2", "exact") <= 13 for s in SETS)
    V["P2_blind_no_loss"] = all(g(s, "X5b", "exact") >= g(s, "X5r", "exact") - 1 for s in SETS)
    V["P3_cost_per_correct_half"] = all((g(s, "X5b", "cost_per_correct_ratio_vs_B2") or 9) <= 0.5 for s in SETS)
    V["P4_blind_input_half"] = all(g(s, "X5b", "in_tok") <= 0.5 * g(s, "B2", "in_tok") for s in SETS)
    V["P5_M*_thinks_more"] = all(g(s, "B2", "think_tok") >= 2 * g(s, "X5b", "think_tok") for s in SETS)
    b2w = sum(g(s, "B2", "steps_wrong") + g(s, "B2", "steps_failed") for s in SETS)
    b2d = sum(g(s, "B2", "wrong_dependent") for s in SETS)
    V["P6_M*_errors_on_dependent_steps"] = (b2d >= 0.7 * b2w) if b2w else None
    A7A = ("B2", "X5r", "X5b")
    V["P7_calls_le_3"] = all(g(s, a, "calls") <= 3 for s in SETS for a in A7A)
    V["P8_drift_healed_all_arms"] = all(g(s, a, "healed_zero_call") == g(s, a, "drifts") for s in SETS for a in A7A)
    V["REACH_cost_tenfold_distance_x"] = {s: g(s, "X5b", "reach_distance_x") for s in SETS}
    return V


if __name__ == "__main__":
    think = sys.argv[1] if len(sys.argv) > 1 else "default"
    if len(sys.argv) > 2:
        SETS = sys.argv[2].split(",")
    P = C.prices()["sheets"][C.prices()["run_time_sheet"]]
    T, SC = {}, {}
    for s in SETS:
        sc, toks = scaffold(s, think)
        SC[s] = {"mean": sc, "tokens": toks}
        T[s] = summary(s, think, P, load(s, think), sc)
    payload = {"think": think, "price_sheet": C.prices()["run_time_sheet"], "scaffold": SC, "tables": T,
               "predictions": verdicts(T, think)}
    path, dig = save(f"a7_long_{think}" if SETS == ["L1", "L2", "L3"] else f"a7_{think}", payload)
    print(json.dumps({"tables": T, "predictions": payload["predictions"]}, indent=1))
    print("saved", path, dig)
