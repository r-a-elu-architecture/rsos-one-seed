"""ORG-REAL2 analysis exactly as PREREG_REAL2.md."""
import json, glob, numpy as np
from scipy.stats import binomtest
from real7 import BASE
def sp(x):
    x = np.asarray(x, float); w = int((x > 0).sum()); t = int((x != 0).sum())
    return {"wins": w, "nonzero": t, "of": len(x), "mean": float(x.mean()), "p": float(binomtest(w, t, 0.5, alternative="greater").pvalue) if t else 1.0}
def holm(ps):
    o = sorted(range(len(ps)), key=lambda i: ps[i]); out = [0] * len(ps); run = 0
    for j, i in enumerate(o): run = max(run, min(1, (len(ps) - j) * ps[i])); out[i] = run
    return out
R = sum([json.load(open(f)) for f in sorted(glob.glob("RAW7_eval_p*.json"))], [])
c = sp([r["own"] - r["rnd_own"] for r in R]); t = sp([r["tr"] - r["rnd_tr"] for r in R])
each = {b: sp([r["tr"] - r[b] for r in R]) for b in BASE}; h = holm([each[b]["p"] for b in BASE])
for b, x in zip(BASE, h): each[b]["holm"] = x
prim = all(each[b]["holm"] < 0.05 for b in BASE)
out = {"control": c, "transfer": t, "tr_vs_each": each,
       "passes": {"control": c["p"] < 0.05, "transfer": c["p"] < 0.05 and t["p"] < 0.05, "primary": c["p"] < 0.05 and t["p"] < 0.05 and prim},
       "tr_vs_best_of_9": sp([r["tr"] - r["best_baseline"] for r in R]),
       "by_data": {d: sp([r["tr"] - r["best_baseline"] for r in R if r["data"] == d]) for d in ("cancer", "wine", "digits", "iris")},
       "iris_vs_each": {b: sp([r["tr"] - r[b] for r in R if r["data"] == "iris"]) for b in BASE},
       "by_noise": {n: sp([r["tr"] - r["best_baseline"] for r in R if r["noise"] == n]) for n in ("sym25", "asym30")},
       "mean_acc": {k: float(np.mean([r[k] for r in R])) for k in ["tr", "own", "best_baseline"] + BASE},
       "structs": sorted({(r["host"], r["own_struct"], r["tr_struct"]) for r in R})}
json.dump(out, open("RESULTS_REAL2.json", "w"), indent=1); print(json.dumps(out, indent=1, default=str))
