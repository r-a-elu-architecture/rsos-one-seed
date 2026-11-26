"""LAWS3: all RSOS laws as mathematics on twin traces, third development loop (layer 2).
Written 23 Nov 2026 ~07:00 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius) AFTER LAWS2's development result
(diag/QUICK_LAWS2.md) and BEFORE any LAWS3 run. LAWS1 and LAWS2 checks are not changed; LAWS3 is a new build.

PART K LINE (unchanged): where = law set -> law of laws; missing = G-level invariants never checked as one set on O
traces; structure = every law as invariant + scope + check + response (F), axioms + model checking on per-tick traces
(I.6), MATH_V1/V2 as exact cases; check = each law holds on fresh traces in its scope, violations predict a lower
result, no two laws conflict.

WHAT CHANGES (LAWS2 diagnosis; everything not named here is laws.py / laws2.py, imported):
  BUDGET  Finding of LAWS1/LAWS2: ORG7's counter-shift (org7.run_st2, sealed, not edited) adds a 5th landing when a
          side has no slot. New arm v3 = run_st3 below = run_st2 with P1 kept inside the shared budget of 4 (if the
          total exceeds 4 after the counter-shift, the last non-counter-shifted landing of the larger side is
          dropped). v2 stays as the sealed record.
  MEMBRANE  arm v3m = v3 inside the membrane, responses in the program order (U157: act, then protect last):
          (1) Law 4 re-target: a landing whose removal changes neither the projected whole nor a projected channel
              is replaced by the best of the 3 highest-lack units of its side (lack_s / lack_d, not already picked)
              whose landing has a measured need (largest projected G); if none has, the landing is kept.
          (2) Law 0 gate, last: if the final action's projected channel exceeds the bound (the unhealed native forked
              to the end at construction), the action is replaced by the lower worst-channel ratio of {final picks
              all inside, default picks inside} (ties: higher G).
          (3) need is measured again on the landings actually made (L4 precision over made landings).
  LE  domain and sampling error: for each direction (odd -> even units, even -> odd) the law is checked at
      T in {2,4,8} with T <= tau/2, tau = 1 / lambda (MATH_V2 A2: the linear form holds for T << tau); tolerance
      |meas - pred| <= 2 * sqrt(pred (1 - pred) / n) + 0.01, n = checked units x floor(ticks / T). In scope iff
      eps >= 0.01 and at least one T is in the domain.
  L5  leave one shade out: the tables are fit on arm v3m traces of the other 20 shades (both seeds) and the
      cross-entropy measured on this shade (both seeds). Inv: CE_R < CE_0.
  L0 scope v3m (also budget <= 4 every tick); L4 scope v3m (made landings); L3 arm v3m vs native report+popular;
  RC: G(v3m) >= G(v3) - 0.01 and G(v3m) > max(natives, beam-only), each on >= 90 % of shade x seed.
  Also reported (no criterion): budget overruns per arm.
QUICK TEST PASS: as LAWS2 (EXACT all; L0, L1p, L1, L2, LE, L4, L5 >= 90 % of in-scope; L3 >= 90 %; C1 no conflict;
C2 >= 90 %; PR >= 2/3 cells negative, mean < 0; RC both parts). PR arms: all 8.
Development seeds: 6420, 6421 (new; never used elsewhere; never for colours). Dry run before sealing this file: throwaway
seed 6499, shade 3, not kept: v3m G 0.9669 vs v3 0.9783, made precision 0.69, 16 re-targets, 7 gates; v3 budget max 4.
Usage: python laws3.py collect <0|1> ; python laws3.py sweep <0|1> ; python laws3.py analyze"""
import sys, os, json, glob, copy, itertools
import numpy as np
import laws as L, laws2 as L2
G, O, V3, X, Z, F4 = L.G, L.O, L.V3, L.X, L.Z, L.F4
SEEDS = [6420, 6421]; KS = L.KS; NV = L.NV; ORG6 = L.ORG6; TR = L.TR; proj = L2.proj
ARMS = ["v2", "v3", "v3m", "own6", "report+popular", "round+round", "random+random", "B"]

def run_st3(W, seed, p, st):
    """org7.run_st2 with the counter-shift kept inside the shared budget (the only change)."""
    w = W(seed, p, "inside"); bm = "above" if "above" in p["modes"] else ("pierced" if "pierced" in p["modes"] else None); memo = {}
    while w.t < O.T:
        ps, pd = V3.org3_picks(w) if st["det"] else O.defaults(w); ps, pd = list(ps), list(pd); n0 = len(ps) + len(pd)
        if st["cs"]:
            i = int(np.argmax(w.dry)); j = int(np.argmax(w.dur)); th = st.get("cs_th", 2); ci = cj = None
            if w.dry[i] >= th and i not in ps: ps = [i] + ps[:-1]; ci = i
            if w.dur[j] >= th and j not in pd: pd = [j] + pd[:-1]; cj = j
            while len(ps) + len(pd) > max(n0, 2 * O.KH):
                big = ps if len(ps) >= len(pd) else pd; keep = ci if big is ps else cj
                idx = max(k for k, u in enumerate(big) if u != keep); big.pop(idx)
        ms, md = {i: "inside" for i in ps}, {j: "inside" for j in pd}
        if st["adapt"]: ms, md = X.beam2(w, ps, pd, p["modes"], st, memo)
        if st["barrier"] and bm:
            if ps: ms[ps[0]] = bm
            if pd: md[pd[0]] = bm
        if st["guard"]:
            ds, dd = O.defaults(w); m0, d0 = {i: "inside" for i in ds}, {j: "inside" for j in dd}
            if any(a > b for a, b in zip(F4.proj(w, ps, pd, ms, md)[1], F4.proj(w, ds, dd, m0, d0)[1])): ps, pd, ms, md = ds, dd, m0, d0
        w.ms, w.md = ms, md; w.tick(ps, pd)
    return {"G": float(w.G()), "ch": [float(x) for x in w.channels()], "flows": int(w.flows)}

def needs(s, ps, pd, ms, md, base):
    g, ch = proj(s, ps, pd, ms, md, base); out = []
    for side, lst in (("s", ps), ("d", pd)):
        for u in lst:
            a = [x for x in ps if x != u] if side == "s" else ps; b = [x for x in pd if x != u] if side == "d" else pd
            g0, c0 = proj(s, a, b, ms, md, base); out.append((side, u, bool(g > g0 + 1e-12 or any(x < y for x, y in zip(ch, c0))), g0, c0))
    return g, ch, out

def recorder(k=1.0, membrane=False):
    class Rec(G.Shade):
        def __init__(s, seed, p, default):
            super().__init__(seed, p, default)
            if k != 1.0: s.h = np.minimum(s.h * k, 0.5)
            r = copy.deepcopy(s); O.to_end(r); s.bound = r.channels()
            s._rid = id(s); TR[s._rid] = []; TR["last"] = s._rid
        def tick(s, ps, pd, glob=False):
            base = G.Shade
            if id(s) != getattr(s, "_rid", None): return base.tick(s, ps, pd, glob)
            ps, pd = list(ps), list(pd); ms, md = dict(s.ms), dict(s.md); g, ch, nd = needs(s, ps, pd, ms, md, base)
            tried = [x[2] for x in nd]; ev = {"retarget": 0, "gate": 0}
            if membrane:
                for side, u, ok, g0u, c0u in nd:                         # (1) Law 4: re-target, never withhold
                    if ok: continue
                    lst, D = (ps, ms) if side == "s" else (pd, md)
                    lack = s.lack_s() if side == "s" else s.lack_d()
                    cands = [int(c) for c in np.argsort(-lack) if int(c) not in lst][:3]; best = None
                    for c in cands:
                        l2 = [c if x == u else x for x in lst]; D2 = {(c if a == u else a): m for a, m in D.items()}
                        P = (l2, pd, D2, md) if side == "s" else (ps, l2, ms, D2)
                        gc, chc = proj(s, *P, base)   # need of c: its landing vs the same action without it (= without u)
                        if (gc > g0u + 1e-12 or any(x < y for x, y in zip(chc, c0u))) and (best is None or gc > best[0]): best = (gc, P)
                    if best: ps, pd, ms, md = best[1]; ev["retarget"] += 1
                g, ch = proj(s, ps, pd, ms, md, base)
                if any(a > b for a, b in zip(ch, s.bound)):              # (2) Law 0: protect, last
                    ds, dd = O.defaults(s); sc = []
                    for c in ((ps, pd, {i: "inside" for i in ps}, {j: "inside" for j in pd}), (ds, dd, {i: "inside" for i in ds}, {j: "inside" for j in dd})):
                        gg, cc = proj(s, *c, base); sc.append((max(a / max(b, 1e-9) for a, b in zip(cc, s.bound)), -gg, c))
                    sc.sort(key=lambda x: (x[0], x[1])); ps, pd, ms, md = sc[0][2]; ev["gate"] = 1
                _, _, nd = needs(s, ps, pd, ms, md, base)                # (3) need of the landings made
            s.ms, s.md = ms, md
            pre_dr, pre_dry = s.dr.copy(), s.res <= 0; nbd = (s.Ad & pre_dr[None, :]).sum(1)
            dmg = float(np.sum(np.minimum(1, s.h * (1 + pre_dry) + 0.02 * nbd) * (~pre_dr) * (s.immune <= 0)))
            base.tick(s, ps, pd, glob)
            TR[s._rid].append({"need": [x[2] for x in nd], "tried": tried, "nl": len(ps) + len(pd), **ev,
                               "dry": (s.res <= 0).tolist(), "dr": s.dr.tolist(), "pdr": pre_dr.tolist(), "pdry": pre_dry.tolist(),
                               "nbd": nbd.tolist(), "dmg": dmg, "maxdry": float(s.maxdry), "maxd": float(s.maxd),
                               "resmax": float(s.res.max()), "bound": [float(x) for x in s.bound]})
    return Rec

def run_arm(arm, v, sd, p, k=1.0):
    W = recorder(k, membrane=(arm == "v3m"))
    if arm in ("v3", "v3m"):
        r = run_st3(W, sd, p, dict(Z.unkey(ORG6[v]), cs=1, vote=0, mem=0, joint=0)); return {"G": r["G"], "ch": r["ch"], "trace": L.take()}
    return L.run_arm(arm, v, sd, p, W)

def collect(part):
    for v in range(1, NV + 1):
        if v % 2 != part: continue
        p = G.params(G.SH["shades"][v - 1]["node"], v)
        out = {sd: {a: run_arm(a, v, sd, p) for a in ARMS} for sd in SEEDS}
        json.dump(out, open(f"diag/l3trace_v{v}.json", "w")); print("collect", v, flush=True)

def sweep(part):
    out = {}
    for v in range(1, NV + 1):
        if v % 2 != part: continue
        p = G.params(G.SH["shades"][v - 1]["node"], v); out[v] = {}
        for sd in SEEDS:
            for k in KS:
                for a in ("v3m", "report+popular"):
                    r = run_arm(a, v, sd, p, k)
                    out[v][f"{sd}|{k}|{a}"] = {"G": r["G"], "dmg": float(np.mean([t["dmg"] for t in r["trace"]]))}
        print("sweep", v, flush=True); json.dump(out, open(f"diag/l3sweep_p{part}.json", "w"))

def le3(F):
    N, Tt = F.shape[1], F.shape[0]; res = {}; inscope = False; ok = True
    for name, est, chk in (("odd->even", np.arange(1, N, 2), np.arange(0, N, 2)), ("even->odd", np.arange(0, N, 2), np.arange(1, N, 2))):
        Fe, Fc = F[:, est], F[:, chk]; eo, lo = Fe.mean(), L.onset_rate(Fe); tau = 1 / lo if lo > 0 else np.inf; d = {}
        for T in (2, 4, 8):
            if T > tau / 2: continue
            pr = eo + (T - 1) * lo; m = L.span(Fc, T); n = len(chk) * (Tt // T); tol = 2 * np.sqrt(max(pr * (1 - pr), 1e-12) / n) + 0.01
            d[T] = {"pred": float(pr), "meas": m, "tol": float(tol), "ok": bool(abs(m - pr) <= tol)}
        res[name] = d; inscope |= bool(d); ok &= all(x["ok"] for x in d.values())
    return res, (bool(ok) if inscope else None)

def analyze():
    ex = json.load(open("diag/exact.json")); rng = np.random.default_rng(6423); S = {}; cells = []; L3r = []; L5 = []; sw = {}
    for f in glob.glob("diag/l3sweep_p*.json"): sw.update({int(a): b for a, b in json.load(open(f)).items()})
    DD = {v: {int(a): b for a, b in json.load(open(f"diag/l3trace_v{v}.json")).items()} for v in range(1, NV + 1)}
    over = {a: [0, 0] for a in ARMS}
    for v in range(1, NV + 1):
        D = DD[v]
        for sd in SEEDS:
            viol, Gs = [], []
            for a in ARMS:
                tr = D[sd][a]["trace"]; s = {}; bd = tr[0]["bound"]
                l0t = sum((t["maxdry"] > bd[0]) + (t["maxd"] > bd[1]) for t in tr); bo = sum(t["nl"] > 4 for t in tr)
                over[a][0] += bo; over[a][1] += bo > 0
                lands = sum(len(t["need"]) for t in tr); off = sum((not x) for t in tr for x in t["need"])
                s.update(L0_ticks=l0t, budget_over=bo, L4_precision=1 - off / max(1, lands),
                         tried_precision=1 - sum((not x) for t in tr for x in t["tried"]) / max(1, sum(len(t["tried"]) for t in tr)),
                         retarget=sum(t["retarget"] for t in tr), gate=sum(t["gate"] for t in tr))
                if a == "v3m":
                    s["L0"] = bool(l0t == 0 and bo == 0 and all(t["resmax"] <= 3.0 + 1e-9 for t in tr))
                    s["L4"] = bool(lands == 0 or s["L4_precision"] >= 0.90)
                viol.append(l0t + bo + off); Gs.append(D[sd][a]["G"])
                for ch, kk in (("sup", "dry"), ("dri", "dr")):
                    F = L.mat(tr, kk); c = L.law_channel(F, F, rng)
                    if c["scope"]:
                        c["LE_detail"], c["LE"] = le3(F)
                    s[ch] = c
                S[f"{v}|{sd}|{a}"] = s
            gi = {a: Gs[i] for i, a in enumerate(ARMS)}
            cells.append({"v": v, "sd": sd, "rho": L.spearman(viol, Gs), "viol": viol, "G": Gs,
                          "rc_cost": bool(gi["v3m"] >= gi["v3"] - 0.01),
                          "rc_margin": bool(gi["v3m"] > max(gi[a] for a in ("report+popular", "round+round", "random+random", "B")))})
        fit = L2.l5_counts([DD[u][sd]["v3m"]["trace"] for u in DD if u != v for sd in SEEDS])
        test = L2.l5_counts([D[sd]["v3m"]["trace"] for sd in SEEDS]); ceR, ce0 = L2.l5_ce(fit, test)
        L5.append({"v": v, "ceR": ceR, "ce0": ce0, "ok": bool(ceR < ce0)})
        for sd in SEEDS:
            g = {a: [sw[v][f"{sd}|{k}|{a}"]["G"] for k in KS] for a in ("v3m", "report+popular")}; dm = [sw[v][f"{sd}|{k}|v3m"]["dmg"] for k in KS]
            keep = all(g["v3m"][i] >= g["v3m"][0] - 0.03 for i in range(len(KS)) if dm[i] <= 2)
            drop = g["v3m"][0] - g["v3m"][-1]; steps = [g["v3m"][i] - g["v3m"][i + 1] for i in range(len(KS) - 1)]
            grad = drop <= 0.02 or max(steps) <= 0.6 * drop; dn = g["report+popular"][0] - g["report+popular"][-1]
            L3r.append({"v": v, "sd": sd, "G": g["v3m"], "G_nat": g["report+popular"], "dmg": dm, "keep": bool(keep),
                        "gradual": bool(grad), "drop": drop, "drop_nat": dn, "ok": bool(keep and grad and drop <= dn)})
    rate = lambda vals: (sum(x for x in vals if x is not None), sum(1 for x in vals if x is not None))
    R = {"EXACT": (sum(x["ok"] for x in ex.values()), len(ex)), "budget_over_ticks_traces": over}
    R["L0"] = rate([s.get("L0") for s in S.values()]); R["L4"] = rate([s.get("L4") for s in S.values()])
    R["L0_channel_traces_by_arm"] = {a: sum(S[f"{v}|{sd}|{a}"]["L0_ticks"] > 0 for v in range(1, NV + 1) for sd in SEEDS) for a in ARMS}
    R["tried_precision_median"] = {a: float(np.median([S[f"{v}|{sd}|{a}"]["tried_precision"] for v in range(1, NV + 1) for sd in SEEDS])) for a in ARMS}
    R["v3m_made_precision_median"] = float(np.median([S[f"{v}|{sd}|v3m"]["L4_precision"] for v in range(1, NV + 1) for sd in SEEDS]))
    R["v3m_retarget_gate_total"] = [sum(S[f"{v}|{sd}|v3m"]["retarget"] for v in range(1, NV + 1) for sd in SEEDS),
                                    sum(S[f"{v}|{sd}|v3m"]["gate"] for v in range(1, NV + 1) for sd in SEEDS)]
    for q in ("L1p", "L1", "L2", "LE", "C2"):
        R[q] = rate([s[ch].get(q) for s in S.values() for ch in ("sup", "dri") if s[ch]["scope"]])
    R["L3"] = (sum(x["ok"] for x in L3r), len(L3r)); R["L3_parts"] = {q: sum(x[q] for x in L3r) for q in ("keep", "gradual")}
    R["L3_parts"]["drop<=nat"] = sum(x["drop"] <= x["drop_nat"] for x in L3r); R["L5"] = (sum(x["ok"] for x in L5), len(L5))
    rh = [c["rho"] for c in cells if c["rho"] is not None]
    R["PR"] = {"neg_cells": sum(r < 0 for r in rh), "cells": len(rh), "mean_rho": float(np.mean(rh))}
    R["RC"] = {"cost": sum(c["rc_cost"] for c in cells), "margin": sum(c["rc_margin"] for c in cells), "cells": len(cells)}
    rows = [{"L0": s.get("L0"), "L4": s.get("L4"), **({q: s[ch].get(q) for q in ("L1p", "L1", "L2", "LE")} if s[ch]["scope"] else {})}
            for s in S.values() for ch in ("sup", "dri")]
    conf = []
    for A, B in itertools.permutations(["L0", "L4", "L1p", "L1", "L2", "LE"], 2):
        both = [r for r in rows if r.get(A) is not None and r.get(B) is not None]; ah = [r for r in both if r[A]]
        if len(both) < 10 or not ah: continue
        pf, pfa = np.mean([not r[B] for r in both]), np.mean([not r[B] for r in ah])
        conf.append({"A": A, "B": B, "n": len(both), "P_B_fail": float(pf), "P_B_fail_given_A": float(pfa), "conflict": bool(pfa > pf + 0.10)})
    R["C1_conflicts"] = sum(c["conflict"] for c in conf); R["C1_pairs"] = len(conf)
    ok = lambda t: t[1] > 0 and t[0] / t[1] >= 0.90
    R["PASS"] = {"EXACT": R["EXACT"][0] == R["EXACT"][1], **{q: ok(R[q]) for q in ("L0", "L1p", "L1", "L2", "LE", "L4", "L5", "L3", "C2")},
                 "C1": R["C1_conflicts"] == 0, "PR": R["PR"]["neg_cells"] >= 2 * R["PR"]["cells"] / 3 and R["PR"]["mean_rho"] < 0,
                 "RC": R["RC"]["cost"] >= 0.9 * len(cells) and R["RC"]["margin"] >= 0.9 * len(cells)}
    R["ROW_PASS"] = all(R["PASS"].values())
    json.dump({"summary": R, "per_trace": S, "cells": cells, "L3": L3r, "L5": L5, "C1": conf}, open("diag/QUICK_LAWS3.json", "w"), default=float)
    print(json.dumps(R, indent=1, default=float))

if __name__ == "__main__":
    c = sys.argv[1]
    if c == "collect": collect(int(sys.argv[2]))
    elif c == "sweep": sweep(int(sys.argv[2]))
    else: analyze()
