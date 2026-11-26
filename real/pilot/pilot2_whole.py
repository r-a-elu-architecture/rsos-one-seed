"""PILOT2 (development cells only; screening, never confirmation): AI-AI with the WHOLE system bound to one structure.
Arms per cell: rollout (plain rollout), v1 (seed3v1, RSOS shapes A only: the CONF5 arm), whole (seed3v1 + the system bound):
  whole = v1 plus
   (1) B shaped by the same structure (Eagle skeleton + hologram of the whole): B's message sends first the facts it
       owns on the question's 4-hop chain as far as B can walk it in its own view, and the facts A asked for by key,
       then fills with the standard order. (Before: B always sent the standard summary.)
   (2) the system sees itself (law as structure: invariant "commit only on a complete skeleton", check = walk the chain
       in the agent's OWN view, response = continue): an agent's ANSWER is taken only if its own view holds the whole
       chain; otherwise it counts as CONTINUE. The model still writes the answer; tokens are counted as before.
Usage: python real/pilot/pilot2_whole.py <models> <arm> <first> <last> -> real/pilot/out2/ai_ai_<arm>_<c0>_<c1>.json"""
import os, sys, json, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "real"), os.path.join(ROOT, "real", "hosts")]
model, arm, c0, c1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
assert c1 <= 16, "pilot: development cells only"
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

def clear():
    for p in (seed3.POOL, seed3.OFF, seed3_ops.OPOOL, seed3_ops.SHAPES, seed3_ops.INH): p.clear()
    seed3.POLICY_FALLBACK[0] = 0

out = {"row": "ai_ai", "arm": arm, "model": model, "cells": {}}
for c in range(c0, c1 + 1):
    clear(); t = time.time()
    if arm == "rollout": o = seed.run(M.AiAi(model), c, "rollout")
    elif arm == "v1": o = seed3.run(M.AiAi(model), c, "seed3v1")
    else: o = seed3.run(Whole(model), c, "seed3v1")
    out["cells"][c] = {k: o[k] for k in ("result", "resource", "choices", "failed_calls") if k in o}
    out["cells"][c]["sec"] = round(time.time() - t, 1)
    print(arm, c, o["result"], round(o["resource"]), flush=True)
os.makedirs(os.path.join(ROOT, "real", "pilot", "out2"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "real", "pilot", "out2", f"ai_ai_{arm}_{c0}_{c1}.json"), "w"), default=str, indent=1)
