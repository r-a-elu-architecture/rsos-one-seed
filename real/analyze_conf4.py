"""CONF4 sealed analysis (fixed in real/PREREG_CONF4.md before any CONF4 cell runs). Reads real/outc4/*.json, writes
real/RESULTS_CONF4.md and .json. Nothing here may change after the run.
Question: does the RSOS language itself make a capable AI write better decision programs than the same AI without it?
Per cell: RSOS = mean of arms R1, R2, R3; CONTROL = mean of arms C1, C2, C3 (three independent agents each).
Units: ai_agents|react, ai_agents|selfcons, ai_human|std, ai_ai|std, space|std.
  AI rows (free resource): deciding quantity = tokens saved by RSOS vs CONTROL (CONTROL.resource - RSOS.resource);
  satellite (fixed budget): result gain RSOS - CONTROL.
Primary family: one-sided paired t per unit, Holm step-down adjusted p over the 5 units.
A unit PASSES if ALL hold:
  1. Holm-adjusted p < 1e-5 (RSOS beats CONTROL);
  2. result guard vs CONTROL (AI rows): mean result gain >= 0 or its 95 % lower bound >= -2 % of CONTROL's mean result;
  3. Law 0, no harm: RSOS's result is not worse than the STANDARD's: mean gain >= 0 or 95 % lower bound >= -2 % of the
     standard's mean result;
  4. Law 4, need-driven use: the RSOS programs were the chosen action in >= 25 % of decisions (mean over R1-R3);
  5. floor: RSOS's mean deciding quantity is at least the STRUCTURE arm's (vs the standard), i.e. the programs add.
A row passes if any of its units passes.
LEVEL (fixed before the run): UNPRECEDENTED = >= 3 of 4 rows; STRONG = 2 rows; NOT SHOWN = fewer.
Reported, decides nothing: RSOS vs standard, CONTROL vs standard, each agent vs CONTROL, harmed cells, use shares."""
import os, json, glob, math, collections
from statistics import mean, stdev
from scipy.stats import t as tdist
HERE = os.path.dirname(os.path.abspath(__file__))
KIND = {"space": "res", "ai_agents": "free", "ai_human": "free", "ai_ai": "free"}
R_ARMS, C_ARMS = ("R1", "R2", "R3"), ("C1", "C2", "C3")
ROWS = ["ai_agents", "ai_human", "ai_ai", "space"]

def p_one(x):
    if len(x) < 2: return 1.0
    m, s = mean(x), stdev(x)
    if s == 0: return 0.0 if m > 0 else 1.0
    return float(tdist.sf(m / (s / math.sqrt(len(x))), len(x) - 1))

def lo95(x):
    if len(x) < 2: return float("nan")
    return mean(x) - tdist.ppf(0.975, len(x) - 1) * stdev(x) / math.sqrt(len(x))

def avg(c, arms, key): return mean(c[a][key] for a in arms)

def use_share(c, arms):
    out = []
    for a in arms:
        ch = c[a].get("choices", {}); tot = sum(ch.values()) or 1
        out.append(sum(n for k, n in ch.items() if k.startswith(a + ":")) / tot)
    return mean(out)

def holm(items):
    items = sorted(items); m = len(items); out = {}; run = 0.0
    for i, (p, k) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p)); out[k] = run
    return out

def main():
    G = collections.defaultdict(list)
    for f in glob.glob(os.path.join(HERE, "outc4", "*.json")):
        d = json.load(open(f))
        for key, r in d["cells"].items():
            if all(a in r for a in ("default", "structure") + R_ARMS + C_ARMS): G[(d["row"], key.split("|")[0])].append(r)
    U = {}
    for (row, std), cells in sorted(G.items()):
        res = KIND[row] == "res"
        q = (lambda c, arms: avg(c, arms, "result")) if res else (lambda c, arms: -avg(c, arms, "resource"))
        d_rc = [q(c, R_ARMS) - q(c, C_ARMS) for c in cells]                     # RSOS vs CONTROL (deciding)
        g_rc = [avg(c, R_ARMS, "result") - avg(c, C_ARMS, "result") for c in cells]
        g_rs = [avg(c, R_ARMS, "result") - c["default"]["result"] for c in cells]  # RSOS vs standard (result)
        base_c = mean(avg(c, C_ARMS, "result") for c in cells); base_s = mean(c["default"]["result"] for c in cells)
        def vs_std(arms): return mean(q(c, arms) - (c["default"]["result"] if res else -c["default"]["resource"]) for c in cells)
        q_struct = mean(q(c, ("structure",)) - (c["default"]["result"] if res else -c["default"]["resource"]) for c in cells)
        per_agent = {a: {"mean_vs_control": mean(q(c, (a,)) - q(c, C_ARMS) for c in cells),
                         "p": p_one([q(c, (a,)) - q(c, C_ARMS) for c in cells]),
                         "use_share": mean(use_share(c, (a,)) for c in cells)} for a in R_ARMS + C_ARMS}
        base_res = mean(avg(c, C_ARMS, "resource") for c in cells) or 1.0
        U[(row, std)] = {
            "cells": len(cells), "p_rsos_vs_control": p_one(d_rc), "mean_rsos_vs_control": mean(d_rc),
            "pct_rsos_vs_control": (100 * mean(d_rc) / abs(base_c) if res else 100 * mean(d_rc) / base_res),
            "wins": sum(x > 0 for x in d_rc),
            "guard_vs_control": bool(res or mean(g_rc) >= 0 or lo95(g_rc) >= -0.02 * abs(base_c)),
            "law0_no_harm": bool(mean(g_rs) >= 0 or lo95(g_rs) >= -0.02 * abs(base_s)),
            "harmed_cells": sum(x < 0 for x in g_rs),
            "use_share_rsos": mean(use_share(c, R_ARMS) for c in cells), "use_share_control": mean(use_share(c, C_ARMS) for c in cells),
            "rsos_vs_standard": vs_std(R_ARMS), "control_vs_standard": vs_std(C_ARMS), "structure_vs_standard": q_struct,
            "floor_ok": bool(vs_std(R_ARMS) >= q_struct), "result_gain_vs_control": mean(g_rc), "per_agent": per_agent}
    adj = holm([[u["p_rsos_vs_control"], k] for k, u in U.items()])
    for k, u in U.items():
        u["holm_p"] = adj[k]
        u["pass"] = bool(adj[k] < 1e-5 and u["guard_vs_control"] and u["law0_no_harm"] and u["use_share_rsos"] >= 0.25 and u["floor_ok"])
    rows = {r: any(u["pass"] for k, u in U.items() if k[0] == r) for r in ROWS}
    n = sum(rows.values()); level = "UNPRECEDENTED" if n >= 3 else "STRONG" if n == 2 else "NOT SHOWN"
    json.dump({"level": level, "rows_passed": n, "rows": rows, "units": {"|".join(k): v for k, v in U.items()}},
              open(os.path.join(HERE, "RESULTS_CONF4.json"), "w"), indent=1, default=float)
    L = ["# RESULTS CONF4 (sealed; analyze_conf4.py exactly as PREREG_CONF4.md)", "",
         f"**LEVEL: {level}** ({n} of 4 rows: the RSOS language's programs beat the control programs at Holm p < 1e-5, with no harm, used >= 25 %, above the floor).", "",
         "| Row | Standard | Cells | RSOS vs control | Holm p | Wins | Guard | Law 0 | RSOS use | Control use | RSOS vs std | Control vs std | Structure vs std | Pass |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for (row, std), u in sorted(U.items()):
        unit = "% result" if KIND[row] == "res" else "% tokens"
        L.append(f"| {row} | {std} | {u['cells']} | {u['pct_rsos_vs_control']:+.1f} {unit} (result {u['result_gain_vs_control']:+.3f}) | {u['holm_p']:.1e} | "
                 f"{u['wins']}/{u['cells']} | {'ok' if u['guard_vs_control'] else 'FAIL'} | {'ok' if u['law0_no_harm'] else 'FAIL'} ({u['harmed_cells']} harmed) | "
                 f"{100*u['use_share_rsos']:.0f} % | {100*u['use_share_control']:.0f} % | {u['rsos_vs_standard']:+.3g} | {u['control_vs_standard']:+.3g} | "
                 f"{u['structure_vs_standard']:+.3g} | {'YES' if u['pass'] else 'no'} |")
    L += ["", "Rows: " + ", ".join(f"{r}: {'PASS' if v else 'no'}" for r, v in rows.items()), "", "## Each agent vs the control mean (secondary)", "",
          "| Row | Standard | " + " | ".join(R_ARMS + C_ARMS) + " |", "|---|---|" + "---|" * 6]
    for (row, std), u in sorted(U.items()):
        L.append(f"| {row} | {std} | " + " | ".join(f"{u['per_agent'][a]['mean_vs_control']:+.3g} (use {100*u['per_agent'][a]['use_share']:.0f} %)" for a in R_ARMS + C_ARMS) + " |")
    open(os.path.join(HERE, "RESULTS_CONF4.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L[:12]))

if __name__ == "__main__":
    main()
