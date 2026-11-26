"""REAL3 v2 row 1 quick test (development cells 1..4 only; never cells >= 100). Per cell and standard (ReAct = the row's
standard; self-consistency = the second baseline) the modes
  seed3    REAL3 v2: v1 choice + the seed operators bound by this host's hooks (real/HOST_INTERFACE_REAL3v2.md)
  seed3v1  REAL3 v1 exactly (primitives + frame levers: blind planning, hologram re-plans, plan reuse, vote)
  seed     REAL2 (with the Law 4 landing step);  rollout (plain rollout);  default (the standard)
then the strongest method (CGES / ReASC early-stopped self-consistency).
Prints result (accuracy), resource (kilotokens, every call incl. plan calls), R, Pareto vs the standard; for seed3 /
seed3v1 the plan calls, failures, reuses, blind answers, fallbacks; for seed3 the operators chosen, rooms, vetoes,
rollouts; failed calls and the bounded-call counters (llm_bounded) per run. Row time guard: env REAL3_ROW_BUDGET_MIN
(default 55 for a real model): no new cell starts after it (a started cell always finishes).
LINEAGES: the process-wide pools (seed3.POOL / OFF, the v2 operator pools OPOOL / SHAPES / INH, the blind plan pool and
its O-traces) are kept per mode lineage: seed3 sees only what earlier seed3 runs left, seed3v1 only what earlier seed3v1
runs left (exactly the REAL3 v1 quick order: cells in order, react before selfcons), so the two are not mixed and
seed3v1 reproduces the REAL3 v1 run. SEED3_POOL_IN is loaded at import (start of the seed3 lineage); with SEED3_POOL_OUT
set the seed3 lineage's TRANSPLANT / COMPRESS pool is written after every seed3 run.
Usage: python real/hosts/ai_agents_quick.py [model spec] [--cells 1-4] [--modes seed3,seed3v1,...]
         default mock:0 (interface check, STAND-IN, no claim)
       python real/hosts/ai_agents_quick.py openrouter:openai/gpt-oss-20b   (cloud, OPENROUTER_API_KEY set)"""
import os, sys, time, copy, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.dirname(HERE), HERE]
import seed                                # noqa: E402
import seed3                               # noqa: E402
import seed3_ops as O                      # noqa: E402
from ai_agents import AIAgents             # noqa: E402
import ai_agents_blind as BL               # noqa: E402
import llm_bounded as LB                   # noqa: E402

argv = sys.argv[1:]; opt = {}
for k in ("--cells", "--modes"):
    if k in argv: i = argv.index(k); opt[k] = argv[i + 1]; del argv[i:i + 2]
spec = argv[0] if argv else "mock:0"
cells = (1, 2, 3, 4)
if "--cells" in opt:
    lo, hi = opt["--cells"].split("-"); cells = tuple(range(int(lo), int(hi) + 1))
assert max(cells) < 100, "cells >= 100 are confirmatory: never run here"
MODES = tuple(opt.get("--modes", "seed3,seed3v1,seed,rollout,default").split(","))

G = [seed3.POOL, seed3.OFF, O.OPOOL, O.SHAPES, O.INH, BL.PLAN_POOL, BL.EXEC, BL.TRACE]
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

print(f"ai_agents  model {spec}  cells {cells}  modes {MODES}  pool in {O.STATS['loaded_from']}", flush=True)
hosts = {std: AIAgents(spec=spec, standard=std) for std in ("react", "selfcons", "strongest")}
T0 = time.time(); tot_ops = {}; bound = None
# ROW TIME GUARD (cloud): a new cell starts only while the row is under REAL3_ROW_BUDGET_MIN minutes (default 55 for a
# real model, none for mock); a cell is never cut in the middle, so every printed run is complete.
BUDGET = float(os.environ.get("REAL3_ROW_BUDGET_MIN", "0" if spec.startswith("mock") else "55")) * 60
for cell in cells:
    if BUDGET and time.time() - T0 > BUDGET:
        print(f"ROW TIME GUARD: {(time.time() - T0) / 60:.1f} min > {BUDGET / 60:.0f} min; cells from {cell} not started", flush=True); break
    for std, host in hosts.items():
        out = {}
        for mode in (MODES if std != "strongest" else ("default",)):
            lineage({"seed3": "v2", "seed3v1": "v1"}.get(mode, "real")); t1 = time.time(); c0 = dict(LB.STATE)
            o = seed3.run(host, cell, mode) if mode in ("seed3", "seed3v1") else seed.run(host, cell, mode)
            out[mode] = o; ch = o["choices"]
            label = "strongest" if (std == "strongest" and mode == "default") else mode
            extra = (f"  land w{ch.get('land_withheld', 0)} r{ch.get('land_retargeted', 0)}" if mode == "seed" else "")
            if mode.startswith("seed3"):
                extra = (f"  plan calls {o['plan_calls']} fail {o['plan_failures']} reused {o['plans_reused']} "
                         f"blind answers {o['blind_answers']} fallbacks {o['blind_fallbacks']} pool {len(BL.PLAN_POOL)}")
            calls = {k: LB.STATE[k] - c0[k] for k in ("calls", "failed", "retries")}
            print(f"cell {cell} standard={std:9s} {label:9s} result {o['result']:.3f}  resource {o['resource']:6.2f}  "
                  f"R {o['R']:.4f}{extra}  failed_calls {o['failed_calls']}  [{time.time() - t1:.1f}s; calls {calls['calls']} "
                  f"failed {calls['failed']} retries {calls['retries']}]"
                  + (f"  ERRORS {len(o['errors'])} logged; last: {o['errors'][-1][:160]}" if o["errors"] else ""), flush=True)
            if mode.startswith("seed3"):
                print(f"        {mode} choices: " + ", ".join(f"{k} {v}" for k, v in sorted(ch.items(), key=lambda x: -x[1])[:8]))
            if mode == "seed3":
                used = {k: v for k, v in o["ops_used"].items() if v}; bound = o["ops_bound"]
                for k, v in used.items():
                    if k not in ("colour", "rooms", "transplant"): tot_ops[k] = tot_ops.get(k, 0) + v
                print(f"        seed3 ops used {used}  rooms {o['rooms']}  vetoed {o['vote_vetoed']}  rollouts v1/ops "
                      f"{o['rollouts_v1']}/{o['rollouts_ops']}  passed {{{', '.join(f'{k}: {v}' for k, v in o['ops_passed_membrane'].items() if v)}}}"
                      f"  inherit {o['inherit_entries']} shapes {o['shape_keys']} fallback {o['op_fallback']} pool_saved {o['pool_saved']}")
        if "default" in out and std != "strongest":
            print(f"cell {cell} standard={std:9s} pareto vs default: " +
                  ", ".join(f"{m} {pareto(out[m], out['default'])}" for m in out if m != "default"), flush=True)
print(f"seed3 v2 operators chosen (all cells, both standards): {tot_ops}")
if bound: print("ops bound: " + json.dumps(bound))
print("bounded calls: " + json.dumps(LB.summary()))
print(f"total {time.time() - T0:.1f}s")
