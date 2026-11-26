"""BEAM6: road 8 built exactly as map Part K.10 (owner OK 23 Nov 2026 ~13:59). Layer 2. Development quick test, the
last round for road 8 (owner: if it fails, C3 is carried open into the combined seal).
Written ~15:45 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius), before any run.

PART K LINE (Part K, row "Road 8"): where = protocol -> physical channel; missing = K (applying) over a lossy carrier
never run end to end; structure = carry a structure through the physical-layer twin and land it, P3 part check and
repair + P8 redundancy + READY; check = beam received and landed correctly more often than the native carrier under
the same loss, no wrong adoption. CLAIM (K.3): structure-coded lockstep.
STRUCTURE (K.10): the two codings of beam5 (per-part repair with the green dot; hologram of the backlog), switched each
tick by the observer from three states it reads in the sender's view:
  q   = 1 - received/sent over the last 5 acknowledged ticks (0 before the first acknowledgement);
  B   = the tick's budget;
  W   = parts not known to be applied, their sizes; m_u = frames part u still lacks by the last syndrome (per-part
        mode) or k_u (hologram mode: partial per-part frames are dropped on a switch); h = hologram frames the receiver
        reported holding (hologram mode) or 0 (per-part mode).
  P_part  = prod_u P[Bin(n_u, 1-q) >= m_u]  (Law 1, read scope), n_u = the per-part carrier's allocation this tick
            (missing frames first, then parity round-robin, oldest first);
  P_joint = P[Bin(B, 1-q) >= F_joint - h]   (Law 2, one blind operation), F_joint = ceil((sum_u (b_u + 16)/8 + 4)/16).
  The coding with the higher probability lands; ties -> per-part. No threshold, no hysteresis.
The receiver drops the other coding's partial frames on a switch (as beam5). Lockstep: same observer, own sizes.
CONTROL (C3, unchanged): beam4.sim_whole. CHECKS (K.3, unchanged): C1 beam > lockstep at B = 3, 4 in all 18 cells;
C3 beam > whole at B = 3, 4 in all 18 cells; C2 no wrong adoption, zero loss exact with sync 1.0; T29 reported.
Reported: hologram share per cell.
Development seeds: worlds 6590, 6591; channels 6600+ (never used elsewhere; never for colours). 21 shades.
Smoke test before the run: throwaway seed 6499, shade 3, light, not kept.
Usage: python beam6.py run <part 0|1> ; python beam6.py analyze"""
import sys, os, json, glob, math
from collections import deque
import numpy as np
from scipy.stats import binom
import beam1 as B1, beam2 as B2, beam4 as B4, beam5 as B5
T, NV, MS, CARRIERS = B1.T, B1.NV, B1.MS, B1.CARRIERS
SEEDS = [6590, 6591]; BUDGETS = [3, 4, 29]

def alloc_part(out, miss, Bf):
    alloc = {u: 0 for u in out}; left = Bf
    for u in out: n = min(miss[u], left); alloc[u] += n; left -= n
    i = 0
    while left > 0 and out: alloc[out[i % len(out)]] += 1; left -= 1; i += 1
    return alloc

def sim_k10(bits, ks, Bf, fwd, back, rng_u, undet):
    held = {}; bad = {}; done = set(); applied = 0; known_applied = 0; known = {}; known_h = 0
    sync = 0; caught = 0; mode = "part"; est = deque(maxlen=5); holo_ticks = 0; hcount = 0; hbad = False
    for t in range(1, T + 1):
        lost = fwd[t - 1][:Bf]; arrived_tick = 0
        q = float(np.mean(est)) if est else 0.0
        W = list(range(known_applied + 1, t + 1))
        miss_p = {u: (ks[u - 1] - known.get(u, 0) if mode == "part" else ks[u - 1]) for u in W}
        outp = [u for u in W if miss_p[u] > 0]; al = alloc_part(outp, miss_p, Bf)
        P_part = float(np.prod([binom.sf(miss_p[u] - 1, al[u], 1 - q) for u in outp])) if outp else 1.0
        F = B1.frames(math.ceil(sum(bits[u - 1] for u in W) / 8) + 4); h = known_h if mode == "holo" else 0
        P_joint = float(binom.sf(F - h - 1, Bf, 1 - q)) if W else 1.0
        new = "holo" if P_joint > P_part else "part"
        if new != mode:
            mode = new; held = {u: c for u, c in held.items() if u <= applied}; bad = {}; hcount = 0; hbad = False; known_h = 0
            known = {}
        if mode == "part":
            out = [u for u in range(known_applied + 1, t + 1) if ks[u - 1] - known.get(u, 0) > 0]
            al = alloc_part(out, {u: ks[u - 1] - known.get(u, 0) for u in out}, Bf); fi = 0
            for u in out:
                n = al[u]
                if n <= 0: continue
                arr = int((~lost[fi:fi + n]).sum()); fi += n; arrived_tick += arr
                if u in done: continue
                if arr and undet > 0 and (rng_u.random(arr) < undet).any(): bad[u] = True
                held[u] = held.get(u, 0) + arr
                if held[u] >= ks[u - 1]:
                    if bad.pop(u, False): caught += 1; held[u] = 0
                    else: done.add(u)
            while applied + 1 in done: applied += 1
        else:
            holo_ticks += 1; arr = int((~lost).sum()); arrived_tick = arr
            if applied < t and arr:
                if undet > 0 and (rng_u.random(arr) < undet).any(): hbad = True
                hcount += arr
                need = B1.frames(math.ceil(sum(bits[u - 1] for u in range(applied + 1, t + 1)) / 8) + 4)
                if hcount >= need:
                    if hbad: caught += 1
                    else: applied = t; done.update(range(1, t + 1))
                    hcount = 0; hbad = False
        if applied == t: sync += 1
        if not back[t - 1]:
            known_applied = applied; known = {u: (ks[u - 1] if u in done else held.get(u, 0)) for u in range(applied + 1, t + 1)}
            known_h = hcount; est.append(1 - arrived_tick / Bf)
    return {"sync": sync / T, "caught": caught, "wrong": 0, "holo_share": holo_ticks / T}

def run(part):
    out = []
    for v in range(1, NV + 1):
        if v % 2 != part: continue
        for sd in SEEDS:
            p, rec, parts, lparts, exact, lex = B2.prep(v, sd)
            kb = [B4.k_beam(parts, u) for u in range(1, T + 1)]; kl = [B4.k_lock(lparts, u) for u in range(1, T + 1)]
            bb = [len(parts[u - 1]) + 16 for u in range(1, T + 1)]; bl = [8 * (len(lparts[u - 1]) + 2) for u in range(1, T + 1)]
            for ci, car in enumerate(CARRIERS):
                for mi, m in enumerate(MS):
                    cs = 6600 + 1000 * ci + 100 * mi + 10 * v + SEEDS.index(sd)
                    fwd = list(B1.loss_process(car, m, np.random.default_rng(cs), 29)); back = B2.back_process(car, m, np.random.default_rng(cs + 3))
                    row = {"v": v, "sd": sd, "carrier": car, "m": m}
                    for b in BUDGETS:
                        row[str(b)] = {"beam": sim_k10(bb, kb, b, fwd, back, np.random.default_rng(cs + 7), B1.UNDET),
                                       "lockstep": sim_k10(bl, kl, b, fwd, back, np.random.default_rng(cs + 7), B1.UNDET),
                                       "whole": B4.sim_whole(parts, b, fwd, back, np.random.default_rng(cs + 7), B1.UNDET)}
                    out.append(row)
            zf = [np.zeros(29, bool)] * T; zb = [False] * T
            out.append({"v": v, "sd": sd, "carrier": "none", "exact": bool(exact),
                        "beam_sync": sim_k10(bb, kb, 29, zf, zb, np.random.default_rng(1), 0.0)["sync"]})
            print("run", v, sd, flush=True)
    json.dump(out, open(f"diag/beam6_p{part}.json", "w"))

def analyze():
    R = []
    for f in sorted(glob.glob("diag/beam6_p*.json")): R += json.load(open(f))
    lossy = [r for r in R if r["carrier"] != "none"]; zero = [r for r in R if r["carrier"] == "none"]; C = {}; H = {}
    for r in lossy:
        for b in BUDGETS:
            k = f"B{b}|{r['carrier']}|{r['m']}"; c = C.setdefault(k, {a: [] for a in ("beam", "lockstep", "whole")})
            for a in c: c[a].append(r[str(b)][a]["sync"])
            H.setdefault(k, []).append(r[str(b)]["beam"]["holo_share"])
    M = {k: {a: round(float(np.mean(v)), 4) for a, v in c.items()} for k, c in C.items()}
    tight = [k for k in M if not k.startswith("B29|")]
    S = {"cells": M, "holo_share_beam": {k: round(float(np.mean(v)), 3) for k, v in H.items()},
         "C1_beam_gt_lockstep": [sum(M[k]["beam"] > M[k]["lockstep"] for k in tight), len(tight)],
         "C3_beam_gt_whole": [sum(M[k]["beam"] > M[k]["whole"] for k in tight), len(tight)],
         "T29_max_abs_beam_minus_lockstep": max(abs(M[k]["beam"] - M[k]["lockstep"]) for k in M if k.startswith("B29|")),
         "caught_by_READY_beam": sum(r[str(b)]["beam"]["caught"] for r in lossy for b in BUDGETS),
         "zero": {"exact": sum(r["exact"] for r in zero), "sync_1": sum(r["beam_sync"] == 1.0 for r in zero), "runs": len(zero)}}
    S["PASS"] = {"C1": S["C1_beam_gt_lockstep"][0] == len(tight), "C3": S["C3_beam_gt_whole"][0] == len(tight),
                 "C2": S["zero"]["exact"] == S["zero"]["runs"] and S["zero"]["sync_1"] == S["zero"]["runs"]}
    S["ROW_PASS"] = all(S["PASS"].values()); json.dump(S, open("diag/QUICK_BEAM6.json", "w"), indent=1); print(json.dumps(S, indent=1))

if __name__ == "__main__":
    run(int(sys.argv[2])) if sys.argv[1] == "run" else analyze()
