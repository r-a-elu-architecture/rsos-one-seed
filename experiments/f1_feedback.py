"""F1: feedback in the White Dragon engine. Pre-registration: PREREGISTRATION_F1.md."""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from rsoslang import dragon as D  # noqa: E402
from common import save  # noqa: E402

K, CAP, GENS, SEEDS = 4, 300, 6, 10


def run(seed, feedback):
    rng = np.random.default_rng(seed)
    spheres, entries = D.load()
    w = {i: 1.0 for i in range(len(entries))}
    idx = {id(e): i for i, e in enumerate(entries)}
    roots = {b["code"]: {"deficit": D.deficit(b), "measured_by": set()} for b in spheres}
    root_of = {b["code"]: b["code"] for b in spheres}
    start = np.mean([r["deficit"] for r in roots.values()])
    frontier, seen, useful_n, share, doms6 = spheres, set(), [], [], set()
    for g in range(GENS):
        kids_all, useful = [], 0
        for b in frontier:
            ps = D.paths(b, entries)
            if not ps:
                continue
            if feedback:
                p = np.array([w[idx[id(e)]] for e, _ in ps]); p = p / p.sum()
            else:
                p = None
            pick = rng.choice(len(ps), size=min(K, len(ps)), replace=False, p=p)
            for j in pick:
                e, s = ps[j]
                c = D.land(b, e, s)
                passed = bool(D.heal_filter([c], seen))
                pdef = b.get("deficit", D.deficit(b))
                good = passed and c["deficit"] < pdef
                root_of[c["code"]] = root_of[b["code"]]
                if feedback:
                    w[idx[id(e)]] *= 1.25 if good else (0.8 if not passed else 1.0)
                    if good:
                        r = roots[root_of[b["code"]]]
                        r["deficit"] = min(r["deficit"], c["deficit"]); r["measured_by"] |= set(c["measured_by"])
                        b["deficit"] = min(pdef, c["deficit"])
                useful += good
                if passed:
                    kids_all.append(c)
                    if g == GENS - 1:
                        doms6.add(e["domain"])
        n = sum(1 for b in frontier for _ in [0])
        useful_n.append(useful); share.append(useful / max(1, min(K, 99) * len(frontier)))
        frontier = kids_all if len(kids_all) <= CAP else [kids_all[i] for i in rng.choice(len(kids_all), CAP, replace=False)]
        if not frontier:
            useful_n += [0] * (GENS - g - 1); share += [0.0] * (GENS - g - 1); break
    u = np.array(useful_n[1:], float)
    cv = float(u.std() / u.mean()) if u.mean() > 0 else float("inf")
    end = np.mean([r["deficit"] for r in roots.values()])
    return {"useful_share": float(np.mean(share[1:])), "cv": cv, "root_drop": float(start - end),
            "domains_gen6": len(doms6), "useful_counts": useful_n}


def main():
    res = {}
    for name, fb in (("open", False), ("feedback", True)):
        rows = [run(s, fb) for s in range(300, 300 + SEEDS)]
        res[name] = {k: float(np.mean([r[k] for r in rows])) for k in ("useful_share", "cv", "root_drop", "domains_gen6")}
        res[name]["useful_counts_seed300"] = rows[0]["useful_counts"]
    o, f = res["open"], res["feedback"]
    checks = {"P1": f["useful_share"] >= o["useful_share"] + 0.10, "P2": f["cv"] <= o["cv"],
              "P3": f["root_drop"] >= 0.10, "P4": f["domains_gen6"] >= 6}
    checks = {k: bool(v) for k, v in checks.items()}
    path, digest = save("f1_feedback", {"summary": res, "checks": checks})
    print(json.dumps(res, indent=1)); print(json.dumps(checks)); print(path, digest)


if __name__ == "__main__":
    main()
