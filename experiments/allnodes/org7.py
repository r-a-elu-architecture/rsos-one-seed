"""ORGANISM v2 roles (map/STRUCTURAL_MAP_22NOV.md Part I), built on org5.run_st unchanged (hash-checked).
New switchable roles, each written once (same rule for every shade; the structure search binds them per shade):
  cs    P1 counter-shift   : the unit that sets a channel (longest dry supply unit, longest drifted unit) pulls one
                             landing to itself when its run reaches 2 ticks (homeostasis on both channels)
  vote  P8 vote of futures : a beam mode is adopted only if it wins in at least 2 of 3 futures with different
                             randomness (not one lucky future)
  mem   P5/P6 value back   : the mode that won at a place is remembered and becomes that place's starting mode
                             (what worked is reinforced and carried forward)
  joint P4 joint choice    : after the beam, the four landings are also tried jointly in one shared mode; the joint
                             choice is kept if it beats the separate choices for the whole without a worse channel
Development only until sealed. Usage: imported by quick7.py"""
import os, copy, hashlib
import numpy as np
os.chdir(os.path.dirname(os.path.abspath(__file__)))
assert hashlib.sha256(open("org5.py", "rb").read()).hexdigest() in open("SEAL_ORG5.txt").read()
import org5 as Z
G, O, V3, F4 = Z.G, Z.O, Z.V3, Z.F4
NEW = ["cs", "vote", "mem", "joint"]

def futures(w, ms, md, ps, pd, n):
    out = []
    for k in range(n):
        f = copy.deepcopy(w)
        if k: f.rng = np.random.default_rng(10_000 * k + w.t)
        f.ms, f.md = dict(ms), dict(md); f.tick(ps, pd); O.to_end(f); out.append((f.G(), f.channels()))
    return out

def better(new, old):  # new beats old for the whole without a worse channel (per future, majority)
    wins = sum(g1 > g0 + 1e-12 and all(a <= b for a, b in zip(c1, c0)) for (g1, c1), (g0, c0) in zip(new, old))
    return wins * 2 > len(new)

def beam2(w, ps, pd, modes, st, memo):
    n = 3 if st["vote"] else 1
    ms = {i: (memo.get(("s", i), "inside") if st["mem"] else "inside") for i in ps}
    md = {j: (memo.get(("d", j), "inside") if st["mem"] else "inside") for j in pd}
    base = futures(w, ms, md, ps, pd, n)
    for host, u in [("s", i) for i in ps] + [("d", j) for j in pd]:
        D = ms if host == "s" else md; cur = D[u]
        for m in modes:
            if m == cur: continue
            D[u] = m; fut = futures(w, ms, md, ps, pd, n)
            if better(fut, base): base, cur = fut, m
            D[u] = cur
        if st["mem"]: memo[(host, u)] = cur
    if st["joint"]:
        for m in modes:
            jm, jd = {i: m for i in ps}, {j: m for j in pd}; fut = futures(w, jm, jd, ps, pd, n)
            if better(fut, base): base, ms, md = fut, jm, jd
    return ms, md

def run_st2(W, seed, p, st):
    w = W(seed, p, "inside"); bm = "above" if "above" in p["modes"] else ("pierced" if "pierced" in p["modes"] else None); memo = {}
    while w.t < O.T:
        ps, pd = V3.org3_picks(w) if st["det"] else O.defaults(w); ps, pd = list(ps), list(pd)
        if st["cs"]:
            i = int(np.argmax(w.dry)); j = int(np.argmax(w.dur))
            th = st.get("cs_th", 2)
            if w.dry[i] >= th and i not in ps: ps = [i] + ps[:-1]
            if w.dur[j] >= th and j not in pd: pd = [j] + pd[:-1]
        ms, md = {i: "inside" for i in ps}, {j: "inside" for j in pd}
        if st["adapt"]: ms, md = beam2(w, ps, pd, p["modes"], st, memo)
        if st["barrier"] and bm:
            if ps: ms[ps[0]] = bm
            if pd: md[pd[0]] = bm
        if st["guard"]:
            ds, dd = O.defaults(w); m0, d0 = {i: "inside" for i in ds}, {j: "inside" for j in dd}
            if any(a > b for a, b in zip(F4.proj(w, ps, pd, ms, md)[1], F4.proj(w, ds, dd, m0, d0)[1])): ps, pd, ms, md = ds, dd, m0, d0
        w.ms, w.md = ms, md; w.tick(ps, pd)
    return {"G": float(w.G()), "ch": [float(x) for x in w.channels()], "flows": int(w.flows)}
