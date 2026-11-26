"""BEAM4: road 8, built exactly as map Part K.7 (owner OK 23 Nov 2026 ~13:19). Layer 2. Development quick test.
Written ~13:30 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius), before any run.

PART K LINE (Part K, row "Road 8"): where = protocol -> physical channel; missing = K (applying) over a lossy carrier
never run end to end; structure = carry a structure through the physical-layer twin and land it, P3 part check and
repair + P8 redundancy + READY; check = beam received and landed correctly more often than the native carrier under
the same loss, no wrong adoption. CLAIM (K.3): structure-coded lockstep. STRUCTURE (K.7):
  the feedback  : the green dot of each part travels back. One acknowledgement frame per tick (lost with the carrier
                  process) carries the receiver's applied tick and, for every later part, how many of its frames it
                  holds (its syndrome). The sender sends for each part only the frames still missing (fresh parity),
                  never parts the receiver holds (reconcile: restore only what differs).
  the carrier   : a constant carrier flowing every tick, no wait for acknowledgements: each tick the budget B is
                  spent on the parts still missing, oldest first: first the frames each still lacks (by the last
                  feedback), then the rest of the budget as further parity frames round the missing parts (P8).
                  (A smoke test on throwaway seed 6499 found the first version left the budget unspent: sync 0.52 vs
                  whole 1.0 at B = 29; corrected here before the quick test.)
  each part     : an envelope: its base tick (precondition), its effects (the coded part), its invariant (a 4-byte
                  READY digest of the state after it, plus the 16-bit part check), its lineage (the tick); frames of a
                  part accumulate across ticks; a decoded part is held and applied as soon as all earlier parts are.
ARMS (same carrier, same feedback, same losses, same budget, same frame check and READY):
  beam      = structure coding (beam1 parts) on the K.7 carrier  (this is also the P3 arm of K.3 C3);
  lockstep  = generic input coding (beam2 lockstep parts) on the same K.7 carrier;
  whole     = beam coding as ONE bundle of all unapplied parts, sent every tick; frames are discarded if the bundle
              does not decode in the tick (whole resend); feedback = applied tick (the K.3 control).
Undetected corruption 1e-3 per arrived frame (zero in the zero-loss run): READY refuses the part, its frames are
dropped and it is sent again (counted).
CHECKS (K.3, fixed): C1 beam > lockstep at B = 3, 4 in all 18 carrier x loss x budget cells; C3 beam (p3) > whole at
B = 3, 4 in all 18 cells; C2 no wrong adoption, zero loss: replay exact every tick and sync(beam) = 1.0 in every run;
T29 B = 29 reported (declared expected tie, not a criterion).
Development seeds: worlds 6540, 6541; channels 6550+ (never used elsewhere; never for colours). 21 shades.
Usage: python beam4.py run <part 0|1> ; python beam4.py analyze"""
import sys, os, json, glob, math
import numpy as np
import beam1 as B1, beam2 as B2
T, NV, MS, CARRIERS = B1.T, B1.NV, B1.MS, B1.CARRIERS
SEEDS = [6540, 6541]; BUDGETS = [3, 4, 29]

def k_beam(parts, u): return B1.frames(math.ceil((len(parts[u - 1]) + 16) / 8) + 4)
def k_lock(lparts, u): return B1.frames(len(lparts[u - 1]) + 2 + 4)

def sim_carrier(ks, Bf, fwd, back, rng_u, undet):
    held = {}; bad = {}; done = set(); applied = 0; known_applied = 0; known = {}; sync = 0; caught = 0; wrong = 0
    for t in range(1, T + 1):
        lost = fwd[t - 1][:Bf]; fi = 0
        out = [u for u in range(known_applied + 1, t + 1) if ks[u - 1] - known.get(u, 0) > 0]   # sender's view only
        alloc = {u: 0 for u in out}; left = Bf
        for u in out:                                                # the missing frames, oldest first
            n = min(ks[u - 1] - known.get(u, 0), left); alloc[u] += n; left -= n
        i = 0
        while left > 0 and out:                                      # the rest of the budget: more parity (P8), oldest first
            alloc[out[i % len(out)]] += 1; left -= 1; i += 1
        for u in out:
            n = alloc[u]
            if n <= 0: continue
            arr = int((~lost[fi:fi + n]).sum()); fi += n
            if u in done: continue                                   # receiver already holds it (feedback was lost)
            if arr and undet > 0 and (rng_u.random(arr) < undet).any(): bad[u] = True
            held[u] = held.get(u, 0) + arr
            if held[u] >= ks[u - 1]:
                if bad.pop(u, False): caught += 1; held[u] = 0      # READY refuses; frames dropped
                else: done.add(u)
        while applied + 1 in done: applied += 1
        if applied == t: sync += 1
        if not back[t - 1]: known_applied = applied; known = {u: (ks[u - 1] if u in done else held.get(u, 0)) for u in range(applied + 1, t + 1)}
    return {"sync": sync / T, "caught": caught, "wrong": wrong}

def sim_whole(parts, Bf, fwd, back, rng_u, undet):
    applied = 0; known = 0; sync = 0; caught = 0
    for t in range(1, T + 1):
        lost = fwd[t - 1][:Bf]
        if known < t:
            k = B1.frames(math.ceil(sum(len(parts[u - 1]) + 16 for u in range(known + 1, t + 1)) / 8) + 4)
            if k <= Bf:
                arr = int((~lost).sum()); bad = arr > 0 and undet > 0 and bool((rng_u.random(arr) < undet).any())
                if arr >= k:
                    if bad: caught += 1
                    else: applied = t
        if applied == t: sync += 1
        if not back[t - 1]: known = applied
    return {"sync": sync / T, "caught": caught, "wrong": 0}

def run(part):
    out = []
    for v in range(1, NV + 1):
        if v % 2 != part: continue
        for sd in SEEDS:
            p, rec, parts, lparts, exact, lex = B2.prep(v, sd)
            kb = [k_beam(parts, u) for u in range(1, T + 1)]; kl = [k_lock(lparts, u) for u in range(1, T + 1)]
            for ci, car in enumerate(CARRIERS):
                for mi, m in enumerate(MS):
                    cs = 6550 + 1000 * ci + 100 * mi + 10 * v + SEEDS.index(sd)
                    fwd = list(B1.loss_process(car, m, np.random.default_rng(cs), 29)); back = B2.back_process(car, m, np.random.default_rng(cs + 3))
                    row = {"v": v, "sd": sd, "carrier": car, "m": m}
                    for b in BUDGETS:
                        row[str(b)] = {"beam": sim_carrier(kb, b, fwd, back, np.random.default_rng(cs + 7), B1.UNDET),
                                       "lockstep": sim_carrier(kl, b, fwd, back, np.random.default_rng(cs + 7), B1.UNDET),
                                       "whole": sim_whole(parts, b, fwd, back, np.random.default_rng(cs + 7), B1.UNDET)}
                    out.append(row)
            zf = [np.zeros(29, bool)] * T; zb = [False] * T
            out.append({"v": v, "sd": sd, "carrier": "none", "exact": bool(exact), "lock_exact": bool(lex),
                        "beam_sync": sim_carrier(kb, 29, zf, zb, np.random.default_rng(1), 0.0)["sync"],
                        "k_median": {"beam": float(np.median(kb)), "lockstep": float(np.median(kl))}})
            print("run", v, sd, flush=True)
    json.dump(out, open(f"diag/beam4_p{part}.json", "w"))

def analyze():
    R = []
    for f in sorted(glob.glob("diag/beam4_p*.json")): R += json.load(open(f))
    lossy = [r for r in R if r["carrier"] != "none"]; zero = [r for r in R if r["carrier"] == "none"]; C = {}
    for r in lossy:
        for b in BUDGETS:
            c = C.setdefault(f"B{b}|{r['carrier']}|{r['m']}", {a: [] for a in ("beam", "lockstep", "whole")})
            for a in c: c[a].append(r[str(b)][a]["sync"])
    M = {k: {a: round(float(np.mean(v)), 4) for a, v in c.items()} for k, c in C.items()}
    tight = [k for k in M if not k.startswith("B29|")]
    S = {"cells": M, "C1_beam_gt_lockstep": [sum(M[k]["beam"] > M[k]["lockstep"] for k in tight), len(tight)],
         "C3_p3_gt_whole": [sum(M[k]["beam"] > M[k]["whole"] for k in tight), len(tight)],
         "T29_max_abs_beam_minus_lockstep": max(abs(M[k]["beam"] - M[k]["lockstep"]) for k in M if k.startswith("B29|")),
         "wrong": sum(r[str(b)][a]["wrong"] for r in lossy for b in BUDGETS for a in ("beam", "lockstep", "whole")),
         "caught_by_READY_beam": sum(r[str(b)]["beam"]["caught"] for r in lossy for b in BUDGETS),
         "zero": {"exact": sum(r["exact"] for r in zero), "sync_1": sum(r["beam_sync"] == 1.0 for r in zero), "runs": len(zero)},
         "k_median": {a: float(np.median([r["k_median"][a] for r in zero])) for a in ("beam", "lockstep")}}
    S["PASS"] = {"C1": S["C1_beam_gt_lockstep"][0] == len(tight), "C3": S["C3_p3_gt_whole"][0] == len(tight),
                 "C2": S["wrong"] == 0 and S["zero"]["exact"] == S["zero"]["runs"] and S["zero"]["sync_1"] == S["zero"]["runs"]}
    S["ROW_PASS"] = all(S["PASS"].values()); json.dump(S, open("diag/QUICK_BEAM4.json", "w"), indent=1); print(json.dumps(S, indent=1))

if __name__ == "__main__":
    run(int(sys.argv[2])) if sys.argv[1] == "run" else analyze()
