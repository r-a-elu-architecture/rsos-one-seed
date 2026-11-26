"""LIVING2: row E short test of map K.17 line E (owner OK 24 Nov 02:40). Layer 2. Development.
Written 24 Nov 2026 ~03:05 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius), before any run.
PART K LINE (row "E · living hosts"): run -> task -> living host; missing an observer above the run; structure living
twin + observer of the observer + P7 + P1; check the structure keeps its margin over the best native while the host
adapts. Host: living1.Living (tolerance +10 %/dose, resistance +10 %/heal, decaying 5 %/tick).
STRUCTURE (K.17 E line; medicine: titration against tolerance; immunology: adaptive response; control: estimator):
  the observer reads the host's ADAPTATION from its own record, not one-tick counts:
    supply: per unit, the observed consumption per tick on ticks without a dose (res before - res after), against that
            unit's first observed value; adapted when the ratio exceeds 1.3;
    drift:  per unit, heals followed by a new drift within 2 ticks, counted over the last 10 ticks; adapted at >= 2.
  response (P7 settle / re-target): a landing chosen by the structure on an adapted unit goes to the next unit by lack
            that is not adapted (the dose moves to where it still works); if none, it stays. P1 always on (v3).
  Common randomness.
ARMS: vobs2 (v3 + this observer) · v3 · three natives · beam-only, on the living twin.
CHECKS (fixed now; shades 1, 4, 7, 10, 13, 16, 19 x development seeds 6700, 6701 = 14 cells):
  E1 vobs2 > best native (max of natives and beam-only) in every cell; E2 reported: vobs2 vs v3, re-targets.
Seeds never used elsewhere; never for colours.
Usage: python living2.py run <part 0|1> ; python living2.py analyze"""
import sys, os, json, glob, copy, time
import numpy as np
import living1 as LV
L4, G, O, F4 = LV.L4, LV.G, LV.O, LV.F4
SEEDS = [6700, 6701]; SHADES = LV.SHADES

def run_obs2(sd, p, st):
    w = LV.Living(sd, p, "inside"); N = len(w.c0); base = np.full(N, np.nan); ratio = np.ones(N); heal_t = {}; redrift = []; moved = 0
    while w.t < O.T:
        r = copy.deepcopy(w.rng); a = L4.step(w, p, st); w.rng = r
        ps, pd, ms, md = list(a[0]), list(a[1]), dict(a[2]), dict(a[3])
        recent = [j for (t, j) in redrift if t >= w.t - 10]
        ad_s = ratio > 1.3; ad_d = np.array([recent.count(j) >= 2 for j in range(N)])
        for lst, D, ad, lack in ((ps, ms, ad_s, w.lack_s()), (pd, md, ad_d, w.lack_d())):
            for k, u in enumerate(list(lst)):
                if ad[u]:
                    c = next((int(x) for x in np.argsort(-lack) if int(x) not in lst and not ad[int(x)]), None)
                    if c is not None: lst[k] = c; D[c] = D.pop(u, "inside"); moved += 1
        pre = w.res.copy(); pre_dr = w.dr.copy()
        w.ms, w.md = ms, md; w.tick(ps, pd)
        drop = pre - w.res
        for i in range(N):
            if i in ps or drop[i] <= 0: continue
            if np.isnan(base[i]): base[i] = drop[i]
            elif base[i] > 0: ratio[i] = drop[i] / base[i]
        for j in pd: heal_t[j] = w.t
        for j in np.where(w.dr & ~pre_dr)[0]:
            if int(j) in heal_t and w.t - heal_t[int(j)] <= 2: redrift.append((w.t, int(j)))
    return {"G": float(w.G()), "ch": [float(x) for x in w.channels()], "moved": moved}

def run_part(part):
    out = []
    for i, v in enumerate(SHADES):
        if i % 2 != part: continue
        p = G.params(G.SH["shades"][v - 1]["node"], v); st = L4.st_of(v)
        for sd in SEEDS:
            t0 = time.time(); r = {"v": v, "sd": sd, "vobs2": run_obs2(sd, p, st), "v3": LV.run_v3(sd, p, st)}
            for a, b in O.NATS: r[f"{a}+{b}"] = F4.run(LV.Living, sd, p, (a, b))["G"]
            r["B"] = F4.run(LV.Living, sd, p, "B")["G"]; r["sec"] = round(time.time() - t0); out.append(r)
            print("cell", v, sd, round(r["vobs2"]["G"], 4), round(r["v3"]["G"], 4), r["vobs2"]["moved"], {k: round(x, 4) for k, x in r.items() if isinstance(x, float)}, flush=True)
            json.dump(out, open(f"diag/living2_p{part}.json", "w"))

def analyze():
    R = []
    for f in glob.glob("diag/living2_p*.json"): R += json.load(open(f))
    nats = [k for k in R[0] if "+" in k] + ["B"]; best = lambda r: max(r[k] for k in nats)
    S = {"cells": len(R), "E1_vobs2_gt_best_native": sum(r["vobs2"]["G"] > best(r) for r in R),
         "E1_margin_mean": float(np.mean([r["vobs2"]["G"] - best(r) for r in R])),
         "E2_vobs2_minus_v3": {"mean": float(np.mean([r["vobs2"]["G"] - r["v3"]["G"] for r in R])), "wins": sum(r["vobs2"]["G"] > r["v3"]["G"] for r in R),
                               "losses": sum(r["vobs2"]["G"] < r["v3"]["G"] for r in R)},
         "retargets_mean": float(np.mean([r["vobs2"]["moved"] for r in R]))}
    S["PASS"] = {"E1": S["E1_vobs2_gt_best_native"] == len(R)}; S["ROW_PASS"] = all(S["PASS"].values())
    json.dump(S, open("diag/QUICK_LIVING2.json", "w"), indent=1); print(json.dumps(S, indent=1))

if __name__ == "__main__":
    run_part(int(sys.argv[2])) if sys.argv[1] == "run" else analyze()
