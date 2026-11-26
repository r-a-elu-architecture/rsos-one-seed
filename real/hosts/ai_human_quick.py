"""REAL3 v2 row 3 quick test (development cells 1..4 = Topical-Chat conversations 1..4; never cells >= 100). Modes:
  seed3    REAL3 v2: v1 choice + the seed operators bound by this host's hooks (real/HOST_INTERFACE_REAL3v2.md)
  seed3v1  REAL3 v1 exactly (primitives + the HOLOGRAM REPLY frame lever with the READY gate)
  seed     REAL2 seed (Law 4 landing step);  rollout (plain rollout);  default (the standard direct reply)
  strongest = default for this row (the direct reply is the strongest available, ai_human.py C): not run twice.
Prints result (coverage of the next human turn's needs, a proxy), resource (kilotokens), R; input / output tokens,
parity (max token difference vs the standard; always <= 0), mention and hologram turns, Pareto vs default.
LINEAGES: seed3.POOL / OFF and the v2 operator pools are kept per mode lineage (as in ai_ai_quick.py), so seed3v1
reproduces the REAL3 v1 run. SEED3_POOL_IN / SEED3_POOL_OUT: the seed3 lineage's TRANSPLANT / COMPRESS pool.
Usage: python real/hosts/ai_human_quick.py [model spec]      default mock:0 (interface check, stand-in model, no claim)
       python real/hosts/ai_human_quick.py openrouter:meta-llama/llama-3.1-8b-instruct   (cloud, OPENROUTER_API_KEY set)"""
import os, sys, time, copy, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.dirname(HERE), HERE]
import seed, seed3                         # noqa: E402
import seed3_ops as O                      # noqa: E402
from ai_human import AIHuman               # noqa: E402
import llm_bounded as LB                   # noqa: E402

spec = sys.argv[1] if len(sys.argv) > 1 else "mock:0"
host = AIHuman(spec=spec)
MODES = ("seed3", "seed3v1", "seed", "rollout", "default")
print(f"ai_human  model {spec}  cells 1-4  modes {MODES}  pool in {O.STATS['loaded_from']}", flush=True)
G = [seed3.POOL, seed3.OFF, O.OPOOL, O.SHAPES, O.INH]
LIN = {"_init": ([copy.deepcopy(d) for d in G], 0, dict(O.STATS)), "_cur": None}
def lineage(name):
    cur = LIN["_cur"]
    if cur == name: return
    if cur is not None: LIN[cur] = ([copy.deepcopy(d) for d in G], seed3.POLICY_FALLBACK[0], dict(O.STATS))
    snap, pf, stats = LIN.get(name, LIN["_init"])
    for d, v in zip(G, snap): d.clear(); d.update(copy.deepcopy(v))
    seed3.POLICY_FALLBACK[0] = pf; O.STATS.clear(); O.STATS.update(stats); LIN["_cur"] = name
def pareto(a, b):
    ge, le = a["result"] >= b["result"], a["resource"] <= b["resource"]
    strict = a["result"] > b["result"] or a["resource"] < b["resource"]
    return "WIN" if ge and le and strict else ("TIE" if a["result"] == b["result"] and a["resource"] == b["resource"] else "no")
T0 = time.time(); tot_ops = {}; bound = None
for cell in (1, 2, 3, 4):
    out = {}
    for mode in MODES:
        lineage({"seed3": "v2", "seed3v1": "v1"}.get(mode, "real")); t1 = time.time()
        o = seed3.run(host, cell, mode) if mode in ("seed3", "seed3v1") else seed.run(host, cell, mode); out[mode] = o
        ch = o["choices"]
        land = f"  land w{ch.get('land_withheld', 0)} r{ch.get('land_retargeted', 0)}" if mode == "seed" else ""
        print(f"cell {cell} {mode:8s} result {o['result']:.3f}  resource {o['resource']:.3f}  R {o['R']:.4f}"
              f"  in {o['input_tokens']} out {o['reply_tokens']} parity {o['parity_max']} mention {o['mentions']} holo {o['holo']}"
              f"  failed {o['failed_calls']}{land} [{time.time() - t1:.1f}s]"
              + (f"  choices={ch}" if mode.startswith("seed3") else "")
              + (f"  ERRORS {len(o['errors'])}; last: {o['errors'][-1][:160]}" if o["errors"] else ""), flush=True)
        if mode == "seed3":
            used = {k: v for k, v in o["ops_used"].items() if v}; bound = o["ops_bound"]
            for k, v in used.items():
                if k not in ("colour", "rooms", "transplant"): tot_ops[k] = tot_ops.get(k, 0) + v
            print(f"        seed3 ops used {used}  rooms {o['rooms']}  vetoed {o['vote_vetoed']}  rollouts v1/ops "
                  f"{o['rollouts_v1']}/{o['rollouts_ops']}  passed {{{', '.join(f'{k}: {v}' for k, v in o['ops_passed_membrane'].items() if v)}}}"
                  f"  enter depth {o['enter_depth']}  inherit {o['inherit_entries']} shapes {o['shape_keys']} fallback {o['op_fallback']} pool_saved {o['pool_saved']}")
    print(f"cell {cell} pareto vs default: " + ", ".join(f"{m} {pareto(out[m], out['default'])}" for m in MODES[:-1])
          + "; strongest = default (row C)", flush=True)
print(f"seed3 v2 operators chosen (cells 1-4): {tot_ops}")
if bound: print("ops bound: " + json.dumps(bound))
print("bounded calls: " + json.dumps(LB.summary()))
print(f"total {time.time() - T0:.1f}s")
