"""CONF5 sealed unit (25 Nov 2026; real/PREREG_CONF5.md): the structure identified by PILOT1 vs plain rollout, fresh cells.
Arms per cell: default (the standard), rollout (plain rollout, Bertsekas), and the row's identified RSOS structure:
  ai_agents (self-consistency): "full" = seed3 v2 (all seed operators) + the host's own levers + the CONF3 composed
             programs, with the trace (seed3.POOL/OFF, seed3_ops OPOOL/SHAPES/INH, blind-plan pools) PERSISTENT over this
             job's own cells in cell order, for this arm only (restored from its own snapshot before each of its cells)
  ai_ai, space: "v1" = seed3v1 with the host's own levers (membrane, landing, library P1-P8, native operator branches)
Every other arm-cell starts with empty pools. Usage: python cloud/conf5_unit.py <row> <model-or-> <first> <last>
-> real/outc5/<row>_<model>_<first>_<last>.json   Seal: real/SEAL_CONF5.txt."""
import os, sys, json, time, copy, hashlib, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for line in open(os.path.join(ROOT, "real", "SEAL_CONF5.txt")):
    if not line.strip() or line.startswith("#"): continue
    h, f = line.split()
    if hashlib.sha256(open(os.path.join(ROOT, f), "rb").read()).hexdigest() != h: sys.exit(f"HASH MISMATCH {f}: stop")
sys.path[:0] = [os.path.join(ROOT, "real"), os.path.join(ROOT, "real", "hosts")]
row, model, c0, c1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
assert {"ai_agents": 1001 <= c0 and c1 <= 1048, "ai_ai": 1201 <= c0 and c1 <= 1300, "space": 1001 <= c0 and c1 <= 1020}[row]
cells = [1] if os.environ.get("CONF5_SMOKE") == "1" else list(range(c0, c1 + 1))   # smoke: pre-seal crash check, dev cell
import seed, seed3, seed3_ops
if row == "ai_agents":
    import ai_agents                      # sets the task path first
    import ai_agents_blind as B
    _calc = B.calc
    def calc(e):
        try: return _calc(e)
        except SyntaxError as err: raise B.PlanError(f"calc: expression does not parse ({err.msg})")
    B.calc = calc
RSOS = "full" if row == "ai_agents" else "v1"

def make():
    if row == "space": from space import Space; return Space("pq")
    if row == "ai_ai": from ai_ai import AiAi; return AiAi(model)
    from ai_agents import AIAgents; return AIAgents(spec=model, standard="selfcons")

def VIEW(st):
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

def pools():
    p = [seed3.POOL, seed3.OFF, seed3_ops.OPOOL, seed3_ops.SHAPES, seed3_ops.INH]
    if row == "ai_agents": p += [B.PLAN_POOL, B.EXEC, B.TRACE]
    return p

def clear():
    for p in pools(): p.clear()
    seed3.POLICY_FALLBACK[0] = 0

def restore(snap):
    clear()
    for p, s in zip(pools(), snap): p.update(copy.deepcopy(s))

KEEP = ("result", "resource", "choices", "ops_passed_membrane", "vote_vetoed", "failed_calls")
out = {"row": row, "model": model, "rsos_arm": RSOS, "cells_run": cells, "cells": {}}
snap = None
for c in cells:
    r = {}
    for arm in ("default", "rollout", RSOS):
        t = time.time()
        if arm == "full": restore(snap) if snap is not None else clear()
        else: clear()
        if arm == "default": o = seed.run(make(), c, "default")
        elif arm == "rollout": o = seed.run(make(), c, "rollout")
        elif arm == "v1": o = seed3.run(make(), c, "seed3v1")
        else:
            o = seed3.run(plus_composed(make()), c, "seed3"); snap = [copy.deepcopy(p) for p in pools()]
        r[arm] = {k: o[k] for k in KEEP if k in o}; r[arm]["sec"] = round(time.time() - t, 1)
    out["cells"][str(c)] = r
    print(row, c, {a: (round(v["result"], 4), round(v["resource"], 1), v["sec"]) for a, v in r.items()}, flush=True)
safe = model.replace("/", "_").replace(":", "_").replace(",", "+")
os.makedirs(os.path.join(ROOT, "real", "outc5"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "real", "outc5", f"{row}_{safe}_{c0}_{c1}.json"), "w"), default=str, indent=1)
