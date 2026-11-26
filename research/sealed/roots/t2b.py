"""T2b: static levers against the living hologram (layer 2). Predictions: PREREG_T2B.md (sealed before this file,
sha256 cae47165cdca2330c7e46caf7f667af1199db4b32a5698aab512cd430ae3e005, commit 77a154c)."""
import json
import os
import sys

import numpy as np
from scipy.special import log_ndtr

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
HERE = os.path.dirname(os.path.abspath(__file__))
import sc1_tasks as SC  # noqa: E402

D = 10_000
SEEDS = list(range(900, 932))
LOSSES = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9]
FIELDS = list(SC.FIELDS)
VALUES = {"x": [str(i) for i in range(10)], "y": [str(i) for i in range(10)],
          "height_mm": [str(i * 100) for i in range(1, 51)], "owner": SC.ROBOTS, "room": SC.ROOMS, "on": SC.SURFACES}
ORDERED = ("x", "y", "height_mm")
OBJ = list(SC.OBJECTS)

rng = np.random.default_rng(7)
bip = lambda n=D: rng.choice(np.array([-1, 1], dtype=np.int8), size=n)
O = np.stack([bip() for _ in OBJ])
Fv = {f: bip() for f in FIELDS}
RAND = {f: np.stack([bip() for _ in VALUES[f]]) for f in FIELDS}


def levels(n, base=None):
    """n ordered bipolar vectors; neighbours similar, ends about orthogonal (flip D/2 positions in total)."""
    v = bip() if base is None else base.copy()
    order = rng.permutation(D)
    step = (D // 2) / max(n - 1, 1)
    out = []
    for i in range(n):
        w = v.copy(); w[order[:int(round(i * step))]] *= -1; out.append(w)
    return np.stack(out)


LINE = {f: (levels(len(VALUES[f])) if f in ORDERED else RAND[f]) for f in FIELDS}

# rule 3/4: roads in a sphere; a point's code binds the level vectors of its x, y, z coordinates
AX = [levels(64) for _ in range(3)]


def q(c):
    return int(np.clip(round((c + 1) / 2 * 63), 0, 63))


def path_points(verts, n, closed=True):
    verts = np.array(verts, float)
    segs = list(zip(verts, np.roll(verts, -1, 0))) if closed else list(zip(verts[:-1], verts[1:]))
    lens = np.array([np.linalg.norm(b - a) for a, b in segs]); total = lens.sum()
    pts = []
    for i in range(n):
        t = i * total / n
        for (a, b), L in zip(segs, lens):
            if t <= L:
                pts.append(a + (b - a) * t / L); break
            t -= L
    return np.array(pts)


ROADS = {
    "x": path_points([(-0.8, -0.5, -0.3), (0.8, -0.5, 0.3), (0.0, 0.9, 0.0)], 10),                       # triangle
    "y": path_points([(-0.6, -0.6, 0.5), (0.6, -0.6, -0.5), (0.6, 0.6, 0.5), (-0.6, 0.6, -0.5)], 10),    # square
    "height_mm": np.array([(0.8 * np.cos(t), 0.8 * np.sin(t) * np.cos(0.5236), 0.8 * np.sin(t) * np.sin(0.5236))
                           for t in np.linspace(0, 2 * np.pi, 50, endpoint=False)]),                     # circle
}
ROAD = {f: (np.stack([AX[0][q(p[0])] * AX[1][q(p[1])] * AX[2][q(p[2])] for p in ROADS[f]]) if f in ORDERED
            else RAND[f]) for f in FIELDS}


# ------------------------------------------------------------------------------------------------ structure
def facts_of(state):
    fo, ff, fv = [], [], []
    for key, val in state.items():
        o, f = key.split(".")
        fo.append(OBJ.index(o)); ff.append(FIELDS.index(f)); fv.append(VALUES[f].index(val))
    return np.array(fo), np.array(ff), np.array(fv)


def roles(fo, ff, rooms, n=D):
    R = (O[fo, :n] * np.stack([Fv[FIELDS[i]][:n] for i in ff])).astype(np.int8)
    if rooms:
        size = n // len(OBJ)
        mask = np.zeros((len(fo), n), np.int8)
        for k, o in enumerate(fo):
            mask[k, o * size:(o + 1) * size] = 1
        R = R * mask
    return R


def bindings(R, ff, vals, codes, n=D):
    return R * np.stack([codes[FIELDS[f]][v, :n] for f, v in zip(ff, vals)])


def sgn(S):
    h = np.sign(S).astype(np.int8); h[h == 0] = 1; return h


def plain_read(h, R, ff, codes, n=D):
    """One read: unbind each role, best candidate by dot product. Returns values, gaps, alive support."""
    vhat = np.zeros(len(ff), int); gap = np.zeros(len(ff)); sup = np.zeros(len(ff))
    hf = h.astype(np.float32)
    for fi, f in enumerate(FIELDS):
        idx = np.where(ff == fi)[0]
        U = hf[None, :] * R[idx].astype(np.float32)
        sc = U @ codes[f][:, :n].T.astype(np.float32)
        srt = np.sort(sc, 1)
        vhat[idx] = sc.argmax(1); gap[idx] = srt[:, -1] - srt[:, -2]
        sup[idx] = (U != 0).sum(1)
    return vhat, gap, sup


def writer_weights(R, ff, vals, codes, rounds=10):
    """Rule 6: strengths stay; weak facts reinforced, over-strong reinforcement dissipates; same budget."""
    B = bindings(R, ff, vals, codes).astype(np.int32)
    w = np.ones(len(ff), np.int32)
    for _ in range(rounds):
        h = sgn(w @ B)
        hf = h.astype(np.float32)
        for fi, f in enumerate(FIELDS):
            idx = np.where(ff == fi)[0]
            sc = (hf[None, :] * R[idx].astype(np.float32)) @ codes[f].T.astype(np.float32)
            corr = sc[np.arange(len(idx)), vals[idx]]
            sc[np.arange(len(idx)), vals[idx]] = -np.inf
            margin = (corr - sc.max(1)) / np.sqrt((R[idx] != 0).sum(1))
            w[idx[margin < 3]] += 1
            w[idx[(margin > 9) & (w[idx] > 1)]] -= 1
    return w


def explain_read(h, alive, R, ff, codes, vprev, w, sigma):
    """Rule 5: read every fact through the relations of all the others (estimated from the previous pass)."""
    Bh = bindings(R, ff, vprev, codes).astype(np.float32)
    S_hat = (w.astype(np.float32)) @ Bh
    vhat = np.zeros(len(ff), int)
    hp = (h == 1)
    for fi, f in enumerate(FIELDS):
        idx = np.where(ff == fi)[0]
        wk = w[idx].astype(np.float32)[:, None]
        Rh = S_hat[None, :] - wk * Bh[idx]                       # the rest, as estimated
        # P(h=+1 | b) = P(rest >= -w b), rest ~ N(Rh, sigma^2), continuity-corrected
        lp_pos = log_ndtr((Rh + wk + 0.5) / sigma)                  # log P(h=+1 | b=+1)
        lp_neg = log_ndtr((Rh - wk + 0.5) / sigma)                  # log P(h=+1 | b=-1)
        lq_pos = log_ndtr(-(Rh + wk + 0.5) / sigma)                 # log P(h=-1 | b=+1)
        lq_neg = log_ndtr(-(Rh - wk + 0.5) / sigma)
        delta = np.where(hp[None, :], lp_pos - lp_neg, lq_pos - lq_neg) * alive[None, :]
        sc = (delta * R[idx].astype(np.float32)) @ codes[f].T.astype(np.float32)
        vhat[idx] = sc.argmax(1)
    return vhat


def read(arm, h, alive, R, ff, codes, writer_w):
    hd = h * alive.astype(np.int8)
    v0, gap, sup = plain_read(hd, R, ff, codes)
    passes = {"plain": 1, "D": 2, "R5": 5}[arm["read"]]
    if passes == 1:
        return v0, np.ones(len(ff), np.int32), 1
    n_low = int((gap < 2 * np.sqrt(np.maximum(sup, 1))).sum())
    sigma = np.sqrt(2 * n_low + 1)
    v = v0; used = 1
    for _ in range(passes - 1):
        w = writer_weights(R, ff, v, codes) if arm["r6"] else np.ones(len(ff), np.int32)
        vn = explain_read(hd, alive.astype(np.float32), R, ff, codes, v, w, sigma)
        used += 1
        if np.array_equal(vn, v):
            v = vn; break
        v = vn
    w = writer_weights(R, ff, v, codes) if arm["r6"] else np.ones(len(ff), np.int32)
    return v, w, used


ARMS = {
    "T2r": dict(rooms=False, codes="rand", read="plain", r6=False, heal=False),
    "A": dict(rooms=True, codes="rand", read="plain", r6=False, heal=False),
    "B": dict(rooms=False, codes="line", read="plain", r6=False, heal=False),
    "D": dict(rooms=False, codes="rand", read="D", r6=False, heal=False),
    "R2": dict(rooms=False, codes="rand", read="plain", r6=False, heal=True),
    "R34": dict(rooms=False, codes="road", read="plain", r6=False, heal=False),
    "R5": dict(rooms=False, codes="rand", read="R5", r6=False, heal=False),
    "R6": dict(rooms=False, codes="rand", read="plain", r6=True, heal=False),
    "Static": dict(rooms=True, codes="line", read="D", r6=False, heal=False),
    "Living": dict(rooms=False, codes="road", read="R5", r6=True, heal=True),
}
CODES = {"rand": RAND, "line": LINE, "road": ROAD}


def damage(seed, loss, rnd, n=D):
    g = np.random.default_rng([seed, int(round(loss * 100)), rnd])
    dead = np.zeros(n, bool); dead[g.choice(n, size=int(loss * n), replace=False)] = True
    return dead


def store(arm, fo, ff, fv):
    codes = CODES[arm["codes"]]
    R = roles(fo, ff, arm["rooms"])
    w = writer_weights(R, ff, fv, codes) if arm["r6"] else np.ones(len(ff), np.int32)
    h = sgn(w @ bindings(R, ff, fv, codes).astype(np.int32))
    return R, codes, w, h


def score(vhat, ff, fv, acc, key):
    for fi, f in enumerate(FIELDS):
        idx = np.where(ff == fi)[0]
        a = acc.setdefault(key, {}).setdefault(f, [0, 0, 0.0])
        a[0] += int((vhat[idx] == fv[idx]).sum()); a[1] += len(idx)
        a[2] += float(np.abs(vhat[idx] - fv[idx]).sum())


# ------------------------------------------------------------------------------------------------ grey (F)
LM = (0.9816, 0.4528, 1.510)       # Lloyd-Max 4-level Gaussian quantiser: threshold, inner level, outer level


def grey_run(fo, ff, fv, dead):
    n = D // 2
    R = roles(fo, ff, False, n)
    S = (bindings(R, ff, fv, RAND, n).astype(np.int32)).sum(0).astype(np.float32)
    s = S.std()
    qv = np.where(np.abs(S) < LM[0] * s, LM[1], LM[2]) * np.sign(S + 1e-9)
    qv[dead] = 0
    vhat = np.zeros(len(ff), int)
    for fi, f in enumerate(FIELDS):
        idx = np.where(ff == fi)[0]
        vhat[idx] = ((qv[None, :] * R[idx]) @ RAND[f][:, :n].T.astype(np.float32)).argmax(1)
    return vhat


# ------------------------------------------------------------------------------------------------ JSON baseline
def json_run(state, seed, loss):
    keys = sorted(state)
    parts, spans, pos = [], [], 1
    for i, k in enumerate(keys):
        tok = json.dumps(k) + ":" + json.dumps(state[k])
        spans.append((pos, pos + len(tok))); parts.append(tok); pos += len(tok) + 1
    text = "{" + ",".join(parts) + "}"
    g = np.random.default_rng([seed, int(round(loss * 100)), 99])
    dead = np.zeros(len(text), bool); dead[g.choice(len(text), size=int(loss * len(text)), replace=False)] = True
    right = 0
    for (a, b), k in zip(spans, keys):
        if not dead[a:b].any():
            right += 1
        else:
            f = k.split(".")[1]
            right += int(g.integers(len(VALUES[f]))) == VALUES[f].index(state[k])
    return right, len(keys), len(text.encode())


def main():
    from k1_k2_t2 import t2
    out = {"prereg_sha256": "cae47165cdca2330c7e46caf7f667af1199db4b32a5698aab512cd430ae3e005"}
    stored = json.load(open(os.path.join(HERE, "RESULTS_K1_K2_T2.json")))["T2"]["accuracy_by_loss"]
    rep = t2()["accuracy_by_loss"]
    out["P1_reproduction"] = {"stored": stored, "rerun": rep, "exact": stored == rep}
    print("P1", out["P1_reproduction"], flush=True)

    single, cyc, wrong = {}, {}, {}
    jr = {l: [0, 0] for l in LOSSES}; jbytes = 0; passes_used = {}
    for seed in SEEDS:
        state = SC.make_task(seed)["init"]
        fo, ff, fv = facts_of(state)
        for l in LOSSES:
            r, t, nb = json_run(state, seed, l); jr[l][0] += r; jr[l][1] += t
            score(grey_run(fo, ff, fv, damage(seed, l, 0, D // 2)), ff, fv, single, f"F|{l}")
        jbytes += nb
        for name, arm in ARMS.items():
            R, codes, w, h = store(arm, fo, ff, fv)
            for l in LOSSES:                                             # single damage
                alive = ~damage(seed, l, 0)
                v, _, used = read(arm, h, alive, R, ff, codes, w)
                score(v, ff, fv, single, f"{name}|{l}")
                passes_used.setdefault(name, []).append(used)
            hc = h.copy(); dead = np.zeros(D, bool)                      # repeated damage: 5 x fresh 30 %
            for rnd in range(1, 6):
                dead |= damage(seed, 0.3, rnd)
                v, wr, _ = read(arm, hc, ~dead, R, ff, codes, w)
                score(v, ff, fv, cyc, f"{name}|{rnd}")
                if arm["heal"]:
                    rec = sgn(wr @ bindings(R, ff, v, codes).astype(np.int32))
                    wb = wrong.setdefault(f"{name}|{rnd}", [0, 0])
                    wb[0] += int((rec[dead] != h[dead]).sum()); wb[1] += int(dead.sum())
                    hc[dead] = rec[dead]; dead[:] = False
        print("scene", seed, "done", flush=True)

    def summarise(acc):
        res = {}
        for key, per in acc.items():
            tot = sum(p[0] for p in per.values()) / sum(p[1] for p in per.values())
            res[key] = {"exact": round(tot, 5), **{f: round(p[0] / p[1], 5) for f, p in per.items()},
                        "mae_ordered": round(sum(per[f][2] for f in ORDERED) / sum(per[f][1] for f in ORDERED), 4)}
        return res
    out["single"] = summarise(single)
    out["cycles"] = summarise(cyc)
    out["wrong_writebacks"] = {k: round(a / b, 5) if b else None for k, (a, b) in wrong.items()}
    out["json"] = {str(l): round(a / b, 5) for l, (a, b) in jr.items()}
    out["chance"] = round(sum(len(VALUES[f]) ** -1 for f in FIELDS) / len(FIELDS), 5)
    out["bytes_ratio"] = round((D // 8) * len(SEEDS) / jbytes, 4)
    out["passes_used_mean"] = {k: round(float(np.mean(v)), 3) for k, v in passes_used.items()}
    json.dump(out, open(os.path.join(HERE, "RESULTS_T2B.json"), "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("json", "chance", "bytes_ratio", "passes_used_mean")}))


if __name__ == "__main__":
    main()
