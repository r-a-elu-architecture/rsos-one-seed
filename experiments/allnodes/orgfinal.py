"""ORG-FINAL (exact ORG5 code, untouched seeds only; see PREREG_FINAL.md). ORG5: STRUCTURE crosses the bridge (owner 22 Nov 2026 04:13; advice accepted, "seal" 04:17). Layer 2 twins + real data.
The violet family = a shared structure; a shade = a binding of it to its own operators (the host decides).
Structure = which roles of the tree (map/STRUCTURE_TREE_22NOV.md) are active; each role binds to an RSOS operator:
  Twins (4 roles, 16 structures):
    det     Detection      -> the dragon's where (organism picks)       | off: the default picks
    adapt   Adaptive resp. -> beam over the node's placements           | off: all landings inside (innate)
    guard   Regulation     -> clean guard (own forks: beamed vs default action from the same state)
    barrier Barrier        -> first picked unit on each side lands 'above' (else 'pierced'; else none: host binding)
    (all off = the native report+popular exactly)
  Real data (5 roles, 32 structures), SGD learner on the hard data (sec1_real_v4.hard, hash-checked via real_v5):
    barrier  noise barrier: examples misclassified persistently (memory > 3) leave the batch and the targeting
    detect   detection: 2 extra examples from the class weakest on validation
    adapt    adaptive: the 4 loudest by lack replace 4 of the batch
    memory   memory: lack weighted by (1 + memory of failures)
    reg      regulation: decaying rate 1/(1+t/100)
Seeds (FINAL, untouched): twin selection 10400-10401; twin evaluation 10410-10421 (12); new worlds 10900; births
  10700-10701; random structures 10800+; real selection 10500-10501; real evaluation 10600-10607.
Arms per shade x eval seed: own (best on its selection table), nb (best mean of the neighbours v-1, v+1 tables: the
  bridge), glob (best mean over all other shades, leave-one-out: no bridge), rnd_nb / rnd_own (random structure of the
  same size as nb / own), natives, beam-only.
Usage: python org5.py select|eval|births <part 0|1> ; python org5.py real"""
import sys, os, json, copy, hashlib, itertools, glob as gl
import numpy as np
os.chdir(os.path.dirname(os.path.abspath(__file__)))
S1, S4 = open("SEAL_ORG1.txt").read(), open("SEAL_ORG4.txt").read()
for f in ("organism.py", "SHADES_v2.json", "real_v5.py"): assert hashlib.sha256(open(f, "rb").read()).hexdigest() in S1, f
assert hashlib.sha256(open("org4.py", "rb").read()).hexdigest() in S4, "org4.py"
import organism as G, org4 as F4
O, V3 = G.O, G.V3
NV = G.NV; SEL, EV, RW, RB = [10400, 10401], list(range(10410, 10422)), 10900, [10700, 10701]
ROLES = ["det", "adapt", "guard", "barrier"]
STRUCTS = [dict(zip(ROLES, b)) for b in itertools.product([0, 1], repeat=4)]
key = lambda st: "".join(f"{r[0]}{st[r]}" for r in ROLES)

def run_st(W, seed, p, st):
    w = W(seed, p, "inside"); bm = "above" if "above" in p["modes"] else ("pierced" if "pierced" in p["modes"] else None)
    while w.t < O.T:
        ps, pd = V3.org3_picks(w) if st["det"] else O.defaults(w)
        ms, md = {i: "inside" for i in ps}, {j: "inside" for j in pd}
        if st["adapt"]: ms, md, _ = G.beam(w, ps, pd, p["modes"])
        if st["barrier"] and bm:
            if ps: ms[ps[0]] = bm
            if pd: md[pd[0]] = bm
        if st["guard"]:
            ds, dd = O.defaults(w); m0, d0 = {i: "inside" for i in ds}, {j: "inside" for j in dd}
            if any(a > b for a, b in zip(F4.proj(w, ps, pd, ms, md)[1], F4.proj(w, ds, dd, m0, d0)[1])): ps, pd, ms, md = ds, dd, m0, d0
        w.ms, w.md = ms, md; w.tick(ps, pd)
    return {"G": float(w.G()), "ch": [float(x) for x in w.channels()], "flows": int(w.flows)}

def select(ks, tag):
    out = {}
    for k in ks:
        p = G.params(G.SH["shades"][k]["node"], k + 1)
        out[k + 1] = {key(st): float(np.mean([run_st(G.Shade, s, p, st)["G"] for s in SEL])) for st in STRUCTS}
        print(tag, "select", k + 1, flush=True)
    json.dump(out, open(f"RAWF_select_{tag}.json", "w"))

def tables():
    T = {}
    for f in sorted(gl.glob("RAWF_select_w*.json")): T.update({int(a): b for a, b in json.load(open(f)).items()})
    return T

def best(T, vs):
    ks = list(T[vs[0]].keys()); return max(ks, key=lambda c: (np.mean([T[v][c] for v in vs]), c))
unkey = lambda c: {r: int(c[2 * i + 1]) for i, r in enumerate(ROLES)}
size = lambda c: sum(unkey(c).values())

def picks_for(T, v):
    nbs = [u for u in (v - 1, v + 1) if u in T]
    return {"own": best(T, [v]), "nb": best(T, nbs), "glob": best(T, [u for u in T if u != v])}

def evaluate(ks, tag):
    T = tables(); out = []
    for k in ks:
        v = k + 1; p = G.params(G.SH["shades"][k]["node"], v); P = picks_for(T, v); allk = list(T[v].keys())
        for i, sd in enumerate(EV):
            rng = np.random.default_rng(10800 + 100 * v + i)
            rn = rng.choice([c for c in allk if size(c) == size(P["nb"])]); ro = rng.choice([c for c in allk if size(c) == size(P["own"])])
            arms = {"own": P["own"], "nb": P["nb"], "glob": P["glob"], "rnd_nb": str(rn), "rnd_own": str(ro)}
            res, cache = {}, {}
            for a, c in arms.items():
                if c not in cache: cache[c] = run_st(G.Shade, sd, p, unkey(c))
                res[a] = cache[c]
            nat = {f"{a}+{b}": F4.run(G.Shade, sd, p, (a, b)) for a, b in O.NATS}
            allarm = F4.run(G.Shade, sd, p, "all")
            out.append({"shade": v, "node": G.SH["shades"][k]["node"], "seed": sd, "structs": arms, **res, "nat": nat,
                        "B": F4.run(G.Shade, sd, p, "B"), "all": allarm})
        wo = {}
        for wn in ("WB", "WC"):
            wo[wn] = {"nb": run_st(F4.WORLDS[wn], RW, p, unkey(P["nb"]))["G"],
                      "nat": {f"{a}+{b}": F4.run(F4.WORLDS[wn], RW, p, (a, b))["G"] for a, b in O.NATS}}
        out.append({"shade": v, "worlds": wo})
        print(tag, "eval", v, P, flush=True)
    json.dump(out, open(f"RAWF_eval_{tag}.json", "w"))

def births(ks, tag):
    T = tables(); out = []
    for k in ks:
        a, b = k + 1, k + 2; pa, pb = G.params(G.SH["shades"][k]["node"], a), G.params(G.SH["shades"][k + 1]["node"], b)
        pc = {"d": round((pa["d"] + pb["d"]) / 2), "hz": (pa["hz"] + pb["hz"]) / 2, "cz": (pa["cz"] + pb["cz"]) / 2,
              "modes": sorted(set(pa["modes"]) | set(pb["modes"]))}
        child, ca, cb = best(T, [a, b]), best(T, [a]), best(T, [b])
        for sd in RB:
            out.append({"bridge": f"v{a}|v{b}", "seed": sd, "child_struct": child, "child": run_st(G.Shade, sd, pc, unkey(child))["G"],
                        "parentA": run_st(G.Shade, sd, pc, unkey(ca))["G"], "parentB": run_st(G.Shade, sd, pc, unkey(cb))["G"],
                        "differs": child not in (ca, cb) or ca != cb})
        print(tag, "birth", a, flush=True)
    json.dump(out, open(f"RAWF_births_{tag}.json", "w"))

RROLES = ["barrier", "detect", "adapt", "memory", "reg"]
RSTRUCTS = ["".join(map(str, b)) for b in itertools.product([0, 1], repeat=5)]

def real_st(name, seed, c):
    import real_v5 as Z; R, V4 = Z.R, Z.V4; st = dict(zip(RROLES, map(int, c)))
    Xtr, ytr, Xva, yva, Xte, yte, classes = V4.hard(name, seed)
    rng = np.random.default_rng(seed); clf = V4.new(classes, seed, Xtr, ytr); r2 = np.random.default_rng(seed + 7)
    batches = [rng.choice(len(Xtr), R.B, replace=False) for _ in range(R.STEPS + 10)]; mem = np.zeros(len(Xtr))
    for t in range(R.STEPS):
        clf.eta0 = R.LR / (1 + t / 100) if st["reg"] else R.LR
        bt = batches[t]; sus = mem > 3 if st["barrier"] else np.zeros(len(Xtr), bool)
        if st["barrier"] and (~sus[bt]).sum() >= R.K: bt = bt[~sus[bt]]
        if st["adapt"]:
            lack = R.loss(clf, Xtr, ytr, classes) * ((1 + mem) if st["memory"] else 1); lack[sus] = -1
            bt = np.concatenate([bt[:max(1, len(bt) - R.K)], np.argsort(-lack)[:R.K]])
        if st["detect"]:
            pool = np.where(ytr == classes[np.argmin(R.per_class(clf, Xva, yva, classes))])[0]
            if st["barrier"] and (~sus[pool]).sum() >= 2: pool = pool[~sus[pool]]
            bt = np.concatenate([bt, r2.choice(pool, 2, replace=len(pool) < 2)])
        clf.partial_fit(Xtr[bt], ytr[bt]); mem = 0.9 * mem + (clf.predict(Xtr) != ytr)
    return float(np.mean(clf.predict(Xte) == yte))

def real():
    import real_v5 as Z; V4 = Z.V4; D = list(Z.R.DATA); T = {}
    for n in D: T[n] = {c: float(np.mean([real_st(n, s, c) for s in (10500, 10501)])) for c in RSTRUCTS}; print("real select", n, flush=True)
    rb = lambda ns: max(RSTRUCTS, key=lambda c: (np.mean([T[n][c] for n in ns]), c)); rows = []
    for n in D:
        own, tr = rb([n]), rb([m for m in D if m != n])
        for i, s in enumerate(range(10600, 10608)):
            rng = np.random.default_rng(10850 + 10 * D.index(n) + i)
            rt = str(rng.choice([c for c in RSTRUCTS if sum(map(int, c)) == sum(map(int, tr))]))
            ro = str(rng.choice([c for c in RSTRUCTS if sum(map(int, c)) == sum(map(int, own))]))
            r = {"data": n, "seed": s, "own_struct": own, "tr_struct": tr, "own": real_st(n, s, own), "tr": real_st(n, s, tr),
                 "rnd_tr": real_st(n, s, rt), "rnd_own": real_st(n, s, ro), **{q: V4.run(n, s, q)[0] for q in ("plain", "decay", "ohem")}}
            r["best_native"] = max(r["plain"], r["decay"], r["ohem"]); rows.append(r); print(n, s, own, tr, round(r["tr"] - r["best_native"], 4), flush=True)
    json.dump({"tables": T, "rows": rows}, open("RAWF_real.json", "w"))

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "real": real()
    else:
        part = int(sys.argv[2]); tag = f"w{part}"
        if cmd == "births": births([k for k in range(NV - 1) if k % 2 == part], tag)
        else: {"select": select, "eval": evaluate}[cmd]([k for k in range(NV) if k % 2 == part], tag)
