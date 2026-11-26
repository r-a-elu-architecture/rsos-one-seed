"""H1: predictive healing at the greatest lack. Pre-registration: experiments/PREREGISTRATION_H1.md."""

import json

import numpy as np

from common import save, bootstrap_ci

N, STEPS, USES, SEEDS = 200, 500, 20, 20
MSG, CHECK, HEAL = 65, 60, 300


def run(seed, policy, K):
    rng = np.random.default_rng(seed)
    h = rng.beta(0.3, 12, size=N)
    pop = 1.0 / np.arange(1, N + 1) ** 1.1
    rng.shuffle(pop)
    pop /= pop.sum()
    drifted = np.zeros(N, bool)
    last = np.zeros(N)
    events, expo, used = np.zeros(N), np.zeros(N), np.ones(N)
    ok = fails = 0
    bytes_ = 0.0
    act = np.random.default_rng(seed + 99)            # policy randomness separate from the world

    def observe(i, t, drift_seen):
        expo[i] += t - last[i]
        events[i] += drift_seen
        last[i] = t

    for t in range(1, STEPS + 1):
        drifted |= rng.random(N) < h
        if policy != "R":
            if policy == "U":
                pick = act.choice(N, size=K, replace=False)
            else:
                hz = (1 + events) / (21 + expo)
                lack = 1 - (1 - hz) ** (t - last)
                score = lack * used / used.sum()
                pick = np.argsort(-(score + act.random(N) * 1e-12))[:K]
            for i in pick:
                if drifted[i]:
                    bytes_ += HEAL; drifted[i] = False; observe(i, t, 1)
                else:
                    bytes_ += CHECK; observe(i, t, 0)
        for i in rng.choice(N, size=USES, p=pop):
            used[i] += 1
            if drifted[i]:
                fails += 1; bytes_ += MSG + HEAL + MSG; drifted[i] = False; observe(i, t, 1)
            else:
                ok += 1; bytes_ += MSG; observe(i, t, 0)
    n = ok + fails
    return ok / n, bytes_ / n, 1 + 2 * fails / n


def main():
    res = {}
    for pol, K in (("R", 0), ("U", 5), ("G", 5), ("U", 10), ("G", 10)):
        rows = [run(s, pol, K) for s in range(1000, 1000 + SEEDS)]
        res[f"{pol}{K}"] = {"first_use_success": float(np.mean([r[0] for r in rows])),
                            "ci": bootstrap_ci([r[0] for r in rows]),
                            "bytes_per_use": float(np.mean([r[1] for r in rows])),
                            "round_trips_per_use": float(np.mean([r[2] for r in rows]))}
    s = lambda k: res[k]["first_use_success"]
    checks = {"P1": bool(s("G5") >= s("R0") + 0.05 and s("G5") >= s("U5") + 0.03),
              "P2": bool(res["G5"]["bytes_per_use"] <= res["R0"]["bytes_per_use"]),
              "P3": bool(s("G5") >= s("U10"))}
    path, digest = save("h1_predictive_heal", {"summary": res, "checks": checks})
    print(json.dumps(res, indent=1)); print(json.dumps(checks)); print(path, digest)


if __name__ == "__main__":
    main()
