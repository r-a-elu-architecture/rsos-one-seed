"""V1: the VAKOG key. Pre-registration: experiments/PREREGISTRATION_V1.md."""

import json

import numpy as np

from common import save
from rsoslang.vakog import VakogPalace, spread

N, CUES, SEED = 200, 2000, 20261117


def make(rng, S):
    anchors = rng.integers(0, S, size=(N, 5))
    return VakogPalace(anchors, [f"book-{i}-{rng.integers(1e9)}" for i in range(N)])


def cue_of(pal, i, k, q, S, rng, chans=None):
    chans = list(rng.choice(5, size=k, replace=False)) if chans is None else chans
    cue = {}
    for ch in chans:
        sym = pal.anchors[i, ch]
        if rng.random() < q:
            sym = (sym + rng.integers(1, S)) % S
        cue[int(ch)] = int(sym)
    return cue


def cell(S, k, q, rng):
    pal = make(rng, S)
    a = c = 0
    for _ in range(CUES):
        i = int(rng.integers(N))
        cue = cue_of(pal, i, k, q, S, rng)
        a += pal.open_by_name(cue, rng) == i
        c += pal.complete(cue, rng) == i
    return a / CUES, c / CUES


def single_channel(S, rng):
    pal = make(rng, S)
    per = []
    for ch in range(5):
        ok = sum(pal.complete(cue_of(pal, i, 1, 0, S, rng, [ch]), rng) == i for i in rng.integers(N, size=CUES))
        per.append(ok / CUES)
    return per


def drift(rng, S=1000, k=2):
    sender = make(rng, S)
    recv = VakogPalace(sender.anchors.copy(), list(sender.contents))
    drifted = rng.choice(N, size=N // 10, replace=False)
    for i in drifted:
        ch = int(rng.integers(5))
        recv.anchors[i, ch] = (recv.anchors[i, ch] + rng.integers(1, S)) % S
        recv.contents[i] = recv.contents[i] + "-changed"
    silent_c = silent_e = detected = drift_opens = 0
    for _ in range(CUES):
        i = int(rng.integers(N))
        cue = cue_of(sender, i, k, 0, S, rng)
        j = recv.complete(cue, rng)
        if j is not None and recv.contents[j] != sender.contents[i]:
            silent_c += 1
        je, det = recv.complete_checked(cue, sender.signal(i), rng)
        if je is not None and recv.contents[je] != sender.contents[i]:
            silent_e += 1
        if i in drifted:
            drift_opens += 1
            detected += det
    return {"silent_wrong_C": silent_c, "silent_wrong_E": silent_e, "drifted_cues": drift_opens,
            "detected_E": detected}


def flow(rng, trials=2000):
    lack, even = [], []
    for _ in range(trials):
        d = rng.beta(0.5, 2.0, size=10)
        b = 0.5 * d.sum()
        lack.append(spread(range(10), d, b, True)); even.append(spread(range(10), d, b, False))
    return float(np.mean(lack)), float(np.mean(even))


def main():
    rng = np.random.default_rng(SEED)
    grid = {}
    for S in (20, 1000):
        for q in (0.0, 0.2):
            for k in range(1, 6):
                grid[f"S{S}_q{q}_k{k}"] = cell(S, k, q, rng)
    single = single_channel(1000, rng)
    dr = drift(rng)
    fl, fe = flow(rng)
    g = lambda S, q, k: grid[f"S{S}_q{q}_k{k}"]
    summary = {"grid_name_vs_completion": grid, "single_channel_S1000": dict(zip("VAKOG", single)),
               "drift": dr, "flow_to_lack": fl, "flow_even": fe, "flow_ratio": fl / fe}
    checks = {
        "P1": bool(g(20, 0.0, 2)[1] >= 0.9 and g(20, 0.0, 2)[1] >= g(20, 0.0, 2)[0] + 0.5),
        "P2": bool(g(20, 0.2, 3)[1] >= 0.8 and g(20, 0.2, 3)[0] <= 0.3),
        "P3": bool(min(single) >= 0.95 and abs(g(1000, 0.0, 1)[0] - 0.2) <= 0.05),
        "P4": bool(dr["silent_wrong_C"] > 0 and dr["silent_wrong_E"] == 0 and dr["detected_E"] == dr["drifted_cues"]),
        "P5": bool(fl / fe >= 1.5),
    }
    path, digest = save("v1_vakog", {"summary": summary, "checks": checks})
    for k2, v in grid.items():
        print(k2, "name %.3f  completion %.3f" % v)
    print(json.dumps({k2: v for k2, v in summary.items() if k2 != "grid_name_vs_completion"}, indent=1))
    print(json.dumps(checks)); print(path, digest)


if __name__ == "__main__":
    main()
