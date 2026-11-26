"""STRUCTURE6 (owner 12:02: fill now, under 5 min). Layer 2, development quick test, no colour. Sealed before the run.
LE checked ON THE TREE, not on one leaf (owner 11:55; finding STRUCTURE5: replay 2 lies at the 1/20 tail of the seed).
Leaves = the 20 seed growths (S5_grow_v*.json) + replay 2 (S4_v*_rep2.json) = 21 leaves per shade. For each leaf:
prediction from the other 20 leaves pooled (leave-one-out; q_i[landed, neighbour drifted] per window, as STRUCTURE5),
measured on that leaf; diff = measured - predicted. Row passes when |mean diff| <= 2 SD(diff)/sqrt(21) + 0.01 at windows
2, 4, 8 (tolerance from how the leaves differ). Disclosed: LE's check changes after it missed; development only; the same
form goes into SEAL2 on fresh seeds. Usage: python structure6.py"""
import json, numpy as np, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "laws")); import laws as L
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # laws import changes directory (fix before the run, re-sealed)
def arrs(g, ch, side):
    F = np.array(g[ch], bool); N = np.array(g["nbd"]) > 0; A = np.zeros_like(F)
    for t, l in enumerate(g["land"]): A[t, l[side]] = True
    return F, N, A
rows = []
for v in (4, 10):
    leaves = json.load(open(f"diag/S5_grow_v{v}.json")) + [json.load(open(f"diag/S4_v{v}_rep2.json"))]
    for ch, side in (("dry", 0), ("dr", 1)):
        if np.mean([np.mean(g[ch]) for g in leaves]) < 0.01: continue
        A3 = [arrs(g, ch, side) for g in leaves]; d = {}
        for T in (2, 4, 8):
            C = []
            for F, N, A in A3:   # per-leaf counts per key
                c = {}
                for i in range(F.shape[1]):
                    for t in range(F.shape[0] - T + 1):
                        if F[t, i]: continue
                        y = int(F[t + 1:t + T, i].any())
                        for key in ((i, int(A[t, i]), int(N[t, i])), (i, None, None)):
                            a, b = c.get(key, (0, 0)); c[key] = (a + y, b + 1)
                C.append(c)
            diffs = []
            for j, (F, N, A) in enumerate(A3):
                cnt = {}
                for k, c in enumerate(C):
                    if k == j: continue
                    for key, (a, b) in c.items(): x, y_ = cnt.get(key, (0, 0)); cnt[key] = (x + a, y_ + b)
                def q(i, l_, n_):
                    for key in ((i, l_, n_), (i, None, None)):
                        if cnt.get(key, (0, 0))[1]: return cnt[key][0] / cnt[key][1]
                    return 0.0
                pr = float(np.mean([1.0 if F[k * T, i] else q(i, int(A[k * T, i]), int(N[k * T, i])) for i in range(F.shape[1]) for k in range(F.shape[0] // T)]))
                diffs.append(L.span(F, T) - pr)
            md, sd = float(np.mean(diffs)), float(np.std(diffs, ddof=1)); tol = 2 * sd / np.sqrt(len(diffs)) + 0.01
            d[T] = {"mean_diff": md, "sd": sd, "tol": float(tol), "ok": bool(abs(md) <= tol), "rep2_diff": float(diffs[-1])}
        rows.append({"v": v, "ch": ch, "detail": d, "ok": all(x["ok"] for x in d.values())})
R3 = json.load(open("diag/RESULT_STRUCTURE3.json")); Ck = dict(R3["checks"]); Ck["LE_relations"] = all(r["ok"] for r in rows) and len(rows) > 0
json.dump({"checks": Ck, "TABLE_FILLED": all(Ck.values()), "LE_tree": rows}, open("diag/RESULT_STRUCTURE6.json", "w"), indent=1)
for r in rows: print(r["v"], r["ch"], r["ok"], {T: (round(x["mean_diff"], 4), round(x["tol"], 4), round(x["rep2_diff"], 3)) for T, x in r["detail"].items()})
print("checks passed", sum(Ck.values()), "/", len(Ck), "TABLE_FILLED", all(Ck.values()))
