"""CONF4 sealed unit (25 Nov 2026; real/PREREG_CONF4.md): does the RSOS language itself make better decision programs?
Arms per cell (all inside the same sealed seed, seed3v1, same forks, membrane and landing):
  default    the row's standard
  structure  seed3v1 with every lever off (no programs): the floor
  R1 R2 R3   seed3v1 whose levers are the programs written by three fresh RSOS agents (real/conf4/R*/<row>_moves.py)
  C1 C2 C3   seed3v1 whose levers are the programs written by three fresh CONTROL agents (real/conf4/C*/<row>_moves.py),
             who received the identical domain description (real/conf4/DOMAINS.md) without the RSOS sources
Programs see the filtered VIEW (no hidden values). Leak fix: trace and plan stores cleared before every arm; one fresh
process per cell. Usage: python cloud/conf4_unit.py <row> <model-or-> <first cell> <last cell> -> real/outc4/...
Seal: real/SEAL_CONF4.txt."""
import os, sys, json, time, hashlib, importlib.util, multiprocessing as mp
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = True
for sealf in ["SEAL_CONF4.txt"]:
    for line in open(os.path.join(ROOT, "real", sealf)):
        if not line.strip() or line.startswith("#"): continue
        h, f = line.split()
        if hashlib.sha256(open(os.path.join(ROOT, f), "rb").read()).hexdigest() != h: sys.exit(f"HASH MISMATCH {f}: stop")
sys.path[:0] = [os.path.join(ROOT, "real"), os.path.join(ROOT, "real", "hosts")]
row, model, c0, c1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
assert row in ("ai_agents", "ai_human", "ai_ai", "space") and c0 <= c1
assert (441 <= c0 and c1 <= 480) if row == "ai_human" else 801 <= c0   # AI-human: Topical-Chat test_freq has 539 conversations
cells = list(range(c0, c1 + 1))
if os.environ.get("CONF4_SMOKE") == "1": cells = [1]   # pre-seal crash check on a development cell only

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
    if row == "space":
        return {"t": st["t"], "passes": list(st["passes"]), "queue": [dict(it) for it in st["queue"]]}
    if row == "ai_agents":
        keep = ("id", "temp", "answer", "calls", "tok", "errors", "restarts")
        return {"ti": st["ti"], "calls": st["calls"], "tok": st["tok"], "br": [{k: b[k] for k in keep if k in b} for b in st["br"]]}
    if row == "ai_human":
        i = st["pos"][st["t"]] if st["t"] < len(st["pos"]) else len(st["conv"]) - 1
        return {"t": st["t"], "conv": [tuple(x) for x in st["conv"][: i + 1]]}
    return {}

ARMS_P = ("R1", "R2", "R3", "C1", "C2", "C3")

def programs(h, arm):
    """The generated moves replace the host's own levers (primitives and frame); native branches stay."""
    spec = importlib.util.spec_from_file_location("gen_moves", os.path.join(ROOT, "real", "conf4", arm, f"{row}_moves.py"))
    g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
    def frame(st):
        out = []
        for op, fn in g.MOVES.items():
            try: a = fn(VIEW(st))
            except Exception: a = None          # a move that fails on a state is simply not offered (counted)
            if a is not None: out.append((f"{arm}:{op}", f"{arm}:{op}", a))
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
    arms = ("default", "structure") + ARMS_P
    for arm in arms:
        if arm == "strongest" and strong is None: continue
        clear(); ta = time.time()
        if arm == "default": o = seed.run(make(), c, "default")
        elif arm == "structure":
            h = make(); h.primitives = lambda s_: []; h.frame = lambda s_: []; o = seed3.run(h, c, "seed3v1")
        else: o = seed3.run(programs(make(), arm), c, "seed3v1")
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
    os.makedirs(os.path.join(ROOT, "real", "outc4"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "real", "outc4", f"{row}_{safe}_{c0}_{c1}.json"), "w"), default=str, indent=1)
