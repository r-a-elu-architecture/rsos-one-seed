"""SEAL2 analysis: fixed in PREREG_SEAL2.md before the run."""
import os, json, glob, io, contextlib, numpy as np
def le_tree(leaves, L):
    rows = []
    for ch, side in (("dry", 0), ("dr", 1)):
        if np.mean([np.mean(g[ch]) for g in leaves]) < 0.01: continue
        A3 = []
        for g in leaves:
            F = np.array(g[ch], bool); N = np.array(g["nbd"]) > 0; A = np.zeros_like(F)
            for t, l in enumerate(g["land"]): A[t, l[side]] = True
            A3.append((F, N, A))
        d = {}
        for T in (2, 4, 8):
            C = []
            for F, N, A in A3:
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
            d[T] = {"mean_diff": md, "tol": float(tol), "ok": bool(abs(md) <= tol)}
        rows.append({"ch": ch, "detail": d, "ok": all(x["ok"] for x in d.values())})
    return rows
def main(OUT, SHADES, LAW_SEEDS, ORG_SEEDS):
    import seal2 as S; L6, L = S.L6, S.L
    L6.SHADES = SHADES; L6.SEEDS = LAW_SEEDS
    with contextlib.redirect_stdout(io.StringIO()): L6.analyze()
    lw = json.load(open("diag/QUICK_LAWS6.json"))["summary"]
    LE = []
    for v in SHADES:
        for r in le_tree(json.load(open(f"diag/le_leaves_v{v}.json")), L): LE.append(dict(r, v=v))
    org = [json.load(open(f)) for f in sorted(glob.glob("diag/organs_v*_s*.json"))]; n = len(org)
    dm = [x["S_org"] - x["best_single"] for x in org]; db = [x["child"] - max(x["parents"]) for x in org]
    C = {"laws_" + q: bool(lw["PASS"][q]) for q in ("EXACT", "L0", "L1p", "L1", "L2", "C2", "C1", "L4", "L5", "L3", "PR", "RC")}
    C["laws_LE_tree"] = len(LE) > 0 and sum(r["ok"] for r in LE) / len(LE) >= 0.90
    C["Meaning_M1"] = sum(x > 0 for x in dm) >= 2 * n / 3 and float(np.mean(dm)) > 0
    C["D_B1"] = sum(x > 0 for x in db) >= 2 * n / 3 and float(np.mean(db)) > 0
    C["E_E1"] = all(x["S_living"] > x["best_native"] for x in org)
    rows = {"All laws as mathematics": all(v for k, v in C.items() if k.startswith("laws_")), "Meaning": C["Meaning_M1"], "D": C["D_B1"], "E": C["E_E1"]}
    R = {"checks": C, "ROWS_TURQUOISE": rows, "laws_summary": lw, "LE_tree": LE, "Meaning": {"wins": sum(x > 0 for x in dm), "n": n, "mean": float(np.mean(dm))},
         "D": {"wins": sum(x > 0 for x in db), "n": n, "mean": float(np.mean(db))}, "E": {"E1": sum(x["S_living"] > x["best_native"] for x in org), "n": n,
         "E2_vs_v3_mean": float(np.mean([x["S_living"] - x["v3_living"] for x in org]))}}
    json.dump(R, open(os.path.join(OUT, "RESULTS_SEAL2.json"), "w"), default=float, indent=1)
    with open(os.path.join(OUT, "RESULTS_SEAL2.md"), "w") as f:
        f.write("# RESULTS SEAL2\n\n| Row | Colour |\n|---|---|\n" + "".join(f"| {k} | {'turquoise' if v else 'started (not passed)'} |\n" for k, v in rows.items()))
        f.write("\n| Check | Pass |\n|---|---|\n" + "".join(f"| {k} | {v} |\n" for k, v in C.items()))
    print(json.dumps(rows, indent=1)); print(json.dumps(C, indent=1))
