"""LAWS5: row 1 short test of map K.8 (completed) + K.16 (owner 24 Nov 00:29: short test here, adjust, until the table
is filled; then one long run). Layer 2. Development. Written 24 Nov 2026 ~00:45 (UTC+02:00 Helsinki, Kyiv, Riga, Sofia,
Tallinn, Vilnius), before any run. Earlier checks are not changed; LAWS5 places the structures the map names:

  COMMON RANDOMNESS (K.5 3; K.16 simulation statistics: common random numbers): the world's generator is restored after
      every decision, so decisions never change the world's events; projections and bound start from the same state.
  L4 + RC (K.8; K.2; K.5 1): arm v5m = v3 inside the membrane: need of each landing by the CHEAP REPLAY (one closed-loop
      own-policy future with common randomness records the plan; each branch replays it); no need -> re-target to the
      highest-lack unit of its side if needed there; else withhold, unless the withheld action's replayed future is
      worse (then kept); then the Law 0 gate, last (defaults projection vs the unhealed bound, common randomness).
      L4 holds iff precision over landings made >= 0.90 (need re-measured on the final action by the same replay).
      RC: G(v5m) >= G(v3) - 0.01 and G(v5m) > max(natives, beam-only) in >= 90 % of cells.
  LE (K.8 + K.16 reliability: renewal, clumped failures): the law in its exact per-element form on a fresh replay of the
      same element: fail_i(T) = eps_i + (1 - eps_i) (1 - (1 - h_i)^(T - 1)), h_i = onsets / up-ticks of element i
      (replay 1); pooled prediction mean_i fail_i(T) checked on replay 2 at T in {2, 4, 8} (no domain restriction now:
      the exact form covers several onsets); tolerance 2 sqrt(p(1-p)/n) + 0.01, n = units x floor(ticks/T).
  L5 (K.8 + K.16 information theory: side information): host whose relations carry information = the coupled pair of
      road 10 (a partner's drift doubles the hazard of the same unit): read the drift state of unit j of world A from
      (A's supply unit j dry, B's unit j drifted, A's drifted neighbours 0..3+) vs the marginal; organisms v3 in both
      worlds (no tubes); tables fit on the other pairs, cross-entropy on this pair. Inv: CE_R < CE_0.
  L3 (K.8 + K.16 resilience: repair at the damaged site): arm v3r = v3 whose drift landings go first to units that
      drifted in the last tick (the damaged site), the rest as v3 chose; damage sweep hazard x {1, 1.5, 2, 3, 4};
      (a) keep, (b) gradual, (c) drop(v3r) <= drop(native) as LAWS4.
  L0, L1', L1, L2, C2, C1, PR as LAWS4, on the collect traces.
SHORT TEST: shades 1, 4, 7, 10, 13, 16, 19 x development seeds 6630, 6631 (14 cells; pairs for L5: (v, v+1) for the
same shades, seed 6630). Criteria as LAWS4 (>= 90 % of in-scope etc.). Seeds never used elsewhere; never for colours.
Smoke test before the run: 6-tick worlds, throwaway seed 6499, shade 4, not kept.
Usage: python laws5.py collect <part 0|1> ; python laws5.py local <part 0|1> ; python laws5.py analyze"""
import sys, os, json, glob, gzip, copy, itertools
import numpy as np
import laws as L, laws2 as L2, laws3 as L3, laws4 as L4, lawneed as LN
G, O, V3, X, Z, F4 = L.G, L.O, L.V3, L.X, L.Z, L.F4
SEEDS = [6630, 6631]; SHADES = [1, 4, 7, 10, 13, 16, 19]; KS = L.KS; TR = L.TR; NV = L.NV
ARMS = ["v3", "v5m", "report+popular", "round+round", "random+random", "B"]
worse = L4.worse

def recorder5(p, st, membrane):
    class Rec(G.Shade):
        def __init__(s, seed, pp, default):
            super().__init__(seed, pp, default); s._r = copy.deepcopy(s.rng)
            r = copy.deepcopy(s); O.to_end(r); s.bound = r.channels()
            s._rid = id(s); TR[s._rid] = []; TR["last"] = s._rid
        def tick(s, ps, pd, glob=False):
            if id(s) != getattr(s, "_rid", None): return G.Shade.tick(s, ps, pd, glob)
            R = s._r; restore = lambda: setattr(s, "rng", copy.deepcopy(R)); restore()      # common randomness
            act = (list(ps), list(pd), dict(s.ms), dict(s.md)); ev = dict(withheld=0, retarget=0, refused=0, gate=0); made = None
            if membrane:
                g, ch, plan = LN.future(s, act, p, st, "crn", record=True); restore()
                fin_s, fin_d = list(act[0]), list(act[1]); ms, md = dict(act[2]), dict(act[3]); known = {}
                for side, lst in (("s", act[0]), ("d", act[1])):
                    for u in lst:
                        g0, c0, _ = LN.future(s, LN.without(act, side, u), p, st, "open", plan=plan); restore()
                        if worse(g0, c0, g, ch): known[(side, u)] = True; continue
                        cur = fin_s if side == "s" else fin_d; lack = s.lack_s() if side == "s" else s.lack_d()
                        c = next((int(x) for x in np.argsort(-lack) if int(x) not in cur), None)
                        if c is not None:
                            l2 = [c if x == u else x for x in cur]; D = ms if side == "s" else md; D2 = {(c if a == u else a): m for a, m in D.items()}
                            P = (l2, fin_d, D2, md) if side == "s" else (fin_s, l2, ms, D2)
                            gc, cc, _ = LN.future(s, P, p, st, "open", plan=plan); restore()
                            if worse(g0, c0, gc, cc):
                                if side == "s": fin_s, ms = l2, D2
                                else: fin_d, md = l2, D2
                                ev["retarget"] += 1; known[(side, c)] = True; continue
                        cur.remove(u); ev["withheld"] += 1
                if ev["withheld"]:
                    gw, cw, _ = LN.future(s, (fin_s, fin_d, ms, md), p, st, "open", plan=plan); restore()
                    if worse(gw, cw, g, ch): ev["refused"] = ev["withheld"]; ev["withheld"] = 0; ev["retarget"] = 0; fin_s, fin_d, ms, md = act[0], act[1], act[2], act[3]; known = {}
                restore(); gp, cp = L2.proj(s, fin_s, fin_d, ms, md, G.Shade)
                if any(a > b for a, b in zip(cp, s.bound)):
                    ds, dd = O.defaults(s); restore(); sc = []
                    for c in ((fin_s, fin_d, {i: "inside" for i in fin_s}, {j: "inside" for j in fin_d}), (ds, dd, {i: "inside" for i in ds}, {j: "inside" for j in dd})):
                        restore(); gg, cc = L2.proj(s, *c, G.Shade); sc.append((max(a / max(b, 1e-9) for a, b in zip(cc, s.bound)), -gg, c))
                    sc.sort(key=lambda x: (x[0], x[1])); fin_s, fin_d, ms, md = sc[0][2]; ev["gate"] = 1
                restore(); fa = (fin_s, fin_d, ms, md); gf, cf, plan2 = LN.future(s, fa, p, st, "crn", record=True); restore(); made = []
                for side, lst in (("s", fin_s), ("d", fin_d)):
                    for u in lst:
                        g0, c0, _ = LN.future(s, LN.without(fa, side, u), p, st, "open", plan=plan2); restore(); made.append(bool(worse(g0, c0, gf, cf)))
                ps, pd = fin_s, fin_d; s.ms, s.md = ms, md
            restore(); G.Shade.tick(s, ps, pd, glob); s._r = copy.deepcopy(s.rng)
            TR[s._rid].append({"need": made if made is not None else [], "nl": len(ps) + len(pd), **ev, "dry": (s.res <= 0).tolist(),
                               "dr": s.dr.tolist(), "maxdry": float(s.maxdry), "maxd": float(s.maxd), "resmax": float(s.res.max()),
                               "bound": [float(x) for x in s.bound]})
    return Rec

def run_v3r(W, sd, p, st):
    """v3 whose drift landings go first to the units that drifted in the last tick (repair at the damaged site)."""
    w = W(sd, p, "inside"); prev = w.dr.copy()
    while w.t < O.T:
        a = L4.step(w, p, st); ps, pd, ms, md = list(a[0]), list(a[1]), dict(a[2]), dict(a[3])
        new = [int(j) for j in np.where(w.dr & ~prev)[0] if int(j) not in pd]
        for j in new[:len(pd)]:
            old = pd.pop(); md.pop(old, None); pd.insert(0, j); md[j] = "inside"
        prev = w.dr.copy(); w.ms, w.md = ms, md; w.tick(ps, pd)
    return {"G": float(w.G()), "ch": [float(x) for x in w.channels()]}

def collect(part):
    for i, v in enumerate(SHADES):
        if i % 2 != part: continue
        p = G.params(G.SH["shades"][v - 1]["node"], v); st = L4.st_of(v); out = {}
        for sd in SEEDS:
            out[sd] = {}
            for a in ARMS:
                if a in ("v3", "v5m"):
                    W = recorder5(p, st, a == "v5m"); r = L3.run_st3(W, sd, p, st); out[sd][a] = {"G": r["G"], "ch": r["ch"], "trace": L.take()}
                else: out[sd][a] = L.run_arm(a, v, sd, p, recorder5(p, st, False))
            print("collect", v, sd, {a: round(out[sd][a]["G"], 4) for a in ARMS}, flush=True)
        with gzip.open(f"diag/l5trace_v{v}.json.gz", "wt") as fh: json.dump(out, fh)

def local(part):
    out = {"sweep": {}, "replay": {}, "pairs": {}}
    for i, v in enumerate(SHADES):
        if i % 2 != part: continue
        p = G.params(G.SH["shades"][v - 1]["node"], v); st = L4.st_of(v)
        for sd in SEEDS:
            for k in KS:
                W = L3.recorder(k)
                out["sweep"][f"{v}|{sd}|{k}|v3r"] = run_v3r(W, sd, p, st)["G"]; L.take()
                out["sweep"][f"{v}|{sd}|{k}|nat"] = L.run_arm("report+popular", v, sd, p, W)["G"]
            for rep in (1, 2):
                W = L4.replay_class(rep)
                for a in ("v3", "report+popular"):
                    if a == "v3": L3.run_st3(W, sd, p, st); tr = L.take()
                    else: tr = L.run_arm(a, v, sd, p, W)["trace"]
                    out["replay"][f"{v}|{sd}|{rep}|{a}"] = {"dry": [t["dry"] for t in tr], "dr": [t["dr"] for t in tr]}
        import partners3 as P3; os.chdir(L.HERE)   # the coupled pair host (road 10); organisms v3, no tubes
        P2 = P3.P2; S = P2.Sys(2, v, SEEDS[0]); sts = [L4.st_of(u) for u in S.vs]; rows = []
        while S.t < O.T:
            acts = []
            for k in (0, 1):
                r = copy.deepcopy(S.w[k].rng); acts.append(L4.step(P3.View(S, k, False), S.p[k], sts[k])); S.w[k].rng = r
            S.tick(acts)
            for k in (0, 1):
                A, B = S.w[k], S.w[1 - k]; nb = np.minimum((A.Ad & A.dr[None, :]).sum(1), 3)
                rows.append([(A.res <= 0).astype(int).tolist(), B.dr.astype(int).tolist(), nb.astype(int).tolist(), A.dr.astype(int).tolist()])
        out["pairs"][str(v)] = rows; print("local", v, flush=True)
        with gzip.open(f"diag/l5local_p{part}.json.gz", "wt") as fh: json.dump(out, fh)

def le5(F0, F1):
    eps = F0.mean(0); up = (~F0[:-1]).sum(0); on = (F0[1:] & ~F0[:-1]).sum(0); h = np.where(up > 0, on / np.maximum(up, 1), 0.0); d = {}
    for T in (2, 4, 8):
        pr = float(np.mean(eps + (1 - eps) * (1 - (1 - h) ** (T - 1)))); m = L.span(F1, T); n = F1.shape[1] * (F1.shape[0] // T)
        tol = 2 * np.sqrt(max(pr * (1 - pr), 1e-12) / n) + 0.01; d[T] = {"pred": pr, "meas": m, "tol": float(tol), "ok": bool(abs(m - pr) <= tol)}
    return d, all(x["ok"] for x in d.values())

def l5_counts(rows):
    c = np.ones((2, 2, 4, 2))
    for dry, bdr, nb, y in rows:
        np.add.at(c, (np.array(dry), np.array(bdr), np.array(nb), np.array(y)), 1)
    return c

def l5_ce(fit, test):
    pR = fit[..., 1] / fit.sum(-1); tot = fit.sum((0, 1, 2)); p0 = tot[1] / tot.sum(); t = test - 1; n = t.sum()
    ceR = -(t[..., 1] * np.log2(pR) + t[..., 0] * np.log2(1 - pR)).sum() / n
    ce0 = -(t[..., 1].sum() * np.log2(p0) + t[..., 0].sum() * np.log2(1 - p0)) / n
    return float(ceR), float(ce0)

def analyze():
    ex = json.load(open("diag/exact.json")); rng = np.random.default_rng(6633); S = {}; cells = []; loc = {"sweep": {}, "replay": {}, "pairs": {}}
    for f in glob.glob("diag/l5local_p*.json.gz"):
        with gzip.open(f, "rt") as fh: d = json.load(fh)
        for q in loc: loc[q].update(d[q])
    ev = {q: 0 for q in ("withheld", "retarget", "refused", "gate")}
    for v in SHADES:
        with gzip.open(f"diag/l5trace_v{v}.json.gz", "rt") as fh: D = {int(a): b for a, b in json.load(fh).items()}
        for sd in SEEDS:
            viol, Gs = [], []
            for a in ARMS:
                tr = D[sd][a]["trace"]; s = {}; bd = tr[0]["bound"]
                l0t = sum((t["maxdry"] > bd[0]) + (t["maxd"] > bd[1]) for t in tr); bo = sum(t["nl"] > 4 for t in tr)
                lands = sum(len(t["need"]) for t in tr); off = sum((not x) for t in tr for x in t["need"])
                if a == "v5m":
                    s["L0"] = bool(l0t == 0 and bo == 0); s["L4_precision"] = 1 - off / max(1, lands); s["L4"] = bool(lands == 0 or s["L4_precision"] >= 0.90)
                    for q in ev: ev[q] += sum(t[q] for t in tr)
                viol.append(l0t + bo + off); Gs.append(D[sd][a]["G"])
                for ch, kk in (("sup", "dry"), ("dri", "dr")): s[ch] = L.law_channel(L.mat(tr, kk), L.mat(tr, kk), rng)
                S[f"{v}|{sd}|{a}"] = s
            gi = dict(zip(ARMS, Gs))
            cells.append({"v": v, "sd": sd, "rho": L.spearman(viol, Gs), "G": Gs, "rc_cost": bool(gi["v5m"] >= gi["v3"] - 0.01),
                          "rc_margin": bool(gi["v5m"] > max(gi[a] for a in ("report+popular", "round+round", "random+random", "B")))})
    LE = []
    for v in SHADES:
        for sd in SEEDS:
            for a in ("v3", "report+popular"):
                r1, r2 = loc["replay"][f"{v}|{sd}|1|{a}"], loc["replay"][f"{v}|{sd}|2|{a}"]
                for ch in ("dry", "dr"):
                    F0, F1 = np.array(r1[ch], bool), np.array(r2[ch], bool)
                    if F0.mean() < 0.01 or F1.mean() < 0.01: continue
                    d, ok = le5(F0, F1); LE.append({"v": v, "sd": sd, "arm": a, "ch": ch, "detail": d, "ok": ok})
    L5r = []
    for v in SHADES:
        fit = l5_counts([x for u in SHADES if u != v for x in loc["pairs"][str(u)]]); test = l5_counts(loc["pairs"][str(v)])
        ceR, ce0 = l5_ce(fit, test); L5r.append({"v": v, "ceR": ceR, "ce0": ce0, "ok": bool(ceR < ce0)})
    L3r = []
    for v in SHADES:
        for sd in SEEDS:
            g = [loc["sweep"][f"{v}|{sd}|{k}|v3r"] for k in KS]; gn = [loc["sweep"][f"{v}|{sd}|{k}|nat"] for k in KS]
            drop = g[0] - g[-1]; steps = [g[i] - g[i + 1] for i in range(len(KS) - 1)]; dn = gn[0] - gn[-1]
            keep = g[1] >= g[0] - 0.03; grad = drop <= 0.02 or max(steps) <= 0.6 * drop
            L3r.append({"v": v, "sd": sd, "G": g, "G_nat": gn, "keep": bool(keep), "gradual": bool(grad), "drop": drop, "drop_nat": dn, "ok": bool(keep and grad and drop <= dn)})
    rate = lambda vals: (sum(x for x in vals if x is not None), sum(1 for x in vals if x is not None))
    R = {"EXACT": (sum(x["ok"] for x in ex.values()), len(ex)), "v5m_events": ev}
    R["L0"] = rate([s.get("L0") for s in S.values()]); R["L4"] = rate([s.get("L4") for s in S.values()])
    R["v5m_made_precision_median"] = float(np.median([S[f"{v}|{sd}|v5m"]["L4_precision"] for v in SHADES for sd in SEEDS]))
    for q in ("L1p", "L1", "L2", "C2"): R[q] = rate([s[ch].get(q) for s in S.values() for ch in ("sup", "dri") if s[ch]["scope"]])
    R["LE"] = (sum(x["ok"] for x in LE), len(LE)); R["L5"] = (sum(x["ok"] for x in L5r), len(L5r)); R["L3"] = (sum(x["ok"] for x in L3r), len(L3r))
    R["L3_parts"] = {q: sum(x[q] for x in L3r) for q in ("keep", "gradual")}; R["L3_parts"]["drop<=nat"] = sum(x["drop"] <= x["drop_nat"] for x in L3r)
    rh = [c["rho"] for c in cells if c["rho"] is not None]; R["PR"] = {"neg_cells": sum(r < 0 for r in rh), "cells": len(rh), "mean_rho": float(np.mean(rh))}
    R["RC"] = {"cost": sum(c["rc_cost"] for c in cells), "margin": sum(c["rc_margin"] for c in cells), "cells": len(cells)}
    rows = [{"L0": s.get("L0"), "L4": s.get("L4"), **({q: s[ch].get(q) for q in ("L1p", "L1", "L2")} if s[ch]["scope"] else {})} for s in S.values() for ch in ("sup", "dri")]
    conf = []
    for A, B in itertools.permutations(["L0", "L4", "L1p", "L1", "L2"], 2):
        both = [r for r in rows if r.get(A) is not None and r.get(B) is not None]; ah = [r for r in both if r[A]]
        if len(both) < 10 or not ah: continue
        pf, pfa = np.mean([not r[B] for r in both]), np.mean([not r[B] for r in ah]); conf.append(bool(pfa > pf + 0.10))
    R["C1_conflicts"] = sum(conf); ok = lambda t: t[1] > 0 and t[0] / t[1] >= 0.90
    R["PASS"] = {"EXACT": R["EXACT"][0] == R["EXACT"][1], **{q: ok(R[q]) for q in ("L0", "L1p", "L1", "L2", "LE", "L4", "L5", "L3", "C2")},
                 "C1": R["C1_conflicts"] == 0, "PR": R["PR"]["neg_cells"] >= 2 * R["PR"]["cells"] / 3 and R["PR"]["mean_rho"] < 0,
                 "RC": R["RC"]["cost"] >= 0.9 * len(cells) and R["RC"]["margin"] >= 0.9 * len(cells)}
    R["ROW_PASS"] = all(R["PASS"].values())
    json.dump({"summary": R, "cells": cells, "L3": L3r, "L5": L5r, "LE": LE}, open("diag/QUICK_LAWS5.json", "w"), default=float); print(json.dumps(R, indent=1, default=float))

if __name__ == "__main__":
    c = sys.argv[1]
    if c == "collect": collect(int(sys.argv[2]))
    elif c == "local": local(int(sys.argv[2]))
    else: analyze()
