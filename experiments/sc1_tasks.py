"""SC1: a grounded robot scene as shared state. PREREGISTRATION_SC1.md.

A warehouse/kitchen scene graph shared by several robots, flattened to the StateBench form `object.field = value`.
The cell has the size of A8's L3 (50 objects x 6 fields = 300 keys, 56 change requests, dependency depth 4), so the
A7/A8 runner, prompts, arms, audit rule and drift injection run unchanged; only the world changes.

Symbol-to-state mapping (published in PREREGISTRATION_SC1.md, section 2):

    object.x          grid column, 0-9 (10 x 10 occupancy grid of the floor plan)
    object.y          grid row, 0-9
    object.height_mm  height of the object's base above the floor, 100-5000 mm
    object.owner      the robot responsible for the object: rover, drone, arm, crane, loader, scout
    object.room       kitchen, lab, dock, hall
    object.on         the surface the object rests on: table, shelf, floor, cart   (scene-graph edge "on")
    object.grip       added during a task: soft, firm, vacuum
    object.weight_g   added during a task: 16-256

Requests use the A1/A7 request templates (so the harness classifier and the replay oracle apply unchanged); in the
scene they read as robot instructions, e.g. "Everything owned by rover is now owned by drone." (hand-over of every
object a robot is responsible for), "Set cup.x to tray.x plus 2, capped at 9." (place the cup two cells right of the
tray, clamped to the grid), "Set cup.height_mm to shelf.height_mm plus 500." (500 mm above), "If cup.room is lab,
set cup.on to shelf; otherwise set it to table." (route by state).
"""

import random

import a1_agents as A

OBJECTS = ["cup", "mug", "tray", "box", "crate", "drill", "wrench", "hammer", "bolt", "cable", "lamp", "sensor",
           "bottle", "jar", "plate", "bowl", "kettle", "pallet", "bin", "tote", "ladder", "helmet", "glove", "tape",
           "pump", "valve", "hose", "filter", "fan", "motor", "gear", "spring", "brick", "plank", "pipe", "panel",
           "screen", "camera", "battery", "charger", "radio", "beacon", "marker", "cone", "sign", "flag", "rope",
           "chain", "hook", "bag"]
FIELDS = ["x", "y", "height_mm", "owner", "room", "on"]
ROBOTS = ["rover", "drone", "arm", "crane", "loader", "scout"]
ROOMS = ["kitchen", "lab", "dock", "hall"]
SURFACES = ["table", "shelf", "floor", "cart"]
FORMAT = {"x": r"\d", "y": r"\d", "height_mm": r"\d{3,5}", "owner": "|".join(ROBOTS), "room": "|".join(ROOMS),
          "on": "|".join(SURFACES), "grip": "soft|firm|vacuum", "weight_g": r"\d{1,4}"}
NUMF = ["x", "y"]
CELLS = {"SC1": (56, 4, 50)}
SEEDS = {"SC1": list(range(900, 916))}
assert len(OBJECTS) == 50 and len(set(OBJECTS)) == 50 and all(o.isalpha() and o.islower() for o in OBJECTS)


def rand_value(field, rng):
    return {"x": lambda: str(rng.randint(0, 9)), "y": lambda: str(rng.randint(0, 9)),
            "height_mm": lambda: str(rng.randint(1, 50) * 100), "owner": lambda: rng.choice(ROBOTS),
            "room": lambda: rng.choice(ROOMS), "on": lambda: rng.choice(SURFACES),
            "grip": lambda: rng.choice(["soft", "firm", "vacuum"]),
            "weight_g": lambda: str(rng.choice([16, 32, 64, 128, 256]))}[field]()


def _dep_request(rng, state, src):
    """One state-dependent request reading src (copy, plus-n, sum); returns (text, target) or None."""
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
    if s_f == "height_mm":
        same = [k for k in state if k.endswith(".height_mm") and k != src]
        if not same:
            return None
        tgt = rng.choice(same)
        if int(state[src]) + 500 <= 99999 and rng.random() < 0.5:
            state[tgt] = str(int(state[src]) + 500)
            return f"Set {tgt} to {src} plus 500.", tgt
        state[tgt] = state[src]
        return f"Make {tgt} equal to {src}.", tgt
    return None


def make_task(seed, steps=56, depth=4, n_objects=50):
    rng = random.Random(seed)
    objs = OBJECTS[:n_objects]
    state = {f"{o}.{f}": rand_value(f, rng) for o in objs for f in FIELDS}
    init = dict(state)
    reqs, touched, truths = [], [], [dict(state)]
    chain_src, chain_left = None, 0
    while len(reqs) < steps:
        if chain_left == 0 and rng.random() < 0.5:
            cand = [k for k in state if k.split(".")[1] in NUMF + ["height_mm"]]
            chain_src, chain_left = rng.choice(cand), depth
        if chain_left > 0 and rng.random() < 0.6:
            out = _dep_request(rng, state, chain_src) if chain_src in state else None
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
            k = rng.choice(keys); f = k.split(".")[1]; v = rand_value(f, rng)
            while v == state[k]:
                v = rand_value(f, rng)
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
            a = rng.choice(present); b = rng.choice([o for o in ROBOTS if o != a])
            text = f"Everything owned by {a} is now owned by {b}."
            t = [k for k, v in state.items() if k.endswith(".owner") and v == a]
            for k in t:
                state[k] = b
        elif kind == "add":
            o = rng.choice(objs); f = rng.choice(["grip", "weight_g"]); k = f"{o}.{f}"
            v = rand_value(f, rng)
            text = f"Set {k} to {v}." if k in state else f"Add a new line {k} = {v} at the end."
            state[k] = v; t = [k]
        elif kind == "delete":
            cand = [k for k in keys if k != chain_src]
            if len(cand) < 10:
                continue
            k = rng.choice(cand); text = f"Remove the line {k} entirely."
            del state[k]; t = [k]
        elif kind == "cond":
            o = rng.choice(objs)
            if f"{o}.room" not in state or f"{o}.on" not in state:
                continue
            r = rng.choice(ROOMS); s1, s2 = rng.sample(SURFACES, 2)
            text = f"If {o}.room is {r}, set {o}.on to {s1}; otherwise set it to {s2}."
            state[f"{o}.on"] = s1 if state[f"{o}.room"] == r else s2; t = [f"{o}.on"]
        else:  # copy
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
    """3 drift events at n/4, n/2, 3n/4 on keys not touched at or after the step (A7b rule)."""
    n = len(task["requests"])
    rng = random.Random(task["seed"] * 7 + 1)
    plan = {}
    for st in (n // 4, n // 2, 3 * n // 4):
        later = set(k for t in task["touched"][st:] for k in t)
        cand = [k for k in truths[st] if k not in later and k in truths[-1] and truths[st][k] == truths[-1][k]]
        if not cand:
            continue
        k = rng.choice(sorted(cand)); f = k.split(".")[1]
        v = rand_value(f, rng)
        while v == truths[st][k]:
            v = rand_value(f, rng)
        plan[st] = (k, v)
    return plan


def patch(cell="SC1"):
    """Install the scene world into the harness (in-process only; no frozen file changes)."""
    A.make_task = make_task
    A.drift_plan = drift_plan
    A.FORMAT.update(FORMAT)
