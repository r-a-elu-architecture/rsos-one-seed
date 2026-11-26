"""BIRTHS3: row D short test of map K.13 + K.16 (owner 24 Nov 00:29: short test here, adjust, until the table is filled;
then one long run). Layer 2. Development. Written 24 Nov 2026 ~01:25 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn,
Vilnius), before any run. births2.py is kept.

PART K LINE (Part K, row "D · births"): where = organism -> generation; missing = O (trace of where each parent is
strong) and A (route by state), averaged host; structure = P9 complementation (heterosis, symbiogenesis); child host =
both parents' pressures (owner YES, 23 Nov 04:59); check = child > max(parents) in the child host; child >= each parent
in the parent's own host.
STRUCTURE (K.13 + K.16):
  child host   both parents' pressures: d, hz, cz = the larger of the two parents, modes = union.
  parents      A = shade v, B = shade v+1, each its ORG6 own structure with the budget-correct counter-shift (v3).
  the book     (genetics: which allele works where; cell biology: symbiogenesis keeps each partner whole) each parent
               runs its own structure in the child host on growth seed 6652; the parent with fewer dry unit-ticks is the
               supply parent, the one with fewer drifted unit-ticks the drift parent (ties: A).
  the child    (complementation + mixture of experts with a gate): each tick the supply side lands the supply parent's
               supply picks and modes, the drift side the drift parent's drift picks and modes (each parent decides with
               its own whole structure on the shared state); the gate routes by state: if the longest dry run >= 3 the
               supply parent's whole action lands, else if the longest drift >= 3 the drift parent's whole action lands.
               Shared budget 4 (the larger side trimmed last-first). Common randomness (deciding never moves the world).
ARMS: child, parA, parB in the child host; in each parent's own host: child (same book, same gate) and that parent.
CHECKS (fixed now; bridges v = 1, 4, 7, 10, 13, 16, 19 x development seeds 6650, 6651 = 14 cells):
  B1 child > max(parA, parB) in the child host in >= 2/3 of cells and mean gain > 0;
  B2 child >= parent - 0.005 in that parent's own host, in >= 90 % of the 28 (cell, parent) pairs.
Seeds never used elsewhere; never for colours. Smoke test before the run: 5-tick worlds, throwaway seed 6499, bridge 4, not kept.
Usage: python births3.py run <part 0|1> ; python births3.py analyze"""
import sys, os, json, glob, copy, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "laws"))
import laws as L, laws4 as L4
os.chdir(HERE)
G, O = L.G, L.O
SEEDS = [6650, 6651]; GROW = 6652; BRIDGES = [1, 4, 7, 10, 13, 16, 19]

def child_host(v):
    pa, pb = G.params(G.SH["shades"][v - 1]["node"], v), G.params(G.SH["shades"][v]["node"], v + 1)
    return {**pa, "d": max(pa["d"], pb["d"]), "hz": max(pa["hz"], pb["hz"]), "cz": max(pa["cz"], pb["cz"]), "modes": sorted(set(pa["modes"]) | set(pb["modes"]))}

def run(sd, p, policy):
    """policy(w) -> action; common randomness; returns G, channels, dry unit-ticks, drifted unit-ticks."""
    w = G.Shade(sd, p, "inside"); dry = dr = 0
    while w.t < O.T:
        r = copy.deepcopy(w.rng); a = policy(w); w.rng = r
        w.ms, w.md = dict(a[2]), dict(a[3]); w.tick(list(a[0]), list(a[1])); dry += int((w.res <= 0).sum()); dr += int(w.dr.sum())
    return {"G": float(w.G()), "ch": [float(x) for x in w.channels()], "dry": dry, "dr": dr}

def parent(p, st): return lambda w: L4.step(w, p, st)

def child(p, stS, stD):
    def pol(w):
        r = copy.deepcopy(w.rng); aS = L4.step(w, p, stS); w.rng = copy.deepcopy(r); aD = L4.step(w, p, stD); w.rng = r
        if float(np.max(w.dry)) >= 3: return aS
        if float(np.max(w.dur)) >= 3: return aD
        ps, ms = list(aS[0]), {i: aS[2].get(i, "inside") for i in aS[0]}; pd, md = list(aD[1]), {j: aD[3].get(j, "inside") for j in aD[1]}
        while len(ps) + len(pd) > 2 * O.KH:
            big, D = (ps, ms) if len(ps) >= len(pd) else (pd, md); D.pop(big.pop(), None)
        return ps, pd, ms, md
    return pol

def run_part(part):
    out = []
    for i, v in enumerate(BRIDGES):
        if i % 2 != part: continue
        pc = child_host(v); pA = G.params(G.SH["shades"][v - 1]["node"], v); pB = G.params(G.SH["shades"][v]["node"], v + 1)
        stA, stB = L4.st_of(v), L4.st_of(v + 1)
        gA, gB = run(GROW, pc, parent(pc, stA)), run(GROW, pc, parent(pc, stB))
        stS = stA if gA["dry"] <= gB["dry"] else stB; stD = stA if gA["dr"] <= gB["dr"] else stB
        book = {"supply": "A" if stS is stA else "B", "drift": "A" if stD is stA else "B"}
        for sd in SEEDS:
            t0 = time.time()
            r = {"v": v, "sd": sd, "book": book,
                 "child_C": run(sd, pc, child(pc, stS, stD)), "parA_C": run(sd, pc, parent(pc, stA)), "parB_C": run(sd, pc, parent(pc, stB)),
                 "child_A": run(sd, pA, child(pA, stS, stD)), "parA_A": run(sd, pA, parent(pA, stA)),
                 "child_B": run(sd, pB, child(pB, stS, stD)), "parB_B": run(sd, pB, parent(pB, stB))}
            r["sec"] = round(time.time() - t0); out.append(r)
            print("bridge", v, sd, book, {k: round(x["G"], 4) for k, x in r.items() if isinstance(x, dict) and "G" in x}, r["sec"], "s", flush=True)
            json.dump(out, open(f"diag/births3_p{part}.json", "w"))

def analyze():
    R = []
    for f in glob.glob("diag/births3_p*.json"): R += json.load(open(f))
    n = len(R); d = [r["child_C"]["G"] - max(r["parA_C"]["G"], r["parB_C"]["G"]) for r in R]
    own = [r["child_A"]["G"] >= r["parA_A"]["G"] - 0.005 for r in R] + [r["child_B"]["G"] >= r["parB_B"]["G"] - 0.005 for r in R]
    S = {"cells": n, "B1_child_gt_max_parents": {"wins": sum(x > 1e-12 for x in d), "mean": float(np.mean(d))},
         "B2_child_ge_parent_own_host": [sum(own), len(own)],
         "mixed_books": sum(r["book"]["supply"] != r["book"]["drift"] for r in R),
         "mean_G": {k: float(np.mean([r[k]["G"] for r in R])) for k in ("child_C", "parA_C", "parB_C", "child_A", "parA_A", "child_B", "parB_B")}}
    S["PASS"] = {"B1": S["B1_child_gt_max_parents"]["wins"] >= 2 * n / 3 and S["B1_child_gt_max_parents"]["mean"] > 0, "B2": sum(own) >= 0.9 * len(own)}
    S["ROW_PASS"] = all(S["PASS"].values()); json.dump(S, open("diag/QUICK_BIRTHS3.json", "w"), indent=1); print(json.dumps(S, indent=1))

if __name__ == "__main__":
    run_part(int(sys.argv[2])) if sys.argv[1] == "run" else analyze()
