"""REAL1 sealed analysis (fixed in PREREG_REAL1.md before the run). Reads real/out/*.json, writes real/RESULTS_REAL1.md/json."""
import os, json, glob, math, collections
from statistics import mean, stdev
HERE = os.path.dirname(os.path.abspath(__file__))
KIND = {"energy": "res", "economics": "res", "quantum": "res", "neuro": "res", "space": "res", "biology": "res",
        "robotics": "free", "ai_agents": "free", "ai_ai": "free", "ai_human": "free"}
T975 = {1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57, 6: 2.45, 7: 2.36, 8: 2.31, 9: 2.26, 10: 2.23, 11: 2.20, 12: 2.18, 13: 2.16,
        14: 2.14, 15: 2.13, 16: 2.12, 17: 2.11, 18: 2.10, 19: 2.09, 20: 2.09, 30: 2.04, 40: 2.02}
def ci(x):
    if len(x) < 2: return (float("nan"), float("nan"))
    t = T975.get(len(x) - 1, 2.0); m, s = mean(x), stdev(x); h = t * s / math.sqrt(len(x)); return (m - h, m + h)
def main():
    G = collections.defaultdict(list)
    for f in glob.glob(os.path.join(HERE, "out", "*.json")):
        d = json.load(open(f))
        for key, r in d["cells"].items():
            if "skip" in r: continue
            std = key.split("|")[0]; G[(d["row"], d["model"], std)].append(r)
    R = {}
    for (row, model, std), cells in sorted(G.items()):
        dr = [c["seed"]["result"] - c["default"]["result"] for c in cells]
        ds = [c["default"]["resource"] - c["seed"]["resource"] for c in cells]   # resource saved
        base_r = mean(c["default"]["result"] for c in cells); base_s = mean(c["default"]["resource"] for c in cells) or 1.0
        if KIND[row] == "res":
            wins = sum(x > 0 for x in dr); lo, hi = ci(dr); shown = mean(dr) > 0 and lo > 0
        else:
            wins = sum(a >= 0 and b >= 0 and (a > 0 or b > 0) for a, b in zip(dr, ds)); lo, hi = ci(ds); rlo, rhi = ci(dr)
            shown = mean(ds) > 0 and lo > 0 and (mean(dr) >= 0 or rlo >= -0.02 * abs(base_r))
        R[f"{row}|{model}|{std}"] = {"kind": KIND[row], "cells": len(cells), "wins": wins, "mean_result_gain": mean(dr),
            "result_gain_pct": 100 * mean(dr) / abs(base_r) if base_r else None, "result_ci95": ci(dr),
            "mean_resource_saved": mean(ds), "resource_saved_pct": 100 * mean(ds) / base_s, "resource_ci95": ci(ds), "SHOWN": bool(shown)}
    json.dump(R, open(os.path.join(HERE, "RESULTS_REAL1.json"), "w"), indent=1, default=float)
    with open(os.path.join(HERE, "RESULTS_REAL1.md"), "w") as f:
        f.write("# RESULTS REAL1 (sealed; analyze_real1.py exactly as PREREG_REAL1.md)\n\n| Row | Model | Standard | Kind | Cells won | Result gain (95% CI) | Resource saved (95% CI) | Shown |\n|---|---|---|---|---|---|---|---|\n")
        for k, v in R.items():
            row, model, std = k.split("|")
            f.write(f"| {row} | {model} | {std} | {v['kind']} | {v['wins']}/{v['cells']} | {v['mean_result_gain']:+.4g} ({v['result_ci95'][0]:+.3g}, {v['result_ci95'][1]:+.3g}); {v['result_gain_pct'] or 0:+.2f}% | "
                    f"{v['mean_resource_saved']:+.4g} ({v['resource_ci95'][0]:+.3g}, {v['resource_ci95'][1]:+.3g}); {v['resource_saved_pct']:+.1f}% | {'YES' if v['SHOWN'] else 'no'} |\n")
    print(open(os.path.join(HERE, "RESULTS_REAL1.md")).read())
if __name__ == "__main__": main()
