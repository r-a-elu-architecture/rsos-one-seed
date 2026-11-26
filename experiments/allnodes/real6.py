"""ORG-REAL1: the family structure on real data against the field's noisy-label methods (owner "1", 22 Nov 2026 07:27).
Layer 1 data (scikit-learn, offline): breast cancer, wine, digits, iris (iris never used before in this project).
Each dataset made hard on the training split only (as sec1_real_v4.hard): every second class reduced by 70 %, then
label noise of one of two kinds: sym25 (25 % flipped to a random other class) or asym30 (30 % flipped to the next
class). 4 datasets x 2 noise kinds = 8 hosts. Validation and test stay clean. Learner and budget as before (SGD log
loss, 300 steps of 16).
Structures: the 5 roles of ORG5 real data (barrier, detect, adapt, memory, reg), 32 structures, code as org5.real_st.
Arms per host x seed:
  own    best structure on this host's selection seeds
  tr     best structure (mean) on the hosts of the OTHER datasets (both noise kinds of the same dataset excluded)
  rnd_own, rnd_tr  random structure of the same size as own / tr
  baselines (9): plain, decay, ohem; smallloss and smallloss+decay (keep the (1-r) lowest-loss of each batch, r = the
  TRUE noise rate); co-teaching and co-teaching+decay (two models, each trains on the other's small-loss part, forget
  rate ramps to the true r over the first 30 steps; the better of the two on validation is reported); confident
  learning (out-of-fold logistic-regression probabilities, per-class thresholds, examples whose confident class differs
  from their label are removed) + plain and + decay. The noisy-label methods are given the true noise rate.
Seeds: selection 11000-11001, evaluation 11100-11107, random structures 11200+.
Usage: python real6.py select <part> ; python real6.py eval <part>"""
import sys, os, json, hashlib, itertools, glob, warnings
import numpy as np
os.chdir(os.path.dirname(os.path.abspath(__file__)))
assert hashlib.sha256(open("real_v5.py", "rb").read()).hexdigest() in open("SEAL_ORG1.txt").read()
import real_v5 as Z
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_predict
from sklearn.preprocessing import StandardScaler
warnings.filterwarnings("ignore")
R, V4 = Z.R, Z.V4
DATA = dict(R.DATA); DATA["iris"] = load_iris
HOSTS = [(d, n) for d in ("cancer", "wine", "digits", "iris") for n in ("sym25", "asym30")]
RATE = {"sym25": 0.25, "asym30": 0.30}
SEL, EV = [11000, 11001], list(range(11100, 11108))
RROLES = ["barrier", "detect", "adapt", "memory", "reg"]
RSTRUCTS = ["".join(map(str, b)) for b in itertools.product([0, 1], repeat=5)]
BASE = ["plain", "decay", "ohem", "smallloss", "smallloss_decay", "coteach", "coteach_decay", "cl", "cl_decay"]

def hard(name, noise, seed):
    X, y = DATA[name](return_X_y=True)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, stratify=y, random_state=seed)
    Xtr, Xva, ytr, yva = train_test_split(Xtr, ytr, test_size=0.2, stratify=ytr, random_state=seed)
    sc = StandardScaler().fit(Xtr); Xtr, Xva, Xte = sc.transform(Xtr), sc.transform(Xva), sc.transform(Xte)
    classes = np.unique(y); r = np.random.default_rng(seed + 50); keep = np.ones(len(ytr), bool)
    for c in classes[1::2]:
        idx = np.where(ytr == c)[0]; keep[r.choice(idx, int(0.7 * len(idx)), replace=False)] = False
    Xtr, ytr = Xtr[keep], ytr[keep].copy(); flip = r.random(len(ytr)) < RATE[noise]
    for i in np.where(flip)[0]:
        ytr[i] = r.choice(classes[classes != ytr[i]]) if noise == "sym25" else classes[(np.searchsorted(classes, ytr[i]) + 1) % len(classes)]
    return Xtr, ytr, Xva, yva, Xte, yte, classes

def start(host, seed):
    D = hard(*host, seed); rng = np.random.default_rng(seed)
    batches = [rng.choice(len(D[0]), R.B, replace=False) for _ in range(R.STEPS + 10)]
    return D, batches

def acc(clf, D): return float(np.mean(clf.predict(D[4]) == D[5]))

def struct(host, seed, c):
    (Xtr, ytr, Xva, yva, Xte, yte, classes), batches = start(host, seed); st = dict(zip(RROLES, map(int, c)))
    clf = V4.new(classes, seed, Xtr, ytr); r2 = np.random.default_rng(seed + 7); mem = np.zeros(len(Xtr))
    for t in range(R.STEPS):
        clf.eta0 = R.LR / (1 + t / 100) if st["reg"] else R.LR
        bt = batches[t]; sus = mem > 3 if st["barrier"] else np.zeros(len(Xtr), bool)
        if st["barrier"] and (~sus[bt]).sum() >= R.K: bt = bt[~sus[bt]]
        if st["adapt"]:
            lack = R.loss(clf, Xtr, ytr, classes) * ((1 + mem) if st["memory"] else 1); lack[sus] = -1
            bt = np.concatenate([bt[:max(1, len(bt) - R.K)], np.argsort(-lack)[:R.K]])
        if st["detect"]:
            pool = np.where(ytr == classes[np.argmin(R.per_class(clf, Xva, yva, classes))])[0]
            if st["barrier"] and (~sus[pool]).sum() >= 2: pool = pool[~sus[pool]]
            bt = np.concatenate([bt, r2.choice(pool, 2, replace=len(pool) < 2)])
        clf.partial_fit(Xtr[bt], ytr[bt]); mem = 0.9 * mem + (clf.predict(Xtr) != ytr)
    return acc(clf, (Xtr, ytr, Xva, yva, Xte, yte))

def baseline(host, seed, b):
    D, batches = start(host, seed); Xtr, ytr, Xva, yva, Xte, yte, classes = D; r = RATE[host[1]]
    dec = b.endswith("decay"); lr = lambda t: R.LR / (1 + t / 100) if dec else R.LR
    if b.startswith("coteach"):
        m = [V4.new(classes, seed, Xtr, ytr), V4.new(classes, seed + 1, Xtr, ytr)]
        for t in range(R.STEPS):
            bt = batches[t]; keep = int(round(len(bt) * (1 - r * min(1, t / 30))))
            sel = [bt[np.argsort(R.loss(mm, Xtr[bt], ytr[bt], classes))[:keep]] for mm in m]
            for k in (0, 1): m[k].eta0 = lr(t); m[k].partial_fit(Xtr[sel[1 - k]], ytr[sel[1 - k]])
        best = max(m, key=lambda mm: np.mean(mm.predict(Xva) == yva)); return acc(best, D)
    idx_ok = np.arange(len(Xtr))
    if b.startswith("cl"):
        P = cross_val_predict(LogisticRegression(max_iter=2000), Xtr, ytr, cv=5, method="predict_proba")
        li = np.searchsorted(classes, ytr); th = np.array([P[li == j, j].mean() if np.any(li == j) else 1.0 for j in range(len(classes))])
        conf = np.where(P >= th[None, :], P, -1); cj = conf.argmax(1); has = conf.max(1) >= 0
        idx_ok = np.where(~(has & (cj != li)))[0]
    clf = V4.new(classes, seed, Xtr, ytr); rng2 = np.random.default_rng(seed + 3)
    for t in range(R.STEPS):
        clf.eta0 = lr(t); bt = batches[t] if not b.startswith("cl") else rng2.choice(idx_ok, R.B, replace=len(idx_ok) < R.B)
        if b == "ohem": l = R.loss(clf, Xtr[bt], ytr[bt], classes); bt = np.concatenate([bt, bt[np.argsort(-l)[:R.K]]])
        if b.startswith("smallloss"): l = R.loss(clf, Xtr[bt], ytr[bt], classes); bt = bt[np.argsort(l)[:int(round(len(bt) * (1 - r)))]]
        clf.partial_fit(Xtr[bt], ytr[bt])
    return acc(clf, D)

hk = lambda h: f"{h[0]}/{h[1]}"
def select(part):
    out = {}
    for h in HOSTS[part::2]:
        out[hk(h)] = {c: float(np.mean([struct(h, s, c) for s in SEL])) for c in RSTRUCTS}; print("select", hk(h), flush=True)
    json.dump(out, open(f"RAW6_select_p{part}.json", "w"))

def evaluate(part):
    T = {}
    for f in sorted(glob.glob("RAW6_select_p*.json")): T.update(json.load(open(f)))
    pick = lambda ks: max(RSTRUCTS, key=lambda c: (np.mean([T[k][c] for k in ks]), c)); rows = []
    for h in HOSTS[part::2]:
        own = pick([hk(h)]); tr = pick([hk(g) for g in HOSTS if g[0] != h[0]])
        for i, s in enumerate(EV):
            rng = np.random.default_rng(11200 + 10 * HOSTS.index(h) + i)
            rt = str(rng.choice([c for c in RSTRUCTS if c.count("1") == tr.count("1")])); ro = str(rng.choice([c for c in RSTRUCTS if c.count("1") == own.count("1")]))
            row = {"host": hk(h), "data": h[0], "noise": h[1], "seed": s, "own_struct": own, "tr_struct": tr, "own": struct(h, s, own),
                   "tr": struct(h, s, tr), "rnd_tr": struct(h, s, rt), "rnd_own": struct(h, s, ro), **{b: baseline(h, s, b) for b in BASE}}
            row["best_baseline"] = max(row[b] for b in BASE); rows.append(row)
            print(hk(h), s, own, tr, round(row["tr"] - row["best_baseline"], 4), flush=True)
    json.dump(rows, open(f"RAW6_eval_p{part}.json", "w"))

if __name__ == "__main__":
    {"select": select, "eval": evaluate}[sys.argv[1]](int(sys.argv[2]))
