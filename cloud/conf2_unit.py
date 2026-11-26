"""CONF2 sealed unit (25 Nov 2026; real/PREREG_CONF2.md): a copy of the CONF1 unit for AI-AI (cells 601-640) and the
satellite generated arm (cells 601-612); the generated moves see a filtered view of the state (VIEW below). Earlier text:
CONF1 sealed unit: confirmatory test of the full sealed REAL3 seed on fresh cells 501+. One row (and model), an explicit list of cells; arms per cell:
  default    the row's standard                       seed.run(h, c, "default")
  seed3v1    the full sealed REAL3 seed               seed3.run(h, c, "seed3v1")
  strongest  the row's strongest method, if any       seed.run(strong, c, "default")
  generated  (AI rows, seal B only) seed3v1 on a host whose primitives()/frame() are replaced by the moves in
             real/generated/<row>_moves.py, written by a fresh agent from the RSOS language sources only.
Leak fix as STRUCT1: seed trace and AI-agent plan stores cleared before every arm; one fresh process per cell.
Usage: python cloud/conf2_unit.py <row> <model-or-> <first cell> <last cell>   -> real/outc2/<row>_<model>_<first>_<last>.json
Seal: real/SEAL_CONF2.txt (everything CONF2 runs, incl. the generated moves and the frozen orbit file)."""
import os, sys, json, time, hashlib, importlib.util, multiprocessing as mp
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = True
for sealf in ["SEAL_CONF2.txt"]:
    for line in open(os.path.join(ROOT, "real", sealf)):
        if not line.strip() or line.startswith("#"): continue
        h, f = line.split()
        if hashlib.sha256(open(os.path.join(ROOT, f), "rb").read()).hexdigest() != h: sys.exit(f"HASH MISMATCH {f}: stop")
sys.path[:0] = [os.path.join(ROOT, "real"), os.path.join(ROOT, "real", "hosts")]
row, model, c0, c1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
assert row in ("ai_ai", "space") and 601 <= c0 <= c1
cells = list(range(c0, c1 + 1))
if os.environ.get("CONF2_SMOKE") == "1": cells = [1]   # pre-seal crash check on a development cell only

def hosts():
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

def VIEW(st):
    """What a generated move may see (fixed before the seal). AI-AI: A's own facts, what B sent, A's unsent facts; never
    B's values. Satellite: the pass schedule and the items on board; no random generators."""
    if row == "ai_ai":
        mine = {k: v for k, v in st["val"].items() if st["owner"][k] == "A"}
        recv = {k: st["val"][k] for k in st["sent"]["B"]}
        return {"question": st["question"], "x": st["x"], "t": st["t"], "mine": mine, "received": recv,
                "sent_A": list(st["sent"]["A"]), "unsent": [k for k in st["order"] if st["owner"][k] == "A" and k not in st["sent"]["A"]]}
    return {"t": st["t"], "passes": list(st["passes"]), "queue": [dict(it) for it in st["queue"]]}

def generated(h):
    """The generated moves replace the host's own levers (primitives and frame); native branches stay."""
    spec = importlib.util.spec_from_file_location("gen_moves", os.path.join(ROOT, "real", "generated", f"{row}_moves.py"))
    g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
    def frame(st):
        out = []
        for op, fn in g.MOVES.items():
            try: a = fn(VIEW(st))
            except Exception: a = None          # a move that fails on a state is simply not offered (counted)
            if a is not None: out.append((f"G:{op}", f"G:{op}", a))
        return out
    h.primitives = lambda s: []; h.frame = frame
    return h

KEEP = ("result", "resource", "R", "choices", "failed_calls", "policy_fallback_steps")
def one(args):
    name, c = args
    import seed, seed3
    if row == "ai_agents":   # REAL3 FIX1 calc wrapper
        import ai_agents_blind as B
        if not getattr(B.calc, "_fix1", False):
            _calc = B.calc
            def calc(e):
                try: return _calc(e)
                except SyntaxError as err: raise B.PlanError(f"calc: expression does not parse ({err.msg})")
            calc._fix1 = True; B.calc = calc
    make, strong = hosts()[name]; r = {}; t0 = time.time()
    arms = ("default", "seed3v1", "strongest", "generated") if row == "ai_ai" else ("default", "strongest", "generated")
    for arm in arms:
        if arm == "strongest" and strong is None: continue
        clear(); ta = time.time()
        if arm == "default": o = seed.run(make(), c, "default")
        elif arm == "seed3v1": o = seed3.run(make(), c, "seed3v1")
        elif arm == "generated": o = seed3.run(generated(make()), c, "seed3v1")
        else: o = seed.run(strong, c, "default")
        r[arm] = {q: o[q] for q in KEEP if q in o}; r[arm]["sec"] = round(time.time() - ta, 1)
    r["sec"] = round(time.time() - t0)
    return f"{name}|{c}", r

if __name__ == "__main__":
    jobs = [(name, c) for name in hosts() for c in cells]
    out = {"row": row, "model": model, "cells_run": cells, "generated": GEN, "cells": {}}
    with mp.get_context("spawn").Pool(2, maxtasksperchild=1) as pool:
        for key, r in pool.imap(one, jobs):
            out["cells"][key] = r; print(key, json.dumps(r, default=str)[:240], flush=True)
    safe = model.replace("/", "_").replace(":", "_").replace(",", "+")
    os.makedirs(os.path.join(ROOT, "real", "outc2"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "real", "outc2", f"{row}_{safe}_{c0}_{c1}.json"), "w"), default=str, indent=1)
