"""A7b long-task generator: horizon, dependency depth and state size. PREREGISTRATION_A7.md, amendment of 18 Nov 13:40.

Cells (16 seeds each):
  L1  56 steps,  depth 4,   30 keys  (5 services)
  L2 224 steps,  depth 16,  30 keys
  L3  56 steps,  depth 4,  300 keys  (50 services)

Requests use only the A1/A4 request templates (so the harness classifier and the oracle apply unchanged). Dependency
depth D: the task contains chains of D consecutive state-dependent requests (copy, plus-n, sum), each reading the key
the previous one wrote, interleaved with the A1 mix (set, inc, double, owner transfer, add, delete, condition, copy).
Drift: 3 events at n/4, n/2, 3n/4 on keys not touched at or after the step (skipped if none exists).
"""

import random

import a1_agents as A

CELLS = {"L1": (56, 4, 5), "L2": (224, 16, 5), "L3": (56, 4, 50)}
SEEDS = {"L1": list(range(500, 516)), "L2": list(range(600, 616)), "L3": list(range(700, 716))}
EXTRA = ["alpha", "beacon", "cargo", "delta", "ember", "falcon", "garnet", "harbor", "indigo", "jasper", "kepler",
         "lumen", "mosaic", "nimbus", "orbit", "prism", "quartz", "raven", "sierra", "tundra", "umber", "vector",
         "willow", "xenon", "yonder", "zephyr", "atlas", "bramble", "cobalt", "dune", "echo", "fjord", "glacier",
         "helix", "iris", "juniper", "kestrel", "lotus", "meadow", "nova", "onyx", "pylon", "rune", "solace", "topaz"]
NUMF = ["replicas", "retries"]
_cell = {"name": None}


def services(n):
    return (A.SERVICES + EXTRA)[:n]


def _dep_request(rng, state, src, frozen_targets):
    """One state-dependent request reading src; returns (text, target) or None. Values stay valid (caps at 9)."""
    s_f = src.split(".")[1]
    if s_f in NUMF:
        same = [k for k in state if k.endswith("." + s_f) and k != src]
        if not same:
            return None
        tgt = rng.choice(same)
        r = rng.random()
        if r < 0.4:
            n = rng.randint(1, 3)
            state[tgt] = str(min(int(state[src]) + n, 9))
            return f"Set {tgt} to {src} plus {n}, capped at 9.", tgt
        if r < 0.7:
            other = [k for k in same if k != tgt]
            if not other:
                return None
            o = rng.choice(other)
            state[tgt] = str(min(int(state[src]) + int(state[o]), 9))
            return f"Set {tgt} to {src} + {o}, capped at 9.", tgt
        state[tgt] = state[src]
        return f"Make {tgt} equal to {src}.", tgt
    if s_f == "timeout_ms":
        same = [k for k in state if k.endswith(".timeout_ms") and k != src]
        if not same:
            return None
        tgt = rng.choice(same)
        if int(state[src]) + 500 <= 99999 and rng.random() < 0.5:
            state[tgt] = str(int(state[src]) + 500)
            return f"Set {tgt} to {src} plus 500.", tgt
        state[tgt] = state[src]
        return f"Make {tgt} equal to {src}.", tgt
    return None


def make_task(seed, steps=None, depth=None, n_services=None):
    steps, depth, n_services = (steps, depth, n_services) if steps else CELLS[_cell["name"]]
    rng = random.Random(seed)
    svcs = services(n_services)
    state = {f"{s}.{f}": A.rand_value(f, rng) for s in svcs for f in A.FIELDS}
    init = dict(state)
    reqs, touched, truths = [], [], [dict(state)]
    chain_src, chain_left = None, 0
    while len(reqs) < steps:
        if chain_left == 0 and rng.random() < 0.5:            # start a chain of `depth` dependent requests
            cand = [k for k in state if k.split(".")[1] in NUMF + ["timeout_ms"]]
            chain_src, chain_left = rng.choice(cand), depth
        if chain_left > 0 and rng.random() < 0.6:
            out = _dep_request(rng, state, chain_src, set()) if chain_src in state else None
            if out is None:
                chain_left = 0
                continue
            text, tgt = out
            reqs.append(text); touched.append([tgt, chain_src]); truths.append(dict(state))
            chain_src, chain_left = tgt, chain_left - 1
            continue
        kind = rng.choice(["set", "set", "inc", "double", "owner", "add", "delete", "cond", "copy"])
        keys = list(state)
        if kind == "set":
            k = rng.choice(keys); f = k.split(".")[1]; v = A.rand_value(f, rng)
            while v == state[k]:
                v = A.rand_value(f, rng)
            text = rng.choice([f"Set {k} to {v}.", f"Change the {f} of {k.split('.')[0]} to {v}.",
                               f"{k.split('.')[0]} needs {f} = {v} from now on."])
            state[k] = v; t = [k]
        elif kind in ("inc", "double"):
            cand = [k for k in keys if k.endswith(("replicas", "retries"))]
            if not cand:
                continue
            k = rng.choice(cand); old = int(state[k])
            if kind == "inc":
                d = rng.randint(1, 2); new = min(old + d, 9); text = f"Increase {k} by {d} (cap at 9)."
            else:
                new = min(old * 2, 9); text = f"Double {k}, capped at 9."
            state[k] = str(new); t = [k]
        elif kind == "owner":
            present = sorted({v for k, v in state.items() if k.endswith(".owner")})
            if not present:
                continue
            a = rng.choice(present); b = rng.choice([o for o in A.OWNERS if o != a])
            text = f"Everything owned by {a} is now owned by {b}."
            t = [k for k, v in state.items() if k.endswith(".owner") and v == a]
            for k in t:
                state[k] = b
        elif kind == "add":
            s = rng.choice(svcs); f = rng.choice(["max_conn", "tier"]); k = f"{s}.{f}"
            v = A.rand_value(f, rng)
            text = f"Set {k} to {v}." if k in state else f"Add a new line {k} = {v} at the end."
            state[k] = v; t = [k]
        elif kind == "delete":
            cand = [k for k in keys if k != chain_src]
            if len(cand) < 10:
                continue
            k = rng.choice(cand); text = f"Remove the line {k} entirely."
            del state[k]; t = [k]
        elif kind == "cond":
            s = rng.choice(svcs)
            if f"{s}.region" not in state or f"{s}.log_level" not in state:
                continue
            r = rng.choice(A.REGIONS); l1, l2 = rng.sample(A.LEVELS, 2)
            text = f"If {s}.region is {r}, set {s}.log_level to {l1}; otherwise set it to {l2}."
            state[f"{s}.log_level"] = l1 if state[f"{s}.region"] == r else l2; t = [f"{s}.log_level"]
        else:  # copy
            f = rng.choice(["timeout_ms", "retries", "replicas"])
            pair = [s for s in svcs if f"{s}.{f}" in state]
            if len(pair) < 2:
                continue
            a, b = rng.sample(pair, 2)
            text = f"Make {b}.{f} equal to {a}.{f}."
            state[f"{b}.{f}"] = state[f"{a}.{f}"]; t = [f"{b}.{f}", f"{a}.{f}"]
        reqs.append(text); touched.append(t); truths.append(dict(state))
    return {"seed": seed, "init": init, "requests": reqs, "touched": touched, "final": dict(state), "truths": truths}


def drift_plan(task, truths):
    n = len(task["requests"])
    rng = random.Random(task["seed"] * 7 + 1)
    plan = {}
    for st in (n // 4, n // 2, 3 * n // 4):
        later = set(k for t in task["touched"][st:] for k in t)
        cand = [k for k in truths[st] if k not in later and k in truths[-1] and truths[st][k] == truths[-1][k]]
        if not cand:
            continue
        k = rng.choice(sorted(cand)); f = k.split(".")[1]
        v = A.rand_value(f, rng)
        while v == truths[st][k]:
            v = A.rand_value(f, rng)
        plan[st] = (k, v)
    return plan


def chain_depth(task):
    """Longest chain of state-dependent requests, each reading the key the previous one wrote (measured)."""
    best, depth_of = 0, {}
    for req, t in zip(task["requests"], task["touched"]):
        if len(t) == 2 and (" plus " in req or " + " in req or req.startswith("Make ")):
            d = depth_of.get(t[1], 0) + 1
            depth_of[t[0]] = d
            best = max(best, d)
        else:
            for k in t:
                depth_of.pop(k, None)
    return best


def patch(cell):
    _cell["name"] = cell
    A.make_task = make_task
    A.drift_plan = drift_plan
