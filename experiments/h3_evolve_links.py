"""H3: healing that evolves, and healing of connections. Pre-registration: PREREGISTRATION_H3.md."""

import json

import numpy as np

from common import save, bootstrap_ci

P, B, STEPS, SEEDS, MSG = 20, 30, 300, 10, 50


def run(seed, policy):
    rng = np.random.default_rng(seed)
    ver = np.zeros((P, B), int)
    qual = np.zeros((P, B))
    q_of = {0: 0.0}                                  # version id -> quality (a version is one content)
    nextv = 1
    link = np.zeros((P, P), int)                     # link[i, j] = i's codebook for the i-j connection
    delivered = 0
    trend = []
    for t in range(STEPS):
        edit = rng.random((P, B)) < 0.02
        for i, b in zip(*np.where(edit)):
            q_of[nextv] = q_of[ver[i, b]] + rng.normal(-0.01, 0.1)
            ver[i, b] = nextv; nextv += 1
        drift = rng.random((P, P)) < 0.01
        link[drift] += 1000 + rng.integers(1, 10**6, size=drift.sum())
        for _ in range(MSG):
            i, j = rng.choice(P, size=2, replace=False)
            b = rng.integers(B)
            if link[i, j] != link[j, i]:
                if policy == "A":
                    continue                         # connection broken: message lost
                link[j, i] = link[i, j]              # heal the connection
            if ver[i, b] != ver[j, b]:
                if policy == "C":
                    qi = q_of[ver[i, b]] + rng.normal(0, 0.02)
                    qj = q_of[ver[j, b]] + rng.normal(0, 0.02)
                    best = ver[i, b] if qi >= qj else ver[j, b]
                    ver[i, b] = ver[j, b] = best     # evolve: both keep the better
                else:
                    ver[j, b] = ver[i, b]            # restore to the sender's
            delivered += 1
        trend.append(np.mean([q_of[v] for v in ver.ravel()]))
    tr = np.array(trend)
    slope = float(np.polyfit(np.arange(100, STEPS), tr[100:], 1)[0])
    return delivered / (STEPS * MSG), float(tr[-1]), slope


def main():
    res = {}
    for pol in "ABC":
        rows = [run(s, pol) for s in range(100, 100 + SEEDS)]
        res[pol] = {"delivery": float(np.mean([r[0] for r in rows])), "delivery_ci": bootstrap_ci([r[0] for r in rows]),
                    "final_quality": float(np.mean([r[1] for r in rows])), "slope": float(np.mean([r[2] for r in rows]))}
    checks = {"P1": bool(res["B"]["delivery"] >= res["A"]["delivery"] + 0.05),
              "P2": bool(res["C"]["final_quality"] >= res["B"]["final_quality"] + 0.10
                         and abs(res["C"]["delivery"] - res["B"]["delivery"]) <= 0.01),
              "P3": bool(res["B"]["slope"] <= 0.0005 and res["C"]["slope"] > 0)}
    path, digest = save("h3_evolve_links", {"summary": res, "checks": checks})
    print(json.dumps(res, indent=1)); print(json.dumps(checks)); print(path, digest)


if __name__ == "__main__":
    main()
