"""PARTNERS3: road 10, the pair test with the two fixes (owner, 23 Nov 2026 ~11:54). Layer 2. Development.
Written ~12:00 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius) after PARTNERS1 (diag/QUICK_PARTNERS1.md),
BEFORE any PARTNERS3 run. PARTNERS1/PARTNERS2 checks are not changed.

PART K LINE (Part K, row "Road 10"): where = organism -> system of organisms; missing = relations between organisms not
built (U166 spheres and tubes); structure = spheres and tubes: organisms share one pool of candidates and traces, P4
joint choice, Law 5; check = the joined organisms > each alone and > the same organisms without tubes (+ K.4 (b), (c)).

HOST: partners2.Sys with n = 2 (pair of coupled twins, shades v, v+1; coupling as PARTNERS1).
FIX 1 (cheap form): ANNOUNCED ACTIONS. Each tick:
  phase 1  each organism chooses as before (its view forks the pair, partner on defaults);
  announce both phase-1 actions go into the shared pool;
  phase 2  each organism chooses again with a view whose forks put the partner on its ANNOUNCED action for this tick
           (defaults only on later ticks).
FIX 2: PER-WORLD LAW 0 GUARD. Bounds: each world's channels with both worlds on defaults from the start. An action is
  landed only if, forked with the partner's announced action to the end, NO world's channels exceed that world's own
  bound; else the organism's phase-1 action is tried the same way; else its default. P4 (one coordinate pass: each
  organism may fall back to its default if the whole rises) accepts a change only under the same per-world guard.
  Counted: proposed, refused (phase 2), refused (phase 1 fallback), P4 changes.
ARMS: joined (fix 1 + fix 2 + P4) · notubes (both organisms, own world only, partner frozen; same per-world guard on
  its own world's bound) · aloneA, aloneB (one organism with tubes, partner on defaults; per-world guard) · native.
CHECKS (fixed now; 20 bridge pairs v = 1..20 x 2 development seeds = 40 cells; pair G = mean of both worlds):
  Q1 joined > max(aloneA, aloneB) in >= 90 % of cells;
  Q2 joined > notubes in >= 90 % of cells;
  Q3 the pair's worst channels under joined not worse than under notubes in >= 90 % of cells;
  Q4 (K.4 b) G_A(joined) >= G_A(aloneA) and G_B(joined) >= G_B(aloneB) in every cell (no tolerance);
  Q5 (K.4 c) no landed action leaves a world's projected channels above its bound (counted every tick).
COMMON RANDOMNESS: deciding (defaults' tie-breaks inside the organisms) draws from the world's generator; before
  every projection and before the real tick the worlds' generators are restored to their state at the start of the
  tick, so decisions never change the world's own events, the bound run is reproduced exactly by the native arm, and
  all arms meet the same events (found in the smoke test: without it the native arm's projection differed from its
  own bound). Default actions (in forks and in the real run) draw their tie-breaks from a copy of the generator.
Development seeds: 6520, 6521 (B: seed + 500). Never used elsewhere; never for colours.
Smoke test before the run: 4-tick worlds on throwaway seed 6499, pair (3,4), not kept: all arms 0.9969, 0 refusals.
Usage: python partners3.py run <part 0|1> ; python partners3.py analyze"""
import sys, os, json, glob, copy, time
import numpy as np
import partners2 as P2
L4, G, O, NV = P2.L4, P2.G, P2.O, P2.NV
SEEDS = [6520, 6521]; ARMS = ["joined", "notubes", "aloneA", "aloneB", "native"]
Sys = P2.Sys
_dact0 = P2.dact
def dact(w):
    """the default action without consuming the world's generator (tie-breaks drawn from a copy)."""
    r = copy.deepcopy(w.rng); a = _dact0(w); w.rng = r; return a
P2.dact = dact   # partners2.to_end's forks use it too

class View(P2.View):
    """partners2.View plus the partner's announced action on the current tick of a fork."""
    def __init__(s, S, k, tubes, announced=None):
        super().__init__(S, k, tubes); object.__setattr__(s, "_ann", announced); object.__setattr__(s, "_t0", S.t)
    def tick(s, ps, pd, glob=False):
        S, k = s._S, s._k
        if s._tubes:
            acts = [dact(w) for w in S.w]
            if s._ann is not None and S.t == s._t0: acts[1 - k] = s._ann
            acts[k] = (ps, pd, dict(S.w[k].ms), dict(S.w[k].md)); S.tick(acts)
        else: S.tick_one(k, ps, pd, s._frozen)

def run_pair(v, sd, arm):
    S = Sys(2, v, sd); sts = [L4.st_of(u) for u in S.vs]
    B = P2.to_end(S, [dact(w) for w in S.w]); bound = [w.channels() for w in B.w]
    R0 = [None, None]
    def keep(): R0[0], R0[1] = copy.deepcopy(S.w[0].rng), copy.deepcopy(S.w[1].rng)
    def restore(): S.w[0].rng, S.w[1].rng = copy.deepcopy(R0[0]), copy.deepcopy(R0[1])
    def proj(acts): restore(); return P2.to_end(S, acts)
    above = lambda f, ks=(0, 1): any(any(a > b for a, b in zip(f.w[j].channels(), bound[j])) for j in ks)
    ev = {"proposed": 0, "refused_p2": 0, "fallback_p1": 0, "refused_both": 0, "p4": 0, "landed_above": 0}
    while S.t < O.T:
        keep()
        org = [arm in ("joined", "notubes") or (arm == "aloneA" and k == 0) or (arm == "aloneB" and k == 1) for k in (0, 1)]
        d = [dact(w) for w in S.w]; acts = list(d)
        tubes = arm != "notubes"
        p1 = [L4.step(View(S, k, tubes), S.p[k], sts[k]) if org[k] else d[k] for k in (0, 1)]
        if arm == "joined": p2 = [L4.step(View(S, k, True, p1[1 - k]), S.p[k], sts[k]) for k in (0, 1)]
        else: p2 = p1
        for k in (0, 1):
            if not org[k]: continue
            other = p1[1 - k] if arm == "joined" else d[1 - k]
            ks = (0, 1) if tubes else (k,)
            def ok(a):
                tr = [None, None]; tr[k] = a; tr[1 - k] = other
                return not above(proj(tr), ks)
            ev["proposed"] += 1
            if ok(p2[k]): acts[k] = p2[k]
            else:
                ev["refused_p2"] += 1
                if p2[k] is not p1[k] and ok(p1[k]): acts[k] = p1[k]; ev["fallback_p1"] += 1
                else: acts[k] = d[k]; ev["refused_both"] += 1
        if arm == "joined":
            gc = proj(acts).G()
            for k in (0, 1):
                if acts[k] is d[k]: continue
                tr = list(acts); tr[k] = d[k]; f = proj(tr)
                if f.G() > gc + 1e-12 and not above(f): acts, gc = tr, f.G(); ev["p4"] += 1
        ev["landed_above"] += above(proj(acts))
        restore(); S.tick(acts)
    return {"G": S.G(), "Gk": [float(w.G()) for w in S.w], "ch": [float(x) for x in S.channels()], "ev": ev}

def run(part):
    out = []
    for v in range(1, NV):
        if v % 2 != part: continue
        for sd in SEEDS:
            r = {"v": v, "sd": sd}
            for a in ARMS: t0 = time.time(); r[a] = run_pair(v, sd, a); r[a]["sec"] = round(time.time() - t0)
            out.append(r); print("pair", v, sd, {a: r[a]["sec"] for a in ARMS}, flush=True)
            json.dump(out, open(f"diag/partners3_p{part}.json", "w"))

def analyze():
    R = []
    for f in sorted(glob.glob("diag/partners3_p*.json")): R += json.load(open(f))
    n = len(R); A = lambda r, a: r[a]["G"]
    S = {"cells": n,
         "Q1_joined_gt_best_alone": sum(A(r, "joined") > max(A(r, "aloneA"), A(r, "aloneB")) for r in R),
         "Q2_joined_gt_notubes": sum(A(r, "joined") > A(r, "notubes") for r in R),
         "Q3_channels_not_worse": sum(all(a <= b for a, b in zip(r["joined"]["ch"], r["notubes"]["ch"])) for r in R),
         "Q4_each_not_worse_than_alone": sum(r["joined"]["Gk"][0] >= r["aloneA"]["Gk"][0] and r["joined"]["Gk"][1] >= r["aloneB"]["Gk"][1] for r in R),
         "Q5_landed_above_bound_ticks": sum(r[a]["ev"]["landed_above"] for r in R for a in ARMS),
         "mean_G": {a: float(np.mean([A(r, a) for r in R])) for a in ARMS},
         "mean_gain_joined_minus_notubes": float(np.mean([A(r, "joined") - A(r, "notubes") for r in R])),
         "events_joined": {q: sum(r["joined"]["ev"][q] for r in R) for q in R[0]["joined"]["ev"]}}
    S["PASS"] = {"Q1": S["Q1_joined_gt_best_alone"] >= 0.9 * n, "Q2": S["Q2_joined_gt_notubes"] >= 0.9 * n,
                 "Q3": S["Q3_channels_not_worse"] >= 0.9 * n, "Q4": S["Q4_each_not_worse_than_alone"] == n, "Q5": S["Q5_landed_above_bound_ticks"] == 0}
    S["ROW_PASS"] = all(S["PASS"].values()); json.dump(S, open("diag/QUICK_PARTNERS3.json", "w"), indent=1); print(json.dumps(S, indent=1))

if __name__ == "__main__":
    if sys.argv[1] == "run": run(int(sys.argv[2]))
    else: analyze()
