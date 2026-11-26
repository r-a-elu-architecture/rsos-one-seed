"""F1 post-hoc diagnostic (not pre-registered): which half of the loop costs usefulness."""
import json, numpy as np
import f1_feedback as F
from rsoslang import dragon as D

orig_run = F.run

def variant(weights, parent):
    def run(seed):
        rng = np.random.default_rng(seed); spheres, entries = D.load()
        w = {i: 1.0 for i in range(len(entries))}; idx = {id(e): i for i, e in enumerate(entries)}
        frontier, seen, share, novel_fail = spheres, set(), [], []
        for g in range(F.GENS):
            kids, useful, tried, nf = [], 0, 0, 0
            for b in frontier:
                ps = D.paths(b, entries)
                if not ps: continue
                p = np.array([w[idx[id(e)]] for e, _ in ps]) if weights else np.ones(len(ps)); p = p / p.sum()
                for j in rng.choice(len(ps), size=min(F.K, len(ps)), replace=False, p=p):
                    e, s = ps[j]; c = D.land(b, e, s); tried += 1
                    sig = (tuple(c["relations"]), tuple(c["domains"])); dup = sig in seen
                    passed = bool(D.heal_filter([c], seen)); nf += dup
                    pdef = b.get("deficit", D.deficit(b)); good = passed and c["deficit"] < pdef
                    if weights: w[idx[id(e)]] *= 1.25 if good else (0.8 if not passed else 1.0)
                    if parent and good: b["deficit"] = min(pdef, c["deficit"])
                    useful += good
                    if passed: kids.append(c)
            share.append(useful / max(1, tried)); novel_fail.append(nf / max(1, tried))
            frontier = kids if len(kids) <= F.CAP else [kids[i] for i in rng.choice(len(kids), F.CAP, replace=False)]
        return np.mean(share[1:]), np.mean(novel_fail[1:])
    return run

out = {}
for name, wt, pa in (("open", 0, 0), ("weights_only", 1, 0), ("parent_only", 0, 1), ("both", 1, 1)):
    r = [variant(wt, pa)(s) for s in range(300, 310)]
    out[name] = {"useful_per_try": round(float(np.mean([x[0] for x in r])), 3), "duplicate_rate": round(float(np.mean([x[1] for x in r])), 3)}
print(json.dumps(out, indent=1))
