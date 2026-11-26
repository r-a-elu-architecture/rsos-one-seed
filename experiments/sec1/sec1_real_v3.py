"""SEC1 v3 real-data host: correction of the three v2 build defects. Imports the sealed sec1_real.py (hash-checked)
for data, natives and global; changes only the exact landing:
  1. lack = current loss x (1 + fading memory of errors) (memory x 0.9 per step, + current error): the letter is the
     one that lacks now, not the one that was always loud;
  2. strict whole: read on validation log-loss (continuous, no ties) plus per-class accuracy not worse; when not
     strictly better, the plain step is taken;
  3. the fork runs a horizon of 20 further plain steps on the SAME future batches for both branches before reading
     the whole (futures, not one step).
Fresh seeds 7500-7515 x cancer/wine/digits. Usage: python sec1_real_v3.py run"""
import sys, json, copy, hashlib
import numpy as np
import sec1_real as R
assert hashlib.sha256(open("sec1_real.py", "rb").read()).hexdigest() in open("SEAL_SEC1.txt").read()
SEEDS, HZ = list(range(7500, 7516)), 20

def run_exact3(name, seed):
    Xtr, ytr, Xva, yva, Xte, yte, classes = R.setup(name, seed)
    rng = np.random.default_rng(seed)
    clf = R.SGDClassifier(loss="log_loss", learning_rate="constant", eta0=R.LR, random_state=seed)
    clf.partial_fit(Xtr[:2 * len(classes)], ytr[:2 * len(classes)], classes=classes)
    mem = np.zeros(len(Xtr)); batches = [rng.choice(len(Xtr), R.B, replace=False) for _ in range(R.STEPS + HZ)]
    landed = 0
    for t in range(R.STEPS):
        idx = batches[t]
        land = np.argsort(-(R.loss(clf, Xtr, ytr, classes) * (1 + mem)))[:R.K]
        f = copy.deepcopy(clf); f.partial_fit(Xtr[np.concatenate([idx[:R.B - R.K], land])], ytr[np.concatenate([idx[:R.B - R.K], land])])
        g = copy.deepcopy(clf); g.partial_fit(Xtr[idx], ytr[idx])
        ff, gg = copy.deepcopy(f), copy.deepcopy(g)
        for b in batches[t + 1:t + 1 + HZ]: ff.partial_fit(Xtr[b], ytr[b]); gg.partial_fit(Xtr[b], ytr[b])
        lf, lg = R.loss(ff, Xva, yva, classes).mean(), R.loss(gg, Xva, yva, classes).mean()
        if lf < lg and np.all(R.per_class(ff, Xva, yva, classes) >= R.per_class(gg, Xva, yva, classes) - 1e-12): clf = f; landed += 1
        else: clf = g
        mem = 0.9 * mem + (clf.predict(Xtr) != ytr)
    return float(np.mean(clf.predict(Xte) == yte)), landed

if __name__ == "__main__" and sys.argv[1] == "run":
    from scipy.stats import binomtest
    def sp(x): x = np.asarray(x); w = int((x > 0).sum()); t = int((x != 0).sum()); return {"wins": w, "nonzero": t, "of": len(x), "mean": float(x.mean()), "p": float(binomtest(w, t, 0.5, alternative="greater").pvalue) if t else 1.0}
    rows = []
    for name in R.DATA:
        for s in SEEDS:
            ex, nl = run_exact3(name, s)
            r = {"exact": ex, "landed": nl, **{p: R.run(name, s, p) for p in ["plain", "global", "decay", "ohem"]}}
            r["best_native"] = max(r["plain"], r["decay"], r["ohem"]); rows.append({"data": name, "seed": s, **r})
        print(name, flush=True)
    out = {"code_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(),
           "P0": sp([r["exact"] - r["plain"] for r in rows]), "P2": sp([r["exact"] - r["global"] for r in rows]),
           "P5": sp([r["exact"] - r["best_native"] for r in rows]),
           "means": {k: {n: float(np.mean([r[k] for r in rows if r["data"] == n])) for n in R.DATA} for k in ["exact", "plain", "global", "best_native", "landed"]}}
    json.dump(rows, open("RAW_SEC1v3_real.json", "w")); json.dump(out, open("RESULTS_SEC1v3_real.json", "w"), indent=1)
    print(json.dumps(out, indent=1))
