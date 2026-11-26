"""SEAL2 runner: the one structure (STRUCTURE1-6, owner 24 Nov 09:27-12:04) on fresh seeds, 60-tick worlds. Layer 2.
Confirmatory. Prereg PREREG_SEAL2.md; hashes SEAL_SEAL2.txt (checked before any unit runs). Rows: All laws as
mathematics (laws part), Meaning, D, E. Usage: python seal2.py <window 0..3> ; python seal2.py analyze
Smoke (pipeline only, never results): SEAL2_SMOKE_T=6 SEAL2_OUT=smoke python seal2.py 0"""
import os, sys, json, time, hashlib, shutil, gzip, glob, copy
ROOT = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(ROOT)
T = int(os.environ.get("SEAL2_SMOKE_T", "60")); OUTN = os.environ.get("SEAL2_OUT", "out")
def check_seal():
    for line in open(os.path.join(ROOT, "SEAL_SEAL2.txt")):
        h, f = line.split()
        if hashlib.sha256(open(os.path.join(REPO, f), "rb").read()).hexdigest() != h: sys.exit(f"HASH MISMATCH {f}: stop, do not run")
if OUTN == "out": check_seal()
OUT = os.path.join(ROOT, OUTN); os.makedirs(os.path.join(OUT, "diag"), exist_ok=True)
shutil.copy(os.path.join(REPO, "experiments/laws/diag/exact.json"), os.path.join(OUT, "diag/exact.json"))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(REPO, "experiments/structure"))
import numpy as np
import structure2 as S2, structure3 as S3, structure5 as S5
S1, L, L4, L6, M, Q, O, G = S2.S1, S2.L, S2.L4, S2.L6, S2.M, S2.Q, S2.O, S2.G
S1._chdir(OUT); O.T = T
SHADES = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21]; LAW_SEEDS = [7100, 7101]; ORG_SEEDS = [7120, 7121]
MIN = {"laws": 80, "le": 9, "organs": 23}   # estimated minutes per unit (dev timings x4 for 60 ticks)
UNITS = [("laws", v, None) for v in SHADES] + [("le", v, None) for v in SHADES] + [("organs", v, sd) for v in SHADES for sd in ORG_SEEDS]
def windows():
    W = [[] for _ in range(4)]; load = [0] * 4
    for u in sorted(UNITS, key=lambda u: -MIN[u[0]]):
        k = load.index(min(load)); W[k].append(u); load[k] += MIN[u[0]]
    return W, load
def unit_laws(v):
    L6.SHADES = [v]; L6.SEEDS = LAW_SEEDS; L6.collect(0); L6.local(0); os.replace("diag/l6local_p0.json.gz", f"diag/l6local_p{v}.json.gz")
def unit_le(v):
    sd = LAW_SEEDS[0]; p = G.params(G.SH["shades"][v - 1]["node"], v); st = L4.st_of(v)
    S1.LAND.clear(); S1.run_struct(L4.replay_class(2), sd, p, st); tr = L.take()
    rep2 = {k: [t[k] for t in tr] for k in ("dry", "dr", "nbd")} | {"land": [[[int(x) for x in s] for s in l] for l in S1.LAND]}
    leaves = []
    for r in S5.GROW:
        w = L4.replay_class(r)(sd, p, "inside"); land = []
        while w.t < O.T:
            rr = copy.deepcopy(w.rng); a = L4.step(w, p, st); w.rng = rr
            land.append([[int(x) for x in a[0]], [int(x) for x in a[1]]]); w.ms, w.md = dict(a[2]), dict(a[3]); w.tick(list(a[0]), list(a[1]))
        tr = L.take(); leaves.append({k: [t[k] for t in tr] for k in ("dry", "dr", "nbd")} | {"land": land})
    json.dump(leaves + [rep2], open(f"diag/le_leaves_v{v}.json", "w"))
def unit_organs(v, sd):
    p = G.params(G.SH["shades"][v - 1]["node"], v); st = L4.st_of(v); sB = L4.st_of(v + 1) if v < 21 else L4.st_of(v - 1); pc = M.params_both(v) if v < 21 else M.params_both(v - 1)
    r = {"v": v, "sd": sd}
    r["S_org"], r["S_org_br"] = S2.organ_struct2(M.Organs, sd, p, st)
    r["best_single"] = max(M.run_house(M.Organs, sd, p, st, "single", o)["G"] for o in M.NAMES)
    r["child"], r["child_src"] = S3.child3(sd, pc, st, sB); r["parents"] = [M.run_parent(M.Organs, sd, pc, s)["G"] for s in (st, sB)]
    r["S_living"], _ = S2.organ_struct2(M.Living, sd, p, st, rooms=False); r["v3_living"] = M.run_parent(M.Living, sd, p, st)["G"]
    r["best_native"] = max([M.F4.run(M.Living, sd, p, n)["G"] for n in O.NATS] + [M.F4.run(M.Living, sd, p, "B")["G"]])
    json.dump(r, open(f"diag/organs_v{v}_s{sd}.json", "w"), default=float)
def run_window(k):
    W, load = windows(); print(f"window {k} units {len(W[k])} estimated minutes {load[k]}", flush=True)
    for kind, v, sd in W[k]:
        t0 = time.time(); {"laws": lambda: unit_laws(v), "le": lambda: unit_le(v), "organs": lambda: unit_organs(v, sd)}[kind]()
        print(f"unit {kind} {v} {sd or ''} done {round((time.time() - t0) / 60, 1)} min {time.strftime('%H:%M')}", flush=True)
    print(f"WINDOW {k} FINISHED", flush=True)
if __name__ == "__main__":
    if sys.argv[1] == "analyze":
        import analyze_seal2; analyze_seal2.main(OUT, SHADES, LAW_SEEDS, ORG_SEEDS)
    else: run_window(int(sys.argv[1]))
