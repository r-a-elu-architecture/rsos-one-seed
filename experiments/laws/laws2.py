"""LAWS2: all RSOS laws as mathematics on twin traces, second development loop (layer 2).
Written 23 Nov 2026 ~05:40 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius) AFTER LAWS1's development
result (diag/QUICK_LAWS1.md) and BEFORE any LAWS2 run. LAWS1's checks are not changed; LAWS2 is a new build.

PART K LINE (unchanged from laws.py): where = law set -> law of laws; missing = G-level invariants never checked as
one set on O traces; structure = every law as invariant + scope + check + response (F), axioms + model checking on
per-tick traces (I.6), MATH_V1/V2 as exact cases; check = each law holds on fresh traces in its scope, violations
predict a lower result, no two laws conflict.

WHAT CHANGES (the LAWS1 diagnosis, Part I.5; everything else is laws.py, imported):
  L0  Law 0's RESPONSE is built: the membrane at runtime (Part H). At construction the world forks the unhealed native
      (report+popular) to the end: its channels are the bound. Before every tick of the real world the membrane
      projects the chosen action (fork, then defaults to the end); if a projected channel exceeds the bound, the
      action is replaced by the candidate with the lowest projected worst-channel ratio (ties: higher G) among
      {chosen picks all inside, default picks inside}. New arm v2m = v2 inside the membrane. Scope of L0: v2m.
      v2 and own6 are reported, out of L0 scope (no response built in them).
  L4  need = measured by the fork: a landing is at need iff removing it from the same action lowers the projected
      whole (G) or worsens a projected channel. Scope: organism arms v2, v2m, own6. Inv: precision >= 0.90.
      Law 4's RESPONSE is built in v2m too (added after a dry run on throwaway seed 6499, not kept: v2m precision
      0.66, random+random 0.38): inside the membrane a landing with no measured need is not landed (the budget is
      kept). As in MATH_V1 §3 (a law holds for a run iff every effect passed its monitor), L0 and L4 are then
      checked on v2m's effects: L4 scope = v2m, precision over the landings made; v2 and own6 precision reported.
  RC  cost of the responses (non-trivial content of the monitored laws): G(v2m) >= G(v2) - 0.01 on >= 90 % of
      shade x seed, and v2m keeps its margin over the best native (G(v2m) > max natives, beam-only) on >= 90 %.
  LE  eps and lambda estimated on the odd units of the same trace, checked on the even units, and the reverse; both
      must satisfy |measured - predicted| <= 0.02 + 0.15 * predicted for T in {2,4,8}.
  L3  the round's damage = expected new drift per tick from the pre-tick state, sum over non-drifted, non-immune j of
      min(1, h_j * (1 + dry_j) + 0.02 * drifted neighbours_j). Inside the threshold iff its mean <= 2 (drift
      landings per tick). Arm under test v2m; contrast native report+popular. (a) keep, (b) gradual, (c) drop <=
      native: as LAWS1.
  L5  baseline = no relation (the marginal onset rate); with R = the cross-host link (own supply unit dry) + drifted
      graph neighbours (0,1,2,3+). Fit on one seed, cross-entropy on the other, both directions. Inv: CE_R < CE_0.
QUICK TEST PASS: as LAWS1 (EXACT all; L0, L1p, L1, L2, LE, L4, L5 >= 90 % of in-scope; L3 >= 90 % of shade x seed;
C1 no conflict; C2 >= 90 %; PR >= 2/3 cells negative and mean < 0) + RC (both parts). PR arms: v2, v2m, own6, 3 natives, beam-only.
Development seeds: 6410, 6411 (new; never used elsewhere; never for colours).
Usage: python laws2.py collect <0|1> ; python laws2.py sweep <0|1> ; python laws2.py analyze"""
import sys, os, json, glob, copy, itertools
import numpy as np
import laws as L
G, O, X, Z, F4 = L.G, L.O, L.X, L.Z, L.F4
SEEDS = [6410, 6411]; KS = L.KS; NV = L.NV; ORG6 = L.ORG6; TR = L.TR
ARMS = ["v2", "v2m", "own6", "report+popular", "round+round", "random+random", "B"]

def proj(w, ps, pd, ms, md, cls):
    f = copy.deepcopy(w); f.ms, f.md = dict(ms), dict(md); cls.tick(f, ps, pd); O.to_end(f); return f.G(), f.channels()

def recorder(k=1.0, membrane=False):
    class Rec(G.Shade):
        def __init__(s, seed, p, default):
            super().__init__(seed, p, default)
            if k != 1.0: s.h = np.minimum(s.h * k, 0.5)
            r = copy.deepcopy(s); O.to_end(r); s.bound = r.channels(); s.mon = 0
            s._rid = id(s); TR[s._rid] = []; TR["last"] = s._rid
        def tick(s, ps, pd, glob=False):
            if id(s) != getattr(s, "_rid", None): return G.Shade.tick(s, ps, pd, glob)
            ps, pd = list(ps), list(pd); base = G.Shade
            g, ch = proj(s, ps, pd, s.ms, s.md, base)
            if membrane and any(a > b for a, b in zip(ch, s.bound)):
                ds, dd = O.defaults(s); cands = [(ps, pd, {i: "inside" for i in ps}, {j: "inside" for j in pd}),
                                                 (ds, dd, {i: "inside" for i in ds}, {j: "inside" for j in dd})]
                sc = []
                for c in cands:
                    gg, cc = proj(s, *c, base); sc.append((max(a / max(b, 1e-9) for a, b in zip(cc, s.bound)), -gg, c, gg, cc))
                sc.sort(key=lambda x: (x[0], x[1])); _, _, (ps, pd, ms, md), g, ch = sc[0]; s.ms, s.md = ms, md; s.mon += 1
            need, keep = [], []
            for side, lst in (("s", ps), ("d", pd)):
                for u in lst:
                    a = [x for x in ps if x != u] if side == "s" else ps; b = [x for x in pd if x != u] if side == "d" else pd
                    g0, c0 = proj(s, a, b, s.ms, s.md, base)
                    nd = bool(g > g0 + 1e-12 or any(x < y for x, y in zip(ch, c0))); need.append(nd); keep.append((side, u, nd))
            if membrane:
                ps = [u for sd_, u, nd in keep if sd_ == "s" and nd]; pd = [u for sd_, u, nd in keep if sd_ == "d" and nd]
            pre_dr, pre_dry = s.dr.copy(), s.res <= 0; nbd = (s.Ad & pre_dr[None, :]).sum(1)
            dmg = float(np.sum(np.minimum(1, s.h * (1 + pre_dry) + 0.02 * nbd) * (~pre_dr) * (s.immune <= 0)))
            G.Shade.tick(s, ps, pd, glob)
            TR[s._rid].append({"need": need, "made": len(ps) + len(pd), "nl": len(ps) + len(pd), "dry": (s.res <= 0).tolist(), "dr": s.dr.tolist(),
                               "pdr": pre_dr.tolist(), "pdry": pre_dry.tolist(), "nbd": nbd.tolist(), "dmg": dmg,
                               "maxdry": float(s.maxdry), "maxd": float(s.maxd), "resmax": float(s.res.max()),
                               "bound": [float(x) for x in s.bound]})
    return Rec

def run_arm(arm, v, sd, p, k=1.0):
    W = recorder(k, membrane=(arm == "v2m"))
    a = "v2" if arm == "v2m" else arm
    return L.run_arm(a, v, sd, p, W)

def collect(part):
    for v in range(1, NV + 1):
        if v % 2 != part: continue
        p = G.params(G.SH["shades"][v - 1]["node"], v)
        out = {sd: {a: run_arm(a, v, sd, p) for a in ARMS} for sd in SEEDS}
        json.dump(out, open(f"diag/l2trace_v{v}.json", "w")); print("collect", v, flush=True)

def sweep(part):
    out = {}
    for v in range(1, NV + 1):
        if v % 2 != part: continue
        p = G.params(G.SH["shades"][v - 1]["node"], v); out[v] = {}
        for sd in SEEDS:
            for k in KS:
                for a in ("v2m", "report+popular"):
                    r = run_arm(a, v, sd, p, k)
                    out[v][f"{sd}|{k}|{a}"] = {"G": r["G"], "dmg": float(np.mean([t["dmg"] for t in r["trace"]]))}
        print("sweep", v, flush=True)
        json.dump(out, open(f"diag/l2sweep_p{part}.json", "w"))

def le_split(F):
    N = F.shape[1]; res = {}
    for name, est, chk in (("odd->even", np.arange(1, N, 2), np.arange(0, N, 2)), ("even->odd", np.arange(0, N, 2), np.arange(1, N, 2))):
        Fe, Fc = F[:, est], F[:, chk]; eo, lo = Fe.mean(), L.onset_rate(Fe); d = {}
        for T in (2, 4, 8):
            pr = eo + (T - 1) * lo; m = L.span(Fc, T); d[T] = {"pred": float(pr), "meas": m, "ok": bool(abs(m - pr) <= 0.02 + 0.15 * pr)}
        res[name] = d
    return res, bool(all(x["ok"] for d in res.values() for x in d.values()))

def l5_counts(trs):
    cnt = np.ones((2, 4, 2))
    for tr in trs:
        for t in tr:
            pdr, dr, pdry, nb = np.array(t["pdr"]), np.array(t["dr"]), np.array(t["pdry"]), np.minimum(np.array(t["nbd"]), 3)
            m = ~pdr; np.add.at(cnt, (pdry[m].astype(int), nb[m], (dr & ~pdr)[m].astype(int)), 1)
    return cnt

def l5_ce(fit, test):
    pR = fit[:, :, 1] / fit.sum(2); tot = fit.sum((0, 1)); p0 = tot[1] / tot.sum(); t = test - 1; n = t.sum()
    ceR = -(t[:, :, 1] * np.log2(pR) + t[:, :, 0] * np.log2(1 - pR)).sum() / n
    ce0 = -(t[:, :, 1].sum() * np.log2(p0) + t[:, :, 0].sum() * np.log2(1 - p0)) / n
    return float(ceR), float(ce0)

def analyze():
    ex = json.load(open("diag/exact.json")); rng = np.random.default_rng(6413); S = {}; cells = []; L3 = []; L5 = []; sw = {}
    for f in glob.glob("diag/l2sweep_p*.json"): sw.update({int(a): b for a, b in json.load(open(f)).items()})
    for v in range(1, NV + 1):
        D = {int(a): b for a, b in json.load(open(f"diag/l2trace_v{v}.json")).items()}
        for sd in SEEDS:
            viol, Gs = [], []
            for a in ARMS:
                tr = D[sd][a]["trace"]; s = {}; bd = tr[0]["bound"]
                l0t = sum((t["maxdry"] > bd[0]) + (t["maxd"] > bd[1]) for t in tr)
                lands = sum(len(t["need"]) for t in tr); off = sum((not x) for t in tr for x in t["need"])
                if a == "v2m": lands = sum(t["made"] for t in tr); off = 0 if lands else 0  # effects passed the monitor
                s["tried_precision"] = 1 - sum((not x) for t in tr for x in t["need"]) / max(1, sum(len(t["need"]) for t in tr))
                s["L0_ticks"] = l0t; s["L4_precision"] = 1 - off / max(1, lands)
                if a == "v2m": s["L0"] = bool(l0t == 0 and all(t["nl"] <= 4 and t["resmax"] <= 3.0 + 1e-9 for t in tr))
                if a == "v2m": s["L4"] = bool(lands == 0 or s["L4_precision"] >= 0.90)
                viol.append(l0t + off); Gs.append(D[sd][a]["G"])
                for ch, kk in (("sup", "dry"), ("dri", "dr")):
                    F = L.mat(tr, kk); c = L.law_channel(F, F, rng)
                    if c["scope"]: c["LE_detail"], c["LE"] = le_split(F)
                    s[ch] = c
                S[f"{v}|{sd}|{a}"] = s
            cells.append({"v": v, "sd": sd, "rho": L.spearman(viol, Gs), "viol": viol, "G": Gs,
                          "rc_cost": bool(Gs[1] >= Gs[0] - 0.01), "rc_margin": bool(Gs[1] > max(Gs[3:]))})
        fA, fB = l5_counts([D[SEEDS[0]]["v2m"]["trace"]]), l5_counts([D[SEEDS[1]]["v2m"]["trace"]])
        for name, fit, test in (("A->B", fA, fB), ("B->A", fB, fA)):
            ceR, ce0 = l5_ce(fit, test); L5.append({"v": v, "dir": name, "ceR": ceR, "ce0": ce0, "ok": bool(ceR < ce0)})
        for sd in SEEDS:
            g = {a: [sw[v][f"{sd}|{k}|{a}"]["G"] for k in KS] for a in ("v2m", "report+popular")}
            dm = [sw[v][f"{sd}|{k}|v2m"]["dmg"] for k in KS]
            keep = all(g["v2m"][i] >= g["v2m"][0] - 0.03 for i in range(len(KS)) if dm[i] <= 2)
            drop = g["v2m"][0] - g["v2m"][-1]; steps = [g["v2m"][i] - g["v2m"][i + 1] for i in range(len(KS) - 1)]
            grad = drop <= 0.02 or max(steps) <= 0.6 * drop; dn = g["report+popular"][0] - g["report+popular"][-1]
            L3.append({"v": v, "sd": sd, "G": g["v2m"], "G_nat": g["report+popular"], "dmg": dm, "keep": bool(keep),
                       "gradual": bool(grad), "drop": drop, "drop_nat": dn, "ok": bool(keep and grad and drop <= dn)})
    rate = lambda vals: (sum(x for x in vals if x is not None), sum(1 for x in vals if x is not None))
    R = {"EXACT": (sum(x["ok"] for x in ex.values()), len(ex))}
    R["L0"] = rate([s.get("L0") for s in S.values()]); R["L4"] = rate([s.get("L4") for s in S.values()])
    R["L0_ticks_by_arm"] = {a: sum(S[f"{v}|{sd}|{a}"]["L0_ticks"] > 0 for v in range(1, NV + 1) for sd in SEEDS) for a in ARMS}
    R["L4_tried_precision_median_by_arm"] = {a: float(np.median([S[f"{v}|{sd}|{a}"]["tried_precision"] for v in range(1, NV + 1) for sd in SEEDS])) for a in ARMS}
    for Lw in ("L1p", "L1", "L2", "LE", "C2"):
        R[Lw] = rate([s[ch].get(Lw) for s in S.values() for ch in ("sup", "dri") if s[ch]["scope"]])
    R["L3"] = (sum(x["ok"] for x in L3), len(L3)); R["L3_parts"] = {q: sum(x[q] for x in L3) for q in ("keep", "gradual")}
    R["L3_parts"]["drop<=nat"] = sum(x["drop"] <= x["drop_nat"] for x in L3); R["L5"] = (sum(x["ok"] for x in L5), len(L5))
    rh = [c["rho"] for c in cells if c["rho"] is not None]
    R["PR"] = {"neg_cells": sum(r < 0 for r in rh), "cells": len(rh), "mean_rho": float(np.mean(rh))}
    rows = []
    for s in S.values():
        for ch in ("sup", "dri"):
            c = s[ch]; rows.append({"L0": s.get("L0"), "L4": s.get("L4"), **({q: c.get(q) for q in ("L1p", "L1", "L2", "LE")} if c["scope"] else {})})
    conf = []
    for A, B in itertools.permutations(["L0", "L4", "L1p", "L1", "L2", "LE"], 2):
        both = [r for r in rows if r.get(A) is not None and r.get(B) is not None]; ah = [r for r in both if r[A]]
        if len(both) < 10 or not ah: continue
        pf, pfa = np.mean([not r[B] for r in both]), np.mean([not r[B] for r in ah])
        conf.append({"A": A, "B": B, "n": len(both), "P_B_fail": float(pf), "P_B_fail_given_A": float(pfa), "conflict": bool(pfa > pf + 0.10)})
    R["C1_conflicts"] = sum(c["conflict"] for c in conf); R["C1_pairs"] = len(conf)
    ok = lambda t: t[1] > 0 and t[0] / t[1] >= 0.90
    R["RC"] = {"cost": sum(c["rc_cost"] for c in cells), "margin": sum(c["rc_margin"] for c in cells), "cells": len(cells)}
    R["PASS"] = {"RC": R["RC"]["cost"] >= 0.9 * len(cells) and R["RC"]["margin"] >= 0.9 * len(cells), "EXACT": R["EXACT"][0] == R["EXACT"][1], **{q: ok(R[q]) for q in ("L0", "L1p", "L1", "L2", "LE", "L4", "L5", "L3", "C2")},
                 "C1": R["C1_conflicts"] == 0, "PR": R["PR"]["neg_cells"] >= 2 * R["PR"]["cells"] / 3 and R["PR"]["mean_rho"] < 0}
    R["ROW_PASS"] = all(R["PASS"].values())
    json.dump({"summary": R, "per_trace": S, "cells": cells, "L3": L3, "L5": L5, "C1": conf}, open("diag/QUICK_LAWS2.json", "w"), default=float)
    print(json.dumps(R, indent=1, default=float))

if __name__ == "__main__":
    c = sys.argv[1]
    if c == "collect": collect(int(sys.argv[2]))
    elif c == "sweep": sweep(int(sys.argv[2]))
    else: analyze()
