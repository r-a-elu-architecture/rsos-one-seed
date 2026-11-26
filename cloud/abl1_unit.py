"""ABL1 sealed unit (25 Nov 2026; real/PREREG_ABL1.md): does each RSOS operator CAUSE the result it carries?
Arms per cell, all on the same sealed seed and the same sealed CONF3 composed programs (real/composed/<row>_moves.py):
  default   the row's standard
  full      seed3v1 whose levers are the composed RSOS programs (the CONF3 "composed" arm, unchanged)
  minus     full with ONE operator switched off (a filter on every candidate action; programs unchanged):
            ai_agents: Law 2 off  (no ("blind",b) / ("reuse",b) action from any source)
            ai_ai:     Law 5 off  (no hologram/packed message and no key; plain sentence messages only)
            space:     composition and Law 4 landing off (no composed programs, seed landing switched off all run)
Usage: python cloud/abl1_unit.py <row> <model-or-> <first cell> <last cell> -> real/outa1/...   Seal: real/SEAL_ABL1.txt."""
import os, sys, json, time, hashlib, importlib.util, multiprocessing as mp
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = True
for sealf in ["SEAL_ABL1.txt"]:
    for line in open(os.path.join(ROOT, "real", sealf)):
        if not line.strip() or line.startswith("#"): continue
        h, f = line.split()
        if hashlib.sha256(open(os.path.join(ROOT, f), "rb").read()).hexdigest() != h: sys.exit(f"HASH MISMATCH {f}: stop")
sys.path[:0] = [os.path.join(ROOT, "real"), os.path.join(ROOT, "real", "hosts")]
row, model, c0, c1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
assert row in ("ai_agents", "ai_ai", "space") and c0 <= c1
assert {"ai_agents": 901 <= c0 and c1 <= 940, "ai_ai": 1001 <= c0 and c1 <= 1150, "space": 901 <= c0 and c1 <= 948}[row]
cells = list(range(c0, c1 + 1))
if os.environ.get("ABL1_SMOKE") == "1": cells = [1]   # pre-seal crash check on a development cell only

def hosts():
    if row == "economics": from economics import Economics; return {"std": (lambda: Economics(), Economics(standard="strongest"))}
    if row == "space": from space import Space; return {"std": (lambda: Space("pq"), Space("strongest"))}
    if row == "ai_ai": from ai_ai import AiAi; return {"std": (lambda: AiAi(model), None)}
    if row == "ai_human": from ai_human import AIHuman; return {"std": (lambda: AIHuman(spec=model), None)}
    from ai_agents import AIAgents
    strong = AIAgents(spec=model, standard="strongest")
    return {"selfcons": (lambda: AIAgents(spec=model, standard="selfcons"), strong)}

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
    if row == "space":
        return {"t": st["t"], "passes": list(st["passes"]), "queue": [dict(it) for it in st["queue"]]}
    if row == "ai_agents":
        keep = ("id", "temp", "answer", "calls", "tok", "errors", "restarts")
        return {"ti": st["ti"], "calls": st["calls"], "tok": st["tok"], "br": [{k: b[k] for k in keep if k in b} for b in st["br"]]}
    if row == "ai_human":
        i = st["pos"][st["t"]] if st["t"] < len(st["pos"]) else len(st["conv"]) - 1
        return {"t": st["t"], "conv": [tuple(x) for x in st["conv"][: i + 1]]}
    return {}

def bad(a):
    """The switched-off operator (fixed before the seal)."""
    try:
        if row == "ai_agents": return isinstance(a, tuple) and len(a) >= 1 and a[0] in ("blind", "reuse")
        if row == "ai_ai":
            import ai_ai as M
            return isinstance(a, (list, tuple)) and any(isinstance(x, tuple) and (x in (M.HOLO, M.PACK) or M.iskey(x)) for x in a)
    except Exception: return False
    return False

def minus(h):
    if row == "space":
        h.primitives = lambda s_: []; h.frame = lambda s_: []; return h
    h = generated(h); b0, f0 = h.branches, h.frame
    h.branches = lambda s_: [(n, a) for n, a in b0(s_) if not bad(a)]
    h.frame = lambda s_: [x for x in f0(s_) if not bad(x[2])]
    return h

def generated(h):
    """The generated moves replace the host's own levers (primitives and frame); native branches stay."""
    spec = importlib.util.spec_from_file_location("gen_moves", os.path.join(ROOT, "real", "composed", f"{row}_moves.py"))
    g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
    def frame(st):
        out = []
        for op, fn in g.MOVES.items():
            try: a = fn(VIEW(st))
            except Exception: a = None          # a move that fails on a state is simply not offered (counted)
            if a is not None: out.append((f"C:{op}", f"C:{op}", a))
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
    for arm in ("default", "full", "minus"):
        clear(); ta = time.time()
        if arm == "default": o = seed.run(make(), c, "default")
        elif arm == "full": o = seed3.run(generated(make()), c, "seed3v1")
        else:
            if row == "space": seed3.OFF["landing"] = 10 ** 9
            o = seed3.run(minus(make()), c, "seed3v1")
        r[arm] = {q: o[q] for q in KEEP if q in o}; r[arm]["sec"] = round(time.time() - ta, 1)
    r["sec"] = round(time.time() - t0)
    return f"{name}|{c}", r

if __name__ == "__main__":
    jobs = [(name, c) for name in hosts() for c in cells]
    out = {"row": row, "model": model, "cells_run": cells, "cells": {}}
    with mp.get_context("spawn").Pool(2, maxtasksperchild=1) as pool:
        for key, r in pool.imap(one, jobs):
            out["cells"][key] = r; print(key, json.dumps(r, default=str)[:240], flush=True)
    safe = model.replace("/", "_").replace(":", "_").replace(",", "+")
    os.makedirs(os.path.join(ROOT, "real", "outa1"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "real", "outa1", f"{row}_{safe}_{c0}_{c1}.json"), "w"), default=str, indent=1)
