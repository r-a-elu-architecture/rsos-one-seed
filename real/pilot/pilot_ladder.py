"""PILOT1 (development cells only; never used for confirmation). The ladder, one arm per process:
  default   the row's standard
  rollout   plain rollout (Bertsekas): present + host branches, standard continuation
  v1        seed3v1 with the host's own levers (library P1-P8 bound, frame levers, native operator branches)
  full      seed3 (v2: all seed operators) with the host's own levers PLUS the sealed CONF3 composed programs, and the
            trace (spheres and tubes, TRANSPLANT, COMPRESS shapes, INHERIT, blind-plan pool) PERSISTENT over the arm's
            own cells in cell order (no other arm shares it: one process per arm)
Usage: python real/pilot/pilot_ladder.py <row> <model-or-> <arm> <first> <last>  -> real/pilot/out/<row>_<arm>_<c0>_<c1>.json"""
import os, sys, json, time, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "real"), os.path.join(ROOT, "real", "hosts")]
row, model, arm, c0, c1 = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
assert c1 <= 8, "pilot: development cells 1-8 only"
import seed, seed3, seed3_ops

def make():
    if row == "space": from space import Space; return Space("pq")
    if row == "ai_ai": from ai_ai import AiAi; return AiAi(model)
    from ai_agents import AIAgents; return AIAgents(spec=model, standard="selfcons")

def VIEW(st):
    if row == "ai_ai":
        mine = {k: v for k, v in st["val"].items() if st["owner"][k] == "A"}
        recv = {k: st["val"][k] for k in st["sent"]["B"]}
        return {"question": st["question"], "x": st["x"], "t": st["t"], "mine": mine, "received": recv,
                "sent_A": list(st["sent"]["A"]), "unsent": [k for k in st["order"] if st["owner"][k] == "A" and k not in st["sent"]["A"]]}
    if row == "space": return {"t": st["t"], "passes": list(st["passes"]), "queue": [dict(it) for it in st["queue"]]}
    keep = ("id", "temp", "answer", "calls", "tok", "errors", "restarts")
    return {"ti": st["ti"], "calls": st["calls"], "tok": st["tok"], "br": [{k: b[k] for k in keep if k in b} for b in st["br"]]}

def plus_composed(h):
    spec = importlib.util.spec_from_file_location("gen_moves", os.path.join(ROOT, "real", "composed", f"{row}_moves.py"))
    g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g); f0 = h.frame
    def frame(st):
        out = list(f0(st))
        for op, fn in g.MOVES.items():
            try: a = fn(VIEW(st))
            except Exception: a = None
            if a is not None: out.append((f"C:{op}", f"C:{op}", a))
        return out
    h.frame = frame; return h

def clear():
    seed3.POOL.clear(); seed3.OFF.clear(); seed3.POLICY_FALLBACK[0] = 0
    for p in (seed3_ops.OPOOL, seed3_ops.SHAPES, seed3_ops.INH): p.clear()
    if row == "ai_agents":
        import ai_agents_blind as B; B.PLAN_POOL.clear(); B.EXEC.clear(); B.TRACE.clear()

if row == "ai_agents":
    import ai_agents  # sets the task path first
    import ai_agents_blind as B
    _calc = B.calc
    def calc(e):
        try: return _calc(e)
        except SyntaxError as err: raise B.PlanError(f"calc: expression does not parse ({err.msg})")
    B.calc = calc

out = {"row": row, "arm": arm, "model": model, "cells": {}}
clear()
for c in range(c0, c1 + 1):
    if arm != "full": clear()                      # every other arm starts each cell empty; full keeps its own trace
    t = time.time()
    if arm == "default": o = seed.run(make(), c, "default")
    elif arm == "rollout": o = seed.run(make(), c, "rollout")
    elif arm == "v1": o = seed3.run(make(), c, "seed3v1")
    else: o = seed3.run(plus_composed(make()), c, "seed3")
    r = {k: o[k] for k in ("result", "resource", "choices", "ops_passed_membrane", "vote_vetoed") if k in o}
    r["sec"] = round(time.time() - t, 1); out["cells"][c] = r
    print(row, arm, c, round(o["result"], 4), round(o["resource"], 1), r["sec"], flush=True)
os.makedirs(os.path.join(ROOT, "real", "pilot", "out"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "real", "pilot", "out", f"{row}_{arm}_{c0}_{c1}.json"), "w"), default=str, indent=1)
