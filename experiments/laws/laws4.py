"""LAWS4: all RSOS laws as mathematics on twin traces, fourth and LAST development round for the laws row (owner,
23 Nov 2026 ~08:30: "if it does not pass, stop and report by cause, and we decide together"). Layer 2.
Written 23 Nov 2026 ~08:45 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius) after LAWS3 (diag/QUICK_LAWS3.md)
and the owner's Law 4 definition (map Part K.2), BEFORE any LAWS4 run. Earlier checks are not changed.

PART K LINE (unchanged): where = law set -> law of laws; missing = G-level invariants never checked as one set on O
traces; structure = every law as invariant + scope + check + response (F), axioms + model checking on per-tick traces
(I.6), MATH_V1/V2 as exact cases; check = each law holds on fresh traces in its scope, violations predict a lower
result, no two laws conflict.

WHAT CHANGES (everything else as laws3.py, imported):
  L4  OWNER'S DEFINITION (Part K.2). Own future = fork, then the organism's own policy (run_st3's step: picks,
      budget-correct counter-shift, beam, barrier, guard) to the end. Arm v4m = v3 inside membrane v4, in this order:
      (1) need: a landing is needed iff removing it makes the own future worse (lower G or a worse channel);
      (2) no need there: re-target to the highest-lack unit of its side not already picked, if that landing is
          needed in the own future (one candidate: cost; the full "anywhere" search was not affordable);
      (3) otherwise withhold, keep the budget; then the cost check: the withheld action's own future must not be
          worse than the full action's (G, channels); if it is, the landings are kept (counted: "withhold_refused");
      (4) Law 0 gate, last, as LAWS3 (defaults projection against the unhealed bound);
      (5) need of every landing made, in the own future: kept landings carry the need measured in (1) (full action),
          re-targeted ones the need measured in (2); a gated action is measured again.
      L4 holds on a trace iff precision over landings made >= 0.90. Scope v4m. Reported: withheld, re-targeted,
      withhold_refused, gated. (PR: other arms' need is the LAWS3 defaults-future need; for report+popular that
      is its own policy.)
  RC  G(v4m) >= G(v3) - 0.01 and G(v4m) > max(natives, beam-only), each >= 90 % of shade x seed (realised cost of
      the responses, measured on the real run, not the projection).
  L0  scope v4m; channels <= unhealed bound and budget <= 4 every tick and res <= 3.
  LE  same element on a fresh replay of the same world (layer 2: the world's structure seed kept, its dynamics
      stream replaced): eps_i, lambda_i of every unit from replay 0, prediction mean_i(eps_i + (T-1) lambda_i) checked
      on replay 1, T in {2,4,8} with T <= tau/2 (tau = 1/mean lambda); tolerance 2 * sqrt(p(1-p)/n) + 0.01,
      n = units x floor(ticks / T). Arms v3 and report+popular; both channels; scope eps >= 0.01.
  L5  reading a partly lost state (MATH_V1 §7): the drift state of a unit at a tick is read from what the reader
      knows. Without R: the marginal prevalence. With R: the link (its own supply unit dry) + drifted graph neighbours
      (0,1,2,3+). Fit on the other 20 shades (v3 replays), cross-entropy on this shade. Inv: CE_R < CE_0.
  L3  damage sweep on v3 (the budget-correct organism; the own-future membrane is not affordable in a 5-level
      sweep), contrast report+popular; (a) keep, (b) gradual, (c) drop <= native, as LAWS2/3.
QUICK TEST PASS: as LAWS3 (EXACT all; L0, L1p, L1, L2, LE, L4, L5 >= 90 % of in-scope; L3 >= 90 %; C1 no conflict;
C2 >= 90 %; PR >= 2/3 cells negative, mean < 0; RC both parts). L1p/L1/L2/C2 on the collect traces of all arms.
Development seeds: 6430, 6431 (new; never used elsewhere; never for colours). Replays: dynamics streams 1 and 2.
Before the run: own-future timing on throwaway seed 6499 (3 ticks, ~95 s/tick before need reuse); a pipeline smoke test
with 6-tick worlds (LAWS_SMOKE_T=6) on 6430/6431, deleted, not kept, numbers not used (6-tick worlds are not the test).
WHERE: collect (needs the own-future forks, ~22-30 min per v4m run) on the owner's laptop, 4 parts in parallel;
local (sweep, replays) and analyze here.
SCOPE CHANGE (owner, 23 Nov 2026 ~11:54, option 2; recorded ~11:58 BEFORE any LAWS4 result was read): the laptop
collect (v4m ~100 min per run, 4x the estimate) is stopped after the second shade of each window, so the collect-based
checks (L0, L4, L1p, L1, L2, C2, C1, PR, RC) run on shades 1-8 x 2 seeds = 16 cells; the criteria (percentages) are
unchanged. LE, L5 (replays) and L3 (sweep) keep all 21 shades (computed here, already pushed).
Usage: python laws4.py collect <part 0..3> ; python laws4.py local <part 0|1> ; python laws4.py analyze"""
import sys, os, json, glob, gzip, copy, itertools, time
import numpy as np
import laws as L, laws2 as L2, laws3 as L3
G, O, V3, X, Z, F4 = L.G, L.O, L.V3, L.X, L.Z, L.F4
SEEDS = [6430, 6431]; KS = L.KS; NV = L.NV; ORG6 = L.ORG6; TR = L.TR; proj = L2.proj
if os.environ.get("LAWS_SMOKE_T"): O.T = int(os.environ["LAWS_SMOKE_T"])   # pipeline smoke test only, never for results
COLLECT_SHADES = [1, 2, 3, 4, 5, 6, 7, 8]   # SCOPE (owner, 23 Nov 11:54, option 2), recorded before any LAWS4 result was read
ARMS = ["v2", "v3", "v4m", "own6", "report+popular", "round+round", "random+random", "B"]

def step(w, p, st):
    """one decision of run_st3 (laws3.py) from the current state: the organism's own policy."""
    bm = "above" if "above" in p["modes"] else ("pierced" if "pierced" in p["modes"] else None)
    ps, pd = V3.org3_picks(w) if st["det"] else O.defaults(w); ps, pd = list(ps), list(pd); n0 = len(ps) + len(pd)
    if st["cs"]:
        i = int(np.argmax(w.dry)); j = int(np.argmax(w.dur)); ci = cj = None
        if w.dry[i] >= 2 and i not in ps: ps = [i] + ps[:-1]; ci = i
        if w.dur[j] >= 2 and j not in pd: pd = [j] + pd[:-1]; cj = j
        while len(ps) + len(pd) > max(n0, 2 * O.KH):
            big = ps if len(ps) >= len(pd) else pd; keep = ci if big is ps else cj
            big.pop(max(k for k, u in enumerate(big) if u != keep))
    ms, md = {i: "inside" for i in ps}, {j: "inside" for j in pd}
    if st["adapt"]: ms, md = X.beam2(w, ps, pd, p["modes"], st, {})
    if st["barrier"] and bm:
        if ps: ms[ps[0]] = bm
        if pd: md[pd[0]] = bm
    if st["guard"]:
        ds, dd = O.defaults(w); m0, d0 = {i: "inside" for i in ds}, {j: "inside" for j in dd}
        if any(a > b for a, b in zip(F4.proj(w, ps, pd, ms, md)[1], F4.proj(w, ds, dd, m0, d0)[1])): ps, pd, ms, md = ds, dd, m0, d0
    return ps, pd, ms, md

def own_future(w, ps, pd, ms, md, p, st):
    f = copy.deepcopy(w); f.ms, f.md = dict(ms), dict(md); G.Shade.tick(f, ps, pd)
    while f.t < O.T:
        a, b, c, d = step(f, p, st); f.ms, f.md = c, d; G.Shade.tick(f, a, b)
    return f.G(), f.channels()

worse = lambda g1, c1, g0, c0: g1 < g0 - 1e-12 or any(x > y for x, y in zip(c1, c0))

def recorder4(p, st):
    class Rec(G.Shade):
        def __init__(s, seed, pp, default):
            super().__init__(seed, pp, default); r = copy.deepcopy(s); O.to_end(r); s.bound = r.channels()
            s._rid = id(s); TR[s._rid] = []; TR["last"] = s._rid
        def tick(s, ps, pd, glob=False):
            if id(s) != getattr(s, "_rid", None): return G.Shade.tick(s, ps, pd, glob)
            ps, pd = list(ps), list(pd); ms, md = dict(s.ms), dict(s.md); ev = dict(withheld=0, retarget=0, refused=0, gate=0)
            OF = lambda a, b, c, d: own_future(s, a, b, c, d, p, st)
            def need_list(a, b, c, d):
                g, ch = OF(a, b, c, d); out = []
                for side, lst in (("s", a), ("d", b)):
                    for u in lst:
                        a2 = [x for x in a if x != u] if side == "s" else a; b2 = [x for x in b if x != u] if side == "d" else b
                        g0, c0 = OF(a2, b2, c, d); out.append((side, u, bool(worse(g0, c0, g, ch)), g0, c0))
                return g, ch, out
            g, ch, nd = need_list(ps, pd, ms, md); fin_s, fin_d = list(ps), list(pd); known = {}
            for side, u, ok, g0, c0 in nd:
                if ok: known[(side, u)] = True; continue
                lst = fin_s if side == "s" else fin_d; lack = s.lack_s() if side == "s" else s.lack_d()
                c = next((int(x) for x in np.argsort(-lack) if int(x) not in lst), None)
                if c is not None:
                    l2 = [c if x == u else x for x in lst]; D = ms if side == "s" else md; D2 = {(c if a == u else a): m for a, m in D.items()}
                    P = (l2, fin_d, D2, md) if side == "s" else (fin_s, l2, ms, D2); gc, cc = OF(*P)
                    if worse(g0, c0, gc, cc):                     # without it (= without u) is worse: c is needed
                        if side == "s": fin_s, ms = l2, D2
                        else: fin_d, md = l2, D2
                        ev["retarget"] += 1; known[(side, c)] = True; continue
                lst.remove(u); ev["withheld"] += 1
            if ev["withheld"]:
                gw, cw = OF(fin_s, fin_d, ms, md)
                if worse(gw, cw, g, ch):                          # withholding would cost: keep the full action
                    ev["refused"] = ev["withheld"]; ev["withheld"] = 0; ev["retarget"] = 0
                    fin_s, fin_d, ms, md = list(ps), list(pd), dict(s.ms), dict(s.md)
            gp, cp = proj(s, fin_s, fin_d, ms, md, G.Shade)
            if any(a > b for a, b in zip(cp, s.bound)):          # Law 0, last
                ds, dd = O.defaults(s); sc = []
                for c in ((fin_s, fin_d, {i: "inside" for i in fin_s}, {j: "inside" for j in fin_d}), (ds, dd, {i: "inside" for i in ds}, {j: "inside" for j in dd})):
                    gg, cc = proj(s, *c, G.Shade); sc.append((max(a / max(b, 1e-9) for a, b in zip(cc, s.bound)), -gg, c))
                sc.sort(key=lambda x: (x[0], x[1])); fin_s, fin_d, ms, md = sc[0][2]; ev["gate"] = 1
            if ev["gate"]: _, _, nd2 = need_list(fin_s, fin_d, ms, md); made = [x[2] for x in nd2]   # gated: measured again
            else:                                             # kept landings: need measured above in the full action
                m0 = {(x[0], x[1]): x[2] for x in nd}; m0.update(known)
                made = [m0.get(("s", u), False) for u in fin_s] + [m0.get(("d", u), False) for u in fin_d]
            s.ms, s.md = ms, md
            G.Shade.tick(s, fin_s, fin_d, glob)
            TR[s._rid].append({"need": made, "tried": [x[2] for x in nd], "nl": len(fin_s) + len(fin_d), **ev,
                               "dry": (s.res <= 0).tolist(), "dr": s.dr.tolist(), "maxdry": float(s.maxdry), "maxd": float(s.maxd),
                               "resmax": float(s.res.max()), "bound": [float(x) for x in s.bound]})
    return Rec

def st_of(v): return dict(Z.unkey(ORG6[v]), cs=1, vote=0, mem=0, joint=0)

def collect(part):
    for v in range(1, NV + 1):
        if v % 4 != part: continue
        p = G.params(G.SH["shades"][v - 1]["node"], v); out = {}
        for sd in SEEDS:
            out[sd] = {}
            for a in ARMS:
                t0 = time.time()
                if a == "v4m": r = L3.run_st3(recorder4(p, st_of(v)), sd, p, st_of(v)); out[sd][a] = {"G": r["G"], "ch": r["ch"], "trace": L.take()}
                else: out[sd][a] = L3.run_arm(a, v, sd, p)
                print("collect", v, sd, a, round(time.time() - t0), "s", flush=True)
        with gzip.open(f"diag/l4trace_v{v}.json.gz", "wt") as fh: json.dump(out, fh)
        print("collect done", v, flush=True)

def replay_class(r):
    base = L3.recorder()
    class Rp(base):
        def __init__(s, seed, p, default):
            super().__init__(seed, p, default); s.rng = np.random.default_rng(seed + 1 + 1000 * r)
            rr = copy.deepcopy(s); rr._rid = None; O.to_end(rr); s.bound = rr.channels()
    return Rp

def local(part):
    out = {"sweep": {}, "replay": {}}
    for v in range(1, NV + 1):
        if v % 2 != part: continue
        p = G.params(G.SH["shades"][v - 1]["node"], v)
        for sd in SEEDS:
            for k in KS:
                W = L3.recorder(k)
                for a in ("v3", "report+popular"):
                    if a == "v3": r = L3.run_st3(W, sd, p, st_of(v)); tr = L.take()
                    else: r = L.run_arm(a, v, sd, p, W); tr = r["trace"]
                    out["sweep"][f"{v}|{sd}|{k}|{a}"] = {"G": r["G"], "dmg": float(np.mean([t["dmg"] for t in tr]))}
            for rep in (1, 2):
                W = replay_class(rep)
                for a in ("v3", "report+popular"):
                    if a == "v3": L3.run_st3(W, sd, p, st_of(v)); tr = L.take()
                    else: tr = L.run_arm(a, v, sd, p, W)["trace"]
                    out["replay"][f"{v}|{sd}|{rep}|{a}"] = {"dry": [t["dry"] for t in tr], "dr": [t["dr"] for t in tr], "nbd_end": None}
        print("local", v, flush=True)
        with gzip.open(f"diag/l4local_p{part}.json.gz", "wt") as fh: json.dump(out, fh)

def le4(F0, F1):
    eps_i, lam_i = F0.mean(0), (F0[1:] & ~F0[:-1]).mean(0); lo = lam_i.mean(); tau = 1 / lo if lo > 0 else np.inf; d = {}
    for T in (2, 4, 8):
        if T > tau / 2 or F1.shape[0] < 2 * T: continue
        pr = float(np.mean(np.minimum(1, eps_i + (T - 1) * lam_i))); m = L.span(F1, T); n = F1.shape[1] * (F1.shape[0] // T)
        tol = 2 * np.sqrt(max(pr * (1 - pr), 1e-12) / n) + 0.01; d[T] = {"pred": pr, "meas": m, "tol": float(tol), "ok": bool(abs(m - pr) <= tol)}
    return d, (all(x["ok"] for x in d.values()) if d else None)

def l5_counts(pairs, Ad_of):
    cnt = np.ones((2, 4, 2))
    for (dry, dr), Ad in pairs:
        dry, dr = np.array(dry, bool), np.array(dr, bool)
        for t in range(len(dr)):
            nb = np.minimum((Ad & dr[t][None, :]).sum(1), 3); np.add.at(cnt, (dry[t].astype(int), nb, dr[t].astype(int)), 1)
    return cnt

def analyze():
    ex = json.load(open("diag/exact.json")); rng = np.random.default_rng(6433); S = {}; cells = []
    loc = {"sweep": {}, "replay": {}}
    for f in glob.glob("diag/l4local_p*.json.gz"):
        with gzip.open(f, "rt") as fh: d = json.load(fh)
        loc["sweep"].update(d["sweep"]); loc["replay"].update(d["replay"])
    over = {a: [0, 0] for a in ARMS}; ev_tot = {q: 0 for q in ("withheld", "retarget", "refused", "gate")}
    for v in COLLECT_SHADES:
        with gzip.open(f"diag/l4trace_v{v}.json.gz", "rt") as fh: D = {int(a): b for a, b in json.load(fh).items()}
        for sd in SEEDS:
            viol, Gs = [], []
            for a in ARMS:
                tr = D[sd][a]["trace"]; s = {}; bd = tr[0]["bound"]
                l0t = sum((t["maxdry"] > bd[0]) + (t["maxd"] > bd[1]) for t in tr); bo = sum(t["nl"] > 4 for t in tr)
                over[a][0] += bo; over[a][1] += bo > 0
                lands = sum(len(t["need"]) for t in tr); off = sum((not x) for t in tr for x in t["need"])
                s.update(L0_ticks=l0t, budget_over=bo, L4_precision=1 - off / max(1, lands))
                if a == "v4m":
                    s["L0"] = bool(l0t == 0 and bo == 0 and all(t["resmax"] <= 3.0 + 1e-9 for t in tr))
                    s["L4"] = bool(lands == 0 or s["L4_precision"] >= 0.90)
                    for q in ev_tot: ev_tot[q] += sum(t[q] for t in tr)
                viol.append(l0t + bo + off); Gs.append(D[sd][a]["G"])
                for ch, kk in (("sup", "dry"), ("dri", "dr")):
                    s[ch] = L.law_channel(L.mat(tr, kk), L.mat(tr, kk), rng)
                S[f"{v}|{sd}|{a}"] = s
            gi = dict(zip(ARMS, Gs))
            cells.append({"v": v, "sd": sd, "rho": L.spearman(viol, Gs), "G": Gs, "rc_cost": bool(gi["v4m"] >= gi["v3"] - 0.01),
                          "rc_margin": bool(gi["v4m"] > max(gi[a] for a in ("report+popular", "round+round", "random+random", "B")))})
    LE = []
    for v in range(1, NV + 1):
        for sd in SEEDS:
            for a in ("v3", "report+popular"):
                r1, r2 = loc["replay"][f"{v}|{sd}|1|{a}"], loc["replay"][f"{v}|{sd}|2|{a}"]
                for ch in ("dry", "dr"):
                    F0, F1 = np.array(r1[ch], bool), np.array(r2[ch], bool)
                    if F0.mean() < 0.01 or F1.mean() < 0.01: continue
                    d, ok = le4(F0, F1)
                    if ok is not None: LE.append({"v": v, "sd": sd, "arm": a, "ch": ch, "detail": d, "ok": ok})
    Ad = {(v, sd): G.Shade(sd, G.params(G.SH["shades"][v - 1]["node"], v), "inside").Ad for v in range(1, NV + 1) for sd in SEEDS}
    pairs = {v: [((loc["replay"][f"{v}|{sd}|{r}|v3"]["dry"], loc["replay"][f"{v}|{sd}|{r}|v3"]["dr"]), Ad[(v, sd)]) for sd in SEEDS for r in (1, 2)] for v in range(1, NV + 1)}
    L5 = []
    for v in range(1, NV + 1):
        fit = l5_counts([x for u in pairs if u != v for x in pairs[u]], None); test = l5_counts(pairs[v], None)
        ceR, ce0 = L2.l5_ce(fit, test); L5.append({"v": v, "ceR": ceR, "ce0": ce0, "ok": bool(ceR < ce0)})
    L3r = []
    for v in range(1, NV + 1):
        for sd in SEEDS:
            g = {a: [loc["sweep"][f"{v}|{sd}|{k}|{a}"]["G"] for k in KS] for a in ("v3", "report+popular")}
            dm = [loc["sweep"][f"{v}|{sd}|{k}|v3"]["dmg"] for k in KS]
            keep = all(g["v3"][i] >= g["v3"][0] - 0.03 for i in range(len(KS)) if dm[i] <= 2)
            drop = g["v3"][0] - g["v3"][-1]; steps = [g["v3"][i] - g["v3"][i + 1] for i in range(len(KS) - 1)]
            grad = drop <= 0.02 or max(steps) <= 0.6 * drop; dn = g["report+popular"][0] - g["report+popular"][-1]
            L3r.append({"v": v, "sd": sd, "G": g["v3"], "G_nat": g["report+popular"], "dmg": dm, "keep": bool(keep),
                        "gradual": bool(grad), "drop": drop, "drop_nat": dn, "ok": bool(keep and grad and drop <= dn)})
    rate = lambda vals: (sum(x for x in vals if x is not None), sum(1 for x in vals if x is not None))
    R = {"EXACT": (sum(x["ok"] for x in ex.values()), len(ex)), "budget_over_ticks_traces": over, "v4m_events": ev_tot}
    R["L0"] = rate([s.get("L0") for s in S.values()]); R["L4"] = rate([s.get("L4") for s in S.values()])
    R["v4m_made_precision_median"] = float(np.median([S[f"{v}|{sd}|v4m"]["L4_precision"] for v in COLLECT_SHADES for sd in SEEDS]))
    for q in ("L1p", "L1", "L2", "C2"):
        R[q] = rate([s[ch].get(q) for s in S.values() for ch in ("sup", "dri") if s[ch]["scope"]])
    R["LE"] = (sum(x["ok"] for x in LE), len(LE)); R["L5"] = (sum(x["ok"] for x in L5), len(L5))
    R["L3"] = (sum(x["ok"] for x in L3r), len(L3r)); R["L3_parts"] = {q: sum(x[q] for x in L3r) for q in ("keep", "gradual")}
    R["L3_parts"]["drop<=nat"] = sum(x["drop"] <= x["drop_nat"] for x in L3r)
    rh = [c["rho"] for c in cells if c["rho"] is not None]
    R["PR"] = {"neg_cells": sum(r < 0 for r in rh), "cells": len(rh), "mean_rho": float(np.mean(rh))}
    R["RC"] = {"cost": sum(c["rc_cost"] for c in cells), "margin": sum(c["rc_margin"] for c in cells), "cells": len(cells)}
    rows = [{"L0": s.get("L0"), "L4": s.get("L4"), **({q: s[ch].get(q) for q in ("L1p", "L1", "L2")} if s[ch]["scope"] else {})}
            for s in S.values() for ch in ("sup", "dri")]
    conf = []
    for A, B in itertools.permutations(["L0", "L4", "L1p", "L1", "L2"], 2):
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
    json.dump({"summary": R, "per_trace": S, "cells": cells, "L3": L3r, "L5": L5, "LE": LE, "C1": conf}, open("diag/QUICK_LAWS4.json", "w"), default=float)
    print(json.dumps(R, indent=1, default=float))

if __name__ == "__main__":
    c = sys.argv[1]
    if c == "collect": collect(int(sys.argv[2]))
    elif c == "local": local(int(sys.argv[2]))
    else: analyze()
