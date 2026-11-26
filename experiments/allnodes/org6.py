"""ORG6: heal without harm (sealed in SEAL_ORG6.txt; rules in PREREG_ORG6.md). Same organism, roles and arms as ORG5 /
ORG-FINAL (org5.run_st, unchanged and hash-checked); ONE change: how a shade chooses its structure.
ORG5/FINAL chose the structure with the highest whole G on the selection seeds, blind to the host's channels; 7 of the 16
non-green shades failed only m2 (worst channels worse than the native in > 2 of 12 runs), and 6 of those 7 had chosen
the guard off. ORG6 rule (the constitution's "do no harm", Law 0, applied to selection): a structure is ADMISSIBLE for a
shade only if on every selection seed none of its channels is worse than the native's (report+popular = all roles off);
the shade takes the admissible structure with the highest mean G. The native itself is always admissible.
The bridge (nb) takes the best structure admissible on BOTH neighbours; glob the best admissible on all other shades.
Fresh seeds: selection 9460-9461; evaluation 9470-9481 (12); new worlds 9950; random structures 9880+.
Usage: python org6.py select <part 0|1> ; python org6.py eval <part 0|1>   (resumable: one file per shade)"""
import sys, os, json, glob as gl, hashlib
import numpy as np
os.chdir(os.path.dirname(os.path.abspath(__file__)))
assert hashlib.sha256(open("org5.py", "rb").read()).hexdigest() in open("SEAL_ORG5.txt").read(), "org5.py changed"
import org5 as Z
G, O, F4, run_st, unkey, size, STRUCTS, key = Z.G, Z.O, Z.F4, Z.run_st, Z.unkey, Z.size, Z.STRUCTS, Z.key
NV = G.NV; SEL, EV, RW = [9460, 9461], list(range(9470, 9482)), 9950
NATIVE = "d0a0g0b0"
os.makedirs("org6", exist_ok=True)

def select_shade(k):
    f = f"org6/sel_{k + 1}.json"
    if os.path.exists(f): return
    p = G.params(G.SH["shades"][k]["node"], k + 1); out = {}
    for st in STRUCTS:
        rs = [run_st(G.Shade, s, p, st) for s in SEL]; out[key(st)] = {"G": [r["G"] for r in rs], "ch": [r["ch"] for r in rs]}
    json.dump(out, open(f, "w")); print("select", k + 1, flush=True)

def tables():
    return {int(f.split("_")[1].split(".")[0]): json.load(open(f)) for f in gl.glob("org6/sel_*.json")}

def admissible(T, v):
    nat = T[v][NATIVE]["ch"]
    return {c for c, r in T[v].items() if all(all(a <= b for a, b in zip(r["ch"][i], nat[i])) for i in range(len(SEL)))}

def best(T, vs):
    adm = set.intersection(*[admissible(T, v) for v in vs]) | {NATIVE}
    return max(sorted(adm), key=lambda c: (np.mean([np.mean(T[v][c]["G"]) for v in vs]), c))

def picks_for(T, v):
    nbs = [u for u in (v - 1, v + 1) if u in T]
    return {"own": best(T, [v]), "nb": best(T, nbs), "glob": best(T, [u for u in T if u != v])}

def eval_shade(k, T):
    v = k + 1; f = f"org6/eval_{v}.json"
    if os.path.exists(f): return
    p = G.params(G.SH["shades"][k]["node"], v); P = picks_for(T, v); allk = [key(s) for s in STRUCTS]; out = []
    for i, sd in enumerate(EV):
        rng = np.random.default_rng(9880 + 100 * v + i)
        rn = rng.choice([c for c in allk if size(c) == size(P["nb"])]); ro = rng.choice([c for c in allk if size(c) == size(P["own"])])
        arms = {"own": P["own"], "nb": P["nb"], "glob": P["glob"], "rnd_nb": str(rn), "rnd_own": str(ro)}; res, cache = {}, {}
        for a, c in arms.items():
            if c not in cache: cache[c] = run_st(G.Shade, sd, p, unkey(c))
            res[a] = cache[c]
        nat = {f"{a}+{b}": F4.run(G.Shade, sd, p, (a, b)) for a, b in O.NATS}
        out.append({"shade": v, "node": G.SH["shades"][k]["node"], "seed": sd, "structs": arms, **res, "nat": nat,
                    "B": F4.run(G.Shade, sd, p, "B"), "all": F4.run(G.Shade, sd, p, "all")})
    wo = {wn: {"nb": run_st(F4.WORLDS[wn], RW, p, unkey(P["nb"]))["G"],
               "nat": {f"{a}+{b}": F4.run(F4.WORLDS[wn], RW, p, (a, b))["G"] for a, b in O.NATS}} for wn in ("WB", "WC")}
    out.append({"shade": v, "worlds": wo}); json.dump(out, open(f, "w")); print("eval", v, P, flush=True)

if __name__ == "__main__":
    cmd, part = sys.argv[1], int(sys.argv[2]); ks = [k for k in range(NV) if k % 2 == part]
    if cmd == "select":
        for k in ks: select_shade(k)
    else:
        T = tables(); assert len(T) == NV, f"selection incomplete: {len(T)}/{NV}"
        for k in ks: eval_shade(k, T)
