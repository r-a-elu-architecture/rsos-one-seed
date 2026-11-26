"""CONF1 sealed analysis (fixed in real/PREREG_CONF1.md before any run). Reads real/outc1/*.json, writes
real/RESULTS_CONF1.md and .json. Nothing here may change after the run.
Primary family (Holm, step-down adjusted p): per unit, the FULL SEED (seed3v1) vs the row's standard (default), one-sided
paired t on all cells of the unit. Units: ai_agents|react, ai_agents|selfcons, ai_human, economics, space.
  economics, space (fixed budget): result gain.  AI rows (free resource): resource (tokens) saved, and the result must not
  be worse (mean result gain >= 0, or its 95 % lower bound >= -2 % of the standard's mean result).
A domain PASSES if one of its units has Holm-adjusted p < 1e-5, and for the AI rows < 1e-7, and the AI guard holds.
Operator trace: every host-written LEVER the full seed chose in any cell (names starting "P" or "F:") must map to an RSOS
operator through the host class's op_of() or the seed's COMMON table (real/seed3_ops.py), both written before this test.
Native branches are listed with their mapping where one exists (e.g. AI agents "stop" has none) but are not part of it.
LEVEL (fixed before the run): UNPRECEDENTED = all 4 domains pass AND every chosen family traces to an operator;
STRONG = 2-3 domains pass; NOT SHOWN = fewer than 2. (If all 4 pass but a family does not trace: STRONG.)
Secondary family (separate Holm, same thresholds, reported, decides nothing about the level): "generated" vs default
in the AI rows: does the operator language alone, written by a fresh agent, produce moves that beat the standard?
Also reported: full seed vs strongest; generated vs full seed; 95 % intervals."""
import os, sys, json, glob, math, collections
from statistics import mean, stdev
from scipy.stats import t as tdist
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, "hosts")]
KIND = {"economics": "res", "space": "res", "ai_agents": "free", "ai_human": "free"}
THR = {"economics": 1e-5, "space": 1e-5, "ai_agents": 1e-7, "ai_human": 1e-7}
DOMAINS = ["ai_agents", "ai_human", "economics", "space"]

def p_one(x):
    if len(x) < 2: return 1.0
    m, s = mean(x), stdev(x)
    if s == 0: return 0.0 if m > 0 else 1.0
    return float(tdist.sf(m / (s / math.sqrt(len(x))), len(x) - 1))

def ci95(x):
    if len(x) < 2: return (float("nan"), float("nan"))
    m, s = mean(x), stdev(x); h = tdist.ppf(0.975, len(x) - 1) * s / math.sqrt(len(x)); return (m - h, m + h)

def comp(row, cells, arm, against):
    cs = [c for c in cells if arm in c and against in c]
    if len(cs) < 2: return None
    dr = [c[arm]["result"] - c[against]["result"] for c in cs]; ds = [c[against]["resource"] - c[arm]["resource"] for c in cs]
    base_r = mean(c[against]["result"] for c in cs); base_s = mean(c[against]["resource"] for c in cs) or 1.0
    rlo, rhi = ci95(dr)
    guard = KIND[row] == "res" or mean(dr) >= 0 or rlo >= -0.02 * abs(base_r)
    return {"cells": len(cs), "p_one_sided": p_one(dr if KIND[row] == "res" else ds), "mean_result_gain": mean(dr),
            "result_ci95": (rlo, rhi), "result_gain_pct": 100 * mean(dr) / abs(base_r) if base_r else None,
            "mean_resource_saved": mean(ds), "resource_ci95": ci95(ds), "resource_saved_pct": 100 * mean(ds) / base_s,
            "guard": bool(guard), "wins": sum(x > 0 for x in (dr if KIND[row] == "res" else ds)),
            "std_result_mean": base_r, "arm_result_mean": mean(c[arm]["result"] for c in cs)}

def holm(items):
    """items: list of [p, key]; returns {key: adjusted p} (step-down, monotone)."""
    items = sorted(items); m = len(items); out = {}; run = 0.0
    for i, (p, k) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p)); out[k] = run
    return out

def trace(G):
    """Lineage of every family the full seed chose: the host class's own op_of() (written before this test), else the
    seed's COMMON table. The LEVEL criterion covers host-written levers only (names starting with "P" or "F:"), the moves
    STRUCT1 showed carry the gain; native branches are reported with their mapping, not part of the criterion."""
    import importlib, seed3_ops as O
    hostcls = {}
    for row, mod, cls in (("ai_agents", "ai_agents", "AIAgents"), ("ai_human", "ai_human", "AIHuman"),
                          ("economics", "economics", "Economics"), ("space", "space", "Space")):
        try: hostcls[row] = getattr(importlib.import_module(mod), cls)
        except Exception: pass
    import re
    fams = collections.defaultdict(collections.Counter)
    for (row, _, _), cells in G.items():
        for c in cells:
            for k, n in c.get("seed3v1", {}).get("choices", {}).items():
                name = k.split("|")[0]
                if name == "present" or re.match(r"^(past-|future\+)\d", name): continue   # time branches = the structure
                fams[row][name] += n
    table = {}
    for row, cnt in fams.items():
        h = hostcls.get(row)
        for name, n in cnt.items():
            cands = list(dict.fromkeys([name, name.split("-")[0], ":".join(name.split(":")[:2]).split("-")[0],
                                        re.split(r"[:-]", name)[0], name.split("_")[0], re.split(r"[:-]", name)[0].rstrip("0123456789")]))
            op = None
            for cnd in cands:
                if h is not None and hasattr(h, "op_of"):
                    try: op = h.op_of(h, cnd)
                    except Exception: op = None
                if not op: op = O.COMMON.get(cnd)
                if op: break
            table[f"{row}|{name}"] = {"uses": n, "operator": op, "lever": name.startswith(("P", "F:"))}
    return table

def main():
    G = collections.defaultdict(list)
    for f in glob.glob(os.path.join(HERE, "outc1", "*.json")):
        d = json.load(open(f))
        for key, r in d["cells"].items():
            if "seed3v1" not in r: continue
            G[(d["row"], d["model"], key.split("|")[0])].append(r)
    units = {}
    for (row, model, std), cells in sorted(G.items()):
        units[(row, model, std)] = {"full_vs_standard": comp(row, cells, "seed3v1", "default"),
                                    "full_vs_strongest": comp(row, cells, "seed3v1", "strongest"),
                                    "generated_vs_standard": comp(row, cells, "generated", "default"),
                                    "generated_vs_full": comp(row, cells, "generated", "seed3v1")}
    for fam, key in (("primary", "full_vs_standard"), ("generated", "generated_vs_standard")):
        items = [[u[key]["p_one_sided"], k] for k, u in units.items() if u[key]]
        adj = holm(items)
        for k, u in units.items():
            if u[key]: u[key]["holm_adjusted_p"] = adj[k]; u[key]["pass"] = bool(adj[k] < THR[k[0]] and u[key]["guard"])
    dom = {d: any((u["full_vs_standard"] or {}).get("pass") for k, u in units.items() if k[0] == d) for d in DOMAINS}
    gen = {d: any((u["generated_vs_standard"] or {}).get("pass") for k, u in units.items() if k[0] == d)
           for d in ("ai_agents", "ai_human")}
    tr = trace(G); untraced = [k for k, v in tr.items() if not v["operator"] and v["lever"]]
    n = sum(dom.values())
    level = ("UNPRECEDENTED" if n == 4 and not untraced else "STRONG" if n >= 2 else "NOT SHOWN")
    out = {"level": level, "domains_passed": n, "domains": dom, "generated_domains_passed": gen,
           "operator_trace": tr, "untraced": untraced, "units": {"|".join(k): v for k, v in units.items()}}
    json.dump(out, open(os.path.join(HERE, "RESULTS_CONF1.json"), "w"), indent=1, default=float)
    def f(v, row):
        if not v: return "–"
        hp = f", Holm p={v['holm_adjusted_p']:.2e}" if "holm_adjusted_p" in v else f", p={v['p_one_sided']:.2e}"
        if KIND[row] == "res": return f"{v['result_gain_pct']:+.2f} % ({v['wins']}/{v['cells']}){hp}"
        return f"{v['resource_saved_pct']:+.1f} % tokens, result {v['mean_result_gain']:+.3f} ({v['wins']}/{v['cells']}){hp}"
    L = ["# RESULTS CONF1 (sealed; analyze_conf1.py exactly as PREREG_CONF1.md)", "",
         f"**LEVEL: {level}** ({n} of 4 domains pass; untraced families: {len(untraced)}).", "",
         "| Row | Model | Standard | Full seed vs standard | pass | Full seed vs strongest | Generated vs standard | pass | Generated vs full seed |",
         "|---|---|---|---|---|---|---|---|---|"]
    for (row, model, std), u in sorted(units.items()):
        L.append(f"| {row} | {model} | {std} | {f(u['full_vs_standard'], row)} | {'YES' if (u['full_vs_standard'] or {}).get('pass') else 'no'} | "
                 f"{f(u['full_vs_strongest'], row)} | {f(u['generated_vs_standard'], row)} | "
                 f"{'YES' if (u['generated_vs_standard'] or {}).get('pass') else 'no' if u['generated_vs_standard'] else '–'} | {f(u['generated_vs_full'], row)} |")
    L += ["", "Domains: " + ", ".join(f"{d}: {'PASS' if v else 'no'}" for d, v in dom.items()),
          "Generated arm (secondary): " + ", ".join(f"{d}: {'PASS' if v else 'no'}" for d, v in gen.items()), "",
          "## Operator trace (families the full seed chose -> RSOS operator)", "", "| Row / family | Uses | Kind | Operator |", "|---|---|---|---|"]
    L += [f"| {k} | {v['uses']} | {'lever' if v['lever'] else 'native'} | {v['operator'] or ('UNTRACED' if v['lever'] else 'no mapping')} |" for k, v in sorted(tr.items())]
    open(os.path.join(HERE, "RESULTS_CONF1.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L[:14]))

if __name__ == "__main__":
    main()
