"""PARTNERS2: road 10, systems of 1, 2, 4, 8 connected organisms (layer 2). Checks from map Part K.4 (owner, 23 Nov
2026 ~08:17), written and pushed (0b9af94) BEFORE the PARTNERS1 pair results were read and before any PARTNERS2 run.
Written ~08:55 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius).

PART K LINE (Part K, row "Road 10"): where = organism -> system of organisms; missing = relations between organisms not
built (U166 spheres and tubes); structure = spheres and tubes: organisms share one pool of candidates and traces, P4
joint choice, Law 5 (relations raise the limit); check = the joined organisms > each alone and > the same organisms
without tubes. PARTNERS2 adds the K.4 checks (a), (b), (c).

HOST: n twin worlds, shades v, v+1, ..., v+n-1 (wrapping 21 -> 1), structure seeds sd + 500 k, each with its own
organism v3 (laws4.step) and budget. Ring coupling, unit to unit: world k's drift hazard x (1 + mean drift of the same
unit in its ring neighbours), capped 0.5; consumption x (1 + 0.25 x mean dryness of that unit in the neighbours).
For n = 2 this equals PARTNERS1's coupling. n = 1: no coupling.
ARMS: joined (tubes: each organism forks the whole system, its picks with every other world on its defaults, and scores
the system's mean G, channels = the worst world's; then P4 as one coordinate pass: each organism in turn falls back
to its default if that raises the projected whole with channels not worse than all-defaults) · notubes (each organism
reads only its own world, neighbours frozen; no P4) · alone_k (organism k with tubes; every other world on defaults).
LAW 0 MEMBRANE on every transfer (all organism arms): a transfer = an organism's chosen action, and the joint action
after P4. Before it lands the system is forked with it (others on defaults) to the end; it is refused if any world's
projected channels exceed that world's unhealed bound (all worlds on defaults from the start), and replaced by the
default action (for the joint action: by the actions that passed individually). Counted in joined: proposed, refused,
would-harm (a partner world's projected G lower than with the organism's default action, or a channel above its
bound), and refused AND would-harm.
CHECKS (K.4, quick test, fixed): cells = starts v in {1, 5, 9, 13, 17} x 2 development seeds = 10 per n.
  (a) gain(n) = mean per-world G joined - notubes (gain(1) = 0): mean gain(1) < gain(2) < gain(4) < gain(8), and the
      sequence increasing in >= 2/3 of the 10 start x seed cells.
  (b) G_k(joined) >= G_k(alone_k) for every organism in every cell, n >= 2 (no tolerance).
  (c) 100 % of landed transfers passed the membrane; no landed transfer has a receiver channel above its bound.
  Also reported: the K line's check per n (joined > max_k alone_k system G; joined > notubes).
Development seeds: 6510, 6511 (never used elsewhere; never for colours). PARTNERS1 = development only.
Before the run: pipeline smoke test with 4-tick worlds (PARTNERS_SMOKE_T=4), one cell per n, deleted, not used.
Cost estimate from it: n = 8 about 40 min per cell, n = 4 about 11 min, n = 2 about 4 min (about 10 CPU-hours in all).
Usage: python partners2.py run <n> <part 0..k-1> <k> ; python partners2.py analyze"""
import sys, os, json, glob, copy, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "laws"))
import laws as L, laws4 as L4
os.chdir(HERE)
G, O = L.G, L.O; NV = L.NV; SEEDS = [6510, 6511]; STARTS = [1, 5, 9, 13, 17]; NS = [1, 2, 4, 8]
if os.environ.get("PARTNERS_SMOKE_T"): O.T = int(os.environ["PARTNERS_SMOKE_T"])   # pipeline smoke only
shade = lambda v, k: (v - 1 + k) % NV + 1

def dact(w):
    ds, dd = O.defaults(w); return ds, dd, {i: "inside" for i in ds}, {j: "inside" for j in dd}

class Sys:
    def __init__(s, n, v, sd):
        s.n = n; s.vs = [shade(v, k) for k in range(n)]; s.p = [G.params(G.SH["shades"][u - 1]["node"], u) for u in s.vs]
        s.w = [G.Shade(sd + 500 * k, s.p[k], "inside") for k in range(n)]
        s.h0 = [w.h.copy() for w in s.w]; s.c00 = [w.c0.copy() for w in s.w]
    def nb(s, k): return [] if s.n == 1 else sorted({(k - 1) % s.n, (k + 1) % s.n} - {k})
    def tick_one(s, k, ps, pd, st):
        w = s.w[k]; nb = s.nb(k)
        if nb:
            dr = np.mean([st[j][0] for j in nb], 0); dry = np.mean([st[j][1] for j in nb], 0)
            w.h = np.minimum(s.h0[k] * (1 + dr), 0.5); w.c0 = s.c00[k] * (1 + 0.25 * dry)
        G.Shade.tick(w, ps, pd); w.h, w.c0 = s.h0[k], s.c00[k]
    def state(s): return [(w.dr.astype(float), (w.res <= 0).astype(float)) for w in s.w]
    def tick(s, acts):
        st = s.state()
        for k in range(s.n):
            ps, pd, ms, md = acts[k]; s.w[k].ms, s.w[k].md = ms, md; s.tick_one(k, ps, pd, st)
    def G(s): return float(np.mean([w.G() for w in s.w]))
    def channels(s): return tuple(max(w.channels()[i] for w in s.w) for i in (0, 1))
    @property
    def t(s): return s.w[0].t

def to_end(S, acts):
    f = copy.deepcopy(S); f.tick(acts)
    while f.t < O.T: f.tick([dact(w) for w in f.w])
    return f

class View:
    def __init__(s, S, k, tubes):
        object.__setattr__(s, "_S", S); object.__setattr__(s, "_k", k); object.__setattr__(s, "_tubes", tubes)
        object.__setattr__(s, "_frozen", S.state())
    def __getattr__(s, a):
        if a.startswith("_"): raise AttributeError(a)
        return getattr(s._S.w[s._k], a)
    def __setattr__(s, a, v): setattr(s._S.w[s._k], a, v)
    def tick(s, ps, pd, glob=False):
        S, k = s._S, s._k
        if s._tubes:
            acts = [dact(w) for w in S.w]; acts[k] = (ps, pd, dict(S.w[k].ms), dict(S.w[k].md)); S.tick(acts)
        else: S.tick_one(k, ps, pd, s._frozen)
    def G(s): return s._S.G() if s._tubes else s._S.w[s._k].G()
    def channels(s): return s._S.channels() if s._tubes else s._S.w[s._k].channels()

def run_sys(n, v, sd, arm, ka=None):
    S = Sys(n, v, sd); sts = [L4.st_of(u) for u in S.vs]
    B = to_end(S, [dact(w) for w in S.w]); bound = [w.channels() for w in B.w]
    ev = {"proposed": 0, "refused": 0, "would_harm": 0, "refused_and_harm": 0, "landed_above_bound": 0, "landed_unchecked": 0, "p4_changed": 0}
    above = lambda f: any(any(a > b for a, b in zip(f.w[j].channels(), bound[j])) for j in range(n))
    while S.t < O.T:
        acts = [dact(w) for w in S.w]; base = to_end(S, acts); checked = [True] * n
        for k in range(n):
            org = arm in ("joined", "notubes") or (arm == "alone" and k == ka)
            if not org: continue
            a = L4.step(View(S, k, arm != "notubes"), S.p[k], sts[k])
            trial = list(acts); trial[k] = a; f = to_end(S, trial); ev["proposed"] += 1
            ref = above(f); harm = ref or any(f.w[j].G() < base.w[j].G() - 1e-12 for j in range(n) if j != k)
            ev["refused"] += ref; ev["would_harm"] += harm; ev["refused_and_harm"] += ref and harm
            if not ref: acts[k] = a
        if arm == "joined" and n > 1:
            g0, c0 = base.G(), base.channels(); cur = list(acts); gc = to_end(S, cur).G()
            for k in range(n):
                if cur[k] is acts[k] and acts[k] != dact(S.w[k]):
                    tr = list(cur); tr[k] = dact(S.w[k]); f = to_end(S, tr)
                    if f.G() > gc + 1e-12 and all(x <= y for x, y in zip(f.channels(), c0)): cur, gc = tr, f.G(); ev["p4_changed"] += 1
            f = to_end(S, cur); ev["proposed"] += 1
            if above(f): ev["refused"] += 1
            else: acts = cur
        fl = to_end(S, acts); ev["landed_above_bound"] += above(fl)
        S.tick(acts)
    return {"G": S.G(), "Gk": [float(w.G()) for w in S.w], "ch": [float(x) for x in S.channels()], "ev": ev}

def run(n, part, k):
    cells = [(v, sd) for v in STARTS for sd in SEEDS]; out = []
    for i, (v, sd) in enumerate(cells):
        if i % k != part: continue
        t0 = time.time(); r = {"n": n, "v": v, "sd": sd, "joined": run_sys(n, v, sd, "joined")}
        r["notubes"] = r["joined"] if n == 1 else run_sys(n, v, sd, "notubes")
        r["alone"] = [r["joined"]] if n == 1 else [run_sys(n, v, sd, "alone", ka) for ka in range(n)]
        r["sec"] = round(time.time() - t0); out.append(r); print("n", n, "cell", v, sd, round(r["joined"]["G"], 4), r["sec"], "s", flush=True)
        json.dump(out, open(f"diag/partners2_n{n}_p{part}.json", "w"))

def analyze():
    R = {}
    for f in glob.glob("diag/partners2_n*_p*.json"):
        for r in json.load(open(f)): R[(r["n"], r["v"], r["sd"])] = r
    cells = [(v, sd) for v in STARTS for sd in SEEDS]
    gain = {n: {c: (R[(n,) + c]["joined"]["G"] - R[(n,) + c]["notubes"]["G"]) if n > 1 else 0.0 for c in cells if (n,) + c in R} for n in NS}
    mg = {n: float(np.mean(list(gain[n].values()))) for n in NS}
    inc = sum(all(gain[a][c] < gain[b][c] for a, b in zip(NS, NS[1:])) for c in cells if all(c in gain[n] for n in NS))
    b_ok = b_tot = 0; ev = {}; kline = {}
    for (n, v, sd), r in R.items():
        if n > 1:
            for k in range(n): b_tot += 1; b_ok += r["joined"]["Gk"][k] >= r["alone"][k]["Gk"][k]
            kline.setdefault(n, [0, 0, 0]); kline[n][0] += r["joined"]["G"] > max(a["G"] for a in r["alone"]); kline[n][1] += r["joined"]["G"] > r["notubes"]["G"]; kline[n][2] += 1
        for q, x in r["joined"]["ev"].items(): ev.setdefault(n, {}).setdefault(q, 0); ev[n][q] += x
    landed_ok = all(e["landed_above_bound"] == 0 for e in ev.values())
    S = {"mean_gain": mg, "a_increasing_cells": [inc, len(cells)], "b_organisms_not_worse": [b_ok, b_tot], "c_events_joined": ev,
         "K_line_joined_gt_best_alone_and_gt_notubes": {n: {"gt_alone": x[0], "gt_notubes": x[1], "cells": x[2]} for n, x in kline.items()}}
    S["PASS"] = {"a": all(mg[a] < mg[b] for a, b in zip(NS, NS[1:])) and inc >= 2 * len(cells) / 3, "b": b_ok == b_tot, "c": landed_ok}
    S["ROW_PASS"] = all(S["PASS"].values()); json.dump(S, open("diag/QUICK_PARTNERS2.json", "w"), indent=1, default=str); print(json.dumps(S, indent=1, default=str))

if __name__ == "__main__":
    if sys.argv[1] == "run": run(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
    else: analyze()
