"""PARTNERS1: road 10, partner organisms joined by spheres and tubes (layer 2). Development build.
Written 23 Nov 2026 ~08:20 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius), before any run.

PART K LINE (map/STRUCTURAL_MAP_22NOV.md Part K, row "Road 10 · partners (partner agents, layer 2)"), copied first:
  where     : organism -> system of organisms
  missing   : relations between organisms not built (U166 spheres and tubes) (Part 0 reading)
  structure : spheres and tubes: two or more organisms share one pool of candidates and traces; P4 joint choice;
              Law 5 (relations raise the limit)
  check     : the joined organisms > each alone and > the same organisms without tubes

HOST: a pair of twin worlds, A = shade v, B = shade v+1 (each its own parameters, structure seed and budget of 4
landings per tick), coupled unit to unit (unit i of A <-> unit i of B; fixed now): a drifted unit in one world doubles
the drift hazard of the same unit in the other (capped at 0.5, as the world's own cap); a dry unit in one world raises
the consumption of the same unit in the other by 25 %. Each world ticks with the sealed tick (organism.Shade, not
edited); the coupling sets h and c0 from the partner's state before the tick and restores them after.
ORGANISM in each world: v3 (ORG6 own structure of that shade + budget-correct counter-shift; laws4.step).
SPHERES AND TUBES: the organism of a world reads the pair through a view. With tubes its forks run the WHOLE pair (its
  own picks, the partner on its defaults) and score the pair's whole (mean G of both worlds; channels = the worse of
  both): one pool of traces. Its candidates stay its own units (its budget, its world); the pool is shared through
  the scoring. P4 joint choice: after both organisms have chosen, the four joint actions {A chosen, A default} x
  {B chosen, B default} are forked jointly to the end and the best whole with channels not worse than default x
  default lands.
ARMS (same pair, same seeds): joined (tubes + P4) · notubes (both organisms; each forks only its own world with the
  partner frozen, scores only its own world; no P4) · aloneA (organism in A with tubes, B on its defaults, i.e. no
  partner organism) · aloneB (symmetric) · native (both on defaults).
CHECKS (quick test, fixed now): over the 20 bridge pairs (v, v+1), v = 1..20, x 2 development seeds = 40 cells,
  pair G = mean of both worlds' G:
  P1  joined > max(aloneA, aloneB) in >= 90 % of cells;
  P2  joined > notubes in >= 90 % of cells;
  P3  Law 0: the pair's worst channels under joined not worse than under notubes in >= 90 % of cells;
  Law 5 reading (reported): mean gain of joined over notubes (relations known to the reader raise the limit).
Development seeds: 6500, 6501 (A's structure seed; B uses seed + 500). Never used elsewhere; never for colours.
Smoke test before the run: throwaway seed 6499, pair (3,4): native 0.8431, aloneA 0.9039, joined 0.9254 (not kept).
Usage: python partners.py run <part 0|1> ; python partners.py analyze"""
import sys, os, json, glob, copy, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "laws"))
import laws as L, laws4 as L4
os.chdir(HERE)
G, O, X = L.G, L.O, L.X; NV = L.NV; SEEDS = [6500, 6501]; os.makedirs("diag", exist_ok=True)

class Pair:
    def __init__(s, v, sd):
        s.p = [G.params(G.SH["shades"][u - 1]["node"], u) for u in (v, v + 1)]
        s.w = [G.Shade(sd, s.p[0], "inside"), G.Shade(sd + 500, s.p[1], "inside")]
        s.h0 = [w.h.copy() for w in s.w]; s.c00 = [w.c0.copy() for w in s.w]
    def tick_one(s, k, ps, pd, partner_state=None):
        w = s.w[k]; o = partner_state if partner_state is not None else (s.w[1 - k].dr.copy(), s.w[1 - k].res <= 0)
        w.h = np.minimum(s.h0[k] * (1 + o[0]), 0.5); w.c0 = s.c00[k] * (1 + 0.25 * o[1])
        G.Shade.tick(w, ps, pd); w.h, w.c0 = s.h0[k], s.c00[k]
    def tick(s, acts):
        st = [(w.dr.copy(), w.res <= 0) for w in s.w]
        for k in (0, 1):
            ps, pd, ms, md = acts[k]; s.w[k].ms, s.w[k].md = ms, md; s.tick_one(k, ps, pd, st[1 - k])
    def G(s): return 0.5 * (s.w[0].G() + s.w[1].G())
    def channels(s): return tuple(max(a, b) for a, b in zip(s.w[0].channels(), s.w[1].channels()))
    @property
    def t(s): return s.w[0].t

def defaults_act(w):
    ds, dd = O.defaults(w); return ds, dd, {i: "inside" for i in ds}, {j: "inside" for j in dd}

class View:
    """what the organism of world k reads: the pair (tubes) or its own world with the partner frozen (no tubes)."""
    _own = ("_pair", "_k", "_tubes", "_frozen")
    def __init__(s, pair, k, tubes):
        object.__setattr__(s, "_pair", pair); object.__setattr__(s, "_k", k); object.__setattr__(s, "_tubes", tubes)
        object.__setattr__(s, "_frozen", (pair.w[1 - k].dr.copy(), pair.w[1 - k].res <= 0))
    def __getattr__(s, a):
        if a.startswith("_"): raise AttributeError(a)
        return getattr(s._pair.w[s._k], a)
    def __setattr__(s, a, v): setattr(s._pair.w[s._k], a, v)
    def tick(s, ps, pd, glob=False):
        P, k = s._pair, s._k
        if s._tubes:
            me = (ps, pd, dict(P.w[k].ms), dict(P.w[k].md)); other = defaults_act(P.w[1 - k])
            P.tick([me, other] if k == 0 else [other, me])
        else: P.tick_one(k, ps, pd, s._frozen)
    def G(s): return s._pair.G() if s._tubes else s._pair.w[s._k].G()
    def channels(s): return s._pair.channels() if s._tubes else s._pair.w[s._k].channels()

def st_of(v): return L4.st_of(v)

def fork_end(P, acts):
    f = copy.deepcopy(P); f.tick(acts)
    while f.t < O.T: f.tick([defaults_act(f.w[0]), defaults_act(f.w[1])])
    return f.G(), f.channels()

def run_pair(v, sd, arm):
    P = Pair(v, sd); sts = [st_of(v), st_of(v + 1)]; p4 = 0
    while P.t < O.T:
        acts = []
        for k in (0, 1):
            org = arm in ("joined", "notubes") or (arm == "aloneA" and k == 0) or (arm == "aloneB" and k == 1)
            if not org: acts.append(defaults_act(P.w[k])); continue
            V = View(P, k, arm != "notubes"); acts.append(L4.step(V, P.p[k], sts[k]))
        if arm == "joined":
            dA, dB = defaults_act(P.w[0]), defaults_act(P.w[1]); g0, c0 = fork_end(P, [dA, dB]); best = None
            for a in (acts[0], dA):
                for b in (acts[1], dB):
                    g, c = fork_end(P, [a, b])
                    if all(x <= y for x, y in zip(c, c0)) and (best is None or g > best[0] + 1e-12): best = (g, [a, b])
            if best is not None:
                p4 += best[1] != acts; acts = best[1]
        P.tick(acts)
    return {"G": float(P.G()), "GA": float(P.w[0].G()), "GB": float(P.w[1].G()), "ch": [float(x) for x in P.channels()], "p4_changed": int(p4)}

ARMS = ["joined", "notubes", "aloneA", "aloneB", "native"]

def run(part):
    out = []
    for v in range(1, NV):
        if v % 2 != part: continue
        for sd in SEEDS:
            r = {"v": v, "sd": sd}
            for a in ARMS: t0 = time.time(); r[a] = run_pair(v, sd, a); r[a]["sec"] = round(time.time() - t0)
            out.append(r); print("pair", v, sd, {a: round(r[a]["G"], 4) for a in ARMS}, flush=True)
            json.dump(out, open(f"diag/partners1_p{part}.json", "w"))

def analyze():
    R = []
    for f in sorted(glob.glob("diag/partners1_p*.json")): R += json.load(open(f))
    n = len(R); p1 = sum(r["joined"]["G"] > max(r["aloneA"]["G"], r["aloneB"]["G"]) for r in R)
    p2 = sum(r["joined"]["G"] > r["notubes"]["G"] for r in R)
    p3 = sum(all(a <= b for a, b in zip(r["joined"]["ch"], r["notubes"]["ch"])) for r in R)
    S = {"cells": n, "P1_joined_gt_each_alone": p1, "P2_joined_gt_notubes": p2, "P3_channels_not_worse": p3,
         "mean_G": {a: float(np.mean([r[a]["G"] for r in R])) for a in ARMS},
         "Law5_mean_gain_joined_minus_notubes": float(np.mean([r["joined"]["G"] - r["notubes"]["G"] for r in R])),
         "mean_gain_joined_minus_best_alone": float(np.mean([r["joined"]["G"] - max(r["aloneA"]["G"], r["aloneB"]["G"]) for r in R])),
         "p4_changed_ticks_mean": float(np.mean([r["joined"]["p4_changed"] for r in R]))}
    S["PASS"] = {"P1": p1 >= 0.9 * n, "P2": p2 >= 0.9 * n, "P3": p3 >= 0.9 * n}; S["ROW_PASS"] = all(S["PASS"].values())
    json.dump(S, open("diag/QUICK_PARTNERS1.json", "w"), indent=1); print(json.dumps(S, indent=1))

if __name__ == "__main__":
    if sys.argv[1] == "run": run(int(sys.argv[2]))
    else: analyze()
