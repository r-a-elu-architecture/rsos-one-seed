import json, numpy as np
from scipy.stats import binomtest, spearmanr
R = {}; raw = {}
for f in ["RAW_HOLO6_1_2_3_4.json", "RAW_HOLO6_5.json"]: raw.update(json.load(open(f)))
D = sorted(int(k) for k in raw)
def sp(x): w = int(np.sum(np.array(x) > 0)); return {"wins": w, "of": len(x), "p": float(binomtest(w, len(x), 0.5, alternative="greater").pvalue)}
adv = {d: np.array([r["live"] - r["best_baseline"] for r in raw[str(d)]]) for d in D}
for d in D:
    rr = raw[str(d)]
    R[f"d{d}"] = {"adv_live": float(adv[d].mean()), "adv_unhealed": float(np.mean([r["unhealed"] - r["best_baseline"] for r in rr])),
                  "adv_holo4": float(np.mean([r["holo4"] - r["best_baseline"] for r in rr])), "wins_vs_best_baseline": int(np.sum(adv[d] > 0)),
                  "letters": int(sum(r["letters"] for r in rr)), "landed": int(sum(r["landed"] for r in rr)), "futures": int(sum(r["futures"] for r in rr))}
R["W1_live_beats_best_baseline_d5"] = sp(adv[5])
rho, p = spearmanr([d for d in D for _ in adv[d]], [v for d in D for v in adv[d]]); R["W2_advantage_grows_with_density"] = {"rho": float(rho), "p": float(p)}
R["W3_coupled_beats_uncoupled_d5"] = sp([r["live"] - r["live_uncoupled"] for r in raw["5"]])
R["W4_live_beats_unhealed_all"] = sp([r["live"] - r["unhealed"] for d in D for r in raw[str(d)]])
R["W5_live_beats_holo4_all"] = sp([r["live"] - r["holo4"] for d in D for r in raw[str(d)]])
R["landed_share_of_letters"] = sum(R[f"d{d}"]["landed"] for d in D) / sum(R[f"d{d}"]["letters"] for d in D)
json.dump(R, open("RESULTS_HOLO6.json", "w"), indent=1); print(json.dumps(R, indent=1))
