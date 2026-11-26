"""STRUCT1 sealed unit (25 Nov 2026; real/PREREG_STRUCT1.md): does the general RSOS STRUCTURE carry without the
host-written levers? One row (and model), one pair of fresh cells (301..308), five arms per cell, all existing modes:
  default    the row's standard method                          seed.run(h, c, "default")
  rollout    plain rollout (Bertsekas): present + host branches   seed.run(h, c, "rollout")
  seed3v1    the full sealed REAL3 seed                            seed3.run(h, c, "seed3v1")
  structure  the same seed3v1 with every host-written lever OFF:   seed3.run(h_off, c, "seed3v1"), where h_off is a fresh
             host whose primitives(s) and frame(s) return [] (a flag on the instance; real/seed3.py is not edited)
  strongest  the row's strongest method where it has one           seed.run(strong, c, "default")
Leak fix (paper rev. 2, §4): before EVERY arm the seed trace (seed3.POOL, OFF) and the AI-agent plan stores
(ai_agents_blind.PLAN_POOL, EXEC, TRACE) are cleared, and every cell runs in a fresh process (maxtasksperchild=1).
The REAL3 FIX1 calc wrapper (an unparsable model-written formula is a plan error) is applied as in cloud/real3_unit_fix1.py.
Usage: python cloud/struct1_unit.py <row> <model-or-> <pair 0..3>. Writes real/outs1/<row>_<model>_p<pair>.json"""
import os, sys, json, time, hashlib, multiprocessing as mp
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for line in open(os.path.join(ROOT, "real", "SEAL_STRUCT1.txt")):
    if not line.strip() or line.startswith("#"): continue
    h, f = line.split()
    if hashlib.sha256(open(os.path.join(ROOT, f), "rb").read()).hexdigest() != h: sys.exit(f"HASH MISMATCH {f}: stop")
sys.path[:0] = [os.path.join(ROOT, "real"), os.path.join(ROOT, "real", "hosts")]
row, model, p = sys.argv[1], sys.argv[2], int(sys.argv[3])
assert row in ("ai_agents", "ai_human", "ai_ai", "economics", "space") and 0 <= p <= 3
cells = [301 + 2 * p, 302 + 2 * p]
if os.environ.get("STRUCT1_SMOKE") == "1": cells = [1]   # pre-seal crash check on a development cell only

def hosts():
    """name -> (factory for a fresh standard host, host whose default is the strongest method, or None)"""
    if row == "economics": from economics import Economics; return {"std": (lambda: Economics(), Economics(standard="strongest"))}
    if row == "space": from space import Space; return {"std": (lambda: Space("pq"), Space("strongest"))}
    if row == "ai_ai": from ai_ai import AiAi; return {"std": (lambda: AiAi(model), None)}
    if row == "ai_human": from ai_human import AIHuman; return {"std": (lambda: AIHuman(spec=model), None)}
    from ai_agents import AIAgents
    strong = AIAgents(spec=model, standard="strongest")
    return {"react": (lambda: AIAgents(spec=model, standard="react"), strong),
            "selfcons": (lambda: AIAgents(spec=model, standard="selfcons"), strong)}

def clear():
    import seed3
    seed3.POOL.clear(); seed3.OFF.clear(); seed3.POLICY_FALLBACK[0] = 0
    if row == "ai_agents":
        import ai_agents_blind as B
        B.PLAN_POOL.clear(); B.EXEC.clear(); B.TRACE.clear()

def levers_off(h):
    h.primitives = lambda s: []; h.frame = lambda s: []      # the flag: no host-written lever reaches the seed
    return h

KEEP = ("result", "resource", "R", "choices", "failed_calls", "policy_fallback_steps")
def one(args):
    name, c = args
    import seed, seed3
    if row == "ai_agents":   # REAL3 FIX1 calc wrapper (PREREG_REAL3_FIX1.md)
        import ai_agents_blind as B
        if not getattr(B.calc, "_fix1", False):
            _calc = B.calc
            def calc(e):
                try: return _calc(e)
                except SyntaxError as err: raise B.PlanError(f"calc: expression does not parse ({err.msg})")
            calc._fix1 = True; B.calc = calc
    make, strong = hosts()[name]; r = {}; t0 = time.time()
    for arm in ("default", "rollout", "seed3v1", "structure", "strongest"):
        if arm == "strongest" and strong is None: continue
        clear(); ta = time.time()
        if arm in ("default", "rollout"): o = seed.run(make(), c, arm)
        elif arm == "seed3v1": o = seed3.run(make(), c, "seed3v1")
        elif arm == "structure": o = seed3.run(levers_off(make()), c, "seed3v1")
        else: o = seed.run(strong, c, "default")
        r[arm] = {q: o[q] for q in KEEP if q in o}; r[arm]["sec"] = round(time.time() - ta, 1)
    r["sec"] = round(time.time() - t0)
    return f"{name}|{c}", r

if __name__ == "__main__":
    jobs = [(name, c) for name in hosts() for c in cells]
    out = {"row": row, "model": model, "pair": p, "cells": {}}
    with mp.get_context("spawn").Pool(2, maxtasksperchild=1) as pool:
        for key, r in pool.imap(one, jobs):
            out["cells"][key] = r; print(key, json.dumps(r, default=str)[:300], flush=True)
    safe = model.replace("/", "_").replace(":", "_").replace(",", "+")
    os.makedirs(os.path.join(ROOT, "real", "outs1"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "real", "outs1", f"{row}_{safe}_p{p}.json"), "w"), default=str, indent=1)
