"""T5: the same dot in different hosts on real data (re-implementation of chat 2 EXP-014 / EXP-016). See
PREREGISTRATION_T5.md."""

import itertools
import warnings

import numpy as np
from scipy.stats import spearmanr
from sklearn.datasets import load_breast_cancer, load_digits, load_wine
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from common import compile_source, bootstrap_ci, save

warnings.filterwarnings("ignore")
DOTS = ["bio", "chem", "music", "feedback"]
HOSTS = {"cancer": load_breast_cancer, "wine": load_wine, "digits": load_digits}
STEPS, BATCH, LR = 300, 16, 0.05


def dots_from_program(dots):
    """Write the configuration in the RSOS Language and read the dots back from the compiled program."""
    src = "LANGUAGE RSOS 0.2\nWORLD learning\nOBJECT learner\nPART learner.training\n"
    src += "".join(f"OBJECT {d}\nDOT {d} INTO learner.training\n" for d in dots)
    res = compile_source(src)
    assert res.ok, res.errors
    return {op["args"]["function"] for op in res.ir["ops"] if op["op"] == "dot"}


def run(host, dots, seed):
    X, y = HOSTS[host](return_X_y=True)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, stratify=y, random_state=seed)
    sc = StandardScaler().fit(Xtr)
    Xtr, Xte = sc.transform(Xtr), sc.transform(Xte)
    classes = np.unique(y)
    clf = SGDClassifier(loss="log_loss", learning_rate="constant", eta0=LR, random_state=seed)
    rng = np.random.default_rng(seed)
    wrong = []                       # indices the learner got wrong (memory for replay)
    err_ema, prev_ema = 0.5, 0.5
    for t in range(STEPS):
        w = 0.0 if t < 100 else (min(1.0, (t - 100) / 100))       # dots fade in over steps 101-200
        idx = rng.choice(len(Xtr), BATCH, replace=False)
        if "bio" in dots and w > 0 and wrong:                     # replay, same batch budget
            k = int(BATCH * 0.5 * w)
            if k:
                idx = np.concatenate([idx[: BATCH - k], rng.choice(wrong, k)])
        Xb, yb = Xtr[idx], ytr[idx]
        lr = LR
        if "music" in dots and w > 0:
            lr *= 1 + w * (0.8 if t % 8 == 0 else -0.2)
        if "feedback" in dots and w > 0:
            lr *= 1 + w * float(np.clip((prev_ema - err_ema) * 10, -0.5, 0.5))
        if "chem" in dots and w > 0 and t > 0:
            pred = clf.predict(Xb)
            miss = pred != yb
            if miss.any():
                cov = np.abs(Xb[miss].mean(axis=0) - Xb[~miss].mean(axis=0)) if (~miss).any() else np.abs(Xb[miss].mean(axis=0))
                Xb = Xb * (1 + w * 0.5 * cov / (cov.max() + 1e-9))       # catalysis: boost error-linked features
        clf.eta0 = lr
        clf.partial_fit(Xb, yb, classes=classes)
        pred_all = clf.predict(Xtr)
        wrong = list(np.where(pred_all != ytr)[0])
        prev_ema, err_ema = err_ema, 0.9 * err_ema + 0.1 * float((pred_all != ytr).mean())
    return float((clf.predict(Xte) == yte).mean())


def main():
    configs = [()] + [c for r in range(1, 5) for c in itertools.combinations(DOTS, r)]
    acc = {h: {c: [run(h, dots_from_program(c), s) for s in range(6)] for c in configs} for h in HOSTS}
    eff = {h: {c: [100 * (a - b) for a, b in zip(acc[h][c], acc[h][()])] for c in configs[1:]} for h in HOSTS}
    mean = {h: {"+".join(c): float(np.mean(v)) for c, v in eff[h].items()} for h in HOSTS}
    ci = {h: {"+".join(c): bootstrap_ci(v) for c, v in eff[h].items()} for h in HOSTS}
    bio = {h: (mean[h]["bio"], ci[h]["bio"]) for h in HOSTS}
    h1 = any(m > 0 for m, _ in bio.values()) and any(m < 0 for m, _ in bio.values()) and \
        any(c[0] > 0 or c[1] < 0 for _, c in bio.values())
    best = {h: max(mean[h], key=mean[h].get) for h in HOSTS}
    keys = list(mean["cancer"])
    rhos = [spearmanr([mean[a][k] for k in keys], [mean[b][k] for k in keys]).correlation
            for a, b in itertools.combinations(HOSTS, 2)]
    h2 = len(set(best.values())) > 1 and float(np.mean(rhos)) < 0.5
    h3 = {}
    for h in HOSTS:
        b = best[h].split("+")
        if len(b) > 1:
            add = sum(mean[h][d] for d in b)
            half = max((ci[h][d][1] - ci[h][d][0]) / 2 for d in b)
            h3[h] = {"best": best[h], "effect": mean[h][best[h]], "sum_of_singles": add,
                     "nonadditive": abs(mean[h][best[h]] - add) > half}
    summary = {
        "H1_same_dot_different_hosts": {"bio_effect_pp": {h: round(m, 3) for h, (m, _) in bio.items()},
                                        "bio_ci95": {h: c for h, (_, c) in bio.items()}, "pass": bool(h1)},
        "H2_host_decides_best": {"best": best, "spearman_pairs": [round(r, 3) for r in rhos],
                                 "mean_spearman": round(float(np.mean(rhos)), 3), "pass": bool(h2)},
        "H3_nonadditive": {"per_host": h3, "pass": any(v["nonadditive"] for v in h3.values())},
        "baseline_accuracy": {h: round(float(np.mean(acc[h][()])), 4) for h in HOSTS},
        "chat_reference": {"bio": {"cancer": -0.390, "wine": -2.160, "digits": 0.586}, "spearman": "-0.28 to -0.22"},
    }
    path, digest = save("T5-DOTS", {"summary": summary, "mean_effect_pp": mean, "ci95": ci})
    print(path, digest)
    for k, v in summary.items():
        print(k, v)


if __name__ == "__main__":
    main()
