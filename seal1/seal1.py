"""SEAL1 runner: the combined sealed run (PREREG_SEAL1.md; hashes in SEAL_SEAL1.txt). Layer 2. Owner's laptop.
Usage: python seal1.py <window 0..3>   (four PowerShell windows; resumable: a finished unit is skipped)
       python seal1.py analyze         (after all four windows are done)
Each unit writes into seal1/out/<unit>/ ; nothing in the development folders is touched."""
import sys, os, json, glob, shutil, hashlib, importlib, time
ROOT = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(ROOT); OUT = os.environ.get("SEAL1_OUT") or os.path.join(ROOT, "out")   # SEAL1_OUT: pipeline smoke only
for line in open(os.path.join(ROOT, "SEAL_SEAL1.txt")):
    if "  " in line and not line.startswith("#"):
        h, f = line.strip().split("  ", 1)
        assert hashlib.sha256(open(os.path.join(REPO, f), "rb").read()).hexdigest() == h, f"changed after the seal: {f}"
sys.path[:0] = [os.path.join(REPO, "experiments", d) for d in ("laws", "beam", "allnodes")]
SHADES = list(range(1, 22)); LAW_SEED = 5340; VERIFY = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21]
BEAM_SEEDS = [5350, 5351]; BEAM_CH = 536000; PAIR_SEED = 5375; PAIRS = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
# estimated laptop minutes per unit (for balancing the four windows)
UNITS = ([("verify", v, 100) for v in VERIFY] + [("laws_collect", v, 35) for v in SHADES] + [("laws_local", v, 20) for v in SHADES]
         + [("partners", v, 40) for v in PAIRS] + [("org8", v, 10) for v in SHADES] + [("beam", k, 30) for k in (0, 1)])

def plan():
    win = [[] for _ in range(4)]; load = [0] * 4
    for u in sorted(UNITS, key=lambda x: -x[2]): i = load.index(min(load)); win[i].append(u); load[i] += u[2]
    return win, load

def unit_dir(kind, v):
    d = os.path.join(OUT, f"{kind}_{v}"); os.makedirs(os.path.join(d, "diag"), exist_ok=True); return d

def done(kind, v): return os.path.exists(os.path.join(OUT, f"{kind}_{v}", "DONE"))

def run_unit(kind, v):
    d = unit_dir(kind, v)
    if kind in ("laws_collect", "laws_local", "verify"):
        import laws6 as M; import laws as L
        L.HERE = d; os.chdir(d); M.SEEDS = [LAW_SEED]; M.SHADES = [v]
        if kind == "laws_collect": M.collect(0)
        elif kind == "laws_local": M.local(0)
        else:
            import lawneed as LN
            orig = LN.future
            def full(w, act, p, st, mode, plan=None, record=False):   # the noise-free full fork (K.5 1): no open-loop replay
                return orig(w, act, p, st, "crn" if mode == "open" else mode, None, record)
            LN.future = full; M.ARMS = ["v5m"]; M.collect(0); LN.future = orig
    elif kind == "partners":
        import partners5 as P; os.chdir(d); P.SEEDS = [PAIR_SEED]; P.PAIRS = [v]; P.run(0)
    elif kind == "org8":
        os.chdir(os.path.join(REPO, "experiments", "allnodes")); import org8run as R, org6 as P6
        R.eval_shade(v - 1, P6.tables())
    elif kind == "beam":
        import beam6 as B6, numpy as np; os.chdir(d); B1, B2, B4 = B6.B1, B6.B2, B6.B4; out = []
        for vv in [x for x in SHADES if x % 2 == v]:
            for sd in BEAM_SEEDS:
                p, rec, parts, lparts, exact, lex = B2.prep(vv, sd); T = B1.T
                kb = [B4.k_beam(parts, u) for u in range(1, T + 1)]; kl = [B4.k_lock(lparts, u) for u in range(1, T + 1)]
                bb = [len(parts[u - 1]) + 16 for u in range(1, T + 1)]; bl = [8 * (len(lparts[u - 1]) + 2) for u in range(1, T + 1)]
                for ci, car in enumerate(B1.CARRIERS):
                    for mi, m in enumerate(B1.MS):
                        cs = BEAM_CH + 1000 * ci + 100 * mi + 10 * vv + BEAM_SEEDS.index(sd)
                        fwd = list(B1.loss_process(car, m, np.random.default_rng(cs), 29)); back = B2.back_process(car, m, np.random.default_rng(cs + 3))
                        row = {"v": vv, "sd": sd, "carrier": car, "m": m}
                        for b in B6.BUDGETS:
                            row[str(b)] = {"beam": B6.sim_k10(bb, kb, b, fwd, back, np.random.default_rng(cs + 7), B1.UNDET),
                                           "lockstep": B6.sim_k10(bl, kl, b, fwd, back, np.random.default_rng(cs + 7), B1.UNDET),
                                           "whole": B4.sim_whole(parts, b, fwd, back, np.random.default_rng(cs + 7), B1.UNDET)}
                        out.append(row)
                zf = [np.zeros(29, bool)] * T; zb = [False] * T
                out.append({"v": vv, "sd": sd, "carrier": "none", "exact": bool(exact), "beam_sync": B6.sim_k10(bb, kb, 29, zf, zb, np.random.default_rng(1), 0.0)["sync"]})
                print("beam", vv, sd, flush=True)
        json.dump(out, open(os.path.join(d, "diag", f"beam6_p{v}.json"), "w"))
    open(os.path.join(d, "DONE"), "w").write(time.strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    if sys.argv[1] == "analyze":
        import analyze_seal1; analyze_seal1.main()
    else:
        w = int(sys.argv[1]); win, load = plan(); print("window", w, "units", len(win[w]), "estimated minutes", load[w], flush=True)
        for kind, v, _ in win[w]:
            if done(kind, v): print("skip", kind, v, flush=True); continue
            t0 = time.time(); print("start", kind, v, time.strftime("%H:%M"), flush=True); run_unit(kind, v)
            print("done", kind, v, round((time.time() - t0) / 60, 1), "min", flush=True)
        print("WINDOW", w, "FINISHED", flush=True)
