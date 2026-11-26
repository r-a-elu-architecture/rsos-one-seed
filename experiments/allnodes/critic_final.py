"""ORG-FINAL critic package (reported separately; does NOT decide colours). Real data, same eval seeds and batches as
orgfinal.py real(): standard noisy-label baselines that know the true noise rate (generous to them):
  smallloss       keep the 75 % lowest-loss examples of each batch (small-loss trick, noise rate 25 % known)
  smallloss_decay the same with the decaying rate 1/(1+t/100)
Compared with the transferred structure 'tr' from RAWF_real.json: tr > max(smallloss, smallloss_decay), sign test."""
import json, numpy as np, real_v5 as Z
from scipy.stats import binomtest
R, V4 = Z.R, Z.V4
def run(name, seed, decay):
    Xtr, ytr, Xva, yva, Xte, yte, classes = V4.hard(name, seed)
    rng = np.random.default_rng(seed); clf = V4.new(classes, seed, Xtr, ytr)
    batches = [rng.choice(len(Xtr), R.B, replace=False) for _ in range(R.STEPS + 10)]
    for t in range(R.STEPS):
        clf.eta0 = R.LR / (1 + t / 100) if decay else R.LR
        b = batches[t]; l = R.loss(clf, Xtr[b], ytr[b], classes); b = b[np.argsort(l)[:int(0.75 * len(b))]]
        clf.partial_fit(Xtr[b], ytr[b])
    return float(np.mean(clf.predict(Xte) == yte))
if __name__ == "__main__":
    rows = json.load(open("RAWF_real.json"))["rows"]; out = []
    for r in rows:
        a, b = run(r["data"], r["seed"], False), run(r["data"], r["seed"], True)
        out.append({"data": r["data"], "seed": r["seed"], "tr": r["tr"], "own": r["own"], "smallloss": a, "smallloss_decay": b}); print(out[-1], flush=True)
    d = [x["tr"] - max(x["smallloss"], x["smallloss_decay"]) for x in out]; w = sum(v > 0 for v in d); n = sum(v != 0 for v in d)
    res = {"rows": out, "tr_vs_best_noisy_baseline": {"wins": w, "nonzero": n, "of": len(d), "mean": float(np.mean(d)),
           "p": float(binomtest(w, n, 0.5, alternative="greater").pvalue) if n else 1.0}}
    json.dump(res, open("RESULTS_FINAL_CRITIC.json", "w"), indent=1); print(res["tr_vs_best_noisy_baseline"])
