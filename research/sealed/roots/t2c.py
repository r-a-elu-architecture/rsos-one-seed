"""T2c: the living hologram against today's best method (layer 2). Predictions: PREREG_T2C.md (sealed before this
file, sha256 7b2a6295b8695dd0b5da183a9fa30292cff6b56a3f0bf68139f3abdb377c4a12, commit 622e354).
Usage: python3 t2c.py run <part 0|1>   then   python3 t2c.py merge"""
import json
import os
import sys

import numpy as np
from scipy.special import ndtr

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
HERE = os.path.dirname(os.path.abspath(__file__))
import sc1_tasks as SC  # noqa: E402

D = 10_000
EPS = 0.01
SEEDS = list(range(900, 916))
ERASE = [0.0, 0.5, 0.7, 0.85, 0.9, 0.95, 0.98, 0.99]
FLIPS = [0.05, 0.1, 0.2, 0.3, 0.4]
FIELDS = list(SC.FIELDS)
VALUES = {"x": [str(i) for i in range(10)], "y": [str(i) for i in range(10)],
          "height_mm": [str(i * 100) for i in range(1, 51)], "owner": SC.ROBOTS, "room": SC.ROOMS, "on": SC.SURFACES}
WIDTH = {"x": 4, "y": 4, "height_mm": 6, "owner": 3, "room": 2, "on": 2}           # 21 bits per object
ORDERED = ("x", "y", "height_mm")
OBJ = list(SC.OBJECTS)

# ---- codebooks: identical to T2 / T2b for the first 50 objects (generator seed 7, same order)
rng = np.random.default_rng(7)
bip = lambda g=rng: g.choice(np.array([-1, 1], dtype=np.int8), size=D)
O = np.stack([bip() for _ in OBJ])
Fv = {f: bip() for f in FIELDS}
RAND = {f: np.stack([bip() for _ in VALUES[f]]) for f in FIELDS}
g13 = np.random.default_rng(13)
O_ALL = np.concatenate([O, np.stack([bip(g13) for _ in range(150)])])          # extra objects for the load test

# ---- the corrected roads (owner, 03:03): own colour, own moves, unique metres, a cube of points per metre
g11 = np.random.default_rng(11)
MOVES = [g11.permutation(D) for _ in range(4)]                                    # straight, up, down, turn
SPLIT = {"x": (5, 2), "y": (5, 2), "height_mm": (10, 5)}                          # metres x points per cube


def road(f, s):
    metres, m = SPLIT[f]
    met = [bip(g11)]
    for mv in g11.integers(4, size=metres - 1):
        met.append(met[-1][MOVES[mv]])
    pts = [bip(g11)]
    for _ in range(m - 1):
        p = pts[-1].copy(); flip = g11.random(D) < (1 - s) / 2; p[flip] *= -1; pts.append(p)
    return np.stack([met[v // m] * pts[v % m] for v in range(metres * m)])


ROAD50 = {f: (road(f, 0.50) if f in ORDERED else RAND[f]) for f in FIELDS}
ROAD25 = {f: (road(f, 0.25) if f in ORDERED else RAND[f]) for f in FIELDS}
CODES = {"rand": RAND, "road50": ROAD50, "road25": ROAD25}

ARMS = {
    "R5": dict(codes="rand", r6=False, heal=False, gate=False),
    "LivNR": dict(codes="rand", r6=True, heal=True, gate=False),
    "LivNRg": dict(codes="rand", r6=True, heal=True, gate=True),
    "LivRd50g": dict(codes="road50", r6=True, heal=True, gate=True),
    "LivRd25g": dict(codes="road25", r6=True, heal=True, gate=True),
}


# ------------------------------------------------------------------------------------------------ hologram
def facts(seed, mult=1):
    fo, ff, fv = [], [], []
    for t in range(mult):
        for key, val in SC.make_task(seed + 1000 * t)["init"].items():
            o, f = key.split(".")
            fo.append(OBJ.index(o) + 50 * t); ff.append(FIELDS.index(f)); fv.append(VALUES[f].index(val))
    return np.array(fo), np.array(ff), np.array(fv)


def roles(fo, ff):
    return (O_ALL[fo] * np.stack([Fv[FIELDS[i]] for i in ff])).astype(np.int8)


def bindings(R, ff, vals, codes):
    return R * np.stack([codes[FIELDS[f]][v] for f, v in zip(ff, vals)])


def sgn(S):
    h = np.sign(S).astype(np.int8); h[h == 0] = 1; return h


def plain_read(h, R, ff, codes):
    vhat = np.zeros(len(ff), int); gap = np.zeros(len(ff)); sup = np.zeros(len(ff))
    hf = h.astype(np.float32)
    for fi, f in enumerate(FIELDS):
        idx = np.where(ff == fi)[0]
        U = hf[None, :] * R[idx].astype(np.float32)
        sc = U @ codes[f].T.astype(np.float32)
        srt = np.sort(sc, 1)
        vhat[idx] = sc.argmax(1); gap[idx] = srt[:, -1] - srt[:, -2]; sup[idx] = (U != 0).sum(1)
    return vhat, gap, sup


def writer_weights(R, ff, vals, codes, rounds=10):
    B = bindings(R, ff, vals, codes).astype(np.int32)
    w = np.ones(len(ff), np.int32)
    for _ in range(rounds):
        hf = sgn(w @ B).astype(np.float32)
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
    Bh = bindings(R, ff, vprev, codes).astype(np.float32)
    S_hat = w.astype(np.float32) @ Bh
    vhat = np.zeros(len(ff), int)
    hp = (h == 1)[None, :]
    for fi, f in enumerate(FIELDS):
        idx = np.where(ff == fi)[0]
        wk = w[idx].astype(np.float32)[:, None]
        Rh = S_hat[None, :] - wk * Bh[idx]
        p_pos = EPS + (1 - 2 * EPS) * ndtr((Rh + wk + 0.5) / sigma)     # P(h=+1 | b=+1), robust
        p_neg = EPS + (1 - 2 * EPS) * ndtr((Rh - wk + 0.5) / sigma)     # P(h=+1 | b=-1), robust
        delta = np.where(hp, np.log(p_pos) - np.log(p_neg), np.log1p(-p_pos) - np.log1p(-p_neg)) * alive[None, :]
        vhat[idx] = ((delta * R[idx].astype(np.float32)) @ codes[f].T.astype(np.float32)).argmax(1)
    return vhat


def holo_read(arm, h, alive, R, ff, codes):
    """Returns values, reconstruction weights, and whether the structure held still (gate)."""
    hd = h * alive.astype(np.int8)
    v, gap, sup = plain_read(hd, R, ff, codes)
    n_low = int((gap < 2 * np.sqrt(np.maximum(sup, 1))).sum())
    held = arm["gate"] and n_low > 0.5 * len(ff)
    use_w = arm["r6"] and not held
    sigma = np.sqrt(2 * n_low + 1)
    ones = np.ones(len(ff), np.int32)
    for _ in range(4):                                         # up to 5 passes in total
        w = writer_weights(R, ff, v, codes) if use_w else ones
        vn = explain_read(hd, alive.astype(np.float32), R, ff, codes, v, w, sigma)
        if np.array_equal(vn, v):
            break
        v = vn
    w = writer_weights(R, ff, v, codes) if use_w else ones
    return v, w, held


def holo_store(arm, fo, ff, fv):
    codes = CODES[arm["codes"]]
    R = roles(fo, ff)
    w = writer_weights(R, ff, fv, codes) if arm["r6"] else np.ones(len(ff), np.int32)
    return R, codes, sgn(w @ bindings(R, ff, fv, codes).astype(np.int32))


# ------------------------------------------------------------------------------------------------ classic codes
def payload(fo, ff, fv, nobj):
    bits = np.zeros(nobj * 21, np.uint8)
    off = {}; o = 0
    for f in FIELDS:
        off[f] = o; o += WIDTH[f]
    for ob, fi, v in zip(fo, ff, fv):
        f = FIELDS[fi]; base = ob * 21 + off[f]
        for b in range(WIDTH[f]):
            bits[base + b] = (v >> (WIDTH[f] - 1 - b)) & 1
    return bits, off


def unpayload(bits, known, fo, ff, off, grng):
    vals = np.zeros(len(fo), int)
    for k, (ob, fi) in enumerate(zip(fo, ff)):
        f = FIELDS[fi]; base = ob * 21 + off[f]; seg = slice(base, base + WIDTH[f])
        if known[seg].all():
            v = 0
            for b in bits[seg]:
                v = (v << 1) | int(b)
            vals[k] = v
        else:
            vals[k] = int(grng.integers(len(VALUES[f])))
    return vals


GEN = {}


def generator(k):
    if k not in GEN:
        GEN[k] = np.random.default_rng(17 + k).integers(0, 2, size=(k, D), dtype=np.uint8)
    return GEN[k]


def classic_encode(d):
    return ((d.astype(np.int32) @ generator(len(d)).astype(np.int32)) & 1).astype(np.uint8)


def classic_decode(c, alive, k, grng):
    """Gauss-Jordan over GF(2) on surviving bits. Returns bits and which are determined."""
    G = generator(k)
    surv = np.where(alive)[0]
    if len(surv) > k + 300:
        surv = np.sort(grng.choice(surv, size=k + 300, replace=False))
    A = np.concatenate([G[:, surv].T, c[surv][:, None]], 1).astype(np.uint8)        # rows x (k+1)
    nb = A.shape[1]
    P = np.packbits(A, axis=1)
    pad = (-P.shape[1]) % 8
    P = np.ascontiguousarray(np.pad(P, ((0, 0), (0, pad)))).view(np.uint64)
    Pb = P.view(np.uint8)
    rows = P.shape[0]; rank = 0; pivcol = []
    for col in range(k):
        if rank == rows:
            break
        colbits = (Pb[:, col // 8] >> (7 - col % 8)) & 1
        cand = np.where(colbits[rank:] == 1)[0]
        if len(cand) == 0:
            continue
        r = rank + cand[0]
        if r != rank:
            P[[rank, r]] = P[[r, rank]]
            colbits[[rank, r]] = colbits[[r, rank]]
        hit = np.where(colbits == 1)[0]; hit = hit[hit != rank]
        P[hit] ^= P[rank]
        pivcol.append(col); rank += 1
    R = np.unpackbits(P.view(np.uint8), axis=1)[:, :nb]
    bits = np.zeros(k, np.uint8); known = np.zeros(k, bool)
    free = np.ones(k, bool); free[pivcol] = False
    for i, col in enumerate(pivcol):
        if not R[i, :k][free].any():
            bits[col] = R[i, k]; known[col] = True
    return bits, known


def repetition_store(d):
    perm = np.random.default_rng(19).permutation(D)
    c = np.zeros(D, np.uint8); c[perm] = d[np.arange(D) % len(d)]
    return c, perm


def repetition_read(c, perm, k, grng):
    owner = np.arange(D) % k
    ones = np.bincount(owner, weights=c[perm].astype(float), minlength=k)
    cnt = np.bincount(owner, minlength=k)
    bits = (ones * 2 > cnt).astype(np.uint8)
    tie = ones * 2 == cnt
    bits[tie] = grng.integers(0, 2, size=tie.sum())
    return bits, np.ones(k, bool)


# ------------------------------------------------------------------------------------------------ run
def erase(seed, loss, rnd, tag=0):
    g = np.random.default_rng([seed, int(round(loss * 100)), rnd, tag])
    dead = np.zeros(D, bool); dead[g.choice(D, size=int(round(loss * D)), replace=False)] = True
    return dead


def add(acc, key, v, ff, fv):
    for fi, f in enumerate(FIELDS):
        idx = np.where(ff == fi)[0]
        a = acc.setdefault(key, {}).setdefault(f, [0, 0, 0.0])
        a[0] += int((v[idx] == fv[idx]).sum()); a[1] += len(idx); a[2] += float(np.abs(v[idx] - fv[idx]).sum())


def run(part):
    acc, extra = {}, {"held": {}, "wrong_wb": {}, "classic_heal_fail": 0}
    for seed in SEEDS[part::2]:
        grng = np.random.default_rng([seed, 5])
        fo, ff, fv = facts(seed)
        d, off = payload(fo, ff, fv, 50)
        cE = classic_encode(d)
        cR, perm = repetition_store(d)
        stores = {name: holo_store(arm, fo, ff, fv) for name, arm in ARMS.items()}
        for loss in ERASE:                                                  # 1. known erasures, single
            alive = ~erase(seed, loss, 0)
            for name, arm in ARMS.items():
                R, codes, h = stores[name]
                v, _, held = holo_read(arm, h, alive, R, ff, codes)
                add(acc, f"E|{name}|{loss}", v, ff, fv)
                extra["held"][f"E|{name}|{loss}"] = extra["held"].get(f"E|{name}|{loss}", 0) + int(held)
            bits, known = classic_decode(cE, alive, len(d), grng)
            add(acc, f"E|ClassicE|{loss}", unpayload(bits, known, fo, ff, off, grng), ff, fv)
        for name, arm in ARMS.items():                                      # 2. repeated damage
            R, codes, h = stores[name]; hc = h.copy(); dead = np.zeros(D, bool)
            for rnd in range(1, 11):
                dead |= erase(seed, 0.3, rnd)
                v, w, held = holo_read(arm, hc, ~dead, R, ff, codes)
                add(acc, f"C|{name}|{rnd}", v, ff, fv)
                if arm["heal"] and not held:
                    rec = sgn(w @ bindings(R, ff, v, codes).astype(np.int32))
                    wb = extra["wrong_wb"].setdefault(f"{name}|{rnd}", [0, 0])
                    wb[0] += int((rec[dead] != h[dead]).sum()); wb[1] += int(dead.sum())
                    hc[dead] = rec[dead]; dead[:] = False
        cc = cE.copy(); dead = np.zeros(D, bool)
        for rnd in range(1, 11):
            dead |= erase(seed, 0.3, rnd)
            bits, known = classic_decode(cc, ~dead, len(d), grng)
            add(acc, f"C|ClassicE|{rnd}", unpayload(bits, known, fo, ff, off, grng), ff, fv)
            if known.all():
                rec = classic_encode(bits); cc[dead] = rec[dead]; dead[:] = False
            else:
                extra["classic_heal_fail"] += 1
        for p in FLIPS:                                                     # 3. silent flips
            g = np.random.default_rng([seed, int(round(p * 100)), 77])
            fl = np.zeros(D, bool); fl[g.choice(D, size=int(round(p * D)), replace=False)] = True
            alive = np.ones(D, bool)
            for name in ("R5", "LivNRg", "LivRd50g", "LivRd25g"):
                R, codes, h = stores[name]; hf = h.copy(); hf[fl] *= -1
                v, _, held = holo_read(ARMS[name], hf, alive, R, ff, codes)
                add(acc, f"F|{name}|{p}", v, ff, fv)
            cf = cR.copy(); cf[fl] ^= 1
            bits, known = repetition_read(cf, perm, len(d), grng)
            add(acc, f"F|ClassicR|{p}", unpayload(bits, known, fo, ff, off, grng), ff, fv)
        print("scene", seed, flush=True)
    for mult in (2, 4):                                                     # 4. load
        for s in range(900 + part, 908, 2):
            grng = np.random.default_rng([s, mult, 6])
            fo, ff, fv = facts(s, mult)
            d, off = payload(fo, ff, fv, 50 * mult)
            cE = classic_encode(d)
            for loss in (0.0, 0.5):
                alive = ~erase(s, loss, 0, mult)
                for name in ("R5", "LivNRg"):
                    R, codes, h = holo_store(ARMS[name], fo, ff, fv)
                    v, _, _ = holo_read(ARMS[name], h, alive, R, ff, codes)
                    add(acc, f"L{mult}|{name}|{loss}", v, ff, fv)
                bits, known = classic_decode(cE, alive, len(d), grng)
                add(acc, f"L{mult}|ClassicE|{loss}", unpayload(bits, known, fo, ff, off, grng), ff, fv)
            print("load", mult, s, flush=True)
    json.dump({"acc": acc, "extra": extra}, open(os.path.join(HERE, f"RAW_T2C_part{part}.json"), "w"))


def merge():
    acc, held, wwb, chf = {}, {}, {}, 0
    for part in (0, 1):
        r = json.load(open(os.path.join(HERE, f"RAW_T2C_part{part}.json")))
        for key, per in r["acc"].items():
            for f, a in per.items():
                b = acc.setdefault(key, {}).setdefault(f, [0, 0, 0.0]); b[0] += a[0]; b[1] += a[1]; b[2] += a[2]
        for k, v in r["extra"]["held"].items():
            held[k] = held.get(k, 0) + v
        for k, (a, b) in r["extra"]["wrong_wb"].items():
            c = wwb.setdefault(k, [0, 0]); c[0] += a; c[1] += b
        chf += r["extra"]["classic_heal_fail"]
    res = {}
    for key, per in acc.items():
        res[key] = {"exact": round(sum(p[0] for p in per.values()) / sum(p[1] for p in per.values()), 5),
                    "height": round(per["height_mm"][0] / per["height_mm"][1], 5),
                    "mae_ordered": round(sum(per[f][2] for f in ORDERED) / sum(per[f][1] for f in ORDERED), 4)}
    out = {"prereg_sha256": "7b2a6295b8695dd0b5da183a9fa30292cff6b56a3f0bf68139f3abdb377c4a12", "results": res,
           "gate_held_count": held, "wrong_writebacks": {k: round(a / b, 5) for k, (a, b) in wwb.items() if b},
           "classic_heal_failures": chf,
           "read_cost_one_fact": {"hologram_bits_touched": D, "classic_bits_to_decode": "all 1,050 payload bits, "
                                  "Gauss-Jordan over >= 1,050 surviving bits (dense code)"}}
    json.dump(out, open(os.path.join(HERE, "RESULTS_T2C.json"), "w"), indent=1)
    return out


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(int(sys.argv[2]))
    else:
        merge()
