"""A5 analysis: costs, ratios, K1-K6. PREREGISTRATION_A5.md sections 4-6. 0 model calls.

    python experiments/a5_analyse.py        # -> results/a5_cost.json (hash of the numbers), printed tables
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
ARMS = ["B1", "X1", "X1s", "X2", "X3", "X5"]
SETS = ["S1", "S2"]
OFFLINE = {"S1": 0.005214, "S2": 0.004206}


def load(set_name):
    p = os.path.join(R, f"a5_results_{set_name}.jsonl")
    out = {}
    if os.path.exists(p):
        for line in open(p):
            r = json.loads(line)
            out[(r["arm"], r["seed"])] = r
    return out


def scaffold(set_name):
    rows = [json.loads(x) for x in open(os.path.join(R, "a5_scaffold.jsonl"))]
    t = [v for r in rows if r["set"] == set_name for v in r["tokens"]]
    return stt.mean(t), t


def task_cost(r, P, basis, sc):
    return sum(C.call_cost(c, P, basis, sc) for c in r["calls_full"])


def paired_ratio_ci(a, b, n=10000, seed=12345):
    a, b = np.asarray(a, float), np.asarray(b, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(a), size=(n, len(a)))
    ratios = a[idx].mean(axis=1) / b[idx].mean(axis=1)
    return [float(np.percentile(ratios, 2.5)), float(np.percentile(ratios, 97.5))]


def role_class(rs, P, sc):
    by_role, by_class = {}, {"input": 0.0, "cache_write": 0.0, "cache_read": 0.0, "output": 0.0}
    for r in rs:
        for c in r["calls_full"]:
            ro = c["role"]
            d = by_role.setdefault(ro, {"calls": 0, "content_in": 0, "out": 0, "think": 0, "cost_api": 0.0})
            d["calls"] += 1
            d["content_in"] += c["in"] + c["cache_w"] + c["cache_r"] - sc
            d["out"] += c["out"]
            d["think"] += c.get("think", 0) or 0
            d["cost_api"] += C.call_cost(c, P, "api", sc)
            w1 = c.get("cache_w1h", 0) or 0
            by_class["input"] += c["in"] * P["input"] / 1e6
            by_class["cache_write"] += ((c["cache_w"] - w1) * P["cache_write_5m"] + w1 * P["cache_write_1h"]) / 1e6
            by_class["cache_read"] += c["cache_r"] * P["cache_read"] / 1e6
            by_class["output"] += c["out"] * P["output"] / 1e6
    n = len(rs)
    return ({k: {x: y / n for x, y in v.items()} for k, v in by_role.items()},
            {k: v / n for k, v in by_class.items()})


def summary(set_name, runs, sc, prices):
    T = {}
    seeds = sorted({s for (_, s) in runs})
    for arm in ARMS:
        rs = [runs[(arm, s)] for s in seeds if (arm, s) in runs]
        if not rs:
            continue
        P0 = prices["sheets"][prices["run_time_sheet"]]
        cost = {sh: {b: [task_cost(r, P, b, sc) for r in rs] for b in ("api", "billed")}
                for sh, P in prices["sheets"].items()}
        roles, classes = role_class(rs, P0, sc)
        d = {"tasks": len(rs), "seeds": [r["seed"] for r in rs],
             "success": sum(r["success"] for r in rs), "replica_success": sum(r["replica_success"] for r in rs),
             "wrong_final_lines": sum(len(r["final_errors"]) for r in rs),
             "steps_failed": sum(r["steps_failed"] for r in rs),
             "calls_mean": stt.mean(r["n_calls"] for r in rs), "out_mean": stt.mean(r["out_tok"] for r in rs),
             "think_mean": stt.mean(sum(c.get("think", 0) or 0 for c in r["calls_full"]) for r in rs),
             "in_mean": stt.mean(r["in_tok"] for r in rs),
             "content_in_mean": stt.mean(r["in_tok"] - sc * r["n_calls"] for r in rs),
             "billed_tok_mean": stt.mean(r["billed_tok"] for r in rs),
             "wall_sec_mean": stt.mean(r["wall_sec"] for r in rs),
             "channel_tok_mean": stt.mean(r["channel_tok"] for r in rs),
             "channel_bpe_mean": stt.mean(r["channel_bpe"] for r in rs),
             "cost_mean": {sh: {b: stt.mean(v) for b, v in x.items()} for sh, x in cost.items()},
             "cost_by_role_api": roles, "cost_by_class_billed": classes,
             "cli_cost_usd_mean": stt.mean(r["cost_usd"] for r in rs)}
        ev = [e for r in rs for e in r["drift"]]
        d["drift"] = {"events": len(ev), "healed": sum(e["healed"] for e in ev),
                      "healed_zero_call": sum(e["healed_zero_call"] for e in ev),
                      "in_authoritative_final": sum(e["silent_in_final"] for e in ev),
                      "in_any_copy_final": sum(e["in_any_copy_final"] for e in ev)}
        if set_name == "S2":
            cm = [c for r in rs for c in (r.get("computes") or [])]
            d["computes"] = {k: sum(1 for c in cm if c["class"] == k) for k in ("correct", "traced", "other_wrong")}
            d["computes"]["drift_reading"] = {k: sum(1 for c in cm if c["class"] == k and c["kind"] == "drift")
                                              for k in ("correct", "traced", "other_wrong")}
        if arm != "B1":
            st = [s for r in rs for s in r["steps"]]
            d["invalid_ops"] = sum(r["invalid_ops"] for r in rs)
            if arm == "X5":
                d["audited_steps_mean"] = sum(1 for s in st if s.get("audited")) / len(rs)
                d["audit_rounds_mean"] = stt.mean(len(r.get("audits", [])) for r in rs)
            else:
                att = [a for s in st for a in s["attempts"]]
                d["audit_calls_mean"] = sum(1 for a in att if "audit" in a) / len(rs)
                d["audit_rejects"] = sum(1 for a in att if "audit" in a and not a["approved"])
                d["planner_attempts_mean"] = len(att) / len(rs)
            d["steps_wrong"] = sum(1 for s in st if s["ok"] and not s["correct"])
            d["audit_misses"] = {"approved": sum(1 for s in st if s.get("audit_miss") == "approved"),
                                 "unsampled": sum(1 for s in st if s.get("audit_miss") == "unsampled")}
            d["audit_miss_list"] = [{"seed": r["seed"], "step": s["step"], "kind": s["audit_miss"],
                                     "ops": s.get("ops") or (s["attempts"][-1].get("ops") if s.get("attempts") else None)}
                                    for r in rs for s in r["steps"] if s.get("audit_miss")]
        T[arm] = (d, cost)
    # ratios vs B1 (paired over seeds)
    out = {}
    if "B1" in T:
        b1 = T["B1"][1]
        for arm, (d, cost) in T.items():
            d["ratio_vs_B1"] = {sh: {b: stt.mean(cost[sh][b]) / stt.mean(b1[sh][b]) for b in ("api", "billed")}
                                for sh in cost}
            if arm != "B1" and len(cost["haiku-5-5"]["api"]) == len(b1["haiku-5-5"]["api"]):
                d["ratio_ci_api_runtime"] = paired_ratio_ci(cost["haiku-5-5"]["api"], b1["haiku-5-5"]["api"])
            d["calls_ratio"] = d["calls_mean"] / T["B1"][0]["calls_mean"]
            d["out_ratio"] = d["out_mean"] / T["B1"][0]["out_mean"]
    for arm, (d, _) in T.items():
        out[arm] = d
    return out


def verdicts(S):
    def g(s, a):
        return S.get(s, {}).get(a)
    K = {}
    sheets = ["haiku-5-5", "alt-sonnet-5-5", "alt-fable-5-2"]

    def cost_k(arm, basis):
        if not all(g(s, arm) and g(s, "B1") for s in SETS):
            return None
        r = {s: {sh: g(s, arm)["ratio_vs_B1"][sh][basis] for sh in sheets} for s in SETS}
        run = all(r[s]["haiku-5-5"] <= 0.1 for s in SETS)
        allsh = all(r[s][sh] <= 0.1 for s in SETS for sh in sheets)
        v = "pass" if run and allsh else ("fail (price-dependent)" if run else "fail")
        return {"ratios": r, "verdict": v}
    K["K1"] = {"api (primary)": cost_k("X3", "api"), "billed": cost_k("X3", "billed")}
    K["K1_secondary_X5"] = {"api": cost_k("X5", "api"), "billed": cost_k("X5", "billed")}
    if all(g(s, "X1s") and g(s, "B1") for s in SETS):
        K["K2"] = {s: {"X1s_calls": g(s, "X1s")["calls_mean"], "B1_calls": g(s, "B1")["calls_mean"],
                       "ratio": g(s, "X1s")["calls_ratio"]} for s in SETS}
        K["K2"]["verdict"] = "pass" if all(K["K2"][s]["ratio"] <= 0.4 for s in SETS) else "fail"
    if all(g(s, "X2") and g(s, "B1") for s in SETS):
        K["K3"] = {s: {"X2_out": g(s, "X2")["out_mean"], "B1_out": g(s, "B1")["out_mean"],
                       "ratio": g(s, "X2")["out_ratio"]} for s in SETS}
        K["K3"]["verdict"] = "pass" if all(K["K3"][s]["ratio"] <= 0.25 for s in SETS) else "fail"
    for arm, key in (("X3", "K4"), ("X5", "K4_secondary_X5")):
        if all(g(s, arm) and g(s, "B1") for s in SETS):
            K[key] = {s: {"exact": g(s, arm)["success"], "B1_exact": g(s, "B1")["success"],
                          "replica": g(s, arm)["replica_success"], "tasks": g(s, arm)["tasks"]} for s in SETS}
            K[key]["verdict"] = "pass" if all(K[key][s]["exact"] >= K[key][s]["B1_exact"] - 1 and
                                              K[key][s]["replica"] == K[key][s]["tasks"] for s in SETS) else "fail"
    for arm, key in (("X3", "K5"), ("X5", "K5_secondary_X5")):
        if g("S2", arm):
            t = g("S2", arm)["computes"]["traced"]
            K[key] = {"traced": t, "B1_traced": g("S2", "B1")["computes"]["traced"] if g("S2", "B1") else None,
                      "verdict": "pass" if t == 0 else "fail"}
    if all(g(s, "B1") for s in SETS):
        K["K6"] = {s: {"offline": OFFLINE[s], "live": g(s, "B1")["cost_mean"]["haiku-5-5"]["api"],
                       "dev": g(s, "B1")["cost_mean"]["haiku-5-5"]["api"] / OFFLINE[s] - 1} for s in SETS}
        K["K6"]["verdict"] = "pass" if all(abs(K["K6"][s]["dev"]) <= 0.25 for s in SETS) else "fail"
    return K


def main():
    prices = C.prices()
    S, scs = {}, {}
    for s in SETS:
        runs = load(s)
        if not runs:
            continue
        sc, raw = scaffold(s)
        scs[s] = {"mean": sc, "calls": raw}
        S[s] = summary(s, runs, sc, prices)
    K = verdicts(S)
    payload = {"prices": prices, "scaffold": scs, "tables": S, "predictions": K}
    path, dig = save("a5_cost", payload)
    for s, T in S.items():
        print(f"== {s} (scaffold {scs[s]['mean']:.1f})")
        for arm, d in T.items():
            print(f"{arm:4s} n={d['tasks']} exact={d['success']} rep={d['replica_success']} calls={d['calls_mean']:.1f} "
                  f"out={d['out_mean']:.0f} content_in={d['content_in_mean']:.0f} "
                  f"api=${d['cost_mean']['haiku-5-5']['api']:.6f} billed=${d['cost_mean']['haiku-5-5']['billed']:.6f} "
                  f"r_api={d.get('ratio_vs_B1', {}).get('haiku-5-5', {}).get('api', float('nan')):.3f} "
                  f"r_billed={d.get('ratio_vs_B1', {}).get('haiku-5-5', {}).get('billed', float('nan')):.3f}"
                  + (f" inv={d['invalid_ops']} miss={d['audit_misses']}" if arm != "B1" else ""))
    print(json.dumps(K, indent=1))
    print(path, dig)


if __name__ == "__main__":
    main()
