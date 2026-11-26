"""BIRTHS4: row D short test of map K.17 (owner OK 24 Nov 02:40). Layer 2. Development.
Written 24 Nov 2026 ~03:00 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius), before any run.
PART K LINE (row "D · births"): organism -> generation; missing O (where each parent is strong) and A (route by state);
structure P9 complementation; child host = both parents' pressures (owner YES); check child > max(parents) in the child
host, child >= each parent in its own host.
STRUCTURE (K.13 + K.17):
  state class  read against the host's own set point (as HOUSE3): 'dry' when the longest dry run exceeds the 75th
               percentile of its own past values and is >= the longest drift; 'drift' when the longest drift exceeds its
               own 75th percentile; else 'calm' (first 5 ticks: calm).
  the book     per host (child host; each parent's own host), on growth seeds 6692 (path driven by parent A) and 6693
               (path driven by parent B): at every tick both parents' actions are forked from the same state (common
               randomness, defaults after) and the parent with the higher projected whole is booked under the tick's
               state class (gene expression switched by the condition; mixture of experts gating on the input).
               Majority per class; ties and unseen classes -> the parent better over the whole growth runs.
  the child    each tick reads its state class and lands the whole action of the parent booked for it; in a parent's
               own host it uses that host's book. Common randomness.
ARMS / CHECKS as births3 (B1 child > max(parents) in the child host in >= 2/3 of cells, mean > 0; B2 child >= parent
- 0.005 in the parent's own host in >= 90 % of the 28 pairs). Bridges 1, 4, 7, 10, 13, 16, 19 x development seeds
6690, 6691. Seeds never used elsewhere; never for colours.
Usage: python births4.py run <part 0|1> ; python births4.py analyze"""
import sys, os, json, glob, copy, time
import numpy as np
import births3 as B3
L4, G, O, L2 = B3.L4, B3.G, B3.O, None
import laws2 as L2
SEEDS = [6690, 6691]; GROW = [6692, 6693]; BRIDGES = B3.BRIDGES

def classify(w, hd, hr):
    a, b = float(np.max(w.dry)), float(np.max(w.dur)); hd.append(a); hr.append(b)
    if len(hd) <= 5: return "calm"
    if a > np.percentile(hd[:-1], 75) and a >= b: return "dry"
    if b > np.percentile(hr[:-1], 75): return "drift"
    return "calm"

def book_for(p, stA, stB):
    tally = {c: [0, 0] for c in ("dry", "drift", "calm")}; tot = [0.0, 0.0]
    for gs, drive in zip(GROW, (stA, stB)):
        w = G.Shade(gs, p, "inside"); hd, hr = [], []
        while w.t < O.T:
            c = classify(w, hd, hr); r = copy.deepcopy(w.rng); res = []
            for st in (stA, stB):
                w.rng = copy.deepcopy(r); a = L4.step(w, p, st); w.rng = copy.deepcopy(r)
                g, _ = L2.proj(w, list(a[0]), list(a[1]), a[2], a[3], G.Shade); res.append((g, a))
            w.rng = copy.deepcopy(r)
            if res[0][0] != res[1][0]: tally[c][0 if res[0][0] > res[1][0] else 1] += 1
            tot[0] += res[0][0]; tot[1] += res[1][0]
            a = res[0][1] if drive is stA else res[1][1]; w.rng = r; w.ms, w.md = dict(a[2]), dict(a[3]); w.tick(list(a[0]), list(a[1]))
    dflt = "A" if tot[0] >= tot[1] else "B"
    return {c: ("A" if t[0] > t[1] else "B" if t[1] > t[0] else dflt) for c, t in tally.items()}, tally

def child(p, stA, stB, book):
    hd, hr = [], []
    def pol(w):
        c = classify(w, hd, hr); return L4.step(w, p, stA if book[c] == "A" else stB)
    return pol

def run_part(part):
    out = []
    for i, v in enumerate(BRIDGES):
        if i % 2 != part: continue
        pc = B3.child_host(v); pA = G.params(G.SH["shades"][v - 1]["node"], v); pB = G.params(G.SH["shades"][v]["node"], v + 1)
        stA, stB = L4.st_of(v), L4.st_of(v + 1)
        bC, tC = book_for(pc, stA, stB); bA, _ = book_for(pA, stA, stB); bB, _ = book_for(pB, stA, stB)
        for sd in SEEDS:
            t0 = time.time()
            r = {"v": v, "sd": sd, "book": bC, "tally": tC, "bookA": bA, "bookB": bB,
                 "child_C": B3.run(sd, pc, child(pc, stA, stB, bC)), "parA_C": B3.run(sd, pc, B3.parent(pc, stA)), "parB_C": B3.run(sd, pc, B3.parent(pc, stB)),
                 "child_A": B3.run(sd, pA, child(pA, stA, stB, bA)), "parA_A": B3.run(sd, pA, B3.parent(pA, stA)),
                 "child_B": B3.run(sd, pB, child(pB, stA, stB, bB)), "parB_B": B3.run(sd, pB, B3.parent(pB, stB))}
            r["sec"] = round(time.time() - t0); out.append(r)
            print("bridge", v, sd, bC, {k: round(x["G"], 4) for k, x in r.items() if isinstance(x, dict) and "G" in x}, r["sec"], "s", flush=True)
            json.dump(out, open(f"diag/births4_p{part}.json", "w"))

def analyze():
    R = []
    for f in glob.glob("diag/births4_p*.json"): R += json.load(open(f))
    n = len(R); d = [r["child_C"]["G"] - max(r["parA_C"]["G"], r["parB_C"]["G"]) for r in R]
    own = [r["child_A"]["G"] >= r["parA_A"]["G"] - 0.005 for r in R] + [r["child_B"]["G"] >= r["parB_B"]["G"] - 0.005 for r in R]
    S = {"cells": n, "B1_child_gt_max_parents": {"wins": sum(x > 1e-12 for x in d), "mean": float(np.mean(d))},
         "B2_child_ge_parent_own_host": [sum(own), len(own)], "mixed_books": sum(len(set(r["book"].values())) > 1 for r in R),
         "mean_G": {k: float(np.mean([r[k]["G"] for r in R])) for k in ("child_C", "parA_C", "parB_C", "child_A", "parA_A", "child_B", "parB_B")}}
    S["PASS"] = {"B1": S["B1_child_gt_max_parents"]["wins"] >= 2 * n / 3 and S["B1_child_gt_max_parents"]["mean"] > 0, "B2": sum(own) >= 0.9 * len(own)}
    S["ROW_PASS"] = all(S["PASS"].values()); json.dump(S, open("diag/QUICK_BIRTHS4.json", "w"), indent=1); print(json.dumps(S, indent=1))

if __name__ == "__main__":
    run_part(int(sys.argv[2])) if sys.argv[1] == "run" else analyze()
