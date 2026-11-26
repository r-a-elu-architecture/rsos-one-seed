"""SC2: the first predicted gap of the operation table, FLOW (derive_where). PREREGISTRATION_SC2.md.

The SC1 robot scene (50 objects, 300 keys, 56 requests, depth 4, three drift events), with 8 requests per task of the new
kind, placed by the seed:

    "Move every object owned by rover 2 cells right (x plus 2, capped at 9)."
    -> FLOW x OVER owner rover +2 CAP 9   ==  derive_where(field=x, cond_field=owner, equals=rover, add=2, max=9)

The 16 task seeds are not chosen by anyone: they are derived from a drand randomness beacon round fixed in advance and
published after the predictor was frozen (experiments/sc2_beacon.json: {"round": ..., "randomness": "<hex>"}):
seed_i = int(sha256("<randomness>:SC2:<i>")[:8 bytes]) for i = 0..15.

FLOW is added to the A7/A8 harness at runtime (parser, executor, renderer, oracle, audit kinds, one grammar line for the
RSOS arms); no frozen file changes.
"""

import hashlib
import json
import os
import random
import re

import a1_agents as A
import sc1_tasks as SC

HERE = os.path.dirname(os.path.abspath(__file__))
BEACON = os.path.join(HERE, "sc2_beacon.json")
CELLS = {"SC2": (56, 4, 50)}
N_FLOW = 8
FLOW_RX = re.compile(r"^FLOW\s+(\S+)\s+OVER\s+(\S+)\s+(\S+)(?:\s+([+-]\d+))?(?:\s+CAP\s+(-?\d+))?\s*;?$", re.I)
FLOW_REQ = r"^Move every object owned by (\S+) (\d) cells? (right|up) \((\S+) plus (\d), capped at 9\)\.$"
GRAMMAR_LINE = (" FLOW field OVER c x [+n] [CAP m]: for every object whose c equals x, its field becomes field+n, "
                "max m (one line moves them all).")


def seeds_from(randomness, n=16):
    return [int.from_bytes(hashlib.sha256(f"{randomness}:SC2:{i}".encode()).digest()[:8], "big") for i in range(n)]


def beacon():
    if os.path.exists(BEACON):
        return json.load(open(BEACON))
    return None


SEEDS = {"SC2": seeds_from(beacon()["randomness"]) if beacon() else seeds_from("dry-run, not the beacon")}


def make_task(seed, steps=56, depth=4, n_objects=50):
    rng = random.Random(seed)
    objs = SC.OBJECTS[:n_objects]
    state = {f"{o}.{f}": SC.rand_value(f, rng) for o in objs for f in SC.FIELDS}
    init = dict(state)
    flow_at = set(rng.sample(range(4, steps), N_FLOW))       # never in the first four steps
    reqs, touched, truths = [], [], [dict(state)]
    chain_src, chain_left = None, 0
    while len(reqs) < steps:
        if len(reqs) in flow_at:                               # the new kind
            robots = sorted({v for k, v in state.items() if k.endswith(".owner")})
            if robots:
                r = rng.choice(robots); n = rng.randint(1, 2); f, d = rng.choice([("x", "right"), ("y", "up")])
                t = []
                for o in objs:
                    if state.get(f"{o}.owner") == r and f"{o}.{f}" in state:
                        state[f"{o}.{f}"] = str(min(int(state[f"{o}.{f}"]) + n, 9)); t.append(f"{o}.{f}")
                reqs.append(f"Move every object owned by {r} {n} cell{'s' if n > 1 else ''} {d} ({f} plus {n}, capped at 9).")
                touched.append(t + [f"{o}.owner" for o in objs if f"{o}.owner" in state]); truths.append(dict(state))
                continue
        if chain_left == 0 and rng.random() < 0.5:
            cand = [k for k in state if k.split(".")[1] in SC.NUMF + ["height_mm"]]
            chain_src, chain_left = rng.choice(cand), depth
        if chain_left > 0 and rng.random() < 0.6:
            out = SC._dep_request(rng, state, chain_src) if chain_src in state else None
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
            k = rng.choice(keys); f = k.split(".")[1]; v = SC.rand_value(f, rng)
            while v == state[k]:
                v = SC.rand_value(f, rng)
            text = rng.choice([f"Set {k} to {v}.", f"Change the {f} of {k.split('.')[0]} to {v}.",
                               f"{k.split('.')[0]} needs {f} = {v} from now on."])
            state[k] = v; t = [k]
        elif kind in ("inc", "double"):
            cand = [k for k in keys if k.endswith((".x", ".y"))]
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
            a = rng.choice(present); b = rng.choice([o for o in SC.ROBOTS if o != a])
            text = f"Everything owned by {a} is now owned by {b}."
            t = [k for k, v in state.items() if k.endswith(".owner") and v == a]
            for k in t:
                state[k] = b
        elif kind == "add":
            o = rng.choice(objs); f = rng.choice(["grip", "weight_g"]); k = f"{o}.{f}"
            v = SC.rand_value(f, rng)
            text = f"Set {k} to {v}." if k in state else f"Add a new line {k} = {v} at the end."
            state[k] = v; t = [k]
        elif kind == "delete":
            cand = [k for k in keys if k != chain_src and not k.endswith((".owner", ".x", ".y"))]
            if len(cand) < 10:
                continue
            k = rng.choice(cand); text = f"Remove the line {k} entirely."
            del state[k]; t = [k]
        elif kind == "cond":
            o = rng.choice(objs)
            if f"{o}.room" not in state or f"{o}.on" not in state:
                continue
            r = rng.choice(SC.ROOMS); s1, s2 = rng.sample(SC.SURFACES, 2)
            text = f"If {o}.room is {r}, set {o}.on to {s1}; otherwise set it to {s2}."
            state[f"{o}.on"] = s1 if state[f"{o}.room"] == r else s2; t = [f"{o}.on"]
        else:
            f = rng.choice(["height_mm", "y", "x"])
            pair = [o for o in objs if f"{o}.{f}" in state]
            if len(pair) < 2:
                continue
            a, b = rng.sample(pair, 2)
            text = f"Make {b}.{f} equal to {a}.{f}."
            state[f"{b}.{f}"] = state[f"{a}.{f}"]; t = [f"{b}.{f}", f"{a}.{f}"]
        reqs.append(text); touched.append(t); truths.append(dict(state))
    return {"seed": seed, "init": init, "requests": reqs, "touched": touched, "final": dict(state), "truths": truths}


def drift_plan(task, truths):
    return SC.drift_plan(task, truths)


def _flow_op(line):
    m = FLOW_RX.match(line.strip())
    if not m:
        return None
    return ("FLOW", m.group(1), m.group(2), m.group(3), int(m.group(4) or 0),
            int(m.group(5)) if m.group(5) is not None else None)


def patch(cell="SC2"):
    """Install the scene and FLOW into the harness, in-process only."""
    import a5_arms as X
    import a5_run as R5
    SC.patch("SC1")
    A.make_task = make_task
    A.drift_plan = drift_plan
    if "FLOW" in X.OPS:
        return
    X.OPS.add("FLOW")
    X.RISK_OPS.add("FLOW")
    X.GRAMMAR = X.GRAMMAR + GRAMMAR_LINE
    R5.ORACLE.append((FLOW_REQ, lambda m: f"FLOW {m[4]} OVER owner {m[1]} +{m[2]} CAP 9"))
    parse0, exec0, text0 = X.parse_ops, X.execute, X.ops_text

    def parse_ops(text, after_sep=False):
        if "FLOW" not in text.upper():
            return parse0(text, after_sep)
        lines = text.strip().split("\n")
        if after_sep:
            parse0(text, after_sep)                              # same '---' rule and errors as before
            lines = lines[[x.strip() for x in lines].index("---") + 1:]
        ops, chunk = [], []

        def flush():
            if chunk and any(c.strip().split(" ")[0].upper() in X.OPS for c in chunk if c.strip()):
                ops.extend(parse0("\n".join(chunk)))
            chunk.clear()
        for ln in lines:
            if ln.strip().upper().startswith("FLOW"):
                flush()
                op = _flow_op(ln)
                if op is None:
                    raise X.OpError(f"cannot parse '{ln.strip()}'")
                ops.append(op)
            else:
                chunk.append(ln)
        flush()
        if not ops:
            raise X.OpError("no operations")
        return ops

    def execute(state, ops):
        st, srcs = dict(state), []
        for op in ops:
            if op[0] != "FLOW":
                st, s = exec0(st, [op]); srcs += s
                continue
            _, fld, cond, x, n, cap = op
            if cond not in A.FORMAT or fld not in A.FORMAT:
                raise X.OpError(f"unknown field in '{text0([op]) if False else fld}'")
            w = [f"{k.split('.')[0]}.{fld}" for k, v in st.items() if k.split(".")[1] == cond and v == x
                 and f"{k.split('.')[0]}.{fld}" in st]
            srcs += w
            for k in w:
                st[k] = str(X.capped(X.num(st, k) + n, cap))
                if not A.valid_line(f"{k} = {st[k]}"):
                    raise X.OpError(f"invalid line '{k} = {st[k]}'")
        return st, list(dict.fromkeys(srcs))

    def ops_text(ops):
        return "\n".join(f"FLOW {o[1]} OVER {o[2]} {o[3]}" + (f" {o[4]:+d}" if o[4] else "") +
                         (f" CAP {o[5]}" if o[5] is not None else "") if o[0] == "FLOW" else text0([o]) for o in ops)

    X.parse_ops, X.execute, X.ops_text = parse_ops, execute, ops_text
