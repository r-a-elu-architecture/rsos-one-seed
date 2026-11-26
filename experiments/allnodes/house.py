"""THE HOUSE as the architect (Meaning row; map Part J.3 'Row Meaning'). Development only until sealed.
Time: 23 Nov 2026, UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius.
CLAUDE.md 1a: house = architecture, rooms = states, objects = models; the architect selects which model runs in which
state. Bound to the twin world (organism v2 = org7.run_st2 roles, unchanged, hash-checked through org7 -> org5):
  rooms    read by the observer each tick from the host's own state (threshold 2, as counter-shift):
           'dry'   the supply side is under pressure (longest dry run >= 2 and >= longest drift)
           'drift' the drift side is under pressure (longest drift > longest dry run and >= 2)
           'calm'  neither side under pressure
  objects  the shade's 4 best admissible structures in its ORG6 selection table (Law 0 kept), each with counter-shift
  house    one object per room; built by one pass of coordinate ascent from 'own in every room' on growth seeds
Controls (same content, different structure):
  fixed    the best SINGLE object of the same 4, chosen on the same growth seeds (no rooms)
  flat     all roles of the 4 objects switched on at once (identical content as one list, no routing)
  shuffled the house's objects with the rooms permuted (switching without the state reading)
Usage: python house.py <growth seeds a-b> <eval seeds a-b> <out.json> [shades, e.g. 1,3,5]"""
import sys, os, json, hashlib, itertools
import numpy as np
from multiprocessing import Pool
os.chdir(os.path.dirname(os.path.abspath(__file__)))
assert hashlib.sha256(open("org6.py", "rb").read()).hexdigest() in open("SEAL_ORG6.txt").read()
import org6 as P6, org7 as X
G, O, V3, F4, unkey = X.G, X.O, X.V3, X.F4, X.Z.unkey
T = P6.tables(); ROOMS = ["dry", "drift", "calm"]; TH = 2
EXTRA = {"cs": 1, "cs_th": 2, "vote": 0, "mem": 0, "joint": 0}

def obj(c): return dict(unkey(c), **EXTRA)

def room(w):
    a, b = float(np.max(w.dry)), float(np.max(w.dur))
    if a >= TH and a >= b: return "dry"
    if b >= TH: return "drift"
    return "calm"

def run_house(W, seed, p, assign):
    """assign: room -> structure dict. Body = org7.run_st2 with the structure chosen per tick by the room."""
    w = W(seed, p, "inside"); bm = "above" if "above" in p["modes"] else ("pierced" if "pierced" in p["modes"] else None); memo = {}
    while w.t < O.T:
        st = assign[room(w)]
        ps, pd = V3.org3_picks(w) if st["det"] else O.defaults(w); ps, pd = list(ps), list(pd)
        if st["cs"]:
            i = int(np.argmax(w.dry)); j = int(np.argmax(w.dur))
            if w.dry[i] >= TH and i not in ps: ps = [i] + ps[:-1]
            if w.dur[j] >= TH and j not in pd: pd = [j] + pd[:-1]
        ms, md = {i: "inside" for i in ps}, {j: "inside" for j in pd}
        if st["adapt"]: ms, md = X.beam2(w, ps, pd, p["modes"], st, memo)
        if st["barrier"] and bm:
            if ps: ms[ps[0]] = bm
            if pd: md[pd[0]] = bm
        if st["guard"]:
            ds, dd = O.defaults(w); m0, d0 = {i: "inside" for i in ds}, {j: "inside" for j in dd}
            if any(a > b for a, b in zip(F4.proj(w, ps, pd, ms, md)[1], F4.proj(w, ds, dd, m0, d0)[1])): ps, pd, ms, md = ds, dd, m0, d0
        w.ms, w.md = ms, md; w.tick(ps, pd)
    return {"G": float(w.G()), "ch": [float(x) for x in w.channels()]}

def objects(v):
    adm = P6.admissible(T, v) | {P6.NATIVE}
    return sorted(adm, key=lambda c: (-np.mean(T[v][c]["G"]), c))[:4]

def shade(args):
    v, gs, es = args; k = v - 1; p = G.params(G.SH["shades"][k]["node"], v); K = objects(v)
    score = lambda asg: float(np.mean([run_house(G.Shade, s, p, {r: obj(asg[r]) for r in ROOMS})["G"] for s in gs]))
    single = {c: score({r: c for r in ROOMS}) for c in K}
    fixed = max(K, key=lambda c: (single[c], c))
    asg = {r: K[0] for r in ROOMS}; cur = single[K[0]]
    for r in ROOMS:                                   # one pass of coordinate ascent, rooms in a fixed order
        for c in K:
            if c == asg[r]: continue
            t = dict(asg, **{r: c}); sc = score(t)
            if sc > cur + 1e-9: asg, cur = t, sc
    flat = "".join(f"{r[0]}{max(unkey(c)[r] for c in K)}" for r in X.Z.ROLES)
    shuf = dict(zip(ROOMS, [asg["drift"], asg["calm"], asg["dry"]]))
    arms = {"house": asg, "fixed": {r: fixed for r in ROOMS}, "flat": {r: flat for r in ROOMS}, "shuffled": shuf}
    rows = []
    for sd in es:
        res = {a: run_house(G.Shade, sd, p, {r: obj(x[r]) for r in ROOMS}) for a, x in arms.items()}
        nat = {f"{a}+{b}": F4.run(G.Shade, sd, p, (a, b))["G"] for a, b in O.NATS}
        rows.append({"shade": v, "seed": sd, **{a: r["G"] for a, r in res.items()}, **{a + "_ch": r["ch"] for a, r in res.items()},
                     "best_native": max(nat.values())})
    print("shade", v, "objects", K, "house", asg, "fixed", fixed, flush=True)
    return {"shade": v, "objects": K, "arms": arms, "rows": rows}

if __name__ == "__main__":
    g0, g1 = map(int, sys.argv[1].split("-")); e0, e1 = map(int, sys.argv[2].split("-")); out = sys.argv[3]
    vs = [int(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 else list(range(1, P6.NV + 1))
    with Pool(int(os.environ.get("WORKERS", os.cpu_count()))) as pool:
        res = pool.map(shade, [(v, list(range(g0, g1 + 1)), list(range(e0, e1 + 1))) for v in vs])
    json.dump(res, open(out, "w"), indent=1)
    from scipy.stats import binomtest
    R = [r for x in res for r in x["rows"]]
    for b in ["fixed", "flat", "shuffled", "best_native"]:
        w = sum(r["house"] > r[b] + 1e-12 for r in R); l = sum(r["house"] < r[b] - 1e-12 for r in R)
        print(f"house > {b}: wins {w} losses {l} ties {len(R) - w - l}", "p", round(binomtest(w, w + l, .5, alternative="greater").pvalue, 4) if w + l else "-",
              "mean", round(float(np.mean([r["house"] - r[b] for r in R])), 4))
    chw = sum(all(a <= b for a, b in zip(r["house_ch"], r["fixed_ch"])) for r in R)
    print(f"channels house <= fixed on both: {chw}/{len(R)}")
    used = sum(len(set(x["arms"]["house"].values())) > 1 for x in res); print(f"shades where the house uses >1 object: {used}/{len(res)}")
