"""ORGANS1: the heterogeneous host of map K.18 (owner OK 24 Nov 06:33) and the short tests of Meaning (house4), D (births5)
and E (living3) on it. Layer 2. Development. Written 24 Nov 2026 ~06:40 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn,
Vilnius), before any run.

HOST (K.18, fixed now): one twin world of 30 units = four organs, each with its own law, one shared budget of 4 per tick.
  heart  units 0-7   pump: consumption x1.8, drift hazard x0.5 (supply decides)
  kidney units 8-15  filter: drift hazard x2.5 (drift decides; the world's graph spreads it)
  liver  units 16-22 transform: every 6 ticks a burst drifts 1/3 of its units (own generator)
  lungs  units 23-29 exchange: a drifted lungs unit j doubles the hazard of units j - 23 (heart), j - 15 (kidney)
         in the next tick (coupling to the other organs)
  Organ deficit = (dry + drifted units of the organ) / organ size; an organ is in deficit when its value exceeds the 75th
  percentile of its own past values (set point, K.17); the organ in deficit with the largest excess is the tick's organ.
  Common randomness: deciding never moves the world's events.
MEANING (house4; K.12 + K.17 + K.18): one room per organ; the room serves its organ's law: two of the four landings (one
  supply, one drift) go to the organ's units of highest lack, with the room's object: heart -> counter-shift; kidney ->
  vote of futures; liver -> memory of the burst (heal the liver units before the next burst tick); lungs -> heal the
  drifted lungs units first. Membrane last (checklist order). No organ in deficit -> the shade's own structure (v3).
  Controls: single_<organ> (that room every tick), flat (each of the four organs gets one landing every tick), shuffled
  (the room chosen at random each tick: same rooms, no state). Checks M1-M4 as house2 (>= 2/3 of cells, mean > 0;
  channels not worse than the best single in >= 2/3).
D (births5; K.13 + K.17 + K.18): parents A = shade v, B = shade v+1 (ORG6 own + budget-correct counter-shift). Child host
  = the organ host with both parents' pressures. The book per organ: on growth seed 6732, at every tick both parents'
  actions are forked from the same state (defaults after) and the parent whose action leaves the organ with the higher
  working fraction at the end is booked for that organ (majority over ticks). The child: each tick both parents decide;
  each organ gets the landings its booked parent puts in it; the budget of 4 is filled by organ deficit order.
  Checks: B1 child > max(parents) in the child host in >= 2/3 of cells, mean > 0; B2 child >= parent - 0.005 in that
  parent's own organ host in >= 90 % of (cell, parent).
E (living3; K.14 + K.17 + K.18): each organ adapts differently: heart tolerance (+10 % consumption per dose, decay 5 %),
  kidney resistance (+10 % hazard per heal, decay 5 %), liver burst period shortens by one tick every 15 ticks (6, 5, 4,
  3), lungs coupling grows by 10 % per heal on lungs. The observer reads per organ the response per landing (deficit
  change of the organ over the tick after a landing in it, running over 10 ticks); a landing in an organ whose response
  is the worst of the four and not better than zero moves to the highest-lack unit of the organ with the best response.
  Check E1: structure > best native (three natives, beam-only) in every cell; E2 reported vs v3.
CELLS: shades 1, 4, 7, 10, 13, 16, 19 x development seeds 6720, 6721 (14). Seeds never used elsewhere; never for colours.
Usage: python organs.py run <test house|births|living> <part 0|1> ; python organs.py analyze <test>"""
import sys, os, json, glob, copy, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "laws"))
import laws as L, laws4 as L4
os.chdir(HERE)
G, O, V3, X, F4, Z = L.G, L.O, L.V3, L.X, L.F4, L.Z
SEEDS = [6720, 6721]; SHADES = [1, 4, 7, 10, 13, 16, 19]; GROW = 6732
ORG = {"heart": list(range(0, 8)), "kidney": list(range(8, 16)), "liver": list(range(16, 23)), "lungs": list(range(23, 30))}
NAMES = list(ORG)

class Organs(G.Shade):
    LIVING = False
    def __init__(s, seed, p, default):
        super().__init__(seed, p, default); n = len(s.c0)
        s.c00 = s.c0.copy(); s.h00 = s.h.copy(); s.c00[ORG["heart"]] *= 1.8; s.h00[ORG["heart"]] *= 0.5; s.h00[ORG["kidney"]] *= 2.5
        s.h00 = np.minimum(s.h00, 0.5); s.brng = np.random.default_rng(seed + 77); s.couple = np.ones(n); s.tol = np.zeros(n); s.rst = np.zeros(n)
        s.period = 6; s.ndose = {k: 0 for k in NAMES}
    def tick(s, ps, pd, glob=False):
        h = s.h00.copy(); lung_dr = s.dr[ORG["lungs"]]
        for k, j in enumerate(ORG["lungs"]):
            if lung_dr[k]:
                for t in (j - 23, j - 15):
                    if 0 <= t < 16: h[t] *= 2 * s.couple[j]
        c = s.c00.copy()
        if s.LIVING: c = c * (1 + 0.1 * s.tol); h = h * (1 + 0.1 * s.rst)
        s.c0, s.h = c, np.minimum(h, 0.5); G.Shade.tick(s, ps, pd, glob)
        if s.t % s.period == 0:
            lv = ORG["liver"]; hit = s.brng.choice(lv, len(lv) // 3, replace=False); s.dr[hit] = True; s.dur[hit] = np.maximum(s.dur[hit], 1)
        if s.LIVING:
            s.tol *= 0.95; s.rst *= 0.95
            for i in ps: s.tol[i] += 1
            for j in pd: s.rst[j] += 1
            for j in pd:
                if j in ORG["lungs"]: s.couple[j] *= 1.1
            if s.t % 15 == 0 and s.period > 3: s.period -= 1
        s.c0, s.h = s.c00, s.h00

class Living(Organs): LIVING = True

def params_both(v):
    pa, pb = G.params(G.SH["shades"][v - 1]["node"], v), G.params(G.SH["shades"][v]["node"], v + 1)
    return {**pa, "d": max(pa["d"], pb["d"]), "hz": max(pa["hz"], pb["hz"]), "cz": max(pa["cz"], pb["cz"]), "modes": sorted(set(pa["modes"]) | set(pb["modes"]))}

def deficit(w): return {k: (float((w.res[u] <= 0).mean()) + float(w.dr[u].mean())) for k, u in ORG.items()}

class Setpoint:
    def __init__(s): s.h = {k: [] for k in NAMES}
    def organ(s, w):
        d = deficit(w); best, ex = None, 0.0
        for k in NAMES:
            if len(s.h[k]) >= 5:
                e = d[k] - np.percentile(s.h[k], 75)
                if e > ex: best, ex = k, e
            s.h[k].append(d[k])
        return best

def decide(w, p, st):
    r = copy.deepcopy(w.rng); a = L4.step(w, p, st); w.rng = r; return [list(a[0]), list(a[1]), dict(a[2]), dict(a[3])]

def focus(w, a, organ, n_s=1, n_d=1):
    ps, pd, ms, md = a; u = ORG[organ]
    ls, ld = w.lack_s(), w.lack_d()
    ts = [int(x) for x in sorted(u, key=lambda i: -ls[i]) if int(x) not in ps][:n_s]
    td = [int(x) for x in sorted(u, key=lambda i: (-int(w.dr[i]), -ld[i])) if int(x) not in pd][:n_d]
    for t in ts:
        if ps: old = ps.pop(); ms.pop(old, None)
        ps.insert(0, t); ms[t] = "inside"
    for t in td:
        if pd: old = pd.pop(); md.pop(old, None)
        pd.insert(0, t); md[t] = "inside"
    return [ps, pd, ms, md]

def membrane(w, a):
    ps, pd, ms, md = a; ds, dd = O.defaults(w); m0, d0 = {i: "inside" for i in ds}, {j: "inside" for j in dd}
    r = copy.deepcopy(w.rng); bad = any(x > y for x, y in zip(F4.proj(w, ps, pd, ms, md)[1], F4.proj(w, ds, dd, m0, d0)[1])); w.rng = r
    return [ds, dd, m0, d0] if bad else a

def room_action(w, p, st, organ, mem):
    if organ == "kidney": a = decide(w, p, dict(st, vote=1)); a = focus(w, a, "kidney")
    elif organ == "heart": a = focus(w, decide(w, p, dict(st, cs=1)), "heart", 2, 0)
    elif organ == "liver":
        a = decide(w, p, dict(st, mem=1)); nxt = w.period - (w.t % w.period)
        a = focus(w, a, "liver", 0, 2 if nxt <= 1 else 1)
    else: a = focus(w, decide(w, p, st), "lungs", 0, 2)
    return membrane(w, a)

def run_house(W, sd, p, st, mode, organ=None, rng_seed=0):
    w = W(sd, p, "inside"); sp = Setpoint(); rr = np.random.default_rng(rng_seed); used = {}
    while w.t < O.T:
        if mode == "house": o = sp.organ(w)
        elif mode == "single": o = organ
        elif mode == "shuffled": sp.organ(w); o = NAMES[int(rr.integers(4))]
        else: o = "flat"
        if o is None: a = decide(w, p, st)
        elif o == "flat":
            a = decide(w, p, st)
            for k in NAMES[:2]: a = focus(w, a, k, 1, 0)
            for k in NAMES[2:]: a = focus(w, a, k, 0, 1)
            a = membrane(w, a)
        else: a = room_action(w, p, st, o, None)
        used[str(o)] = used.get(str(o), 0) + 1
        w.ms, w.md = a[2], a[3]; w.tick(a[0], a[1])
    return {"G": float(w.G()), "ch": [float(x) for x in w.channels()], "rooms": used}

def organ_score(w): return {k: 1.0 - (float((w.res[u] <= 0).mean()) + float(w.dr[u].mean())) / 2 for k, u in ORG.items()}

def book_organs(W, p, stA, stB):
    tally = {k: [0, 0] for k in NAMES}; w = W(GROW, p, "inside")
    while w.t < O.T:
        sc = []
        for st in (stA, stB):
            a = decide(w, p, st); f = copy.deepcopy(w); f.ms, f.md = a[2], a[3]; f.tick(a[0], a[1]); O.to_end(f); sc.append(organ_score(f))
        for k in NAMES:
            if sc[0][k] != sc[1][k]: tally[k][0 if sc[0][k] > sc[1][k] else 1] += 1
        a = decide(w, p, stA); w.ms, w.md = a[2], a[3]; w.tick(a[0], a[1])
    return {k: ("A" if t[0] >= t[1] else "B") for k, t in tally.items()}, tally

def run_child(W, sd, p, stA, stB, book):
    w = W(sd, p, "inside")
    while w.t < O.T:
        acts = {"A": decide(w, p, stA), "B": decide(w, p, stB)}; d = deficit(w); order = sorted(NAMES, key=lambda k: -d[k])
        cs, cd = [], []
        for side, out in ((0, cs), (1, cd)):
            for k in order:
                for u in acts[book[k]][side]:
                    if u in ORG[k] and u not in out: out.append(u)
        ps, pd = [], []
        i = 0
        while len(ps) + len(pd) < 2 * O.KH and (i < len(cs) or i < len(cd)):
            if i < len(cs) and len(ps) + len(pd) < 2 * O.KH: ps.append(cs[i])
            if i < len(cd) and len(ps) + len(pd) < 2 * O.KH: pd.append(cd[i])
            i += 1
        ms = {u: acts["A"][2].get(u, acts["B"][2].get(u, "inside")) for u in ps}; md = {u: acts["A"][3].get(u, acts["B"][3].get(u, "inside")) for u in pd}
        w.ms, w.md = ms, md; w.tick(ps, pd)
    return {"G": float(w.G()), "ch": [float(x) for x in w.channels()]}

def run_parent(W, sd, p, st):
    w = W(sd, p, "inside")
    while w.t < O.T:
        a = decide(w, p, st); w.ms, w.md = a[2], a[3]; w.tick(a[0], a[1])
    return {"G": float(w.G()), "ch": [float(x) for x in w.channels()]}

def run_living_obs(sd, p, st):
    w = Living(sd, p, "inside"); resp = {k: [] for k in NAMES}; moved = 0
    while w.t < O.T:
        a = decide(w, p, st); d0 = deficit(w)
        score = {k: (np.mean(resp[k][-10:]) if resp[k] else 0.0) for k in NAMES}
        worst = min(NAMES, key=lambda k: score[k]); best = max(NAMES, key=lambda k: score[k])
        if score[worst] <= 0 and best != worst and resp[worst]:
            for side in (0, 1):
                lst = a[side]; D = a[2 + side]; lack = w.lack_s() if side == 0 else w.lack_d()
                for idx, u in enumerate(list(lst)):
                    if u in ORG[worst]:
                        c = next((int(x) for x in sorted(ORG[best], key=lambda i: -lack[i]) if int(x) not in lst), None)
                        if c is not None: lst[idx] = c; D[c] = D.pop(u, "inside"); moved += 1
        landed = {k: any(u in ORG[k] for u in a[0] + a[1]) for k in NAMES}
        w.ms, w.md = a[2], a[3]; w.tick(a[0], a[1]); d1 = deficit(w)
        for k in NAMES:
            if landed[k]: resp[k].append(d0[k] - d1[k])
    return {"G": float(w.G()), "ch": [float(x) for x in w.channels()], "moved": moved}

def run(test, part):
    out = []
    for i, v in enumerate(SHADES):
        if i % 2 != part: continue
        p = G.params(G.SH["shades"][v - 1]["node"], v); st = L4.st_of(v)
        if test == "births":
            pc = params_both(v); pB = G.params(G.SH["shades"][v]["node"], v + 1); stA, stB = st, L4.st_of(v + 1)
            bC, tC = book_organs(Organs, pc, stA, stB); bA, _ = book_organs(Organs, p, stA, stB); bB, _ = book_organs(Organs, pB, stA, stB)
        for sd in SEEDS:
            t0 = time.time(); r = {"v": v, "sd": sd}
            if test == "house":
                r["house"] = run_house(Organs, sd, p, st, "house")
                for k in NAMES: r["single_" + k] = run_house(Organs, sd, p, st, "single", k)
                r["flat"] = run_house(Organs, sd, p, st, "flat"); r["shuffled"] = run_house(Organs, sd, p, st, "shuffled", rng_seed=sd + 5)
                r["native"] = F4.run(Organs, sd, p, ("report", "popular"))["G"]
            elif test == "births":
                r.update(book=bC, tally=tC, bookA=bA, bookB=bB, child_C=run_child(Organs, sd, pc, stA, stB, bC), parA_C=run_parent(Organs, sd, pc, stA),
                         parB_C=run_parent(Organs, sd, pc, stB), child_A=run_child(Organs, sd, p, stA, stB, bA), parA_A=run_parent(Organs, sd, p, stA),
                         child_B=run_child(Organs, sd, pB, stA, stB, bB), parB_B=run_parent(Organs, sd, pB, stB))
            else:
                r["vobs"] = run_living_obs(sd, p, st); r["v3"] = run_parent(Living, sd, p, st)
                for a_, b_ in O.NATS: r[f"{a_}+{b_}"] = F4.run(Living, sd, p, (a_, b_))["G"]
                r["B"] = F4.run(Living, sd, p, "B")["G"]
            r["sec"] = round(time.time() - t0); out.append(r)
            print(test, v, sd, {k: round(x["G"], 4) if isinstance(x, dict) and "G" in x else x for k, x in r.items() if k not in ("tally",)}, flush=True)
            json.dump(out, open(f"diag/organs_{test}_p{part}.json", "w"))

def analyze(test):
    R = []
    for f in glob.glob(f"diag/organs_{test}_p*.json"): R += json.load(open(f))
    n = len(R); S = {"cells": n}
    if test == "house":
        best = lambda r: max((r["single_" + k] for k in NAMES), key=lambda x: x["G"])
        for name, ctl in (("M1_best_single", best), ("M2_flat", lambda r: r["flat"]), ("M3_shuffled", lambda r: r["shuffled"])):
            d = [r["house"]["G"] - ctl(r)["G"] for r in R]
            S[name] = {"wins": sum(x > 1e-12 for x in d), "mean": float(np.mean(d)), "pass": sum(x > 1e-12 for x in d) >= 2 * n / 3 and float(np.mean(d)) > 0}
        ch = sum(all(a <= b for a, b in zip(r["house"]["ch"], best(r)["ch"])) for r in R); S["M4_channels"] = {"ok": ch, "pass": ch >= 2 * n / 3}
        S["mean_G"] = {k: float(np.mean([r[k]["G"] for r in R])) for k in ["house", "flat", "shuffled"] + ["single_" + k for k in NAMES]}
        S["mean_G"]["native"] = float(np.mean([r["native"] for r in R]))
        S["ROW_PASS"] = all(S[k]["pass"] for k in ("M1_best_single", "M2_flat", "M3_shuffled", "M4_channels"))
    elif test == "births":
        d = [r["child_C"]["G"] - max(r["parA_C"]["G"], r["parB_C"]["G"]) for r in R]
        own = [r["child_A"]["G"] >= r["parA_A"]["G"] - 0.005 for r in R] + [r["child_B"]["G"] >= r["parB_B"]["G"] - 0.005 for r in R]
        S.update(B1={"wins": sum(x > 1e-12 for x in d), "mean": float(np.mean(d))}, B2=[sum(own), len(own)],
                 mixed_books=sum(len(set(r["book"].values())) > 1 for r in R))
        S["PASS"] = {"B1": S["B1"]["wins"] >= 2 * n / 3 and S["B1"]["mean"] > 0, "B2": sum(own) >= 0.9 * len(own)}; S["ROW_PASS"] = all(S["PASS"].values())
    else:
        nats = [k for k in R[0] if "+" in k] + ["B"]; best = lambda r: max(r[k] for k in nats)
        S.update(E1=sum(r["vobs"]["G"] > best(r) for r in R), E1_margin=float(np.mean([r["vobs"]["G"] - best(r) for r in R])),
                 E2={"mean": float(np.mean([r["vobs"]["G"] - r["v3"]["G"] for r in R])), "wins": sum(r["vobs"]["G"] > r["v3"]["G"] for r in R),
                     "losses": sum(r["vobs"]["G"] < r["v3"]["G"] for r in R)}, moved=float(np.mean([r["vobs"]["moved"] for r in R])))
        S["ROW_PASS"] = S["E1"] == n
    json.dump(S, open(f"diag/QUICK_ORGANS_{test}.json", "w"), indent=1); print(json.dumps(S, indent=1))

if __name__ == "__main__":
    run(sys.argv[2], int(sys.argv[3])) if sys.argv[1] == "run" else analyze(sys.argv[2])
