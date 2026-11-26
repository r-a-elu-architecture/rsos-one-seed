"""F1b: feedback loop scored against the original parent, with a compute budget. Pre-registration: PREREGISTRATION_F1B.md."""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from rsoslang import dragon as D  # noqa: E402
from common import save  # noqa: E402

BUDGET, GENS, SEEDS = 1200, 6, 10


def run(seed, weights, parent):
    rng = np.random.default_rng(seed)
    spheres, entries = D.load()
    idx = {id(e): i for i, e in enumerate(entries)}
    w = np.ones(len(entries))
    roots = {b["code"]: D.deficit(b) for b in spheres}
    start = np.mean(list(roots.values()))
    root_of = {b["code"]: b["code"] for b in spheres}
    frontier, seen, share, counts = spheres, set(), [], []
    for _ in range(GENS):
        live = [(b, D.paths(b, entries)) for b in frontier]
        live = [x for x in live if x[1]]
        if not live:
            share.append(0.0); counts.append(0); continue
        kids, useful = [], 0
        for _ in range(BUDGET):
            b, ps = live[rng.integers(len(live))]
            p = np.array([w[idx[id(e)]] for e, _ in ps]) if weights else np.ones(len(ps))
            e, s = ps[rng.choice(len(ps), p=p / p.sum())]
            c = D.land(b, e, s)
            passed = bool(D.heal_filter([c], seen))
            good = passed and c["deficit"] < D.deficit(b)          # original parent deficit
            root_of[c["code"]] = root_of[b["code"]]
            if weights:
                w[idx[id(e)]] *= 1.25 if good else (0.8 if not passed else 1.0)
            if parent and good:
                r = root_of[b["code"]]; roots[r] = min(roots[r], c["deficit"])
            useful += good
            if passed:
                kids.append(c)
        share.append(useful / BUDGET); counts.append(useful)
        frontier = kids
    u = np.array(counts[1:], float)
    return {"share": float(np.mean(share[1:])), "cv": float(u.std() / u.mean()) if u.mean() else float("inf"),
            "root_drop": float(start - np.mean(list(roots.values()))), "counts": counts}


def main():
    res = {}
    for name, wt, pa in (("open", 0, 0), ("weights", 1, 0), ("weights_parent", 1, 1)):
        rows = [run(s, wt, pa) for s in range(700, 700 + SEEDS)]
        res[name] = {k: float(np.mean([r[k] for r in rows])) for k in ("share", "cv", "root_drop")}
        res[name]["counts_seed700"] = rows[0]["counts"]
    o, wv, wp = res["open"], res["weights"], res["weights_parent"]
    checks = {"P1": wp["share"] >= o["share"] + 0.05, "P2": wv["share"] >= o["share"] + 0.03,
              "P3": wv["cv"] <= o["cv"] and wp["cv"] <= o["cv"], "P4": wp["root_drop"] >= 0.10}
    checks = {k: bool(v) for k, v in checks.items()}
    path, digest = save("f1b_feedback", {"summary": res, "checks": checks})
    print(json.dumps(res, indent=1)); print(json.dumps(checks)); print(path, digest)


if __name__ == "__main__":
    main()
