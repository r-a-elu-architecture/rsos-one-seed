"""BIRTHS v2 (Level D, 'the seed grows itself'), built from diag/DIAG_BIRTHS.md. Development only until sealed.
Diagnosis: in ORG5/FINAL 40 of 58 'births' were a parent's structure picked again (selection, not generation), the child
never grew in its own host, and counter-shift did not exist yet.
Births v2 (biology's order: genome by recombination, then development in the child's own environment):
  genome     child = union of both parents' roles (det adapt guard barrier) + the organism v2 roles (cs, mem, joint);
             a parent's genome = its own roles + the same organism v2 roles
  growth     development in the host it lives in: start with the whole genome expressed; one pass over the genome in a
             fixed order, each role is switched off (or on) if that raises G on ONE growth seed of the host (never the
             evaluation seeds). Same procedure for child and parents.
  host       child host = the ORG5 child host (mean of both parents' parameters, union of modes)
Arms in the child host, per bridge (v, v+1) and evaluation seed:
  parA, parB   each parent's selected structure (ORG6 picks) + cs, transplanted unchanged (the ORG5 'parents')
  gA, gB       each parent grown in the child host from its own genome (fair control: same growth step)
  child        the child grown from the union genome
Hypotheses (for the sealed run): D1 child > max(parA, parB); D2 child > max(gA, gB) (inheritance from both parents adds
beyond each parent's own growth). Sign tests over bridges x seeds, ties excluded.
Usage: python births2.py <growth seed> <eval seeds a-b> <out.json> [bridges, e.g. 1,3,5]"""
import sys, os, json, hashlib
import numpy as np
from multiprocessing import Pool
os.chdir(os.path.dirname(os.path.abspath(__file__)))
assert hashlib.sha256(open("org6.py", "rb").read()).hexdigest() in open("SEAL_ORG6.txt").read()
import org6 as P6, org7 as X
G, unkey, ROLES = X.G, X.Z.unkey, X.Z.ROLES
EXTRA = ["cs", "mem", "joint"]
T = P6.tables(); PICK = {v: P6.picks_for(T, v)["own"] for v in T}

def full(expr):  # expressed roles -> run_st2 structure
    st = {r: int(r in expr) for r in ROLES + EXTRA}; st.update(cs_th=2, vote=0); return st

def child_host(a):
    pa, pb = G.params(G.SH["shades"][a - 1]["node"], a), G.params(G.SH["shades"][a]["node"], a + 1)
    return {"d": round((pa["d"] + pb["d"]) / 2), "hz": (pa["hz"] + pb["hz"]) / 2, "cz": (pa["cz"] + pb["cz"]) / 2,
            "modes": sorted(set(pa["modes"]) | set(pb["modes"]))}

def grow(genome, p, gseed):
    expr = set(genome); g = X.run_st2(G.Shade, gseed, p, full(expr))["G"]
    for r in [r for r in ROLES + EXTRA if r in genome]:
        trial = expr ^ {r}; gt = X.run_st2(G.Shade, gseed, p, full(trial))["G"]
        if gt > g + 1e-9: expr, g = trial, gt
    return sorted(expr)

def bridge(args):
    a, gseed, evs = args; b = a + 1; p = child_host(a)
    A = {r for r, x in unkey(PICK[a]).items() if x}; B = {r for r, x in unkey(PICK[b]).items() if x}
    arms = {"parA": sorted(A | {"cs"}), "parB": sorted(B | {"cs"}),
            "gA": grow(A | set(EXTRA), p, gseed), "gB": grow(B | set(EXTRA), p, gseed), "child": grow(A | B | set(EXTRA), p, gseed)}
    rows = []
    for sd in evs:
        cache = {}; res = {}
        for k, e in arms.items():
            t = tuple(e)
            if t not in cache: cache[t] = X.run_st2(G.Shade, sd, p, full(set(e)))["G"]
            res[k] = cache[t]
        rows.append({"bridge": f"v{a}|v{b}", "seed": sd, **res})
    print("bridge", a, {k: "".join(x[0] for x in v) for k, v in arms.items()}, flush=True)
    return {"bridge": a, "arms": arms, "rows": rows}

if __name__ == "__main__":
    gseed = int(sys.argv[1]); lo, hi = map(int, sys.argv[2].split("-")); out = sys.argv[3]
    brs = [int(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 else list(range(1, P6.NV))
    with Pool(int(os.environ.get("WORKERS", os.cpu_count()))) as pool:
        res = pool.map(bridge, [(a, gseed, list(range(lo, hi + 1))) for a in brs])
    json.dump(res, open(out, "w"), indent=1)
    from scipy.stats import binomtest
    R = [r for x in res for r in x["rows"]]
    for name, bar in [("D1 child > max(parA,parB)", lambda r: max(r["parA"], r["parB"])), ("D2 child > max(gA,gB)", lambda r: max(r["gA"], r["gB"]))]:
        w = sum(r["child"] > bar(r) + 1e-12 for r in R); l = sum(r["child"] < bar(r) - 1e-12 for r in R)
        print(name, f"wins {w} losses {l} ties {len(R) - w - l}", "p", round(binomtest(w, w + l, .5, alternative="greater").pvalue, 4) if w + l else "-")
    print("mean child - max(parA,parB):", round(float(np.mean([r["child"] - max(r["parA"], r["parB"]) for r in R])), 4))
