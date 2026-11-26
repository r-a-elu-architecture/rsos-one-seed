"""BEAM5: road 8 built exactly as map Part K.9 (owner OK 23 Nov 2026 ~13:30, threshold 0.4 fixed). Layer 2.
Development quick test. Written ~14:50 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius), before any run.

PART K LINE (Part K, row "Road 8"): where = protocol -> physical channel; missing = K (applying) over a lossy carrier
never run end to end; structure = carry a structure through the physical-layer twin and land it, P3 part check and
repair + P8 redundancy + READY; check = beam received and landed correctly more often than the native carrier under
the same loss, no wrong adoption. CLAIM (K.3): structure-coded lockstep. STRUCTURE (K.9):
  low loss  : per-part repair with the green dot (beam4.sim_carrier logic: per-part envelopes, syndrome feedback,
              missing frames first, the rest of the budget as parity, oldest first).
  high loss : the hologram of the backlog: every frame a joint combination of all parts the sender does not know to
              be applied (sliding window over the backlog), one READY for the backlog (4 bytes) + a 16-bit tag per
              part; frames accumulate across ticks; the receiver decodes all its unknown parts as soon as the frames
              it received since its last decode reach the joint size of those parts (ideal random linear code:
              a received frame always covers the receiver's unknown parts because the window ends at the current
              tick). READY refusal (undetected corruption) drops the accumulated frames.
  the switch: route by state. The feedback frame (one per tick, lossy) also carries how many frames arrived that tick;
              the observer's loss estimate = 1 - received/sent over the last 5 acknowledged ticks; per-part while the
              estimate <= 0.4, hologram above; hysteresis: per-part -> hologram when > 0.45, back when < 0.35; start
              per-part. On a switch the receiver's partial frames of unapplied parts are dropped (disclosed).
  fairness  : lockstep gets the same switch and both codings with its own generic parts.
CONTROL (C3, unchanged from BEAM4): whole = one bundle of all unapplied parts each tick, frames discarded if it does
not decode in the tick (beam4.sim_whole).
CHECKS (K.3, unchanged): C1 beam > lockstep at B = 3, 4 in all 18 cells; C3 beam > whole at B = 3, 4 in all 18 cells;
C2 no wrong adoption, zero loss: replay exact and sync(beam) = 1.0 every run; T29 reported (declared tie).
Reported: share of ticks in hologram mode per carrier x loss x budget.
Development seeds: worlds 6570, 6571; channels 6580+ (never used elsewhere; never for colours). 21 shades.
Smoke test before the run: throwaway seed 6499, shade 3, radio, not kept (switch reached hologram mode at m = 0.5).
Usage: python beam5.py run <part 0|1> ; python beam5.py analyze"""
import sys, os, json, glob, math
from collections import deque
import numpy as np
import beam1 as B1, beam2 as B2, beam4 as B4
T, NV, MS, CARRIERS = B1.T, B1.NV, B1.MS, B1.CARRIERS
SEEDS = [6570, 6571]; BUDGETS = [3, 4, 29]; TH_UP, TH_DOWN = 0.45, 0.35

def sim_route(bits, ks, Bf, fwd, back, rng_u, undet):
    """bits[u-1] = size of part u in bits (incl. its 16-bit tag); ks[u-1] = per-part frames (own envelope)."""
    held = {}; bad = {}; done = set(); applied = 0; known_applied = 0; known = {}; sync = 0; caught = 0
    mode = "part"; est = deque(maxlen=5); holo_ticks = 0; hcount = 0; hbad = False
    for t in range(1, T + 1):
        lost = fwd[t - 1][:Bf]; arrived_tick = 0
        if mode == "part":
            out = [u for u in range(known_applied + 1, t + 1) if ks[u - 1] - known.get(u, 0) > 0]
            alloc = {u: 0 for u in out}; left = Bf
            for u in out: n = min(ks[u - 1] - known.get(u, 0), left); alloc[u] += n; left -= n
            i = 0
            while left > 0 and out: alloc[out[i % len(out)]] += 1; left -= 1; i += 1
            fi = 0
            for u in out:
                n = alloc[u]
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
        if not back[t - 1]:                                     # acknowledgement arrives: syndrome + arrivals of the tick
            known_applied = applied; known = {u: (ks[u - 1] if u in done else held.get(u, 0)) for u in range(applied + 1, t + 1)}
            est.append(1 - arrived_tick / Bf)
            e = float(np.mean(est)); new = mode
            if mode == "part" and e > TH_UP: new = "holo"
            elif mode == "holo" and e < TH_DOWN: new = "part"
            if new != mode:
                mode = new; held = {u: c for u, c in held.items() if u <= applied}; bad = {}; hcount = 0; hbad = False
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
                    cs = 6580 + 1000 * ci + 100 * mi + 10 * v + SEEDS.index(sd)
                    fwd = list(B1.loss_process(car, m, np.random.default_rng(cs), 29)); back = B2.back_process(car, m, np.random.default_rng(cs + 3))
                    row = {"v": v, "sd": sd, "carrier": car, "m": m}
                    for b in BUDGETS:
                        row[str(b)] = {"beam": sim_route(bb, kb, b, fwd, back, np.random.default_rng(cs + 7), B1.UNDET),
                                       "lockstep": sim_route(bl, kl, b, fwd, back, np.random.default_rng(cs + 7), B1.UNDET),
                                       "whole": B4.sim_whole(parts, b, fwd, back, np.random.default_rng(cs + 7), B1.UNDET)}
                    out.append(row)
            zf = [np.zeros(29, bool)] * T; zb = [False] * T
            out.append({"v": v, "sd": sd, "carrier": "none", "exact": bool(exact),
                        "beam_sync": sim_route(bb, kb, 29, zf, zb, np.random.default_rng(1), 0.0)["sync"]})
            print("run", v, sd, flush=True)
    json.dump(out, open(f"diag/beam5_p{part}.json", "w"))

def analyze():
    R = []
    for f in sorted(glob.glob("diag/beam5_p*.json")): R += json.load(open(f))
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
    S["ROW_PASS"] = all(S["PASS"].values()); json.dump(S, open("diag/QUICK_BEAM5.json", "w"), indent=1); print(json.dumps(S, indent=1))

if __name__ == "__main__":
    run(int(sys.argv[2])) if sys.argv[1] == "run" else analyze()
