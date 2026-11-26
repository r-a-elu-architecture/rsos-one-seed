"""BEAM3: road 8, the form for the sealed run (map Part K.3, owner 23 Nov 2026 ~08:04). Layer 2.
Written 23 Nov 2026 ~08:10 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius), before any BEAM3 run.

PART K LINE (Part K, row "Road 8"): where = protocol -> physical channel; missing = K (applying) over a lossy carrier
never run end to end; structure = carry a structure through the physical-layer twin and land it, P3 part check and
repair + P8 redundancy + READY; check = beam received and landed correctly more often than the native carrier under
the same loss, no wrong adoption.
CLAIM (Part K.3): structure-coded lockstep.

ARMS and channel: beam2.py (beam, lockstep, snap, delta; lossy feedback; MDS parity; frame check; READY; zero-loss run
with no loss, no corruption, no feedback loss), plus the P3 pair below.
CHECKS (Part K.3, fixed now):
  C1  beam > lockstep (mean sync) at B = 3 and B = 4 in every carrier x loss cell (18 cells).
  C2  no wrong adoption by the beam (all budgets); zero loss: replay exact every tick, sync(beam) = 1.0, every run.
  T29 B = 29 is run and reported: declared expected tie (|beam - lockstep| small), NOT a criterion.
  C3  P3 test: sync(p3) > sync(whole) at B = 3 and B = 4 in every carrier x loss cell (18 cells).
        p3    : every tick is its own part (beam coding + 16-bit part check + 4-byte READY hash of the state after
                the part); frames of a part accumulate across ticks; each tick the sender spends the budget on the
                parts not yet acknowledged, oldest first, k_part fresh frames each until the budget is used; the
                receiver applies parts in order as soon as they are contiguous; feedback (lossy) carries the latest
                applied tick.
        whole : the same coding, all unacknowledged parts as ONE bundle; if fewer than k_bundle frames arrive in a
                tick the frames are discarded and the whole bundle is sent again next tick (whole resend).
QUICK TEST (development seeds; does not count): worlds 6480, 6481; channels 6490+.
SEALED RUN: fresh seeds set in the combined PREREG (not chosen here).
Usage: python beam3.py run <part 0|1> [seed,seed] ; python beam3.py analyze"""
import sys, os, json, glob, math
import numpy as np
import beam1 as B1, beam2 as B2
T, NV, MS, CARRIERS = B1.T, B1.NV, B1.MS, B1.CARRIERS
BUDGETS = [3, 4, 29]

def part_k(parts, t): return B1.frames(math.ceil((len(parts[t - 1]) + 16) / 8) + 4)

def sim_p3(parts, Bf, fwd, back, rng_u, undet, whole):
    applied = 0; known = 0; got = {}; sync = 0; caught = 0
    for t in range(1, T + 1):
        lost = fwd[t - 1][:Bf]; ok = list(~lost); fi = 0
        if whole:
            if known < t:
                k = B1.frames(math.ceil(sum(len(parts[u - 1]) + 16 for u in range(known + 1, t + 1)) / 8) + 4)
                arr = int(np.sum(ok)); bad = arr > 0 and undet > 0 and bool((rng_u.random(arr) < undet).any())
                if arr >= k and k <= Bf:
                    if bad: caught += 1
                    else: applied = t
        else:
            for u in range(known + 1, t + 1):
                if u <= applied: continue
                k = part_k(parts, u); n = min(k, Bf - fi)
                if n <= 0: break
                arr = int(np.sum(ok[fi:fi + n])); fi += n
                if arr and undet > 0 and (rng_u.random(arr) < undet).any(): caught += 1; got[u] = 0; continue
                got[u] = got.get(u, 0) + arr
            while applied + 1 <= t and got.get(applied + 1, 0) >= part_k(parts, applied + 1): applied += 1
        if applied == t: sync += 1
        if not back[t - 1]: known = applied
    return {"sync": sync / T, "caught": caught}

def run(part, seeds):
    out = []
    for v in range(1, NV + 1):
        if v % 2 != part: continue
        for sd in seeds:
            p, rec, parts, lparts, exact, lex = B2.prep(v, sd); init = B1.state_bytes(B1.receiver(sd, p))
            for ci, car in enumerate(CARRIERS):
                for mi, m in enumerate(MS):
                    cs = (6490 if sd in (6480, 6481) else sd + 50) + 1000 * ci + 100 * mi + 10 * v + seeds.index(sd)
                    fwd = list(B1.loss_process(car, m, np.random.default_rng(cs), 29)); back = B2.back_process(car, m, np.random.default_rng(cs + 3))
                    row = {"v": v, "sd": sd, "carrier": car, "m": m}
                    for b in BUDGETS:
                        row[str(b)] = {a: B2.simulate(a, rec, parts, lparts, b, fwd, back, np.random.default_rng(cs + 7), init, B1.UNDET) for a in ("beam", "lockstep")}
                        row[str(b)]["p3"] = sim_p3(parts, b, fwd, back, np.random.default_rng(cs + 9), B1.UNDET, False)
                        row[str(b)]["whole"] = sim_p3(parts, b, fwd, back, np.random.default_rng(cs + 9), B1.UNDET, True)
                    out.append(row)
            zf = [np.zeros(29, bool)] * T; zb = [False] * T
            out.append({"v": v, "sd": sd, "carrier": "none", "exact": bool(exact), "lock_exact": bool(lex),
                        **{str(b): {"beam": B2.simulate("beam", rec, parts, lparts, b, zf, zb, np.random.default_rng(1), init, 0.0)} for b in BUDGETS}})
            print("run", v, sd, flush=True)
    json.dump(out, open(f"diag/beam3_p{part}_{'_'.join(map(str, seeds))}.json", "w"))

def analyze(seeds):
    R = []
    for f in sorted(glob.glob(f"diag/beam3_p*_{'_'.join(map(str, seeds))}.json")): R += json.load(open(f))
    lossy = [r for r in R if r["carrier"] != "none"]; zero = [r for r in R if r["carrier"] == "none"]; C = {}
    for r in lossy:
        for b in BUDGETS:
            c = C.setdefault(f"B{b}|{r['carrier']}|{r['m']}", {a: [] for a in ("beam", "lockstep", "p3", "whole")})
            for a in c: c[a].append(r[str(b)][a]["sync"])
    M = {k: {a: round(float(np.mean(v)), 4) for a, v in c.items()} for k, c in C.items()}
    tight = [k for k in M if k.startswith(("B3|", "B4|"))]
    S = {"cells": M, "C1_beam_gt_lockstep": (sum(M[k]["beam"] > M[k]["lockstep"] for k in tight), len(tight)),
         "C3_p3_gt_whole": (sum(M[k]["p3"] > M[k]["whole"] for k in tight), len(tight)),
         "T29_declared_tie_max_abs_diff": max(abs(M[k]["beam"] - M[k]["lockstep"]) for k in M if k.startswith("B29|")),
         "wrong_beam": sum(r[str(b)]["beam"]["wrong"] for r in lossy for b in BUDGETS), "zero": {"exact": sum(r["exact"] for r in zero), "runs": len(zero),
                                   "beam_sync_1_B29": sum(r["29"]["beam"]["sync"] == 1.0 for r in zero)}}
    S["PASS"] = {"no_wrong": S["wrong_beam"] == 0, "C1": S["C1_beam_gt_lockstep"][0] == len(tight), "C3": S["C3_p3_gt_whole"][0] == len(tight),
                 "C2": S["zero"]["exact"] == S["zero"]["runs"] and S["zero"]["beam_sync_1_B29"] == S["zero"]["runs"]}
    S["ROW_PASS"] = all(S["PASS"].values()); json.dump(S, open(f"diag/QUICK_BEAM3_{'_'.join(map(str, seeds))}.json", "w"), indent=1); print(json.dumps(S, indent=1))

if __name__ == "__main__":
    seeds = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else [6480, 6481]
    if sys.argv[1] == "run": run(int(sys.argv[2]), seeds)
    else: analyze([int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [6480, 6481])
