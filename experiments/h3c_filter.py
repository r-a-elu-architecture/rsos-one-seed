"""H3c: evolve-healing decided by the White Dragon filter. Pre-registration: PREREGISTRATION_H3C.md."""

import json

import numpy as np

from common import save

P, B, STEPS, SEEDS, MSG = 20, 30, 300, 10, 50


def run(seed, policy):
    rng = np.random.default_rng(seed)
    ver = np.zeros((P, B), int)
    q = {0: 0.0}; harm = {0: False}; flag = {0: False}; meas = {0: True}
    nv = 1
    for _ in range(STEPS):
        for i, b in zip(*np.where(rng.random((P, B)) < 0.02)):
            h = rng.random() < 0.05
            q[nv] = q[ver[i, b]] + (rng.normal(-0.5, 0.1) if h else rng.normal(-0.01, 0.1))
            harm[nv] = h; flag[nv] = h and rng.random() < 0.9; meas[nv] = rng.random() < 0.6
            ver[i, b] = nv; nv += 1
        for _ in range(MSG):
            i, j = rng.choice(P, size=2, replace=False); b = rng.integers(B)
            vi, vj = ver[i, b], ver[j, b]
            if vi == vj:
                continue
            if policy == "restore":
                keep = vi
            elif policy == "oracle":
                keep = vi if q[vi] >= q[vj] else vj
            else:
                cand = [v for v in (vi, vj) if not flag[v]]
                if not cand:
                    keep = vj                                   # both flagged: keep the receiver's, send nothing on
                elif len(cand) == 1:
                    keep = cand[0]
                else:
                    m = [v for v in cand if meas[v]]
                    if len(m) == 2:
                        s = {v: q[v] + rng.normal(0, 0.15) for v in m}
                        keep = max(m, key=s.get)
                    elif len(m) == 1:
                        keep = m[0]
                    else:
                        keep = vi
            ver[i, b] = ver[j, b] = keep if policy != "restore" else vi
    flat = ver.ravel()
    return float(np.mean([q[v] for v in flat])), float(np.mean([harm[v] for v in flat]))


def main():
    res = {}
    for pol in ("restore", "oracle", "filter"):
        r = [run(s, pol) for s in range(500, 500 + SEEDS)]
        res[pol] = {"quality": float(np.mean([x[0] for x in r])), "harmful_share": float(np.mean([x[1] for x in r]))}
    R, O, F = res["restore"], res["oracle"], res["filter"]
    capture = (F["quality"] - R["quality"]) / (O["quality"] - R["quality"])
    res["filter_capture_of_oracle_gain"] = capture
    checks = {"P1": bool(F["quality"] >= R["quality"] + 0.5), "P2": bool(capture >= 0.5),
              "P3": bool(F["harmful_share"] <= R["harmful_share"] / 2)}
    path, digest = save("h3c_filter", {"summary": res, "checks": checks})
    print(json.dumps(res, indent=1)); print(json.dumps(checks)); print(path, digest)


if __name__ == "__main__":
    main()
