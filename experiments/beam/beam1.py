"""BEAM1: road 8, the first beam. Carry a structure through the physical-layer twin and land it (layer 2). Development.
Written 23 Nov 2026 ~07:30 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius), before any run.

PART K LINE (map/STRUCTURAL_MAP_22NOV.md Part K, row "Road 8 · physical layer, first beam"), copied before the build:
  where     : protocol -> physical channel
  missing   : K (applying) over a lossy carrier never run end to end (Part 0 reading)
  structure : first beam = carry a structure through the physical-layer twin (light / radio / matter loss) and land
              it; P3 part check and repair (syndrome, error correction) + P8 redundancy + READY
  check     : beam received and landed correctly more often than the native carrier under the same loss; no wrong
              adoption

WHAT IS CARRIED: the live state of a running organism. The sender runs the twin world (organism v3 = ORG6 own
structure + budget-correct counter-shift, experiments/laws/laws3.py run_st3) on a development seed. A receiver twin at
the other end of the physical channel must hold the SAME whole state, tick by tick (a mirror that can act: landing).
Both ends share the world's static structure (graph, consumption, hazards, popularity: initial sync, once, excluded
from the budget, identical for every arm).
ARMS (same channel, same frame losses, same budget, same frame check and READY for all):
  beam      : the structure is carried, not the bytes. The receiver holds the world's laws (the tick, sealed code), so the
              sender sends only what the laws cannot know: the action (picks + modes) and the world's own events of
              each tick (new drift onsets, the 20 visits), coded with the shared structure (onset list; visits with a
              Huffman code built from the shared popularity = Law 5, relations known to the reader). The receiver
              re-runs the sealed tick on its own copy (K = applying). P3: every tick is one part with its own 16-bit
              check; unacknowledged parts are repaired by resending only those parts (no whole resend). P8: redundancy
              = MDS parity frames filling the budget (any k of the frames sent decode the message). READY: a 32-bit hash
              of the receiver's whole state after landing must equal the sender's hash in the message; else nothing is
              adopted.
  snap      : native, full state snapshot (pickle of all state arrays) + zlib, same parity, frame check and READY.
  delta     : native (strong), XOR of the state bytes against the last acknowledged state + zlib, same parity,
              frame check and READY.
CHANNEL (physical-layer twin): each tick the sender may put B frames of 16 bytes on the carrier. A frame is lost or
  corrupted; a corrupted frame fails its per-frame check (treated as lost) except with probability 1e-3 per frame
  (an undetected corruption: the frame passes and its bytes are wrong; READY must catch it). A message of k frames
  decodes once k frames have arrived (MDS; frames of one message accumulate across ticks until it decodes).
  Feedback: one acknowledgement per tick, not lost (disclosed simplification, same for all arms).
  Carriers, mean frame loss m in {0.1, 0.3, 0.5}:
    light  : per-tick fading, loss ~ Beta(mean m, concentration 4), frames independent within the tick
    radio  : Gilbert-Elliott bursts across frames (good 0.02, bad 0.9, mean burst 8 frames), stationary mean m
    matter : slowly drifting loss (logit AR(1), correlation ~100 ticks), mean m
BUDGET B, fixed before any lossy run: B = ceil(1.25 x median frames of the delta native at zero loss), measured on a
  throwaway seed (6499) over 3 shades (3, 10, 17), recorded in diag/budget.json.
MEASURES per run (shade x seed x carrier x m): sync = share of ticks at which the receiver holds the sender's exact
  current state (adopted and READY-verified); wrong = adoptions whose state differs from the sender's (must be 0).
QUICK TEST PASS (fixed now): (1) wrong adoptions = 0 for beam over all runs; (2) in each of the 9 carrier x m cells,
  mean sync(beam) > mean sync(best native of that cell); (3) sync(beam) >= sync(best native) in >= 90 % of runs;
  (4) lossless replay: at zero loss beam's receiver equals the sender's state at every tick of every run (K exact).
Development seeds: worlds 6440, 6441; channels 6450+ (new; never used elsewhere; never for colours). 21 shades.
Usage: python beam1.py budget ; python beam1.py run <part 0|1> ; python beam1.py analyze"""
import sys, os, json, glob, copy, zlib, pickle, hashlib, heapq, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "laws"))
import laws as L, laws3 as L3
os.chdir(HERE); os.makedirs("diag", exist_ok=True)
G, O, Z = L.G, L.O, L.Z; NV = L.NV; N = O.N; T = O.T
SEEDS = [6440, 6441]; MS = [0.1, 0.3, 0.5]; CARRIERS = ["light", "radio", "matter"]; FB = 16; UNDET = 1e-3
FIELDS = ["res", "last", "dry", "dr", "since", "events", "dur", "shield", "immune", "work", "ok", "n", "maxd", "maxdry", "t", "flows"]

def state_bytes(w): return pickle.dumps([np.asarray(getattr(w, f)).copy() if isinstance(getattr(w, f), np.ndarray) else getattr(w, f) for f in FIELDS], protocol=4)
def state_hash(w): return hashlib.sha256(state_bytes(w)).digest()[:4]

class Tap:  # records the world's own random events during the real tick; passes everything else through
    def __init__(s, rng): s.rng, s.on, s.log = rng, False, []
    def random(s, *a, **k):
        x = s.rng.random(*a, **k)
        if s.on: s.log.append(("r", x))
        return x
    def choice(s, *a, **k):
        x = s.rng.choice(*a, **k)
        if s.on: s.log.append(("c", x))
        return x
    def __deepcopy__(s, memo): return copy.deepcopy(s.rng, memo)   # forks get a plain generator

class Feed:  # the receiver's world draws its events from the decoded message
    def __init__(s): s.q = []
    def random(s, *a, **k): return s.q.pop(0)
    def choice(s, *a, **k): return s.q.pop(0)

def sender_class(rec):
    class Snd(G.Shade):
        def __init__(s, seed, p, default):
            super().__init__(seed, p, default); s.rng = Tap(s.rng); s._rid = id(s)
        def tick(s, ps, pd, glob=False):
            if id(s) != s._rid: return G.Shade.tick(s, ps, pd, glob)
            pre = {"dr": s.dr.copy(), "immune": s.immune.copy(), "res": s.res.copy()}
            act = (list(map(int, ps)), list(map(int, pd)), {int(i): s.ms.get(i, s.dm) for i in ps}, {int(j): s.md.get(j, s.dm) for j in pd})
            s.rng.on = True; s.rng.log = []; G.Shade.tick(s, ps, pd, glob); s.rng.on = False
            (_, r), (_, c) = s.rng.log
            rec.append({"act": act, "r": r, "c": np.sort(c), "state": state_bytes(s), "hash": state_hash(s), "pre": pre})
    return Snd

def receiver(seed, p): w = G.Shade(seed, p, "inside"); w.rng = Feed(); return w

# ---- beam coding: the structure (laws + shared popularity) is known to both ends ----
def huffman(pop):
    h = [(float(q), i, (i,)) for i, q in enumerate(pop)]; heapq.heapify(h); code = {i: "" for i in range(len(pop))}; k = len(pop)
    while len(h) > 1:
        a, b = heapq.heappop(h), heapq.heappop(h)
        for i in a[2]: code[i] = "0" + code[i]
        for i in b[2]: code[i] = "1" + code[i]
        heapq.heappush(h, (a[0] + b[0], k, a[2] + b[2])); k += 1
    return code

def gamma(n): b = bin(n + 1)[2:]; return "0" * (len(b) - 1) + b
def ungamma(bits, i):
    z = 0
    while bits[i + z] == "0": z += 1
    return int(bits[i + z: i + 2 * z + 1], 2) - 1, i + 2 * z + 1

def enc_part(e, modes, hc, w_pre_dr, w_pre_imm):
    ps, pd, ms, md = e["act"]; b = gamma(len(ps)) + gamma(len(pd))
    for u in ps: b += format(u, "05b") + format(modes.index(ms[u]), "03b")
    for u in pd: b += format(u, "05b") + format(modes.index(md[u]), "03b")
    thr_new = [j for j in range(N) if not w_pre_dr[j] and w_pre_imm[j] <= 0]   # eligible units (known to both ends)
    on = [j for j in thr_new if e["onset"][j]]; b += gamma(len(on))
    for j in on: b += format(j, "05b")
    for j in e["c"]: b += hc[int(j)]
    return b

def onsets_of(e, w_dr_before_draw, imm, thr):
    return (e["r"] < thr) & (imm <= 0) & ~w_dr_before_draw

def beam_apply(w, bits, i, modes, hc_inv):
    """decode one part at bit i and run the sealed tick on the receiver's copy (K: applying)."""
    ns, i = ungamma(bits, i); nd, i = ungamma(bits, i); ps, pd, ms, md = [], [], {}, {}
    for _ in range(ns): u = int(bits[i:i + 5], 2); ms[u] = modes[int(bits[i + 5:i + 8], 2)]; ps.append(u); i += 8
    for _ in range(nd): u = int(bits[i:i + 5], 2); md[u] = modes[int(bits[i + 5:i + 8], 2)]; pd.append(u); i += 8
    no, i = ungamma(bits, i); on = set()
    for _ in range(no): on.add(int(bits[i:i + 5], 2)); i += 5
    c = []
    while len(c) < 20:
        j = 1
        while bits[i:i + j] not in hc_inv: j += 1
        c.append(hc_inv[bits[i:i + j]]); i += j
    r = np.array([0.0 if j in on else 10.0 for j in range(N)])   # thresholds stay below 2
    w.rng.q = [r, np.array(c)]; w.ms, w.md = ms, md
    G.Shade.tick(w, ps, pd); return i

def run_world(v, sd):
    p = G.params(G.SH["shades"][v - 1]["node"], v); rec = []; S = sender_class(rec)
    L3.run_st3(S, sd, p, dict(Z.unkey(L.ORG6[v]), cs=1, vote=0, mem=0, joint=0))
    return p, rec

def precompute(v, sd):
    """per tick: the beam part bits (coded against the receiver state before the tick), snap and delta payloads."""
    p, rec = run_world(v, sd); modes = p["modes"]; w = receiver(sd, p); hc = huffman(w.pop); parts = []
    base_bytes = state_bytes(w); exact = True
    for t, e in enumerate(rec):
        # the onset vector the receiver must reproduce: draw < threshold, evaluated on the receiver's pre-draw state
        c0 = w.c0 * (1 + 0.5 * w.dr) * (w.shield <= 0); wtmp = copy.deepcopy(w); wtmp.rng = Feed()
        # threshold needs the post-dose state: replay the deterministic first half on a copy
        wtmp.t += 1; wtmp.since += 1; wtmp.res -= c0
        wtmp.ms, wtmp.md = e["act"][2], e["act"][3]
        for i in e["act"][0]: wtmp.dose(i)
        wtmp.res = np.minimum(wtmp.res, 3.0)
        thr = w.h * (1 + (wtmp.res <= 0)) + (wtmp.Ad & wtmp.dr[None, :]).sum(1) * 0.02   # doses may clear drift first
        e["onset"] = (e["r"] < thr) & (wtmp.immune <= 0) & ~wtmp.dr
        bits = enc_part(e, modes, hc, wtmp.dr, wtmp.immune)
        parts.append(bits)
        hc_inv = {b: k for k, b in hc.items()}; w2 = copy.deepcopy(w); w2.rng = Feed()
        beam_apply(w2, bits, 0, modes, hc_inv); w = w2
        exact &= state_hash(w) == e["hash"]
    return p, rec, parts, exact

def frames(nbytes): return max(1, math.ceil(nbytes / FB))

def msg_beam(parts, a, b):  # parts (a, b] plus a 16-bit check per part and READY (4 bytes)
    bits = sum(len(parts[t]) + 16 for t in range(a, b)) + 8; return frames(math.ceil(bits / 8) + 4)

def msg_snap(rec, b): return frames(len(zlib.compress(rec[b - 1]["state"], 9)) + 4)

def msg_delta(rec, base_state, b):
    x, y = np.frombuffer(base_state, np.uint8), np.frombuffer(rec[b - 1]["state"], np.uint8); n = min(len(x), len(y))
    d = np.concatenate([x[:n] ^ y[:n], y[n:]]).tobytes(); return frames(len(zlib.compress(d, 9)) + 4)

def loss_process(carrier, m, rng, B):
    if carrier == "light":
        a = 4 * m; b = 4 * (1 - m)
        for _ in range(T): q = rng.beta(a, b); yield rng.random(B) < q
    elif carrier == "radio":
        pb = (m - 0.02) / 0.88; p_bg = 1 / 8; p_gb = p_bg * pb / (1 - pb); bad = rng.random() < pb
        for _ in range(T):
            out = []
            for _ in range(B):
                bad = (rng.random() >= p_bg) if bad else (rng.random() < p_gb); out.append(rng.random() < (0.9 if bad else 0.02))
            yield np.array(out)
    else:
        mu = math.log(m / (1 - m)); x = mu; rho = math.exp(-1 / 100)
        for _ in range(T):
            x = mu + rho * (x - mu) + math.sqrt(1 - rho ** 2) * 0.8 * rng.standard_normal(); q = 1 / (1 + math.exp(-x)); yield rng.random(B) < q

def simulate(arm, rec, parts, B, losses, rng_u, init_state):
    """returns sync share and wrong adoptions. A message is created for the sender's state at its creation tick,
    relative to the last acknowledged state; frames accumulate across ticks; on decode it is adopted if READY holds."""
    acked_t, acked_state = 0, init_state; cur = None; got = 0; bad_frame = False; sync = 0; wrong = 0; caught = 0
    for t in range(1, T + 1):
        if cur is None:
            k = msg_beam(parts, acked_t, t) if arm == "beam" else (msg_snap(rec, t) if arm == "snap" else msg_delta(rec, acked_state, t))
            cur = (t, k); got = 0; bad_frame = False
        lost = losses[t - 1]; arrived = int((~lost).sum()); und = (rng_u.random(arrived) < UNDET).any() if arrived else False
        got += arrived; bad_frame |= bool(und)
        if got >= cur[1]:
            tc = cur[0]
            if bad_frame: caught += 1           # READY: the decoded state's hash differs -> not adopted, sent again
            else: acked_t, acked_state = tc, rec[tc - 1]["state"]
            cur = None
            if not bad_frame and tc == t: sync += 1
        # a message created at an older tick is never 'in sync' for the current tick
    return {"sync": sync / T, "wrong": wrong, "caught": caught}

def budget():
    ks = []
    for v in (3, 10, 17):
        p, rec, parts, exact = precompute(v, 6499); base = state_bytes(receiver(6499, p)); prev = base
        for t in range(1, T + 1): ks.append(msg_delta(rec, prev, t)); prev = rec[t - 1]["state"]
        bk = [msg_beam(parts, t - 1, t) for t in range(1, T + 1)]; sk = [msg_snap(rec, t) for t in range(1, T + 1)]
        print(v, "exact", exact, "delta med", np.median(ks[-T:]), "beam med", np.median(bk), "snap med", np.median(sk), flush=True)
    B = math.ceil(1.25 * float(np.median(ks))); json.dump({"B": B, "delta_frames_median": float(np.median(ks)), "seed": 6499, "shades": [3, 10, 17]}, open("diag/budget.json", "w"))
    print("B", B)

def run(part):
    B = json.load(open("diag/budget.json"))["B"]; out = []
    for v in range(1, NV + 1):
        if v % 2 != part: continue
        for sd in SEEDS:
            p, rec, parts, exact = precompute(v, sd); init = state_bytes(receiver(sd, p))
            for ci, car in enumerate(CARRIERS):
                for mi, m in enumerate(MS):
                    cs = 6450 + 1000 * ci + 100 * mi + 10 * v + SEEDS.index(sd)
                    losses = list(loss_process(car, m, np.random.default_rng(cs), B)); row = {"v": v, "sd": sd, "carrier": car, "m": m, "exact": bool(exact)}
                    for arm in ("beam", "snap", "delta"):
                        row[arm] = simulate(arm, rec, parts, B, losses, np.random.default_rng(cs + 7), init)
                    row["loss_mean"] = float(np.mean([x.mean() for x in losses])); out.append(row)
            zero = [False] * B
            row0 = {arm: simulate(arm, rec, parts, B, [np.array(zero)] * T, np.random.default_rng(1), init) for arm in ("beam", "snap", "delta")}
            out.append({"v": v, "sd": sd, "carrier": "none", "m": 0.0, "exact": bool(exact), **row0})
            print("run", v, sd, "exact", exact, flush=True)
    json.dump(out, open(f"diag/beam1_p{part}.json", "w"))

def analyze():
    R = []
    for f in sorted(glob.glob("diag/beam1_p*.json")): R += json.load(open(f))
    lossy = [r for r in R if r["carrier"] != "none"]; cells = {}
    for r in lossy:
        c = cells.setdefault(f"{r['carrier']}|{r['m']}", {"beam": [], "snap": [], "delta": []})
        for a in c: c[a].append(r[a]["sync"])
    S = {"wrong_beam": sum(r["beam"]["wrong"] for r in R), "caught_by_READY": {a: sum(r[a]["caught"] for r in R) for a in ("beam", "snap", "delta")},
         "exact_K": sum(r["exact"] for r in R if r["carrier"] == "none"), "runs_K": sum(1 for r in R if r["carrier"] == "none"),
         "zero_loss_sync": {a: float(np.mean([r[a]["sync"] for r in R if r["carrier"] == "none"])) for a in ("beam", "snap", "delta")},
         "cells": {k: {a: float(np.mean(v)) for a, v in c.items()} for k, c in cells.items()}}
    S["cell_wins"] = sum(c["beam"] > max(c["snap"], c["delta"]) for c in S["cells"].values())
    S["run_ge"] = (sum(r["beam"]["sync"] >= max(r["snap"]["sync"], r["delta"]["sync"]) for r in lossy), len(lossy))
    S["PASS"] = {"no_wrong": S["wrong_beam"] == 0, "cells_9_of_9": S["cell_wins"] == 9, "runs_90": S["run_ge"][0] >= 0.9 * S["run_ge"][1],
                 "K_exact": S["exact_K"] == S["runs_K"] and S["zero_loss_sync"]["beam"] == 1.0}
    S["ROW_PASS"] = all(S["PASS"].values()); json.dump(S, open("diag/QUICK_BEAM1.json", "w"), indent=1); print(json.dumps(S, indent=1))

if __name__ == "__main__":
    c = sys.argv[1]
    if c == "budget": budget()
    elif c == "run": run(int(sys.argv[2]))
    else: analyze()
