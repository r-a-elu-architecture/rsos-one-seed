"""LAWNEED: a cheaper Law 4 need computation, tested against the full own-future fork (owner, 23 Nov 2026 ~11:54:
"before the combined seal, design a cheaper Law 4 need computation, test it against the full fork on development
seeds, and estimate the sealed run's total laptop time"). Layer 2. Development.
Written ~12:20 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius) before any run. Owner's Law 4: map K.2.

WHY IT IS COSTLY: a landing's need = with vs without it, both futures under the organism's own policy to the end
(laws4.own_future). Five closed-loop futures per tick, each re-deciding every tick (the organism's own forks inside):
~100 min per run on the laptop.
FOUND WHILE DESIGNING (stated before any comparison is run): the organism's decisions draw tie-breaks from the world's
own generator, and the number of draws depends on the branch; so two futures that differ by one landing also meet
different world events, and part of what laws4 measures as "need" can be event noise, not the landing's effect.
The reference here therefore removes that noise:
  FULL_CRN (reference): laws4.own_future, but in every future every decision draws from a copy of the generator
           (common random numbers: the world's events are the same in both branches).
METHODS compared with FULL_CRN on the same decision points:
  FULL     : laws4.own_future as run in LAWS4 (no common randomness) - shows how much of LAWS4's need is noise.
  OPEN     : (cheap, the candidate) one closed-loop FULL_CRN future of the whole action, recording the organism's
             actions on every later tick; each "without u" branch replays that recorded plan open-loop (no
             re-deciding). Cost: 1 closed-loop future + n open-loop replays per tick.
  H5       : (cheap, reported) own policy with common randomness for 5 ticks, then defaults to the end.
CHECK for the candidate OPEN (fixed now): agreement with FULL_CRN >= 95 % of landings, and wrongly withheld (OPEN says
no need, FULL_CRN says need) <= 2 % of landings. Reported for all: agreement, wrongly withheld, wrongly kept, seconds.
SAMPLE: shades 3, 10, 17 x development seed 6530 x decision ticks 5, 15, 25, 35, 45 (organism v3 driven to the tick
with its own policy). Seed 6530 never used elsewhere; never for colours.
Usage: python lawneed.py run ; python lawneed.py analyze"""
import sys, os, json, copy, time
import numpy as np
import laws as L, laws4 as L4
G, O = L.G, L.O
SHADES = [3, 10, 17]; SEED = 6530; TICKS = [5, 15, 25, 35, 45]
worse = L4.worse

def step_crn(f, p, st):
    r = copy.deepcopy(f.rng); a = L4.step(f, p, st); f.rng = r; return a

def future(w, act, p, st, mode, plan=None, record=False):
    f = copy.deepcopy(w); ps, pd, ms, md = act; f.ms, f.md = dict(ms), dict(md); G.Shade.tick(f, ps, pd); rec = []; h = 0
    while f.t < O.T:
        if mode == "full": a = L4.step(f, p, st)
        elif mode == "crn": a = step_crn(f, p, st)
        elif mode == "open": a = plan[h]
        elif mode == "h5": a = step_crn(f, p, st) if h < 5 else None
        if a is None: ds, dd = O.defaults(f); a = (ds, dd, {i: "inside" for i in ds}, {j: "inside" for j in dd})
        if record: rec.append(a)
        f.ms, f.md = dict(a[2]), dict(a[3]); G.Shade.tick(f, a[0], a[1]); h += 1
    return f.G(), f.channels(), rec

def without(act, side, u):
    ps, pd, ms, md = act
    return ([x for x in ps if x != u], pd, ms, md) if side == "s" else (ps, [x for x in pd if x != u], ms, md)

def needs(w, act, p, st, mode):
    t0 = time.time(); landings = [("s", u) for u in act[0]] + [("d", u) for u in act[1]]
    if mode == "open":
        g, ch, plan = future(w, act, p, st, "crn", record=True)
        out = [worse(*future(w, without(act, sd, u), p, st, "open", plan=plan)[:2], g, ch) for sd, u in landings]
    else:
        g, ch, _ = future(w, act, p, st, mode)
        out = [worse(*future(w, without(act, sd, u), p, st, mode)[:2], g, ch) for sd, u in landings]
    return [bool(x) for x in out], time.time() - t0

def run():
    rows = []
    for v in SHADES:
        p = G.params(G.SH["shades"][v - 1]["node"], v); st = L4.st_of(v); w = G.Shade(SEED, p, "inside")
        while w.t < max(TICKS):
            a = L4.step(w, p, st)
            if w.t in TICKS:
                r = {"v": v, "t": int(w.t), "n": len(a[0]) + len(a[1])}
                for m in ("crn", "full", "open", "h5"):
                    r[m], r[m + "_sec"] = needs(w, a, p, st, m)
                rows.append(r); print(v, w.t, {m: (r[m], round(r[m + "_sec"])) for m in ("crn", "full", "open", "h5")}, flush=True)
                json.dump(rows, open("diag/lawneed.json", "w"))
            w.ms, w.md = a[2], a[3]; G.Shade.tick(w, a[0], a[1])

def analyze():
    R = json.load(open("diag/lawneed.json")); S = {}
    for m in ("full", "open", "h5"):
        ref = [x for r in R for x in r["crn"]]; got = [x for r in R for x in r[m]]; n = len(ref)
        S[m] = {"landings": n, "agreement": sum(a == b for a, b in zip(ref, got)) / n,
                "wrongly_withheld": sum(a and not b for a, b in zip(ref, got)) / n, "wrongly_kept": sum(b and not a for a, b in zip(ref, got)) / n,
                "sec_per_tick_mean": float(np.mean([r[m + "_sec"] for r in R]))}
    S["crn_sec_per_tick_mean"] = float(np.mean([r["crn_sec"] for r in R])); S["crn_need_rate"] = float(np.mean([x for r in R for x in r["crn"]]))
    S["PASS_open"] = S["open"]["agreement"] >= 0.95 and S["open"]["wrongly_withheld"] <= 0.02
    json.dump(S, open("diag/QUICK_LAWNEED.json", "w"), indent=1); print(json.dumps(S, indent=1))

if __name__ == "__main__":
    run() if sys.argv[1] == "run" else analyze()
