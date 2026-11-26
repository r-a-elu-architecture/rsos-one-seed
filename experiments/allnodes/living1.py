"""LIVING1: row E short test of map K.14 + K.16 (the light lands in living hosts; layer-2 living twin). Development.
Written 24 Nov 2026 ~02:40 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius), before any run.

PART K LINE (Part K, row "E · living hosts"): where = run -> task -> living host; missing = no observer above the run;
structure = living twin (the host regulates itself against the landings) + observer of the observer + P7
explore-then-settle + P1; check = the structure keeps its margin over the best native while the host adapts.
STRUCTURE (K.14 + K.16):
  living twin  (medicine: tolerance; immunology: resistance) every dose raises that unit's consumption by 10 % (tolerance,
               decaying 5 % per tick); every heal raises that unit's drift hazard by 10 % (resistance, decaying 5 % per
               tick; capped at the world's 0.5). The host answers what lands on it.
  observer of the observer (control: self-tuning estimator) after every tick the structure compares what its last
               projection predicted for the next tick (dry units, drifted units) with what happened; calibration error =
               |predicted - observed|, running over the last 5 ticks.
  P7 explore-then-settle (dual control: probe when the model is wrong, exploit when right) if the current error exceeds
               1.5 x its running mean of the run so far: explore = the deeper search (org3 picks + the full mode beam,
               counter-shift) for that tick; otherwise settle = the shade's own structure (v3).
  P1           the budget-correct counter-shift, always on (as v3).
  Common randomness: deciding never moves the world's events.
ARMS (living twin): vobs (v3 + observer + P7) · v3 · report+popular · round+round · random+random · beam-only (B).
CHECKS (fixed now; shades 1, 4, 7, 10, 13, 16, 19 x development seeds 6660, 6661 = 14 cells):
  E1 vobs > best native (max of the three natives and beam-only) in every cell (K.14: keeps its margin);
  E2 reported: vobs vs v3 (what the observer adds), explore share.
Seeds never used elsewhere; never for colours. Smoke test before the run: 5-tick worlds, throwaway seed 6499, shade 4, not kept.
Usage: python living1.py run <part 0|1> ; python living1.py analyze"""
import sys, os, json, glob, copy, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "laws"))
import laws as L, laws4 as L4
os.chdir(HERE)
G, O, V3, X, F4, Z = L.G, L.O, L.V3, L.X, L.F4, L.Z
SEEDS = [6660, 6661]; SHADES = [1, 4, 7, 10, 13, 16, 19]

class Living(G.Shade):
    def __init__(s, seed, p, default):
        super().__init__(seed, p, default); s.c00 = s.c0.copy(); s.h00 = s.h.copy(); s.tol = np.zeros(len(s.c0)); s.res_ = np.zeros(len(s.h))
    def tick(s, ps, pd, glob=False):
        s.c0 = s.c00 * (1 + 0.1 * s.tol); s.h = np.minimum(s.h00 * (1 + 0.1 * s.res_), 0.5)
        G.Shade.tick(s, ps, pd, glob)
        s.tol *= 0.95; s.res_ *= 0.95
        for i in ps: s.tol[i] += 1
        for j in pd: s.res_[j] += 1
        s.c0, s.h = s.c00, s.h00

def explore_step(w, p, st):
    st2 = dict(st, det=1, adapt=1, cs=1); return L4.step(w, p, st2)

def run_obs(sd, p, st):
    w = Living(sd, p, "inside"); errs = []; pred = None; n_explore = 0
    while w.t < O.T:
        if pred is not None:
            errs.append(abs(pred[0] - int((w.res <= 0).sum())) + abs(pred[1] - int(w.dr.sum())))
        explore = len(errs) >= 3 and np.mean(errs[-1:]) > 1.5 * np.mean(errs) and np.mean(errs) > 0
        r = copy.deepcopy(w.rng)
        a = explore_step(w, p, st) if explore else L4.step(w, p, st); n_explore += explore
        f = copy.deepcopy(w); f.rng = copy.deepcopy(r); f.ms, f.md = dict(a[2]), dict(a[3]); Living.tick(f, list(a[0]), list(a[1]))
        pred = (int((f.res <= 0).sum()), int(f.dr.sum())); w.rng = r
        w.ms, w.md = dict(a[2]), dict(a[3]); w.tick(list(a[0]), list(a[1]))
    return {"G": float(w.G()), "ch": [float(x) for x in w.channels()], "explore": n_explore / O.T}

def run_v3(sd, p, st):
    w = Living(sd, p, "inside")
    while w.t < O.T:
        r = copy.deepcopy(w.rng); a = L4.step(w, p, st); w.rng = r; w.ms, w.md = dict(a[2]), dict(a[3]); w.tick(list(a[0]), list(a[1]))
    return {"G": float(w.G()), "ch": [float(x) for x in w.channels()]}

def run_part(part):
    out = []
    for i, v in enumerate(SHADES):
        if i % 2 != part: continue
        p = G.params(G.SH["shades"][v - 1]["node"], v); st = L4.st_of(v)
        for sd in SEEDS:
            t0 = time.time(); r = {"v": v, "sd": sd, "vobs": run_obs(sd, p, st), "v3": run_v3(sd, p, st)}
            for a, b in O.NATS: r[f"{a}+{b}"] = F4.run(Living, sd, p, (a, b))["G"]
            r["B"] = F4.run(Living, sd, p, "B")["G"]; r["sec"] = round(time.time() - t0); out.append(r)
            print("cell", v, sd, round(r["vobs"]["G"], 4), round(r["v3"]["G"], 4), {k: round(x, 4) for k, x in r.items() if isinstance(x, float)}, r["sec"], "s", flush=True)
            json.dump(out, open(f"diag/living1_p{part}.json", "w"))

def analyze():
    R = []
    for f in glob.glob("diag/living1_p*.json"): R += json.load(open(f))
    nats = [k for k in R[0] if "+" in k] + ["B"]; best = lambda r: max(r[k] for k in nats)
    S = {"cells": len(R), "E1_vobs_gt_best_native": sum(r["vobs"]["G"] > best(r) for r in R),
         "E1_margin_mean": float(np.mean([r["vobs"]["G"] - best(r) for r in R])),
         "E2_vobs_minus_v3": {"mean": float(np.mean([r["vobs"]["G"] - r["v3"]["G"] for r in R])), "wins": sum(r["vobs"]["G"] > r["v3"]["G"] for r in R)},
         "v3_gt_best_native": sum(r["v3"]["G"] > best(r) for r in R), "explore_share_mean": float(np.mean([r["vobs"]["explore"] for r in R]))}
    S["PASS"] = {"E1": S["E1_vobs_gt_best_native"] == len(R)}; S["ROW_PASS"] = all(S["PASS"].values())
    json.dump(S, open("diag/QUICK_LIVING1.json", "w"), indent=1); print(json.dumps(S, indent=1))

if __name__ == "__main__":
    run_part(int(sys.argv[2])) if sys.argv[1] == "run" else analyze()
