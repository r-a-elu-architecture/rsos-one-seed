"""BEAM2: road 8, the first beam, second development loop (layer 2).
Written 23 Nov 2026 ~08:00 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius) after BEAM1 (diag/QUICK_BEAM1.md)
and the owner's instruction of 07:53, BEFORE any BEAM2 run. BEAM1's checks are not changed.

PART K LINE (unchanged from beam1.py): where = protocol -> physical channel; missing = K (applying) over a lossy carrier
never run end to end; structure = carry a structure through the physical-layer twin (light / radio / matter loss) and
land it, P3 part check and repair + P8 redundancy + READY; check = beam received and landed correctly more often than
the native carrier under the same loss, no wrong adoption.

CHANGES (owner, 07:53):
  (1) zero-loss run: no frame loss, no undetected corruption, no feedback loss.
  (2) lossy feedback: the receiver sends one acknowledgement frame per tick while it holds the outstanding message;
      the frame is lost with the same carrier process (its own stream). The sender keeps transmitting the outstanding
      message until an acknowledgement arrives, and only then creates the next message (relative to the state it
      knows the receiver holds). Same for all arms.
  (3) new native, LOCKSTEP: both ends hold the same simulation and only the inputs cross (the action, the onset mask of
      the tick, the 20 visit indices), in a generic encoding (bytes: counts, ids, mode index, a 30-bit mask, 20 one-byte
      indices; zlib if shorter), with the same parity, frame check, READY and budget, no RSOS structure (no shared
      popularity code, no eligibility pruning, no per-part check). Decoded and replayed for real on a receiver twin.
  The beam is unchanged from BEAM1: structure-coded parts (Huffman on shared popularity, eligible-only onset list),
  16-bit check per part (P3: only missing parts are resent), parity (P8), READY.
BUDGET: B = 29 frames per tick (BEAM1's budget, fixed on throwaway seed 6499).
CHECKS (fixed now):
  (1) wrong adoptions of the beam = 0;
  (2) in each of the 9 carrier x loss cells, mean sync(beam) > mean sync(lockstep) AND > max(snap, delta);
  (3) sync(beam) >= max(snap, delta, lockstep) in >= 90 % of lossy runs;
  (4) zero loss: replay exact at every tick in every run, and sync(beam) = 1.0 in every run.
REPORTED, NO CRITERION (what the beam adds beyond lockstep, labelled descriptive): frames per message (median, beam
  vs lockstep, single-tick and with backlog); a budget sweep B in {1, 2, 3, 4, 6} frames per tick with beam and
  lockstep in every carrier x loss cell (same losses, on the same runs).
Development seeds: worlds 6460, 6461; channels 6470+ (new; never used; never for colours). Smoke test before the run:
throwaway seed 6499, shade 3: beam and lockstep replays exact; single-tick median frames beam 2, lockstep 3.
Usage: python beam2.py run <part 0|1> ; python beam2.py analyze"""
import sys, os, json, glob, copy, zlib, struct, math
import numpy as np
import beam1 as B1
G, O, N, T, FB = B1.G, B1.O, B1.N, B1.T, B1.FB
NV = B1.NV; SEEDS = [6460, 6461]; MS = B1.MS; CARRIERS = B1.CARRIERS; BUD = 29; SWEEP = [1, 2, 3, 4, 6]
ARMS = ["beam", "lockstep", "snap", "delta"]

def lock_part(e, modes, t):
    ps, pd, ms, md = e["act"]; b = struct.pack("BBB", t, len(ps), len(pd))
    for u in ps: b += struct.pack("BB", u, modes.index(ms[u]))
    for u in pd: b += struct.pack("BB", u, modes.index(md[u]))
    mask = sum(1 << j for j in range(N) if e["onset"][j]); b += struct.pack("<I", mask) + bytes(int(x) for x in e["c"])
    return b

def lock_msg(lparts, a, b):
    raw = b"".join(lparts[a:b]); z = zlib.compress(raw, 9); return B1.frames(min(len(raw), len(z)) + 4)

def lock_apply(w, part, modes):
    t, ns, nd = struct.unpack("BBB", part[:3]); i = 3; ps, pd, ms, md = [], [], {}, {}
    for _ in range(ns): u, m = struct.unpack("BB", part[i:i + 2]); ps.append(u); ms[u] = modes[m]; i += 2
    for _ in range(nd): u, m = struct.unpack("BB", part[i:i + 2]); pd.append(u); md[u] = modes[m]; i += 2
    mask = struct.unpack("<I", part[i:i + 4])[0]; c = list(part[i + 4:i + 24])
    w.rng.q = [np.array([0.0 if mask >> j & 1 else 10.0 for j in range(N)]), np.array(c)]; w.ms, w.md = ms, md
    G.Shade.tick(w, ps, pd)

def prep(v, sd):
    p, rec, parts, exact = B1.precompute(v, sd); modes = p["modes"]
    lparts = [lock_part(e, modes, t + 1) for t, e in enumerate(rec)]
    w = B1.receiver(sd, p); lex = True
    for t, lp in enumerate(lparts):
        w2 = copy.deepcopy(w); w2.rng = B1.Feed(); lock_apply(w2, lp, modes); w = w2; lex &= B1.state_hash(w) == rec[t]["hash"]
    return p, rec, parts, lparts, exact, lex

def msg_k(arm, rec, parts, lparts, base_t, base_state, t):
    if arm == "beam": return B1.msg_beam(parts, base_t, t)
    if arm == "lockstep": return lock_msg(lparts, base_t, t)
    if arm == "snap": return B1.msg_snap(rec, t)
    return B1.msg_delta(rec, base_state, t)

def simulate(arm, rec, parts, lparts, Bf, fwd, back, rng_u, init_state, undet):
    known_t, known_state = 0, init_state; cur = None; got = 0; bad = False; held = None
    sync = 0; wrong = 0; caught = 0; ks = []
    for t in range(1, T + 1):
        if cur is None:
            k = msg_k(arm, rec, parts, lparts, known_t, known_state, t); cur = (t, k); got = 0; bad = False; held = None; ks.append(k)
        if held is None:
            lost = fwd[t - 1][:Bf]; arr = int((~lost).sum()); got += arr
            if arr and undet > 0: bad |= bool((rng_u.random(arr) < undet).any())
            if got >= cur[1]:
                if bad: caught += 1; got = 0; bad = False      # READY refuses; the sender keeps sending fresh parity
                else:
                    held = cur[0]
                    if held == t: sync += 1
        if held is not None and not back[t - 1]:              # acknowledgement arrives: next message from this state
            known_t, known_state = held, rec[held - 1]["state"]; cur = None
    return {"sync": sync / T, "wrong": wrong, "caught": caught, "k_median": float(np.median(ks)) if ks else None}

def back_process(carrier, m, rng):
    return [x[0] for x in B1.loss_process(carrier, m, rng, 1)]

def run(part):
    out = []
    for v in range(1, NV + 1):
        if v % 2 != part: continue
        for sd in SEEDS:
            p, rec, parts, lparts, exact, lex = prep(v, sd); init = B1.state_bytes(B1.receiver(sd, p))
            single = {"beam": float(np.median([B1.msg_beam(parts, t - 1, t) for t in range(1, T + 1)])),
                      "lockstep": float(np.median([lock_msg(lparts, t - 1, t) for t in range(1, T + 1)]))}
            for ci, car in enumerate(CARRIERS):
                for mi, m in enumerate(MS):
                    cs = 6470 + 1000 * ci + 100 * mi + 10 * v + SEEDS.index(sd)
                    fwd = list(B1.loss_process(car, m, np.random.default_rng(cs), BUD)); back = back_process(car, m, np.random.default_rng(cs + 3))
                    row = {"v": v, "sd": sd, "carrier": car, "m": m}
                    for a in ARMS: row[a] = simulate(a, rec, parts, lparts, BUD, fwd, back, np.random.default_rng(cs + 7), init, B1.UNDET)
                    row["sweep"] = {str(b): {a: simulate(a, rec, parts, lparts, b, fwd, back, np.random.default_rng(cs + 7), init, B1.UNDET)["sync"]
                                             for a in ("beam", "lockstep")} for b in SWEEP}
                    out.append(row)
            zf = [np.zeros(BUD, bool)] * T; zb = [False] * T
            out.append({"v": v, "sd": sd, "carrier": "none", "m": 0.0, "exact": bool(exact), "lock_exact": bool(lex), "single_k": single,
                        **{a: simulate(a, rec, parts, lparts, BUD, zf, zb, np.random.default_rng(1), init, 0.0) for a in ARMS}})
            print("run", v, sd, exact, lex, single, flush=True)
    json.dump(out, open(f"diag/beam2_p{part}.json", "w"))

def analyze():
    R = []
    for f in sorted(glob.glob("diag/beam2_p*.json")): R += json.load(open(f))
    lossy = [r for r in R if r["carrier"] != "none"]; zero = [r for r in R if r["carrier"] == "none"]; cells = {}
    for r in lossy:
        c = cells.setdefault(f"{r['carrier']}|{r['m']}", {a: [] for a in ARMS}); [c[a].append(r[a]["sync"]) for a in ARMS]
    C = {k: {a: float(np.mean(v)) for a, v in c.items()} for k, c in cells.items()}
    S = {"wrong_beam": sum(r["beam"]["wrong"] for r in R), "caught_by_READY": {a: sum(r[a]["caught"] for r in lossy) for a in ARMS}, "cells": C}
    S["cells_beam_gt_lockstep"] = sum(c["beam"] > c["lockstep"] for c in C.values())
    S["cells_beam_gt_snap_delta"] = sum(c["beam"] > max(c["snap"], c["delta"]) for c in C.values())
    S["runs_ge"] = (sum(r["beam"]["sync"] >= max(r[a]["sync"] for a in ARMS[1:]) for r in lossy), len(lossy))
    S["runs_beam_gt_lock"] = sum(r["beam"]["sync"] > r["lockstep"]["sync"] for r in lossy); S["runs_beam_lt_lock"] = sum(r["beam"]["sync"] < r["lockstep"]["sync"] for r in lossy)
    S["zero"] = {"exact": sum(r["exact"] for r in zero), "lock_exact": sum(r["lock_exact"] for r in zero), "runs": len(zero),
                 "beam_sync_1": sum(r["beam"]["sync"] == 1.0 for r in zero), "sync_mean": {a: float(np.mean([r[a]["sync"] for r in zero])) for a in ARMS}}
    S["DESCRIPTIVE_frames_single_tick_median"] = {a: float(np.median([r["single_k"][a] for r in zero])) for a in ("beam", "lockstep")}
    S["DESCRIPTIVE_frames_per_message_median_lossy"] = {a: float(np.median([r[a]["k_median"] for r in lossy])) for a in ARMS}
    sw = {}
    for r in lossy:
        for b, d in r["sweep"].items():
            c = sw.setdefault(f"B{b}|{r['carrier']}|{r['m']}", {"beam": [], "lockstep": []}); c["beam"].append(d["beam"]); c["lockstep"].append(d["lockstep"])
    S["DESCRIPTIVE_budget_sweep"] = {k: {a: round(float(np.mean(v)), 3) for a, v in c.items()} for k, c in sw.items()}
    S["PASS"] = {"no_wrong": S["wrong_beam"] == 0, "beam_gt_lockstep_9": S["cells_beam_gt_lockstep"] == 9, "beam_gt_snap_delta_9": S["cells_beam_gt_snap_delta"] == 9,
                 "runs_90": S["runs_ge"][0] >= 0.9 * S["runs_ge"][1], "zero_exact": S["zero"]["exact"] == S["zero"]["runs"] and S["zero"]["beam_sync_1"] == S["zero"]["runs"]}
    S["ROW_PASS"] = all(S["PASS"].values()); json.dump(S, open("diag/QUICK_BEAM2.json", "w"), indent=1); print(json.dumps(S, indent=1))

if __name__ == "__main__":
    if sys.argv[1] == "run": run(int(sys.argv[2]))
    else: analyze()
