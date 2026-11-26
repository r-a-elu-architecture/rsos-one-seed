import json, numpy as np
from scipy.stats import binomtest, spearmanr
def sp(x):
    x = np.asarray(x); w = int((x > 0).sum()); t = int((x != 0).sum())
    return {"wins": w, "nonzero": t, "of": len(x), "mean": float(x.mean()), "p": float(binomtest(w, t, 0.5, alternative="greater").pvalue) if t else 1.0}
def holm(R):
    ps = sorted((v["p"], k) for k, v in R.items()); m = len(ps); out = {}; run = 0
    for i, (p, k) in enumerate(ps): run = max(run, min(1, (m - i) * p)); out[k] = run
    return out
rows = sum([json.load(open(f"RAW_SEC1v4_org_{d}.json")) for d in (1, 3, 5)], [])
g = lambda a, b: [r[a] - r[b] for r in rows]
O = {"P0": sp(g("sparse", "unhealed")), "P5": sp(g("sparse", "best_native")), "P8": sp(g("sparse", "all")), "P9": sp(g("sparse", "inside"))}
rho, p = spearmanr([r["d"] for r in rows], g("sparse", "all")); O["P3p"] = {"rho": float(rho), "p": float(p / 2 if rho > 0 else 1 - p / 2)}
O["holm"] = holm(O)
O["flows"] = {"sparse": float(np.mean([r["flows_sparse"] for r in rows])), "all": float(np.mean([r["flows_all"] for r in rows]))}
O["modes"] = {m: int(sum(r["modes"][m] for r in rows)) for m in rows[0]["modes"]}
O["by_density"] = {d: {k: float(np.mean([r[k] for r in rows if r["d"] == d])) for k in ["sparse", "all", "inside", "unhealed", "best_native"]} for d in (1, 3, 5)}
real = json.load(open("RAW_SEC1v4_real.json")); h = lambda a, b: [r[a] - r[b] for r in real]
Rr = {"P0": sp(h("sparse", "plain")), "P2": sp(h("sparse", "global")), "P5": sp(h("sparse", "best_native")), "P9": sp(h("sparse", "inside"))}
Rr["holm"] = holm({k: v for k, v in Rr.items()})
Rr["P5_by_data"] = {n: sp([r["sparse"] - r["best_native"] for r in real if r["data"] == n]) for n in ("cancer", "wine", "digits")}
Rr["which_native_best"] = {n: {k: int(sum(1 for r in real if r["data"] == n and r[k] == r["best_native"])) for k in ("plain", "decay", "ohem")} for n in ("cancer", "wine", "digits")}
Rr["placements"] = {k: int(sum(r["used"][k] for r in real)) for k in real[0]["used"]}
json.dump({"organism": O, "real": Rr}, open("RESULTS_SEC1v4.json", "w"), indent=1); print(json.dumps({"organism": O, "real": Rr}, indent=1))
