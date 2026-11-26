"""SPHERE2: powered re-test. Predictions: PREREG_SPHERE2.md (sha256 667619b5…0e50, commit aa80b3f), sealed first."""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sphere"))
import sphere1 as S1  # noqa: E402

ops1, E2, H, E1 = S1.ops1, S1.E2, S1.H, S1.E1
COUNTS = {"key": (1, 20000), "pair": (2, 20000), "condition": (50, 4000), "scan": (300, 4000)}
FIELD_ELEMS = [list(range(f, 300, 6)) for f in range(6)]


def run_node(op, g):
    out = {}
    for fam, (n, cnt) in COUNTS.items():
        fails = sum(int(op(fam, n, g)) for _ in range(cnt))
        out[fam] = [fails, cnt]
    return out


def node_ops(g):
    ch = ops1.GE(g); L = ops1.Ledger(g)

    def n2(fam, n, g):
        for _ in range(10):
            ch.send()
        return not all(ops1.net_element(ch) for _ in range(n))

    def n3(fam, n, g):
        for _ in range(10):
            L.epoch()
        return not all(L.epoch() for _ in range(n))

    def n5(fam, n, g):
        return bool((g.poisson(4, size=n) == 0).any())

    def n6(fam, n, g):
        t0 = g.uniform(0, 100)
        return any(((t0 + i * 0.01) % 100) >= 70 for i in range(n))

    def n7(fam, n, g):
        down = set(int(x) for x in g.choice(300, 10, replace=False))
        idx = FIELD_ELEMS[g.integers(6)] if fam == "condition" else [int(x) for x in g.choice(300, n, replace=False)]
        return any(i in down for i in idx)
    return {"N2": n2, "N3": n3, "N5": n5, "N6": n6, "N7": n7}


def classify(c):
    k, kn = c["key"]; p, pn = c["pair"]
    pk, pp = k / kn, p / pn
    d = pp - pk; se = math.sqrt(pk * (1 - pk) / kn + pp * (1 - pp) / pn)
    lo, hi = d - 1.96 * se, d + 1.96 * se
    cls = "element" if lo > pk / 4 else ("time" if hi < pk / 4 else "undecided")
    return cls, round(d, 5), round(lo, 5), round(hi, 5)


def healing():
    g = np.random.default_rng(2030); res = {}
    for loss in (0.85, 0.95):
        a = {"alone": [0, 0], "with_N3": [0, 0]}
        for s in range(1030, 1046):
            ff, fv, R, codes, h = E1.store(s, 1)
            alive = ~H.erase(s, loss, 0)
            known = g.random(len(ff)) < 0.30
            idxs = {fi: np.where(ff == fi)[0] for fi in range(6)}

            def prior(Pd, idxs=idxs, known=known, fv=fv):
                lp = {}
                for fi, ix in idxs.items():
                    arr = np.zeros((len(ix), E2.NV[H.FIELDS[fi]]))
                    for r, k in enumerate(ix):
                        if known[k]:
                            arr[r, :] = -30.0; arr[r, fv[k]] = 0.0
                    lp[fi] = arr
                return lp
            v0, _, _ = E2.soft_read(h, alive, R, ff, codes)
            v1, _, _ = E2.soft_read(h, alive, R, ff, codes, prior=prior)
            u = ~known
            a["alone"][0] += int((v0[u] == fv[u]).sum()); a["alone"][1] += int(u.sum())
            a["with_N3"][0] += int((v1[u] == fv[u]).sum()); a["with_N3"][1] += int(u.sum())
        res[str(loss)] = {k: round(x / y, 5) for k, (x, y) in a.items()}
        print("heal", loss, res[str(loss)], flush=True)
    return res


def main():
    g = np.random.default_rng(2002)
    out = {"nodes": {}}
    for name, op in node_ops(g).items():
        c = run_node(op, g)
        r = {f: round(a / b, 5) for f, (a, b) in c.items()}
        cls, d, lo, hi = classify(c)
        eps = r["key"]
        r.update({"class": cls, "pair_minus_key": d, "ci": [lo, hi],
                  "bound": {f: round(1 - (1 - eps) ** COUNTS[f][0], 5) for f in COUNTS}})
        out["nodes"][name] = r; print(name, r, flush=True)
    out["healing"] = healing()
    N = out["nodes"]
    orbit_theory = {f: round((30 + 0.01 * (COUNTS[f][0] - 1)) / 100, 5) for f in COUNTS}
    v = {
        "T1": N["N2"]["class"] == "element" and N["N3"]["class"] == "time" and N["N5"]["class"] == "element"
        and N["N6"]["class"] == "time",
        "T2": abs(N["N5"]["condition"] - N["N5"]["bound"]["condition"]) <= 0.02,
        "T3": all(abs(N["N6"][f] - orbit_theory[f]) <= 0.01 for f in COUNTS),
        "T4": N["N7"]["condition"] >= N["N7"]["bound"]["condition"] + 0.015,
        "T5": out["healing"]["0.85"]["with_N3"] >= out["healing"]["0.85"]["alone"] + 0.05
        and out["healing"]["0.95"]["with_N3"] >= out["healing"]["0.95"]["alone"] + 0.03,
    }
    out["orbit_theory"] = orbit_theory; out["verdicts"] = v
    json.dump(out, open(os.path.join(HERE, "RESULTS_SPHERE2.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
