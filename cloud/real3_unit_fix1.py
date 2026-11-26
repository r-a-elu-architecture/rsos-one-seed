"""REAL3 sealed unit, FIX1 copy (only the seal file name differs; see real/PREREG_REAL3_FIX1.md). REAL3 sealed unit (25 Nov 2026): one row (and model), one pair of fresh cells, the REAL3 seed (real/seed3.py, mode
"seed3v1" = the composed seed REAL3 v1 with policy continuation, chosen by the rule in PREREG_REAL3.md) against the row's
standard ("default") and, where the row has one, its strongest method.
Usage: python cloud/real3_unit.py <row> <model-or-> <pair 0..3> <stage 1|2>. Writes real/out3/<row>_<model>_s<stage>_p<pair>.json
Cells (fixed in PREREG_REAL3.md): stage 1 = 201..208 (pair p: 201+2p, 202+2p); stage 2 = 209..216 (pair p: 209+2p,
210+2p); neuroscience: recording windows 5..12 (pair p: 5+2p, 6+2p), stage 1 only.
Each cell runs in its own process with an empty seed trace (POOL, OFF), so every cell is independent and can be re-run
alone with the same numbers. The two cells of a pair run in parallel (2 cores)."""
import os, sys, json, time, hashlib, multiprocessing as mp
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for line in open(os.path.join(ROOT, "real", "SEAL_REAL3_FIX1.txt")):
    if not line.strip() or line.startswith("#"): continue
    h, f = line.split()
    if hashlib.sha256(open(os.path.join(ROOT, f), "rb").read()).hexdigest() != h: sys.exit(f"HASH MISMATCH {f}: stop")
sys.path[:0] = [os.path.join(ROOT, "real"), os.path.join(ROOT, "real", "hosts")]
row, model, p, stage = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
assert 0 <= p <= 3 and stage in (1, 2) and not (row == "neuro" and stage == 2)
if row == "neuro": cells = [5 + 2 * p, 6 + 2 * p]
else: cells = [201 + 8 * (stage - 1) + 2 * p, 202 + 8 * (stage - 1) + 2 * p]
if os.environ.get("REAL3_SMOKE") == "1": cells = [1]   # pre-run check on a development cell only (never a fresh cell)

def hosts():
    """name -> (host for default and seed3v1, host whose default is the strongest method or None)"""
    if row == "quantum": from quantum import Quantum; return {"std": (Quantum(), None)}          # strongest = default
    if row == "energy": from energy import Energy; return {"std": (Energy(), Energy(standard="strongest"))}
    if row == "economics": from economics import Economics; return {"std": (Economics(), Economics(standard="strongest"))}
    if row == "space": from space import Space; return {"std": (Space("pq"), Space("strongest"))}
    if row == "robotics": from robotics import Robotics; return {"std": (Robotics(), None)}
    if row == "biology": from biology import Biology; return {"std": (Biology(), None)}
    if row == "neuro": from neuro import Neuro; return {"std": (Neuro(data="/tmp/neuro.npz"), None)}
    if row == "ai_ai": from ai_ai import AiAi; return {"std": (AiAi(model), None)}                  # strongest = default
    if row == "ai_human": from ai_human import AIHuman; return {"std": (AIHuman(spec=model), None)}  # strongest = default
    if row == "ai_agents":
        from ai_agents import AIAgents
        strong = AIAgents(spec=model, standard="strongest")
        return {"react": (AIAgents(spec=model, standard="react"), strong),
                "selfcons": (AIAgents(spec=model, standard="selfcons"), strong)}

KEEP = ("result", "resource", "R", "choices", "failed_calls", "policy_fallback_steps")
def one(args):
    name, c = args
    import seed, seed3
    if row == "ai_agents":   # FIX1 (PREREG_REAL3_FIX1.md): an unparsable model-written calc is a plan error, not a crash.
        import ai_agents, ai_agents_blind as B           # Applied here, so no sealed file is edited.
        if not getattr(B.calc, "_fix1", False):
            _calc = B.calc
            def calc(e):
                try: return _calc(e)
                except SyntaxError as err: raise B.PlanError(f"calc: expression does not parse ({err.msg})")
            calc._fix1 = True; B.calc = calc
    h, strong = hosts()[name]; r = {}; t0 = time.time()
    try:
        for m in ("default", "seed3v1"):
            seed3.POOL.clear(); seed3.OFF.clear(); seed3.POLICY_FALLBACK[0] = 0     # independent cell: empty trace
            o = seed.run(h, c, m) if m == "default" else seed3.run(h, c, m)
            r[m] = {q: o[q] for q in KEEP if q in o}
        if strong is not None:
            o = seed.run(strong, c, "default"); r["strongest"] = {q: o[q] for q in KEEP if q in o}
    except (IndexError, ValueError) as e:
        if row == "neuro": r = {"skip": f"beyond recording: {e}"}
        else: raise
    r["sec"] = round(time.time() - t0)
    return f"{name}|{c}", r

if __name__ == "__main__":
    jobs = [(name, c) for name in hosts() for c in cells]
    out = {"row": row, "model": model, "stage": stage, "pair": p, "cells": {}}
    with mp.get_context("spawn").Pool(2) as pool:
        for key, r in pool.imap(one, jobs):
            out["cells"][key] = r; print(key, json.dumps(r, default=str)[:300], flush=True)
    safe = model.replace("/", "_").replace(":", "_").replace(",", "+")
    os.makedirs(os.path.join(ROOT, "real", "out3"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "real", "out3", f"{row}_{safe}_s{stage}_p{p}.json"), "w"), default=str, indent=1)
