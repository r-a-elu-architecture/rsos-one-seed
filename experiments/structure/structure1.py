"""STRUCTURE1 (owner 24 Nov 10:06-10:17): ONE structure placed once; every open layer-2 check read from it. Layer 2.
Development quick test, no colour. Written 24 Nov 2026 ~10:25 (UTC+02:00), pushed before the run.

STRUCTURE: the unit holds its branches - space (rooms / organs), lineage (parents), time (its own past t-1, t-2, present
t, own future plan t+1, t+2) - and ONE operator chooses among them: Law 4, the unit's own future (common randomness; one
closed-loop own-policy future records the plan, every branch is replayed open-loop on it, K.5 cheap replay). The same
structure at any level: here at the organism level (one choice per tick) and at the organ level (one choice per organ,
composed by deficit order), to compare levels.
SEED WORLD (owner 10:15: time is structure): T = 16 ticks, the shortest world that holds every time branch once (liver
burst 6, LE windows 2/4/8, living step 15, plan t+2). 16-tick worlds widen LE's tolerance (fewer windows): reported.
CHECKS read from the one structure, unchanged from where they were written:
  laws: LAWS6 analyze as is (L0, L1', L1, L2, C2, L4, L5, L3, LE, PR, RC, EXACT) with the organism = the structure;
        plus LE recombined (owner 10:12): pred = eps_i + (1-eps_i) [s_i q_i(landed) + (1-s_i) q_i(not landed)], q from
        replay 1 split by the organism's own landing on unit i, s_i = share of ticks the organism's own actions land on i in
        replay 2; same tolerance and windows as LE.
  Meaning M1: structure > best single room;  D B1: child (branches = both parents' trajectories) > best parent;
  E E1: structure > best native in the living host, E2 vs v3.  LEVEL: organ-level vs organism-level structure.
CELLS: laws shades 4, 10 x seed 6670 (LAWS6 dev seed); organs shades 4, 10 x seed 6720 (ORGANS dev seed).
Usage: python structure1.py laws | organs | report"""
import os, sys, copy, json, gzip, glob, time
T_SEED = int(os.environ.get("S1_T", "16")); os.environ["LAWS_SMOKE_T"] = str(T_SEED)   # 10:25: S1_T=30 run (seed must hold its past/future branches)
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "diag")
sys.path.insert(0, os.path.join(HERE, "..", "laws")); sys.path.insert(0, os.path.join(HERE, "..", "allnodes"))
import numpy as np
import laws as L, laws4 as L4, lawneed as LN
import partners3   # imported first: it changes directory on import
import laws6 as L6, organs as M
G, O = L.G, L.O
O.T = T_SEED
_chdir = os.chdir; _chdir(HERE); _sfx = "" if T_SEED == 16 else f"_T{T_SEED}"; os.chdir = lambda *a, **k: None   # every output stays in experiments/structure/diag
L6.SHADES = [4, 10]; L6.SEEDS = [6670]; M.SEEDS = [6720]

# ---------- the structure (laws world: G.Shade) ----------
def _crn_step(w, p, st):
    r = copy.deepcopy(w.rng); a = L4.step(w, p, st); w.rng = r; return (list(a[0]), list(a[1]), dict(a[2]), dict(a[3]))
def choose(w, opts, p, st):
    base = opts[0][1]; g, ch, plan = LN.future(w, base, p, st, "crn", record=True); best, bv = opts[0], (g, -sum(ch))
    for name, a in opts[1:]:
        g2, c2, _ = LN.future(w, a, p, st, "open", plan=plan)
        if (g2, -sum(c2)) > bv: best, bv = (name, a), (g2, -sum(c2))
    return best, plan
def run_struct(W, seed, p, st):
    w = W(seed, p, "inside"); past = []; plan = []; LOG.setdefault("chosen", {})
    while w.t < O.T:
        base = _crn_step(w, p, st); opts = [("t", base)] + [(f"t-{i}", past[-i]) for i in (1, 2) if len(past) >= i]
        _, plan = (None, plan)
        g, ch, plan = LN.future(w, base, p, st, "crn", record=True)
        opts += [(f"t+{i}", plan[i - 1]) for i in (1, 2) if len(plan) >= i]
        (name, a), _ = choose(w, opts, p, st); LOG["chosen"][name] = LOG["chosen"].get(name, 0) + 1
        past.append(base); LAND.append((list(a[0]), list(a[1]))); w.ms, w.md = dict(a[2]), dict(a[3]); w.tick(list(a[0]), list(a[1]))
    return {"G": float(w.G()), "ch": [float(x) for x in w.channels()], "flows": int(getattr(w, "flows", 0))}
LOG = {}; LAND = []
L6.L3.run_st3 = run_struct; L6.run_v3r = run_struct          # the organism everywhere in the laws checks = the structure

def le_recombined():
    rows = []
    for v in L6.SHADES:
        p = G.params(G.SH["shades"][v - 1]["node"], v); st = L4.st_of(v)
        for sd in L6.SEEDS:
            R = {}
            for rep in (1, 2):
                W = L4.replay_class(rep); LAND.clear(); run_struct(W, sd, p, st); tr = L.take(); R[rep] = (tr, list(LAND))
            for ch, side in (("dry", 0), ("dr", 1)):
                F0 = np.array([t[ch] for t in R[1][0]], bool); F1 = np.array([t[ch] for t in R[2][0]], bool)
                if F0.mean() < 0.01 or F1.mean() < 0.01: continue
                N = F0.shape[1]; A0 = np.zeros_like(F0); A1 = np.zeros_like(F1)
                for t, l in enumerate(R[1][1]): A0[t, l[side]] = True
                for t, l in enumerate(R[2][1]): A1[t, l[side]] = True
                eps = F0.mean(0); share = A1.mean(0); d = {}
                for T in (2, 4, 8):
                    q1, q0, qa = [], [], []
                    for i in range(N):
                        ups = [t for t in range(F0.shape[0] - T + 1) if not F0[t, i]]
                        nxt = lambda t: F0[t + 1:t + T, i].any()
                        a = [nxt(t) for t in ups]; qa.append(np.mean(a) if a else 0.0)
                        l1 = [nxt(t) for t in ups if A0[t, i]]; l0 = [nxt(t) for t in ups if not A0[t, i]]
                        q1.append(np.mean(l1) if l1 else qa[-1]); q0.append(np.mean(l0) if l0 else qa[-1])
                    q = share * np.array(q1) + (1 - share) * np.array(q0)
                    pr = float(np.mean(eps + (1 - eps) * q)); m = L.span(F1, T); n = N * (F1.shape[0] // T)
                    tol = 2 * np.sqrt(max(pr * (1 - pr), 1e-12) / n) + 0.01; d[T] = {"pred": pr, "meas": m, "tol": float(tol), "ok": bool(abs(m - pr) <= tol)}
                rows.append({"v": v, "sd": sd, "ch": ch, "detail": d, "ok": all(x["ok"] for x in d.values())})
    return rows

# ---------- the structure (organ host) ----------
import types
Q = types.ModuleType("Q"); _src = open(os.path.join(HERE, "..", "allnodes", "quick_l4choice.py")).read()
_h, _t = _src.split("v = int(sys.argv[1])"); exec(_h + "\n" + _t[_t.index("# v3"):], Q.__dict__)   # definitions only, no run
def organ_struct(W, sd, p, st, level="organism", rooms=True):
    w = W(sd, p, "inside"); past = []; chosen = {}
    while w.t < O.T:
        base = M.decide(w, p, st); plan = Q.own_plan(w, base, p, st)
        br = [("t", base)] + [(f"t-{i}", M.membrane(w, copy.deepcopy(past[-i]))) for i in (1, 2) if len(past) >= i]
        br += [(f"t+{i}", M.membrane(w, copy.deepcopy(plan[i - 1]))) for i in (1, 2) if len(plan) >= i]
        if rooms: br += [("room_" + k, M.room_action(w, p, st, k, None)) for k in M.NAMES]
        br += [("organ_" + k, M.membrane(w, M.focus(w, copy.deepcopy(base), k, 1, 1))) for k in M.NAMES]
        val = lambda a: Q.replay(w, a, plan)
        if level == "organism":
            name, a = max(br, key=lambda o: val(o[1]))
        else:   # organ level: each organ takes its landings from the branch best for it, composed by deficit order
            book = {}
            for k in M.NAMES:
                def v_k(a):
                    f = copy.deepcopy(w); f.ms, f.md = a[2], a[3]; f.tick(a[0], a[1])
                    for b in plan:
                        if f.t >= O.T: break
                        f.ms, f.md = b[2], b[3]; f.tick(b[0], b[1])
                    return M.organ_score(f)[k]
                book[k] = max(br, key=lambda o: v_k(o[1]))[0]
            acts = dict(br); a = Q.compose(w, {**{n: acts[n] for n in set(book.values())}, "A": base, "B": base}, book); name = "organs"
        chosen[name] = chosen.get(name, 0) + 1; past.append(base); w.ms, w.md = a[2], a[3]; w.tick(a[0], a[1])
    return float(w.G()), chosen

def run_laws():
    t0 = time.time(); L6.collect(0); L6.collect(1); L6.local(0); L6.local(1)
    for f in ("l6local_p0.json.gz", "l6local_p1.json.gz"): pass
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): L6.analyze()
    le = le_recombined()
    json.dump({"laws6": json.load(open("diag/QUICK_LAWS6.json"))["summary"], "LE_recombined": le, "chosen": LOG.get("chosen"), "sec": round(time.time() - t0)},
              open(f"diag/S1_laws{_sfx}.json", "w"), default=float, indent=1); print("laws done", round(time.time() - t0), flush=True)

def run_organs():
    t0 = time.time(); out = []
    for v in ([int(sys.argv[2])] if len(sys.argv) > 2 else (4, 10)):
        sd = 6720; p = M.G.params(M.G.SH["shades"][v - 1]["node"], v); st = L4.st_of(v); sB = L4.st_of(v + 1); pc = M.params_both(v)
        r = {"v": v}
        r["S_org"], r["S_org_rooms"] = organ_struct(M.Organs, sd, p, st, "organism")
        r["S_organ"], _ = organ_struct(M.Organs, sd, p, st, "organ")
        r["best_single"] = max(M.run_house(M.Organs, sd, p, st, "single", k)["G"] for k in M.NAMES)
        r["child"], r["child_src"] = Q.child_time(sd, pc, st, sB); r["best_parent"] = max(M.run_parent(M.Organs, sd, pc, s)["G"] for s in (st, sB))
        r["S_living"], _ = organ_struct(M.Living, sd, p, st, "organism", rooms=False); r["S_living_organ"], _ = organ_struct(M.Living, sd, p, st, "organ", rooms=False)
        r["v3_living"] = M.run_parent(M.Living, sd, p, st)["G"]
        r["best_native"] = max([M.F4.run(M.Living, sd, p, n)["G"] for n in O.NATS] + [M.F4.run(M.Living, sd, p, "B")["G"]])
        out.append(r); print(json.dumps(r), flush=True)
    json.dump({"cells": out, "sec": round(time.time() - t0)}, open(f"diag/S1_organs{_sfx}" + (f"_v{sys.argv[2]}" if len(sys.argv) > 2 else "") + ".json", "w"), indent=1)

if __name__ == "__main__":
    {"laws": run_laws, "organs": run_organs}[sys.argv[1]]()
