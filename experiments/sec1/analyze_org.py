import json, numpy as np
from scipy.stats import binomtest, spearmanr
rows = json.load(open("RAW_SEC1v2_org_1_2_3.json")) + json.load(open("RAW_SEC1v2_org_4_5.json"))
def sp(x):
    x = np.asarray(x); w = int((x > 0).sum()); t = int((x != 0).sum())
    return {"wins": w, "nonzero": t, "of": len(x), "mean": float(x.mean()), "p": float(binomtest(w, t, 0.5, alternative="greater").pvalue) if t else 1.0}
g = lambda a, b: [r[a] - r[b] for r in rows]
R = {"P0_org_vs_unhealed": sp(g("organism", "unhealed")), "P1_spread_on_vs_off": sp(g("spread_on", "spread_off")),
     "P2_org_vs_global": sp(g("organism", "global")), "P5_org_vs_best_native": sp(g("organism", "best_native")),
     "P7_org_vs_apart": sp(g("organism", "apart"))}
rho, p = spearmanr([r["d"] for r in rows], g("organism", "unhealed")); R["P3_spearman_d_gain"] = {"rho": float(rho), "p_one_sided": float(p / 2 if rho > 0 else 1 - p / 2)}
ps = sorted([(v["p"] if "p" in v else v["p_one_sided"], k) for k, v in R.items()]); m = len(ps)
R["holm"] = {k: min(1.0, max((m - j) * pp for j, (pp, _) in enumerate(ps[:i + 1]))) for i, (_, k) in enumerate(ps)}
R["transpersonal_mean"] = float(np.mean([r["transpersonal"] for r in rows]))
R["by_density"] = {d: {k: float(np.mean([r[k] for r in rows if r["d"] == d])) for k in ["organism", "apart", "global", "unhealed", "best_native", "spread_on", "spread_off"]} for d in range(1, 6)}
json.dump(R, open("RESULTS_SEC1v2_ORG.json", "w"), indent=1); print(json.dumps(R, indent=1))
