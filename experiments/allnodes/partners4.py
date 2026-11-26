"""PARTNERS4: road 10 built exactly as map Part K.6 (owner OK 23 Nov 2026 ~13:19: shared pool, total 4n). Layer 2.
Development quick test. Written ~13:45 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius), before any run.

PART K LINE (Part K, row "Road 10"): where = organism -> system of organisms; missing = relations between organisms not
built (U166 spheres and tubes); structure = spheres and tubes: organisms share one pool of candidates and traces, P4
joint choice, Law 5; check = the joined organisms > each alone and > the same organisms without tubes (+ K.4).
STRUCTURE (K.6), in program order each tick of the joined arm:
  1 reading the partner : PARTNERS3 phase 1 + announced actions + phase 2 (each organism chooses for its world).
  2 the host (pool)     : one pool of 4n landings per tick for the system (conserved; worlds have no private budget).
  3 allocation          : the pool's candidates = every proposed landing + the 2 highest-lack units per side of every
                          world not proposed. Need is measured in the SYSTEM'S OWN FUTURE by the cheap replay with
                          common randomness (K.5): one closed-loop future of the joint proposal records every world's
                          later actions (each organism's own step on its own world, its partners frozen per tick - the
                          affordable form of the own policy), ONCE per tick; every branch (removal, candidate, final
                          re-check) replays that plan open-loop. A proposed
                          landing without need frees its particle into the pool; a freed particle goes to the candidate
                          (any world) whose landing raises the replayed whole most (particles land at the places of need).
  4 joint choice (P4)   : the freed particles are allocated jointly, best gain first, one candidate per particle; a
                          candidate in a world that has given more particles than it received (debt > 0) is preferred
                          when its gain is positive (repayment, time-sharing, P2).
  5 the donor           : every transfer (a particle moving from world i to world j) passes the per-world Law 0
                          membrane: the system forked with the new joint action (common randomness, defaults after) to
                          the end; refused if any world's projected channels exceed that world's bound (all worlds on
                          defaults from the start); a refused transfer returns the particle to its world's proposal.
                          Envelope per transfer: from, to, unit, side, gain (effect), harm check (invariant), tick.
  Then PARTNERS3's per-world guard on the final joint action; if it fails, the per-world-checked proposal lands.
HOST: partners2.Sys (ring coupling as PARTNERS1/3); n in {1, 2} (K.5).
ARMS: joined · notubes (fixed 4 per world, own world only, per-world guard: PARTNERS3) · alone_k (organism k with
  tubes, every other world on its defaults, fixed 4 per world, no pool) · native.
CHECKS (fixed now): cells = 20 bridge pairs (v, v+1) x 2 development seeds = 40 (n = 2); n = 1 = the same 40 starts,
  gain(1) = 0 by definition.
  R1 joined > max_k alone_k in >= 90 % of cells;      R2 joined > notubes in >= 90 % of cells;
  R3 (K.4 a, n in {1, 2}) mean gain(2) > gain(1) = 0, and gain(2) > 0 in >= 2/3 of cells;
  R4 (K.4 b) G_k(joined) >= G_k(alone_k) for both organisms in every cell (no tolerance);
  R5 (K.4 c) 0 landed joint actions above a world's projected bound; reported: transfers proposed, refused,
     would-harm (a world's projected G lower than without the transfer, or a channel above its bound);
  R6 pool conserved: <= 4n landings every tick;
  R7 transferred landings with measured need >= 0.90 (need re-measured in the final joint action: removing the
     transferred landing makes the replayed whole worse).
Development seeds: 6560, 6561 (B: seed + 500). Never used elsewhere; never for colours.
Smoke test before the run: 6-tick worlds, throwaway seed 6499, pair (3,4), not kept (42 particles freed, 0 transfers).
Usage: python partners4.py run <part 0|1> ; python partners4.py analyze"""
import sys, os, json, glob, copy, time
import numpy as np
import partners3 as P3
P2, L4, G, O, NV = P3.P2, P3.L4, P3.G, P3.O, P3.NV
SEEDS = [6560, 6561]; dact = P3.dact; Sys = P2.Sys; View = P3.View
ARMS = ["joined", "notubes", "aloneA", "aloneB", "native"]

def own_plan(S, acts, sts, keep_rng):
    """closed-loop future of the joint action: each organism steps on its own world (partners frozen per tick);
    decisions never draw from the worlds' generators (common randomness). Returns G, per-world channels, plan."""
    f = copy.deepcopy(S); f.tick(acts); plan = []
    while f.t < O.T:
        a = []
        for k in range(f.n):
            r = copy.deepcopy(f.w[k].rng); a.append(L4.step(View(f, k, False), f.p[k], sts[k])); f.w[k].rng = r
        plan.append(a); f.tick(a)
    return f, plan

def replay(S, acts, plan):
    f = copy.deepcopy(S); f.tick(acts)
    for a in plan: f.tick(a)
    return f

def with_landing(act, side, u):
    ps, pd, ms, md = act
    if side == "s": return (ps + [u], pd, {**ms, u: "inside"}, md)
    return (ps, pd + [u], ms, {**md, u: "inside"})

def without_landing(act, side, u):
    ps, pd, ms, md = act
    return ([x for x in ps if x != u], pd, ms, md) if side == "s" else (ps, [x for x in pd if x != u], ms, md)

def run_sys(v, sd, arm):
    n = 2; S = Sys(n, v, sd); sts = [L4.st_of(u) for u in S.vs]
    B = P2.to_end(S, [dact(w) for w in S.w]); bound = [w.channels() for w in B.w]
    R0 = [None] * n
    def keep():
        for k in range(n): R0[k] = copy.deepcopy(S.w[k].rng)
    def restore():
        for k in range(n): S.w[k].rng = copy.deepcopy(R0[k])
    def proj(acts): restore(); return P2.to_end(S, acts)
    above = lambda f, ks=(0, 1): any(any(a > b for a, b in zip(f.w[j].channels(), bound[j])) for j in ks)
    worse = lambda f1, f0: f1.G() < f0.G() - 1e-12 or any(any(a > b for a, b in zip(f1.w[j].channels(), f0.w[j].channels())) for j in range(n))
    ev = {"freed": 0, "transfers": 0, "refused": 0, "would_harm": 0, "landed_above": 0, "pool_over": 0, "tr_need": 0, "tr_total": 0}
    debt = [0] * n
    while S.t < O.T:
        keep(); d = [dact(w) for w in S.w]
        org = [arm in ("joined", "notubes") or (arm == "aloneA" and k == 0) or (arm == "aloneB" and k == 1) for k in range(n)]
        tubes = arm != "notubes"
        p1 = [L4.step(View(S, k, tubes), S.p[k], sts[k]) if org[k] else d[k] for k in range(n)]; restore()
        acts = [p1[k] if org[k] else d[k] for k in range(n)]
        if arm == "joined":
            p2 = [L4.step(View(S, k, True, p1[1 - k]), S.p[k], sts[k]) for k in range(n)]; restore()
            acts = list(p2)
            restore(); base, plan = own_plan(S, acts, sts, True)
            freed = []
            for k in range(n):                                       # need of every proposed landing (cheap replay)
                for side, lst in (("s", acts[k][0]), ("d", acts[k][1])):
                    for u in list(lst):
                        tr = list(acts); tr[k] = without_landing(acts[k], side, u); restore(); f0 = replay(S, tr, plan)
                        if not worse(f0, base): freed.append((k, side, u)); acts[k] = without_landing(acts[k], side, u)
            ev["freed"] += len(freed); moved = []
            if freed:
                restore(); base = replay(S, acts, plan); cands = []
                for k in range(n):
                    lk_s, lk_d = S.w[k].lack_s(), S.w[k].lack_d()
                    for side, lack, lst in (("s", lk_s, acts[k][0]), ("d", lk_d, acts[k][1])):
                        for u in [int(x) for x in np.argsort(-lack) if int(x) not in lst][:2]:
                            tr = list(acts); tr[k] = with_landing(acts[k], side, u); restore(); f1 = replay(S, tr, plan)
                            gain = f1.G() - base.G(); cands.append((gain, k, side, u))
                for fk, fside, fu in freed:                          # P4: one particle at a time, best whole first
                    pos = [c for c in cands if c[0] > 1e-12]
                    if not pos: acts[fk] = with_landing(acts[fk], fside, fu); continue   # no need anywhere: keep in place
                    pref = [c for c in pos if debt[c[1]] > 0]
                    g, k, side, u = max(pref or pos); cands.remove((g, k, side, u))
                    if k != fk:                                      # a transfer: per-world Law 0 membrane
                        ev["transfers"] += 1; tr = list(acts); tr[k] = with_landing(acts[k], side, u); f = proj(tr)
                        restore(); f_no = proj(acts)
                        if above(f): ev["refused"] += 1; acts[fk] = with_landing(acts[fk], fside, fu); continue
                        if any(f.w[j].G() < f_no.w[j].G() - 1e-12 for j in range(n) if j != k): ev["would_harm"] += 1
                        acts = tr; debt[fk] += 1; debt[k] -= 1; moved.append((k, side, u))
                    else: acts[k] = with_landing(acts[k], side, u)
            if moved:                                                # R7: need of each transferred landing, measured again
                restore(); fin = replay(S, acts, plan)
                for k, side, u in moved:
                    tr = list(acts); tr[k] = without_landing(acts[k], side, u); restore()
                    ev["tr_total"] += 1; ev["tr_need"] += worse(replay(S, tr, plan), fin)
            if above(proj(acts)):                                    # final per-world guard
                acts = [p if not above(proj([p if j == k else d[j] for j in range(n)])) else d[k] for k, p in enumerate(p2)]
        elif any(org):
            for k in range(n):                                       # per-world guard (as PARTNERS3)
                if not org[k]: continue
                ks = (0, 1) if tubes else (k,)
                if above(proj([acts[k] if j == k else d[j] for j in range(n)]), ks): acts[k] = d[k]
        ev["landed_above"] += above(proj(acts)); ev["pool_over"] += sum(len(a[0]) + len(a[1]) for a in acts) > 4 * n
        restore(); S.tick(acts)
    return {"G": S.G(), "Gk": [float(w.G()) for w in S.w], "ch": [float(x) for x in S.channels()], "ev": ev, "debt": debt}

def run(part):
    fn = f"diag/partners4_p{part}.json"; out = json.load(open(fn)) if os.path.exists(fn) else []   # resume (execution only)
    have = {(r["v"], r["sd"]) for r in out}
    for v in range(1, NV):
        if v % 2 != part: continue
        for sd in SEEDS:
            if (v, sd) in have: continue
            r = {"v": v, "sd": sd}
            for a in ARMS: t0 = time.time(); r[a] = run_sys(v, sd, a); r[a]["sec"] = round(time.time() - t0)
            out.append(r); print("pair", v, sd, {a: r[a]["sec"] for a in ARMS}, flush=True)
            json.dump(out, open(f"diag/partners4_p{part}.json", "w"))

def analyze():
    R = []
    for f in sorted(glob.glob("diag/partners4_p*.json")): R += json.load(open(f))
    n = len(R); A = lambda r, a: r[a]["G"]; gain = [A(r, "joined") - A(r, "notubes") for r in R]
    ev = {q: sum(r["joined"]["ev"][q] for r in R) for q in R[0]["joined"]["ev"]}
    S = {"cells": n, "R1_joined_gt_best_alone": sum(A(r, "joined") > max(A(r, "aloneA"), A(r, "aloneB")) for r in R),
         "R2_joined_gt_notubes": sum(g > 0 for g in gain), "R3_mean_gain2": float(np.mean(gain)), "R3_cells_gain2_pos": sum(g > 0 for g in gain),
         "R4_each_not_worse_than_alone": sum(r["joined"]["Gk"][0] >= r["aloneA"]["Gk"][0] and r["joined"]["Gk"][1] >= r["aloneB"]["Gk"][1] for r in R),
         "R5_landed_above_joined": ev["landed_above"], "R6_pool_over_ticks": ev["pool_over"],
         "R7_transfer_need_precision": ev["tr_need"] / max(1, ev["tr_total"]), "events_joined": ev,
         "mean_G": {a: float(np.mean([A(r, a) for r in R])) for a in ARMS}}
    S["PASS"] = {"R1": S["R1_joined_gt_best_alone"] >= 0.9 * n, "R2": S["R2_joined_gt_notubes"] >= 0.9 * n,
                 "R3": S["R3_mean_gain2"] > 0 and S["R3_cells_gain2_pos"] >= 2 * n / 3, "R4": S["R4_each_not_worse_than_alone"] == n,
                 "R5": S["R5_landed_above_joined"] == 0, "R6": S["R6_pool_over_ticks"] == 0, "R7": S["R7_transfer_need_precision"] >= 0.90}
    S["ROW_PASS"] = all(S["PASS"].values()); json.dump(S, open("diag/QUICK_PARTNERS4.json", "w"), indent=1); print(json.dumps(S, indent=1))

if __name__ == "__main__":
    run(int(sys.argv[2])) if sys.argv[1] == "run" else analyze()
