"""SEC1 v4 real-data host, HARD version, with U167 (turquoise at places of need).
Data: cancer, wine, digits (scikit-learn). Made hard on the TRAINING split only: 25 % of training labels flipped to
another class (label noise) and, for every second class, 70 % of its training examples removed (imbalance).
Validation (from the clean split, before noise) and test stay clean. Disclosed: the beam reads the whole on a small
clean validation set.
Learner and budget as sec1_real.py (SGD log loss, 300 steps of 16, 4 places per step).
Policies:
  plain, decay, ohem, global : as v2 (on the hard data)
  inside : v3 exact landing (fading-memory lack, strict whole, horizon) - landing always inside
  sparse : U167. Core = the plain step. At each step the beam reads five placements for the 4 places, each forked
           10 steps ahead on common batches: core (no landing), inside (the 4 loudest by lack into the batch),
           above (the 4 loudest IN the batch are read and taken out, replaced by random others: no push on them),
           outside (the 4 nearest same-label neighbours of the loudest: the boundary around them),
           tube (4 examples of the class weakest on validation: sharing to the weak sphere).
           Lands the best by validation log-loss with no class accuracy worse; otherwise the core.
P0 sparse > plain; P2 sparse > global; P5 sparse > best native (plain, decay, ohem); P9 sparse > inside.
Fresh seeds 7700-7711 x 3 datasets (36 runs). Usage: python sec1_real_v4.py run"""
import sys, json, copy, hashlib
import numpy as np
import sec1_real as R, sec1_real_v3 as V3
for f in ("sec1_real.py", "sec1_real_v3.py"):
    assert hashlib.sha256(open(f, "rb").read()).hexdigest() in open("SEAL_SEC1.txt").read(), f
SEEDS, HZ = list(range(7700, 7712)), 10

def hard(name, seed):
    Xtr, ytr, Xva, yva, Xte, yte, classes = R.setup(name, seed)
    r = np.random.default_rng(seed + 50); keep = np.ones(len(ytr), bool)
    for c in classes[1::2]:
        idx = np.where(ytr == c)[0]; keep[r.choice(idx, int(0.7 * len(idx)), replace=False)] = False
    Xtr, ytr = Xtr[keep], ytr[keep].copy()
    flip = r.random(len(ytr)) < 0.25
    for i in np.where(flip)[0]: ytr[i] = r.choice(classes[classes != ytr[i]])
    return Xtr, ytr, Xva, yva, Xte, yte, classes

def new(classes, seed, Xtr, ytr, eta=R.LR):
    clf = R.SGDClassifier(loss="log_loss", learning_rate="constant", eta0=eta, random_state=seed)
    m = len(classes); idx = np.concatenate([np.where(ytr == c)[0][:2] for c in classes]); clf.partial_fit(Xtr[idx], ytr[idx], classes=classes)
    return clf

def run(name, seed, policy):
    Xtr, ytr, Xva, yva, Xte, yte, classes = hard(name, seed)
    rng = np.random.default_rng(seed); clf = new(classes, seed, Xtr, ytr)
    batches = [rng.choice(len(Xtr), R.B, replace=False) for _ in range(R.STEPS + HZ)]
    mem = np.zeros(len(Xtr)); used = {"core": 0, "inside": 0, "above": 0, "outside": 0, "tube": 0}
    for t in range(R.STEPS):
        idx = batches[t]
        if policy in ("plain", "decay", "global", "ohem"):
            if policy == "decay": clf.eta0 = R.LR / (1 + t / 100)
            if policy == "global": clf.eta0 = R.LR * (R.B + R.K) / R.B
            if policy == "ohem":
                l = R.loss(clf, Xtr[idx], ytr[idx], classes); idx = np.concatenate([idx, idx[np.argsort(-l)[:R.K]]])
            clf.partial_fit(Xtr[idx], ytr[idx]); continue
        lack = R.loss(clf, Xtr, ytr, classes) * (1 + mem); loud = np.argsort(-lack)[:R.K]
        opts = {"core": idx, "inside": np.concatenate([idx[:R.B - R.K], loud])}
        if policy == "sparse":
            lb = R.loss(clf, Xtr[idx], ytr[idx], classes); keep = idx[np.argsort(lb)[:R.B - R.K]]
            opts["above"] = np.concatenate([keep, rng.choice(len(Xtr), R.K, replace=False)])
            nbrs = []
            for i in loud:
                same = np.where(ytr == ytr[i])[0]; dd = np.linalg.norm(Xtr[same] - Xtr[i], axis=1); dd[same == i] = np.inf
                nbrs.append(same[np.argmin(dd)])
            opts["outside"] = np.concatenate([idx[:R.B - R.K], np.array(nbrs)])
            pc = R.per_class(clf, Xva, yva, classes); wc = classes[np.argmin(pc)]; pool = np.where(ytr == wc)[0]
            opts["tube"] = np.concatenate([idx[:R.B - R.K], rng.choice(pool, R.K, replace=len(pool) < R.K)])
        res = {}
        for k, b in opts.items():
            f = copy.deepcopy(clf); f.partial_fit(Xtr[b], ytr[b]); ff = copy.deepcopy(f)
            for bb in batches[t + 1:t + 1 + HZ]: ff.partial_fit(Xtr[bb], ytr[bb])
            res[k] = (f, R.loss(ff, Xva, yva, classes).mean(), R.per_class(ff, Xva, yva, classes))
        best = "core"
        for k in opts:
            if k != "core" and res[k][1] < res[best][1] and np.all(res[k][2] >= res["core"][2] - 1e-12): best = k
        clf = res[best][0]; used[best] += 1
        mem = 0.9 * mem + (clf.predict(Xtr) != ytr)
    return float(np.mean(clf.predict(Xte) == yte)), used

if __name__ == "__main__" and sys.argv[1] == "run":
    from scipy.stats import binomtest
    def sp(x): x = np.asarray(x); w = int((x > 0).sum()); t = int((x != 0).sum()); return {"wins": w, "nonzero": t, "of": len(x), "mean": float(x.mean()), "p": float(binomtest(w, t, 0.5, alternative="greater").pvalue) if t else 1.0}
    rows = []
    for name in R.DATA:
        for s in SEEDS:
            r = {p: run(name, s, p)[0] for p in ["plain", "decay", "ohem", "global", "inside"]}
            r["sparse"], r["used"] = run(name, s, "sparse"); r["best_native"] = max(r["plain"], r["decay"], r["ohem"])
            rows.append({"data": name, "seed": s, **r}); print(name, s, round(r["sparse"] - r["best_native"], 4), r["used"], flush=True)
    out = {"code_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(),
           "P0": sp([r["sparse"] - r["plain"] for r in rows]), "P2": sp([r["sparse"] - r["global"] for r in rows]),
           "P5": sp([r["sparse"] - r["best_native"] for r in rows]), "P9": sp([r["sparse"] - r["inside"] for r in rows]),
           "means": {k: {n: float(np.mean([r[k] for r in rows if r["data"] == n])) for n in R.DATA} for k in ["sparse", "inside", "plain", "global", "best_native"]}}
    json.dump(rows, open("RAW_SEC1v4_real.json", "w")); json.dump(out, open("RESULTS_SEC1v4_real.json", "w"), indent=1)
    print(json.dumps(out, indent=1))
