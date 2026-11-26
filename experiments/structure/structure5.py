"""STRUCTURE5 (owner OK 24 Nov 11:58). Layer 2, development quick test, no colour. Sealed and pushed before the run.
LE reads each unit's tendency from the SEED, not from one leaf (owner 11:55: the structure is the same at all times and
places; a replay is one leaf of the tree). The seed (same world structure, shade, organism) is grown 20 times with fresh
randomness (replay classes 3..22: never replay 2's), driven by the organism's own policy (L4.step; disclosed: the
structure chose its own present action in 629/660 ticks in STRUCTURE1, the full per-tick fork is not run here). Each unit's
tendency q_i[landed, neighbour drifted] for windows 2/4/8 is pooled over the 20 growths; replay 2 (diag/S4_v*_rep2.json,
STRUCTURE4, sealed code) is predicted window by window: unit down at t0 -> 1, else q_i[landed at t0, neighbour drifted
at t0]. Comparison, windows, tolerance unchanged. Usage: python structure5.py grow <v> ; python structure5.py final"""
import os, sys, json, copy
os.environ["S1_T"] = "30"
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import structure2 as S2
L, L4, G, O = S2.L, S2.L4, S2.G, S2.O
GROW = range(3, 23)

def grow(v):
    O.T = 60; p = G.params(G.SH["shades"][v - 1]["node"], v); st = L4.st_of(v); out = []
    for r in GROW:
        w = L4.replay_class(r)(6670, p, "inside"); land = []
        while w.t < O.T:
            rr = copy.deepcopy(w.rng); a = L4.step(w, p, st); w.rng = rr
            land.append([[int(x) for x in a[0]], [int(x) for x in a[1]]]); w.ms, w.md = dict(a[2]), dict(a[3]); w.tick(list(a[0]), list(a[1]))
        tr = L.take(); out.append({k: [t[k] for t in tr] for k in ("dry", "dr", "nbd")} | {"land": land})
    json.dump(out, open(f"diag/S5_grow_v{v}.json", "w"))

def final():
    rows = []
    for v in (4, 10):
        Gr = json.load(open(f"diag/S5_grow_v{v}.json")); R2 = json.load(open(f"diag/S4_v{v}_rep2.json"))
        for ch, side in (("dry", 0), ("dr", 1)):
            F1 = np.array(R2[ch], bool)
            if F1.mean() < 0.01 or np.mean([np.mean(g[ch]) for g in Gr]) < 0.01: continue
            N1 = np.array(R2["nbd"]) > 0; A1 = np.zeros_like(F1)
            for t, l in enumerate(R2["land"]): A1[t, l[side]] = True
            d = {}
            for T in (2, 4, 8):
                cnt = {}; tot = {}
                for g in Gr:
                    F0 = np.array(g[ch], bool); N0 = np.array(g["nbd"]) > 0; A0 = np.zeros_like(F0)
                    for t, l in enumerate(g["land"]): A0[t, l[side]] = True
                    for i in range(F0.shape[1]):
                        for t in range(F0.shape[0] - T + 1):
                            if F0[t, i]: continue
                            y = int(F0[t + 1:t + T, i].any())
                            for key in ((i, int(A0[t, i]), int(N0[t, i])), (i, None, None)):
                                cnt[key] = cnt.get(key, 0) + y; tot[key] = tot.get(key, 0) + 1
                q = lambda i, l_, n_: (cnt[(i, l_, n_)] / tot[(i, l_, n_)]) if tot.get((i, l_, n_)) else (cnt[(i, None, None)] / tot[(i, None, None)] if tot.get((i, None, None)) else 0.0)
                preds = [1.0 if F1[k * T, i] else q(i, int(A1[k * T, i]), int(N1[k * T, i])) for i in range(F1.shape[1]) for k in range(F1.shape[0] // T)]
                pr = float(np.mean(preds)); m = L.span(F1, T); n = F1.shape[1] * (F1.shape[0] // T)
                tol = 2 * np.sqrt(max(pr * (1 - pr), 1e-12) / n) + 0.01; d[T] = {"pred": pr, "meas": m, "tol": float(tol), "ok": bool(abs(m - pr) <= tol)}
            rows.append({"v": v, "ch": ch, "detail": d, "ok": all(x["ok"] for x in d.values()), "growth_share": float(np.mean([np.mean(g[ch]) for g in Gr])), "rep2_share": float(F1.mean())})
    R3 = json.load(open("diag/RESULT_STRUCTURE3.json")); C = dict(R3["checks"]); C["LE_relations"] = all(r["ok"] for r in rows) and len(rows) > 0
    S = {"checks": C, "TABLE_FILLED": all(C.values()), "LE_seed": rows}
    json.dump(S, open("diag/RESULT_STRUCTURE5.json", "w"), default=float, indent=1)
    for r in rows: print(r["v"], r["ch"], r["ok"], "seed share %.3f rep2 %.3f" % (r["growth_share"], r["rep2_share"]), {T: (round(x["pred"], 3), round(x["meas"], 3), round(x["tol"], 3)) for T, x in r["detail"].items()})
    print("checks passed", sum(C.values()), "/", len(C), "TABLE_FILLED", S["TABLE_FILLED"])

if __name__ == "__main__":
    grow(int(sys.argv[2])) if sys.argv[1] == "grow" else final()
