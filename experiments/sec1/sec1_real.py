"""SEC1 v2 build 2: real-data host (T5 data: breast cancer, wine, digits from scikit-learn), under TOP_MAP_SEC1_v2.md.
A learner (SGD, log loss) trains in steps of 16 examples. Budget: 4 landings per step (4 of the 16 batch places).
  unhealed : plain SGD, random batch
  exact    : the White Dragon: the 4 places go to the examples with the greatest lack (highest current loss, read from
             memory of past errors); the step is forked (copy of the model) and kept only if the whole (validation
             accuracy) is not worse and no class's accuracy drops (turquoise gate); otherwise the plain step is taken
  global   : the same budget spread over the whole batch (learning rate x 1.25 = 20/16)
  natives  : plain SGD; SGD with decaying rate; online hard-example mining (top-loss 4 inside the batch)
P0 exact > unhealed; P2 exact > global; P5 exact > best native (test accuracy at the end). P1, P3, P4, P7 not measurable.
Usage: python sec1_real.py run"""
import sys, json, copy, hashlib, warnings
import numpy as np
from sklearn.datasets import load_breast_cancer, load_digits, load_wine
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
warnings.filterwarnings("ignore")
DATA = {"cancer": load_breast_cancer, "wine": load_wine, "digits": load_digits}
STEPS, B, K, LR = 300, 16, 4, 0.05
SEEDS = list(range(7300, 7316))

def setup(name, seed):
    X, y = DATA[name](return_X_y=True)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, stratify=y, random_state=seed)
    Xtr, Xva, ytr, yva = train_test_split(Xtr, ytr, test_size=0.2, stratify=ytr, random_state=seed)
    sc = StandardScaler().fit(Xtr)
    return sc.transform(Xtr), ytr, sc.transform(Xva), yva, sc.transform(Xte), yte, np.unique(y)

def loss(clf, X, y, classes):
    p = clf.predict_proba(X); idx = np.searchsorted(classes, y)
    return -np.log(np.clip(p[np.arange(len(y)), idx], 1e-9, 1))

def per_class(clf, X, y, classes):
    pr = clf.predict(X); return np.array([np.mean(pr[y == c] == c) if np.any(y == c) else 1.0 for c in classes])

def run(name, seed, policy):
    Xtr, ytr, Xva, yva, Xte, yte, classes = setup(name, seed)
    rng = np.random.default_rng(seed)
    clf = SGDClassifier(loss="log_loss", learning_rate="constant", eta0=LR, random_state=seed)
    clf.partial_fit(Xtr[:2 * len(classes)], ytr[:2 * len(classes)], classes=classes)     # identical warm start
    memory = np.zeros(len(Xtr))                                                         # past errors per example
    for t in range(STEPS):
        idx = rng.choice(len(Xtr), B, replace=False)
        if policy == "decay": clf.eta0 = LR / (1 + t / 100)
        if policy == "global": clf.eta0 = LR * (B + K) / B
        if policy == "ohem":
            l = loss(clf, Xtr[idx], ytr[idx], classes); idx = np.concatenate([idx, idx[np.argsort(-l)[:K]]])
        if policy == "exact":
            l_all = loss(clf, Xtr, ytr, classes) * (1 + memory)
            land = np.argsort(-l_all)[:K]
            idx_l = np.concatenate([idx[:B - K], land])
            f = copy.deepcopy(clf); f.partial_fit(Xtr[idx_l], ytr[idx_l])
            g = copy.deepcopy(clf); g.partial_fit(Xtr[idx], ytr[idx])
            a_f, a_g = np.mean(f.predict(Xva) == yva), np.mean(g.predict(Xva) == yva)
            if a_f >= a_g and np.all(per_class(f, Xva, yva, classes) >= per_class(g, Xva, yva, classes) - 1e-12):
                clf = f
            else:
                clf = g
            memory += (clf.predict(Xtr) != ytr)
            continue
        clf.partial_fit(Xtr[idx], ytr[idx])
    return float(np.mean(clf.predict(Xte) == yte))

if __name__ == "__main__" and sys.argv[1] == "run":
    from scipy.stats import binomtest
    def sp(x): x = np.asarray(x); w = int(np.sum(x > 0)); t = int(np.sum(x != 0)); return {"wins": w, "nonzero": t, "of": len(x), "p": float(binomtest(w, max(t, 1), 0.5, alternative="greater").pvalue) if t else 1.0}
    rows = []
    for name in DATA:
        for s in SEEDS:
            r = {p: run(name, s, p) for p in ["exact", "plain", "global", "decay", "ohem"]}
            r["best_native"] = max(r["plain"], r["decay"], r["ohem"]); rows.append({"data": name, "seed": s, **r})
        print(name, flush=True)
    R = {"code_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(),
         "P0_exact_beats_unhealed": sp([r["exact"] - r["plain"] for r in rows]),
         "P2_exact_beats_global": sp([r["exact"] - r["global"] for r in rows]),
         "P5_exact_beats_best_native": sp([r["exact"] - r["best_native"] for r in rows]),
         "means": {k: {n: float(np.mean([r[k] for r in rows if r["data"] == n])) for n in DATA} for k in ["exact", "plain", "global", "decay", "ohem", "best_native"]}}
    json.dump(rows, open("RAW_SEC1v2_real.json", "w")); json.dump(R, open("RESULTS_SEC1v2_real.json", "w"), indent=1)
    print(json.dumps(R, indent=1))
