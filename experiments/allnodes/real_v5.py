"""ORG1 real-data host, layer 1 (hard data of sec1_real_v4, hash-checked) with U150 SYSTEM THAT SEES ITSELF: the
"above" placement turned on the learner's own regulation. At each step the beam reads the v4 placements (core,
inside, above, outside, tube) and also the core step at half and at double the rate; each forked 10 steps ahead on
common batches; lands the best by validation log-loss with no class worse, else the core. The rate change applies to
that step only (regulation only where needed). Natives: plain, decaying rate, hard-example mining; global.
Fresh seeds 7900-7907 x cancer/wine/digits (24 runs). P5r: reg > best native; P0r: reg > plain; P9r: reg > v4 sparse."""
import sys, os, json, copy, hashlib
import numpy as np
os.chdir(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, "../sec1")
for f in ("sec1_real.py", "sec1_real_v3.py", "sec1_real_v4.py"):
    assert hashlib.sha256(open("../sec1/" + f, "rb").read()).hexdigest() in open("../sec1/SEAL_SEC1.txt").read(), f
cwd = os.getcwd(); os.chdir("../sec1"); import sec1_real as R, sec1_real_v4 as V4; os.chdir(cwd)
SEEDS, HZ = list(range(7900, 7908)), 10

def run_reg(name, seed):
    Xtr, ytr, Xva, yva, Xte, yte, classes = V4.hard(name, seed)
    rng = np.random.default_rng(seed); clf = V4.new(classes, seed, Xtr, ytr)
    batches = [rng.choice(len(Xtr), R.B, replace=False) for _ in range(R.STEPS + HZ)]
    mem = np.zeros(len(Xtr)); used = {}
    for t in range(R.STEPS):
        idx = batches[t]
        lack = R.loss(clf, Xtr, ytr, classes) * (1 + mem); loud = np.argsort(-lack)[:R.K]
        lb = R.loss(clf, Xtr[idx], ytr[idx], classes); keep = idx[np.argsort(lb)[:R.B - R.K]]
        nbrs = []
        for i in loud:
            same = np.where(ytr == ytr[i])[0]; dd = np.linalg.norm(Xtr[same] - Xtr[i], axis=1); dd[same == i] = np.inf; nbrs.append(same[np.argmin(dd)])
        pc = R.per_class(clf, Xva, yva, classes); pool = np.where(ytr == classes[np.argmin(pc)])[0]
        opts = {"core": (idx, 1.0), "inside": (np.concatenate([idx[:R.B - R.K], loud]), 1.0),
                "above": (np.concatenate([keep, rng.choice(len(Xtr), R.K, replace=False)]), 1.0),
                "outside": (np.concatenate([idx[:R.B - R.K], np.array(nbrs)]), 1.0),
                "tube": (np.concatenate([idx[:R.B - R.K], rng.choice(pool, R.K, replace=len(pool) < R.K)]), 1.0),
                "reg_half": (idx, 0.5), "reg_double": (idx, 2.0)}
        res = {}
        for k, (b, sc) in opts.items():
            f = copy.deepcopy(clf); f.eta0 = R.LR * sc; f.partial_fit(Xtr[b], ytr[b]); f.eta0 = R.LR; ff = copy.deepcopy(f)
            for bb in batches[t + 1:t + 1 + HZ]: ff.partial_fit(Xtr[bb], ytr[bb])
            res[k] = (f, R.loss(ff, Xva, yva, classes).mean(), R.per_class(ff, Xva, yva, classes))
        best = "core"
        for k in opts:
            if k != "core" and res[k][1] < res[best][1] and np.all(res[k][2] >= res["core"][2] - 1e-12): best = k
        clf = res[best][0]; used[best] = used.get(best, 0) + 1
        mem = 0.9 * mem + (clf.predict(Xtr) != ytr)
    return float(np.mean(clf.predict(Xte) == yte)), used

if __name__ == "__main__":
    rows = []
    for name in R.DATA:
        for s in SEEDS:
            reg, used = run_reg(name, s); r = {p: V4.run(name, s, p)[0] for p in ["plain", "decay", "ohem", "global"]}
            r["sparse_v4"] = V4.run(name, s, "sparse")[0]
            rows.append({"data": name, "seed": s, "reg": reg, "used": used, **r, "best_native": max(r["plain"], r["decay"], r["ohem"])})
            print(name, s, round(reg - rows[-1]["best_native"], 4), used, flush=True)
    json.dump(rows, open("RAW_real_v5.json", "w"))
