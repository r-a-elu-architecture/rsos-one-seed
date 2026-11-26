"""REAL3 sealed analysis (fixed in PREREG_REAL3.md before the run). Reads real/out3/*.json, writes real/RESULTS_REAL3.md/json
and real/REAL3_STAGE2_UNITS.json (the units that go to stage 2 under the sealed sequential rule).
Unit = (row, model, standard). Primary comparison: seed3v1 vs the row's standard (default). Secondary: vs strongest.
Sequential rule (two looks, Bonferroni): at each look the interval is the two-sided 97.5 % paired-t interval
(one-sided 1.25 % per look, 2.5 % overall).
  priced / fixed-budget rows ("res"): SHOWN if mean result gain > 0 and interval lower bound > 0.
  free-resource rows ("free"): SHOWN if mean resource saved > 0 with lower bound > 0, AND the result is not worse:
    mean result gain >= 0 or its lower bound >= -2 % of the standard's mean result.
  Stage 1 (8 cells): SHOWN -> stop; NOT SHOWN if the upper bound of the deciding quantity <= 0 -> stop; else UNDECIDED
  -> stage 2 (8 more cells). After stage 2 (16 cells): SHOWN or NOT SHOWN on all 16. Neuro: 8 windows, one look only."""
import os, json, glob, math, collections
from statistics import mean, stdev
from scipy.stats import t as tdist
HERE = os.path.dirname(os.path.abspath(__file__))
KIND = {"energy": "res", "economics": "res", "quantum": "res", "neuro": "res", "space": "res", "biology": "res",
        "robotics": "free", "ai_agents": "free", "ai_ai": "free", "ai_human": "free"}
def ci(x, level=0.975):
    if len(x) < 2: return (float("nan"), float("nan"))
    m, s = mean(x), stdev(x); h = tdist.ppf(1 - (1 - level) / 2, len(x) - 1) * s / math.sqrt(len(x)); return (m - h, m + h)

def judge(row, cells, against):
    cs = [c for c in cells if against in c and "seed3v1" in c]
    if len(cs) < 2: return None
    dr = [c["seed3v1"]["result"] - c[against]["result"] for c in cs]
    ds = [c[against]["resource"] - c["seed3v1"]["resource"] for c in cs]
    base_r = mean(c[against]["result"] for c in cs); base_s = mean(c[against]["resource"] for c in cs) or 1.0
    rlo, rhi = ci(dr); slo, shi = ci(ds)
    if KIND[row] == "res":
        wins = sum(x > 0 for x in dr); shown = mean(dr) > 0 and rlo > 0; futile = rhi <= 0
    else:
        wins = sum(a >= 0 and b >= 0 and (a > 0 or b > 0) for a, b in zip(dr, ds))
        noninf = mean(dr) >= 0 or rlo >= -0.02 * abs(base_r)
        shown = mean(ds) > 0 and slo > 0 and noninf; futile = shi <= 0 or (not noninf and rhi < -0.02 * abs(base_r))
    return {"kind": KIND[row], "cells": len(cs), "wins": wins, "mean_result_gain": mean(dr),
            "result_gain_pct": 100 * mean(dr) / abs(base_r) if base_r else None, "result_ci975": (rlo, rhi),
            "mean_resource_saved": mean(ds), "resource_saved_pct": 100 * mean(ds) / base_s, "resource_ci975": (slo, shi),
            "shown": bool(shown), "futile": bool(futile)}

def main():
    G = collections.defaultdict(list); stages = collections.defaultdict(set)
    for f in glob.glob(os.path.join(HERE, "out3", "*.json")):
        d = json.load(open(f))
        for key, r in d["cells"].items():
            if "skip" in r: continue
            std = key.split("|")[0]; G[(d["row"], d["model"], std)].append(r); stages[(d["row"], d["model"], std)].add(d["stage"])
    R = {}; nxt = []
    for (row, model, std), cells in sorted(G.items()):
        prim = judge(row, cells, "default"); sec = judge(row, cells, "strongest")
        last = 2 in stages[(row, model, std)] or row == "neuro"
        if prim is None: continue
        status = "SHOWN" if prim["shown"] else "NOT SHOWN" if (prim["futile"] or last) else "UNDECIDED"
        if status == "UNDECIDED": nxt.append({"row": row, "model": model})
        R[f"{row}|{model}|{std}"] = {"vs_standard": prim, "vs_strongest": sec, "status": status,
                                     "stages": sorted(stages[(row, model, std)])}
    json.dump(R, open(os.path.join(HERE, "RESULTS_REAL3.json"), "w"), indent=1, default=float)
    units = sorted({(u["row"], u["model"]) for u in nxt})
    json.dump([{"row": r, "model": m} for r, m in units], open(os.path.join(HERE, "REAL3_STAGE2_UNITS.json"), "w"), indent=1)
    def fmt(v):
        if v is None: return "–", "–", "–"
        return (f"{v['wins']}/{v['cells']}",
                f"{v['mean_result_gain']:+.4g} ({v['result_ci975'][0]:+.3g}, {v['result_ci975'][1]:+.3g}); {v['result_gain_pct'] or 0:+.2f}%",
                f"{v['mean_resource_saved']:+.4g} ({v['resource_ci975'][0]:+.3g}, {v['resource_ci975'][1]:+.3g}); {v['resource_saved_pct']:+.1f}%")
    with open(os.path.join(HERE, "RESULTS_REAL3.md"), "w") as f:
        f.write("# RESULTS REAL3 (sealed; analyze_real3.py exactly as PREREG_REAL3.md)\n\n97.5 % paired-t intervals (two looks).\n\n"
                "| Row | Model | Standard | Kind | Status | Won vs standard | Result gain | Resource saved | Won vs strongest | Result gain vs strongest | Resource saved vs strongest |\n"
                "|---|---|---|---|---|---|---|---|---|---|---|\n")
        for k, v in R.items():
            row, model, std = k.split("|"); a = fmt(v["vs_standard"]); b = fmt(v["vs_strongest"])
            f.write(f"| {row} | {model} | {std} | {v['vs_standard']['kind']} | {v['status']} | {a[0]} | {a[1]} | {a[2]} | {b[0]} | {b[1]} | {b[2]} |\n")
        f.write(f"\nStage-2 units: {units}\n")
    print(open(os.path.join(HERE, "RESULTS_REAL3.md")).read())
if __name__ == "__main__": main()
