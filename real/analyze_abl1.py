"""ABL1 sealed analysis (fixed in real/PREREG_ABL1.md before any ABL1 cell runs). Reads real/outa1/*.json and writes
real/RESULTS_ABL1.md and .json. Nothing here may change after the run.
Rows and their one deciding contrast (full RSOS vs full minus the row's operator):
  ai_agents (self-consistency standard): Law 2 off            deciding = tokens saved  (minus.resource - full.resource)
  ai_ai:                                 Law 5 off            deciding = tokens saved  (minus.resource - full.resource)
  space:                                 composition + Law 4 landing off   deciding = result gain (full.result - minus.result)
A row PASSES if ALL hold:
  1. CAUSE: one-sided paired t of the deciding contrast, Holm-adjusted over the 3 rows, p < 1e-5;
  2. GUARD (AI rows): full's result is not worse than minus's (mean >= 0 or 95 % lower bound >= -2 % of minus's mean result);
  3. FULL BEATS STANDARD: one-sided paired p < 1e-3 on the same deciding quantity vs the standard;
  4. LAW 0, no harm: full's result vs the standard: mean >= 0 or 95 % lower bound >= -2 % of the standard's mean result.
LEVEL (fixed before the run): UNPRECEDENTED = 3 of 3 rows; STRONG = 2; NOT SHOWN = fewer."""
import os, json, glob, math, collections
from statistics import mean, stdev
from scipy.stats import t as tdist
HERE = os.path.dirname(os.path.abspath(__file__))
OP = {"ai_agents": "Law 2 (blind plan) off", "ai_ai": "Law 5 (hologram / key) off", "space": "composition + Law 4 landing off"}

def p_one(x):
    m, s = mean(x), stdev(x)
    if s == 0: return 0.0 if m > 0 else 1.0
    return float(tdist.sf(m / (s / math.sqrt(len(x))), len(x) - 1))

def lo95(x): return mean(x) - tdist.ppf(0.975, len(x) - 1) * stdev(x) / math.sqrt(len(x))

def main():
    G = collections.defaultdict(list)
    for f in glob.glob(os.path.join(HERE, "outa1", "*.json")):
        d = json.load(open(f))
        for r in d["cells"].values():
            if all(a in r for a in ("default", "full", "minus")): G[d["row"]].append(r)
    U = {}
    for row, cells in sorted(G.items()):
        res = row == "space"
        q = (lambda c, a: c[a]["result"]) if res else (lambda c, a: -c[a]["resource"])
        d = [q(c, "full") - q(c, "minus") for c in cells]
        ds = [q(c, "full") - q(c, "default") for c in cells]
        g = [c["full"]["result"] - c["minus"]["result"] for c in cells]
        h = [c["full"]["result"] - c["default"]["result"] for c in cells]
        bm = mean(c["minus"]["result"] for c in cells); bs = mean(c["default"]["result"] for c in cells)
        base = mean(c["minus"]["result"] if res else c["minus"]["resource"] for c in cells)
        U[row] = {"operator": OP[row], "cells": len(cells), "mean_full_vs_minus": mean(d), "pct_full_vs_minus": 100 * mean(d) / abs(base),
                  "p_cause": p_one(d), "wins": sum(x > 0 for x in d), "p_full_vs_standard": p_one(ds), "mean_full_vs_standard": mean(ds),
                  "guard": bool(res or mean(g) >= 0 or lo95(g) >= -0.02 * abs(bm)), "law0": bool(mean(h) >= 0 or lo95(h) >= -0.02 * abs(bs)),
                  "harmed_cells": sum(x < 0 for x in h), "result_full_vs_minus": mean(g), "result_full_vs_standard": mean(h),
                  "means": {a: {"result": mean(c[a]["result"] for c in cells), "resource": mean(c[a]["resource"] for c in cells)} for a in ("default", "full", "minus")}}
    order = sorted(U, key=lambda k: U[k]["p_cause"]); run = 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, (len(order) - i) * U[k]["p_cause"])); U[k]["holm_p"] = run
    for u in U.values(): u["pass"] = bool(u["holm_p"] < 1e-5 and u["guard"] and u["p_full_vs_standard"] < 1e-3 and u["law0"])
    n = sum(u["pass"] for u in U.values()); level = "UNPRECEDENTED" if n >= 3 else "STRONG" if n == 2 else "NOT SHOWN"
    json.dump({"level": level, "rows_passed": n, "rows": U}, open(os.path.join(HERE, "RESULTS_ABL1.json"), "w"), indent=1, default=float)
    L = ["# RESULTS ABL1 (sealed; analyze_abl1.py exactly as PREREG_ABL1.md)", "",
         f"**LEVEL: {level}** ({n} of 3 rows: switching the row's RSOS operator off costs the result at Holm p < 1e-5; full RSOS beats the standard; no harm).", "",
         "| Row | Operator switched off | Cells | Full vs minus | Holm p | Wins | Guard | Full vs standard (p) | Law 0 | Pass |", "|---|---|---|---|---|---|---|---|---|---|"]
    for row, u in sorted(U.items()):
        unit = "% result" if row == "space" else "% tokens saved"
        L.append(f"| {row} | {u['operator']} | {u['cells']} | {u['pct_full_vs_minus']:+.1f} {unit} (result {u['result_full_vs_minus']:+.3f}) | {u['holm_p']:.1e} | "
                 f"{u['wins']}/{u['cells']} | {'ok' if u['guard'] else 'FAIL'} | {u['mean_full_vs_standard']:+.3g} ({u['p_full_vs_standard']:.1e}) | "
                 f"{'ok' if u['law0'] else 'FAIL'} ({u['harmed_cells']} harmed) | {'YES' if u['pass'] else 'no'} |")
    L += ["", "Means per arm (result, resource):", ""] + [f"- {row}: " + "; ".join(f"{a} {m['result']:.4g}, {m['resource']:.4g}" for a, m in u["means"].items()) for row, u in sorted(U.items())]
    open(os.path.join(HERE, "RESULTS_ABL1.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L))

if __name__ == "__main__":
    main()
