"""LAWS1: all RSOS laws as mathematics, executed on the twin world's per-tick traces (layer 2). Development build.

PART K LINE (map/STRUCTURAL_MAP_22NOV.md, Part K, row "All laws as mathematics"), copied before any build:
  where     : law set -> law of laws
  missing   : G-level invariants never checked as one set on O traces (Part 0 reading)
  structure : every law as invariant + scope + check + response (Part F); axioms + model checking on per-tick traces
              (Part I.6); MATH_V1/V2 as exact cases
  check     : each law holds on fresh traces in its scope; violations predict a lower result; no two laws conflict

HOW (each law = invariant + scope + check + response; a trace = one run of one arm on one shade and seed, recorded per
tick by a subclass of the sealed twin world; sealed code is imported and hash-checked, never edited):
  Hosts inside one trace: supply channel (element i fails at tick t iff res_i <= 0) and drift channel (j drifted).
  L0  Law 0 constitution. Inv: no channel ends worse than the unhealed native (report+popular) of the same shade and
      seed; landings per tick <= 4 (shared budget); res_i <= 3 every tick. Scope: organism arms (v2 = ORG6 own + P1
      counter-shift; own6 = ORG6 own). Response: the monitor logs the tick (guard).
  L1p Law 1' bound (Theorem 1). Inv: fail(n) <= mean of 1 - prod(1 - eps_i) over the read set + 2 SE, n in {2,4,8}.
      Scope: channel traces with mean eps >= 0.01 and mean pairwise covariance of success indicators >= 0 (the
      association proxy; negative association = the corollary, out of scope, counted).
  L1  Law 1 read scope. Inv: fail(1) < fail(2) < fail(4) < fail(8) (n units read at one tick) and the trace classifies
      as element-class (fail(2) - fail(1) >= eps/2). Scope: channel traces with mean eps >= 0.01.
  L2  Law 2 blind operation. Inv (element-class host, mu = eps): blind (one request at t, one reply at t+1 to one
      host unit) fails more than a 1-unit pull and less than a 4- and 8-unit pull. Scope: as L1.
  LE  Law of error events (time windows, MATH_V2 A1/A2). Inv: an operation on one unit spanning T ticks fails with
      eps + (T - 1) * lambda (lambda = failure onsets per unit per tick), T in {2,4,8}; eps, lambda estimated on the
      OTHER development seed of the same shade and arm; |measured - predicted| <= 0.02 + 0.15 * predicted.
      Scope: as L1.
  L3  Law 3 living structure. Damage sweep: drift hazard x k, k in {1, 1.5, 2, 3, 4}, arm v2 and the native
      report+popular. Inv per shade and seed: (a) kept inside the threshold: at every k whose mean drift onsets per
      tick <= 2 (the drift landings per tick), G(k) >= G(1) - 0.03; (b) gradual beyond: the largest drop between
      consecutive k <= 0.6 x the total drop G(1) - G(4) (checked when the total drop > 0.02); (c) the living
      structure keeps more: drop(v2) <= drop(native). Scope: every shade.
  L4  Law 4 landing (particles land where needed). A supply landing is at need iff res_i <= 1.0 before the tick; a
      drift landing iff j is drifted or has a drifted neighbour. Inv: precision >= 0.90. Scope: organism arms.
  L5  Law 5 relations raise the limit. Onset of drift at j (not drifted at t-1, drifted at t) predicted from j's own
      state (dry or not) vs own state + number of drifted neighbours (0,1,2,3+); Laplace-smoothed frequency tables
      fit on one development seed, cross-entropy measured on the other. Inv: CE with relations < CE without.
      Scope: arm v2, every shade, both directions.
  EXACT  MATH_V1/V2 exact cases by Monte Carlo (seed 6402, 200,000 draws each): Theorem 1 equality under
      independence; A1 periodic window law; A3 exchangeable unavailability. Inv: |MC - formula| <= 3 SE.
Law of laws (consistency):
  C1  pairwise: for every pair of laws with >= 10 traces in common scope, P(B fails | A holds) <= P(B fails) + 0.10
      (and with A, B swapped): satisfying one law never pushes another to fail.
  C2  common point: at n = 1 and T = 1, L1, L1p and LE all predict eps; measured fail(1) and the one-tick span
      failure equal eps within 2 SE on every in-scope trace.
Violations predict the result:
  PR  per shade x seed cell, over the six arms (v2, own6, report+popular, round+round, random+random, beam-only),
      Spearman(L0 violation ticks + L4 off-need landings, G) < 0 in >= 2/3 of cells and mean < 0.

QUICK TEST PASS (fixed before the first run): EXACT 3/3; L0, L1p, L1, L2, LE, L4, L5 each hold on >= 90 % of their
in-scope traces; L3 on >= 90 % of shade x seed; C1 no conflict; C2 on >= 90 %; PR as above.
Development seeds only: 6400, 6401 (never used anywhere in the repo; never for colours). Fresh seeds only in a sealed run.
Usage: python laws.py collect <part 0|1> ; python laws.py sweep <part 0|1> ; python laws.py exact ; python laws.py analyze"""
import sys, os, json, glob, hashlib, itertools
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); AN = os.path.join(HERE, "..", "allnodes")
sys.path.insert(0, AN); os.chdir(AN)
assert hashlib.sha256(open("org7.py", "rb").read()).hexdigest() in open("SEAL_ORG7.txt").read(), "org7.py"
import org7 as X
G, O, V3, F4, Z = X.G, X.O, X.V3, X.F4, X.Z
os.chdir(HERE); os.makedirs("diag", exist_ok=True)
SEEDS = [6400, 6401]; KS = [1, 1.5, 2, 3, 4]; NV = G.NV
ORG6 = {}
for f in glob.glob(os.path.join(AN, "org6", "eval_*.json")):
    for r in json.load(open(f)):
        if "seed" in r: ORG6[r["shade"]] = r["structs"]["own"]

TR = {}
def recorder(k=1.0):
    class Rec(G.Shade):
        def __init__(s, seed, p, default):
            super().__init__(seed, p, default)
            if k != 1.0: s.h = np.minimum(s.h * k, 0.5)
            s._rid = id(s); TR[s._rid] = []; TR["last"] = s._rid
        def tick(s, ps, pd, glob=False):
            rec = id(s) == getattr(s, "_rid", None)
            if rec:
                ns = [bool(s.res[i] <= 1.0) for i in ps]
                nd = [bool(s.dr[j] or (s.Ad[j] & s.dr).any()) for j in pd]
                pre_dr, pre_dry = s.dr.copy(), s.res <= 0
            super().tick(ps, pd, glob)
            if rec:
                TR[s._rid].append({"ns": ns, "nd": nd, "nl": len(ps) + len(pd), "dry": (s.res <= 0).tolist(),
                                   "dr": s.dr.tolist(), "pdr": pre_dr.tolist(), "pdry": pre_dry.tolist(),
                                   "nbd": (s.Ad & pre_dr[None, :]).sum(1).tolist(), "maxdry": float(s.maxdry),
                                   "maxd": float(s.maxd), "resmax": float(s.res.max())})
    return Rec

def take():
    t = TR.pop(TR["last"]); TR.clear(); return t

def run_arm(arm, v, sd, p, W):
    if arm == "v2": r = X.run_st2(W, sd, p, dict(Z.unkey(ORG6[v]), cs=1, vote=0, mem=0, joint=0))
    elif arm == "own6": r = Z.run_st(W, sd, p, Z.unkey(ORG6[v]))
    elif arm == "B": r = F4.run(W, sd, p, "B")
    else: r = F4.run(W, sd, p, tuple(arm.split("+")))
    return {"G": r["G"], "ch": r["ch"], "trace": take()}

ARMS = ["v2", "own6", "report+popular", "round+round", "random+random", "B"]

def collect(part):
    W = recorder()
    for v in range(1, NV + 1):
        if v % 2 != part: continue
        p = G.params(G.SH["shades"][v - 1]["node"], v); out = {}
        for sd in SEEDS:
            out[sd] = {a: run_arm(a, v, sd, p, W) for a in ARMS}
        json.dump(out, open(f"diag/trace_v{v}.json", "w")); print("collect", v, flush=True)

def sweep(part):
    out = {}
    for v in range(1, NV + 1):
        if v % 2 != part: continue
        p = G.params(G.SH["shades"][v - 1]["node"], v); out[v] = {}
        for sd in SEEDS:
            for k in KS:
                W = recorder(k)
                for a in ("v2", "report+popular"):
                    r = run_arm(a, v, sd, p, W); tr = r["trace"]
                    on = np.mean([sum(x and not y for x, y in zip(t["dr"], t["pdr"])) for t in tr])
                    out[v][f"{sd}|{k}|{a}"] = {"G": r["G"], "onsets": float(on)}
        print("sweep", v, flush=True)
    json.dump(out, open(f"diag/sweep_p{part}.json", "w"))

def exact():
    rng = np.random.default_rng(6402); M = 200_000; res = {}
    eps = np.array([0.02, 0.05, 0.1, 0.03, 0.07]); A = rng.random((M, 5)) >= eps
    mc = 1 - A.all(1).mean(); f = 1 - np.prod(1 - eps); se = np.sqrt(mc * (1 - mc) / M)
    res["thm1_independent"] = {"mc": mc, "formula": f, "se": se, "ok": bool(abs(mc - f) <= 3 * se)}
    U, P, dl = 0.7, 100.0, 0.01
    for n in (1, 10, 50, 200):
        s = rng.random(M) * P; T = dl * (n - 1)
        # fails iff [s, s+T] leaves the window [0, U*P) of the period
        mcv = ((s >= U * P) | (s + T >= U * P)).mean() if T < P - U * P else 1.0
        fv = (1 - U) + T / P; se = np.sqrt(mcv * (1 - mcv) / M)
        res[f"A1_n{n}"] = {"mc": float(mcv), "formula": fv, "se": se, "ok": bool(abs(mcv - fv) <= 3 * se)}
    N, k, n = 300, 10, 50; Mm = 50_000
    fails = np.array([bool(set(rng.choice(N, n, replace=False)) & set(range(k))) for _ in range(Mm)]).mean()
    from math import comb
    fv = 1 - comb(N - k, n) / comb(N, n); se = np.sqrt(fails * (1 - fails) / Mm)
    res["A3_exchangeable"] = {"mc": float(fails), "formula": fv, "bound": 1 - (1 - k / N) ** n, "se": se,
                              "ok": bool(abs(fails - fv) <= 3 * se and fv > 1 - (1 - k / N) ** n)}
    json.dump(res, open("diag/exact.json", "w"), indent=1, default=float); print(json.dumps(res, indent=1, default=float))

# ---------------- analysis ----------------
def mat(tr, key): return np.array([t[key] for t in tr], bool)

def reads(F, rng, n, S=4000):
    T, N = F.shape; ts = rng.integers(T, size=S); sub = np.array([rng.choice(N, n, replace=False) for _ in range(S)])
    fl = F[ts[:, None], sub].any(1); eps = F.mean(0); b = 1 - np.prod(1 - eps[sub], 1)
    return fl.mean(), np.sqrt(fl.mean() * (1 - fl.mean()) / S), b.mean()

def assoc(F):
    Sx = (~F).astype(float); C = np.cov(Sx.T); N = C.shape[0]; return float((C.sum() - np.trace(C)) / (N * (N - 1)))

def span(F, T):
    Tt, N = F.shape; m = [F[t:t + T].any(0).mean() for t in range(Tt - T + 1)]; return float(np.mean(m))

def onset_rate(F):
    return float((F[1:] & ~F[:-1]).mean())

def law_channel(F, Fo, rng):
    eps = F.mean(); out = {"eps": float(eps)}
    if eps < 0.01: return {**out, "scope": False}
    r = {n: reads(F, rng, n) for n in (1, 2, 4, 8)}; a = assoc(F)
    out.update(scope=True, fail={n: r[n][0] for n in r}, se={n: r[n][1] for n in r}, bound={n: r[n][2] for n in r}, assoc=a)
    out["L1p_scope"] = a >= 0
    out["L1p"] = bool(all(r[n][0] <= r[n][2] + 2 * r[n][1] for n in (2, 4, 8))) if a >= 0 else None
    elem = r[2][0] - r[1][0] >= eps / 2
    out["L1"] = bool(elem and r[1][0] < r[2][0] < r[4][0] < r[8][0])
    S = 4000; ts = rng.integers(F.shape[0] - 1, size=S); us = rng.integers(F.shape[1], size=S)
    blind = (F[ts, us] | F[ts + 1, us]).mean(); out["blind"] = float(blind)
    out["L2"] = bool(r[1][0] < blind < r[4][0] and blind < r[8][0])
    eo, lo = Fo.mean(), onset_rate(Fo); le = {}
    for T in (2, 4, 8):
        pr = eo + (T - 1) * lo; m = span(F, T); le[T] = {"pred": float(pr), "meas": m, "ok": bool(abs(m - pr) <= 0.02 + 0.15 * pr)}
    out["LE_detail"] = le; out["LE"] = bool(all(x["ok"] for x in le.values()))
    out["C2"] = bool(abs(r[1][0] - eps) <= 2 * r[1][1] + 1e-12 and abs(span(F, 1) - eps) < 1e-9)
    return out

def l5_counts(trs):
    cnt = np.ones((2, 4, 2))  # own dry, drifted neighbours (0..3+), onset; Laplace +1
    for tr in trs:
        for t in tr:
            pdr, dr, pdry, nb = np.array(t["pdr"]), np.array(t["dr"]), np.array(t["pdry"]), np.minimum(np.array(t["nbd"]), 3)
            m = ~pdr
            for a, b, y in zip(pdry[m].astype(int), nb[m], (dr & ~pdr)[m].astype(int)): cnt[a, b, y] += 1
    return cnt

def l5_ce(fit, test):
    pR = fit[:, :, 1] / fit.sum(2); f0 = fit.sum(1); p0 = f0[:, 1] / f0.sum(1); ceR = ce0 = 0.0; n = 0
    for a in range(2):
        for b in range(4):
            for y in range(2):
                c = test[a, b, y] - 1
                if c <= 0: continue
                q = pR[a, b] if y else 1 - pR[a, b]; q0 = p0[a] if y else 1 - p0[a]
                ceR -= c * np.log2(q); ce0 -= c * np.log2(q0); n += c
    return ceR / n, ce0 / n

def spearman(x, y):
    from scipy.stats import spearmanr
    r = spearmanr(x, y).correlation; return None if np.isnan(r) else float(r)

def analyze():
    ex = json.load(open("diag/exact.json")); rng = np.random.default_rng(6403); S = {}; cells = []; L3 = []; L5 = []
    sw = {}
    for f in glob.glob("diag/sweep_p*.json"): sw.update({int(a): b for a, b in json.load(open(f)).items()})
    for v in range(1, NV + 1):
        D = json.load(open(f"diag/trace_v{v}.json")); D = {int(a): b for a, b in D.items()}
        for sd in SEEDS:
            od = SEEDS[1 - SEEDS.index(sd)]; ref = D[sd]["report+popular"]["ch"]; viol, Gs = [], []
            for a in ARMS:
                tr = D[sd][a]["trace"]; key = (v, sd, a); s = {}
                l0t = sum((t["maxdry"] > ref[0]) + (t["maxd"] > ref[1]) for t in tr)
                lands = sum(len(t["ns"]) + len(t["nd"]) for t in tr); off = sum((not x) for t in tr for x in t["ns"] + t["nd"])
                if a in ("v2", "own6"):
                    s["L0"] = bool(l0t == 0 and all(t["nl"] <= 4 and t["resmax"] <= 3.0 + 1e-9 for t in tr))
                    s["L4"] = bool(lands == 0 or 1 - off / lands >= 0.90); s["L4_precision"] = 1 - off / max(1, lands)
                viol.append(l0t + off); Gs.append(D[sd][a]["G"])
                for ch, kk in (("sup", "dry"), ("dri", "dr")):
                    c = law_channel(mat(tr, kk), mat(D[od][a]["trace"], kk), rng); s[ch] = c
                S[f"{v}|{sd}|{a}"] = s
            cells.append({"v": v, "sd": sd, "rho": spearman(viol, Gs), "viol": viol, "G": Gs})
        fA, fB = l5_counts([D[SEEDS[0]]["v2"]["trace"]]), l5_counts([D[SEEDS[1]]["v2"]["trace"]])
        for name, fit, test in (("A->B", fA, fB), ("B->A", fB, fA)):
            ceR, ce0 = l5_ce(fit, test); L5.append({"v": v, "dir": name, "ceR": ceR, "ce0": ce0, "ok": bool(ceR < ce0)})
        for sd in SEEDS:
            g = {a: [sw[v][f"{sd}|{k}|{a}"]["G"] for k in KS] for a in ("v2", "report+popular")}
            on = [sw[v][f"{sd}|{k}|v2"]["onsets"] for k in KS]
            keep = all(g["v2"][i] >= g["v2"][0] - 0.03 for i, k in enumerate(KS) if on[i] <= 2)
            drop = g["v2"][0] - g["v2"][-1]; steps = [g["v2"][i] - g["v2"][i + 1] for i in range(len(KS) - 1)]
            grad = drop <= 0.02 or max(steps) <= 0.6 * drop
            dn = g["report+popular"][0] - g["report+popular"][-1]
            L3.append({"v": v, "sd": sd, "G_v2": g["v2"], "G_nat": g["report+popular"], "onsets": on, "keep": bool(keep),
                       "gradual": bool(grad), "drop": drop, "drop_nat": dn, "ok": bool(keep and grad and drop <= dn)})
    def rate(vals):
        vals = [x for x in vals if x is not None]; return (sum(vals), len(vals))
    R = {}
    R["EXACT"] = (sum(x["ok"] for x in ex.values()), len(ex))
    R["L0"] = rate([s["L0"] for k, s in S.items() if "L0" in s]); R["L4"] = rate([s["L4"] for k, s in S.items() if "L4" in s])
    for L in ("L1p", "L1", "L2", "LE", "C2"):
        R[L] = rate([s[ch].get(L) for s in S.values() for ch in ("sup", "dri") if s[ch]["scope"]])
    R["L1p_out_of_scope_negative_assoc"] = sum(1 for s in S.values() for ch in ("sup", "dri") if s[ch]["scope"] and not s[ch]["L1p_scope"])
    R["L3"] = (sum(x["ok"] for x in L3), len(L3)); R["L5"] = (sum(x["ok"] for x in L5), len(L5))
    rh = [c["rho"] for c in cells if c["rho"] is not None]
    R["PR"] = {"neg_cells": sum(r < 0 for r in rh), "cells": len(rh), "mean_rho": float(np.mean(rh))}
    # C1 pairwise consistency over traces (channel laws per trace-channel; trace laws per trace)
    rows = []
    for k, s in S.items():
        for ch in ("sup", "dri"):
            c = s[ch]; rows.append({"L0": s.get("L0"), "L4": s.get("L4"), **({L: c.get(L) for L in ("L1p", "L1", "L2", "LE")} if c["scope"] else {})})
    laws = ["L0", "L4", "L1p", "L1", "L2", "LE"]; conf = []
    for A, B in itertools.permutations(laws, 2):
        both = [r for r in rows if r.get(A) is not None and r.get(B) is not None]
        if len(both) < 10: continue
        pf = np.mean([not r[B] for r in both]); ah = [r for r in both if r[A]]
        if not ah: continue
        pfa = np.mean([not r[B] for r in ah]); conf.append({"A": A, "B": B, "n": len(both), "P_B_fail": float(pf), "P_B_fail_given_A": float(pfa), "conflict": bool(pfa > pf + 0.10)})
    R["C1_conflicts"] = sum(c["conflict"] for c in conf); R["C1_pairs"] = len(conf)
    ok = lambda t: t[1] > 0 and t[0] / t[1] >= 0.90
    R["PASS"] = {"EXACT": R["EXACT"][0] == R["EXACT"][1], **{L: ok(R[L]) for L in ("L0", "L1p", "L1", "L2", "LE", "L4", "L5", "L3", "C2")},
                 "C1": R["C1_conflicts"] == 0, "PR": R["PR"]["neg_cells"] >= 2 * R["PR"]["cells"] / 3 and R["PR"]["mean_rho"] < 0}
    R["ROW_PASS"] = all(R["PASS"].values())
    json.dump({"summary": R, "per_trace": S, "cells": cells, "L3": L3, "L5": L5, "C1": conf}, open("diag/QUICK_LAWS.json", "w"), default=float)
    print(json.dumps(R, indent=1, default=float))

if __name__ == "__main__":
    c = sys.argv[1]
    if c == "collect": collect(int(sys.argv[2]))
    elif c == "sweep": sweep(int(sys.argv[2]))
    elif c == "exact": exact()
    else: analyze()
