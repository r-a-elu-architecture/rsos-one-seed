"""REAL3 v2 row 2 quick test (development cells 1..4 only; never cells >= 100). Modes per cell:
  seed3    REAL3 v2: v1 choice + the seed operators bound by this host's hooks (real/HOST_INTERFACE_REAL3v2.md)
  seed3v1  REAL3 v1 exactly (primitives + the HOLOGRAM MESSAGE frame levers)
  seed     REAL2 seed (Law 4 landing step);  rollout (plain rollout);  default (the standard)
  strongest = default for this row (the standard is the strongest available, ai_ai.py C): not run twice.
LINEAGES: seed3.POOL / OFF and the v2 operator pools are kept per mode lineage (seed3 sees only earlier seed3 runs,
seed3v1 only earlier seed3v1 runs, as in the REAL3 v1 quick), so seed3v1 reproduces the REAL3 v1 run. SEED3_POOL_IN is
loaded at import (start of the seed3 lineage); with SEED3_POOL_OUT set the seed3 lineage's pool is written after every
seed3 run. Models: argument 1 (comma: A,B) or env REAL1_AIAI_MODELS; default mock:0,mock:0 (interface check only).
Env REAL3_AIAI_PACK=0 (default) keeps the token-parity PACK lever off (decided; see ai_ai.py REAL3)."""
import sys, os, time, copy, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seed, seed3
import seed3_ops as O
from ai_ai import AiAi, USE_PACK
import llm_bounded as LB
host = AiAi(sys.argv[1] if len(sys.argv) > 1 else None)
MODES = ("seed3", "seed3v1", "seed", "rollout", "default")
G = [seed3.POOL, seed3.OFF, O.OPOOL, O.SHAPES, O.INH]
LIN = {"_init": ([copy.deepcopy(d) for d in G], 0, dict(O.STATS)), "_cur": None}
def lineage(name):
    cur = LIN["_cur"]
    if cur == name: return
    if cur is not None: LIN[cur] = ([copy.deepcopy(d) for d in G], seed3.POLICY_FALLBACK[0], dict(O.STATS))
    snap, pf, stats = LIN.get(name, LIN["_init"])
    for d, v in zip(G, snap): d.clear(); d.update(copy.deepcopy(v))
    seed3.POLICY_FALLBACK[0] = pf; O.STATS.clear(); O.STATS.update(stats); LIN["_cur"] = name
def pareto(a, b):   # a vs standard b: result >= AND resource <=, at least one strictly
    ge, le = a["result"] >= b["result"], a["resource"] <= b["resource"]
    strict = a["result"] > b["result"] or a["resource"] < b["resource"]
    return "WIN" if ge and le and strict else ("TIE" if a["result"] == b["result"] and a["resource"] == b["resource"] else "no")
print(f"ai_ai  models {host.models}  pack {USE_PACK}  cells 1-4  modes {MODES}  pool in {O.STATS['loaded_from']}", flush=True)
T0 = time.time(); tot_ops = {}; bound = None
for cell in (1, 2, 3, 4):
    out = {}
    for mode in MODES:
        lineage({"seed3": "v2", "seed3v1": "v1"}.get(mode, "real")); t1 = time.time()
        o = seed3.run(host, cell, mode) if mode in ("seed3", "seed3v1") else seed.run(host, cell, mode); out[mode] = o
        print(f"cell {cell} {mode:8s} result {o['result']:.0f} resource {o['resource']:5.0f} R {o['R']:.6f} "
              f"rounds {o['rounds']} msg {o['msg_tokens']} calls {o['model_calls']} failed {o['failed_calls']} held {o['held_slots']} "
              f"holo {o['holo_msgs']} keys {o['keys_sent']} [{time.time() - t1:.1f}s]"
              + (f" choices={o['choices']}" if mode != "default" else "")
              + (f" ERRORS {len(o['errors'])}; last: {o['errors'][-1][:160]}" if o["errors"] else ""), flush=True)
        if mode == "seed3":
            used = {k: v for k, v in o["ops_used"].items() if v}; bound = o["ops_bound"]
            for k, v in used.items():
                if k not in ("colour", "rooms", "transplant"): tot_ops[k] = tot_ops.get(k, 0) + v
            print(f"        seed3 ops used {used}  rooms {o['rooms']}  vetoed {o['vote_vetoed']}  rollouts v1/ops "
                  f"{o['rollouts_v1']}/{o['rollouts_ops']}  passed {{{', '.join(f'{k}: {v}' for k, v in o['ops_passed_membrane'].items() if v)}}}"
                  f"  enter depth {o['enter_depth']}  inherit {o['inherit_entries']} shapes {o['shape_keys']} fallback {o['op_fallback']} pool_saved {o['pool_saved']}")
    print(f"cell {cell} pareto vs default: " + ", ".join(f"{m} {pareto(out[m], out['default'])}" for m in MODES[:-1])
          + f"; strongest = default (row C)", flush=True)
print(f"seed3 v2 operators chosen (cells 1-4): {tot_ops}")
if bound: print("ops bound: " + json.dumps(bound))
print("bounded calls: " + json.dumps(LB.summary()))
print(f"total {time.time() - T0:.1f}s")
