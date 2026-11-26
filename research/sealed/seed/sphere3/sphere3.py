"""SPHERE3: Theorem 1 with ε measured inside the same operations. Predictions: PREREG_SPHERE3.md (sealed first)."""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sphere"))
import sphere1 as S1  # noqa: E402

ops1 = S1.ops1
N_OPS, N = 8000, 50
FIELD_ELEMS = [list(range(f, 300, 6)) for f in range(6)]


def run(name, g):
    ch = ops1.GE(g); L = ops1.Ledger(g)
    joint = 0; elem_fail = 0
    for _ in range(N_OPS):
        if name == "N2":
            for _ in range(10):
                ch.send()
            reads = [ops1.net_element(ch) for _ in range(N)]
        elif name == "N3":
            for _ in range(10):
                L.epoch()
            reads = [L.epoch() for _ in range(N)]
        elif name == "N5":
            reads = list(g.poisson(4, size=N) > 0)
        else:
            down = set(int(x) for x in g.choice(300, 10, replace=False))
            reads = [i not in down for i in FIELD_ELEMS[g.integers(6)]]
        bad = N - sum(bool(r) for r in reads)
        elem_fail += bad; joint += int(bad > 0)
    eps = elem_fail / (N_OPS * N); obs = joint / N_OPS
    bound = 1 - (1 - eps) ** N
    se = math.sqrt(obs * (1 - obs) / N_OPS)
    return {"eps_inside": round(eps, 6), "joint_failure": round(obs, 5), "bound": round(bound, 5),
            "gap_pp": round(100 * (obs - bound), 3), "se_pp": round(100 * se, 3)}


def main():
    g = np.random.default_rng(3003)
    out = {n: run(n, g) for n in ("N2", "N3", "N5", "N7")}
    for n, r in out.items():
        print(n, r, flush=True)
    v = {"U1": abs(out["N5"]["gap_pp"]) <= 1.0,
         "U2": out["N7"]["gap_pp"] >= 1.5,
         "U3": out["N2"]["gap_pp"] <= -5 and out["N3"]["gap_pp"] <= -5,
         "U4": all(out[n]["gap_pp"] <= 1.0 for n in ("N2", "N3", "N5"))}
    out["verdicts"] = v
    json.dump(out, open(os.path.join(HERE, "RESULTS_SPHERE3.json"), "w"), indent=1)
    print(json.dumps(v))


if __name__ == "__main__":
    main()
