"""CONF3 sealed analysis (fixed in real/PREREG_CONF3.md before any CONF3 cell runs). Reads ONLY CONF3 outputs
(real/outc3/*.json), an independent, higher-powered confirmation; writes real/RESULTS_CONF3.md and .json.
Nothing here may change after the run. Claim 3 uses the "composed" arm (operator chains) instead of "generated".
All tests: one-sided paired t on all cells of a unit; Holm step-down adjusted p within each claim's family.
Result guard for free-resource rows (AI rows): mean result gain >= 0, or its 95 % lower bound >= -2 % of the standard's mean.
CLAIM 1, cross-domain seed. Family: full seed vs standard, units AI agents|react, AI agents|selfcons, AI-human, AI-AI,
  inventory, satellite (6 tests). A row passes if one of its units has Holm p < 1e-5 (+ guard in AI rows).
  UNPRECEDENTED = all 5 rows; STRONG = 3-4; NOT SHOWN = fewer.
CLAIM 2, communication principle (meaning through structure, not volume). Family: full seed vs standard on tokens,
  units AI agents|react, AI agents|selfcons, AI-human, AI-AI (4 tests); a row passes if one of its units has fewer tokens at
  Holm p < 1e-7 AND mean result gain >= 0 (equal or better result). UNPRECEDENTED = all 3 rows; STRONG = 2; NOT SHOWN fewer.
CLAIM 3, the RSOS language composes winning moves. Family: composed vs standard, units AI agents|react, AI agents|selfcons, AI-human, AI-AI,
  satellite (5 tests); a row passes if one of its units has Holm p < 1e-5 (+ guard in AI rows).
  UNPRECEDENTED = >= 3 of 4 rows; STRONG = 2; NOT SHOWN fewer.
Lineage: every family the full seed and the generated arm chose, mapped to an RSOS operator (host class op_of, the seed's
COMMON table, or the generated move's own operator name "G:<op>"); reported with every claim."""
import os, sys, json, glob, math, re, importlib, collections
from statistics import mean, stdev
from scipy.stats import t as tdist
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, "hosts")]
KIND = {"economics": "res", "space": "res", "ai_agents": "free", "ai_human": "free", "ai_ai": "free"}

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
    rlo, _ = ci95(dr); q = dr if KIND[row] == "res" else ds
    return {"cells": len(cs), "p_one_sided": p_one(q), "p_tokens": p_one(ds), "mean_result_gain": mean(dr),
            "result_ci95": ci95(dr), "result_gain_pct": 100 * mean(dr) / abs(base_r) if base_r else None,
            "resource_saved_pct": 100 * mean(ds) / base_s, "resource_ci95": ci95(ds),
            "guard": bool(KIND[row] == "res" or mean(dr) >= 0 or rlo >= -0.02 * abs(base_r)),
            "equal_or_better": bool(mean(dr) >= 0), "wins": sum(x > 0 for x in q)}

def holm(items):
    items = sorted(items); m = len(items); out = {}; run = 0.0
    for i, (p, k) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p)); out[k] = run
    return out

def load():
    G = collections.defaultdict(list)
    for d_ in ("outc3",):
        for f in glob.glob(os.path.join(HERE, d_, "*.json")):
            d = json.load(open(f))
            for key, r in d["cells"].items(): G[(d["row"], key.split("|")[0])].append(r)
    return G

def lineage(G):
    import seed3_ops as O
    cls = {}
    for row, mod, c in (("ai_agents", "ai_agents", "AIAgents"), ("ai_human", "ai_human", "AIHuman"), ("ai_ai", "ai_ai", "AiAi"),
                        ("economics", "economics", "Economics"), ("space", "space", "Space")):
        try: cls[row] = getattr(importlib.import_module(mod), c)
        except Exception: pass
    cnt = collections.defaultdict(collections.Counter)
    for (row, _), cells in G.items():
        for c in cells:
            for arm in ("seed3v1", "composed"):
                for k, n in c.get(arm, {}).get("choices", {}).items():
                    name = k.split("|")[0]
                    if name == "present" or re.match(r"^(past-|future\+)\d", name): continue
                    cnt[(row, arm)][name] += n
    out = {}
    for (row, arm), cc in cnt.items():
        h = cls.get(row)
        for name, n in cc.items():
            if name.startswith(("G:", "C:")): op = name[2:]
            else:
                op = None
                for cnd in dict.fromkeys([name, name.split("-")[0], ":".join(name.split(":")[:2]).split("-")[0],
                                          re.split(r"[:-]", name)[0], name.split("_")[0], re.split(r"[:-]", name)[0].rstrip("0123456789")]):
                    if h is not None and hasattr(h, "op_of"):
                        try: op = h.op_of(h, cnd)
                        except Exception: op = None
                    if not op: op = O.COMMON.get(cnd)
                    if op: break
            out[f"{row}|{arm}|{name}"] = {"uses": n, "operator": op, "lever": name.startswith(("P", "F:", "G:", "C:"))}
    return out

def main():
    G = load(); U = {}
    for (row, std), cells in sorted(G.items()):
        U[(row, std)] = {"full": comp(row, cells, "seed3v1", "default"), "strong": comp(row, cells, "seed3v1", "strongest"),
                         "gen": comp(row, cells, "composed", "default"), "gen_vs_full": comp(row, cells, "composed", "seed3v1")}
    def fam(key, rows, pfield):
        items = [[u[key][pfield], k] for k, u in U.items() if k[0] in rows and u[key]]
        return holm(items)
    c1 = fam("full", ["ai_agents", "ai_human", "ai_ai", "economics", "space"], "p_one_sided")
    c2 = fam("full", ["ai_agents", "ai_human", "ai_ai"], "p_tokens")
    c3 = fam("gen", ["ai_agents", "ai_human", "ai_ai", "space"], "p_one_sided")
    def rowpass(adj, key, thr, extra):
        res = collections.defaultdict(bool)
        for k, p in adj.items():
            u = U[k][key]; res[k[0]] |= bool(p < thr and extra(u))
        return dict(res)
    r1 = rowpass(c1, "full", 1e-5, lambda u: u["guard"])
    r2 = rowpass(c2, "full", 1e-7, lambda u: u["equal_or_better"])
    r3 = rowpass(c3, "gen", 1e-5, lambda u: u["guard"])
    n1, n2, n3 = sum(r1.values()), sum(r2.values()), sum(r3.values())
    L1 = "UNPRECEDENTED" if n1 == 5 else "STRONG" if n1 >= 3 else "NOT SHOWN"
    L2 = "UNPRECEDENTED" if n2 == 3 else "STRONG" if n2 == 2 else "NOT SHOWN"
    L3 = "UNPRECEDENTED" if n3 >= 3 else "STRONG" if n3 == 2 else "NOT SHOWN"
    lin = lineage(G)
    out = {"claim1": {"level": L1, "rows": r1, "holm": {"|".join(k): v for k, v in c1.items()}},
           "claim2": {"level": L2, "rows": r2, "holm": {"|".join(k): v for k, v in c2.items()}},
           "claim3": {"level": L3, "rows": r3, "holm": {"|".join(k): v for k, v in c3.items()}},
           "units": {"|".join(k): v for k, v in U.items()}, "lineage": lin}
    json.dump(out, open(os.path.join(HERE, "RESULTS_CONF3.json"), "w"), indent=1, default=float)
    def f(v, row, adj=None, tok=False):
        if not v: return "–"
        hp = f", Holm p={adj:.1e}" if adj is not None else f", p={v['p_one_sided']:.1e}"
        if KIND[row] == "res" and not tok: return f"{v['result_gain_pct']:+.2f} % ({v['wins']}/{v['cells']}){hp}"
        return f"{v['resource_saved_pct']:+.1f} % tokens, result {v['mean_result_gain']:+.3f} ({v['cells']} cells){hp}"
    L = ["# RESULTS CONF3 (sealed; analyze_conf3.py exactly as PREREG_CONF3.md; CONF3 outputs only)", "",
         f"- **Claim 1, cross-domain seed: {L1}** ({n1} of 5 rows at Holm p < 1e-5)",
         f"- **Claim 2, communication principle: {L2}** ({n2} of 3 rows at Holm p < 1e-7, equal or better result)",
         f"- **Claim 3, the RSOS language composes winning moves (composed arm): {L3}** ({n3} of 4 rows at Holm p < 1e-5)", "",
         "| Row | Standard | Full seed vs standard (claim 1) | Tokens (claim 2) | Composed vs standard (claim 3) | Full seed vs strongest | Composed vs full seed |",
         "|---|---|---|---|---|---|---|"]
    for k, u in sorted(U.items()):
        row = k[0]
        L.append(f"| {row} | {k[1]} | {f(u['full'], row, c1.get(k))} | {f(u['full'], row, c2.get(k), tok=True) if k in c2 else '–'} | "
                 f"{f(u['gen'], row, c3.get(k))} | {f(u['strong'], row)} | {f(u['gen_vs_full'], row)} |")
    L += ["", "## Lineage: every move chosen -> RSOS operator", "", "| Row / arm / move | Uses | Kind | Operator |", "|---|---|---|---|"]
    L += [f"| {k} | {v['uses']} | {'lever' if v['lever'] else 'native'} | {v['operator'] or ('UNTRACED' if v['lever'] else 'no mapping')} |"
          for k, v in sorted(lin.items())]
    open(os.path.join(HERE, "RESULTS_CONF3.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L[:16]))

if __name__ == "__main__":
    main()
