"""ORG8 = ORG7 re-check with the budget-correct counter-shift (laws3.run_st3), SEAL1 (24 Nov 2026). Was: ORG7 confirmatory run: organism v2 = ORG6 structures + the counter-shift role (P1, cs, threshold 2) for every arm.
Rules: PREREG_ORG7.md, sealed in SEAL_ORG7.txt. Structures are ORG6's picks (selected on ORG6 selection seeds
9460-9461, untouched here); cs is universal (one rule, no per-shade choice). Fresh seeds: evaluation 9490-9501 (12),
worlds 9960, random structures 9890+.
Usage: python org7run.py <part 0..3>   (four parts; resumable, one file per shade)"""
import sys, os, json, glob, hashlib
import numpy as np
os.chdir(os.path.dirname(os.path.abspath(__file__)))
assert hashlib.sha256(open("org6.py", "rb").read()).hexdigest() in open("SEAL_ORG6.txt").read(), "org6.py changed"
import org6 as P6, org7 as X
G, O, F4, unkey, size, key, STRUCTS = X.G, X.O, X.F4, X.Z.unkey, X.Z.size, X.Z.key, X.Z.STRUCTS
EV, RW = list(range(5300, 5312)), 5320
import sys as _s; _s.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'laws')); import laws3 as L3
CS = {"cs": 1, "cs_th": 2, "vote": 0, "mem": 0, "joint": 0}
os.chdir(os.path.dirname(os.path.abspath(__file__))); os.makedirs("org8", exist_ok=True)

def st(c): return dict(unkey(c), **CS)

def eval_shade(k, T):
    v = k + 1; f = f"org8/eval_{v}.json"
    if os.path.exists(f): return
    p = G.params(G.SH["shades"][k]["node"], v); P = P6.picks_for(T, v); allk = [key(s) for s in STRUCTS]; out = []
    for i, sd in enumerate(EV):
        rng = np.random.default_rng(530000 + 100 * v + i)
        rn = rng.choice([c for c in allk if size(c) == size(P["nb"])]); ro = rng.choice([c for c in allk if size(c) == size(P["own"])])
        arms = {"own": P["own"], "nb": P["nb"], "glob": P["glob"], "rnd_nb": str(rn), "rnd_own": str(ro)}; res, cache = {}, {}
        for a, c in arms.items():
            if c not in cache: cache[c] = L3.run_st3(G.Shade, sd, p, st(c))
            res[a] = cache[c]
        nat = {f"{a}+{b}": F4.run(G.Shade, sd, p, (a, b)) for a, b in O.NATS}
        out.append({"shade": v, "node": G.SH["shades"][k]["node"], "seed": sd, "structs": arms, **res, "nat": nat,
                    "B": F4.run(G.Shade, sd, p, "B"), "all": F4.run(G.Shade, sd, p, "all")})
    wo = {wn: {"nb": L3.run_st3(F4.WORLDS[wn], RW, p, st(P["nb"]))["G"],
               "nat": {f"{a}+{b}": F4.run(F4.WORLDS[wn], RW, p, (a, b))["G"] for a, b in O.NATS}} for wn in ("WB", "WC")}
    out.append({"shade": v, "worlds": wo}); json.dump(out, open(f, "w")); print("eval", v, P, flush=True)

if __name__ == "__main__":
    part = int(sys.argv[1]); T = P6.tables(); assert len(T) == P6.NV
    for k in [k for k in range(P6.NV) if k % 4 == part]: eval_shade(k, T)
