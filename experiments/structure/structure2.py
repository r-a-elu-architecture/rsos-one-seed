"""STRUCTURE2 (owner 24 Nov 10:50-10:53): STRUCTURE1 (one structure: branches of space, lineage, time; Law 4 choice in
the organism's own future, K.2 unchanged) + RELATIONS = the same structure recombined across units. Layer 2. Development
quick test, no colour. Prereg: PREREG_STRUCTURE2.md. Sealed (SEAL_STRUCTURE2.txt) and pushed before the run.
  #1 relations in space (LE): q_i from replay 1 split by (organism landed on i at t) x (i had a drifted neighbour at t,
     trace 'nbd' > 0); replay 2, each window of T from t0: unit down at t0 -> 1, else q_i[landed at t0 by the organism's
     own action, neighbour drifted at t0]; pred = mean over units and windows; measured, windows 2/4/8 and tolerance as LE.
  #2 relations between organs: lungs + heart + kidney = one coupled branch (lungs drift landing, heart supply landing,
     kidney drift landing in one action); added to the structure's branches (Meaning, E) and, for D, the coupled book
     (lungs, heart, kidney from one parent, liver from the other, both ways).
  #3 relations between organisms (L5): pair rows from all 7 shades (1, 4, ..., 19, LAWS6's set), fit on the other 6.
Seed 30 ticks; shades 4, 10; laws seed 6670, organs seed 6720 (dev). Usage: python structure2.py part <0|1> ; python structure2.py final"""
import os, sys, copy, json, time
os.environ["S1_T"] = "30"
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import structure1 as S1
L, L4, L6, M, Q, O, G = S1.L, S1.L4, S1.L6, S1.M, S1.Q, S1.O, S1.G
ALL7 = [1, 4, 7, 10, 13, 16, 19]

def coupled(w, a):
    a = M.focus(w, copy.deepcopy(a), "lungs", 0, 1); a = M.focus(w, a, "heart", 1, 0); a = M.focus(w, a, "kidney", 0, 1); return M.membrane(w, a)

def organ_struct2(W, sd, p, st, rooms=True):
    w = W(sd, p, "inside"); past = []; chosen = {}
    while w.t < O.T:
        base = M.decide(w, p, st); plan = Q.own_plan(w, base, p, st)
        br = [("t", base)] + [(f"t-{i}", M.membrane(w, copy.deepcopy(past[-i]))) for i in (1, 2) if len(past) >= i]
        br += [(f"t+{i}", M.membrane(w, copy.deepcopy(plan[i - 1]))) for i in (1, 2) if len(plan) >= i]
        if rooms: br += [("room_" + k, M.room_action(w, p, st, k, None)) for k in M.NAMES]
        br += [("organ_" + k, M.membrane(w, M.focus(w, copy.deepcopy(base), k, 1, 1))) for k in M.NAMES]
        br += [("coupled", coupled(w, base))]
        name, a = max(br, key=lambda o: Q.replay(w, o[1], plan)); chosen[name] = chosen.get(name, 0) + 1
        past.append(base); w.ms, w.md = a[2], a[3]; w.tick(a[0], a[1])
    return float(w.G()), chosen

def child2(sd, pc, sA, sB):
    w = M.Organs(sd, pc, "inside"); past = {"A": [], "B": []}; src = {}; C = ("lungs", "heart", "kidney")
    while w.t < O.T:
        acts = {"A": M.decide(w, pc, sA), "B": M.decide(w, pc, sB)}
        plans = {"A": Q.own_plan(w, acts["A"], pc, sA), "B": Q.own_plan(w, acts["B"], pc, sB)}; opts = []
        for k in ("A", "B"):
            opts.append((k + "0", acts[k]))
            for i in (1, 2):
                if len(past[k]) >= i: opts.append((k + "-" + str(i), M.membrane(w, copy.deepcopy(past[k][-i]))))
                if len(plans[k]) >= i: opts.append((k + "+" + str(i), M.membrane(w, copy.deepcopy(plans[k][i - 1]))))
        for x, y in (("A", "B"), ("B", "A")): opts.append(("coupled" + x, Q.compose(w, acts, {o: (x if o in C else y) for o in M.NAMES})))
        name, a = max(opts, key=lambda o: max(Q.replay(w, o[1], pl) for pl in plans.values())); src[name] = src.get(name, 0) + 1
        for k in ("A", "B"): past[k].append(acts[k])
        w.ms, w.md = a[2], a[3]; w.tick(a[0], a[1])
    return float(w.G()), src

def le_rel(v, sd):
    p = G.params(G.SH["shades"][v - 1]["node"], v); st = L4.st_of(v); R = {}; rows = []
    for rep in (1, 2):
        W = L4.replay_class(rep); S1.LAND.clear(); S1.run_struct(W, sd, p, st); tr = L.take(); R[rep] = (tr, list(S1.LAND))
    for ch, side in (("dry", 0), ("dr", 1)):
        F0 = np.array([t[ch] for t in R[1][0]], bool); F1 = np.array([t[ch] for t in R[2][0]], bool)
        if F0.mean() < 0.01 or F1.mean() < 0.01: continue
        N0 = np.array([t["nbd"] for t in R[1][0]]) > 0; N1 = np.array([t["nbd"] for t in R[2][0]]) > 0
        A0 = np.zeros_like(F0); A1 = np.zeros_like(F1)
        for t, l in enumerate(R[1][1]): A0[t, l[side]] = True
        for t, l in enumerate(R[2][1]): A1[t, l[side]] = True
        d = {}
        for T in (2, 4, 8):
            preds = []
            for i in range(F0.shape[1]):
                ups = [t for t in range(F0.shape[0] - T + 1) if not F0[t, i]]; y = {t: F0[t + 1:t + T, i].any() for t in ups}
                qa = np.mean(list(y.values())) if ups else 0.0
                q = {}
                for l in (0, 1):
                    for n in (0, 1):
                        z = [y[t] for t in ups if A0[t, i] == l and N0[t, i] == n]; q[(l, n)] = np.mean(z) if z else qa
                for k in range(F1.shape[0] // T):
                    t0 = k * T; preds.append(1.0 if F1[t0, i] else q[(int(A1[t0, i]), int(N1[t0, i]))])
            pr = float(np.mean(preds)); m = L.span(F1, T); n = F1.shape[1] * (F1.shape[0] // T)
            tol = 2 * np.sqrt(max(pr * (1 - pr), 1e-12) / n) + 0.01; d[T] = {"pred": pr, "meas": m, "tol": float(tol), "ok": bool(abs(m - pr) <= tol)}
        rows.append({"v": v, "sd": sd, "ch": ch, "detail": d, "ok": all(x["ok"] for x in d.values())})
    return rows

def pair_rows(v):
    P3 = S1.partners3; P2 = P3.P2; S = P2.Sys(2, v, L6.SEEDS[0]); sts = [L4.st_of(u) for u in S.vs]; rows = []
    S.h0 = [np.minimum(h * 3.0, 0.5) for h in S.h0]
    while S.t < O.T:
        acts = []
        for k in (0, 1):
            r = copy.deepcopy(S.w[k].rng); acts.append(L4.step(P3.View(S, k, False), S.p[k], sts[k])); S.w[k].rng = r
        S.tick(acts)
        for k in (0, 1):
            A, B = S.w[k], S.w[1 - k]; nb = np.minimum((A.Ad & A.dr[None, :]).sum(1), 3)
            rows.append([(A.res <= 0).astype(int).tolist(), B.dr.astype(int).tolist(), nb.astype(int).tolist(), A.dr.astype(int).tolist()])
    return rows

def part(k):
    t0 = time.time(); v = L6.SHADES[k]; L6.collect(k); L6.local(k); print("laws", v, round(time.time() - t0), flush=True)
    out = {"v": v, "LE_rel": le_rel(v, L6.SEEDS[0])}
    out["pairs"] = {str(u): pair_rows(u) for u in ALL7[k::2]}; print("le+pairs", v, round(time.time() - t0), flush=True)
    sd = 6720; p = G.params(G.SH["shades"][v - 1]["node"], v); st = L4.st_of(v); sB = L4.st_of(v + 1); pc = M.params_both(v)
    out["S_org"], out["S_org_br"] = organ_struct2(M.Organs, sd, p, st)
    out["best_single"] = max(M.run_house(M.Organs, sd, p, st, "single", o)["G"] for o in M.NAMES)
    out["child"], out["child_src"] = child2(sd, pc, st, sB); out["best_parent"] = max(M.run_parent(M.Organs, sd, pc, s)["G"] for s in (st, sB))
    out["S_living"], out["S_living_br"] = organ_struct2(M.Living, sd, p, st, rooms=False); out["v3_living"] = M.run_parent(M.Living, sd, p, st)["G"]
    out["best_native"] = max([M.F4.run(M.Living, sd, p, n)["G"] for n in O.NATS] + [M.F4.run(M.Living, sd, p, "B")["G"]])
    out["sec"] = round(time.time() - t0); json.dump(out, open(f"diag/S2_part{k}.json", "w"), default=float, indent=1)
    print(json.dumps({x: y for x, y in out.items() if x not in ("pairs", "LE_rel")}, default=float), flush=True)

def final():
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()): L6.analyze()
    lw = json.load(open("diag/QUICK_LAWS6.json"))["summary"]; P = [json.load(open(f"diag/S2_part{k}.json")) for k in (0, 1)]
    pairs = {}; [pairs.update(x["pairs"]) for x in P]
    L5 = []
    for x in P:
        v = x["v"]; fit = L6.l5_counts([r for u in ALL7 if u != v for r in pairs[str(u)]]); test = L6.l5_counts(pairs[str(v)])
        ceR, ce0 = L6.l5_ce(fit, test); L5.append({"v": v, "ceR": ceR, "ce0": ce0, "ok": bool(ceR < ce0)})
    le = [r for x in P for r in x["LE_rel"]]
    C = {"laws_" + q: bool(lw["PASS"][q]) for q in ("EXACT", "L0", "L1p", "L1", "L2", "C2", "C1", "L4", "L3", "PR", "RC")}
    C["LE_relations"] = all(r["ok"] for r in le) and len(le) > 0; C["L5_relations"] = all(r["ok"] for r in L5)
    C["Meaning_M1"] = all(x["S_org"] > x["best_single"] for x in P); C["D_B1"] = all(x["child"] > x["best_parent"] for x in P)
    C["E_E1"] = all(x["S_living"] > x["best_native"] for x in P)
    S = {"checks": C, "TABLE_FILLED": all(C.values()), "E2_reported": [x["S_living"] - x["v3_living"] for x in P], "LE_rel": le, "L5": L5,
         "cells": [{k: x[k] for k in ("v", "S_org", "best_single", "child", "best_parent", "S_living", "v3_living", "best_native", "S_org_br", "child_src", "sec")} for x in P]}
    json.dump(S, open("diag/RESULT_STRUCTURE2.json", "w"), default=float, indent=1); print(json.dumps(S["checks"], indent=1), "\nTABLE_FILLED", S["TABLE_FILLED"])

if __name__ == "__main__":
    part(int(sys.argv[2])) if sys.argv[1] == "part" else final()
