"""ORG-REAL1 analysis exactly as PREREG_REAL1.md."""
import json, glob, numpy as np
from scipy.stats import binomtest
from real6 import BASE
def sp(x):
    x = np.asarray(x, float); w = int((x > 0).sum()); t = int((x != 0).sum())
    return {"wins": w, "nonzero": t, "of": len(x), "mean": float(x.mean()), "p": float(binomtest(w, t, 0.5, alternative="greater").pvalue) if t else 1.0}
R = sum([json.load(open(f)) for f in sorted(glob.glob("RAW6_eval_p*.json"))], [])
c = sp([r["own"] - r["rnd_own"] for r in R]); t = sp([r["tr"] - r["rnd_tr"] for r in R]); p = sp([r["tr"] - r["best_baseline"] for r in R])
out = {"control": c, "transfer": t, "primary": p,
       "passes": {"control": c["p"] < 0.05, "transfer": c["p"] < 0.05 and t["p"] < 0.05, "primary": c["p"] < 0.05 and t["p"] < 0.05 and p["p"] < 0.05},
       "tr_vs_each": {b: sp([r["tr"] - r[b] for r in R]) for b in BASE},
       "iris_only": sp([r["tr"] - r["best_baseline"] for r in R if r["data"] == "iris"]),
       "by_noise": {n: sp([r["tr"] - r["best_baseline"] for r in R if r["noise"] == n]) for n in ("sym25", "asym30")},
       "by_data": {d: sp([r["tr"] - r["best_baseline"] for r in R if r["data"] == d]) for d in ("cancer", "wine", "digits", "iris")},
       "own_vs_best": sp([r["own"] - r["best_baseline"] for r in R]),
       "mean_acc": {k: float(np.mean([r[k] for r in R])) for k in ["tr", "own", "best_baseline"] + BASE},
       "structs": sorted({(r["host"], r["own_struct"], r["tr_struct"]) for r in R})}
json.dump(out, open("RESULTS_REAL1.json", "w"), indent=1); print(json.dumps(out, indent=1, default=str))
