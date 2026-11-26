"""CONF5 sealed analysis (fixed in real/PREREG_CONF5.md before any CONF5 cell runs). Reads real/outc5/*.json, writes
real/RESULTS_CONF5.md and .json. Nothing here may change after the run.
Per row, the identified RSOS structure (ai_agents: "full"; ai_ai, space: "v1") vs PLAIN ROLLOUT (the RSOS-free planning
baseline), paired by cell.
  ai_agents, ai_ai (free resource): deciding = tokens saved (rollout.resource - rsos.resource);
  space (fixed budget): deciding = result gain (rsos.result - rollout.result).
A row PASSES if ALL hold:
  1. one-sided paired t, Holm-adjusted over the 3 rows, p < 1e-5;
  2. guard (AI rows): RSOS's result vs rollout's: mean >= 0 or 95 % lower bound >= -2 % of rollout's mean result;
  3. Law 0, no harm: RSOS's result vs the standard's: mean >= 0 or 95 % lower bound >= -2 % of the standard's mean result.
LEVEL: UNPRECEDENTED = 3 of 3 rows; STRONG = 2; NOT SHOWN = fewer.
Reported, decides nothing: RSOS vs standard, rollout vs standard, wins, AI-agents learning slope over each job's cells."""
import os, json, glob, math, collections
from statistics import mean, stdev
from scipy.stats import t as tdist
HERE = os.path.dirname(os.path.abspath(__file__))

def p_one(x):
    m, s = mean(x), stdev(x)
    if s == 0: return 0.0 if m > 0 else 1.0
    return float(tdist.sf(m / (s / math.sqrt(len(x))), len(x) - 1))

def lo95(x): return mean(x) - tdist.ppf(0.975, len(x) - 1) * stdev(x) / math.sqrt(len(x))

def main():
    G = collections.defaultdict(list); POS = collections.defaultdict(list)
    for f in sorted(glob.glob(os.path.join(HERE, "outc5", "*.json"))):
        d = json.load(open(f)); A = d["rsos_arm"]
        for i, (c, r) in enumerate(sorted(d["cells"].items(), key=lambda x: int(x[0]))):
            if all(a in r for a in ("default", "rollout", A)): G[d["row"]].append((A, r)); POS[d["row"]].append(i)
    U = {}
    for row, items in sorted(G.items()):
        res = row == "space"; A = items[0][0]; cells = [r for _, r in items]
        q = (lambda c, a: c[a]["result"]) if res else (lambda c, a: -c[a]["resource"])
        d = [q(c, A) - q(c, "rollout") for c in cells]
        g = [c[A]["result"] - c["rollout"]["result"] for c in cells]
        h = [c[A]["result"] - c["default"]["result"] for c in cells]
        br = mean(c["rollout"]["result"] for c in cells); bs = mean(c["default"]["result"] for c in cells)
        base = mean(c["rollout"]["result"] if res else c["rollout"]["resource"] for c in cells)
        U[row] = {"rsos_arm": A, "cells": len(cells), "mean_vs_rollout": mean(d), "pct_vs_rollout": 100 * mean(d) / abs(base),
                  "p": p_one(d), "wins": sum(x > 0 for x in d),
                  "guard": bool(res or mean(g) >= 0 or lo95(g) >= -0.02 * abs(br)), "law0": bool(mean(h) >= 0 or lo95(h) >= -0.02 * abs(bs)),
                  "harmed_cells": sum(x < 0 for x in h), "result_vs_rollout": mean(g), "result_vs_standard": mean(h),
                  "means": {a: {"result": mean(c[a]["result"] for c in cells), "resource": mean(c[a]["resource"] for c in cells)} for a in ("default", "rollout", A)}}
        if row == "ai_agents":
            by = collections.defaultdict(list)
            for i, x in zip(POS[row], d): by[i].append(x)
            U[row]["by_position_in_job"] = {i: mean(v) for i, v in sorted(by.items())}
    order = sorted(U, key=lambda k: U[k]["p"]); run = 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, (len(order) - i) * U[k]["p"])); U[k]["holm_p"] = run
    for u in U.values(): u["pass"] = bool(u["holm_p"] < 1e-5 and u["guard"] and u["law0"])
    n = sum(u["pass"] for u in U.values()); level = "UNPRECEDENTED" if n >= 3 else "STRONG" if n == 2 else "NOT SHOWN"
    json.dump({"level": level, "rows_passed": n, "rows": U}, open(os.path.join(HERE, "RESULTS_CONF5.json"), "w"), indent=1, default=float)
    L = ["# RESULTS CONF5 (sealed; analyze_conf5.py exactly as PREREG_CONF5.md)", "",
         f"**LEVEL: {level}** ({n} of 3 rows: the identified RSOS structure beats plain rollout at Holm p < 1e-5, guard and Law 0 held).", "",
         "| Row | RSOS structure | Cells | vs plain rollout | Holm p | Wins | Guard | Law 0 | Pass |", "|---|---|---|---|---|---|---|---|---|"]
    for row, u in sorted(U.items()):
        unit = "% result" if row == "space" else "% tokens saved"
        L.append(f"| {row} | {u['rsos_arm']} | {u['cells']} | {u['pct_vs_rollout']:+.2f} {unit} (result {u['result_vs_rollout']:+.3f}) | {u['holm_p']:.1e} | "
                 f"{u['wins']}/{u['cells']} | {'ok' if u['guard'] else 'FAIL'} | {'ok' if u['law0'] else 'FAIL'} ({u['harmed_cells']} harmed) | {'YES' if u['pass'] else 'no'} |")
    L += ["", "Means per arm (result, resource):", ""] + [f"- {row}: " + "; ".join(f"{a} {m['result']:.4g}, {m['resource']:.4g}" for a, m in u["means"].items()) for row, u in sorted(U.items())]
    if "ai_agents" in U: L += ["", "AI agents, tokens saved vs rollout by position of the cell in its job (trace persists): " +
                               ", ".join(f"{i}: {v:+.2f}" for i, v in U["ai_agents"]["by_position_in_job"].items())]
    open(os.path.join(HERE, "RESULTS_CONF5.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L))

if __name__ == "__main__":
    main()
