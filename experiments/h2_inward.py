"""H2: landing changes the place, travels inward, lack speeds it up. Pre-registration: PREREGISTRATION_H2.md."""

import json

import numpy as np

from common import save, bootstrap_ci

N, K, STEPS, SEEDS = 200, 10, 300, 20


def run(seed, policy, speed_rule=True):
    rng = np.random.default_rng(seed)
    c = rng.lognormal(np.log(0.05) - 0.32, 0.8, size=N)          # mean ≈ 0.05
    reserve = rng.uniform(0.5, 2.0, size=N)
    dry = np.zeros(N)
    last_supply = np.zeros(N)                                      # what the guessing policy knows
    inflight = []                                                  # (arrival_step, node, dose)
    work = longdry = 0
    pol = np.random.default_rng(seed + 7)
    for t in range(1, STEPS + 1):
        reserve -= c
        dry += 1
        if policy == "R":
            pick = pol.choice(N, size=K, replace=False)
        elif policy == "guess":
            est = (t - last_supply) * c.mean()
            pick = np.argsort(-(est + pol.random(N) * 1e-9))[:K]
        elif policy == "report":                                   # report: the host tells its own lack
            pick = np.lexsort((-dry, reserve))[:K]
        else:                                                      # report_net: lack minus help on the way
            coming = np.zeros(N)
            for _, j, dz in inflight:
                coming[j] += dz
            pick = np.lexsort((-dry, reserve + coming))[:K]
        for i in pick:
            d = dry[i]
            tau = max(1, round(3 / (1 + d / 10))) if speed_rule else 3
            dose = 1 + min(d, 20) / 20
            inflight.append((t + 3 * tau, int(i), dose))           # surface → capillary → cell
            last_supply[i] = t
        keep = []
        for arr, i, dose in inflight:
            if arr <= t:
                reserve[i] = min(3.0, max(reserve[i], 0) + dose); dry[i] = 0
            else:
                keep.append((arr, i, dose))
        inflight = keep
        work += (reserve > 0).mean()
        longdry += (dry > 30).mean()
    return work / STEPS, longdry / STEPS


def main_b():
    res = {}
    for sp in (True, False):
        for pol in ("R", "guess", "report_net"):
            rows = [run(s, pol, sp) for s in range(900, 920)]
            res[f"{pol}_{'speed' if sp else 'constant'}"] = {"working": float(np.mean([r[0] for r in rows])),
                                                             "ci": bootstrap_ci([r[0] for r in rows])}
    w = lambda k: res[k]["working"]
    checks = {"P1": bool(w("report_net_speed") >= w("guess_speed") + 0.02 and w("report_net_speed") >= w("R_speed") + 0.05),
              "P2": bool(abs(w("report_net_speed") - w("report_net_constant")) < 0.01)}
    path, digest = save("h2b_report_net", {"summary": res, "checks": checks})
    print(json.dumps(res, indent=1)); print(json.dumps(checks)); print(path, digest)


def main():
    res = {}
    for sp in (True, False):
        for pol in ("R", "guess", "report"):
            rows = [run(s, pol, sp) for s in range(500, 500 + SEEDS)]
            key = f"{pol}_{'speed' if sp else 'constant'}"
            res[key] = {"working": float(np.mean([r[0] for r in rows])), "ci": bootstrap_ci([r[0] for r in rows]),
                        "long_dry": float(np.mean([r[1] for r in rows]))}
    w = lambda k: res[k]["working"]
    adv_speed = w("report_speed") - w("R_speed")
    adv_const = w("report_constant") - w("R_constant")
    checks = {"P1": bool(w("report_speed") >= w("guess_speed") + 0.05 and adv_speed >= 0.10),
              "P2": bool(adv_speed - adv_const >= 0.02),
              "P3": bool(res["report_speed"]["long_dry"] <= 0.02)}
    summary = {"results": res, "advantage_speed": adv_speed, "advantage_constant": adv_const}
    path, digest = save("h2_inward", {"summary": summary, "checks": checks})
    print(json.dumps(summary, indent=1)); print(json.dumps(checks)); print(path, digest)


if __name__ == "__main__":
    import sys
    main_b() if "b" in sys.argv[1:] else main()
