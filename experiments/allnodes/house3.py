"""HOUSE3: Meaning short test of map K.17 (owner OK 24 Nov 02:40). Layer 2. Development. As house2.py except:
  selection  rooms chosen against the host's own set point (physiology: homeostasis): overload when the longest run
             (max of the longest dry run and the longest drift) exceeds the 75th percentile of its own values over the
             ticks so far (from tick 5; before that: stable); uncertain and stable as house2.
  content    the selector in every room (basal ganglia): the vote of futures in every room: overload {vote, counter-
             shift, membrane}; uncertain {vote, memory, membrane}; stable {vote, memory, apoptosis, membrane}.
CHECKS as house2 (M1-M4). Development seeds 6680, 6681 (never used elsewhere; never for colours).
Written 24 Nov 2026 ~02:55 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius), before any run.
Usage: python house3.py run <part 0|1> ; python house3.py analyze"""
import sys, os, json, glob, copy, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "laws"))
import laws as L, laws4 as L4
os.chdir(HERE)
G, O, V3, X, F4, Z = L.G, L.O, L.V3, L.X, L.F4, L.Z
SEEDS = [6680, 6681]; SHADES = [1, 4, 7, 10, 13, 16, 19]; K_STRESS = 3.0
OBJS = ["vote", "memory", "cs", "apoptosis", "membrane"]
ROOMS = {"overload": ["vote", "cs", "membrane"], "uncertain": ["vote", "memory", "membrane"], "stable": ["vote", "memory", "apoptosis", "membrane"]}

class Stress(G.Shade):
    def __init__(s, seed, p, default):
        super().__init__(seed, p, default); s.h = np.minimum(s.h * K_STRESS, 0.5)

def run(W, sd, p, base, mode, objs=None, order="program"):
    w = W(sd, p, "inside"); hist = []; retired = {}; prev_dry = int((w.res <= 0).sum()); prev_dr = w.dr.copy()
    bm = "above" if "above" in p["modes"] else ("pierced" if "pierced" in p["modes"] else None); rooms_used = {}
    lvl = []
    while w.t < O.T:
        cur = max(float(np.max(w.dry)), float(np.max(w.dur)))
        if mode == "house":
            if len(lvl) >= 5 and cur > np.percentile(lvl, 75): room = "overload"
            elif int((w.dr & ~prev_dr).sum()) >= 2 or int((w.res <= 0).sum()) > prev_dry: room = "uncertain"
            else: room = "stable"
            on = set(ROOMS[room]); rooms_used[room] = rooms_used.get(room, 0) + 1
        else: on = set(objs)
        lvl.append(cur); prev_dry = int((w.res <= 0).sum()); prev_dr = w.dr.copy()
        def choose():
            ps, pd = V3.org3_picks(w) if base["det"] else O.defaults(w); ps, pd = list(ps), list(pd)
            st = dict(base, vote=int("vote" in on), mem=int("memory" in on))
            ms, md = X.beam2(w, ps, pd, p["modes"], st, {}) if base["adapt"] or "vote" in on or "memory" in on else ({i: "inside" for i in ps}, {j: "inside" for j in pd})
            if base["barrier"] and bm:
                if ps: ms[ps[0]] = bm
                if pd: md[pd[0]] = bm
            return [ps, pd, ms, md]
        def cs(a):
            if "cs" not in on: return a
            ps, pd, ms, md = a; n0 = len(ps) + len(pd); i = int(np.argmax(w.dry)); j = int(np.argmax(w.dur)); ci = cj = None
            if w.dry[i] >= 2 and i not in ps: ps = [i] + ps[:-1]; ms = {**ms, i: "inside"}; ci = i
            if w.dur[j] >= 2 and j not in pd: pd = [j] + pd[:-1]; md = {**md, j: "inside"}; cj = j
            while len(ps) + len(pd) > max(n0, 2 * O.KH):
                big = ps if len(ps) >= len(pd) else pd; keep = ci if big is ps else cj; big.pop(max(k for k, u in enumerate(big) if u != keep))
            return [ps, pd, ms, md]
        def apoptosis(a):
            if "apoptosis" not in on: return a
            ps, pd, ms, md = a; last = hist[-5:]
            for side, lst, D, fail, lack in (("s", ps, ms, w.res <= 0, w.lack_s()), ("d", pd, md, w.dr, w.lack_d())):
                for k, u in enumerate(list(lst)):
                    hits = sum(u in h[side] for h in last)
                    if (hits >= 3 and fail[u]) or retired.get((side, u), -1) >= w.t:
                        retired[(side, u)] = max(retired.get((side, u), -1), w.t + 3) if hits >= 3 and fail[u] else retired[(side, u)]
                        c = next((int(x) for x in np.argsort(-lack) if int(x) not in lst and retired.get((side, int(x)), -1) < w.t), None)
                        if c is not None: lst[k] = c; D[c] = D.pop(u, "inside")
            return [ps, pd, ms, md]
        def membrane(a):
            if "membrane" not in on: return a
            ps, pd, ms, md = a; ds, dd = O.defaults(w); m0, d0 = {i: "inside" for i in ds}, {j: "inside" for j in dd}
            if any(x > y for x, y in zip(F4.proj(w, ps, pd, ms, md)[1], F4.proj(w, ds, dd, m0, d0)[1])): return [ds, dd, m0, d0]
            return a
        r = copy.deepcopy(w.rng)                                   # common randomness: deciding never moves the world's events
        if order == "program": a = membrane(apoptosis(cs(choose())))
        else:                                                      # shuffled: membrane first, then choose, apoptosis, counter-shift
            membrane(choose()); a = cs(apoptosis(choose()))
        w.rng = r; ps, pd, ms, md = a; hist.append({"s": set(ps), "d": set(pd)})
        w.ms, w.md = ms, md; w.tick(ps, pd)
    return {"G": float(w.G()), "ch": [float(x) for x in w.channels()], "rooms": rooms_used}

def run_part(part):
    out = []
    for i, v in enumerate(SHADES):
        if i % 2 != part: continue
        p = G.params(G.SH["shades"][v - 1]["node"], v); base = dict(Z.unkey(L.ORG6[v]), cs=0, vote=0, mem=0, joint=0)
        for sd in SEEDS:
            t0 = time.time(); r = {"v": v, "sd": sd, "house": run(Stress, sd, p, base, "house")}
            for o in OBJS: r["single_" + o] = run(Stress, sd, p, base, "fixed", [o])
            r["flat"] = run(Stress, sd, p, base, "fixed", OBJS)
            r["shuffled"] = run(Stress, sd, p, base, "house", order="shuffled")
            r["native"] = F4.run(Stress, sd, p, ("report", "popular"))["G"]
            r["sec"] = round(time.time() - t0); out.append(r)
            print("cell", v, sd, {k: round(x["G"], 4) for k, x in r.items() if isinstance(x, dict) and "G" in x}, r["sec"], "s", flush=True)
            json.dump(out, open(f"diag/house3_p{part}.json", "w"))

def analyze():
    R = []
    for f in glob.glob("diag/house3_p*.json"): R += json.load(open(f))
    n = len(R); best = lambda r: max((r["single_" + o] for o in OBJS), key=lambda x: x["G"])
    res = {}
    for name, ctl in (("M1_best_single", best), ("M2_flat", lambda r: r["flat"]), ("M3_shuffled", lambda r: r["shuffled"])):
        d = [r["house"]["G"] - ctl(r)["G"] for r in R]; res[name] = {"wins": sum(x > 1e-12 for x in d), "mean": float(np.mean(d)), "cells": n,
                                                                    "pass": sum(x > 1e-12 for x in d) >= 2 * n / 3 and float(np.mean(d)) > 0}
    ch = sum(all(a <= b for a, b in zip(r["house"]["ch"], best(r)["ch"])) for r in R)
    res["M4_channels"] = {"ok": ch, "cells": n, "pass": ch >= 2 * n / 3}
    res["mean_G"] = {k: float(np.mean([r[k]["G"] for r in R])) for k in ["house", "flat", "shuffled"] + ["single_" + o for o in OBJS]}
    res["mean_G"]["native"] = float(np.mean([r["native"] for r in R])); res["rooms_used"] = {}
    for r in R:
        for k, c in r["house"]["rooms"].items(): res["rooms_used"][k] = res["rooms_used"].get(k, 0) + c
    res["ROW_PASS"] = all(res[k]["pass"] for k in ("M1_best_single", "M2_flat", "M3_shuffled", "M4_channels"))
    json.dump(res, open("diag/QUICK_HOUSE3.json", "w"), indent=1); print(json.dumps(res, indent=1))

if __name__ == "__main__":
    run_part(int(sys.argv[2])) if sys.argv[1] == "run" else analyze()
