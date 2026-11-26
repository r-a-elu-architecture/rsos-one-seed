"""CONF6 sealed unit (26 Nov 2026; real/PREREG_CONF6.md): AI-AI with the WHOLE system bound to one RSOS structure,
vs plain rollout, on fresh cells. Arms per cell:
  default   the standard (both agents send their K most relevant facts)
  rollout   plain rollout (Bertsekas), the RSOS-free planning baseline
  v1        seed3v1, RSOS shapes A only (the CONF5 arm)
  whole     seed3v1 + the whole system bound (identified by PILOT2, real/pilot/PILOT2_NOTES.md):
   (1) B shaped by the same structure (Eagle skeleton + hologram of the whole): B sends first the facts it owns on the
       question's 4-hop chain as far as B can walk it in its own view, and the facts A asked for by key, then the
       standard order;
   (2) the system sees itself (law as structure: invariant "commit only on a complete skeleton", check = walk the chain
       in the agent's OWN view, response = continue): an agent's ANSWER is taken only if its own view holds the chain;
       otherwise it counts as CONTINUE. The model still writes the answer; its tokens are counted.
  noholo    whole with Law 5 off (no hologram / packed message and no key from any source)
Usage: python cloud/conf6_unit.py <models> <first> <last> -> real/outc6/ai_ai_<first>_<last>.json   Seal: real/SEAL_CONF6.txt."""
import os, sys, json, time, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for line in open(os.path.join(ROOT, "real", "SEAL_CONF6.txt")):
    if not line.strip() or line.startswith("#"): continue
    h, f = line.split()
    if hashlib.sha256(open(os.path.join(ROOT, f), "rb").read()).hexdigest() != h: sys.exit(f"HASH MISMATCH {f}: stop")
sys.path[:0] = [os.path.join(ROOT, "real"), os.path.join(ROOT, "real", "hosts")]
model, c0, c1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
assert 1401 <= c0 <= c1 <= 1600
cells = [1] if os.environ.get("CONF6_SMOKE") == "1" else list(range(c0, c1 + 1))
import seed, seed3, seed3_ops
import ai_ai as M

class Whole(M.AiAi):
    def _standard(s, st, who):
        if who != "B": return super()._standard(st, who)
        view = s._view(st, "B"); sentB = set(st["sent"]["B"]); first = []
        e = st["x"]
        for r in M.PATH:                                   # Eagle: walk the skeleton as far as B's own view allows
            k = (r, e)
            if k in view:
                if st["owner"][k] == "B" and k not in sentB and k not in first: first.append(k)
                e = view[k]
            else: break
        for q in st.get("asked", ()):                      # hologram key: the hop A asked B to resolve
            k = (q[1], q[2])
            if k in st["owner"] and st["owner"][k] == "B" and k not in sentB and k not in first: first.append(k)
        rest = [k for k in M.AiAi._ranked(s, st, "B")[0] if k not in first]
        return (first + rest)[:M.K]

    def _answer(s, st, who, spec):
        a, t = super()._answer(st, who, spec)
        if a is not None and not st["model"] and M.resolve(s._view(st, who), st["x"]) is None: a = None
        return a, t

class NoHolo(Whole):
    @staticmethod
    def _bad(a): return isinstance(a, (list, tuple)) and any(isinstance(x, tuple) and (x in (M.HOLO, M.PACK) or M.iskey(x)) for x in a)
    def branches(s, st): return [(n, a) for n, a in super().branches(st) if not NoHolo._bad(a)]
    def frame(s, st): return [x for x in super().frame(st) if not NoHolo._bad(x[2])]
    def primitives(s, st): return [x for x in super().primitives(st) if not NoHolo._bad(x[-1])]

def clear():
    for p in (seed3.POOL, seed3.OFF, seed3_ops.OPOOL, seed3_ops.SHAPES, seed3_ops.INH): p.clear()
    seed3.POLICY_FALLBACK[0] = 0

KEEP = ("result", "resource", "choices", "failed_calls", "holo_msgs", "keys_sent")
out = {"row": "ai_ai", "model": model, "cells_run": cells, "cells": {}}
for c in cells:
    r = {}
    for arm in ("default", "rollout", "v1", "whole", "noholo"):
        clear(); t = time.time()
        if arm == "default": o = seed.run(M.AiAi(model), c, "default")
        elif arm == "rollout": o = seed.run(M.AiAi(model), c, "rollout")
        elif arm == "v1": o = seed3.run(M.AiAi(model), c, "seed3v1")
        elif arm == "whole": o = seed3.run(Whole(model), c, "seed3v1")
        else: o = seed3.run(NoHolo(model), c, "seed3v1")
        r[arm] = {k: o[k] for k in KEEP if k in o}; r[arm]["sec"] = round(time.time() - t, 1)
    out["cells"][str(c)] = r
    print(c, {a: (v["result"], round(v["resource"])) for a, v in r.items()}, flush=True)
os.makedirs(os.path.join(ROOT, "real", "outc6"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "real", "outc6", f"ai_ai_{c0}_{c1}.json"), "w"), default=str, indent=1)
