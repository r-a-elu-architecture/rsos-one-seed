"""A8 analysis: blind planning across models (PREREGISTRATION_A8.md). 0 model calls.
    python experiments/a8_analyse.py        # -> results/a8.json
Reads every results/a7_results_<cell>_<label>.jsonl for cells S1, L3 and labels other than the A7 ones
(default, off), plus A7's default runs as the Haiku 5.5 rows."""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a5_cost as C                     # noqa: E402
from common import save                 # noqa: E402

R = os.path.join(os.path.dirname(HERE), "results")
DEP = {"INHERIT", "FUSE", "SCALE", "ROUTE", "REHOST"}
PRICED = {"default": "haiku-5-5", "haiku_b2s": "haiku-5-5", "sonnet55": "alt-sonnet-5-5", "opus55": None}


def rows():
    out = {}
    for p in glob.glob(os.path.join(R, "a7_results_*_*.jsonl")):
        m = re.match(r"a7_results_(S1|L3)_(.+)\.jsonl$", os.path.basename(p))
        if not m or m.group(2) in ("off",):
            continue
        cell, label = m.groups()
        for line in open(p):
            r = json.loads(line)
            out.setdefault((label, cell, r["arm"]), {})[r["seed"]] = r
    return out


def table():
    prices = C.prices()["sheets"]
    T = {}
    for (label, cell, arm), rs in sorted(rows().items()):
        rs = list(rs.values())
        failed = [s for r in rs for s in r["steps"] if not s["ok"] or not s["correct"]]
        sheet = PRICED.get(label)
        cost = None
        if sheet in prices and all(r["calls_full"] for r in rs):
            P = prices[sheet]
            tot = sum(C.call_cost(c, P, "api", 571 if label in ("default", "haiku_b2s", "sonnet55", "opus55") else 0)
                      for r in rs for c in r["calls_full"])
            ex = sum(r["success"] for r in rs)
            cost = tot / ex if ex else None
        T.setdefault(label, {}).setdefault(cell, {})[arm] = {
            "tasks": len(rs), "exact": sum(r["success"] for r in rs), "failed_steps": len(failed),
            "failed_dependent": sum(1 for s in failed if s["kind"] in DEP),
            "model": (rs[0]["calls_full"][0].get("model") if rs[0]["calls_full"] else None), "cost_per_correct": cost}
    return T


def verdicts(T):
    def g(l, c, a, k):
        return T.get(l, {}).get(c, {}).get(a, {}).get(k)
    labels = [l for l in T if l not in ("default",)]
    V = {}
    big = [l for l in labels if not l.startswith("local_")]
    V["G1_invariance"] = all((g(l, c, "X5b", "exact") or 0) >= 15 for l in big + ["default"] for c in T.get(l, {})
                             if g(l, c, "X5b", "tasks"))
    fb = sum(g(l, c, a, "failed_steps") or 0 for l in T for c in T[l] for a in ("B2", "B2s"))
    fd = sum(g(l, c, a, "failed_dependent") or 0 for l in T for c in T[l] for a in ("B2", "B2s"))
    fx = sum(g(l, c, "X5b", "failed_steps") or 0 for l in T for c in T[l])
    fb2 = sum(g(l, c, "B2", "failed_steps") or 0 for l in T for c in T[l])
    V["G2_error_class"] = (fb > 0 and fd >= 0.9 * fb and fx <= 0.1 * fb2)
    V["G2_counts"] = {"m_star_failed": fb, "m_star_dependent": fd, "blind_failed": fx}
    priced = [l for l in ("default", "sonnet55") if g(l, "L3", "B2", "cost_per_correct") and
              g(l, "L3", "X5b", "cost_per_correct")]
    V["G3_cost_L3"] = (all(g(l, "L3", "X5b", "cost_per_correct") <= g(l, "L3", "B2", "cost_per_correct") for l in priced)
                       if priced else None)
    hb = {c: g("haiku_b2s", c, "B2s", "exact") for c in ("S1", "L3")}
    V["G4_stronger_m_star"] = (all(hb[c] is not None and hb[c] <= g("default", c, "X5b", "exact") for c in hb) and
                               (g("haiku_b2s", "L3", "B2s", "cost_per_correct") or 0) >=
                               1.2 * (g("default", "L3", "X5b", "cost_per_correct") or 9))
    V["G5_no_family_where_m_star_wins"] = not any((g(l, c, "B2", "exact") or 0) - (g(l, c, "X5b", "exact") or 0) >= 2
                                                  for l in T for c in T[l])
    V["REACH_families_blind_exact"] = sorted({l for l in T for c in T[l] if (g(l, c, "X5b", "exact") or 0) >= 15})
    return V


if __name__ == "__main__":
    T = table()
    payload = {"tables": T, "predictions": verdicts(T)}
    path, dig = save("a8", payload)
    print(json.dumps(payload, indent=1, default=str)[:4000])
    print("saved", path, dig)
