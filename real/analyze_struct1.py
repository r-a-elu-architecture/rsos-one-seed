"""STRUCT1 sealed analysis (fixed in real/PREREG_STRUCT1.md before the run). Reads real/outs1/*.json, writes
real/RESULTS_STRUCT1.md and .json. Nothing here may change after the run.
Unit = (row, model, standard). Primary question: does the "structure" arm (seed3v1 with every host-written lever off)
beat BOTH the row's standard ("default") and plain rollout ("rollout")?
Per unit, two one-sided paired-t tests on 8 cells (one look):
  priced / fixed-budget rows (economics, space): result gain of structure over the comparator;
  free-resource rows (ai_agents, ai_human, ai_ai): resource saved by structure over the comparator.
Holm correction at family-wise one-sided alpha 0.025 over ALL primary tests (units x {default, rollout}).
A primary test PASSES if Holm rejects it AND, for free-resource rows, the result is not worse: mean result gain >= 0
or the two-sided 95 % lower bound of the result gain >= -2 % of the comparator's mean result (REAL3's guard).
A unit passes if both of its tests pass. A row passes if any of its units passes.
LEVEL (fixed before the run): UNPRECEDENTED >= 4 of 5 rows; STRONG 2-3 rows; NOT SHOWN < 2 rows.
Secondary (reported, no level): seed3v1 vs strongest, structure vs seed3v1, seed3v1 vs default, 95 % intervals."""
import os, json, glob, math, collections
from statistics import mean, stdev
from scipy.stats import t as tdist
HERE = os.path.dirname(os.path.abspath(__file__))
KIND = {"economics": "res", "space": "res", "ai_agents": "free", "ai_human": "free", "ai_ai": "free"}
ROWS = ["ai_agents", "ai_human", "ai_ai", "economics", "space"]
ALPHA = 0.025

def p_one(x):
    if len(x) < 2: return 1.0
    m, s = mean(x), stdev(x)
    if s == 0: return 0.0 if m > 0 else 1.0
    return float(1 - tdist.cdf(m / (s / math.sqrt(len(x))), len(x) - 1))

def ci95(x):
    if len(x) < 2: return (float("nan"), float("nan"))
    m, s = mean(x), stdev(x); h = tdist.ppf(0.975, len(x) - 1) * s / math.sqrt(len(x)); return (m - h, m + h)

def comp(row, cells, arm, against):
    cs = [c for c in cells if arm in c and against in c]
    if len(cs) < 2: return None
    dr = [c[arm]["result"] - c[against]["result"] for c in cs]
    ds = [c[against]["resource"] - c[arm]["resource"] for c in cs]
    base_r = mean(c[against]["result"] for c in cs); base_s = mean(c[against]["resource"] for c in cs) or 1.0
    q = dr if KIND[row] == "res" else ds
    rlo, rhi = ci95(dr)
    noninf = KIND[row] == "res" or mean(dr) >= 0 or rlo >= -0.02 * abs(base_r)
    return {"cells": len(cs), "p_one_sided": p_one(q), "mean_result_gain": mean(dr), "result_ci95": (rlo, rhi),
            "result_gain_pct": 100 * mean(dr) / abs(base_r) if base_r else None, "mean_resource_saved": mean(ds),
            "resource_ci95": ci95(ds), "resource_saved_pct": 100 * mean(ds) / base_s, "noninferior": bool(noninf),
            "wins": sum(x > 0 for x in q)}

def main():
    G = collections.defaultdict(list)
    for f in glob.glob(os.path.join(HERE, "outs1", "*.json")):
        d = json.load(open(f))
        for key, r in d["cells"].items(): G[(d["row"], d["model"], key.split("|")[0])].append(r)
    units = {}; tests = []
    for (row, model, std), cells in sorted(G.items()):
        u = {k: comp(row, cells, a, b) for k, (a, b) in {
            "structure_vs_default": ("structure", "default"), "structure_vs_rollout": ("structure", "rollout"),
            "seed3v1_vs_strongest": ("seed3v1", "strongest"), "structure_vs_seed3v1": ("structure", "seed3v1"),
            "seed3v1_vs_default": ("seed3v1", "default"), "rollout_vs_default": ("rollout", "default")}.items()}
        units[(row, model, std)] = u
        for k in ("structure_vs_default", "structure_vs_rollout"):
            tests.append([u[k]["p_one_sided"] if u[k] else 1.0, (row, model, std), k])
    tests.sort(key=lambda x: x[0]); m = len(tests); go = True
    for i, t in enumerate(tests):
        thr = ALPHA / (m - i); rej = go and t[0] <= thr; go = rej
        u = units[t[1]][t[2]]
        if u: u["holm_threshold"] = thr; u["holm_rejected"] = bool(rej); u["pass"] = bool(rej and u["noninferior"])
    rows_pass = {}
    for row in ROWS:
        rows_pass[row] = any((u["structure_vs_default"] or {}).get("pass") and (u["structure_vs_rollout"] or {}).get("pass")
                             for (r, _, _), u in units.items() if r == row)
    n = sum(rows_pass.values())
    level = "UNPRECEDENTED" if n >= 4 else "STRONG" if n >= 2 else "NOT SHOWN"
    out = {"level": level, "rows_passed": n, "rows": rows_pass, "holm_tests": m,
           "units": {"|".join(k): v for k, v in units.items()}}
    json.dump(out, open(os.path.join(HERE, "RESULTS_STRUCT1.json"), "w"), indent=1, default=float)
    def f(v, key):
        if not v: return "–"
        if key == "res": return f"{v['result_gain_pct']:+.2f} % (CI {v['result_ci95'][0]:+.3g}, {v['result_ci95'][1]:+.3g}), p={v['p_one_sided']:.4f}"
        return (f"{v['resource_saved_pct']:+.1f} % resource (CI {v['resource_ci95'][0]:+.3g}, {v['resource_ci95'][1]:+.3g}), "
                f"result {v['mean_result_gain']:+.3g}, p={v['p_one_sided']:.4f}")
    L = ["# RESULTS STRUCT1 (sealed; analyze_struct1.py exactly as PREREG_STRUCT1.md)", "",
         f"**LEVEL: {level}** ({n} of 5 rows: structure beats both the standard and plain rollout after Holm over {m} tests).", "",
         "| Row | Model | Standard | Structure vs standard | pass | Structure vs plain rollout | pass | Full seed vs strongest (secondary) | Structure vs full seed |",
         "|---|---|---|---|---|---|---|---|---|"]
    for (row, model, std), u in sorted(units.items()):
        k = KIND[row]; sd, sr = u["structure_vs_default"], u["structure_vs_rollout"]
        L.append(f"| {row} | {model} | {std} | {f(sd, k)} | {'YES' if sd and sd.get('pass') else 'no'} | {f(sr, k)} | "
                 f"{'YES' if sr and sr.get('pass') else 'no'} | {f(u['seed3v1_vs_strongest'], k)} | {f(u['structure_vs_seed3v1'], k)} |")
    L += ["", "Rows passed: " + ", ".join(f"{r}: {'YES' if v else 'no'}" for r, v in rows_pass.items())]
    open(os.path.join(HERE, "RESULTS_STRUCT1.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L))

if __name__ == "__main__":
    main()
